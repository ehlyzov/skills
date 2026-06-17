# Pressure Scenario: Product Quick Plan

## User prompt

`Напиши короткий planning checkpoint по покрытию сценариев для публичного запуска. Без реализации и без полного PRD.`

## Prior risk

The skill described an end-to-end 9-phase product workflow and a mandatory Phase 0 gate before product artifacts. A Codex agent could over-apply the full pipeline, block on broad scope questions, or create `overview.md`, scenario files, and plans when the user only asked for a small planning artifact.

## Expected new behavior

Choose `quick-plan`. Create one repo-local planning/design-only Markdown artifact with evidence paths, assumptions, status, and next steps. Do not create full PRD artifacts or implementation/hardening plans unless the user explicitly expands scope.
