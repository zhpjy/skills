from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable
from uuid import uuid4


LOCAL_STATE_RELATIVE_PATH = Path(".agents") / ".local" / "skill-manager.json"


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


def replace_directory(
    source_dir: Path,
    target_dir: Path,
    *,
    symlinks: bool = False,
) -> Path:
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    staged_dir = target_dir.parent / f".{target_dir.name}.tmp-{uuid4().hex}"
    backup_dir = target_dir.parent / f".{target_dir.name}.bak-{uuid4().hex}"

    shutil.copytree(source_dir, staged_dir, symlinks=symlinks)

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
        shutil.rmtree(backup_dir, ignore_errors=True)

    return target_dir


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "GIT_TERMINAL_PROMPT": "0",
    }
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        raise RuntimeError(f"git {' '.join(args)} failed: {message}")
    return result


def _read_json_file(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _is_plausible_repo_root(path: Path) -> bool:
    return (
        (path / ".git").exists()
        or (path / "tools" / "push_skill.py").is_file()
        or (path / "skills" / "skill-manager" / "SKILL.md").is_file()
    )


def write_repo_info(skill_dir: Path, repo_url: str) -> None:
    repo_info = {
        "repo_url": repo_url,
    }
    (skill_dir / "repo-info.json").write_text(
        json.dumps(repo_info, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_local_repo_state(project_root: Path, repo_root: Path) -> None:
    state_path = project_root / LOCAL_STATE_RELATIVE_PATH
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps({"repo_root": str(repo_root)}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def resolve_local_repo_root(
    project_root: Path,
    *,
    explicit_repo_root: str | None = None,
    fallback_repo_root: Path | None = None,
) -> Path | None:
    candidates: list[Path] = []
    if explicit_repo_root:
        candidates.append(Path(explicit_repo_root).expanduser().resolve())

    env_repo_root = os.environ.get("SKILLS_REPO_ROOT")
    if env_repo_root:
        candidates.append(Path(env_repo_root).expanduser().resolve())

    state_repo_root = _read_json_file(project_root / LOCAL_STATE_RELATIVE_PATH).get("repo_root")
    if state_repo_root:
        candidates.append(Path(state_repo_root).expanduser().resolve())

    legacy_repo_root = _read_json_file(
        project_root / ".agents" / "skills" / "skill-manager" / "repo-info.json"
    ).get("repo_root")
    if legacy_repo_root:
        candidates.append(Path(legacy_repo_root).expanduser().resolve())

    if fallback_repo_root is not None:
        candidates.append(fallback_repo_root.resolve())

    for candidate in candidates:
        if _is_plausible_repo_root(candidate):
            return candidate
    return None


def clone_repository(repo_url: str, clone_dir: Path) -> None:
    try:
        run_git(["clone", "--depth=1", repo_url, str(clone_dir)], cwd=Path.cwd())
    except RuntimeError as exc:
        _, _, detail = str(exc).partition(": ")
        raise RuntimeError(
            f"Failed to clone repository '{repo_url}': {detail or str(exc)}"
        ) from exc


def sync_skill_manager(
    clone_dir: Path,
    project_root: Path,
    repo_root: Path | None,
    repo_url: str,
) -> None:
    manager_source_dir = clone_dir / "skills" / "skill-manager"
    manager_skill_file = manager_source_dir / "SKILL.md"
    if not manager_skill_file.is_file():
        return

    manager_target_dir = project_root / ".agents" / "skills" / "skill-manager"
    replace_directory(manager_source_dir, manager_target_dir)
    write_repo_info(manager_target_dir, repo_url)
    if repo_root is not None:
        write_local_repo_state(project_root, repo_root)


def install_skill(
    repo_url: str,
    skill_name: str,
    project_root: Path,
    local_repo_root: Path | None = None,
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

        resolved_local_repo_root = local_repo_root or resolve_local_repo_root(project_root)
        if skill_name == "skill-manager":
            write_repo_info(target_dir, repo_url)
            if resolved_local_repo_root is not None:
                write_local_repo_state(project_root, resolved_local_repo_root)
        else:
            sync_skill_manager(clone_dir, project_root, resolved_local_repo_root, repo_url)

        return target_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install a skill from a git repository.")
    parser.add_argument("--repo", required=True, help="Git repository URL")
    parser.add_argument("--repo-root", help="Optional local skills repository root to persist as local state")
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
            local_repo_root=resolve_local_repo_root(
                Path.cwd(),
                explicit_repo_root=args.repo_root,
            ),
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
