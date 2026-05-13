# Knowledge Contour Skills

Репозиторий содержит готовые Codex skills: самодостаточные папки с `SKILL.md`,
вспомогательными prompt-файлами, reference-документами и скриптами.

## Навыки

### `service-knowledge-contour`

Навык для bootstrap, refresh, audit, promote и prune минимального knowledge
contour в одном service-репозитории.

Используется, когда сервису нужен устойчивый операционный слой знаний для
людей и агентов: `AGENTS.md`, `CLAUDE.md`, `docs/service/SERVICE_MAP.md`,
`docs/service/VERIFY.md`, реестр knowledge gaps и генерируемые overlays.

Состав:

- `SKILL.md` — правила и workflow поддержания service knowledge contour.
- `bin/` — shell-скрипты для bootstrap, refresh, audit, promote и prune.
- `examples/` — пример GitHub Actions проверки и PR template.
- `tests/` — контрактные проверки bootstrap-поведения.

### `product-workflow`

Навык для сквозной продуктовой проработки: PRD, сценарии, command-level план
реализации, hardening plan, независимая верификация и сборка единого PDF.

Используется, когда нужно описать продукт или фичу через пользовательские
сценарии, согласовать roadmap с реализационным планом и получить артефакты,
которые можно передать команде разработки или стейкхолдерам.

Состав:

- `SKILL.md` — основной workflow из 7 фаз.
- `agents/` — prompt-файлы для критиков, аудитора hardening, UX continuity
  author и независимого verifier.
- `references/` — шаблоны overview, сценариев, implementation plan,
  hardening plan и checklist для критики.
- `scripts/` — проверка структуры markdown-артефактов и сборка PDF.
- `evals/` — eval-набор для проверки ожидаемого поведения навыка.

## Установка

Скопируйте нужную папку навыка в локальный каталог Codex skills:

```bash
cp -R service-knowledge-contour ~/.codex/skills/
cp -R product-workflow ~/.codex/skills/
```

Если навык уже установлен и его нужно заменить:

```bash
rm -rf ~/.codex/skills/service-knowledge-contour ~/.codex/skills/product-workflow
cp -R service-knowledge-contour product-workflow ~/.codex/skills/
```

## Проверка

Проверить наличие обязательных файлов:

```bash
test -f service-knowledge-contour/SKILL.md
test -f product-workflow/SKILL.md
```

Проверить исполняемые скрипты:

```bash
test -x service-knowledge-contour/bin/bootstrap.sh
test -x product-workflow/scripts/build_pdf.sh
test -x product-workflow/scripts/verify_artifacts.py
```

Для `service-knowledge-contour` также доступен pytest-контракт:

```bash
pytest service-knowledge-contour/tests
```

## Правила поддержки

- Канонический вход в каждый навык — `SKILL.md`.
- Дополнительные материалы должны лежать рядом с навыком в `agents/`,
  `references/`, `scripts/`, `assets/`, `examples/`, `tests/` или `evals/`.
- Не добавляйте README внутрь папок навыков без отдельной причины: описание
  набора навыков хранится в этом корневом файле.
- Скрипты должны оставаться исполняемыми, если workflow вызывает их напрямую.
