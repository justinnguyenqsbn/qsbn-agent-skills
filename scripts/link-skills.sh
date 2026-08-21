#!/usr/bin/env bash
set -euo pipefail

# Symlinks every skill in this repo into ~/.claude/skills so Claude Code can
# discover and load them while you develop qsbn-agent-skills itself. This is
# for local development of THIS repo only - do not use this to install
# qsbn-agent-skills into a real tracking repo, which must get its own copy
# (see README.md). Re-run after adding, removing, or renaming a skill.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$HOME/.claude/skills"

if [ -L "$DEST" ]; then
  resolved="$(readlink -f "$DEST")"
  case "$resolved" in
    "$REPO"|"$REPO"/*)
      echo "error: $DEST is a symlink into this repo ($resolved)." >&2
      echo "Remove it (rm \"$DEST\") and re-run; the script will recreate it as a real dir." >&2
      exit 1
      ;;
  esac
fi

mkdir -p "$DEST"

found=0
while IFS= read -r -d '' skill_md; do
  src="$(dirname "$skill_md")"
  name="$(basename "$src")"
  target="$DEST/$name"

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
