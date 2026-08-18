#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""Create a deterministic repository discovery summary for architecture extraction.

This script inventories facts. It does not infer semantic architecture, ownership,
or bounded contexts.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Iterable

SKIP_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", ".venv", "venv",
    "node_modules", "vendor", "dist", "build", "target", "out", "coverage",
    ".next", ".nuxt", ".cache", "__pycache__", ".pytest_cache", ".mypy_cache",
}

LANG_BY_EXT = {
    ".py": "Python", ".pyi": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin",
    ".cs": "C#", ".fs": "F#", ".rb": "Ruby", ".php": "PHP", ".swift": "Swift",
    ".scala": "Scala", ".c": "C", ".h": "C/C++", ".cc": "C++", ".cpp": "C++",
    ".hpp": "C++", ".sql": "SQL", ".proto": "Protocol Buffers", ".graphql": "GraphQL",
    ".gql": "GraphQL", ".yaml": "YAML", ".yml": "YAML", ".json": "JSON",
    ".toml": "TOML", ".tf": "Terraform", ".sh": "Shell",
}

MANIFEST_NAMES = {
    "package.json", "pnpm-workspace.yaml", "yarn.lock", "package-lock.json", "pnpm-lock.yaml",
    "pyproject.toml", "requirements.txt", "setup.py", "setup.cfg", "poetry.lock", "pdm.lock",
    "go.mod", "go.work", "Cargo.toml", "Cargo.lock", "pom.xml", "build.gradle",
    "build.gradle.kts", "settings.gradle", "settings.gradle.kts", "Gemfile", "composer.json",
    "mix.exs", "pubspec.yaml", "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
}

ARCH_DOC_TERMS = ("architecture", "architectural", "adr", "decision", "design", "rfc")
TEST_DIR_NAMES = {"test", "tests", "spec", "specs", "__tests__", "integration", "e2e"}
SCHEMA_DIR_TERMS = ("migration", "migrations", "schema", "schemas", "database", "db")
ENTRYPOINT_STEMS = {"main", "app", "server", "index", "bootstrap", "application", "program"}


def iter_files(root: Path, max_files: int) -> Iterable[Path]:
    seen = 0
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith(".git"))
        for name in sorted(files):
            path = Path(current) / name
            try:
                if path.is_symlink():
                    continue
            except OSError:
                continue
            yield path
            seen += 1
            if seen >= max_files:
                return


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def limited(values: list[str], limit: int = 200) -> list[str]:
    return values[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory repository facts for architecture extraction.")
    parser.add_argument("repo_root", help="Repository root directory")
    parser.add_argument("--output", help="Write JSON to this file instead of stdout")
    parser.add_argument("--max-files", type=int, default=50000, help="Maximum files to scan (default: 50000)")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")

    scan_limit = max(1, args.max_files)
    discovered = list(iter_files(root, scan_limit + 1))
    truncated = len(discovered) > scan_limit
    files = discovered[:scan_limit]
    ext_counts: Counter[str] = Counter()
    language_counts: Counter[str] = Counter()
    top_level_counts: Counter[str] = Counter()
    manifests: list[str] = []
    arch_docs: list[str] = []
    test_paths: set[str] = set()
    schema_paths: set[str] = set()
    entrypoints: list[str] = []

    for path in files:
        rp = rel(path, root)
        parts = Path(rp).parts
        top = parts[0] if len(parts) > 1 else "."
        top_level_counts[top] += 1

        suffix = path.suffix.lower()
        if suffix:
            ext_counts[suffix] += 1
            language = LANG_BY_EXT.get(suffix)
            if language:
                language_counts[language] += 1

        lower_name = path.name.lower()
        lower_rp = rp.lower()
        if path.name in MANIFEST_NAMES or lower_name.endswith((".sln", ".csproj", ".fsproj")):
            manifests.append(rp)

        if suffix in {".md", ".mdx", ".rst", ".adoc", ".txt"} and any(term in lower_rp for term in ARCH_DOC_TERMS):
            arch_docs.append(rp)

        if any(part.lower() in TEST_DIR_NAMES for part in parts[:-1]) or lower_name.startswith("test_") or ".test." in lower_name or ".spec." in lower_name:
            test_paths.add("/".join(parts[:-1]) or ".")

        if any(term in part.lower() for part in parts[:-1] for term in SCHEMA_DIR_TERMS) or suffix in {".sql", ".proto", ".graphql", ".gql"}:
            schema_paths.add("/".join(parts[:-1]) or ".")

        if path.stem.lower() in ENTRYPOINT_STEMS and suffix in LANG_BY_EXT:
            entrypoints.append(rp)

    top_level_dirs = sorted(
        p.name for p in root.iterdir()
        if p.is_dir() and p.name not in SKIP_DIRS and not p.name.startswith(".git")
    )

    result = {
        "schema_version": 1,
        "repo_root": str(root),
        "scan": {
            "files_scanned": len(files),
            "max_files": args.max_files,
            "truncated": truncated,
            "skipped_directories": sorted(SKIP_DIRS),
        },
        "top_level_directories": top_level_dirs,
        "top_level_file_counts": dict(top_level_counts.most_common()),
        "language_file_counts": dict(language_counts.most_common()),
        "extension_counts": dict(ext_counts.most_common(50)),
        "manifests": limited(sorted(set(manifests))),
        "architecture_doc_candidates": limited(sorted(set(arch_docs))),
        "test_path_candidates": limited(sorted(test_paths)),
        "schema_migration_candidates": limited(sorted(schema_paths)),
        "entrypoint_candidates": limited(sorted(set(entrypoints))),
        "interpretation_warning": (
            "These are repository facts and path-based candidates only. Do not infer semantic boundaries, "
            "ownership, or intended architecture from this inventory alone."
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
