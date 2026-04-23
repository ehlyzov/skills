# Service Knowledge Contour B+ Package

This package provides a ready-to-commit starter kit for the `service-knowledge-contour` skill.

## Contents

- `SKILL.md` — final B+ operating model for a single service repository
- `bin/bootstrap.sh` — creates the mandatory canonical core and generated layer
- `bin/refresh_contour.sh` — rebuilds generated overlays and detects likely update triggers
- `bin/audit_contour.sh` — validates contour integrity and writes `health-report.json`
- `bin/promote_learning.sh` — classifies transient learning and proposes one canonical home
- `bin/prune_contour.sh` — finds delete / merge / archive candidates
- `examples/` — optional PR and CI examples

## Expected repository shape after bootstrap

- `AGENTS.md`
- `CLAUDE.md`
- `docs/service/SERVICE_MAP.md`
- `docs/service/VERIFY.md`
- `docs/service/knowledge-gaps.yaml`
- `docs/service/generated/change-surface.json`
- `docs/service/generated/hotspots.md`
- `docs/service/generated/health-report.json`

## Suggested usage

From the target repository root:

```bash
cp -R /path/to/service-knowledge-contour/* .
chmod +x bin/*.sh
./bin/bootstrap.sh
./bin/refresh_contour.sh
./bin/audit_contour.sh
```

To promote durable learning:

```bash
./bin/promote_learning.sh --input-file /tmp/learning.txt
```

To inspect stale contour candidates:

```bash
./bin/prune_contour.sh
```

## Notes

- The scripts default to safe behavior. They do not overwrite existing canonical docs unless `FORCE=1` is passed to `bootstrap.sh`.
- Generated artifacts are rebuildable. Treat them as navigation and audit overlays, not source of truth.
- `knowledge-gaps.yaml` is the only allowed registry for unresolved durable uncertainty.
