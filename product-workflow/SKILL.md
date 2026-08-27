---
name: product-workflow
description: "Create product-facing documents only when explicitly requested: PRDs, user scenarios, baselines, feature impact, roadmaps, stakeholder packages, and product implementation or hardening plans. Do not use for code changes, approved-plan execution, technical research, benchmarks, or developer-tool implementation unless product documentation is explicitly requested."
---

# Product Workflow

Скилл создаёт продуктовые документы и планы. Он не исполняет утверждённый
технический план и не управляет обычной разработкой. Выбирай только те
артефакты и фазы, которые пользователь запросил явно; полный пакет не является
режимом по умолчанию.

Возможные выходы:

1. **Продуктовое описание** (`docs/product/overview.md` + `docs/product/scenarios/01..N.md`) — задача, персоны, проблемы, цели, N сценариев по строгому шаблону.
2. **Журнал решений** (`docs/product/decisions.md`) — варианты, факты, trade-offs, рекомендация агента и явный статус решения.
3. **Baseline текущих сценариев** (`docs/product/current-scenario-baseline.md` + `docs/product/scenario-cards.md` + `docs/product/scenario-graph.dot`) — карта существующих сценариев, компактные пользовательские истории, страницы и переходы, если продукт уже существует или задача является доработкой.
4. **Impact-документ инкремента** (`docs/product/increments/<feature>-impact.md`) — как новая фича расширяет, меняет или добавляет сценарии относительно baseline.
5. **План реализации** (`docs/plans/<product>-implementation-plan.md`) — command-level задачи T0..TN для оркестратора + worker-а.
6. **План усиления** (`docs/plans/<product>-hardening-plan.md`) — архитектура / безопасность / поддерживаемость, не добавляющая функционала; задачи H1..HN с зависимостями от T-задач.
7. **Независимый вердикт и PDF** (`docs/product/validation/verdict.md` + PDF в `~/Downloads/`) — stakeholder-facing продуктовый документ без T/H-планов по умолчанию.

Независимый верификатор обязателен только для полного PRD/delivery package,
stakeholder PDF и явно запрошенного финального product gate. Для узкого режима
он проверяет только созданный артефакт и его прямые источники. Не заставляй
малую задачу оплачивать аудит полного продуктового архива.

## Когда использовать

- Пользователь явно сказал: «нужно продуктовое описание», «PRD по фиче X», «спроектируй сценарии», «составь продуктовый план реализации», «hardening plan», «оформи продукт».
- Есть кодовая база и нужно зафиксировать её продуктовое лицо + roadmap.
- Нужно встроить новую фичу или доработку в уже существующий продукт, не создавая сценарный «остров».
- Есть идея/новый продукт без кода — нужно собрать целостную картину сценариев + план.
- Пользователь хочет один артефакт-PDF для шеринга со стейкхолдерами.

## Когда **не** использовать

- Точечный bug-fix или одиночная фича без претензий на продуктовый уровень — это переусложнение.
- Чисто технический proposal без пользовательских сценариев — лучше обычный design doc.
- Исполнение уже утверждённого плана, изменение кода, рефакторинг, code review
  или проверка тестов — используй обычный repository workflow.
- Исследовательский DAG, benchmark/evidence plan, agent/tool infrastructure или
  разработка developer tool не становятся продуктовой проработкой только
  потому, что репозиторий является продуктом.
- Запрос «реализуй фичу» сам по себе не означает «создай PRD». Применяй этот
  навык только при явной потребности в продуктовых артефактах.
- Готовое описание уже есть и нужен только PDF — выполни напрямую через `scripts/build_pdf.sh`.

## Routing guard

Перед началом выбери минимальный режим. Если результатом запроса должен быть
код, тест, технический design/research document или benchmark result, а не
продуктовый артефакт, прекрати этот workflow. Не создавай baseline, personas,
scenario graph, decision log, hardening plan или PDF «на всякий случай».

Если в текущей сессии уже есть явное одобрение нужного product scope, считай
его достаточным. Не запрашивай повторный approval и не создавай identity,
attestation или approval infrastructure.

## Работа с пользователем

Все prompt-файлы агентов в `agents/` пишутся на английском. Язык итоговых артефактов выбирается по пользовательскому контексту: если запрос, существующие документы или целевые артефакты русскоязычные, агенты пишут хороший русский текст; если контекст английский, пишут по-английски. В русском продукте английский допустим только для кода, команд, путей, API, имён библиотек и устойчивых собственных названий. Тон — продуктовый, без воды. Сценарии и планы — иммутабельные после approval (правки только через явный запрос).

Агент помогает принимать решения, но не подменяет пользователя:

- агент собирает факты, варианты, trade-offs, риски, рекомендацию и вопросы;
- человек принимает продуктовые решения согласно своему видению;
- агент может принять решение сам только если пользователь явно делегировал это решение;
- каждое нетривиальное решение фиксируется со статусом `proposed`, `approved_by_human` или `delegated_to_agent`;
- планы реализации строятся только по решениям `approved_by_human` или `delegated_to_agent`.

## Совместимость с harness-ом (Claude / Codex)

Скилл агностичен к конкретному harness-у:

- **Subagent / sub-task** — где в инструкциях написано «запусти subagent с промптом из `agents/<name>.md`», в Claude это `Agent(subagent_type="general-purpose", prompt=...)`, в Codex — соответствующий механизм child-task. Передавай промпт целиком, без обрезки.
- **Уточняющие вопросы пользователю** — где написано «задать вопросы пользователю», в Claude `AskUserQuestion` (до 4 вопросов за вызов), в Codex — interactive prompt в чате.
- **Параллельные subagent-ы** — если фаза разрешает параллелизм (Phase 0 Discovery), в Claude используется один сообщение с несколькими tool-calls; в Codex — последовательно или согласно его модели параллелизма.
- **Скрипты** (`scripts/build_pdf.sh`, `scripts/verify_artifacts.py`) — bash и python, работают одинаково в обоих harness-ах.
- **Финальный артефакт** — markdown-файлы в репозитории и единый stakeholder-facing PDF в `~/Downloads/`. PDF по умолчанию не содержит implementation/hardening планы.

Если harness не поддерживает одну из возможностей (например, нет structured AskUserQuestion) — fallback на простой текстовый вопрос с явным маркером `?` и ожиданием ответа в чате.

### Codex no-subagent fallback

Если Codex-сессия не даёт реального механизма отдельного subagent / fresh child task, не имитируй независимость.

- Такой проход must be labeled as fallback.
- Такой проход must not be called independent verification.
- Используй self-review / fresh-context checklist только как временный safety net: перечитай артефакты с начала, проверь чек-лист соответствующей фазы, сохрани отчёт с явной пометкой `Fallback review, not independent verification`.
- Для Phase 5, Phase 8 и PDF gate настоящий независимый verifier остаётся
  предпочтительным и обязательным, когда выбранный режим действительно требует
  соответствующий gate.

## Высокоуровневый поток полного пакета

Используй этот поток только когда пользователь запросил полный пакет. В других
режимах запускай лишь выбранные фазы. Подтверждение пользователя нужно только
на нерешённых продуктовых развилках, а не между каждой технической операцией.

```
[Phase 0] Discovery, scope & decision support
   ↓
[Phase 1] Overview + N scenarios (строгий шаблон)
   ↓ один critic pass + targeted delta recheck
[Phase 2] UX continuity (раздел «Дополнительные сценарии и связь с продуктом»)
   ↓ targeted cross-reference check
[Phase 3] Implementation plan (только если запрошен)
   ↓ один полный critic pass + targeted delta recheck
[Phase 4] Hardening plan (только если запрошен)
   ↓ risk-based review
[Phase 5] Independent package verification (allowlisted artifacts)
   ↓ blocking fix + один targeted recheck
[Phase 6] Editorial/style pass (единый русский стиль)
   ↓ semantic-diff check
[Phase 7] Product PDF assembly (без T/H-планов по умолчанию)
   ↓ если фича реализована
[Phase 8] Post-implementation scenario verification
```

Подробности и templates — в `references/`. Промпты для агентов-критиков — в `agents/`. Скрипты сборки и проверки — в `scripts/`.

## Codex operating modes

Выбирай самый лёгкий режим, который закрывает запрос пользователя. Не запускай полный pipeline только потому, что скилл умеет полный pipeline.

| Mode | Use when | Required output | Gate rule |
| --- | --- | --- | --- |
| `quick-plan` | Пользователь явно просит небольшой продуктовый planning checkpoint или product design artifact без реализации | Один repo-local Markdown artifact с evidence, статусом, assumptions и next steps | Phase 0 gate нужен только для нерешённых продуктовых решений; generic technical/research plan не относится к этому режиму |
| `baseline-only` | Нужно зафиксировать текущие сценарии существующего продукта | `current-scenario-baseline.md`, `scenario-cards.md`, `scenario-graph.dot` | Human gate только при спорных current/growth классификациях |
| `increment-impact` | Нужно встроить фичу/доработку в существующий baseline | pre-scan при неоднозначности + `<feature>-impact.md` | Не переходить к implementation plan без affected Sxx или явного `N/A` rationale |
| `product-plan` | По утверждённым сценариям нужен именно продуктовый implementation plan | Phase 3 и проверка plan scope | Не добавлять PRD/hardening/PDF, если они не запрошены |
| `hardening-plan` | Пользователь отдельно просит усиление утверждённого product plan | Phase 4 | Создавать только evidence-backed protections; нет обязательного количества задач |
| `full-prd` | Нужен полный PRD или целостная продуктовая проработка | Phase 0..2, 5 и 6; Phase 3/4/7 только если названы в запросе | Phase 0 gate обязателен только при нерешённом scope |
| `pdf-package` | Артефакты уже есть, нужно только собрать stakeholder PDF | PDF через `scripts/build_pdf.sh` | Требуется свежий разрешающий verdict, если пользователь явно не попросил bypass |
| `post-implementation-check` | Реализация T/H-плана завершена или нужна release readiness проверка | `implementation-verdict.md` + реальные команды проверки | Не утверждать готовность при critical/major blockers |

Для `quick-plan` не создавай `overview.md`, scenario-файлы, implementation plan
или hardening plan, если пользователь не попросил их явно. Такой артефакт
помечай как planning/design-only, если поведение не проверялось тестами или
runtime evidence. После выдачи утверждённого плана заверши product-workflow;
его исполнение является отдельной задачей.

## Режим `baseline`

Используй режим `baseline`, когда продукт уже существует, когда пользователь просит доработку/новую фичу поверх существующего поведения, или когда сценарии должны стать устойчивой опорой для будущих инкрементов.

Цель режима — зафиксировать текущие сценарии и заставить каждую новую фичу объяснять своё место в существующем пользовательском пути.

Минимальные артефакты:

- `docs/product/current-scenario-baseline.md` — текущие сценарии, страницы/команды/API, входы, выходы, known gaps.
- `docs/product/scenario-cards.md` — компактные карточки Sxx: user story, happy path, extension points, regression checks, что читать перед планированием.
- `docs/product/scenario-graph.dot` — явный граф страниц/сценариев и переходов в DOT. DOT — визуальная карта, не единственный источник продуктовой семантики.
- `docs/product/increments/<feature>-pre-scan.md` — быстрый скрининг affected/rejected scenarios перед impact, если зона влияния неочевидна или фича cross-cutting.
- `docs/product/increments/<feature>-impact.md` — только для инкремента: affected scenarios, added/changed flows, обновления FR/AC/Test plan, verification impact.

Правила:

- Новая фича не описывается как отдельный остров. Она должна быть классифицирована как `extends`, `changes`, `adds`, `splits`, `replaces` или `deprecates` относительно baseline.
- Если фича добавляет новый сценарий, impact-документ обязан указать вход из существующего сценария и возврат/следующий шаг.
- Если фича меняет существующий сценарий, нужно перечислить конкретные scenario cards, extension points, happy-path steps, regression checks и FR/AC/Test plan, которые меняются.
- Перед планированием инкремента агент обязан открыть `scenario-cards.md`, найти affected Sxx и прочитать только их карточки плюс referenced evidence.
- Если affected Sxx неясны, фича меняет широкую пользовательскую область или может затронуть cross-cutting areas, сначала создать `docs/product/increments/<feature>-pre-scan.md`, а не писать impact или план реализации. Cross-cutting areas: auth/session/legal, search/recall/navigation, settings/preferences/privacy, operator/admin/runtime. Для каждой области укажи `Baseline scenario` = Sxx или `N/A` с rationale.
- Pre-scan обязан перечислить candidate affected scenarios, rejected scenarios с rationale, cross-cutting checklist, evidence opened и open decisions.
- DOT фиксирует явные связи страниц/сценариев и, при необходимости, шаги продуктового инкремента через edge labels вроде `increment: <feature>`.
- Для нового продукта без существующего поведения baseline создаётся после Phase 1 как первичная карта current/growth-сценариев; impact-документ не нужен, пока нет инкремента.
- Для доработки существующего продукта baseline — preflight перед Phase 1/3: сначала найти или создать карту текущих сценариев, затем проектировать изменение.

Шаблоны: [references/baseline-template.md](references/baseline-template.md), [references/scenario-card-template.md](references/scenario-card-template.md), [references/impact-pre-scan-template.md](references/impact-pre-scan-template.md) и [references/increment-impact-template.md](references/increment-impact-template.md).

## Phase gates

| Фаза | Вход | Выход | Machine check | Human gate |
| --- | --- | --- | --- | --- |
| 0 | запрос пользователя + repo/идея | scope summary + `docs/product/decisions.md` | evidence paths в explorer-отчётах | подтверждение scope и решений |
| 1 | approved/delegated scope | overview + сценарии | `scripts/verify_artifacts.py --phase scenarios <repo>` | подтверждение сценариев |
| baseline | существующий продукт или approved сценарии | `current-scenario-baseline.md` + `scenario-cards.md` + `scenario-graph.dot` + optional increment impact | `--phase baseline`; для инкремента также `--phase pre-scan` и `--phase impact`; semantic связность проверяют scenario-critic + independent-verifier | подтверждение только при спорном impact |
| 2 | сценарии Phase 1 | UX continuity во всех сценариях | `--phase scenarios` + scenario-critic | только при смысловых развилках |
| 3 | approved сценарии и явный запрос product plan | implementation plan + optional gap.yaml | `--phase plan` | подтверждение только нерешённых scope gaps |
| 4 | implementation plan и явный запрос hardening | evidence-backed hardening plan | `--phase hardening` | подтверждение только новых policy decisions |
| 5 | artifacts выбранного режима | `docs/product/validation/verdict.md` | `--phase validation` | critical/major блокируют только проверяемый package/claim |
| 6 | свежий verdict | вычитанные product docs | style-editor report + повторный verifier | утверждение тона при спорных правках |
| 7 | вычитанные docs | PDF в `~/Downloads/` | `build_pdf.sh` с validation gate | визуальная проверка PDF |
| 8 | выполненный T/H-план | implementation readiness verdict | implementation-verifier + реальные tests | решение о готовности релиза |

## Mandatory Phase 0 user gate

Перед созданием `overview.md`, файлов сценариев, implementation plan или
hardening plan проверь, остались ли нерешённые продуктовые решения. Если scope
уже явно одобрен в текущей сессии, зафиксируй источник approval и продолжай без
повторного вопроса.

Сообщение с запросом подтверждения должно содержать:

1. Краткую discovery-сводку: что уже известно, какие evidence paths найдены, какие unknowns остаются.
2. Нумерованный список решений, на которые пользователь должен ответить.
3. Для каждого решения: варианты, помеченную `Рекомендация`, rationale/evidence и impact выбора.
4. Финальный явный вопрос с маркером `?`.

Не переходи к Phase 1, пока пользователь не ответил или явно не делегировал
агенту все реально открытые решения. Не спрашивай обязательный шаблонный набор,
если ответы уже даны или не влияют на выбранный режим.

Потенциальные вопросы Phase 0, задаваемые только когда ответ не следует из
запроса и существенно меняет результат:

- Локация артефактов.
- Число сценариев.
- Соотношение current vs growth.
- Persona-список.
- Нужен ли режим `baseline`: продукт уже существует / это инкремент / это новый продукт без baseline.
- Любая продуктовая развилка scope, найденная во время discovery.

Если structured-механизм пользовательских вопросов недоступен, задай эти вопросы обычным Markdown-сообщением в чате и дождись ответа. Не продолжай работу в том же ходе после вопроса.

## Phase 0 — Discovery, scope & decision support

Цель: понять продуктовое пространство, собрать факты для решений и зафиксировать scope без самовольного выбора продуктового направления.

1. Если есть кодовая база и полный продуктовый scope нельзя понять из уже
   существующих документов, запусти до 2-3 параллельных Explore агентов:
   - UI / пользовательские поверхности: [agents/explore-ui.md](agents/explore-ui.md).
   - API / контракты: [agents/explore-api.md](agents/explore-api.md).
   - Runtime / верификация: [agents/explore-runtime.md](agents/explore-runtime.md).
   Результаты идут в `docs/product/discovery/` или в рабочий контекст фазы: evidence paths, confidence, unknowns, risk notes.
2. Через AskUserQuestion уточни только неизвестные и значимые пункты:
   - **Локация артефактов** (рекомендация: `docs/product/`, `docs/plans/`).
   - **Число сценариев**: 5-7 (компактный продукт), 8-12 (типичный), 13+ (большой).
   - **Соотношение current vs growth**: сколько сценариев описывают текущую функциональность, сколько — точки роста.
   - **Persona-список**: кто целевая аудитория (developer / agent / QA / PM / support / other).
3. Создай или обнови `docs/product/decisions.md` по шаблону [references/decision-log-template.md](references/decision-log-template.md).
4. По каждой смысловой развилке покажи человеку варианты, evidence, trade-offs, recommendation и impact. Не выбирай молча.
5. Запиши scope-сводку (одним сообщением пользователю, перед стартом Phase 1) и дождись подтверждения.

Если задача является инкрементом существующего продукта, не переходи к планированию реализации, пока не создан или не обновлён `current-scenario-baseline.md`, не прочитаны affected cards из `scenario-cards.md`, не создан pre-scan для неоднозначного/cross-cutting scope и не описан `<feature>-impact.md`.

## Phase 1 — Overview + N scenarios

Цель: написать главный документ + N файлов сценариев по строгому шаблону.

**Шаблон сценария (обязательный, не сокращать):** см. [references/scenario-template.md](references/scenario-template.md).

**Структура overview.md:** см. [references/overview-template.md](references/overview-template.md).

Алгоритм:
1. Создать `docs/product/overview.md` со скелетом: Назначение документа, Видение, Аудитория и персоны, Сводные проблемы (P1..PN), Цели (G1..GN), Не входит в продукт, Карта возможностей, Дорожная карта и точки роста, Метрики успеха, Глоссарий, Индекс сценариев.
2. Создать `docs/product/scenarios/NN-<slug>.md` для каждого сценария по шаблону. Все 9 разделов обязательны, предпочтительно с русскими заголовками: Проблема / Цель / Не входит в сценарий / Пользовательский сценарий (с подсекциями Основной/Альтернативные/Ошибочные сценарии) / Функциональные требования / Нефункциональные требования / Архитектурные ограничения / Критерии приёмки / План проверки.
3. После draft запустить scenario-critic (см. [agents/scenario-critic.md](agents/scenario-critic.md)) один раз:
   - Применить найденные правки.
   - Задать пользователю уточняющие вопросы по реальным развилкам через harness-механизм пользовательских вопросов (Claude `AskUserQuestion`, Codex — interactive prompt).
   - После исправления blocking findings выполнить один targeted recheck только
     изменённых сценариев и связей. Если остаётся новая структурная проблема,
     запросить решение пользователя вместо неограниченного цикла.
4. Запустить `scripts/verify_artifacts.py --phase scenarios <docs/product/>` для машинной проверки структуры (9 разделов, 3 user-flow подсекции, валидные cross-refs).
5. Если включён режим `baseline`, создать или обновить `current-scenario-baseline.md`, `scenario-cards.md` и `scenario-graph.dot` по шаблону. Для инкремента дополнительно создать `docs/product/increments/<feature>-pre-scan.md` при неоднозначном/cross-cutting scope, затем `docs/product/increments/<feature>-impact.md` и связать их с изменёнными scenario-файлами/cards.
6. Прогнать `scripts/verify_artifacts.py --phase baseline <docs/product/>`; для инкремента также `--phase pre-scan <docs/product/>` и `--phase impact <docs/product/>`. Machine-check валидирует структуру, поля, enum-значения и лёгкую Sxx-связность; продуктовый смысл остаётся за critic/verifier.

Не планируй заранее несколько раундов критики. Один полный проход и один
targeted recheck являются нормой; дополнительные полные проходы требуют нового
структурного риска, а не косметических замечаний.

## Phase 2 — UX continuity

Цель: добавить ко всем сценариям естественно-языковой раздел `## Дополнительные сценарии и связь с продуктом`, замыкающий UX (откуда пользователь пришёл, куда уходит, какие соседние сценарии дополняют, где границы передачи управления).

Алгоритм:
1. Запустить general-purpose агента с инструкцией добавить раздел к каждому файлу (см. [agents/ux-continuity-author.md](agents/ux-continuity-author.md)). 200-400 слов на сценарий, повествование, не bullet-список.
2. Прогнать scenario-critic ещё раз — он валидирует bidirectional cross-refs и непротиворечивость.
3. После исправления выполнить один targeted recheck изменённых cross-refs.

## Phase 3 — Implementation plan

Цель: command-level план задач T0..TN, который оркестратор + 1 worker (Sonnet 4.6) могут исполнять без догадок.

**Формат задачи и conventions:** см. [references/plan-template.md](references/plan-template.md).

Алгоритм:
1. Создать `docs/plans/<product>-implementation-plan.md`. Делать отдельный
   `gap.yaml` только когда coverage многих сценариев действительно неизвестен
   и существующие документы/тесты не дают компактного ответа. Для малого
   инкремента записать `done` / `partial` / `missing` непосредственно в Sources
   и не создавать подготовительный artifact.
2. Первой незавершённой задачей сделать минимальный acceptance-bearing
   vertical slice: пользовательское поведение или измеримый product outcome с
   тестом. Допускается не более одного предшествующего enabling task, только
   если без него slice технически невозможен; enabler обязан назвать первый
   consumer, точную необходимость и минимальный scope.
3. Строить последовательность как `vertical slice → just-in-time shared
   primitive → следующие slices → final verification`. Не создавать общую
   инфраструктуру, контроллеры, схемы, manifests или observability заранее без
   непосредственного consumer-а.
4. Каждая задача — `## TXX. <название>` с фиксированной структурой: Status / Goal / Sources / Depends on / Read first / Modify / Product artifacts / Steps / Verify / DoD. Steps содержит inline-код или конкретные команды.
5. `Product artifacts` обязателен. Если задача меняет пользовательский flow, он перечисляет обновления `scenario-cards.md`, `current-scenario-baseline.md`, `scenario-graph.dot`, scenario/impact docs. Если не меняет — явная строка `No product artifact update because ...`.
6. Для каждой задачи проверить ownership: она даёт прямой product outcome,
   минимальный enabler ближайшего outcome или assurance этого outcome. Гейт
   может блокировать только защищаемый artifact/claim; telemetry gap не должен
   блокировать несвязанную реализацию.
7. Если план задаёт budgets, считать полный execution contour: orchestrator,
   producer, независимый verifier и один разрешённый repair. Проверять stop-loss
   до следующего действия, не после перерасхода. Не вводить универсальные
   числовые лимиты без task-local основания.
8. Запустить plan-critic один раз. Исправить blocking findings и выполнить один
   targeted recheck изменённых задач. Не повторять полный аудит после локальной
   правки.
9. Прогнать `scripts/verify_artifacts.py --phase plan <docs/plans/>` — проверка чекбоксов, формата, bidirectional file-refs.

## Phase 4 — Hardening plan

Цель: по явному запросу создать отдельный план усиления архитектуры /
безопасности / поддерживаемости. **Не вводит новой функциональности** — только
инварианты, защиты и observability, подтверждённые риском или evidence.

**Формат:** см. [references/hardening-template.md](references/hardening-template.md). Тот же task-формат, что в Phase 3, но с префиксом H. Каждая H-задача имеет `Depends on:` на конкретную T-задачу.

Алгоритм:
1. Запустить hardening-auditor (см. [agents/hardening-auditor.md](agents/hardening-auditor.md)) — он читает план реализации, сценарии и (если есть) код; возвращает только применимые H-задачи. Минимального количества и искусственного распределения по категориям нет.
2. Записать `docs/plans/<product>-hardening-plan.md` по тому же формату что в Phase 3.
3. В начале файла — раздел «Известные пробелы покрытия» (что hardening **не** закрывает, чтобы критик не возвращался). Минимум: pen-test, TLS на localhost (если применимо), formal contract verification, любые отложенные retention/cleanup механизмы.
4. Прогнать plan-critic один раз. После blocking repair проверить только изменённые H-задачи.
5. Если риск не подтверждён кодом, сценарием, threat model или обязательной policy, оставить его как non-blocking gap, а не превращать в задачу.

## Phase 5 — Independent artifact verification

Цель: **независимый** агент-валидатор (отдельный от писавших и критиковавших)
подтверждает целостность artifacts выбранного режима и их прямых источников.
Только полный delivery package требует чтения overview + scenarios + decisions
+ plan + hardening целиком.

Алгоритм:
1. Запустить independent-verifier (см. [agents/independent-verifier.md](agents/independent-verifier.md)). Он читает artifacts текущего package и их прямые canonical sources, без истории работы. Не включать optional планы и views, которые выбранный режим не создавал и не менял.
2. Чек-лист валидатора:
   - Overview index ↔ scenario-файлы согласованы (1-к-1).
   - Persona в overview = персоны в шапках сценариев.
   - Цели G1..GN из overview покрыты в критериях приёмки/NFR хотя бы одного сценария с тем же числовым ориентиром.
   - Если есть baseline: каждый сценарий в baseline представлен в `scenario-cards.md`, scenario-файлах или явно помечен как external/legacy; `scenario-graph.dot` не содержит висячих сценариев без объяснения.
   - Если есть scenario cards: каждая current-карточка содержит user story, happy path, extension points, regression checks и read-before/evidence.
   - Если есть pre-scan: candidate/rejected scenarios имеют rationale; cross-cutting checklist закрывает auth/session/legal, search/recall/navigation, settings/preferences/privacy, operator/admin/runtime через `Baseline scenario` = Sxx или `N/A` с rationale.
   - Если есть increment impact: каждая новая фича классифицирована как `extends` / `changes` / `adds` / `splits` / `replaces` / `deprecates`; affected scenarios/cards обновлены в extension points, FR/AC/Test plan; новые сценарии имеют вход и возврат/следующий шаг.
   - Implementation plan: каждая T-задача содержит `Product artifacts` и либо обновляет нужные baseline/cards/DOT/impact docs, либо объясняет `No product artifact update because ...`.
   - План: каждый FR/AC сценария покрыт задачей либо помечен `done` в optional
     gap.yaml или непосредственно в plan evidence; каждый enabler называет
     ближайший acceptance-bearing consumer.
   - Hardening: каждая H-задача имеет валидный `Depends on:` T-задачу; не вводит новой функциональности.
   - Cross-references двусторонни.
   - Числовые контракты не противоречат друг другу (одно число в overview = то же число в сценарии).
3. Сохранить полный отчёт в `docs/product/validation/verdict.md`.
4. Прогнать `scripts/verify_artifacts.py --phase validation <repo-root>`.
5. Если вердикт содержит blocking defect — вернуться к соответствующей фазе и применить минимальную правку.
6. Выполнить один targeted recheck changed artifacts/invariants. Если он выявил новую structural ambiguity, запросить решение пользователя; не запускать новый полный цикл автоматически. Non-blocking micro-notes не блокируют package.

## Phase 6 — Editorial/style pass

Цель: перед PDF сделать продуктовый текст цельным русскоязычным документом, а не смесью русских и английских рабочих терминов.

Алгоритм:
1. Запустить language-specific style editor на `docs/product/overview.md`, `docs/product/scenarios/*.md`, `docs/product/decisions.md` и `docs/product/validation/verdict.md`: [agents/style-editor-ru.md](agents/style-editor-ru.md) для русскоязычного продукта или [agents/style-editor-en.md](agents/style-editor-en.md) для англоязычного.
2. Правки применяются только к продуктовым формулировкам, структуре и стилю. Нельзя менять смысл, acceptance criteria, T/H-планы или инженерные команды.
3. Английский оставить только в code/API/path/command/proper noun.
4. После правок снова прогнать `scripts/verify_artifacts.py --phase scenarios <repo-root>`.
5. Так как изменились только формулировки, выполнить targeted verifier pass по semantic-diff и обновить `docs/product/validation/verdict.md`; не перечитывать неизменённые implementation/hardening планы.
6. Прогнать `scripts/verify_artifacts.py --phase validation <repo-root>`.

## Phase 7 — Product PDF assembly

Цель: собрать единый читаемый stakeholder-facing PDF для шеринга со стейкхолдерами.

Алгоритм:
1. Запустить `bash scripts/build_pdf.sh <repo-root> <output-pdf>`. По умолчанию скрипт собирает overview + сценарии + validation verdict и **не включает** implementation/hardening планы.
2. Если нужен внутренний инженерный PDF, пользователь должен явно запросить это; тогда допускается `INCLUDE_ENGINEERING_PLANS=1`.
3. Если pandoc/Chrome недоступны — fallback на python-markdown + Chrome (см. скрипт). Если и Chrome нет — скрипт упадёт с понятной ошибкой и инструкцией.
4. Путь output обычно `~/Downloads/<product>-product-docs.pdf`. **Не коммитить** PDF — только markdown.
5. Открыть PDF через `open` для визуальной проверки пользователем.

## Phase 8 — Post-implementation scenario verification

Цель: после выполнения T/H-плана независимо проверить, что реализованными сценариями можно пользоваться без скрытых доработок.

Запускать эту фазу, когда пользователь просит проверить реализацию, когда план T/H отмечен выполненным, или перед релизом.

Алгоритм:
1. Обновить `docs/plans/<product>-gap.yaml` фактическим статусом каждого FR/AC (`done` / `partial` / `missing`) по коду и тестам.
2. Запустить implementation-verifier (см. [agents/implementation-verifier.md]) без истории обсуждения. Он читает продуктовые сценарии, планы, gap.yaml, фактический код и verification evidence.
3. Верификатор обязан проверить реальные команды из плана и `docs/service/VERIFY.md`, если они применимы.
4. Сохранить отчёт в `docs/product/validation/implementation-verdict.md`.
5. Если есть critical/major — не утверждать готовность; вернуть список блокеров с привязкой к сценарию, FR/AC, файлам и командам.

## Карта файлов скилла

| Файл | Назначение | Когда читать |
| --- | --- | --- |
| [references/scenario-template.md](references/scenario-template.md) | Полный шаблон одного сценария | Phase 1, перед написанием каждого scenario.md |
| [references/overview-template.md](references/overview-template.md) | Структура overview.md | Phase 1, перед написанием overview |
| [references/baseline-template.md](references/baseline-template.md) | Шаблон baseline текущих сценариев + DOT-графа | Режим `baseline`, перед инкрементом или после Phase 1 |
| [references/scenario-card-template.md](references/scenario-card-template.md) | Шаблон компактных scenario cards для планирования инкрементов | Режим `baseline`, перед созданием impact-документа |
| [references/impact-pre-scan-template.md](references/impact-pre-scan-template.md) | Шаблон pre-scan для выбора affected/rejected scenarios до impact | Режим `baseline`, когда affected Sxx неочевидны или фича cross-cutting |
| [references/increment-impact-template.md](references/increment-impact-template.md) | Шаблон impact-документа для новой фичи/доработки | Режим `baseline`, когда задача является инкрементом |
| [references/plan-template.md](references/plan-template.md) | Формат T-задачи + conventions для worker-а | Phase 3 |
| [references/hardening-template.md](references/hardening-template.md) | Формат H-задачи и распределение углов | Phase 4 |
| [references/decision-log-template.md](references/decision-log-template.md) | Формат журнала продуктовых решений | Phase 0 и все human gates |
| [references/product-pdf-template.md](references/product-pdf-template.md) | Состав stakeholder-facing PDF | Phase 6, 7 |
| [references/critic-checklist.md](references/critic-checklist.md) | Универсальный чек-лист для критиков (что проверять) | Все фазы критики |
| [agents/explore-ui.md](agents/explore-ui.md) | Discovery по UI и пользовательским поверхностям | Phase 0 |
| [agents/explore-api.md](agents/explore-api.md) | Discovery по API и контрактам | Phase 0 |
| [agents/explore-runtime.md](agents/explore-runtime.md) | Discovery по runtime и верификации | Phase 0 |
| [agents/scenario-critic.md](agents/scenario-critic.md) | Промпт для критика сценариев | Phase 1, 2 |
| [agents/plan-critic.md](agents/plan-critic.md) | Промпт для критика T- и H-планов | Phase 3, 4 |
| [agents/hardening-auditor.md](agents/hardening-auditor.md) | Промпт для аудитора-генератора H-задач | Phase 4 |
| [agents/independent-verifier.md](agents/independent-verifier.md) | Финальный независимый валидатор | Phase 5 |
| [agents/style-editor-ru.md](agents/style-editor-ru.md) | Финальная вычитка русского продуктового текста | Phase 6 |
| [agents/style-editor-en.md](agents/style-editor-en.md) | Финальная вычитка английского продуктового текста | Phase 6 |
| [agents/implementation-verifier.md](agents/implementation-verifier.md) | Проверка пригодности реализованных сценариев | Phase 8 |
| [agents/ux-continuity-author.md](agents/ux-continuity-author.md) | Автор раздела «Дополнительные сценарии и связь» | Phase 2 |
| [scripts/build_pdf.sh](scripts/build_pdf.sh) | Сборка единого PDF | Phase 7 |
| [scripts/verify_artifacts.py](scripts/verify_artifacts.py) | Машинная проверка структуры артефактов и validation gate | Phase 1, 3, 4, 5, 6 |

## Принципы работы

1. **Выбирай минимальный режим.** Не создавай артефакты, которые не являются
   ответом пользователя или прямой зависимостью выбранного package.
2. **Планируй от результата.** Первая исполняемая задача даёт
   acceptance-bearing vertical slice; foundation появляется just-in-time с
   первым consumer-ом.
3. **Ограничивай assurance.** Норма — один critic/verifier pass и один targeted
   delta recheck. Полный повтор требует нового structural risk.
4. **Соблюдай gate locality.** Проверка блокирует только тот artifact, claim или
   unsafe action, который она защищает.
5. **Считай полный contour.** Budget включает orchestration, author/producer,
   verifier и разрешённый repair; stop-loss применяется до перерасхода.
6. **Независимый верификатор пропорционален package.** Он обязателен для полного
   PRD/delivery package и stakeholder gate; узкие режимы проверяют только свой
   semantic delta и прямые источники.
7. **Решения не прятать в тексте.** Варианты и выбор фиксируются в `docs/product/decisions.md`; планы нельзя строить по неутверждённым решениям.
8. **Иммутабельность сценариев.** После Phase 1 + критика сценарии — иммутабельная цель для плана и hardening. Все изменения требуют явного запроса пользователя.
9. **Инкремент встраивается в baseline.** Новая фича должна показать влияние на текущие сценарии; если влияния нет, это отдельный продуктовый остров и требует явного решения пользователя.
10. **Сценарии не лезут в код, план не лезет в продуктовую ценность.** Сценарии описывают «что и зачем»; план — «как», на уровне команд и файлов; hardening — «что укрепить».
11. **PDF — продуктовый артефакт для шеринга, а не источник правды.** Markdown — каноничен; PDF только генерируется из него и не коммитится. Implementation/hardening планы не попадают в PDF без явного запроса.
