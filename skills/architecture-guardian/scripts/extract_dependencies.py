#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""Extract best-effort static dependency evidence from a repository.

The output is evidence, not an architecture model. Python and JavaScript/TypeScript
relative imports receive lightweight path resolution; other supported languages are
reported as import facts without claiming semantic ownership or boundaries.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

SKIP_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", ".venv", "venv",
    "node_modules", "vendor", "dist", "build", "target", "out", "coverage",
    ".next", ".nuxt", ".cache", "__pycache__", ".pytest_cache", ".mypy_cache",
}
SOURCE_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs", ".java", ".kt", ".cs"}
JS_IMPORT_RE = re.compile(r"(?:import\s+(?:[^'\"]+?\s+from\s+)?|export\s+[^'\"]+?\s+from\s+|require\s*\()\s*['\"]([^'\"]+)['\"]")
GO_IMPORT_RE = re.compile(r'^[ \t]*(?:import[ \t]+)?["`]([^"`]+)["`]', re.MULTILINE)
RUST_USE_RE = re.compile(r"^[ \t]*use[ \t]+([^;]+);", re.MULTILINE)
JAVA_IMPORT_RE = re.compile(r"^[ \t]*import[ \t]+(?:static[ \t]+)?([A-Za-z0-9_.*]+)[ \t]*;", re.MULTILINE)
KOTLIN_IMPORT_RE = re.compile(r"^[ \t]*import[ \t]+([A-Za-z0-9_.*]+)", re.MULTILINE)
CSHARP_USING_RE = re.compile(r"^[ \t]*using[ \t]+(?:static[ \t]+)?([A-Za-z0-9_.]+)[ \t]*;", re.MULTILINE)


def iter_source_files(root: Path, max_files: int) -> Iterable[Path]:
    seen = 0
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith(".git"))
        for name in sorted(files):
            path = Path(current) / name
            if path.suffix.lower() not in SOURCE_EXTS or path.is_symlink():
                continue
            yield path
            seen += 1
            if seen >= max_files:
                return


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def resolve_js_relative(source: Path, spec: str, root: Path) -> str | None:
    if not spec.startswith("."):
        return None
    base = (source.parent / spec).resolve()
    candidates = [base]
    for ext in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"):
        candidates.append(Path(str(base) + ext))
    for ext in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"):
        candidates.append(base / f"index{ext}")
    for candidate in candidates:
        try:
            if candidate.is_file() and root in candidate.parents:
                return rel(candidate, root)
        except OSError:
            pass
    return None


def resolve_python(source: Path, module: str | None, level: int, root: Path) -> str | None:
    if level > 0:
        base = source.parent
        for _ in range(level - 1):
            base = base.parent
        parts = module.split(".") if module else []
        target = base.joinpath(*parts)
    else:
        if not module:
            return None
        target = root.joinpath(*module.split("."))

    candidates = [target.with_suffix(".py"), target / "__init__.py"]
    for candidate in candidates:
        try:
            if candidate.is_file() and (candidate == root or root in candidate.parents):
                return rel(candidate, root)
        except OSError:
            pass
    return None


def python_imports(path: Path, root: Path) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    out: list[dict[str, object]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                spec = alias.name
                resolved = resolve_python(path, spec, 0, root)
                out.append({"specifier": spec, "kind": "import", "resolved": resolved})
        elif isinstance(node, ast.ImportFrom):
            spec = ("." * node.level) + (node.module or "")
            resolved = resolve_python(path, node.module, node.level, root)
            out.append({"specifier": spec, "kind": "from", "resolved": resolved})
    return out


def regex_imports(path: Path, pattern: re.Pattern[str], kind: str) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [{"specifier": match.group(1).strip(), "kind": kind, "resolved": None} for match in pattern.finditer(text)]


def js_imports(path: Path, root: Path) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    out = []
    for match in JS_IMPORT_RE.finditer(text):
        spec = match.group(1).strip()
        out.append({"specifier": spec, "kind": "import", "resolved": resolve_js_relative(path, spec, root)})
    return out


def extract_for_file(path: Path, root: Path) -> list[dict[str, object]]:
    ext = path.suffix.lower()
    if ext == ".py":
        return python_imports(path, root)
    if ext in {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}:
        return js_imports(path, root)
    if ext == ".go":
        return regex_imports(path, GO_IMPORT_RE, "go-import")
    if ext == ".rs":
        return regex_imports(path, RUST_USE_RE, "rust-use")
    if ext == ".java":
        return regex_imports(path, JAVA_IMPORT_RE, "java-import")
    if ext == ".kt":
        return regex_imports(path, KOTLIN_IMPORT_RE, "kotlin-import")
    if ext == ".cs":
        return regex_imports(path, CSHARP_USING_RE, "csharp-using")
    return []


def path_group(path: str, depth: int) -> str:
    parts = Path(path).parent.parts
    if not parts or parts == (".",):
        return "."
    return "/".join(parts[:max(1, depth)])


def strongly_connected_components(edges: list[tuple[str, str]]) -> list[list[str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    nodes: set[str] = set()
    for src, dst in edges:
        graph[src].add(dst)
        nodes.add(src)
        nodes.add(dst)

    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    components: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlink[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for nxt in sorted(graph.get(node, ())):
            if nxt not in indices:
                visit(nxt)
                lowlink[node] = min(lowlink[node], lowlink[nxt])
            elif nxt in on_stack:
                lowlink[node] = min(lowlink[node], indices[nxt])

        if lowlink[node] == indices[node]:
            component: list[str] = []
            while True:
                item = stack.pop()
                on_stack.remove(item)
                component.append(item)
                if item == node:
                    break
            if len(component) > 1:
                components.append(sorted(component))

    for node in sorted(nodes):
        if node not in indices:
            visit(node)
    return sorted(components, key=lambda c: (-len(c), c))


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract static dependency evidence for architecture analysis.")
    parser.add_argument("repo_root", help="Repository root directory")
    parser.add_argument("--output", help="Write JSON to this file instead of stdout")
    parser.add_argument("--max-files", type=int, default=30000, help="Maximum source files to scan (default: 30000)")
    parser.add_argument("--max-edges", type=int, default=100000, help="Maximum import facts retained (default: 100000)")
    parser.add_argument("--group-depth", type=int, default=2, help="Path segments used for structural grouping (default: 2)")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")

    scan_limit = max(1, args.max_files)
    discovered_sources = list(iter_source_files(root, scan_limit + 1))
    file_limit_reached = len(discovered_sources) > scan_limit
    source_files = discovered_sources[:scan_limit]
    edges: list[dict[str, object]] = []
    cross_group_counts: Counter[tuple[str, str]] = Counter()
    unresolved_specs: Counter[str] = Counter()
    resolved_count = 0

    for source in source_files:
        source_rel = rel(source, root)
        for item in extract_for_file(source, root):
            record = {"source": source_rel, **item}
            edges.append(record)
            target = item.get("resolved")
            if isinstance(target, str):
                resolved_count += 1
                sg = path_group(source_rel, args.group_depth)
                tg = path_group(target, args.group_depth)
                if sg != tg:
                    cross_group_counts[(sg, tg)] += 1
            else:
                spec = item.get("specifier")
                if isinstance(spec, str):
                    unresolved_specs[spec] += 1
            if len(edges) >= args.max_edges:
                break
        if len(edges) >= args.max_edges:
            break

    grouped = [
        {"from_path_group": src, "to_path_group": dst, "resolved_edge_count": count}
        for (src, dst), count in cross_group_counts.most_common()
    ]
    group_cycles = strongly_connected_components(list(cross_group_counts))
    result = {
        "schema_version": 1,
        "repo_root": str(root),
        "scan": {
            "source_files_scanned": len(source_files),
            "max_files": args.max_files,
            "file_limit_reached": file_limit_reached,
            "edge_limit": args.max_edges,
            "edge_limit_reached": len(edges) >= args.max_edges,
        },
        "summary": {
            "import_facts": len(edges),
            "resolved_internal_file_edges": resolved_count,
            "unresolved_or_external_import_facts": len(edges) - resolved_count,
        },
        "path_grouping": {"depth": max(1, args.group_depth), "semantic_boundary": False},
        "cross_path_group_edges": grouped[:500],
        "path_group_cycles": group_cycles[:100],
        "frequent_unresolved_or_external_specifiers": [
            {"specifier": spec, "count": count} for spec, count in unresolved_specs.most_common(200)
        ],
        "edges": edges,
        "interpretation_warning": (
            "Path groups and import edges are structural evidence only. They are not semantic architecture boundaries, "
            "ownership declarations, or proof that a dependency is architecturally intended."
        ),
    }

    payload = json.dumps(result, indent=2, sort_keys=False)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
