---
name: har-query
description: Use when需要从 HAR 文件中查询接口、搜索请求或响应内容、提取 JSON 字段树、查看相邻调用上下文，或比较两个 HAR 的接口差异，而不希望把大型 HAR 原文整体读入上下文。
---

# HAR Query

## 概览

优先使用随 skill 内置的 `harq.py` 查询 HAR 文件。它适合快速定位接口、样例请求体、响应体字段结构和相邻调用上下文，避免直接打开大型 HAR JSON。

工具入口：

```bash
uv run python .agents/skills/har-query/scripts/harq.py --help
```

如果当前项目没有 `uv`，且脚本不依赖第三方包，也可以使用：

```bash
python .agents/skills/har-query/scripts/harq.py --help
```

## 适用场景

- 确认某个接口是否出现在 HAR 中
- 为某个 path 提取一条请求或响应样例
- 查看请求 JSON 或响应 JSON 的字段树
- 追踪某个命中请求前后发生了哪些调用
- 比较两个 HAR 在归一化接口层面的差异

## 快速参考

列出 `har/*.json` 中的归一化接口：

```bash
uv run python .agents/skills/har-query/scripts/harq.py --all list
```

搜索请求体或响应体：

```bash
uv run python .agents/skills/har-query/scripts/harq.py --all find keyword
uv run python .agents/skills/har-query/scripts/harq.py --all find fieldName --field response
```

提取一条代表性的请求与响应样例：

```bash
uv run python .agents/skills/har-query/scripts/harq.py --all sample --normalized-path /api/items/{ID}
```

提取请求或响应的字段树：

```bash
uv run python .agents/skills/har-query/scripts/harq.py --all fields --normalized-path /api/items/{ID} --side response
```

查看某一条完整请求：

```bash
uv run python .agents/skills/har-query/scripts/harq.py --all show capture.har:42 --around 2
```

围绕某个关键词命中点回看前后请求：

```bash
uv run python .agents/skills/har-query/scripts/harq.py --all trace --keyword fieldName --window 2
```

比较两个 HAR 文件的接口差异：

```bash
uv run python .agents/skills/har-query/scripts/harq.py diff --base before.har --target after.har
```

## 建议流程

1. 先用 `list` 了解当前 HAR 里有哪些归一化接口。
2. 已知关键词、字段名、展示名或资源 ID 碎片时，优先用 `find`。
3. 需要把样例写进文档或实现说明时，用 `sample`。
4. 写代码前如果依赖 JSON 结构，先用 `fields` 提取字段树。
5. 逆向操作链路时，用 `trace` 或 `show --around`。
6. 对比两个动作或两个 HAR 的差异时，用 `diff`。

## 说明

- 工具默认过滤静态资源和 websocket 请求。
- 路径归一化会把 32 位 ID、UUID，以及常见 token/session/ticket 片段替换成占位符，便于稳定统计接口族。
- `sample` 和 `show` 在可能的情况下会优先输出格式化后的 JSON；否则保留原始文本。
