# Шаблон плана реализации (T-задачи)

План реализации (`docs/plans/<product>-implementation-plan.md`) — это command-level список задач T0..TN, который оркестратор передаёт worker-у (Sonnet 4.6, single instance, без памяти между задачами).

## Структура файла

```markdown
# <Продукт> — план реализации продуктовых сценариев

## Метаданные

- **Source of truth (продуктовая правда):** [docs/product/overview.md](...), [docs/product/scenarios/01..N](...).
- **Канон по архитектуре:** ссылки на existing canon (SERVICE_MAP, AGENTS).
- **Целевая модель worker-а:** Sonnet 4.6, single instance.
- **Оркестратор:** очередь задач читает этот файл сверху вниз; worker берёт первую задачу со `Status: - [ ]`, выполняет её, прогоняет Verify, заменяет в Status `- [ ]` на `- [x]` и (если требуется) делает commit.
- **Параллелизм:** последовательное выполнение, одна задача за раз.

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

## T0. Gap-analysis

(см. ниже формат)

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

1. **Phase 0 — Foundation T0**: gap-analysis всех FR/AC сценариев. Результат: structured YAML, на который ссылаются все последующие задачи. Без этого 60% задач окажутся уже реализованными, и worker зря потратит время.
2. **Phase 1 — Cross-feature foundation**: общая инфраструктура, нужная нескольким сценариям (audit-trail, approve-token, capabilities skeleton, etc.). Раньше всего, чтобы зависимые задачи имели готовый primitive.
3. **Phase 2 — Current scenario gap-fixes**: задачи, доводящие current-сценарии до 100% acceptance. Чередовать сценарии по принципу зависимости и общих файлов (не блок в один сценарий — это перегружает worker один и тот же файл).
4. **Phase 3 — Growth-сценарии**: реализация MVP growth-сценариев. Их разбиение естественно идёт через FR.
5. **Phase 4 — Final**: gap.yaml refresh, full test run, e2e на стенде.

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
- Атомарность: никакая задача не объединяет 5+ часов работы.
- Inline-код в Steps корректен (синтаксис, импорты, типы).

## Размер задач

«Средние блоки»: 1 задача = 1 файл или 1 feature-фрагмент с тестом. Целевое распределение для типового продукта на 10 сценариев: ~30-50 задач.

- < 20 задач — недостаточно гранулярно, worker завязнет.
- > 80 задач — слишком атомарно, оркестратор устанет.
