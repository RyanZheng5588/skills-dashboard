# Skill Dashboard

![Skill](https://img.shields.io/badge/Skill-Agent-111111?style=flat-square)
![Codex](https://img.shields.io/badge/Codex-Supported-222222?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square)
![License](https://img.shields.io/github/license/RyanZheng5588/skills-dashboard?style=flat-square)

An installable skill for Codex, Claude Code, and local agent environments. It scans installed local skills and builds a self-contained browser dashboard for search, filtering, detail inspection, and local example previews.

It answers a practical question: "What skills do I have installed, what can they do, and when should I use each one?"

## Quick Start

```bash
npx skills add https://github.com/RyanZheng5588/skills-dashboard --skill skill-dashboard
```

Or ask a shell-capable AI agent:

```text
Install skill-dashboard. Clone https://github.com/RyanZheng5588/skills-dashboard into ~/.codex/skills/skill-dashboard, then verify that SKILL.md, assets/, references/, and scripts/ exist.
```

Manual install:

```bash
git clone https://github.com/RyanZheng5588/skills-dashboard.git ~/.codex/skills/skill-dashboard
```

## Use

After installation, ask Codex:

```text
Use $skill-dashboard to open the local skill dashboard.
```

The simplest macOS one-click start is:

```bash
open ~/.codex/skills/skill-dashboard/Skill\ Dashboard.command
```

You can also open `~/.codex/skills/skill-dashboard` in Finder and double-click `Skill Dashboard.command`. It starts the local server and opens the browser.

Terminal start:

```bash
~/.codex/skills/skill-dashboard/scripts/start.sh
```

If you installed or refreshed the skill with `scripts/install.sh`, it also creates this short command:

```bash
skill-dashboard
```

Update Skill Dashboard:

```bash
open ~/.codex/skills/skill-dashboard/Skill\ Dashboard\ Update.command
```

Or:

```bash
skill-dashboard-update
```

If you installed manually with `git clone`, you can still use:

```bash
cd ~/.codex/skills/skill-dashboard
git pull --ff-only
```

The lower-level builder is still available for custom options:

```bash
python3 ~/.codex/skills/skill-dashboard/scripts/skill_dashboard.py --serve --open
```

Add custom scan roots:

```bash
python3 ~/.codex/skills/skill-dashboard/scripts/skill_dashboard.py --root ~/my-skills --open
```

## Features

- Scans common local roots: Codex, Claude, Hermes, agent skills, and Codex plugin caches.
- Browse by platform: Codex, Claude, Hermes, and Other.
- Browse by use case: copy, images, video, slides, layout, data, code, knowledge, automation, design, docs, audio, research, and more.
- Fuzzy search across skill names, descriptions, usage notes, categories, platforms, and paths.
- Detects git-installed skills and supports click-to-update in localhost mode.
- Card-based directory with pagination, ranking rail, and click-through detail drawer.
- Bilingual UI: Chinese and English.
- Theme switching: Orbit dark theme and Daylight light theme.
- Local example previews that do not consume tokens or call external services.
- Python standard library only for the dashboard builder.

## Good Fit / Poor Fit

**Good fit**: local skill inventory, skill discovery, comparing Codex/Claude/Hermes skills, team demos, open-source skill repo audits.

**Poor fit**: cloud-hosted multi-user management, remote skill marketplace sync, automatic third-party skill installation, or replacing the agent's own skill routing.

## Layout

```text
SKILL.md
agents/openai.yaml
assets/dashboard.html
references/classification.md
scripts/
  skill_dashboard.py
  start.sh
  update.sh
  install.sh
  check.sh
Skill Dashboard.command
Skill Dashboard Update.command
```

## Development

Run checks:

```bash
./scripts/check.sh
```

Build a preview without installing:

```bash
python3 scripts/skill_dashboard.py --out /tmp/skill-dashboard-preview --quiet
open /tmp/skill-dashboard-preview/index.html
```

Install the working tree version:

```bash
./scripts/install.sh
```

The install script copies the skill into `~/.codex/skills/skill-dashboard` and creates `~/.local/bin/skill-dashboard` plus `~/.local/bin/skill-dashboard-update`.

## Privacy

This tool reads local `SKILL.md` files and writes a generated `.dashboard/` output. That output may contain local paths, skill names, and descriptions. It is intentionally ignored by git.

Do not commit `.dashboard/` unless you have reviewed it and intentionally want to publish that data.

## License

MIT
