from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable
from uuid import uuid4


def clone_repository(repo_url: str, clone_dir: Path) -> None:
    result = subprocess.run(
        ["git", "clone", "--depth=1", repo_url, str(clone_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        raise RuntimeError(f"Failed to clone repository '{repo_url}': {message}")


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


def install_skill(
    repo_url: str,
    skill_name: str,
    project_root: Path,
    clone_repo: Callable[[str, Path], None] = clone_repository,
) -> Path:
    validate_skill_name(skill_name)

    with tempfile.TemporaryDirectory() as temp_dir:
        clone_dir = Path(temp_dir) / "repo"
        clone_repo(repo_url, clone_dir)

        remote_skill_dir = clone_dir / "skills" / skill_name
        remote_skill_file = remote_skill_dir / "SKILL.md"
        if not remote_skill_file.is_file():
            raise ValueError(
                f"Skill '{skill_name}' not found in repository '{repo_url}' "
                f"(expected {remote_skill_file.relative_to(clone_dir)})"
            )

        target_dir = project_root / ".agents" / "skills" / skill_name
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        staged_dir = target_dir.parent / f".{skill_name}.tmp-{uuid4().hex}"
        backup_dir = target_dir.parent / f".{skill_name}.bak-{uuid4().hex}"

        shutil.copytree(remote_skill_dir, staged_dir)

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install a skill from a git repository.")
    parser.add_argument("--repo", required=True, help="Git repository URL")
    parser.add_argument("--skill", required=True, help="Skill name under skills/")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        install_skill(
            repo_url=args.repo,
            skill_name=args.skill,
            project_root=Path.cwd(),
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
