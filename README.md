# skills

## 仓库用途

这是一个用于管理技能相关内容的仓库。

## 目录与内容

```text
.
|-- bundles/
|-- docs/
|-- registry/
|-- skills/
|-- vendor/
`-- tools/
```

当前仓库中：

- `registry/sources/`：存放来源配置，描述每个来源的上游位置与同步目标。
- `registry/state/`：存放来源状态，记录本地同步后的基础结果与时间信息。
- `bundles/`：存放面向不同 agent 的清单文件，用来声明一组可安装技能。
- `skills/`：存放自有 skill。
- `vendor/`：存放同步到本地的外部 skill 内容。
- `tools/`：存放项目级安装、上传、bundle 启用和 vendor 同步的相关脚本。

## vendor 自动同步

仓库提供 GitHub Actions 工作流用于自动同步 vendor 内容。该工作流会通过手动触发和定时任务运行，并执行：

```bash
uv run tools/sync_vendor.py --all
```

行为说明：

- GitHub Actions 会定时运行 `uv run tools/sync_vendor.py --all`
- 工作流运行后会输出 `git status --short`，用于展示同步后的工作区状态
- 工作流内部会额外基于 `git status --porcelain=v1 -z` 做结构化检查，判断是否只改动了 `vendor/` 与 `registry/state/`
- 对 rename/copy 这类双路径变更，旧路径和新路径都会被纳入同一套限制检查
- 当 `vendor/` 或 `registry/state/` 有变化时，工作流会直接提交到 `main`
- 如果同步过程中检测到这两个目录之外也出现改动，工作流会直接失败，不会带着脏工作区继续提交
- 无论是定时触发还是手动触发，工作流都会以 `main` 为基准执行同步并回推到 `main`
- 工作流要求仓库允许 `GITHUB_TOKEN` 直接 push 到 `main`，并已授予 `contents: write`
- 如果 `main` 开启了必须走 PR、禁止 GitHub Actions 写入或其他分支保护限制，这个工作流将无法按设计直接提交
- GitHub Actions 的 cron 使用 UTC 时区，`0 2 * * *` 表示每天 UTC 02:00 运行

## 安装器使用说明

当前仓库提供一个基于命令行的 skill 安装器，当前版本只支持通过“仓库 URL + skill 名”安装单个 skill。

安装命令如下：

```bash
uv run --no-project https://raw.githubusercontent.com/zhpjy/skills/main/tools/sync_skill.py --repo <repo-url> --skill <skill-name>
```

安装行为说明：

- 安装来源是远程仓库中的 `skills/<skill-name>/` 目录。
- 安装目标是当前项目中的 `.agents/skills/<skill-name>/` 目录。
- 如果目标位置已存在同名 skill，安装器会直接覆盖更新。
- 当前版本依赖本机已安装 `git`。
- 当前版本不扩展其他安装方式。
- 如果仓库刚更新而本机 `uv` 仍命中旧缓存，可追加 `--refresh`；若需要强制绕过缓存，可用 `--no-cache` 或改用带提交 hash 的 raw URL。

## 上传器使用说明

当前仓库还提供一个基于命令行的 skill 上传器，用于把本地项目中的 skill 备份或更新到这个仓库远端。

默认命令如下：

```bash
uv run --no-project https://raw.githubusercontent.com/zhpjy/skills/main/tools/push_skill.py --repo <repo-url> --skill <skill-name>
```

如果需要显式指定本地源目录，可以这样调用：

```bash
uv run --no-project https://raw.githubusercontent.com/zhpjy/skills/main/tools/push_skill.py --repo <repo-url> --skill <skill-name> --source /path/to/local/skill
```

上传行为说明：

- 不传 `--source` 时，默认从当前工作目录的 `.agents/skills/<skill-name>/` 读取本地 skill。
- 传入 `--source` 时，脚本会直接使用该目录作为上传源。
- 目标固定是这个仓库远端中的 `skills/<skill-name>/`。
- 脚本会在 `/tmp` 中临时 clone 这个仓库，再在临时 clone 中覆盖、提交并 push。
- 如果远端当前内容和本地源目录完全一致，脚本会直接返回成功，不提交、不 push。
- 所有 git 操作都发生在临时 clone 中，不会修改你当前业务仓库的 git 状态。

## skill-manager

仓库中包含一个 `skill-manager` skill，用于告诉 AI 什么时候该调用下载器、bundle 同步器，什么时候该调用上传器。

- `sync_skill.py` 成功后，会自动安装或更新当前项目中的 `.agents/skills/skill-manager/`
- `sync_bundle.py` 成功后，也会自动安装或更新同一路径
- `push_skill.py` 成功后也会自动安装或更新同一路径
- 即使上传器遇到“内容无变化直接成功返回”的情况，也会同步 `skill-manager`
- 这三个脚本都会在本地 `skill-manager` 目录中写入 `repo-info.json`，用于记录这个 skills 仓库的本地路径和仓库 URL，供后续 AI 调用脚本时读取
