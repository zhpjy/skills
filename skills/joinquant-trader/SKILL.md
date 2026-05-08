---
name: joinquant-trader
description: Use when需要让 AI 通过项目内 jqcli 操作聚宽策略、目录、回测和回测详情，或需要创建/修改/运行/评价 JoinQuant 量化策略。
---

# JoinQuant Trader

## Overview

这个 skill 使用项目内置 `jqcli` 操作聚宽。`jqcli` 面向 AI 自动化：所有命令输出 JSON，调用前会自动复用或刷新登录态。

高体积查询命令默认返回摘要，减少 token 消耗；只有显式传 `--full` 时才返回完整 payload。

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
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py strategy list --folder-id <folder-id>
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py strategy get --id <strategy-id>
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py strategy create --name <name> --file <strategy.py>
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py strategy create --name <name> --file <strategy.py> --folder-id <folder-id>
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py strategy update-code --id <strategy-id> --file <strategy.py>
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py strategy rename --id <strategy-id> --name <new-name>
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py strategy delete --id <strategy-id> --confirm-delete

# 目录
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py directory list --parent-id 0
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py directory create --name <name> --parent-id 0
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py directory delete --id <directory-id> --parent-id 0 --confirm-delete

# 回测
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py backtest compile --strategy-id <strategy-id> --start-date 2025-01-01 --end-date 2026-05-01
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py backtest run --strategy-id <strategy-id> --start-date 2025-01-01 --end-date 2026-05-01
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py backtest detail --backtest-id <backtest-id>
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py backtest logs --backtest-id <backtest-id>
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py backtest errors --backtest-id <backtest-id>
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py backtest logs --backtest-id <backtest-id> --full
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py backtest positions --backtest-id <backtest-id> --full

# 因子看板
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py factor list --category-id 0 --universe-type hs300 --time-range 3y --commision-fee 8 --skip-paused 0
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py factor detail --id <factor-id> --universe-type hs300 --time-range 3y --commision-fee 8 --skip-paused 0
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py factor performance --id <factor-id> --universe-type zz500 --time-range 1y --commision-fee 0 --skip-paused 1
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py factor daily-stats --id <factor-id> --side long --universe-type zz500 --time-range 1y --commision-fee 0 --skip-paused 1
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py factor ic --id <factor-id> --universe-type zz500 --time-range 1y --skip-paused 1
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py factor turnovers --id <factor-id> --side long --universe-type zz500 --time-range 1y --commision-fee 0 --skip-paused 1
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py factor stocks --id <factor-id> --universe-type zz500
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py factor detail --id <factor-id> --universe-type zz500 --full
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py factor stocks --id <factor-id> --universe-type zz500 --full
```

## 因子工作流

- 常规查询直接用 `factor list` 和 `factor detail`，不要每次都先查元数据。
- `factor list`、`factor detail`、`factor stocks` 默认只返回摘要；只有需要完整原始结果时才加 `--full`。
- 只有当用户要查看可选参数、按分类查找、或参数校验失败时，才调用 `factor settings` / `factor categories`。
- 默认筛选参数可直接使用：`category-id=0`、`universe-type=zz500`、`time-range=3y`、`commision-fee=0`、`skip-paused=1`。
- `factor detail` 默认只聚合轻量结果：基础信息、绩效摘要、极值股票列表。需要完整曲线时再加 `--include-series`，或分别调用 `daily-stats`、`ic`、`turnovers`。
- 对因子排序或初筛时，优先看 `annual_ex_return_1q`、`sharpe_1q`、`max_drawdown_1q`、`ic_mean`、`ir`、`good_ic`、`turnover_mean_1q`，并说明筛选参数。

## 编译与回测工作流

- 目录内创建策略时，使用 `strategy create --folder-id <folder-id>`；这个参数会按 HAR 观察透传到 `/algorithm/index/new?fId=...`。
- 修改策略后，先调用 `backtest compile`，不要直接跑完整回测。
- 如果 `compiled=false`，读取返回里的 `errors`，修改代码后用 `strategy update-code` 写回，再重复 `backtest compile`。
- 只有 `compiled=true` 后才执行 `backtest run`。
- `backtest run` 自身也会先执行一次编译门禁；编译失败时会返回 `backtest_id=null` 和 `compile.errors`，不会发起正式回测。
- 编译接口来自 HAR 观察到的 `POST /algorithm/index/build?ajax=1`，其中 `backtest[type]=1`；正式回测仍使用 `backtest[type]=0`。

## 安全边界

- 删除策略或目录必须显式传 `--confirm-delete`。
- 不要输出 `.env`、cookie、token、session 文件内容。
- 写策略前先读取远端策略，确认目标 `strategy-id` 正确。
- 回测评价优先用 `backtest detail`，需要原始明细时再调用 `stats/risk/positions/transactions/logs/errors`。
- `backtest stats/risk/positions/transactions/logs/errors` 默认返回摘要；只有在排查明细时才加 `--full`。
- 因子大曲线输出可能很长，除非用户要求画图或时间序列分析，否则不要默认拉取或完整展示。

## 验证

`jqcli` 的单测随 skill 放在 `tests/` 中：

```bash
uv run python -m unittest discover -s .agents/skills/joinquant-trader/tests -v
```
