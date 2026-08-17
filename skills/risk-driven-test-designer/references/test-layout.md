# 语言无关的测试目录规范

## 原则

- 优先按业务能力和测试意图组织，不按类、方法或编程语言组织。
- 测试层级可通过框架标签、CI 分组或元数据表达，不必全部作为顶层目录。
- 已有项目优先沿用现有有效结构；默认只规范新增测试。
- 移动文件前检查测试发现与 CI；移动后必须运行验证。

## 缺少项目约定时的默认结构

```text
tests/
├── journeys/       # 跨能力的核心业务旅程，数量少
├── capabilities/   # 各业务能力的流程、规则和场景，测试主体
├── contracts/      # HTTP、消息、文件、第三方等边界契约
├── qualities/      # 并发、一致性、恢复、安全、性能等横切风险
├── manual/         # 人工验收、探索性测试、检查清单
├── probes/         # 外部环境探测与诊断，不进入默认回归
├── data/           # fixture、builder、sample，不是测试用例
└── support/        # driver、fake、stub、utility，不直接被发现
```

建议细分：

```text
tests/
├── journeys/<core-journey>/
│   ├── happy-path/
│   └── critical-failures/
├── capabilities/<business-capability>/
│   ├── flows/
│   ├── rules/
│   └── scenarios/
├── contracts/
│   ├── inbound/
│   ├── outbound/
│   └── schemas/
├── qualities/
│   ├── concurrency/
│   ├── consistency/
│   ├── resilience/
│   ├── security/
│   └── performance/
├── manual/
│   ├── acceptance/
│   ├── exploratory/
│   └── checklists/
├── probes/
│   ├── external/
│   └── diagnostics/
├── data/
│   ├── fixtures/
│   ├── builders/
│   └── samples/
└── support/
    ├── drivers/
    ├── fakes/
    ├── stubs/
    └── utilities/
```

## 放置决策

1. 人工执行 → `manual/`。
2. 外部可用性检查或诊断 → `probes/`。
3. 测试数据或生成器 → `data/`。
4. 测试基础设施 → `support/`。
5. 跨多个能力并验证核心用户目标 → `journeys/`。
6. 验证输入输出、消息、文件或第三方边界 → `contracts/`。
7. 主要验证并发、安全、恢复、一致性或性能 → `qualities/`。
8. 其余自动化测试按业务能力进入 `capabilities/`：
   - 子流程和组件协作 → `flows/`；
   - 规则、计算、边界、不变量和状态机 → `rules/`；
   - 其他独立业务行为 → `scenarios/`。

## 命名

- 目录优先使用业务术语和 `lowercase-kebab-case`。
- 文件前后缀遵循当前语言与测试框架。
- 语义表达“行为 + 条件 + 结果”，避免只使用类名或方法名。
- 避免 `misc`、`others`、`temp`、`methods`、`classes` 等无稳定责任的目录。

## 可选元数据

在框架支持时，可使用标签表达：

```text
scope: rule | component | integration | journey
speed: fast | medium | slow
dependency: isolated | local-infrastructure | external
risk: critical | high | normal
```

不要为了统一标签而破坏项目已有机制。
