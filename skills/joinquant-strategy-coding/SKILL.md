---
name: joinquant-strategy-coding
description: Use when需要编写、修改、调试、编译或回测聚宽 JoinQuant 策略 Python 代码，尤其是 strategies/ 下的策略文件、jqfactor 因子、多因子选股、定时调仓、下单、基准比较或远端 jqcli 验证。
---

# 聚宽策略编写

## 概览

这个 skill 用于编写真正能在聚宽编译、运行、回测的策略代码。本地 Python 测试只能验证纯函数和语法，最终仍要以聚宽远端编译作为门禁。

## 工作流

1. 先读现有策略和测试，理解已有风格。
2. 先确认用户资金量、交易费率、最低佣金、调仓频率、持股数量偏好和风险目标；如果没有给出，先简短询问，不要擅自默认。
3. 新建最小必要策略变体，不要覆盖已经跑通的基线策略，除非用户明确要求。
4. 为纯函数、因子权重、评分、风控和调仓逻辑补本地测试。
5. 运行本地语法和测试。
6. 用 `joinquant-trader` 上传或更新远端策略。
7. 先做一次远端编译门禁。
8. 编译通过后，再跑目标区间回测。
9. 回测时同时比较策略基准和用户关心的额外基准。

远端操作使用 `joinquant-trader`。本仓库通常从项目根目录执行：

```bash
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py <resource> <action> ...
```

如果仓库指令要求 `rtk`，所有 shell 命令前加 `rtk`。

## 文件位置

- 策略文件放在 `strategies/jq_<name>.py`
- 策略测试放在 `strategies/tests/test_<name>.py`
- 测试导入辅助使用 `strategies/tests/strategy_test_path.py`
- jqcli 等工具实现归 `.agents/skills/` 管，不要在仓库根目录重复创建工具包。

创建策略变体时，用清晰后缀区分，例如 `版本D`、`版本F`、`risk`。保留旧版本，方便横向比较。

## 聚宽运行时规则

写代码时按聚宽运行时约束来，而不是只按本地 Python：

- 避免 `from __future__ import annotations`。
- 优先使用 `order_target_value`，不要默认用 `order_target_percent`；有些聚宽运行时不会注入 `order_target_percent`。
- 策略运行时代码里如果项目已有 `_sum_values`，优先使用它，不要依赖内置 `sum()`；之前遇到过兼容性/全局污染问题。
- `get_price` 构建 DataFrame 逻辑时使用 `panel=False`。
- 对空 DataFrame、缺失因子、停牌、ST、退市名、涨跌停、缺失财务数据都要显式防护。
- 不要大改已经跑通的调度和下单链路。
- 让策略 helper 可以在本地导入测试，避免导入时执行依赖聚宽全局对象的逻辑。

## 策略骨架

使用聚宽常规生命周期：

```python
def initialize(context):
    set_benchmark("000300.XSHG")
    set_option("use_real_price", True)
    set_order_cost(OrderCost(
        close_tax=0.001,
        open_commission=0.0003,
        close_commission=0.0003,
        min_commission=5,
    ), type="stock")
    run_weekly(before_market_open, 1, time="before_open")
    run_weekly(rebalance, 1, time="open")

def before_market_open(context):
    # 计算候选股票和目标权重
    pass

def rebalance(context):
    # 使用 order_target_value 调整仓位
    pass
```

小资金账户要考虑 100 股整数手和最低佣金。比如 5 万资金、8 只股票时，要过滤掉 100 股一手价格相对单票目标金额过高的股票。

资金量和交易费用不能硬编码成固定假设。策略设计前要向用户确认：

- 初始资金
- 佣金费率，例如万三
- 最低佣金，例如 5 元
- 印花税和滑点假设
- 目标持股数量
- 周度、双周还是月度调仓

这些输入会直接影响持股数量、一手可买过滤、换手约束和回测结果解释。

## 因子代码

多因子策略建议采用稳定的行式数据构建方式：

- 用 `get_fundamentals` 拉基础财务和估值数据。
- 用 `jqfactor.get_factor_values` 拉可选因子。
- `jqfactor` 的 import 和查询都要包 `try/except`。
- `jqfactor` 不可用时提供保守 fallback，不能让整套策略直接失效。
- 因子打分前先 winsorize，再 standardize。
- 权重统一走 `_normalize_weights` 一类 helper。

代码中保留 API 因子名，文档和面向用户解释使用中文名称。

常用因子组：

- 收益/估值：`earnyild`、`predicted_earnings_to_price_ratio`、`btop`
- 现金流质量：`cfo_to_ev`、`cash_flow_to_price_ratio`
- 分红：`divyild`、`dividend_yield_v2`
- 盈利质量：`earnqlty`、`quality_v2`
- 动量/相对强弱：`momentum_6m`、`relative_strength_12m`、`relative_momentum`
- 风险控制：`lowvol`、低 `beta`、低残余波动、价格相对均值惩罚

不要假设防守因子越多越好。过度加大低 Beta、低残余波动、均值回归惩罚，可能让组合过度接近红利低波，收益明显塌缩。

## 调仓和风控

做周度或月度策略时：

- 可以每周检查，提高响应速度。
- 加最小调仓间隔，例如 14 天，减少换手。
- 保存 `last_rebalance_date`。
- 动态现金仓位只能作为风控，不要当主要收益来源。
- 买入前做趋势过滤和一手可买过滤。
- 卖出前检查停牌和跌停状态。

对于保守型用户，优先通过仓位、现金、趋势过滤降低 Beta，不要直接用强防守因子替代整个 alpha 模型。

## 远端编译和回测

策略改动后，先远端编译，不要直接跑长回测。

```bash
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py backtest compile \
  --strategy-id <id> \
  --capital 50000 \
  --frequency day

uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py backtest run \
  --strategy-id <id> \
  --start-date <start-date> \
  --end-date <end-date> \
  --capital 50000 \
  --frequency day
```

如果编译失败：

- 先读返回里的 `errors`。
- 本地修代码。
- 更新远端策略。
- 继续重新编译。

如果聚宽返回 `当前并行编译或回测数量最多2个`，等待后串行重试。不要继续并发提交。

编译通过后，再跑目标回测窗口。稳健性评估至少看：

- 近 1 年
- 从 `2024-01-01` 开始
- 短区间表现有希望时，再跑从 `2023-01-01` 开始的长区间

如果目标是同时跑赢沪深300和红利低波，比较：

- 策略收益
- `000300.XSHG` 的 `benchmark_return`
- 红利低波代理，例如直接指数不可用时用 `512890.XSHG`
- 最大回撤
- Sharpe/Sortino
- Beta
- 交易次数/换手率

如果新变体在近 1 年和 2024 起点都明显落后，不要继续消耗资源跑更长区间，除非用户明确要求。

## 评价纪律

不能只因为回撤低就推荐策略，要看完整取舍：

- 是否跑赢沪深300？
- 是否跑赢红利低波代理？
- 回撤是否更低或至少可接受？
- Beta 是否符合用户风险偏好？
- 在万三和最低佣金下，换手是否合理？
- 多个起点下表现是否稳定？

如果某个因子 IC 看起来不错，但组合收益变差，先按组合构建问题处理，不要直接判定因子无效。

## 本地验证

上传远端前先跑本地检查：

```bash
uv run python -m py_compile strategies/<strategy>.py
uv run python -m unittest discover -s strategies/tests -v
```

本地测试重点覆盖纯 helper：

- 权重归一化
- 调仓间隔
- 现金仓位
- 趋势/风险过滤
- 代表性样本的评分顺序
- 目标权重构建

本地测试不能证明聚宽兼容性。策略代码改动后，远端编译仍然是必需门禁。

## 常见错误

- 没有先远端编译，直接跑一年回测。
- 没有先问用户资金量、佣金、最低佣金和调仓频率，就默认套用某个账户假设。
- 凭记忆使用远端策略 ID；创建或更新后 ID 可能变化，要先 `strategy list` 确认。
- 使用聚宽不支持的直接指数代码；要用小基准策略或代理标的验证。
- 低 Beta、低残余波动、价格均值回归惩罚过重，导致收益塌缩。
- 小资金策略忽略 100 股整数手和最低佣金。
- 用户要求中文文档时，仍然只解释英文因子名。
- `factor performance` 返回 `null` 就放弃；`detail`、`ic`、极值股票列表仍可能提供有效证据。
