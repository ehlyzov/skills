#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
mkdir -p "$ROOT/docs/service/generated"

"$PYTHON_BIN" - "$ROOT" <<'PY'
import json, subprocess, sys, re
from pathlib import Path
root = Path(sys.argv[1]).resolve()
gen = root / "docs" / "service" / "generated"
gen.mkdir(parents=True, exist_ok=True)
CONFIG_NAMES = {
    "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "Makefile", "pyproject.toml",
    "requirements.txt", "poetry.lock", "go.mod", "go.sum", "Cargo.toml", "Cargo.lock", "Dockerfile",
    "docker-compose.yml", "docker-compose.yaml"
}
CI_PATTERNS = [".github/workflows", ".gitlab-ci.yml", "Jenkinsfile", ".circleci", ".azure-pipelines"]
ENTRYPOINT_NAMES = {"main.py", "app.py", "manage.py", "server.py", "index.js", "server.js", "main.ts", "main.go"}

def git(*args):
    try:
        return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return ""

changed_files = []
inside = git("rev-parse", "--is-inside-work-tree")
if inside == "true":
    base = git("rev-parse", "HEAD~1")
    head = git("rev-parse", "HEAD")
    if base and head:
        diff = git("diff", "--name-only", f"{base}..{head}")
        if diff:
            changed_files = [x for x in diff.splitlines() if x.strip()]

entrypoints = []
for p in root.rglob('*'):
    if not p.is_file():
        continue
    rel = p.relative_to(root).as_posix()
    if p.name in ENTRYPOINT_NAMES:
        entrypoints.append(rel)
    elif rel.startswith('cmd/') and p.suffix == '.go':
        entrypoints.append(rel)
entrypoints = sorted(set(entrypoints))[:40]

config_files = []
for p in root.rglob('*'):
    if not p.is_file():
        continue
    rel = p.relative_to(root).as_posix()
    if p.name in CONFIG_NAMES or any(rel.startswith(x) for x in CI_PATTERNS):
        config_files.append(rel)
config_files = sorted(set(config_files))[:80]

modules = []
for name in ["src", "app", "cmd", "internal", "pkg", "service", "services", "api", "lib"]:
    p = root / name
    if p.exists() and p.is_dir():
        modules.append(name)
if not modules:
    for p in root.iterdir():
        if p.is_dir() and not p.name.startswith('.') and p.name not in {'.git', 'node_modules', 'dist', 'build', 'vendor'}:
            modules.append(p.name)
modules = sorted(set(modules))[:20]

adjacent = sorted(set(path.split('/')[0] for path in changed_files if path))[:20]
triggers = []
if any(Path(x).name in CONFIG_NAMES or any(x.startswith(ci) for ci in CI_PATTERNS) for x in changed_files):
    triggers.append({"trigger": "verification-or-build-config-changed", "update": ["docs/service/VERIFY.md"]})
if any(x in entrypoints for x in changed_files) or any(x.startswith(tuple(modules)) for x in changed_files if modules):
    triggers.append({"trigger": "topology-or-entrypoint-changed", "update": ["docs/service/SERVICE_MAP.md"]})
if any(re.search(r"(migrations?|schema|db|sql|generated|proto|vendor|legacy)", x, re.I) for x in changed_files):
    triggers.append({"trigger": "hotspot-or-risk-path-changed", "update": ["docs/service/SERVICE_MAP.md", "docs/service/VERIFY.md"]})

(gen / 'change-surface.json').write_text(json.dumps({
    "status": "generated",
    "confidence": "medium" if changed_files or entrypoints or config_files else "low",
    "changed_files": changed_files,
    "entrypoints": entrypoints,
    "config_files": config_files,
    "top_level_modules": modules,
    "adjacent_paths": adjacent,
    "triggers": triggers,
}, indent=2, ensure_ascii=False) + "\n", encoding='utf-8')

churn = {}
if inside == 'true':
    log = git('log', '--name-only', '--pretty=format:', '-n', '100')
    for line in log.splitlines():
        line = line.strip()
        if not line:
            continue
        top = line.split('/')[0]
        churn[top] = churn.get(top, 0) + 1

danger = []
for p in root.rglob('*'):
    if not p.is_file():
        continue
    rel = p.relative_to(root).as_posix()
    if re.search(r'(migrations?|generated|vendor|dist|build|proto|schema|legacy)', rel, re.I):
        danger.append(rel)
danger = sorted(danger)[:60]

lines = ["# Generated hotspots", "", "This file is generated guidance, not canon.", ""]
if churn:
    lines.append("## High-churn top-level paths")
    for k, v in sorted(churn.items(), key=lambda kv: (-kv[1], kv[0]))[:10]:
        lines.append(f"- `{k}` — recent churn score: {v}")
    lines.append("")
if danger:
    lines.append("## Paths matching fragile-risk heuristics")
    for rel in danger[:20]:
        lines.append(f"- `{rel}`")
    lines.append("")
if changed_files:
    lines.append("## Recently changed paths")
    for rel in changed_files[:20]:
        lines.append(f"- `{rel}`")
    lines.append("")
if not churn and not danger and not changed_files:
    lines.append("No strong hotspot signals were inferred.")
(gen / 'hotspots.md').write_text("\n".join(lines).rstrip() + "\n", encoding='utf-8')
PY

if [[ -x "$ROOT/bin/audit_contour.sh" ]]; then
  "$ROOT/bin/audit_contour.sh" "$ROOT"
fi

echo "refresh complete"
