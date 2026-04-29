from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4


def validate_skill_name(skill_name: str) -> None:
    candidate = Path(skill_name)
    if (
        not skill_name
        or candidate.is_absolute()
        or "/" in skill_name
        or "\\" in skill_name
        or skill_name in {".", ".."}
        or ".." in candidate.parts
    ):
        raise ValueError(
            "skill_name must be a single directory name without path separators, "
            "absolute paths, or '..'"
        )


def replace_directory(source_dir: Path, target_dir: Path) -> Path:
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    staged_dir = target_dir.parent / f".{target_dir.name}.tmp-{uuid4().hex}"
    backup_dir = target_dir.parent / f".{target_dir.name}.bak-{uuid4().hex}"

    shutil.copytree(source_dir, staged_dir)

    replaced_existing = False
    try:
        if target_dir.exists():
            target_dir.rename(backup_dir)
            replaced_existing = True

        staged_dir.rename(target_dir)
    except Exception:
        if replaced_existing and backup_dir.exists() and not target_dir.exists():
            backup_dir.rename(target_dir)
        if staged_dir.exists():
            shutil.rmtree(staged_dir, ignore_errors=True)
        raise

    if backup_dir.exists():
        shutil.rmtree(backup_dir)

    return target_dir


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        raise RuntimeError(f"git {' '.join(args)} failed: {message}")
    return result


def write_repo_info(skill_dir: Path, repo_root: Path, repo_url: str) -> None:
    repo_info = {
        "repo_root": str(repo_root),
        "repo_url": repo_url,
    }
    (skill_dir / "repo-info.json").write_text(
        json.dumps(repo_info, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
