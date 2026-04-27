# skills

## 仓库用途

这是一个用于管理技能相关内容的仓库。

## 目录结构

```text
.
|-- docs/
|-- skills/
`-- tools/
```

其中，`skills/` 目录用于存放 skill，`tools/` 目录用于存放工具。

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
