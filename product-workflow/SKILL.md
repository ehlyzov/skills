---
name: product-workflow
description: "Сквозная продуктовая проработка для команды разработки. Итеративно строит целостный набор пользовательских сценариев по строгому шаблону, формирует command-level план реализации и отдельный план усиления (архитектура, безопасность, поддерживаемость). В конце независимый агент-валидатор подтверждает целостность и непротиворечивость всех артефактов. Финальный артефакт — markdown-набор и единый PDF. Используй этот скилл всегда, когда пользователь просит «продуктовая проработка», «PRD», «продуктовое описание», «спроектировать сценарии», «составить план реализации фичи / продукта», «hardening plan», «product roadmap с проверкой», «оформить продукт по сценариям», «упаковать сценарии в PDF», даже если он не назвал слово «product-workflow». Подходит и для нового продукта с нуля, и для рефакторинга/оформления существующей кодовой базы."
---

# Product Workflow

Скилл ведёт продуктовую проработку «end-to-end»: от анализа продуктового пространства до полностью согласованных артефактов. На выходе пользователь получает три согласованных пакета:

1. **Продуктовое описание** (`docs/product/overview.md` + `docs/product/scenarios/01..N.md`) — vision, персоны, проблемы, цели, N сценариев по строгому шаблону, плюс единый PDF.
2. **План реализации** (`docs/plans/launchpad-implementation-plan.md` или аналог) — command-level задачи T0..TN для оркестратора + worker-а.
3. **План усиления** (`docs/plans/launchpad-hardening-plan.md` или аналог) — архитектура / безопасность / поддерживаемость, не добавляющая функционала; задачи H1..HN с зависимостями от T-задач.

После завершения работы запускается **независимый верификатор** — отдельный агент, читающий все артефакты и подтверждающий целостность и непротиворечивость. Только после его «всё хорошо» работа считается законченной.

## Когда использовать

- Пользователь сказал: «нужно продуктовое описание», «PRD по фиче X», «спроектируй сценарии», «составь план реализации», «hardening plan», «оформи продукт».
- Есть кодовая база и нужно зафиксировать её продуктовое лицо + roadmap.
- Есть идея/новый продукт без кода — нужно собрать целостную картину сценариев + план.
- Пользователь хочет один артефакт-PDF для шеринга со стейкхолдерами.

## Когда **не** использовать

- Точечный bug-fix или одиночная фича без претензий на продуктовый уровень — это переусложнение.
- Чисто технический proposal без пользовательских сценариев — лучше обычный design doc.
- Готовое описание уже есть и нужен только PDF — выполни напрямую через `scripts/build_pdf.sh`.

## Работа с пользователем

Все артефакты пишутся **на русском языке**. Тон — продуктовый, без воды. Сценарии и планы — иммутабельные после approval (правки только через явный запрос).

## Совместимость с harness-ом (Claude / Codex)

Скилл агностичен к конкретному harness-у:

- **Subagent / sub-task** — где в инструкциях написано «запусти subagent с промптом из `agents/<name>.md`», в Claude это `Agent(subagent_type="general-purpose", prompt=...)`, в Codex — соответствующий механизм child-task. Передавай промпт целиком, без обрезки.
- **Уточняющие вопросы пользователю** — где написано «задать вопросы пользователю», в Claude `AskUserQuestion` (до 4 вопросов за вызов), в Codex — interactive prompt в чате.
- **Параллельные subagent-ы** — если фаза разрешает параллелизм (Phase 0 Discovery), в Claude используется один сообщение с несколькими tool-calls; в Codex — последовательно или согласно его модели параллелизма.
- **Скрипты** (`scripts/build_pdf.sh`, `scripts/verify_artifacts.py`) — bash и python, работают одинаково в обоих harness-ах.
- **Финальный артефакт** — markdown-файлы в репозитории и единый PDF в `~/Downloads/` — формат идентичен.

Если harness не поддерживает одну из возможностей (например, нет structured AskUserQuestion) — fallback на простой текстовый вопрос с явным маркером `?` и ожиданием ответа в чате.

## Высокоуровневый поток

Скилл ведёт пользователя через 7 фаз. Между фазами — обязательно подтверждение от пользователя через harness-механизм пользовательских вопросов (Claude `AskUserQuestion`, Codex — interactive prompt) на критических развилках (scope, локация, число сценариев, growth-направления).

```
[Phase 0] Discovery & scope
   ↓
[Phase 1] Overview + N scenarios (строгий шаблон)
   ↓ итеративная критика, до «всё хорошо»
[Phase 2] UX continuity (раздел «Дополнительные сценарии и связь с продуктом»)
   ↓ итеративная критика
[Phase 3] Implementation plan (command-level T-tasks)
   ↓ итеративная критика
[Phase 4] Hardening plan (H-tasks — архитектура/безопасность/поддерживаемость)
   ↓ итеративная критика
[Phase 5] Independent verification (отдельный агент, all artifacts)
   ↓ если «нужны правки» — возврат к нужной фазе
[Phase 6] PDF assembly (один файл)
```

Подробности и templates — в `references/`. Промпты для агентов-критиков — в `agents/`. Скрипты сборки и проверки — в `scripts/`.

## Phase 0 — Discovery & scope

Цель: понять продуктовое пространство и зафиксировать scope.

1. Если есть кодовая база — запусти 2-3 параллельных Explore агентов (разные углы: UI, API, runtime). Результаты идут в контекст для последующих фаз.
2. Через AskUserQuestion уточни:
   - **Локация артефактов** (рекомендация: `docs/product/`, `docs/plans/`).
   - **Число сценариев**: 5-7 (компактный продукт), 8-12 (типичный), 13+ (большой).
   - **Соотношение current vs growth**: сколько сценариев описывают текущую функциональность, сколько — точки роста.
   - **Persona-список**: кто целевая аудитория (developer / agent / QA / PM / support / other).
3. Запиши scope-сводку (одним сообщением пользователю, перед стартом Phase 1).

## Phase 1 — Overview + N scenarios

Цель: написать главный документ + N файлов сценариев по строгому шаблону.

**Шаблон сценария (обязательный, не сокращать):** см. [references/scenario-template.md](references/scenario-template.md).

**Структура overview.md:** см. [references/overview-template.md](references/overview-template.md).

Алгоритм:
1. Создать `docs/product/overview.md` со скелетом: Vision, Personas, Problems (P1..PN), Goals (G1..GN), Non-goals, Product map, Roadmap, Success metrics, Glossary, Index сценариев.
2. Создать `docs/product/scenarios/NN-<slug>.md` для каждого сценария по шаблону. Все 9 разделов обязательны: Problem / Goal / Non-goals / User flow (с подсекциями Основной/Альтернативные/Ошибочные сценарии) / Functional requirements / Non-functional requirements / Architecture constraints / Acceptance criteria / Test plan.
3. После draft — запустить scenario-critic (см. [agents/scenario-critic.md](agents/scenario-critic.md)) автоматически, в цикле:
   - Применить найденные правки.
   - Задать пользователю уточняющие вопросы по реальным развилкам через harness-механизм пользовательских вопросов (Claude `AskUserQuestion`, Codex — interactive prompt).
   - Повторять, пока критик не вернёт **«Всё хорошо»**.
4. Запустить `scripts/verify_artifacts.py --phase scenarios <docs/product/>` для машинной проверки структуры (9 разделов, 3 user-flow подсекции, валидные cross-refs).

Разворачивание Phase 1 обычно занимает 3-5 раундов критики. Не торопись закрыть фазу до явного «всё хорошо».

## Phase 2 — UX continuity

Цель: добавить ко всем сценариям естественно-языковой раздел `## Дополнительные сценарии и связь с продуктом`, замыкающий UX (откуда пользователь пришёл, куда уходит, какие соседние сценарии дополняют, где границы передачи control).

Алгоритм:
1. Запустить general-purpose агента с инструкцией добавить раздел к каждому файлу (см. [agents/ux-continuity-author.md](agents/ux-continuity-author.md)). 200-400 слов на сценарий, повествование, не bullet-список.
2. Прогнать scenario-critic ещё раз — он валидирует bidirectional cross-refs и непротиворечивость.
3. Итерации до «всё хорошо».

## Phase 3 — Implementation plan

Цель: command-level план задач T0..TN, который оркестратор + 1 worker (Sonnet 4.6) могут исполнять без догадок.

**Формат задачи и conventions:** см. [references/plan-template.md](references/plan-template.md).

Алгоритм:
1. Создать `docs/plans/<product>-implementation-plan.md`. Первая задача — T0 gap-analysis: пройти все FR/AC сценариев, выводить `docs/plans/<product>-gap.yaml` со статусом каждого требования (`done` / `partial` / `missing`).
2. Спроектировать оптимальную последовательность T-задач: foundation (общая инфра) → current scenario gap-fixes → growth → final verification. Зависимости — явный `Depends on:` в каждой задаче.
3. Каждая задача — `## TXX. <название>` с фиксированной структурой: Status / Goal / Sources / Depends on / Read first / Modify / Steps / Verify / DoD. Steps содержит inline-код или конкретные команды.
4. Запустить plan-critic (см. [agents/plan-critic.md](agents/plan-critic.md)) автоматически, в цикле, до «достаточно».
5. Прогнать `scripts/verify_artifacts.py --phase plan <docs/plans/>` — проверка чекбоксов, формата, bidirectional file-refs.

## Phase 4 — Hardening plan

Цель: отдельный план усиления архитектуры / безопасности / поддерживаемости. **Не вводит новой функциональности** — только инварианты, защиты, observability.

**Формат:** см. [references/hardening-template.md](references/hardening-template.md). Тот же task-формат, что в Phase 3, но с префиксом H. Каждая H-задача имеет `Depends on:` на конкретную T-задачу.

Алгоритм:
1. Запустить hardening-auditor (см. [agents/hardening-auditor.md](agents/hardening-auditor.md)) — он читает план реализации, сценарии и (если есть) код; возвращает 12-25 H-задач с распределением примерно 1/3 архитектура, 1/3 безопасность, 1/3 поддерживаемость.
2. Записать `docs/plans/<product>-hardening-plan.md` по тому же формату что в Phase 3.
3. В начале файла — раздел «Известные пробелы покрытия» (что hardening **не** закрывает, чтобы критик не возвращался). Минимум: pen-test, TLS на localhost (если применимо), formal contract verification, любые отложенные retention/cleanup механизмы.
4. Прогнать plan-critic ещё раз (универсальный — работает и для T, и для H задач).
5. Итерации до «достаточно».

## Phase 5 — Independent verification

Цель: **независимый** агент-валидатор (отдельный от писавших и критиковавших) подтверждает целостность всех артефактов: overview + сценарии + план + hardening.

Алгоритм:
1. Запустить independent-verifier (см. [agents/independent-verifier.md](agents/independent-verifier.md)). Он читает **все** артефакты, без знания истории работы.
2. Чек-лист валидатора:
   - Overview index ↔ scenario-файлы согласованы (1-к-1).
   - Persona в overview = персоны в шапках сценариев.
   - Goals G1..GN из overview покрыты в acceptance/NFR хотя бы одного сценария с тем же числовым ориентиром.
   - План: каждый FR/AC сценария попадает в gap.yaml; каждая T-задача либо реализует FR/AC, либо foundation.
   - Hardening: каждая H-задача имеет валидный `Depends on:` T-задачу; не вводит новой функциональности.
   - Cross-references двусторонни.
   - Числовые контракты не противоречат друг другу (одно число в overview = то же число в сценарии).
3. Если вердикт «нужны правки» — вернуться к соответствующей фазе и применить.
4. Цикл повторяется до **«Постановки полные, непротиворечивы, целостны»**.

## Phase 6 — PDF assembly

Цель: собрать единый читаемый PDF со всеми артефактами для шеринга со стейкхолдерами.

Алгоритм:
1. Запустить `bash scripts/build_pdf.sh <docs-root> <output-pdf>` — скрипт собирает overview + сценарии + план + hardening в одну markdown, конвертирует через pandoc → standalone HTML с TOC и стилями, печатает через Chrome headless.
2. Если pandoc/Chrome недоступны — fallback на python-markdown + Chrome (см. скрипт). Если и Chrome нет — скрипт упадёт с понятной ошибкой и инструкцией.
3. PDF копируется в `~/Downloads/<product>-product-docs.pdf`. **Не коммитить** PDF — только markdown.
4. Открыть PDF через `open` для визуальной проверки пользователем.

## Карта файлов скилла

| Файл | Назначение | Когда читать |
| --- | --- | --- |
| [references/scenario-template.md](references/scenario-template.md) | Полный шаблон одного сценария | Phase 1, перед написанием каждого scenario.md |
| [references/overview-template.md](references/overview-template.md) | Структура overview.md | Phase 1, перед написанием overview |
| [references/plan-template.md](references/plan-template.md) | Формат T-задачи + conventions для worker-а | Phase 3 |
| [references/hardening-template.md](references/hardening-template.md) | Формат H-задачи и распределение углов | Phase 4 |
| [references/critic-checklist.md](references/critic-checklist.md) | Универсальный чек-лист для критиков (что проверять) | Все фазы критики |
| [agents/scenario-critic.md](agents/scenario-critic.md) | Промпт для критика сценариев | Phase 1, 2 |
| [agents/plan-critic.md](agents/plan-critic.md) | Промпт для критика T- и H-планов | Phase 3, 4 |
| [agents/hardening-auditor.md](agents/hardening-auditor.md) | Промпт для аудитора-генератора H-задач | Phase 4 |
| [agents/independent-verifier.md](agents/independent-verifier.md) | Финальный независимый валидатор | Phase 5 |
| [agents/ux-continuity-author.md](agents/ux-continuity-author.md) | Автор раздела «Дополнительные сценарии и связь» | Phase 2 |
| [scripts/build_pdf.sh](scripts/build_pdf.sh) | Сборка единого PDF | Phase 6 |
| [scripts/verify_artifacts.py](scripts/verify_artifacts.py) | Машинная проверка структуры артефактов | Phase 1, 3, 4 |

## Принципы работы

1. **Не пиши задачи за один присест на всю фазу.** Делай каркас, потом заполняй итеративно. Каждая итерация критики делает артефакты лучше.
2. **Критики автоматизированы.** Цикл «правка → критик → правка» крутится сам, без вмешательства пользователя, пока критик не вернёт «всё хорошо». Пользователь подключается только на реальных развилках смысла (через harness-механизм пользовательских вопросов (Claude `AskUserQuestion`, Codex — interactive prompt)).
3. **Независимый верификатор — обязателен.** Без Phase 5 работа не считается завершённой. Это независимая пара глаз, защищающая от «слепых пятен» автора.
4. **Иммутабельность сценариев.** После Phase 1 + критика, сценарии — иммутабельная цель для плана и hardening. Все изменения требуют явного запроса пользователя.
5. **Сценарии не лезут в код, план не лезет в продуктовую ценность.** Сценарии описывают «что и зачем»; план — «как», на уровне команд и файлов; hardening — «что укрепить».
6. **PDF — артефакт для шеринга, а не источник правды.** Markdown — каноничен; PDF только генерируется из него и не коммитится.

## Эталонный пример

В этом репозитории есть пример полного выхода скилла на проекте Launchpad: `docs/product/`, `docs/plans/launchpad-implementation-plan.md`, `docs/plans/launchpad-hardening-plan.md`. Если столкнёшься с непонятным форматированием — сверяйся с ним.
