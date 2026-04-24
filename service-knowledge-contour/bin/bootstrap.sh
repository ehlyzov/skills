#!/usr/bin/env bash
set -euo pipefail

ROOT="."
STARTUP_ONLY="${STARTUP_ONLY:-0}"
FORCE="${FORCE:-0}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --startup-only)
      STARTUP_ONLY="1"
      shift
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "unknown arg: $1" >&2
      exit 2
      ;;
    *)
      ROOT="$1"
      shift
      ;;
  esac
done

write_if_allowed() {
  local path="$1"
  mkdir -p "$(dirname "$path")"
  if [[ -f "$path" && "$FORCE" != "1" ]]; then
    echo "skip existing: $path"
    return
  fi
  cat > "$path"
}

CMDS_JSON="$($PYTHON_BIN - "$ROOT" <<'PY'
import json, re, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
result = {
    "install": None,
    "local_run": None,
    "narrow_verify": None,
    "full_verify": None,
    "notes": [],
}
package = root / "package.json"
if package.exists():
    try:
        data = json.loads(package.read_text(encoding="utf-8"))
        scripts = data.get("scripts", {})
        if scripts:
            result["install"] = "npm install"
            if "start" in scripts:
                result["local_run"] = "npm run start"
            elif "dev" in scripts:
                result["local_run"] = "npm run dev"
            if "test" in scripts:
                result["narrow_verify"] = "npm test -- <target>"
                result["full_verify"] = "npm test"
            if "lint" in scripts:
                result["full_verify"] = (result["full_verify"] + " && npm run lint") if result["full_verify"] else "npm run lint"
            if "typecheck" in scripts:
                result["full_verify"] = (result["full_verify"] + " && npm run typecheck") if result["full_verify"] else "npm run typecheck"
    except Exception:
        result["notes"].append("package.json exists but scripts could not be parsed")
pyproject = root / "pyproject.toml"
if pyproject.exists() and not result["install"]:
    txt = pyproject.read_text(encoding="utf-8", errors="ignore")
    result["install"] = "pip install -e ."
    if re.search(r"\[tool\.pytest\]|pytest", txt):
        result["narrow_verify"] = "pytest -k <pattern>"
        result["full_verify"] = "pytest"
    if "ruff" in txt:
        result["full_verify"] = (result["full_verify"] + " && ruff check .") if result["full_verify"] else "ruff check ."
    if "mypy" in txt or "pyright" in txt:
        result["full_verify"] = (result["full_verify"] + " && mypy .") if result["full_verify"] else "mypy ."
    if (root / "main.py").exists() or (root / "app.py").exists():
        result["local_run"] = result["local_run"] or "python main.py"
if (root / "go.mod").exists() and not result["install"]:
    result["install"] = "go mod download"
    result["local_run"] = "go run ./..."
    result["narrow_verify"] = "go test ./path/to/package -run <TestName>"
    result["full_verify"] = "go test ./..."
if (root / "Makefile").exists():
    text = (root / "Makefile").read_text(encoding="utf-8", errors="ignore")
    targets = set(re.findall(r"^([A-Za-z0-9_\-]+):", text, re.M))
    if "install" in targets:
        result["install"] = "make install"
    if "run" in targets:
        result["local_run"] = "make run"
    elif "dev" in targets:
        result["local_run"] = result["local_run"] or "make dev"
    if "test" in targets:
        result["narrow_verify"] = result["narrow_verify"] or "make test TEST=<target>"
        result["full_verify"] = "make test"
    if "lint" in targets:
        result["full_verify"] = (result["full_verify"] + " && make lint") if result["full_verify"] else "make lint"
for key in ["install", "local_run", "narrow_verify", "full_verify"]:
    if not result[key]:
        result[key] = "Add after repository inspection or record an unresolved fact in docs/service/knowledge-gaps.yaml."
print(json.dumps(result, ensure_ascii=False))
PY
)"
export CMDS_JSON
INSTALL_CMD="$($PYTHON_BIN - <<'PY'
import json, os
print(json.loads(os.environ['CMDS_JSON'])['install'])
PY
)"
LOCAL_RUN_CMD="$($PYTHON_BIN - <<'PY'
import json, os
print(json.loads(os.environ['CMDS_JSON'])['local_run'])
PY
)"
NARROW_VERIFY_CMD="$($PYTHON_BIN - <<'PY'
import json, os
print(json.loads(os.environ['CMDS_JSON'])['narrow_verify'])
PY
)"
FULL_VERIFY_CMD="$($PYTHON_BIN - <<'PY'
import json, os
print(json.loads(os.environ['CMDS_JSON'])['full_verify'])
PY
)"

write_if_allowed "$ROOT/AGENTS.md" <<'EOD'
# AGENTS.md

Read this file before starting work.

## Non-negotiables
- Do not guess commands, paths, APIs, ownership, or verification results.
- Read the relevant files before editing.
- Keep changes small, direct, and reviewable.
- Use `docs/service/VERIFY.md` as the canonical verification contract.
- Treat `docs/service/SERVICE_MAP.md` as the canonical structural map.
- Put unresolved durable uncertainty only in `docs/service/knowledge-gaps.yaml`.
- Do not duplicate architecture or verification truth in startup docs.

## Working rules
- Prefer repository evidence over assumptions.
- Verify non-trivial changes with the commands documented in `docs/service/VERIFY.md`.
- Keep startup guidance short and push durable detail into canonical docs.

## Canonical knowledge
- Structure and risk: `docs/service/SERVICE_MAP.md`
- Verification: `docs/service/VERIFY.md`
- Durable unknowns: `docs/service/knowledge-gaps.yaml`

## Generated overlays
- `docs/service/generated/change-surface.json`
- `docs/service/generated/hotspots.md`
- `docs/service/generated/health-report.json`
EOD

write_if_allowed "$ROOT/CLAUDE.md" <<'EOD'
# CLAUDE.md

Use `AGENTS.md` as the startup contract.

Keep this file thin.
Do not fork project canon here.

Canonical knowledge lives in:
- `docs/service/SERVICE_MAP.md`
- `docs/service/VERIFY.md`
- `docs/service/knowledge-gaps.yaml`
EOD

if [[ "$STARTUP_ONLY" == "1" ]]; then
  echo "startup layer update complete"
  exit 0
fi

write_if_allowed "$ROOT/docs/service/SERVICE_MAP.md" <<'EOD'
# SERVICE_MAP

## Service purpose
Describe the service in one short paragraph after repository inspection.

Bootstrap seeds this file in English. The repository team may later maintain it in Russian or English.

## Runtime entrypoints
List the actual runtime entrypoints and top-level startup paths visible from the repo.

## Top-level module map
Summarize only the modules or directories that matter for change-surface localization.

## Boundaries and invariants
Record only boundaries and invariants that repeatedly affect safe edits.

## Critical integrations visible from the repo
List only integrations and interfaces visible from source, configs, or tests.

## Dangerous zones and legacy hotspots
Keep this section short. Prefer risk-oriented bullets over architecture prose.

## Generated overlays
- `docs/service/generated/change-surface.json`
- `docs/service/generated/hotspots.md`

## Review triggers
Update this file when topology, entrypoints, boundaries, schema shape, or workflow shape changes.
EOD

write_if_allowed "$ROOT/docs/service/VERIFY.md" <<EOD
# VERIFY

## Fastest local setup path
- ${INSTALL_CMD}
- ${LOCAL_RUN_CMD}

Bootstrap seeds this file in English. The repository team may later maintain it in Russian or English, but commands must remain literal.

## Narrow verification path
- ${NARROW_VERIFY_CMD}

## Full local verification path
- ${FULL_VERIFY_CMD}

## CI-only checks
List checks that cannot be reproduced locally after repository inspection.

## Risk-triggered extra checks
Add the extra checks required for hotspot changes, migrations, flaky areas, or generated code.

## Required change evidence
Every non-trivial change should report:
- changed surface;
- commands run;
- observed results;
- what was not verified locally;
- risk notes.

## What cannot be verified locally
Record the boundaries that depend on internal infrastructure or unavailable environments.
EOD

write_if_allowed "$ROOT/docs/service/knowledge-gaps.yaml" <<'EOD'
gaps: []
EOD

write_if_allowed "$ROOT/docs/service/generated/change-surface.json" <<'EOD'
{
  "status": "generated",
  "confidence": "low",
  "changed_files": [],
  "entrypoints": [],
  "config_files": [],
  "adjacent_paths": [],
  "triggers": []
}
EOD

write_if_allowed "$ROOT/docs/service/generated/hotspots.md" <<'EOD'
# Generated hotspots

This file is generated guidance, not canon.
Run `bin/refresh_contour.sh` to rebuild it.
EOD

write_if_allowed "$ROOT/docs/service/generated/health-report.json" <<'EOD'
{
  "status": "generated",
  "audit_ok": false,
  "errors": [],
  "warnings": []
}
EOD

if [[ -x "$ROOT/bin/refresh_contour.sh" ]]; then
  "$ROOT/bin/refresh_contour.sh" "$ROOT" || true
fi
if [[ -x "$ROOT/bin/audit_contour.sh" ]]; then
  "$ROOT/bin/audit_contour.sh" "$ROOT" || true
fi

echo "bootstrap complete"
