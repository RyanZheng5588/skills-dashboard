# Skill Dashboard

An installable Codex skill that scans local skill folders and builds a self-contained browser dashboard for discovering, filtering, and previewing skills.

一个可安装的 Codex skill：读取本机 skill 目录，生成本地浏览器 dashboard，用于搜索、分类、查看详情和生成本地案例预览。

## Features

- Scan common local roots: Codex, Claude, Hermes, agent skills, and Codex plugin caches.
- Browse by platform: Codex, Claude, Hermes, and Other.
- Browse by use case: copy, images, video, slides, layout, data, code, knowledge, automation, design, docs, audio, research, and more.
- Fuzzy search across skill names, descriptions, usage notes, categories, platforms, and paths.
- Card-based directory with pagination, ranking rail, and click-through detail drawer.
- Bilingual UI: Chinese and English.
- Theme switching: Orbit dark theme and Daylight light theme.
- Local example previews that do not consume tokens or call external services.
- Python standard library only for the dashboard builder.

## Install

Clone or download this project, then run:

```bash
./scripts/install.sh
```

The installer copies `skill-dashboard/` into:

```bash
${CODEX_HOME:-$HOME/.codex}/skills/skill-dashboard
```

It excludes generated local output such as `.dashboard/`.

## Use

After installation:

```bash
python3 ~/.codex/skills/skill-dashboard/scripts/skill_dashboard.py --open
```

Serve over localhost:

```bash
python3 ~/.codex/skills/skill-dashboard/scripts/skill_dashboard.py --serve --open
```

Add custom scan roots:

```bash
python3 ~/.codex/skills/skill-dashboard/scripts/skill_dashboard.py --root ~/my-skills --open
```

Or:

```bash
SKILL_DASHBOARD_ROOTS="$HOME/work/skills:$HOME/.custom/skills" \
  python3 ~/.codex/skills/skill-dashboard/scripts/skill_dashboard.py --open
```

## Project Layout

```text
skill-dashboard/
  SKILL.md
  agents/openai.yaml
  assets/dashboard.html
  references/classification.md
  scripts/skill_dashboard.py
scripts/
  install.sh
  check.sh
```

## Development

Run the local checks:

```bash
./scripts/check.sh
```

Build a dashboard from the repo copy without installing:

```bash
python3 skill-dashboard/scripts/skill_dashboard.py --out /tmp/skill-dashboard-preview --quiet
open /tmp/skill-dashboard-preview/index.html
```

## Privacy

This tool reads local `SKILL.md` files and writes a generated dashboard. The generated `.dashboard/` output may contain local file paths, skill names, and descriptions from your machine. It is intentionally ignored by git.

Do not commit generated dashboard output unless you have reviewed it and intentionally want to publish that data.

## License

MIT
