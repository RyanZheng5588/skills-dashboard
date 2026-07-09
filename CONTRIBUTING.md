# Contributing

Thanks for improving Skill Dashboard.

## Local Checks

Run:

```bash
./scripts/check.sh
```

The check script:

- compiles the Python builder
- builds a temporary dashboard
- parses the generated HTML
- runs Codex skill validation when the local validator exists

## Guidelines

- Keep `SKILL.md` concise and focused on agent-facing workflow.
- Put deterministic behavior in `scripts/skill_dashboard.py`.
- Put UI changes in `assets/dashboard.html`.
- Update `references/classification.md` when changing platform or use-case inference.
- Do not commit `.dashboard/` output; it may contain local paths and private skill metadata.

## Release Checklist

1. Run `./scripts/check.sh`.
2. Confirm `git status --short` has only intentional changes.
3. Verify README install commands still match the repository layout.
4. Push to `main` after review.
