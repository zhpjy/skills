from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
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


def write_repo_info(skill_dir: Path, repo_root: Path, repo_url: str) -> None:
    repo_info = {
        "repo_root": str(repo_root),
        "repo_url": repo_url,
    }
    (skill_dir / "repo-info.json").write_text(
        json.dumps(repo_info, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def clone_repository(repo_url: str, clone_dir: Path) -> None:
    try:
        run_git(["clone", "--depth=1", repo_url, str(clone_dir)], cwd=Path.cwd())
    except RuntimeError as exc:
        _, _, detail = str(exc).partition(": ")
        raise RuntimeError(
            f"Failed to clone repository '{repo_url}': {detail or str(exc)}"
        ) from exc


def infer_repo_root(script_path: Path | None = None) -> Path:
    current_script = script_path or Path(__file__).resolve()
    return current_script.parent.parent


def infer_repo_url(repo_root: Path) -> str:
    return run_git(["remote", "get-url", "origin"], cwd=repo_root).stdout.strip()


def load_bundle(bundle_name: str, repo_root: Path) -> dict:
    bundle_path = repo_root / "bundles" / f"{bundle_name}.json"
    if not bundle_path.is_file():
        raise ValueError(f"Bundle '{bundle_name}' not found at {bundle_path}")
    return json.loads(bundle_path.read_text(encoding="utf-8"))


def resolve_bundle_skill_paths(
    bundle: dict,
    repo_root: Path,
) -> list[tuple[str, Path]]:
    resolved: list[tuple[str, Path]] = []
    for item in bundle.get("skills", []):
        source = item["source"]
        skill_name = item["path"]
        validate_skill_name(skill_name)

        if source == "local":
            skill_dir = repo_root / "skills" / skill_name
        elif source.startswith("vendor/"):
            vendor_name = source.partition("/")[2]
            if not vendor_name or "/" in vendor_name:
                raise ValueError(f"Unsupported bundle source '{source}'")
            skill_dir = repo_root / "vendor" / vendor_name / "skills" / skill_name
        else:
            raise ValueError(f"Unsupported bundle source '{source}'")

        resolved.append((skill_name, skill_dir))

    return resolved


def write_bundle_state(
    bundle_name: str,
    bundle: dict,
    skill_names: list[str],
    project_root: Path,
    repo_url: str,
) -> None:
    state = {
        "bundle": bundle_name,
        "agent": bundle.get("agent"),
        "repo_url": repo_url,
        "skills": skill_names,
    }
    state_path = project_root / ".agents" / "bundles" / f"{bundle_name}.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def sync_bundle(
    bundle_name: str,
    project_root: Path,
    repo_root: Path,
    repo_url: str,
) -> Path:
    bundle = load_bundle(bundle_name, repo_root)
    resolved_skills = resolve_bundle_skill_paths(bundle, repo_root)

    skills_root = project_root / ".agents" / "skills"
    installed_skill_names: list[str] = []
    for skill_name, source_dir in resolved_skills:
        if not (source_dir / "SKILL.md").is_file():
            raise ValueError(f"Skill '{skill_name}' not found at {source_dir}")
        replace_directory(source_dir, skills_root / skill_name)
        installed_skill_names.append(skill_name)

    manager_dir = skills_root / "skill-manager"
    if (manager_dir / "SKILL.md").is_file():
        write_repo_info(manager_dir, repo_root, repo_url)

    write_bundle_state(
        bundle_name=bundle_name,
        bundle=bundle,
        skill_names=installed_skill_names,
        project_root=project_root,
        repo_url=repo_url,
    )
    return skills_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sync a bundle of skills into the current project."
    )
    parser.add_argument("--repo", help="Git repository URL for remote script usage")
    parser.add_argument("--bundle", required=True, help="Bundle name under bundles/")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.repo:
            repo_url = args.repo
            with tempfile.TemporaryDirectory() as temp_dir:
                repo_root = Path(temp_dir) / "repo"
                clone_repository(repo_url, repo_root)
                sync_bundle(
                    bundle_name=args.bundle,
                    project_root=Path.cwd(),
                    repo_root=repo_root,
                    repo_url=repo_url,
                )
            return 0

        repo_root = infer_repo_root()
        repo_url = infer_repo_url(repo_root)
        sync_bundle(
            bundle_name=args.bundle,
            project_root=Path.cwd(),
            repo_root=repo_root,
            repo_url=repo_url,
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
