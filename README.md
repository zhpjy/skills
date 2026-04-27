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
uv run /path/to/this-repo/tools/install_skill.py --repo <repo-url> --skill <skill-name>
```

安装行为说明：

- 安装来源是远程仓库中的 `skills/<skill-name>/` 目录。
- 安装目标是当前项目中的 `.agents/skills/<skill-name>/` 目录。
- 如果目标位置已存在同名 skill，安装器会直接覆盖更新。
- 当前版本依赖本机已安装 `git`。
- 当前版本不扩展其他安装方式。
