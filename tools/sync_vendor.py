from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from tools.lib.common import replace_directory, run_git


def load_source_config(repo_root: Path, source_name: str) -> dict:
    config_path = repo_root / "registry" / "sources" / f"{source_name}.json"
    return json.loads(config_path.read_text(encoding="utf-8"))


def iter_source_names(repo_root: Path) -> list[str]:
    source_root = repo_root / "registry" / "sources"
    return sorted(path.stem for path in source_root.glob("*.json"))


def collect_sync_candidates(source_root: Path, blacklist: set[str]) -> list[Path]:
    candidates: list[Path] = []
    for child in sorted(source_root.iterdir()):
        if child.name in blacklist:
            continue
        if not child.is_dir():
            continue
        if not (child / "SKILL.md").is_file():
            continue
        candidates.append(child)
    return candidates


def write_state(repo_root: Path, source_name: str, state: dict) -> Path:
    state_path = repo_root / "registry" / "state" / f"{source_name}.json"
    payload = {"name": source_name, "kind": "vendor-state", **state}
    state_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return state_path


def resolve_vendor_target_path(repo_root: Path, target_path: str) -> Path:
    normalized = normalize_relative_path(
        target_path,
        "sync.target_path must be a relative path under vendor/",
    )
    if not normalized.parts or normalized.parts[0] != "vendor":
        raise ValueError("sync.target_path must be a relative path under vendor/")

    return repo_root / normalized


def normalize_relative_path(raw_path: str, error_message: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        raise ValueError(error_message)

    normalized_parts: list[str] = []
    for part in candidate.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if normalized_parts:
                normalized_parts.pop()
            else:
                normalized_parts.append(part)
            continue
        normalized_parts.append(part)

    normalized = Path(*normalized_parts)
    if ".." in normalized.parts:
        raise ValueError(error_message)
    return normalized


def resolve_clone_source_path(clone_dir: Path, source_path: str) -> Path:
    normalized = normalize_relative_path(
        source_path,
        "sync.source_path must be a relative path within the cloned repository",
    )
    return clone_dir / normalized


def validate_sync_mode(mode: str) -> None:
    if mode != "directory":
        raise ValueError("sync.mode must be 'directory'")


def sync_vendor_source(repo_root: Path, source_name: str) -> dict:
    config = load_source_config(repo_root, source_name)
    upstream = config["upstream"]
    sync = config["sync"]
    blacklist = set(config.get("filter", {}).get("blacklist", []))
    validate_sync_mode(sync["mode"])
    target_dir = resolve_vendor_target_path(repo_root, sync["target_path"])

    with tempfile.TemporaryDirectory(prefix="sync-vendor-") as temp_dir:
        temp_root = Path(temp_dir)
        clone_dir = temp_root / "repo"
        source_root = resolve_clone_source_path(clone_dir, sync["source_path"])
        run_git(
            [
                "clone",
                "--depth=1",
                "--branch",
                upstream["ref"],
                upstream["repo"],
                str(clone_dir),
            ],
            cwd=repo_root,
        )
        resolved_ref = run_git(["rev-parse", "HEAD"], cwd=clone_dir).stdout.strip()
        candidates = collect_sync_candidates(source_root, blacklist)

        staged_root = temp_root / "staged"
        staged_root.mkdir(parents=True, exist_ok=True)
        for candidate in candidates:
            replace_directory(candidate, staged_root / candidate.name)

        replace_directory(staged_root, target_dir)
        state = {
            "last_synced_ref": resolved_ref,
            "last_synced_at": datetime.now(timezone.utc).isoformat(),
            "last_source_count": len([item for item in source_root.iterdir() if item.is_dir()]),
            "last_synced_count": len(candidates),
        }
        write_state(repo_root, source_name, state)
        return state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync vendor skill sources into vendor/.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source", help="Single source name under registry/sources/")
    group.add_argument("--all", action="store_true", help="Sync all registered sources")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = Path(__file__).resolve().parent.parent

    try:
        if args.source:
            sync_vendor_source(repo_root, args.source)
        else:
            for source_name in iter_source_names(repo_root):
                sync_vendor_source(repo_root, source_name)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
