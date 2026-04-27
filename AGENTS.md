# AGENTS

## Scope

本文件只约束这个 skills 仓库相关的 skill 管理请求：

- 安装 skill
- 下载 skill
- 更新本地 skill
- 上传 skill
- 更新 skill 到仓库

不相关的普通开发任务不要套用这里的规则。

## Bootstrap

当用户请求安装、下载、更新或上传 skill 时，先检查当前项目是否存在：

```text
.agents/skills/skill-manager/
```

如果不存在，则先安装 `skill-manager`，再继续后续操作。

安装命令：

```bash
uv run /home/zhpjy/project/skills/tools/sync_skill.py --repo git@github.com:zhpjy/skills.git --skill skill-manager
```

如果已经存在 `skill-manager`，不要重复安装。

## Preferred Metadata

如果当前项目存在：

```text
.agents/skills/skill-manager/repo-info.json
```

则优先读取其中的：

- `repo_root`
- `repo_url`

后续调用脚本时优先使用这里记录的信息，而不是重新猜测路径或仓库地址。

## Download Rules

当用户表达以下意图时：

- 安装某个 skill
- 从仓库获取某个 skill
- 更新本地 skill

优先调用：

```bash
uv run <repo_root>/tools/sync_skill.py --repo <repo_url> --skill <skill-name>
```

如果没有可用的 `repo-info.json`，则使用这个仓库的默认信息：

- `repo_root`: `/home/zhpjy/project/skills`
- `repo_url`: `git@github.com:zhpjy/skills.git`

## Upload Rules

当用户表达以下意图时：

- 上传某个 skill
- 更新 skill 到仓库
- 把本地 skill 备份到仓库

优先调用：

```bash
uv run <repo_root>/tools/push_skill.py --skill <skill-name>
```

如果用户明确给了本地源目录，再附加：

```bash
--source /path/to/local/skill
```

## Direction Defaults

- “更新 skill”默认理解为：从仓库更新到当前项目本地
- “上传 skill”默认理解为：把当前项目本地 skill 上传到仓库
- 如果用户明确说“更新到仓库”或“从仓库更新到本地”，按用户说的方向执行，不要反着做

## Notes

- `sync_skill.py` 和 `push_skill.py` 成功后都会自动更新当前项目中的 `skill-manager`
- 不要为了无关任务主动安装 `skill-manager`
- 只在处理 skill 管理请求、且本地还没有 `skill-manager` 时，才执行 bootstrap 安装
