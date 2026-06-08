#!/usr/bin/env bash
#
# Installs the three-tier model router into your user-level Claude Code config.
#
#   - Copies the `deep-work` and `quick` subagents into ~/.claude/agents/
#   - Sets "model": "sonnet" as your session default (only if you haven't set one)
#   - Appends the routing rubric to ~/.claude/CLAUDE.md (idempotent, marker-guarded)
#
# Safe to re-run. Backs up settings.json before touching it. Honors $CLAUDE_CONFIG_DIR.

set -euo pipefail

CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
AGENTS_DIR="$CLAUDE_DIR/agents"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$AGENTS_DIR"

# 1. Subagents -----------------------------------------------------------------
cp "$REPO_DIR/agents/deep-work.md" "$AGENTS_DIR/deep-work.md"
cp "$REPO_DIR/agents/quick.md"     "$AGENTS_DIR/quick.md"
echo "✓ Installed subagents: deep-work (Opus), quick (Haiku)"

# 2. settings.json default model ----------------------------------------------
# Uses setdefault semantics: we never overwrite a model you've already chosen.
SETTINGS="$CLAUDE_DIR/settings.json"
python3 - "$SETTINGS" <<'PY'
import json, os, shutil, sys
path = sys.argv[1]
data = {}
if os.path.exists(path):
    with open(path) as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("! settings.json isn't valid JSON — leaving it untouched. "
                  "Add  \"model\": \"sonnet\"  manually.")
            sys.exit(0)
    shutil.copy(path, path + ".bak")

if "model" in data:
    print(f'• settings.json already pins "model": "{data["model"]}" — left as-is. '
          f'Change to "sonnet" manually if you want the router default.')
else:
    data["model"] = "claude-sonnet-4-6"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print('✓ Set "model": "claude-sonnet-4-6" as session default')
PY

# 3. Routing rubric in CLAUDE.md ----------------------------------------------
CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
RUBRIC_SRC="$REPO_DIR/CLAUDE.routing.md"
START="<!-- BEGIN overkill -->"
END="<!-- END overkill -->"

if [ -f "$CLAUDE_MD" ] && grep -qF "$START" "$CLAUDE_MD"; then
  echo "• Routing rubric already present in CLAUDE.md — skipped (edit between the markers to update)."
else
  {
    printf '\n%s\n' "$START"
    cat "$RUBRIC_SRC"
    printf '%s\n' "$END"
  } >> "$CLAUDE_MD"
  echo "✓ Appended routing rubric to CLAUDE.md"
fi

echo
echo "Done. Start a new Claude Code session for the changes to take effect."
