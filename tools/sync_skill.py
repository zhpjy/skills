from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Callable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.lib.common import replace_directory, run_git, validate_skill_name, write_repo_info


def clone_repository(repo_url: str, clone_dir: Path) -> None:
    try:
        run_git(["clone", "--depth=1", repo_url, str(clone_dir)], cwd=Path.cwd())
    except RuntimeError as exc:
        _, _, detail = str(exc).partition(": ")
        raise RuntimeError(
            f"Failed to clone repository '{repo_url}': {detail or str(exc)}"
        ) from exc

def sync_skill_manager(clone_dir: Path, project_root: Path, repo_root: Path, repo_url: str) -> None:
    manager_source_dir = clone_dir / "skills" / "skill-manager"
    manager_skill_file = manager_source_dir / "SKILL.md"
    if not manager_skill_file.is_file():
        return

    manager_target_dir = project_root / ".agents" / "skills" / "skill-manager"
    replace_directory(manager_source_dir, manager_target_dir)
    write_repo_info(manager_target_dir, repo_root, repo_url)


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
        replace_directory(remote_skill_dir, target_dir)

        repo_root = Path(__file__).resolve().parent.parent
        if skill_name == "skill-manager":
            write_repo_info(target_dir, repo_root, repo_url)
        else:
            sync_skill_manager(clone_dir, project_root, repo_root, repo_url)

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
