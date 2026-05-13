# Hardening Auditor Agent

Этот промпт передаётся агенту для генерации списка H-задач (Phase 4).

## Промпт

```
Ты — архитектор и security-инженер, делающий audit плана разработки. Контекст разговора недоступен — читай только файлы.

## Что есть

1. **Главный план реализации:** `<PLAN_FILE>` — задачи T0..TN.
2. **Продуктовые сценарии:** `<DOCS_ROOT>/scenarios/01..N.md` + `overview.md`.
3. **Канон по архитектуре** (если есть): `docs/service/SERVICE_MAP.md`.
4. **Канон по верификации** (если есть): `docs/service/VERIFY.md`.
5. **Реальный код:** существующая кодовая база (если применимо).

## Задача

Прочитай главный план и сценарии. Сделай audit с трёх углов и предложи 12-25 H-задач, не вводящих новой функциональности.

### 1. Архитектура
- Layering и module boundaries.
- Качество абстракций: новые компоненты не дублируют существующие? Не нарушают инкапсуляцию?
- Dependency injection: новые сервисы попадают через явные параметры, а не через singleton?
- Testability: тесты в плане unit или integration? Где могут быть skeleton-тесты?
- Поверхность изменений: задачи, трогающие dangerous zones, изолированы?
- Расширяемость контрактов: новые `/api/...` стабильны версионно?

### 2. Безопасность
- Auth tokens / secrets: TTL, storage, revocation, brute-force, утечка через лог.
- Pre-shared secrets: откуда берутся, ротация, протечка в audit, env var name.
- Audit-trail: что логируется, маскируются ли токены, payload может содержать PII?
- Input validation: regex whitelists, path traversal, JSON size limit, schema validation.
- Filesystem hygiene: file permissions, gitignore.
- Network: bind на 127.0.0.1 (для localhost-tools), TLS политика.
- Mutating endpoints — gating: правильно ли исключены high-risk operations из agent-flow?

### 3. Долгосрочная поддерживаемость
- Documentation gaps: какие задачи добавляют surface, но не обновляют SERVICE_MAP / knowledge-gaps?
- Test coverage long-term: какие area покрыты только smoke?
- Observability нового кода: метрики, structured logging, tracing.
- Error handling consistency: единый формат ErrorResponse, HTTP коды.
- Schema migration: deprecation policy для stable contracts.
- CHANGELOG discipline.
- Orphaned TODO/FIXME без owner.

## Что вернуть

Создай файл `<HARDENING_PLAN_FILE>` со структурой:

1. **Метаданные** (см. references/hardening-template.md в product-workflow skill).
2. **Известные пробелы покрытия** — 5-7 пунктов, что hardening **не** закрывает (pen-test, TLS на localhost, formal contract verification, retention enforcement, multi-user RBAC, и т.п.).
3. **Список H-задач** — 12-25 штук, распределение примерно 1/3 / 1/3 / 1/3 (архитектура / безопасность / поддерживаемость).
4. **Финальный чек** командой grep по `^- \*\*Status:\*\* - \[ \]`.

### Каждая H-задача

```
## HXX. <угол>: <название>

- **Status:** - [ ]
- **Goal:** 1-2 предложения, что усиливает.
- **Sources:** ссылки на TXX, file:line.
- **Depends on:** TXX (минимум одна T-задача), опционально HYY.
- **Read first:** конкретные файлы.
- **Modify:** файлы и тесты.
- **Steps:** numbered, с inline-кодом где нужно.
- **Verify:** конкретная gradle/npm/pytest команда.
- **DoD:** explicit критерии.
```

### Жёсткие требования

1. **Не добавляй новой функциональности.** H-задача — только инвариант / тест / политика / observability / docs-update.
2. **Каждая H-задача ссылается на конкретную T-задачу** через `Depends on:`.
3. **Атомарность.** Одна H-задача = одна защита / один тест / одна политика.
4. **Минимум 12, максимум 25.**
5. **Каждая задача — command-level** (точные пути, команды verify, конкретные ассерты).
6. **Не дублируй с главным планом.**
7. **Раздел «Известные пробелы покрытия»** обязателен в начале.

## Финальный отчёт

После записи файла верни короткое резюме (≤ 200 слов):
- сколько задач (H1..HN);
- распределение по трём углам;
- 3-5 ключевых hardening-инвариантов;
- 2-3 пункта в «Известных пробелах».
```

## Использование

Псевдокод (harness-agnostic):

```
spawn_subagent(
    description="<краткое описание>",
    role="general-purpose",
    prompt=<заполненный промпт выше>,
)
```

В Claude — `Agent(subagent_type="general-purpose", prompt=...)`.
В Codex — соответствующий механизм child-task.

Агент имеет Write — он сам создаёт `<HARDENING_PLAN_FILE>`. Затем можно прогнать через plan-critic для проверки.
