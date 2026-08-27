# Java 语言规范

本文件是 `technical-preferences` 的 Java 语言规范。

## JDK 版本

Java 开发优先使用 JDK 21。项目级 `mise.toml` 推荐固定发行版和主版本：

```toml
[tools]
java = "temurin-21"
```

也可以根据项目组织要求使用其他 JDK 21 发行版，例如 `zulu-21` 或 `corretto-21`。通过 mise 初始化和执行：

```bash
mise use java@temurin-21
mise install
mise exec -- java --version
```

JDK 21 是默认开发运行时，不代表可以未经要求提高项目的字节码兼容基线。项目已有的 `source`、`target`、toolchain 或 release 配置优先；升级兼容基线必须有明确需求。

## 构建与依赖

遵循项目已有的 Maven 或 Gradle 配置和 wrapper：

```bash
mise exec -- ./mvnw test
mise exec -- ./gradlew test
```

优先使用仓库提交的 `mvnw` 或 `gradlew`，不要替换为全局 Maven、Gradle 或手动下载的 JDK。依赖版本写入项目构建文件和锁定机制，避免在源码或脚本中临时下载依赖。

## 代码与注释

复杂业务流程、并发控制、事务边界、外部调用、异常恢复和非显然的性能取舍使用简洁中文注释。注释解释意图和约束，不重复 Java 语法或方法名。

保持可测试的边界，避免把业务逻辑全部塞进 `main`、controller 或构建脚本。异常处理应保留可诊断上下文，不能静默捕获 `Exception`。

## 验证

优先使用项目已有 task；没有 task 时通过 mise 执行 wrapper：

```bash
mise run test
mise exec -- ./mvnw verify
mise exec -- ./gradlew check
mise exec -- java --version
```

至少执行一条与改动相关的构建、测试或静态检查命令，并如实报告结果。
