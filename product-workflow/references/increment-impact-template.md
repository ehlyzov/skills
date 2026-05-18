# Impact инкремента

Файл: `docs/product/increments/<feature>-impact.md`

Используется в режиме `baseline`, когда новая фича или доработка должна встроиться в существующий продукт.

Если affected scenarios были неочевидны или фича cross-cutting, сначала создай `docs/product/increments/<feature>-pre-scan.md` по [impact-pre-scan-template.md](impact-pre-scan-template.md), затем ссылайся на него здесь.

````markdown
# Increment Impact — <feature>

## Назначение инкремента

1-3 абзаца: какую проблему решает фича и почему она является развитием существующего продукта, а не отдельным сценарием-островом.

## Pre-scan

- **Pre-scan:** [<feature>-pre-scan.md](<feature>-pre-scan.md) или `N/A — affected scenario obvious: <rationale>`.

## Тип изменения

Используй один или несколько типов:

- `extends` — расширяет существующий сценарий без смены цели.
- `changes` — меняет flow, FR, AC или Test plan существующего сценария.
- `adds` — добавляет новый сценарий, встроенный в существующий путь.
- `splits` — разделяет один сценарий на несколько.
- `replaces` — заменяет прежний сценарий новым.
- `deprecates` — выводит сценарий из core flow.

## Affected scenarios

| Scenario card | Impact type | Touched extension points | Changed happy-path steps | Required artifact updates | Regression checks |
| --- | --- | --- | --- | --- | --- |
| S02 | extends | `s02.<extension>` | Step 3 | scenario card, scenario, baseline, DOT, plan | <команды/тесты> |

## Added scenarios

| New scenario | Entry | Exit / next | Why this is not an island |
| --- | --- | --- | --- |
| S04 | S02 | S03 | <объяснение> |

## DOT diff

Фрагмент для `docs/product/scenario-graph.dot`:

```dot
"S02: Open details" -> "S04: Configure rule" [label="increment: <feature>"];
"S04: Configure rule" -> "S03: Take action" [label="returns"];
```

## Обновления требований

| Scenario | FR/NFR/AC/Test plan | Change | Reason |
| --- | --- | --- | --- |
| S02 | FR2 | changed | <why> |

## Verification impact

- Какие старые happy paths нужно проверить повторно.
- Какие error/alternative paths затронуты.
- Какие новые проверки доказывают, что инкремент встроен в существующий продукт.
- Какие scenario-card regression checks должны попасть в implementation plan.
````

## Правило достаточности

Impact-документ достаточен, когда по нему понятно:

- откуда пользователь попадает в новую функциональность;
- куда он возвращается или какой следующий сценарий запускает;
- какие существующие scenario cards, extension points, FR/AC и проверки меняются;
- какие regression checks не дают старому пути деградировать.
