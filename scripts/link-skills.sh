#!/usr/bin/env bash
set -euo pipefail

# Symlinks every skill in this repo into ~/.claude/skills, and every
# skill-bundled subagent (skills/<bucket>/<name>/agents/*.md) into
# ~/.claude/agents, so Claude Code can discover and load them while you
# develop qsbn-agent-skills itself. A subagent lives inside the skill that
# owns it - see CLAUDE.md's "Agents" section for why - this script just
# also mirrors it to ~/.claude/agents for local testing, the same place a
# skill's own self-install step would put it in a real install. This is for
# local development of THIS repo only - do not use this to install
# qsbn-agent-skills into a real tracking repo, which must get its own copy
# (see README.md). Re-run after adding, removing, or renaming a skill or
# agent.

REPO="$(cd "$(dirname "$0")/.." && pwd)"

link_into() {
  local dest="$1"

  if [ -L "$dest" ]; then
    local resolved
    resolved="$(readlink -f "$dest")"
    case "$resolved" in
      "$REPO"|"$REPO"/*)
        echo "error: $dest is a symlink into this repo ($resolved)." >&2
        echo "Remove it (rm \"$dest\") and re-run; the script will recreate it as a real dir." >&2
        exit 1
        ;;
    esac
  fi

  mkdir -p "$dest"
}

DEST_SKILLS="$HOME/.claude/skills"
link_into "$DEST_SKILLS"

found=0
while IFS= read -r -d '' skill_md; do
  src="$(dirname "$skill_md")"
  name="$(basename "$src")"
  target="$DEST_SKILLS/$name"

  if [ -e "$target" ] && [ ! -L "$target" ]; then
    rm -rf "$target"
  fi

  ln -sfn "$src" "$target"
  echo "linked $name -> $src"
  found=$((found + 1))
done < <(find "$REPO/skills" -name SKILL.md -not -path '*/deprecated/*' -print0 2>/dev/null)

if [ "$found" -eq 0 ]; then
  echo "no skills found under $REPO/skills yet"
fi

DEST_AGENTS="$HOME/.claude/agents"
link_into "$DEST_AGENTS"

agents_found=0
while IFS= read -r -d '' agent_md; do
  name="$(basename "$agent_md")"
  target="$DEST_AGENTS/$name"

  if [ -e "$target" ] && [ ! -L "$target" ]; then
    rm -f "$target"
  fi

  ln -sfn "$agent_md" "$target"
  echo "linked $name -> $agent_md"
  agents_found=$((agents_found + 1))
done < <(find "$REPO/skills" -path '*/agents/*.md' -print0 2>/dev/null)

if [ "$agents_found" -eq 0 ]; then
  echo "no skill-bundled agents found under $REPO/skills/*/*/agents yet"
fi
