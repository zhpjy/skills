from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.lib.common import replace_directory, run_git, validate_skill_name, write_repo_info


def sync_local_skill_manager(
    project_root: Path,
    repo_root: Path,
    repo_url: str,
    pushed_skill_name: str,
    pushed_source_dir: Path,
) -> None:
    if pushed_skill_name == "skill-manager":
        manager_source_dir = pushed_source_dir
    else:
        manager_source_dir = repo_root / "skills" / "skill-manager"

    manager_skill_file = manager_source_dir / "SKILL.md"
    if not manager_skill_file.is_file():
        return

    manager_target_dir = project_root / ".agents" / "skills" / "skill-manager"
    replace_directory(manager_source_dir, manager_target_dir)
    write_repo_info(manager_target_dir, repo_root, repo_url)


def resolve_source_dir(skill_name: str, source: str | None) -> Path:
    if source is not None:
        return Path(source).expanduser().resolve()
    return (Path.cwd() / ".agents" / "skills" / skill_name).resolve()


def validate_source_dir(source_dir: Path) -> None:
    if not source_dir.is_dir():
        raise ValueError(f"source skill directory does not exist: {source_dir}")
    skill_file = source_dir / "SKILL.md"
    if not skill_file.is_file():
        raise ValueError(f"source skill directory is missing SKILL.md: {source_dir}")


def get_repo_root(script_path: Path) -> Path:
    result = run_git(["rev-parse", "--show-toplevel"], cwd=script_path.parent)
    return Path(result.stdout.strip()).resolve()


def get_origin_url(repo_root: Path) -> str:
    result = run_git(["remote", "get-url", "origin"], cwd=repo_root)
    return result.stdout.strip()


def has_staged_skill_changes(clone_dir: Path, skill_name: str) -> bool:
    result = run_git(
        ["diff", "--cached", "--name-only", "--", f"skills/{skill_name}"],
        cwd=clone_dir,
    )
    return bool(result.stdout.strip())


def push_skill(skill_name: str, source_dir: Path, script_path: Path) -> None:
    project_root = Path.cwd()
    repo_root = get_repo_root(script_path)
    origin_url = get_origin_url(repo_root)

    with tempfile.TemporaryDirectory(prefix="push-skill-") as temp_dir:
        clone_dir = Path(temp_dir) / "repo"
        run_git(["clone", "--depth=1", origin_url, str(clone_dir)], cwd=repo_root)

        target_dir = clone_dir / "skills" / skill_name
        replace_directory(source_dir, target_dir)

        run_git(["add", f"skills/{skill_name}"], cwd=clone_dir)
        if not has_staged_skill_changes(clone_dir, skill_name):
            sync_local_skill_manager(project_root, repo_root, origin_url, skill_name, source_dir)
            print(f"No changes for skill '{skill_name}'.")
            return

        run_git(["commit", "-m", f"Update skill: {skill_name}"], cwd=clone_dir)
        run_git(["push"], cwd=clone_dir)
        sync_local_skill_manager(project_root, repo_root, origin_url, skill_name, source_dir)
        print(f"Pushed skill '{skill_name}' to remote repository.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Push a local skill to this repository.")
    parser.add_argument("--skill", required=True, help="Skill name under skills/")
    parser.add_argument(
        "--source",
        help="Optional local skill directory. Defaults to .agents/skills/<skill-name> in the current project.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        validate_skill_name(args.skill)
        source_dir = resolve_source_dir(args.skill, args.source)
        validate_source_dir(source_dir)
        push_skill(args.skill, source_dir, Path(__file__).resolve())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
