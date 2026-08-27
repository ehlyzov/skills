# Шаблон плана реализации (T-задачи)

План реализации (`docs/plans/<product>-implementation-plan.md`) — это
command-level список задач T0..TN, который оркестратор передаёт worker-у
(single instance, без памяти между задачами). План начинается с минимального
acceptance-bearing результата, а не с общей инфраструктуры.

## Структура файла

```markdown
# <Продукт> — план реализации продуктовых сценариев

## Метаданные

- **Source of truth (продуктовая правда):** [docs/product/overview.md](...), [docs/product/scenarios/01..N](...).
- **Канон по архитектуре:** ссылки на existing canon (SERVICE_MAP, AGENTS).
- **Целевая модель worker-а:** Sonnet 4.6, single instance.
- **Оркестратор:** очередь задач читает этот файл сверху вниз; worker берёт первую задачу со `Status: - [ ]`, выполняет её, прогоняет Verify, заменяет в Status `- [ ]` на `- [x]` и (если требуется) делает commit.
- **Параллелизм:** последовательное выполнение, одна задача за раз.
- **Assurance budget:** если budget задан, он включает orchestrator, worker,
  независимый verifier и один разрешённый repair.
- **Stop-loss:** условие проверяется до следующего действия; ceiling нельзя
  пересматривать после наблюдения результата.

## Как читать задачу

(скопируй описание полей: Status / Goal / Sources / Depends on / Read first / Modify / Product artifacts / Steps / Verify / DoD)

## Конвенции выполнения

1. Не реализуй больше, чем сказано.
2. Пиши только конкретно — без угадывания.
3. Если код уже реализует требование — пометь `- [x]`, добавь `### Note: already implemented at <file>:<line>`, переходи дальше.
4. При неясности — `- **Status:** - [ ] ASK: <вопрос>` и завершай задачу.
5. Verify обязан проходить.
6. Каждая задача — один атомарный commit `feat(plan): TXX <название>` или `fix(plan): TXX ...`.
7. Никогда не правь acceptance criteria сценариев.
8. Каждая задача имеет `Product artifacts`: обновления baseline/cards/DOT/impact docs или явное `No product artifact update because ...`.

## Команды verify (общие)

| Команда | Назначение |
| --- | --- |
| ... | ... |

## Известные пробелы покрытия

Что план **не** закрывает (зафиксировать сразу, чтобы критик не возвращался). Минимум 3-5 пунктов.

## Список задач

## T0. <Первый acceptance-bearing vertical slice или доказанно необходимый enabler>

## T1. ...
```

## Формат одной задачи

```markdown
## TXX. <Краткое название>

- **Status:** - [ ]
- **Goal:** 1-2 предложения, что эта задача даёт.
- **Sources:** [сценарий FR/AC](...), [файл канона](...).
- **Depends on:** TYY, TZZ, или —.
- **Read first:**
  - точные файлы и грубые диапазоны строк (для самодостаточности worker-а);
  - gap-yaml entry (если задача — gap-fix существующего FR/AC).
- **Modify:**
  - точные файлы — что создаём и что правим;
  - тестовые файлы.
- **Product artifacts:**
  - `docs/product/scenario-cards.md`: SXX extension point `<id>` — update/regression check/no change;
  - `docs/product/current-scenario-baseline.md`: update/no change because ...;
  - `docs/product/scenario-graph.dot`: update/no change because ...;
  - `docs/product/increments/<feature>-impact.md`: update/no change because ...;
  - или `No product artifact update because this task is internal-only and does not change user-visible flow, extension points, regression checks, scenario transitions, or product decisions.`
- **Steps:**
  1. конкретный шаг с inline-кодом / командой;
  2. ...;
  3. тест: какие assert-ы.
- **Verify:**
  ```bash
  <конкретная команда, которая должна выйти с success>
  ```
- **DoD:**
  - явный критерий 1;
  - явный критерий 2.

---
```

## Дизайн оптимальной последовательности

1. **Первый vertical slice:** минимальное пользовательское поведение или
   измеримый product outcome с проверкой. Если implementation coverage уже
   понятен из кода/тестов, отдельный gap artifact не создаётся.
2. **Опциональный bounded coverage scan:** нужен только при большом неизвестном
   current surface. Результат должен непосредственно выбирать первый slice;
   это не самостоятельная foundation wave.
3. **Just-in-time foundation:** общий primitive создаётся вместе с первым
   consumer-ом или непосредственно перед ним. Enabler обязан назвать consumer,
   доказать невозможность slice без себя и иметь минимальный scope.
4. **Следующие slices:** current gaps, compatibility изменения и growth
   реализуются как independently verifiable outcomes. Близкие изменения можно
   объединять по shared files, не превращая задачу в многочасовой комбайн.
5. **Final assurance:** targeted regression checks, затем необходимые full/e2e
   tests. Не строить отдельную verification infrastructure, если существующие
   repo tools уже доказывают acceptance.

## Финальный чек

```bash
unchecked=$(grep -cE '^- \*\*Status:\*\* - \[ \]' docs/plans/<product>-implementation-plan.md)
test "$unchecked" = "0" && echo PLAN-COMPLETE || { echo "outstanding tasks:"; grep -nE '^- \*\*Status:\*\* - \[ \]' docs/plans/<product>-implementation-plan.md; }
```

## Что критик проверяет

- Все задачи имеют 10 обязательных полей (Status, Goal, Sources, Depends on, Read first, Modify, Product artifacts, Steps, Verify, DoD).
- Если задача меняет пользовательский flow, `Product artifacts` указывает конкретные baseline/cards/DOT/impact updates. Если не меняет — есть проверяемое объяснение `No product artifact update because ...`.
- `Depends on:` — корректные ссылки на существующие задачи.
- Verify-команда реалистична для текущего проекта (правильный gradle/npm/pytest синтаксис, правильный модуль).
- Каждый Goal G1..GN из overview покрыт хотя бы одной T-задачей.
- Первая незавершённая T-задача даёт acceptance-bearing outcome; до неё не
  более одного доказанно необходимого enabler-а.
- Каждый enabler называет ближайший consumer и не присваивает обязанности
  будущих задач или гейтов.
- Гейт блокирует только защищаемый artifact/claim; missing telemetry не
  блокирует несвязанную реализацию.
- Если указан budget, он покрывает полный execution contour и имеет pre-action
  stop-loss.
- Атомарность: никакая задача не объединяет 5+ часов работы.
- Inline-код в Steps корректен (синтаксис, импорты, типы).

## Размер задач

Размер определяется independently verifiable outcome, а не числом файлов или
целевым количеством задач. Не устанавливай минимум задач. Разделяй задачу,
если один worker не может завершить outcome и Verify в одном bounded run;
объединяй микрозадачи, если самостоятельная проверка не добавляет нового факта.
