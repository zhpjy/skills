# skills

## 仓库用途

这是一个用于管理技能相关内容的仓库。

## 目录结构

```text
.
|-- bundles/
|-- docs/
|-- registry/
|-- skills/
|-- vendor/
`-- tools/
```

其中，`skills/` 目录用于存放 skill，`tools/` 目录用于存放工具。

## 新架构概览

为后续引入可追踪的来源管理与 bundle 组织方式，仓库新增了一层轻量注册表脚手架：

- `registry/sources/`：记录上游来源定义，例如来源类型、仓库地址、默认 bundle、状态文件位置。
- `registry/state/`：记录每个来源的本地同步状态，例如当前是否尚未同步、最近同步时间、对应 revision。
- `bundles/`：定义面向具体运行环境的安装清单，把多个 skill 按 bundle 组织起来。
- `vendor/`：预留给后续同步下来的第三方或上游内容，当前先保留目录占位。

当前已加入 `superpowers` 这一组基础元数据，用于作为后续 registry 读写和同步逻辑的最小样例。

## 安装器使用说明

当前仓库提供一个基于命令行的 skill 安装器，当前版本只支持通过“仓库 URL + skill 名”安装单个 skill。

安装命令如下：

```bash
uv run /path/to/this-repo/tools/sync_skill.py --repo <repo-url> --skill <skill-name>
```

安装行为说明：

- 安装来源是远程仓库中的 `skills/<skill-name>/` 目录。
- 安装目标是当前项目中的 `.agents/skills/<skill-name>/` 目录。
- 如果目标位置已存在同名 skill，安装器会直接覆盖更新。
- 当前版本依赖本机已安装 `git`。
- 当前版本不扩展其他安装方式。

## 上传器使用说明

当前仓库还提供一个基于命令行的 skill 上传器，用于把本地项目中的 skill 备份或更新到这个仓库远端。

默认命令如下：

```bash
uv run /path/to/this-repo/tools/push_skill.py --skill <skill-name>
```

如果需要显式指定本地源目录，可以这样调用：

```bash
uv run /path/to/this-repo/tools/push_skill.py --skill <skill-name> --source /path/to/local/skill
```

上传行为说明：

- 不传 `--source` 时，默认从当前工作目录的 `.agents/skills/<skill-name>/` 读取本地 skill。
- 传入 `--source` 时，脚本会直接使用该目录作为上传源。
- 目标固定是这个仓库远端中的 `skills/<skill-name>/`。
- 脚本会在 `/tmp` 中临时 clone 这个仓库，再在临时 clone 中覆盖、提交并 push。
- 如果远端当前内容和本地源目录完全一致，脚本会直接返回成功，不提交、不 push。
- 所有 git 操作都发生在临时 clone 中，不会修改你当前业务仓库的 git 状态。

## skill-manager

仓库中包含一个 `skill-manager` skill，用于告诉 AI 什么时候该调用下载器，什么时候该调用上传器。

- `sync_skill.py` 成功后，会自动安装或更新当前项目中的 `.agents/skills/skill-manager/`
- `push_skill.py` 成功后也会自动安装或更新同一路径
- 即使上传器遇到“内容无变化直接成功返回”的情况，也会同步 `skill-manager`
- 两个脚本都会在本地 `skill-manager` 目录中写入 `repo-info.json`，用于记录这个 skills 仓库的本地路径和仓库 URL，供后续 AI 调用脚本时读取
