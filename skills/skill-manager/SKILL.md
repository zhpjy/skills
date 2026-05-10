---
name: skill-manager
description: Use when the user wants to download a skill from this skills repository into the current project, or upload a local project skill back to this repository
---

# Skill 管理器

## 何时使用

当用户表达以下意图时使用这个 skill：

- 安装某个 skill
- 更新本地 skill
- 从 skills 仓库获取某个 skill
- 在项目中启用 superpowers
- 上传某个 skill
- 把本地 skill 更新回 skills 仓库

## 先读本地仓库信息

这个 skill 安装到项目后，同目录会有一个 `repo-info.json` 文件。

执行上传或下载前，先读取这个文件，获取：

- `repo_root`：本机上的 skills 仓库路径
- `repo_url`：这个 skills 仓库对应的仓库 URL

如果 `repo-info.json` 不存在，就说明当前项目里的 `skill-manager` 还没有正确同步。此时应提示用户先通过这个 skills 仓库重新安装或更新一次 skill。

## 下载或更新本地 skill

当用户说“安装 skill”“更新本地 skill”“从 skill 仓库获取 skill”时，调用下载器：

```bash
uv run --refresh --no-project https://raw.githubusercontent.com/zhpjy/skills/main/tools/sync_skill.py --repo <repo_url> --skill <skill-name>
```

如果用户说的是“在项目中启用 superpowers”“启用 superpowers bundle”或等价意图，优先调用 bundle 同步器，而不是逐个安装：

```bash
uv run --refresh --no-project https://raw.githubusercontent.com/zhpjy/skills/main/tools/sync_bundle.py --repo <repo_url> --bundle superpowers-codex
```

默认行为：

- 从仓库中的 `skills/<skill-name>/` 获取 skill
- 安装到当前项目 `.agents/skills/<skill-name>/`
- 如果本地已存在同名 skill，则直接覆盖更新
- bundle 同步会把 `bundles/superpowers-codex.json` 中声明的整组 skill 安装到当前项目 `.agents/skills/`

## 上传本地 skill

当用户说“上传 skill”“更新到 skill 仓库”“把本地 skill 备份到仓库”时，调用上传器：

```bash
uv run --refresh --no-project https://raw.githubusercontent.com/zhpjy/skills/main/tools/push_skill.py --repo <repo_url> --skill <skill-name>
```

如果本地 skill 不在默认位置，再显式加上：

```bash
uv run --refresh --no-project https://raw.githubusercontent.com/zhpjy/skills/main/tools/push_skill.py --repo <repo_url> --skill <skill-name> --source /path/to/local/skill
```

默认行为：

- 不传 `--source` 时，默认从当前项目 `.agents/skills/<skill-name>/` 读取
- 上传目标固定为仓库中的 `skills/<skill-name>/`
- 如果远端当前内容无变化，则直接返回成功，不提交、不 push

## 默认判定规则

- “更新 skill”默认理解为：从 skills 仓库更新到当前项目本地
- “上传 skill”默认理解为：把当前项目本地 skill 上传到 skills 仓库
- 如果用户已经明确说“更新到仓库”或“从仓库更新到本地”，按用户表达的方向执行，不要反着做

## 自更新说明

这三个脚本在成功路径上都会自动安装或更新当前项目里的 `skill-manager`，这样后续 AI 会使用同一套规则继续工作。
