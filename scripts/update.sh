#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_URL="${SKILL_DASHBOARD_REPO:-https://github.com/RyanZheng5588/skills-dashboard.git}"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required to update Skill Dashboard." >&2
  exit 1
fi

is_repo=false
if git -C "$ROOT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  repo_root="$(git -C "$ROOT_DIR" rev-parse --show-toplevel)"
  if [[ "$repo_root" == "$ROOT_DIR" ]]; then
    is_repo=true
  fi
fi

if [[ "$is_repo" == "true" ]]; then
  git -C "$ROOT_DIR" pull --ff-only
else
  tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/skill-dashboard-update.XXXXXX")"
  trap 'rm -rf "$tmp_dir"' EXIT
  git clone --depth 1 "$REPO_URL" "$tmp_dir/repo"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
      --exclude ".git" \
      --exclude ".dashboard" \
      --exclude "__pycache__" \
      "$tmp_dir/repo/" "$ROOT_DIR/"
  else
    shopt -s dotglob nullglob
    for item in "$ROOT_DIR"/*; do
      case "$(basename "$item")" in
        .dashboard|__pycache__) continue ;;
      esac
      rm -rf "$item"
    done
    shopt -u dotglob nullglob
    cp -R "$tmp_dir/repo/." "$ROOT_DIR/"
    rm -rf "$ROOT_DIR/.git"
  fi
fi

chmod +x "$ROOT_DIR/scripts/start.sh" "$ROOT_DIR/scripts/install.sh" "$ROOT_DIR/scripts/check.sh" "$ROOT_DIR/scripts/update.sh"
chmod +x "$ROOT_DIR/Skill Dashboard.command" "$ROOT_DIR/Skill Dashboard Update.command" 2>/dev/null || true

BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/skill-dashboard" <<EOF
#!/usr/bin/env bash
exec "$ROOT_DIR/scripts/start.sh" "\$@"
EOF
chmod +x "$BIN_DIR/skill-dashboard"

cat > "$BIN_DIR/skill-dashboard-update" <<EOF
#!/usr/bin/env bash
exec "$ROOT_DIR/scripts/update.sh" "\$@"
EOF
chmod +x "$BIN_DIR/skill-dashboard-update"

echo "Skill Dashboard updated at $ROOT_DIR"
echo "Start: skill-dashboard"
