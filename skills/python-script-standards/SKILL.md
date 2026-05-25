---
name: python-script-standards
description: Use when creating, modifying, reviewing, or running Python scripts, one-off automation, CLI utilities, data processing helpers, repository maintenance scripts, or small ETL/debug tools. Enforces uv-based execution, PEP 723 inline dependency metadata for simple scripts, project-level dependency management for complex Python projects, Chinese comments for the main workflow, and practical script quality checks.
---

# Python Script Standards

## Core Rules

- Execute Python through `uv`. Do not tell the user to run `python script.py`, `pip install ...`, or ad hoc virtualenv commands when `uv` can handle it.
- For simple standalone scripts with few dependencies, use PEP 723 inline metadata in the script.
- For complex projects, use the repository's existing dependency system; if creating a new project, prefer `pyproject.toml` plus `uv.lock`.
- Add Chinese comments for the main workflow. Comment major process blocks and non-obvious decisions, not every line.
- Preserve existing repository conventions when they are stricter or more specific than this skill.

## Dependency Choice

Use PEP 723 when the script is mostly self-contained:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests>=2.32",
# ]
# ///
```

Run it with:

```bash
uv run path/to/script.py
```

Use project dependencies instead when any of these are true:

- The code spans multiple modules or packages.
- There are many dependencies, native/system dependencies, or dependency groups.
- The script shares dependencies with tests, application code, or CI.
- The repository already has `pyproject.toml`, `uv.lock`, or a clear package layout.
- The work needs repeatable environments beyond one script.

For project mode, prefer:

```bash
uv sync
uv run path/to/script.py
uv run pytest
```

## Script Structure

For new scripts, prefer this shape:

```python
from __future__ import annotations

import argparse
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # 主流程：读取输入并完成基础校验

    # 主流程：执行核心处理逻辑

    # 主流程：写出结果并记录关键状态
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Adapt this shape to the repository style, but keep a clear `main()` boundary and `if __name__ == "__main__"` guard unless the file is intentionally import-only.

## Chinese Comment Standard

Add concise Chinese comments before major blocks such as:

- 参数解析、配置读取、环境变量读取
- 输入校验、路径解析、权限或前置条件检查
- 外部接口调用、数据库查询、文件扫描
- 数据清洗、转换、聚合、匹配
- 写文件、上传、删除、发送消息等有副作用的操作
- 异常处理、重试、回滚、临时文件清理

Good:

```python
# 主流程：按任务日期过滤输入文件，避免处理历史归档
files = [path for path in input_dir.iterdir() if should_process(path, args.biz_date)]
```

Avoid noisy comments:

```python
# 遍历文件
for file in files:
    ...
```

## Quality Checks

When writing or changing a script, check the following:

- Use `pathlib.Path` for filesystem paths unless an API requires strings.
- Use `logging` for operational output; reserve `print` for intentional command output.
- Use `argparse` for CLI parameters; avoid hard-coded local paths, dates, tokens, and accounts.
- Read and write text with explicit `encoding="utf-8"` when practical.
- Keep credentials in environment variables, `.env` files, or existing secret mechanisms; never commit real secrets.
- Make side effects explicit in names, logs, flags, or confirmation text.
- Prefer idempotent behavior for maintenance/data scripts; add `--dry-run` when destructive or broad operations are possible.
- Fail with actionable error messages and non-zero exit codes; do not silently swallow broad exceptions.
- Keep reusable logic importable and testable outside the CLI wrapper.

## Env Files and Secrets

For scripts that need local secrets or private configuration, prefer `.env` files loaded by `python-dotenv`.

For a simple standalone script, add it to PEP 723 metadata:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "python-dotenv>=1.0",
# ]
# ///
```

Use it near the start of `main()`:

```python
from dotenv import load_dotenv


def main() -> int:
    # 主流程：加载本地环境变量文件，避免把敏感信息写进代码
    load_dotenv()
    ...
```

For project mode, add the dependency through `uv`:

```bash
uv add python-dotenv
```

When introducing `.env` support:

- Add `.env` to `.gitignore` if it is not already ignored.
- Add `.env.example` only with placeholder values when users need a template.
- Allow an explicit `--env-file` argument when the script may run against multiple environments.
- Read secrets with `os.environ[...]` when required and fail fast if missing; use `os.getenv(...)` only for optional values.
- Never log secret values or derived tokens.

## Verification

Use `uv` for verification commands:

```bash
uv run path/to/script.py --help
uv run path/to/script.py <safe sample args>
```

If the repository already has checks, run them through `uv`:

```bash
uv run pytest
uv run ruff check .
uv run mypy .
```

Only claim completion after at least one relevant `uv run ...` command has been executed or after clearly stating why verification could not be run.
