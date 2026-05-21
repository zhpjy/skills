import argparse
import json
from pathlib import Path
import re
import shutil
import sys


ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
VERSION_ID_RE = re.compile(r"^r\d{2}-(main|exp-[a-z])$")
BRANCH_TYPE_RE = re.compile(r"^(main|exp-[a-z])$")
PLACEHOLDER_RE = re.compile(r"{{([a-zA-Z_][a-zA-Z0-9_]*)}}")
INVALID_TOPIC_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
README_REMOTE_DIR_RE = re.compile(r"^- 聚宽远端目录：(.+)$", re.MULTILINE)
README_STATUS_LINE_RE = re.compile(r"^- {label}：.*$", re.MULTILINE)


def _render_template(template_name: str, context: dict[str, str]) -> str:
    template_path = ASSETS_DIR / template_name
    content = template_path.read_text(encoding="utf-8")
    placeholders = set(PLACEHOLDER_RE.findall(content))
    extra_keys = set(context) - placeholders
    if extra_keys:
        raise ValueError(
            f"unused template context keys: {', '.join(sorted(extra_keys))}"
        )
    missing_keys = placeholders - set(context)
    if missing_keys:
        raise ValueError(
            f"missing template context keys: {', '.join(sorted(missing_keys))}"
        )
    for key, value in context.items():
        content = content.replace(f"{{{{{key}}}}}", value)
    remaining = PLACEHOLDER_RE.findall(content)
    if remaining:
        raise ValueError(
            f"unfilled template placeholders: {', '.join(sorted(set(remaining)))}"
        )
    return content


def _validate_version_id(version_id: str) -> None:
    if not VERSION_ID_RE.match(version_id):
        raise ValueError(f"invalid version id: {version_id}")


def _validate_branch_type(version_id: str, branch_type: str) -> None:
    if not BRANCH_TYPE_RE.match(branch_type):
        raise ValueError(f"invalid branch type: {branch_type}")
    version_branch = version_id.split("-", 1)[1]
    if version_branch != branch_type:
        raise ValueError(
            f"branch type {branch_type} does not match version id {version_id}"
        )


def _sanitize_topic(topic: str) -> str:
    sanitized = INVALID_TOPIC_CHARS_RE.sub("-", topic)
    sanitized = re.sub(r"-{2,}", "-", sanitized).strip(" .-")
    if not sanitized:
        raise ValueError("topic must contain at least one valid character")
    return sanitized


def _validate_package_dir(package_dir: Path) -> None:
    if not package_dir.is_dir():
        raise ValueError(f"invalid package directory: {package_dir}")
    if not (package_dir / "README.md").is_file():
        raise ValueError(
            f"invalid package directory: missing README.md in {package_dir}"
        )
    if not (package_dir / "PATH.md").is_file():
        raise ValueError(
            f"invalid package directory: missing PATH.md in {package_dir}"
        )
    if not (package_dir / "candidate").is_dir():
        raise ValueError(
            f"invalid package directory: missing candidate/ in {package_dir}"
        )
    if not (package_dir / "versions").is_dir():
        raise ValueError(
            f"invalid package directory: missing versions/ in {package_dir}"
        )


def _validate_parent_version(
    package_dir: Path,
    version_id: str,
    parent_version: str | None,
    branch_type: str,
) -> None:
    if not branch_type.startswith("exp-"):
        return
    if not parent_version:
        raise ValueError(f"experimental version {version_id} requires parent_version")
    parent_dir = package_dir / "versions" / parent_version
    if not parent_dir.is_dir():
        raise ValueError(f"parent version directory does not exist: {parent_version}")


def _resolve_remote_directory_name(
    package_dir: Path,
    remote_directory_name: str,
) -> str:
    readme_path = package_dir / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    match = README_REMOTE_DIR_RE.search(readme)
    if not match:
        raise ValueError("README.md missing 聚宽远端目录 entry")
    recorded_name = match.group(1).strip()
    if recorded_name in {"待创建", "未确定"}:
        if remote_directory_name != package_dir.name:
            raise ValueError(
                "remote_directory_name must match the research package directory name on first binding"
            )
        return remote_directory_name
    if recorded_name != remote_directory_name:
        raise ValueError(
            "remote_directory_name must match README.md recorded remote directory"
        )
    return recorded_name


def _validate_source_file_in_candidate_workspace(
    package_dir: Path,
    source_file: Path,
) -> None:
    candidate_dir = (package_dir / "candidate").resolve()
    resolved_source = source_file.resolve()
    if not resolved_source.is_relative_to(candidate_dir):
        raise ValueError(
            "source_file must be inside the research package candidate/ workspace"
        )


def _replace_readme_status_line(readme: str, label: str, value: str) -> str:
    pattern = re.compile(
        README_STATUS_LINE_RE.pattern.format(label=re.escape(label)),
        re.MULTILINE,
    )
    updated, count = pattern.subn(f"- {label}：{value}", readme, count=1)
    if count != 1:
        raise ValueError(f"README.md missing {label} status line")
    return updated


def _append_readme_version_row(
    readme: str,
    version_id: str,
    branch_type: str,
    parent_version: str | None,
) -> str:
    marker = "| --- | --- | --- | --- | --- | --- |"
    row = (
        f"| {version_id} | {branch_type} | {parent_version or '-'} | "
        "待补充 | pending | "
        f"{'首个主线版本' if branch_type == 'main' and parent_version is None else '-'} |"
    )
    if row in readme:
        return readme
    if marker not in readme:
        raise ValueError("README.md missing version table header")
    return readme.replace(marker, f"{marker}\n{row}", 1)


def _sync_readme_after_init_version(
    package_dir: Path,
    version_id: str,
    branch_type: str,
    parent_version: str | None,
    remote_directory_name: str,
) -> None:
    readme_path = package_dir / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    readme = _replace_readme_status_line(readme, "聚宽远端目录", remote_directory_name)
    if branch_type == "main":
        readme = _replace_readme_status_line(readme, "当前主线版本", version_id)
        if "- 当前最优版本：未确定" in readme:
            readme = _replace_readme_status_line(readme, "当前最优版本", version_id)
    readme = _append_readme_version_row(readme, version_id, branch_type, parent_version)
    if "未确定" not in readme and "待创建" not in readme:
        readme = _replace_readme_status_line(
            readme,
            "下一步",
            "补充最新正式版本的真实远端信息与回测结论",
        )
    readme_path.write_text(readme, encoding="utf-8")


def init_package(root: Path, research_date: str, topic: str) -> Path:
    research_name = f"{research_date}-{_sanitize_topic(topic)}"
    package_dir = root / research_name
    package_dir.mkdir(parents=True, exist_ok=False)
    (package_dir / "candidate").mkdir()
    (package_dir / "versions").mkdir()

    readme_context = {
        "research_date": research_date,
        "topic": topic,
        "research_name": research_name,
    }
    path_context = {
        "research_date": research_date,
        "research_name": research_name,
    }
    (package_dir / "README.md").write_text(
        _render_template("README.md.tmpl", readme_context),
        encoding="utf-8",
    )
    (package_dir / "PATH.md").write_text(
        _render_template("PATH.md.tmpl", path_context),
        encoding="utf-8",
    )
    return package_dir


def init_version(
    package_dir: Path,
    version_id: str,
    source_file: Path,
    parent_version: str | None,
    branch_type: str,
    remote_directory_name: str,
) -> Path:
    _validate_version_id(version_id)
    _validate_branch_type(version_id, branch_type)
    _validate_package_dir(package_dir)
    _validate_parent_version(package_dir, version_id, parent_version, branch_type)
    remote_directory_name = _resolve_remote_directory_name(
        package_dir,
        remote_directory_name,
    )
    if not source_file.exists():
        raise FileNotFoundError(source_file)
    if not source_file.is_file():
        raise ValueError(f"source file is not a file: {source_file}")
    _validate_source_file_in_candidate_workspace(package_dir, source_file)

    version_dir = package_dir / "versions" / version_id
    version_dir.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(source_file, version_dir / "strategy.py")

    context = {
        "version_id": version_id,
        "parent_version": parent_version or "无",
        "branch_type": branch_type,
        "remote_directory_name": remote_directory_name,
    }
    (version_dir / "result.md").write_text(
        _render_template("result.md.tmpl", context),
        encoding="utf-8",
    )

    meta = {
        "version_id": version_id,
        "parent_version": parent_version,
        "branch_type": branch_type,
        "remote_directory_name": remote_directory_name,
        "remote_directory_id": None,
        "remote_strategy_name": None,
        "remote_strategy_id": None,
        "compile_status": "pending",
        "latest_backtest_id": None,
        "backtest_start_date": None,
        "backtest_end_date": None,
        "metrics_summary": {},
    }
    (version_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _sync_readme_after_init_version(
        package_dir=package_dir,
        version_id=version_id,
        branch_type=branch_type,
        parent_version=parent_version,
        remote_directory_name=remote_directory_name,
    )
    return version_dir


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_package_parser = subparsers.add_parser("init-package")
    init_package_parser.add_argument("--root", required=True)
    init_package_parser.add_argument("--date", required=True)
    init_package_parser.add_argument("--topic", required=True)

    init_version_parser = subparsers.add_parser("init-version")
    init_version_parser.add_argument("--package-dir", required=True)
    init_version_parser.add_argument("--version-id", required=True)
    init_version_parser.add_argument("--source-file", required=True)
    init_version_parser.add_argument("--parent-version")
    init_version_parser.add_argument("--branch-type", required=True)
    init_version_parser.add_argument("--remote-directory-name", required=True)

    args = parser.parse_args()
    if args.command == "init-package":
        init_package(
            root=Path(args.root),
            research_date=args.date,
            topic=args.topic,
        )
        return 0

    init_version(
        package_dir=Path(args.package_dir),
        version_id=args.version_id,
        source_file=Path(args.source_file),
        parent_version=args.parent_version,
        branch_type=args.branch_type,
        remote_directory_name=args.remote_directory_name,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
