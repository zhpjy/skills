# 统一环境入口

优先使用 `mise` 管理项目环境，而不是依赖全局安装和手动激活：

- 用项目根目录的 `mise.toml` 固定运行时和 CLI 工具版本。
- 用语言生态的包管理器管理项目依赖，并通过 `mise` 解析出的工具执行。
- 用 `[env]` 管理项目环境变量，用 `[tasks]` 声明重复使用的开发、测试、检查和构建命令。
- 一次性命令使用 `mise exec -- ...`，项目任务使用 `mise run <task>`。
- 新增工具前先确认项目确实需要它，并选择项目认可的版本；不要无理由使用 `latest`。

典型配置：

```toml
[tools]
python = "3.12"
java = "temurin-21"

[env]
# 由 mise 为任务和 mise exec 加载本地环境变量
_.file = ".env"

[tasks.test]
run = "<project-test-command>"
```

初始化或修改环境时：

1. 先阅读 `mise.toml`、`.mise.toml`、`.python-version`、项目文档和 CI，确认版本来源与现有管理器。
2. 配置可信且已确认后，使用 `mise install` 安装声明的工具。
3. 缺少项目版本配置时，使用 `mise use <tool>@<version>` 添加项目级版本，而不是修改全局环境。
4. 验证时优先使用 `mise exec -- <command>` 或 `mise run <task>`，使命令使用项目配置解析出的工具链。

不要自动信任来源不明的 `mise.toml`。配置包含模板、环境变量、hook 或其他可执行行为时，先审查内容，再由用户决定是否执行 `mise trust`。

## 未安装工具

需要使用但本机或项目 `mise.toml` 未声明的工具时，优先使用 `nix run` 或 Docker，不要直接修改系统环境：

```bash
nix run nixpkgs#<tool> -- <args>
docker run --rm -v "$PWD:/workspace" -w /workspace <image>:<tag> <command>
```

选择方式：

- 工具在 Nix 仓库中可用，且主要需要访问当前工作区时，优先 `nix run`。
- 需要完整系统依赖、隔离环境或项目已有容器工作流时，使用 Docker。
- 为可复现性固定 Nix 输入版本或 Docker 镜像 tag；不要无理由使用浮动的 `latest`。
- 先检查工具是否已有 `mise` 版本；如果有，优先纳入项目 `mise.toml`，不要为同一工具维护多套入口。
- Nix 和 Docker 都不可用时，说明阻塞原因；只有用户或仓库明确要求时才使用全局安装。

## 环境变量与私密配置

本地开发优先使用 `.env` 配合 `mise` 加载：

```toml
[env]
_.file = ".env"
```

遵循以下边界：

- `.env` 放本地私密值，并确保已加入 `.gitignore`。
- 需要给协作者提供模板时，添加只含占位符的 `.env.example`。
- 不把真实凭据写入 `mise.toml`、源码、日志、异常消息或测试输出。
- 必需配置缺失时快速失败并给出变量名；可选配置才提供默认值。
- CI、生产环境优先使用平台 secret 注入，不把 `.env` 当作部署凭据存储。
- 需要切换环境时使用显式的 `--env-file` 或 mise 的环境配置，不通过修改源码切换。
