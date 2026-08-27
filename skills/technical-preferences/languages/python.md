# Python 语言规范

本文件是 `technical-preferences` 的 Python 语言规范。Python 运行时由 `mise` 管理，Python 包依赖和脚本执行由 `uv` 管理。

## 依赖模式

脚本自包含、依赖较少且不属于多模块项目时，使用 PEP 723 内联依赖元数据：

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests>=2.32",
# ]
# ///
```

通过 `mise` 执行：

```bash
mise exec -- uv run path/to/script.py
```

满足以下任一条件时，使用项目依赖管理，而不是脚本内联依赖：

- 代码跨越多个模块或包。
- 依赖较多，包含原生依赖、系统依赖或依赖组。
- 脚本与测试、应用代码或 CI 共享依赖。
- 仓库已有 `pyproject.toml`、`uv.lock` 或清晰的包布局。
- 工作需要长期可复现的开发、测试或 CI 环境。

新建项目优先使用 `pyproject.toml` 和 `uv.lock`：

```bash
mise exec -- uv sync
mise exec -- uv run path/to/script.py
mise exec -- uv run pytest
```

在 `mise.toml` 中让 `uv` 使用 mise 管理的 Python：

```toml
[tools]
python = "3.12"

[env]
UV_PYTHON = { value = "{{ tools.python.path }}", tools = true }
```

已有项目如果使用其他依赖系统，先遵循该项目的系统，不要无依据迁移到 uv。

## 脚本结构

新脚本优先保留清晰的 `main()` 边界和模块入口保护：

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

根据仓库风格调整结构；明确设计为纯导入模块时，可以不添加 CLI 入口。

## 可维护性与安全性

编写或修改 Python 脚本时逐项检查：

- 文件路径使用 `pathlib.Path`，除非外部 API 要求字符串。
- 运维状态使用 `logging`；只有刻意作为命令结果输出时才使用 `print`。
- CLI 参数使用 `argparse`；不要硬编码本地路径、日期、token、账号或环境地址。
- 读写文本时，在适用场景显式使用 `encoding="utf-8"`。
- 凭据通过 mise 的 `.env` 加载或使用既有 secret 机制，绝不提交真实密钥，也不记录密钥或派生 token。
- 让副作用体现在函数名、日志、参数或确认信息中。
- 维护和数据脚本优先幂等；可能进行破坏性或大范围操作时提供 `--dry-run`。
- 失败时给出可执行的错误信息并返回非零退出码；不要静默吞掉宽泛异常。
- 将可复用逻辑与 CLI 包装分开，使其可以被导入和测试。

如果代码必须脱离 `mise` 在运行时自行加载 `.env`，才使用 `python-dotenv`；在已由 mise 注入环境变量的流程中不要重复加载。使用 `python-dotenv` 时，独立脚本将其写入 PEP 723 元数据，项目模式通过项目依赖管理添加。

## 验证

根据项目已有入口执行最小但相关的验证：

```bash
mise exec -- uv run path/to/script.py --help
mise exec -- uv run path/to/script.py <safe-sample-args>
mise exec -- uv run pytest
mise exec -- uv run ruff check .
mise exec -- uv run mypy .
```

如果仓库定义了 `mise` task，优先使用对应的 `mise run <task>`。只有至少执行了一条相关验证命令，或明确说明为什么无法执行，才能宣称工作完成。
