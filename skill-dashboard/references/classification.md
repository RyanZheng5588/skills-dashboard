# Classification Reference

Use these dimensions when maintaining the dashboard scanner or interpreting its output.

## Platform

- Codex: paths under `~/.codex`, OpenAI/Codex plugin skills, or skill text mentioning Codex/OpenAI.
- Claude: paths under `~/.claude`, or skill text mentioning Claude/Anthropic/Claude Code.
- Hermes: paths under `~/.hermes`, or skill text mentioning Hermes.
- Other: skills that do not match the above.

Skills may appear in multiple platform tabs when their path or instructions mention multiple agent systems.

## Usage Categories

- 文案: writing, copywriting, translation, article drafting, titles, social posts, prompts.
- 图片: image generation/editing, posters, covers, illustrations, comics, screenshots, visual assets.
- 视频: video, film, storyboard, Remotion, HyperFrames, YouTube, transcripts.
- PPT: slides, presentation decks, PowerPoint, teaching decks.
- 排版: markdown/HTML/rich text formatting, WeChat article layout, print cleanup, typography.
- 数据: analytics, charts, KPI reports, dashboards, spreadsheets, market sizing.
- 代码: coding, repo work, git, debugging, tests, refactoring, plugins, APIs.
- 知识库: wiki, KB, Obsidian, notes, memory, search, ingestion and querying.
- 自动化: workflow, cron, sync, archive, publish, agent orchestration, operations.
- 设计: UI, UX, Figma, product design, frontend polish, web design.
- 文档: DOCX, PDF, document templates, reports, contracts, paper cleanup.
- 音频: audio, speech, voice, podcasts, music, TTS, transcription.
- 研究: research, audit, review, exploration, validation, triage.
- 其他: fallback when no category is confidently inferred.

## Example Generation Policy

Dashboard examples start empty. The browser UI generates local previews from skill metadata and `SKILL.md` snippets; this path does not consume tokens and does not call external services.

For high-fidelity examples that require model output, image generation, video rendering, PPT creation, or other paid/configured tools:

1. State that the action may consume model tokens or require configured providers.
2. Ask for confirmation before starting.
3. Prefer the current Codex App built-in tools and the user's active provider instructions.
4. Store or summarize the resulting example only after the generation succeeds.
