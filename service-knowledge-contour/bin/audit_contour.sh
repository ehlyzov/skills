#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
mkdir -p "$ROOT/docs/service/generated"

"$PYTHON_BIN" - "$ROOT" <<'PY'
import datetime as dt
import json, re, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
gen = root / 'docs' / 'service' / 'generated'
gen.mkdir(parents=True, exist_ok=True)
required = [
    root / 'AGENTS.md',
    root / 'CLAUDE.md',
    root / 'docs/service/SERVICE_MAP.md',
    root / 'docs/service/VERIFY.md',
    root / 'docs/service/knowledge-gaps.yaml',
    root / 'docs/service/generated/change-surface.json',
    root / 'docs/service/generated/hotspots.md',
]
errors, warnings = [], []

def err(msg): errors.append(msg)
def warn(msg): warnings.append(msg)

for p in required:
    if not p.exists():
        err(f"missing required file: {p.relative_to(root)}")
    elif p.is_file() and p.stat().st_size == 0:
        err(f"empty required file: {p.relative_to(root)}")

link_pattern = re.compile(r'`([^`]+)`')
for doc in [root / 'AGENTS.md', root / 'CLAUDE.md', root / 'docs/service/SERVICE_MAP.md', root / 'docs/service/VERIFY.md']:
    if not doc.exists():
        continue
    text = doc.read_text(encoding='utf-8', errors='ignore')
    for match in link_pattern.findall(text):
        if '/' in match or match.endswith(('.md', '.yaml', '.json')):
            target = (root / match).resolve()
            if not target.exists():
                err(f"dead reference in {doc.relative_to(root)} -> {match}")

agents = root / 'AGENTS.md'
if agents.exists():
    txt = agents.read_text(encoding='utf-8', errors='ignore')
    if 'TODO' in txt or 'TBD' in txt or 'TODO-CHECK' in txt:
        err('AGENTS.md contains forbidden placeholders')

kg = root / 'docs/service/knowledge-gaps.yaml'
if kg.exists():
    text = kg.read_text(encoding='utf-8', errors='ignore')
    entries, current = [], None
    in_gaps = False
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if stripped == 'gaps:' or stripped.startswith('gaps:'):
            in_gaps = True
            continue
        if not in_gaps:
            continue
        if stripped.startswith('- '):
            if current:
                entries.append(current)
            current = {}
            rest = stripped[2:]
            if ': ' in rest:
                k, v = rest.split(': ', 1)
                current[k.strip()] = v.strip().strip('"')
        elif current is not None and ': ' in stripped:
            k, v = stripped.split(': ', 1)
            current[k.strip()] = v.strip().strip('"')
    if current:
        entries.append(current)
    today = dt.date.today()
    for idx, item in enumerate(entries, start=1):
        needed = ['id', 'fact', 'why_missing', 'owner', 'created_on', 'expires_on', 'promotion_target', 'status']
        missing = [k for k in needed if not item.get(k)]
        if missing:
            err(f"knowledge gap item {idx} missing fields: {', '.join(missing)}")
            continue
        try:
            expires = dt.date.fromisoformat(item['expires_on'])
            if expires < today:
                err(f"expired knowledge gap: {item['id']}")
        except Exception:
            err(f"knowledge gap invalid expires_on: {item.get('id', idx)}")

startup = ''
for doc in [root / 'AGENTS.md', root / 'CLAUDE.md']:
    if doc.exists():
        startup += doc.read_text(encoding='utf-8', errors='ignore') + '\n'
canon = ''
for doc in [root / 'docs/service/SERVICE_MAP.md', root / 'docs/service/VERIFY.md']:
    if doc.exists():
        canon += doc.read_text(encoding='utf-8', errors='ignore') + '\n'
startup_lines = {x.strip() for x in startup.splitlines() if len(x.strip()) > 40}
canon_lines = {x.strip() for x in canon.splitlines() if len(x.strip()) > 40}
if len(startup_lines & canon_lines) > 3:
    warn('startup docs duplicate canonical docs excessively')

for rel in ['docs/service/SERVICE_MAP.md', 'docs/service/VERIFY.md']:
    p = root / rel
    if p.exists() and len(p.read_text(encoding='utf-8', errors='ignore').splitlines()) > 220:
        warn(f'oversized canonical doc: {rel}')

verify = root / 'docs/service/VERIFY.md'
invalid_cmds = []
if verify.exists():
    text = verify.read_text(encoding='utf-8', errors='ignore')
    for line in text.splitlines():
        m = re.match(r'^\s*-\s+(.+)$', line)
        if not m:
            continue
        cmd = m.group(1).strip()
        if not any(cmd.startswith(prefix) for prefix in ['npm ', 'pnpm ', 'yarn ', 'python ', 'pytest', 'ruff', 'mypy', 'go ', 'make ', 'cargo ']):
            continue
        if cmd.startswith('npm ') and not (root / 'package.json').exists():
            invalid_cmds.append(cmd)
        if cmd.startswith(('pytest', 'python ', 'ruff', 'mypy')) and not (root / 'pyproject.toml').exists() and not (root / 'requirements.txt').exists():
            invalid_cmds.append(cmd)
        if cmd.startswith('go ') and not (root / 'go.mod').exists():
            invalid_cmds.append(cmd)
        if cmd.startswith('make ') and not (root / 'Makefile').exists():
            invalid_cmds.append(cmd)
if invalid_cmds:
    warn('commands referenced in VERIFY may be invalid for the current repo: ' + '; '.join(invalid_cmds[:10]))

surface = root / 'docs/service/generated/change-surface.json'
if surface.exists():
    try:
        payload = json.loads(surface.read_text(encoding='utf-8'))
        changed = set(payload.get('changed_files') or [])
        missing_updates = []
        for trigger in payload.get('triggers') or []:
            for rel in trigger.get('update') or []:
                if rel not in changed:
                    missing_updates.append(rel)
        for rel in sorted(set(missing_updates)):
            warn(f'contour trigger fired but {rel} was not changed')
    except Exception:
        warn('change-surface.json could not be parsed for trigger drift checks')

report = {
    'status': 'generated',
    'audit_ok': not errors,
    'errors': errors,
    'warnings': warnings,
    'generated_on': dt.datetime.now(dt.UTC).isoformat().replace('+00:00', 'Z'),
}
(gen / 'health-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2, ensure_ascii=False))
if errors:
    sys.exit(1)
PY
