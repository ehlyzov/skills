#!/usr/bin/env bash
set -euo pipefail
INPUT=""
INPUT_FILE=""
TYPE=""
PYTHON_BIN="${PYTHON_BIN:-python3}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input) INPUT="$2"; shift 2 ;;
    --input-file) INPUT_FILE="$2"; shift 2 ;;
    --type) TYPE="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$INPUT" && -n "$INPUT_FILE" ]]; then
  INPUT="$(cat "$INPUT_FILE")"
fi
if [[ -z "$INPUT" ]]; then
  echo "provide --input or --input-file" >&2
  exit 2
fi

export INPUT TYPE
"$PYTHON_BIN" - <<'PY'
import json, os
text = os.environ['INPUT'].strip()
forced = os.environ.get('TYPE', '').strip().lower()

def classify(t: str) -> str:
    if forced:
        return forced
    tl = t.lower()
    if any(x in tl for x in ['tradeoff', 'decision', 'decided', 'alternative']):
        return 'decision'
    if any(x in tl for x in ['verify', 'test', 'lint', 'ci', 'cannot verify locally', 'evidence']):
        return 'verification'
    if any(x in tl for x in ['runbook', 'restart', 'recovery', 'incident', 'procedure', 'how to recover']):
        return 'operational'
    if any(x in tl for x in ['entrypoint', 'boundary', 'topology', 'module', 'schema', 'integration']):
        return 'structural'
    if any(x in tl for x in ['term', 'meaning', 'definition', 'ambiguous']):
        return 'terminology'
    return 'discard'

kind = classify(text)
home = {
    'structural': 'docs/service/SERVICE_MAP.md',
    'verification': 'docs/service/VERIFY.md',
    'operational': 'docs/service/runbooks/<name>.md',
    'terminology': 'docs/service/GLOSSARY.md',
    'decision': 'docs/service/ADR/<id>-<title>.md',
    'discard': None,
}[kind]
print(json.dumps({
    'classification': kind,
    'proposed_home': home,
    'should_create_event_driven_doc': kind in {'operational', 'terminology', 'decision'},
    'notes': [
        'Promote to exactly one canonical or event-driven home.',
        'Delete or expire the transient source after promotion.',
        'Do not duplicate the same durable learning across multiple files.'
    ]
}, indent=2, ensure_ascii=False))
PY
