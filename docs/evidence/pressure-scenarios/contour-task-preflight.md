# Pressure Scenario: Contour Task Preflight

## User prompt

`В этом сервисе есть docs/service. Нужно поправить feature bug; сначала быстро пойми карту сервиса и проверки.`

## Prior risk

Because the contour skill emphasized bootstrap, refresh, audit, promote, and prune, a Codex agent could start maintaining contour artifacts when the user only needed context for ordinary feature/debug work.

## Expected new behavior

Choose `task-preflight`. Read existing `AGENTS.md`, `CLAUDE.md`, `SERVICE_MAP.md`, `VERIFY.md`, and `knowledge-gaps.yaml` when present. Report likely change surface, risk zones, verification path, and trigger expectation. Do not bootstrap or refresh.
