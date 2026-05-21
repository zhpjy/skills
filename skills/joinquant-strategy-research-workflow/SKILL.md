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

## 执行顺序

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

- `README.md` 维护研究目标、当前主线版本、当前最优版本、远端目录和下一步
- `PATH.md` 维护研究路径上的关键决策节点
- `candidate/` 保存当前正在验证的候选策略和候选测试；不要在 `joinquant/strategies/` 为研究包生成候选版本
- `versions/<version>/strategy.py` 保存该正式版本的代码快照
- `versions/<version>/meta.json` 保存该正式版本的机器可读状态，供 AI 续跑、接手和状态恢复使用
- `versions/<version>/result.md` 写该版本自己的结论，并保留一句类似 `> 跨版本结论：r02-main 取代 r01-main 成为主线。`

## 常见错误

- 把一个研究包混入多个研究假设
- 还没远端验证，就先创建 `rNN-*` 正式版本目录
- 在研究包已经存在时，仍把候选代码写到 `joinquant/strategies/` 或其他全局目录
- 创建正式版本后，没有同步更新 `README.md`
- 在 `PATH.md` 写单版本细节，或在 `result.md` 写跨版本主记录
- 用 `current/`、`latest/` 一类目录代替正式版本编号
- 让本 skill 直接承担策略编码或远端操作职责
