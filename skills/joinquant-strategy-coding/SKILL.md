---
name: joinquant-strategy-coding
description: Use when需要编写、修改、调试、编译或回测聚宽 JoinQuant 策略 Python 代码，且策略默认需要满足聚宽运行时兼容性、交易成本建模和实盘准备约束。
---

# 聚宽策略编写

## 概览

这个 skill 用于编写真正能在聚宽编译、运行、回测，并默认按实盘约束设计的策略代码。

本 skill 的底线不是“回测能跑”，而是：

- 默认防未来函数
- 默认使用真实价格
- 显式建模手续费、最低佣金和滑点
- 显式处理整数手、停牌、涨跌停和缺失数据
- 本地测试后仍必须先过聚宽远端短区间编译，再按短到长递进回测

如果只需要查看实盘准备清单或回测评价口径，按需读取：

- `references/live-trading-checklist.md`
- `references/backtest-evaluation.md`

## 与通用 superpowers 的边界

在本仓库里，只要任务主体是“编写、修改、调试、编译或回测聚宽策略代码”，本 skill 就是主流程；如果通用 superpowers skill 的默认动作与这里的领域门禁冲突，以本 skill 为准。

- 不要求每次策略小改动都先走 `superpowers:brainstorming -> spec -> plan`。只有在做策略框架重构、跨策略研究流程重设计、或会明显改变既有策略族结构时，才补这套设计流程。
- 不要求把 `superpowers:test-driven-development` 机械套到整个 JoinQuant 生命周期。TDD 重点用于纯 helper、评分函数、权重归一化、风控判定、调仓约束等可在本地稳定验证的逻辑。
- 本地 failing test 只能证明局部行为，不等价于聚宽运行时兼容性；远端短区间编译仍然是策略代码改动后的首要真实性门禁。
- `superpowers:systematic-debugging`、`superpowers:verification-before-completion`、`superpowers:requesting-code-review` 这类通用 skill 仍然推荐保留，因为它们通常补强的是排错纪律、验证纪律和审查纪律，而不是替代领域流程。
- 如果用户或项目文档已明确给出更高优先级约束，继续按用户或项目文档执行。

## 工作流

1. 先读现有策略和测试，理解已有风格与已跑通链路。
2. 先确认账户输入：初始资金、佣金、最低佣金、印花税、滑点、调仓频率、目标持股数量、风险目标。
3. 如果用户没有给出这些输入，先简短询问；不要擅自默认成某个常见账户。
4. 新建最小必要策略变体，不要覆盖已经跑通的基线策略，除非用户明确要求。
5. 先把实盘默认约束写进策略，再实现因子、选股、调仓和风控逻辑。
6. 为纯函数、评分、风控和调仓逻辑补本地测试。
7. 运行本地语法和测试。
8. 用 `joinquant-trader` 上传或更新远端策略。
9. 先做远端短区间编译，通过后先跑短区间回测，再根据结果决定是否逐级扩大到 6 个月、1 年、3 年等更长区间。

远端操作使用 `joinquant-trader`。本仓库通常从项目根目录执行：

```bash
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py <resource> <action> ...
```

## 文件位置

- 如果当前任务属于某个 `joinquant/research/YYYYMMDD-研究主题/` 研究包，候选策略文件必须放在该研究包的 `candidate/` 内，例如 `candidate/strategy.py`；候选测试也放在同一 `candidate/` 内，例如 `candidate/test_strategy.py`
- 只有没有研究包上下文、或者用户明确要求维护长期策略库时，策略文件才放在 `strategies/jq_<name>.py`
- 只有没有研究包上下文、或者用户明确要求维护长期策略库时，策略测试才放在 `strategies/tests/test_<name>.py`
- 测试导入辅助使用 `strategies/tests/strategy_test_path.py`
- jqcli 等工具实现归 `.agents/skills/` 管，不要在仓库根目录重复创建工具包

创建策略变体时，用清晰后缀区分，例如 `版本D`、`版本F`、`risk`。保留旧版本，方便横向比较。

## 实盘默认约束

所有策略默认都要考虑以下事项；这些不是可选优化，而是基本要求：

- 必开 `set_option("avoid_future_data", True)`。
- 默认开启 `set_option("use_real_price", True)`。
- 必须显式设置手续费、最低佣金、印花税和滑点，不要依赖平台默认值。
- 小资金账户必须考虑 100 股整数手、最低佣金和最小成交额。
- 买入前必须检查停牌、ST、退市名、涨停、缺失行情和现金是否足够。
- 卖出前必须检查停牌、跌停和 `closeable_amount`，避免当天买入当天卖出。
- 排序、打分和调仓逻辑必须对空 DataFrame、缺失因子、缺失财务数据和异常值显式防护。
- 不要把未来可得信息混入当期决策，例如用未来财报披露结果、未来复权信息或错误的日期对齐。
- 不要只按理想价格假设成交；策略说明和回测解释里要体现滑点、交易成本和流动性限制。
- 调仓逻辑要能处理“目标仓位算出来了，但因为现金、整数手、停牌或涨跌停而无法完全成交”的情况。

更完整的清单见 `references/live-trading-checklist.md`。

## 聚宽运行时规则

写代码时按聚宽运行时约束来，而不是只按本地 Python：

- 避免 `from __future__ import annotations`。
- 优先使用 `order_target_value`，不要默认用 `order_target_percent`；有些聚宽运行时不会注入 `order_target_percent`。
- 策略运行时代码里如果项目已有 `_sum_values`，优先使用它，不要依赖内置 `sum()`；之前遇到过兼容性/全局污染问题。
- `get_price` 构建 DataFrame 逻辑时使用 `panel=False`。
- 不要大改已经跑通的调度和下单链路。
- 让策略 helper 可以在本地导入测试，避免导入时执行依赖聚宽全局对象的逻辑。
- 本地测试只能证明语法和纯函数行为，不能替代聚宽远端编译。

## 策略骨架

使用聚宽常规生命周期：

```python
def initialize(context):
    set_benchmark("000300.XSHG")
    set_option("avoid_future_data", True)
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

如果账户较小，调仓代码里要先过滤“一手就明显超过单票目标金额”的标的，否则策略会在回测里看起来能买，实盘里却长期空转。

## 因子和数据处理

多因子或基本面策略建议采用稳定的数据构建方式：

- 用 `get_fundamentals` 拉基础财务和估值数据。
- 用 `jqfactor.get_factor_values` 拉可选因子。
- `jqfactor` 的 import 和查询都要包 `try/except`。
- `jqfactor` 不可用时提供保守 fallback，不能让整套策略直接失效。
- 因子打分前先 winsorize，再 standardize。
- 权重统一走 `_normalize_weights` 一类 helper。
- 对缺失值、极端值、样本过少和字段为空显式处理，不要直接排序后下单。

代码中保留 API 因子名，文档和面向用户解释使用中文名称。

## 调仓、执行和风控

所有策略都应默认考虑以下执行与风控约束：

- 用最小调仓间隔控制换手，例如保存 `last_rebalance_date`。
- 设最小调仓金额，避免为了很小的偏差反复交易。
- 买入前做趋势过滤、一手可买过滤和现金检查。
- 卖出前检查停牌、跌停和可卖数量。
- 仓位控制优先通过持股数量、单票权重、现金仓位和调仓频率来实现。
- 不要把动态现金仓位当作主要收益来源；它首先是风控工具。
- 对流动性差的股票或 ETF，要加成交额、成交量或冲击成本约束。
- 回测解释里要说明策略对资金规模、换手和交易成本是否敏感。

## 远端编译和回测

策略改动后，先远端编译，不要直接跑长回测。正式回测默认采用“短区间先行、通过后再扩区间”的递进方式。

- `backtest compile` 使用 `joinquant-trader` 内部维护的固定短区间编译窗口，命令里不需要额外传 `--start-date` 和 `--end-date`。
- `backtest run` 使用用户显式传入的 `--start-date` 和 `--end-date` 发起正式回测；日期格式必须是 `YYYY-MM-DD`，且 `start-date` 不能晚于 `end-date`。
- 如果用户没有给区间，默认按 `6个月 -> 1年 -> 3年` 递进；上一档结果还没有基本解释清楚前，不进入下一档。
- 如果用户一开始就要求 1 年或 3 年，也先补一次约 6 个月短回测做烟雾测试；只有在收益、回撤、换手和交易成本口径没有明显异常时，才扩到更长区间。
- 每扩大一档，都要先判断前一档是否值得继续：是否真实跑赢基准、回撤是否可接受、换手和费用是否失真、是否暴露出容量或风格集中问题。

```bash
uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py backtest compile \
  --strategy-id <id> \
  --capital <capital> \
  --frequency day

uv run python .agents/skills/joinquant-trader/scripts/jqcli_tool.py backtest run \
  --strategy-id <id> \
  --start-date <start-date> \
  --end-date <end-date> \
  --capital <capital> \
  --frequency day
```

如果编译失败：

- 先读返回里的 `errors`
- 本地修代码
- 更新远端策略
- 继续用同一个短区间重新编译

如果聚宽返回 `当前并行编译或回测数量最多2个`，等待后串行重试，不要继续并发提交。

## 评价纪律

不能只因为收益高或回撤低就推荐策略。至少同时看：

- 递进区间下的结果是否一致，例如 6 个月、1 年、3 年是否都能讲通，而不是只看单个最长区间
- 收益率与基准比较
- 最大回撤
- Sharpe / Sortino
- Beta 或波动暴露
- 交易次数和换手率
- 在真实手续费、最低佣金和滑点假设下是否仍成立
- 多个起点和不同市场阶段下是否稳定

如果某个因子 IC 看起来不错，但组合收益变差，先按组合构建、执行成本或调仓约束问题处理，不要直接判定因子无效。

更完整的评价口径见 `references/backtest-evaluation.md`。

## 本地验证

上传远端前先跑本地检查：

```bash
uv run python -m py_compile strategies/<strategy>.py
uv run python -m unittest discover -s strategies/tests -v
```

本地测试重点覆盖纯 helper：

- 权重归一化
- 调仓间隔
- 最小调仓金额
- 现金仓位
- 趋势/风险过滤
- 代表性样本的评分顺序
- 目标权重构建

本地测试不能证明聚宽兼容性。策略代码改动后，远端短区间编译仍然是必需门禁。

## 常见错误

- 没有先确认资金量、佣金、最低佣金和调仓频率，就默认套用某个账户假设
- 没有开启 `avoid_future_data` 或在日期处理上混入未来信息
- 只做本地测试，不做远端短区间编译
- 机械套用通用 `brainstorming` 或全量 TDD 流程，反而跳过了账户约束确认、远端编译和递进回测这些领域门禁
- 编译刚通过就直接跑 1 年或 3 年，不先做短区间烟雾回测
- 短区间已经暴露明显问题，还继续堆长区间回测掩盖问题
- 滑点和手续费写成理想值，导致回测解释失真
- 忽略 100 股整数手、最低佣金和最小成交额，小资金账户无法执行
- 遇到停牌、涨跌停、缺失数据或空结果时直接报错或继续下单
- 只看收益，不看换手、容量、回撤和成本敏感性
- 凭记忆使用远端策略 ID；创建或更新后 ID 可能变化，要先 `strategy list` 确认
