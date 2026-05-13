#!/usr/bin/env bash
# Синхронизирует skill из ~/.claude/skills/product-workflow/ в ~/.codex/skills/product-workflow/.
# Запускать после любых правок в Claude-копии, чтобы Codex видел те же изменения.
set -euo pipefail

SRC="${HOME}/.claude/skills/product-workflow"
DST="${HOME}/.codex/skills/product-workflow"

[[ -d "$SRC" ]] || { echo "ERROR: $SRC не существует" >&2; exit 1; }

mkdir -p "$(dirname "$DST")"
rm -rf "$DST"
cp -r "$SRC" "$DST"

echo "Synced: $SRC → $DST"
diff -rq "$SRC" "$DST" 2>&1 | grep -v "Only in" | head -5 || true
echo "(пустой diff = синхронизация успешна)"
