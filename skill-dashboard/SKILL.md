---
name: skill-dashboard
description: Build and open an interactive local dashboard for discovering installed skills across Codex, Claude, Hermes, agents, and plugin caches. Use when the user asks to browse, search, classify, audit, preview, or compare local skills; when they want card-based skill inventory views; or when they want examples and usage details generated from SKILL.md files.
---

# Skill Dashboard

## Quick Start

Run the bundled builder:

```bash
python3 ~/.codex/skills/skill-dashboard/scripts/skill_dashboard.py --open
```

This scans local skill roots, writes a self-contained bilingual dashboard to `~/.codex/skills/skill-dashboard/.dashboard/index.html`, and opens it in the browser.

For a localhost URL instead:

```bash
python3 ~/.codex/skills/skill-dashboard/scripts/skill_dashboard.py --serve --open
```

## Workflow

1. Scan local skills with `scripts/skill_dashboard.py`.
2. Open the generated dashboard file or serve it on localhost.
3. Use platform tabs for `Codex`, `Claude`, `Hermes`, and `Other`.
4. Use category chips for usage dimensions such as `文案`, `图片`, `视频`, `PPT`, `排版`, `数据`, `代码`, `知识库`, `自动化`, `设计`, `文档`, `音频`, and `研究`.
5. Use fuzzy search for skill name, display name, description, purpose, category, platform, and path.
6. Click a card to inspect purpose, source path, parsed usage sections, and example previews.
7. Switch between Chinese and English UI labels, and between the Orbit dark theme and Daylight light theme.

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

Dashboard examples start empty. The browser can generate local previews from scanned metadata without tokens or external services.

If the user asks for high-fidelity examples, real generated images, video renders, PPT files, or long model-authored examples, first state that the action may consume tokens or require configured providers, then ask for confirmation before generating.

## Maintenance

Read `references/classification.md` before changing platform or usage-category inference rules.

Edit `assets/dashboard.html` for the UI shell and `scripts/skill_dashboard.py` for scanning, classification, build, and serving behavior.
