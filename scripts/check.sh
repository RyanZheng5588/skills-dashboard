#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_DIR="$ROOT_DIR/skill-dashboard"
OUT_DIR="$(mktemp -d "${TMPDIR:-/tmp}/skill-dashboard-check.XXXXXX")"
trap 'rm -rf "$OUT_DIR"' EXIT

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile "$SKILL_DIR/scripts/skill_dashboard.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/skill_dashboard.py" --out "$OUT_DIR" --quiet

python3 - "$OUT_DIR" <<'PY'
import json
import sys
from html.parser import HTMLParser
from pathlib import Path

out = Path(sys.argv[1])
data = json.loads((out / "skills-data.json").read_text(encoding="utf-8"))
if not isinstance(data.get("skills"), list):
    raise SystemExit("skills-data.json is missing a skills list")
HTMLParser().feed((out / "index.html").read_text(encoding="utf-8"))
print(f"Built dashboard with {data.get('skillCount', len(data['skills']))} skills")
PY

VALIDATOR="$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py"
if [[ -f "$VALIDATOR" ]]; then
  PYTHONDONTWRITEBYTECODE=1 python3 "$VALIDATOR" "$SKILL_DIR"
else
  echo "Skipped Codex skill validation; validator not found at $VALIDATOR"
fi
