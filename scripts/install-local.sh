#!/usr/bin/env bash
set -euo pipefail

# Installs qsbn-agent-skills into a target tracking repo, from this local
# checkout - a stand-in for `npx skills@latest add <owner>/qsbn-agent-skills`
# until this repo has a remote to publish from. Copies by default, matching
# the real install's semantics (each tracking repo owns its own copy); pass
# --link to symlink instead, for fast local iteration while developing a
# skill here.
#
# Usage:
#   scripts/install-local.sh <target-dir> [--link]

if [ "${1:-}" = "" ]; then
  echo "usage: scripts/install-local.sh <target-dir> [--link]" >&2
  exit 1
fi

TARGET="$(cd "$1" && pwd)"
MODE="copy"
if [ "${2:-}" = "--link" ]; then
  MODE="link"
fi

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST_SKILLS="$TARGET/.claude/skills"
DEST_COMMANDS="$TARGET/.claude/commands/qsbn"

mkdir -p "$DEST_SKILLS" "$DEST_COMMANDS"

place() {
  local src="$1" dest="$2"
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    rm -rf "$dest"
  fi
  if [ "$MODE" = "link" ]; then
    ln -sfn "$src" "$dest"
  else
    cp -R "$src" "$dest"
  fi
}

found=0
while IFS= read -r -d '' skill_md; do
  src="$(dirname "$skill_md")"
  name="$(basename "$src")"
  place "$src" "$DEST_SKILLS/$name"
  echo "$MODE: $name -> $DEST_SKILLS/$name"
  found=$((found + 1))
done < <(find "$REPO/skills" -name SKILL.md -not -path '*/deprecated/*' -print0 2>/dev/null)

for cmd in "$REPO"/commands/qsbn/*.md; do
  [ -e "$cmd" ] || continue
  place "$cmd" "$DEST_COMMANDS/$(basename "$cmd")"
done

if [ "$found" -eq 0 ]; then
  echo "no skills found under $REPO/skills yet"
fi

echo "done ($MODE mode) - target: $TARGET"
