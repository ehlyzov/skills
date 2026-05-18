# Scenario cards

Файл: `docs/product/scenario-cards.md`

Используется в режиме `baseline`, чтобы агент при продуктовом инкременте быстро нашёл затронутые сценарии, прочитал их пользовательскую историю и учёл regression paths перед планированием.

Scenario card не заменяет полный PRD/scenario-файл. Это компактный индекс пользовательского поведения и точек расширения.

````markdown
# Scenario Cards

## Как использовать при инкременте

1. Найди в `current-scenario-baseline.md` и `scenario-graph.dot` вероятные affected Sxx.
2. Прочитай карточки affected Sxx в этом файле.
3. В `<feature>-impact.md` укажи:
   - affected Sxx;
   - touched extension points;
   - changed happy-path steps;
   - required regression checks;
   - files/docs from `Read before`.
4. Не пиши implementation plan, пока impact-документ не показывает влияние на эти карточки.

## SXX — <Scenario name>

- **Status:** current / current runtime / growth / legacy / external / approved deprecation pending.
- **Persona:** <1-3 персоны>.
- **Entry:** <страница, команда, внешний канал, deep link>.
- **Exit / next:** <куда пользователь уходит после сценария>.
- **Read before:** <3-7 links: code/docs/tests/contracts>.

### User story

Как <persona>, я <действие/намерение>, чтобы <ценность/результат>.

### Happy path

1. <Шаг пользователя>.
2. <Системная реакция>.
3. <Переход или результат>.

### Alternative / error paths

- A1. <вариант>.
- E1. <ошибка/guard/fallback>.

### Extension points

- `<extension-id>` — <что можно расширять и какие границы нельзя ломать>.

### Regression checks

- <что обязательно проверить, если инкремент трогает этот сценарий>.

### Planning notes

- <короткие ограничения, unresolved decisions, known gaps>.
````

## Правила достаточности

- Каждая current-карточка имеет 3-8 happy-path шагов и 3-7 regression checks.
- Extension points должны быть конкретнее, чем "UI" или "backend": `<surface>.<capability>`, `<domain>.<lifecycle>`, `<flow>.<branch>`.
- `Read before` должен вести к живым файлам или документам, чтобы агент быстро открыл нужный контекст.
- Если сценарий имеет approved deprecation pending, карточка должна назвать и current runtime, и approved target state.
