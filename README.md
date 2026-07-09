# Skill Dashboard

![Skill](https://img.shields.io/badge/Skill-Agent-111111?style=flat-square)
![Codex](https://img.shields.io/badge/Codex-Supported-222222?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square)
![License](https://img.shields.io/github/license/RyanZheng5588/skills-dashboard?style=flat-square)

> 🌏 English version: [README.en.md](./README.en.md)

一个适配 Codex / Claude Code / 本地 Agent 环境的 skill，用来扫描本机已安装的 skills，并生成一个可搜索、可分类、可查看详情与案例预览的本地浏览器 dashboard。

它解决的是「我到底装了哪些 skill、分别能干什么、应该什么时候用」这个问题。

## 30 秒开始

```bash
npx skills add https://github.com/RyanZheng5588/skills-dashboard --skill skill-dashboard
```

也可以直接把下面这段话发给有 shell 权限的 AI Agent：

```text
帮我安装 skill-dashboard。请把 https://github.com/RyanZheng5588/skills-dashboard 克隆到 ~/.codex/skills/skill-dashboard，安装完成后检查 SKILL.md、assets/、references/、scripts/ 是否存在。
```

手动安装：

```bash
git clone https://github.com/RyanZheng5588/skills-dashboard.git ~/.codex/skills/skill-dashboard
```

已经安装过的话，更新：

```bash
cd ~/.codex/skills/skill-dashboard
git pull
```

## 使用

安装后可以对 Codex 说：

```text
Use $skill-dashboard to open the local skill dashboard.
```

普通用户最简单的方式是在 macOS 上一键打开：

```bash
open ~/.codex/skills/skill-dashboard/Skill\ Dashboard.command
```

也可以在 Finder 里进入 `~/.codex/skills/skill-dashboard`，双击 `Skill Dashboard.command`。它会自动启动本地服务并打开浏览器。

终端里直接运行：

```bash
~/.codex/skills/skill-dashboard/scripts/start.sh
```

如果你用 `scripts/install.sh` 整理过安装，还会额外创建一个短命令：

```bash
skill-dashboard
```

底层命令仍然保留，适合自定义参数：

```bash
python3 ~/.codex/skills/skill-dashboard/scripts/skill_dashboard.py --serve --open
```

添加自定义扫描目录：

```bash
python3 ~/.codex/skills/skill-dashboard/scripts/skill_dashboard.py --root ~/my-skills --open
```

或：

```bash
SKILL_DASHBOARD_ROOTS="$HOME/work/skills:$HOME/.custom/skills" \
  python3 ~/.codex/skills/skill-dashboard/scripts/skill_dashboard.py --open
```

## 功能

- 扫描常见本地 skill 根目录：Codex、Claude、Hermes、agent skills 和 Codex plugin cache。
- 按平台浏览：Codex、Claude、Hermes、Other。
- 按用途浏览：文案、图片、视频、PPT、排版、数据、代码、知识库、自动化、设计、文档、音频、研究等。
- 支持对 skill 名称、描述、使用说明、分类、平台和路径进行模糊搜索。
- 卡片式目录、分页、右侧用途榜单、详情抽屉。
- 中英文 UI 切换。
- Orbit 暗色主题与 Daylight 浅色主题。
- 本地案例预览，不消耗 token，不调用外部服务。
- 构建脚本只依赖 Python 标准库。

## 适合 / 不适合

**适合**：整理本机 skills / 查看 skill 用途 / 对比 Codex、Claude、Hermes skill / 给团队演示本地 skill 能力 / 开源 skill 仓库自查。

**不适合**：云端托管多用户管理 / 远程同步 skill 市场 / 自动安装第三方 skill / 替代 Codex 自身 skill 调度。

## 目录结构

```text
SKILL.md
agents/openai.yaml
assets/dashboard.html
references/classification.md
scripts/
  skill_dashboard.py
  start.sh
  install.sh
  check.sh
Skill Dashboard.command
```

## 开发

本地检查：

```bash
./scripts/check.sh
```

不安装，直接从仓库构建预览：

```bash
python3 scripts/skill_dashboard.py --out /tmp/skill-dashboard-preview --quiet
open /tmp/skill-dashboard-preview/index.html
```

安装当前工作区版本：

```bash
./scripts/install.sh
```

安装脚本会复制 skill 到 `~/.codex/skills/skill-dashboard`，并创建 `~/.local/bin/skill-dashboard` 作为一键启动命令。

## 隐私

这个工具会读取本机的 `SKILL.md` 文件，并生成 `.dashboard/` 输出。生成结果可能包含本机路径、skill 名称和说明，因此 `.dashboard/` 默认被 `.gitignore` 排除。

除非你已经审查过生成内容并明确想公开，否则不要提交 `.dashboard/`。

## License

MIT
