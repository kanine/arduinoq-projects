#!/bin/bash
# sync-skills.sh
# Two-way sync between .agents/skills/ and .claude/skills/.
# Newest file wins on conflict. Run from project root.

set -e

DIR_A=".agents/skills"
DIR_B=".claude/skills"

mkdir -p "$DIR_A" "$DIR_B"

updated_b=0
updated_a=0

# Pass 1: sync A → B (new or newer files in A go to B)
while IFS= read -r -d '' file; do
  rel="${file#"$DIR_A"/}"
  dst="$DIR_B/$rel"

  if [ ! -f "$dst" ]; then
    mkdir -p "$(dirname "$dst")"
    cp -p "$file" "$dst"
    echo "  + $DIR_B/$rel  (new)"
    updated_b=$((updated_b + 1))
  else
    src_time=$(stat -c %Y "$file")
    dst_time=$(stat -c %Y "$dst")
    if [ "$src_time" -gt "$dst_time" ]; then
      cp -p "$file" "$dst"
      echo "  ^ $DIR_B/$rel  (newer in $DIR_A)"
      updated_b=$((updated_b + 1))
    fi
  fi
done < <(find "$DIR_A" -type f -print0 | sort -z)

# Pass 2: sync B → A (new or newer files in B go to A)
while IFS= read -r -d '' file; do
  rel="${file#"$DIR_B"/}"
  dst="$DIR_A/$rel"

  if [ ! -f "$dst" ]; then
    mkdir -p "$(dirname "$dst")"
    cp -p "$file" "$dst"
    echo "  + $DIR_A/$rel  (new)"
    updated_a=$((updated_a + 1))
  else
    src_time=$(stat -c %Y "$file")
    dst_time=$(stat -c %Y "$dst")
    if [ "$src_time" -gt "$dst_time" ]; then
      cp -p "$file" "$dst"
      echo "  ^ $DIR_A/$rel  (newer in $DIR_B)"
      updated_a=$((updated_a + 1))
    fi
  fi
done < <(find "$DIR_B" -type f -print0 | sort -z)

echo ""
echo "✓ $DIR_A ↔ $DIR_B synced  ($updated_b file(s) updated in B, $updated_a file(s) updated in A)"
echo "Done."
