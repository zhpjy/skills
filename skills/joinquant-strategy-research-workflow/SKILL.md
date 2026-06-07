---
name: joinquant-strategy-research-workflow
description: Use when需要围绕单个研究假设组织聚宽策略研究包、正式版本沉淀、跨版本判断和结论留痕，而不是直接编写策略代码或单独操作聚宽远端资源。
---

# 聚宽策略研究工作流

## 概览

这个 skill 只负责编排“单个研究假设”的完整研究生命周期，不替代具体执行：

- 编写、修改、本地测试策略代码时，使用 `joinquant-strategy-coding`
- 创建远端目录、上传策略、编译、回测、读取回测结果时，使用 `joinquant-trader`

文档默认使用中文。

## 硬规则

- 一个研究主题只对应一个本地研究包；目录语义默认是 `joinquant/research/YYYYMMDD-研究主题/`，但脚手架会对 `topic` 做必要清洗，后续一律以实际生成目录名为准
- 研究包固定包含 `README.md`、`PATH.md`、`candidate/`、`versions/`
- `candidate/` 是本研究包唯一候选工作区；策略代码、候选测试和上传聚宽前的本地修改都先放在这里
- 不使用 `current/`
- 每个正式版本目录固定包含 `strategy.py`、`result.md`、`meta.json`
- `meta.json` 是 AI 续跑或接手时的机器状态落点，用来记录远端目录、策略 ID、编译状态、最近一次回测和指标摘要
- 正式版本命名只允许 `rNN-main` 或 `rNN-exp-a` / `rNN-exp-b` 这类 `rNN-exp-x`
- `result.md` 只负责单版本判断
- `PATH.md` 只负责跨版本比较、主线切换、分叉与淘汰决策
- 相关版本的 `result.md` 中必须保留一句引用式结论，用来引用最终跨版本判断
- 只有满足“已上传、已编译、已回测、已有结论”四个条件，才允许从 `candidate/` 创建正式版本目录
- 每次创建正式版本后，必须同步更新 `README.md`

## 递进式研究阶段

研究包内的策略开发按固定阶段递进。每个阶段有明确的进入条件、产出物、退出标准和失败处理方式。阶段信息记录在 `README.md`（当前阶段）和 `PATH.md`（阶段切换决策），`meta.json` 中记录版本所属阶段。

### 阶段定义

| 阶段 | 名称 | 核心任务 | 产出物 |
|---|---|---|---|
| P0 | 初始化 | 创建研究包、明确评价标准（年化收益、最大回撤、Sharpe 底线） | README（含量化门槛）、PATH |
| P1 | Baseline | 搭建最简策略骨架，跑通回测链路 | r01-main：纯 ETF 等权/市值加权 baseline |
| P2 | 单因子验证 | 一次只测一个因子，独立判定有效性 | rNN-exp-a/b/c…：因子变体 |
| P3 | 多因子组合 | 组合已验证有效因子，检查共线性 | rNN-main：多因子版本 |
| P4 | 参数优化 | 对关键参数做网格扫描，确认稳健性 | rNN-exp-x：参数网格变体 |
| P5 | 业绩归因 | 拆解收益来源，确认因子贡献 | rNN-main：归因分析版本 |
| P6 | 实盘准备 | 成本复核、小资金验证、上线 | rNN-main：最终实盘版本 |

### 阶段进入/退出条件

- **P0 → P1**：评价标准已写入 README（年化收益、最大回撤、Sharpe 底线）
- **P1 → P2**：baseline 回测通过——收益不低于基准、回撤在容忍范围内、换手率合理
- **P2 → P3**：至少一个因子被判定有效（扣费后 IC 显著、多时段稳健）；无效因子必须在 PATH.md 记录淘汰原因
- **P3 → P4**：多因子组合不退化（扣费后跑赢单因子最优版）
- **P4 → P5**：网格扫描中心值附近 ±20% 不塌缩，过拟合嫌疑排除
- **P5 → P6**：因子贡献 > 50%，非因子暴露（行业/市值）不主导收益

### 阶段记录格式

PATH.md 中按以下格式记录每次阶段推进：

```
## P2 阶段开始 / 20260531
- 阶段：P2 单因子验证
- 进入版本：r01-main
- 测试因子：相对强弱 (RSI_20)
- 候选方案：candidate/r02-exp-a

## P2 → P3 阶段门禁 / 20260605
- 因子：相对强弱 (RSI_20)
- 结果：扣费后年化超额 +3.2%，IC 均值 0.04，三段均正向
- 判定：通过，进入 P3
```

README.md 中维护当前阶段状态行：

```
- 当前阶段：P2 单因子验证
```

## 执行顺序

研究包整体按递进式研究阶段推动（P0→P6），每个阶段内按以下原子循环执行：

1. 先为单个研究假设创建研究包。
2. 用 `joinquant-strategy-coding` 在本研究包 `candidate/` 内产出候选策略代码和候选测试；此时不要提前创建正式版本目录。
3. 用 `joinquant-trader` 创建或确认聚宽远端目录，上传候选策略，完成编译与正式回测。
4. 基于回测结果写出该候选方案的明确结论。
5. 只有到这一步，才把 `candidate/` 中已验证的候选方案固化为正式版本目录。
6. 在对应版本 `result.md` 记录单版本判断；若涉及版本比较、主线切换或淘汰，同时更新 `PATH.md`。

如果某个候选方案还没上传、还没编译通过、还没跑回测，或者还没有结论，它只能是过程中的候选，不是正式版本。

## 脚手架命令

研究包初始化：

```bash
uv run python .agents/skills/joinquant-strategy-research-workflow/scripts/research_scaffold.py init-package \
  --root joinquant/research \
  --date 20260512 \
  --topic 中证红利低波增强
```

正式版本固化：

```bash
uv run python .agents/skills/joinquant-strategy-research-workflow/scripts/research_scaffold.py init-version \
  --package-dir joinquant/research/20260512-中证红利低波增强 \
  --version-id r01-main \
  --source-file /abs/path/to/strategy.py \
  --branch-type main \
  --remote-directory-name 20260512-中证红利低波增强
```

分支实验版本示例：

```bash
uv run python .agents/skills/joinquant-strategy-research-workflow/scripts/research_scaffold.py init-version \
  --package-dir joinquant/research/20260512-中证红利低波增强 \
  --version-id r02-exp-a \
  --source-file /abs/path/to/strategy.py \
  --parent-version r01-main \
  --branch-type exp-a \
  --remote-directory-name 20260512-中证红利低波增强
```

`init-version` 的 `--source-file` 必须位于当前研究包的 `candidate/` 目录内。输入应当是已经完成上传、编译、回测并且已有结论的最终代码快照，而不是尚未验证的中间草稿。

`init-version` 只负责生成正式版本目录和占位状态。创建完成后，必须立即把 `meta.json` 和 `result.md` 回填为真实远端信息、真实回测状态和真实结论；`pending`、`null`、`待补充` 只能是刚生成时的占位值，不能被当成已完成状态继续流转。

## 记录要求

- `README.md` 维护研究目标、当前阶段、当前主线版本、当前最优版本、远端目录和下一步
- `PATH.md` 维护研究路径上的关键决策节点
- `candidate/` 保存当前正在验证的候选策略和候选测试；不要在 `joinquant/strategies/` 为研究包生成候选版本
- `versions/<version>/strategy.py` 保存该正式版本的代码快照
- `versions/<version>/meta.json` 保存该正式版本的机器可读状态，供 AI 续跑、接手和状态恢复使用。字段包括 `phase`（所属阶段）、`factors`（已验证因子的 IC 摘要，P2+ 填写）、`data_split`（训练/测试集切分日期，P3+ 填写）、`grid_params`（参数网格扫描信息，P4+ 填写）
- `versions/<version>/result.md` 写该版本自己的结论，并保留一句类似 `> 跨版本结论：r02-main 取代 r01-main 成为主线。`

## 常见错误

- 把一个研究包混入多个研究假设
- 还没远端验证，就先创建 `rNN-*` 正式版本目录
- 在研究包已经存在时，仍把候选代码写到 `joinquant/strategies/` 或其他全局目录
- 创建正式版本后，没有同步更新 `README.md`
- 在 `PATH.md` 写单版本细节，或在 `result.md` 写跨版本主记录
- 用 `current/`、`latest/` 一类目录代替正式版本编号
- 让本 skill 直接承担策略编码或远端操作职责
