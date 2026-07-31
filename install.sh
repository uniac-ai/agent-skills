#!/usr/bin/env bash
# Install every skill in ./skills/ through the global entry ~/.agents/skills/:
#
#   ~/.agents/skills/<name>  ->  <this checkout>/skills/<name>   (global entry)
#   ~/.claude/skills/<name>  ->  ../../.agents/skills/<name>     (Claude Code)
#   ~/.codex/skills/<name>   ->  ../../.agents/skills/<name>     (Codex)
#
# Every agent consumes the same copy, and that copy is this checkout — content
# edits are live through the links without re-installing.
# Idempotent. Re-run anytime — updates links, never clobbers a real directory.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
GLOBAL="$HOME/.agents/skills"
# Each agent dir sits exactly at $HOME/<agent>/skills, so the relative target
# ../../.agents/skills/<name> resolves from all of them.
AGENT_DIRS=("$HOME/.claude/skills" "$HOME/.codex/skills")

link() { # link <target> <linkpath>
  if [[ -e "$2" && ! -L "$2" ]]; then
    echo "WARN: $2 exists and is not a symlink — skipping" >&2
    return
  fi
  ln -sfn "$1" "$2"
  echo "linked: $2 -> $1"
}

mkdir -p "$GLOBAL" "${AGENT_DIRS[@]}"

for skill_dir in "$REPO_DIR"/skills/*/; do
  [ -d "$skill_dir" ] || continue
  name=$(basename "$skill_dir")
  link "${skill_dir%/}" "$GLOBAL/$name"
  for agent_dir in "${AGENT_DIRS[@]}"; do
    link "../../.agents/skills/$name" "$agent_dir/$name"
  done
done
