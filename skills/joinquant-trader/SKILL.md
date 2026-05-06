---
name: joinquant-trader
description: Use when需要让 AI 通过项目内 jqcli 操作聚宽策略、目录、回测和回测详情，或需要创建/修改/运行/评价 JoinQuant 量化策略。
---

# JoinQuant Trader

## Overview

这个 skill 使用项目内置 `jqcli` 操作聚宽。`jqcli` 面向 AI 自动化：所有命令输出 JSON，调用前会自动复用或刷新登录态。

## 配置

- 真实凭证放在执行目录的 `.env`，或用 `JQCLI_ENV_FILE=/path/to/.env` 指定。
- 不要把真实 `.env` 放进 skill 目录；skill 目录只保留 `.env.example`。
- `jqcli` 不会回退读取 `joinquant/.env`。

## 命令入口

从项目根目录优先使用：

```bash
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py <resource> <action> [args]
```

## 常用操作

```bash
# 登录状态
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py auth status

# 策略
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py strategy list
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py strategy get --id <strategy-id>
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py strategy create --name <name> --file <strategy.py>
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py strategy update-code --id <strategy-id> --file <strategy.py>
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py strategy rename --id <strategy-id> --name <new-name>
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py strategy delete --id <strategy-id> --confirm-delete

# 目录
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py directory list --parent-id 0
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py directory create --name <name> --parent-id 0
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py directory delete --id <directory-id> --parent-id 0 --confirm-delete

# 回测
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py backtest run --strategy-id <strategy-id> --start-date 2025-01-01 --end-date 2026-05-01
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py backtest detail --backtest-id <backtest-id>
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py backtest logs --backtest-id <backtest-id>
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py backtest errors --backtest-id <backtest-id>
```

## 安全边界

- 删除策略或目录必须显式传 `--confirm-delete`。
- 不要输出 `.env`、cookie、token、session 文件内容。
- 写策略前先读取远端策略，确认目标 `strategy-id` 正确。
- 回测评价优先用 `backtest detail`，需要原始明细时再调用 `stats/risk/positions/transactions/logs/errors`。

## 验证

`jqcli` 的单测随 skill 放在 `tests/` 中：

```bash
uv run python -m unittest discover -s .agents/skills/joinquant-trader/tests -v
```
