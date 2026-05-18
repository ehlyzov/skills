# Impact pre-scan

Файл: `docs/product/increments/<feature>-pre-scan.md`

Используется перед impact-документом, когда affected scenarios неочевидны или инкремент может затронуть широкие пользовательские области. Цель — быстро сузить scope и не пропустить соседние сценарии.

````markdown
# Impact pre-scan — <feature>

## Назначение

1-3 предложения: что за инкремент и почему нужен pre-scan.

## Evidence opened

| Evidence | Why opened | Signal |
| --- | --- | --- |
| `docs/product/current-scenario-baseline.md` | Найти Sxx-карту продукта | <что нашли> |
| `docs/product/scenario-cards.md#SXX` | Проверить user story / extension points | <что нашли> |
| `path/to/code` | Проверить runtime entrypoint | <что нашли> |

## Candidate affected scenarios

| Scenario | Why candidate | Touched extension points | Evidence to read next |
| --- | --- | --- | --- |
| S05 | <почему может быть затронут> | `<surface>.<extension>` | `path/to/file`, `scenario-cards.md#S05` |

## Rejected scenarios

| Scenario | Why not affected | Evidence |
| --- | --- | --- |
| S06 | <почему не меняется flow/action semantics> | <evidence> |

## Cross-cutting checklist

| Area | Baseline scenario | Affected? | Rationale |
| --- | --- | --- | --- |
| Auth / session / legal | Sxx or N/A | yes/no/maybe | <why; if N/A, explain why the product has no such baseline area> |
| Search / recall / navigation | Sxx or N/A | yes/no/maybe | <why; if N/A, explain why the product has no such baseline area> |
| Settings / preferences / privacy | Sxx or N/A | yes/no/maybe | <why; if N/A, explain why the product has no such baseline area> |
| Operator / admin / runtime | Sxx or N/A | yes/no/maybe | <why; if N/A, explain why the product has no such baseline area> |

## Open decisions

- <решение, которое должен принять пользователь или агент по делегации>.

## Recommendation

Proceed to impact with affected scenarios: SXX, SYY.
````

## Правило достаточности

Pre-scan достаточен, когда:

- есть минимум один candidate affected scenario или явно объяснено, что нужен новый scenario;
- rejected scenarios показывают, что агент проверил ближайшие соседние сценарии, а не просто проигнорировал их;
- cross-cutting checklist заполнен для auth/session/legal, search/recall/navigation, settings/preferences/privacy, operator/admin/runtime; для отсутствующих областей указан `N/A` с rationale;
- каждый `maybe` превращён в open decision или evidence task перед implementation plan.
