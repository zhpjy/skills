---
name: finebi-har-query
description: 当需要从 HAR 文件中逆向分析 FineBI 行为、定位接口请求与响应样例，或在不手动打开大型 HAR JSON 文件的情况下追踪调用链路时使用。
---

# FineBI HAR 查询

## 概览

优先使用本地 HAR 查询工具，而不是直接打开原始 HAR 文件。它更适合从 `har/*.json` 中快速定位接口、样例请求体、字段结构和相邻调用上下文。

工具入口：

```bash
uv run python tools/harq.py --help
```

## 适用场景

- 需要确认某个 FineBI 接口是否出现在 HAR 中
- 需要为某个 path 提取一条请求或响应样例
- 需要查看请求 JSON 或响应 JSON 的字段树
- 需要追踪某个命中请求前后发生了哪些调用
- 需要比较两个 HAR 在归一化接口层面的差异

## 快速参考

列出所有 HAR 中的归一化接口：

```bash
uv run python tools/harq.py --all list
```

搜索请求体或响应体：

```bash
uv run python tools/harq.py --all find 张鹏
uv run python tools/harq.py --all find reportWidgetsMap --field response
```

提取一条代表性的请求与响应样例：

```bash
uv run python tools/harq.py --all sample --normalized-path /webroot/decision/v5/conf/tables/add
```

提取请求或响应的字段树：

```bash
uv run python tools/harq.py --all fields --normalized-path /webroot/decision/v5/conf/tables/fields/page --side response
```

查看某一条完整请求：

```bash
uv run python tools/harq.py --all show create-temp-dataset-and-analyse-subject.json:42 --around 2
```

围绕某个关键词命中点回看前后请求：

```bash
uv run python tools/harq.py --all trace --keyword reportWidgetsMap --window 2
```

比较两个 HAR 文件的接口差异：

```bash
uv run python tools/harq.py diff --base har/login-har.json --target har/create-temp-dataset-and-analyse-subject.json
```

## 建议流程

1. 先用 `list` 了解当前 HAR 里有哪些归一化接口。
2. 已知关键词、字段名、展示名或资源 ID 碎片时，优先用 `find`。
3. 需要把样例写进文档或实现说明时，用 `sample`。
4. 写代码前如果依赖 JSON 结构，先用 `fields` 提取字段树。
5. 逆向创建或编辑链路时，用 `trace` 或 `show --around`。
6. 对比两个动作或两个 HAR 的差异时，用 `diff`。

## 说明

- 工具默认会过滤静态资源和 websocket 请求。
- 路径归一化会把 32 位 ID、UUID 和 ticket token 替换成占位符，便于稳定统计接口族。
- `sample` 和 `show` 在可能的情况下会优先输出格式化后的 JSON；否则保留原始文本。
