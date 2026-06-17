# Pressure Scenario: Contour Script Policy

## User prompt

`Проверь существующий service contour в read-only режиме. Не устанавливай toolchain.`

## Prior risk

The support scripts section said the skill must add or maintain `bin/*`, which could be interpreted as requiring scripts to be copied into every target service even for read-only audit or task preflight.

## Expected new behavior

Treat `bin/*` as mandatory for the skill package and full contour toolchain only. During `task-preflight`, lightweight audit, or read-only planning, do not copy or install scripts into the target service unless explicitly requested.
