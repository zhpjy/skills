from __future__ import annotations

import argparse
import filecmp
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


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


def directories_equal(left: Path, right: Path) -> bool:
    comparison = filecmp.dircmp(left, right)
    if comparison.left_only or comparison.right_only or comparison.funny_files:
        return False
    _, mismatched, errors = filecmp.cmpfiles(
        left,
        right,
        comparison.common_files,
        shallow=False,
    )
    if mismatched or errors:
        return False
    return all(
        directories_equal(left / common_dir, right / common_dir)
        for common_dir in comparison.common_dirs
    )


def push_skill(skill_name: str, source_dir: Path, script_path: Path) -> None:
    repo_root = get_repo_root(script_path)
    origin_url = get_origin_url(repo_root)

    with tempfile.TemporaryDirectory(prefix="push-skill-") as temp_dir:
        clone_dir = Path(temp_dir) / "repo"
        run_git(["clone", "--depth=1", origin_url, str(clone_dir)], cwd=repo_root)

        target_dir = clone_dir / "skills" / skill_name
        if target_dir.exists() and directories_equal(source_dir, target_dir):
            print(f"No changes for skill '{skill_name}'.")
            return

        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_dir, target_dir)

        run_git(["add", f"skills/{skill_name}"], cwd=clone_dir)
        run_git(["commit", "-m", f"Update skill: {skill_name}"], cwd=clone_dir)
        run_git(["push"], cwd=clone_dir)
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
