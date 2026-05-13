# Шаблон плана усиления (H-задачи)

План усиления (`docs/plans/<product>-hardening-plan.md`) описывает архитектурные, безопасностные и поддерживаемостные задачи поверх плана реализации. **Не вводит новой функциональности** — только инварианты, защиты, observability к уже существующему/добавляемому коду.

## Ключевое отличие от Implementation plan

- H-задача всегда имеет `Depends on: TXX` — конкретную T-задачу из главного плана.
- Hardening не правит главный план (`docs/plans/<product>-implementation-plan.md` — иммутабельный).
- Если H-задача обнаруживает, что инвариант уже выполнен — пометь `### Note: already enforced at <file>:<line>` и закрой `- [x]`.
- Конвенция коммитов: `feat(harden): HXX <название>` или `fix(harden): HXX ...`.

## Распределение H-задач

Целевое: 12-25 задач, примерно по трети на угол:

- **Архитектура:** layering, DI, абстракции, расширяемость контрактов, atomic operations, error handling consistency.
- **Безопасность:** auth (token management, TTL), input validation (path traversal, regex whitelists), audit (no-secret-leak), rate-limit, file permissions, gitignore, размер payload, secrets management.
- **Поддерживаемость:** обновление SERVICE_MAP / knowledge-gaps, structured logging, metrics, CHANGELOG policy, инварианты против orphaned TODO.

## Структура файла

Тот же формат, что Implementation plan, но:

```markdown
# <Продукт> — план усиления архитектуры, безопасности и поддерживаемости

## Метаданные

- **Цель:** не меняя планируемого функционала T0..TN, усилить инвариантами, защитами и observability существующие/добавляемые компоненты.
- **Источники:** [implementation-plan](...), [SERVICE_MAP](...), [сценарии](...).
- **Worker:** тот же Sonnet 4.6, single instance.
- **Запуск:** после или параллельно с основным планом.

## Конвенции выполнения

(те же 7 пунктов, что в implementation plan, плюс пункт «не правь главный план»)

## Известные пробелы покрытия (план усиления НЕ закрывает)

5-7 пунктов: pen-test, TLS на localhost (если применимо), formal contract verification, любые отложенные retention/cleanup механизмы, multi-user RBAC, container sandboxing seed-скриптов и т.п. Это design choices или backlog items.

## Список задач

(распределение: архитектура / безопасность / поддерживаемость с явным упоминанием каких какие)

## H1. Архитектура: <название>

(тот же формат: Status / Goal / Sources / Depends on / Read first / Modify / Steps / Verify / DoD)

## H2. Безопасность: <название>
...
```

## Финальный чек

```bash
unchecked=$(grep -cE '^- \*\*Status:\*\* - \[ \]' docs/plans/<product>-hardening-plan.md)
test "$unchecked" = "0" && echo HARDENING-COMPLETE || { echo "outstanding tasks:"; grep -nE '^- \*\*Status:\*\* - \[ \]' docs/plans/<product>-hardening-plan.md; }
```

## Что критик проверяет

- Каждая H-задача имеет `Depends on: TXX`.
- Ни одна H-задача не вводит **новой функциональности** (только инвариант, тест, политика, обновление docs).
- Распределение по углам близко к 1/3 / 1/3 / 1/3.
- Известные пробелы покрытия зафиксированы в начале — критик не возвращается к ним каждый раунд.
- Verify-команды реалистичны (правильные модули, правильные test-классы).
- H-задача не дублирует уже сделанное в T-задаче (если дублирует — `### Note` и close).

## Критические hardening-инварианты, которые часто упускают

При генерации H-задач обязательно проверь, что **хотя бы по одному пункту** из каждой группы попало в план (если применимо к продукту):

1. **Auth & secrets:**
   - Approve-token / API key — где хранится, какой TTL, sliding или fixed.
   - Pre-shared secret — обязательность, минимальная длина (≥ 32 chars).
   - Audit-log не содержит сырых secret/token (тест-инвариант).

2. **Input validation:**
   - Все user-supplied id/name/path параметры — regex whitelist.
   - Path traversal guard на любые id, входящие в filesystem path.
   - JSON payload — лимит размера.
   - Schema validation на mutating endpoints.

3. **Network & runtime:**
   - HTTP сервер биндится только на 127.0.0.1 (если это localhost-tool).
   - Rate-limit на auth-endpoints (brute-force protection).
   - Atomic file writes (tmp + Files.move) для критичных артефактов.

4. **Filesystem hygiene:**
   - File permissions 0700 / 0600 на каталоги с чувствительными данными.
   - .gitignore закрывает runtime-artifacts с потенциально чувствительными данными.

5. **Observability of new code:**
   - Counters для всех новых компонентов.
   - Structured logging для всех новых routes.

6. **Documentation maintenance:**
   - Обновление SERVICE_MAP под новые модули.
   - knowledge-gaps.yaml фиксирует осознанные ограничения.
   - API CHANGELOG с deprecation policy.
   - Инвариант: нет orphaned TODO без owner-prefix.

Эти 6 групп — стандартный чек-лист hardening-auditor. Если что-то из этого не попало в план — добавляй H-задачу.
