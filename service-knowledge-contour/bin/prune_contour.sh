#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

"$PYTHON_BIN" - "$ROOT" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
candidates = []

for rel in ['docs/service/SERVICE_MAP.md', 'docs/service/VERIFY.md']:
    p = root / rel
    if not p.exists():
        continue
    text = p.read_text(encoding='utf-8', errors='ignore')
    lines = [x for x in text.splitlines() if x.strip()]
    reasons = []
    action = None
    if len(lines) < 8:
        reasons.append('near-empty canonical doc')
        action = 'merge-or-delete'
    todo_count = text.count('TODO') + text.count('TBD') + text.count('TODO-CHECK')
    if todo_count > 5:
        reasons.append('placeholder-heavy')
        action = action or 'delete-or-rewrite'
    if len(text.splitlines()) > 260:
        reasons.append('oversized canonical doc')
        action = action or 'split-if-overload-proven'
    if reasons:
        candidates.append({'path': rel, 'recommended_action': action, 'reasons': reasons})

for base in [root / 'docs/service/ADR', root / 'docs/service/runbooks', root / 'docs/service/incidents', root / 'docs/service/migrations']:
    if not base.exists():
        continue
    for p in base.rglob('*.md'):
        lines = [x for x in p.read_text(encoding='utf-8', errors='ignore').splitlines() if x.strip()]
        if len(lines) < 6:
            candidates.append({'path': p.relative_to(root).as_posix(), 'recommended_action': 'delete', 'reasons': ['event-driven doc appears low-signal or near-empty']})

refs = ''
for doc in [root / 'AGENTS.md', root / 'CLAUDE.md', root / 'docs/service/SERVICE_MAP.md', root / 'docs/service/VERIFY.md']:
    if doc.exists():
        refs += doc.read_text(encoding='utf-8', errors='ignore') + '\n'
for p in (root / 'docs/service').rglob('*.md'):
    rel = p.relative_to(root).as_posix()
    if rel in {'docs/service/SERVICE_MAP.md', 'docs/service/VERIFY.md'}:
        continue
    if '/generated/' in rel:
        continue
    if rel not in refs:
        candidates.append({'path': rel, 'recommended_action': 'review-delete-or-link', 'reasons': ['no obvious read path from startup or canonical core']})

print(json.dumps({'prune_candidates': candidates}, indent=2, ensure_ascii=False))
PY
