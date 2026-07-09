---
name: skill-dashboard
description: Build, open, and update an interactive local dashboard for discovering installed skills across System, Codex, Claude, Hermes, agents, and plugin caches. Use when the user asks to browse, search, classify, audit, preview, update, compare, open paths for, copy branch prompts for, or generate real examples from local skills; when they want card-based skill inventory views; or when they want bilingual introductions and usage guidance generated from SKILL.md files.
---

# Skill Dashboard

## Quick Start

Use the bundled one-click launcher first:

```bash
~/.codex/skills/skill-dashboard/scripts/start.sh
```

On macOS, the same launcher can be opened from Finder by double-clicking `~/.codex/skills/skill-dashboard/Skill Dashboard.command`.

If `scripts/install.sh` has been run, the short command is also available:

```bash
skill-dashboard
```

This scans local skill roots, writes a self-contained bilingual dashboard to `~/.codex/skills/skill-dashboard/.dashboard/index.html`, starts a localhost service, and opens it in the browser.

To update Skill Dashboard itself, use:

```bash
~/.codex/skills/skill-dashboard/scripts/update.sh
```

On macOS, the same updater can be opened from Finder by double-clicking `~/.codex/skills/skill-dashboard/Skill Dashboard Update.command`. If `scripts/install.sh` has been run, `skill-dashboard-update` is also available.

For advanced custom options, call the builder directly:

```bash
python3 ~/.codex/skills/skill-dashboard/scripts/skill_dashboard.py --serve --open
```

## Workflow

1. Scan local skills with `scripts/skill_dashboard.py`.
2. Open the generated dashboard file or serve it on localhost.
3. Use platform tabs for `System`, `Codex`, `Claude`, `Hermes`, and `Other`; system-level skills are intentionally separated from user skills.
4. Use category chips for usage dimensions such as `文案`, `图片`, `视频`, `PPT`, `排版`, `数据`, `代码`, `知识库`, `自动化`, `设计`, `文档`, `音频`, and `研究`.
5. Use fuzzy search for skill name, display name, generated introduction, purpose, category, platform, path, and git remote.
6. Click a card to inspect generated bilingual introductions, purpose chips, local source links, usage guidance, branch/variant prompts, and examples. Do not expose raw SKILL.md body text in the UI.
7. Click local paths to open folders or files. In localhost mode this uses the local `/api/open-path` endpoint; in static file mode it falls back to file URLs when available.
8. Use branch/variant cards to copy or run focused prompts for different tones, styles, or use types.
9. Use the real example action to call local Codex CLI and write artifacts into `.dashboard/real-examples/`. Confirm token/provider/local-app requirements before running.
10. Use the update section in a detail drawer to copy update commands or update git-installed skills when the dashboard is running in localhost mode.
11. Switch between Chinese and English UI labels, and between the Orbit dark theme and Daylight light theme.

## Custom Roots

Add roots with either `--root` or `SKILL_DASHBOARD_ROOTS`:

```bash
python3 ~/.codex/skills/skill-dashboard/scripts/skill_dashboard.py --root ~/my-skills --open
SKILL_DASHBOARD_ROOTS="$HOME/work/skills:$HOME/.custom/skills" python3 ~/.codex/skills/skill-dashboard/scripts/skill_dashboard.py --open
```

The scanner already includes common roots:

- `~/.codex/skills`
- `~/.agents/skills`
- `~/.claude/skills`
- `~/.claude/commands`
- `~/.hermes/skills`
- `~/.codex/plugins/cache/**/skills`

## Examples

Dashboard examples start empty. The browser can generate metadata-only local previews without tokens, or real examples through the localhost API.

If the user asks for high-fidelity examples, real generated images, video renders, PPT files, or long model-authored examples, first state that the action may consume tokens or require configured providers, then ask for confirmation before generating. Real generation uses Codex CLI when available or reports the missing configuration.

## Maintenance

Read `references/classification.md` before changing platform or usage-category inference rules.

Edit `assets/dashboard.html` for the UI shell and `scripts/skill_dashboard.py` for scanning, classification, build, and serving behavior.
