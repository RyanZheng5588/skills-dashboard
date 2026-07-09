#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_ROOT="${CODEX_HOME:-$HOME/.codex}/skills"
DEST_DIR="$DEST_ROOT/skill-dashboard"

if [[ ! -f "$ROOT_DIR/SKILL.md" ]]; then
  echo "Cannot find SKILL.md in $ROOT_DIR" >&2
  exit 1
fi

mkdir -p "$DEST_ROOT"

if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete \
    --exclude ".git" \
    --exclude ".dashboard" \
    --exclude "__pycache__" \
    "$ROOT_DIR/" "$DEST_DIR/"
else
  rm -rf "$DEST_DIR"
  mkdir -p "$DEST_DIR"
  cp -R "$ROOT_DIR/." "$DEST_DIR/"
fi

rm -rf "$DEST_DIR/.git" "$DEST_DIR/.dashboard" "$DEST_DIR"/scripts/__pycache__
chmod +x "$DEST_DIR/scripts/start.sh" "$DEST_DIR/scripts/install.sh" "$DEST_DIR/scripts/check.sh" "$DEST_DIR/Skill Dashboard.command"

BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/skill-dashboard" <<EOF
#!/usr/bin/env bash
exec "$DEST_DIR/scripts/start.sh" "\$@"
EOF
chmod +x "$BIN_DIR/skill-dashboard"

echo "Installed skill-dashboard to $DEST_DIR"
echo "One-click start on macOS: open \"$DEST_DIR/Skill Dashboard.command\""
echo "Terminal start: skill-dashboard"
echo "Direct start: \"$DEST_DIR/scripts/start.sh\""

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "Tip: add $BIN_DIR to PATH if the skill-dashboard command is not found." ;;
esac
