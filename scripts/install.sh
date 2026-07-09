#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="$ROOT_DIR/skill-dashboard"
DEST_ROOT="${CODEX_HOME:-$HOME/.codex}/skills"
DEST_DIR="$DEST_ROOT/skill-dashboard"

if [[ ! -f "$SOURCE_DIR/SKILL.md" ]]; then
  echo "Cannot find skill source: $SOURCE_DIR" >&2
  exit 1
fi

mkdir -p "$DEST_ROOT"

if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete \
    --exclude ".dashboard" \
    --exclude "__pycache__" \
    "$SOURCE_DIR/" "$DEST_DIR/"
else
  rm -rf "$DEST_DIR"
  mkdir -p "$DEST_DIR"
  cp -R "$SOURCE_DIR/." "$DEST_DIR/"
  rm -rf "$DEST_DIR/.dashboard" "$DEST_DIR"/scripts/__pycache__
fi

echo "Installed skill-dashboard to $DEST_DIR"
echo "Run: python3 \"$DEST_DIR/scripts/skill_dashboard.py\" --open"
