from __future__ import annotations

import subprocess
import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VERIFY = REPO_ROOT / "product-workflow" / "scripts" / "verify_artifacts.py"
BUILD_PDF = REPO_ROOT / "product-workflow" / "scripts" / "build_pdf.sh"


def run_verify(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(VERIFY), *args],
        cwd=cwd or REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def write_task(path: Path, prefix: str, depends_on: str) -> None:
    path.write_text(
        f"""# Example plan

## {prefix}1. Example task

- **Status:** - [ ]
- **Goal:** Проверить структуру задачи.
- **Sources:** docs/product/overview.md
- **Depends on:** {depends_on}
- **Read first:**
  - docs/product/overview.md
- **Modify:**
  - src/example.py
- **Product artifacts:** No product artifact update because this fixture only checks plan task structure.
- **Steps:**
  1. Сделать минимальную правку.
- **Verify:**
  ```bash
  pytest
  ```
- **DoD:**
  - Проверка прошла.
""",
        encoding="utf-8",
    )


def write_baseline_bundle(product: Path) -> None:
    product.mkdir(parents=True, exist_ok=True)
    (product / "current-scenario-baseline.md").write_text(
        """# Current Scenario Baseline

## Назначение

Fixture baseline.

## Источники evidence

| Область | Evidence paths | Confidence | Unknowns |
| --- | --- | --- | --- |
| UI / pages | `web/app.py` | high | none |

## Сценарии baseline

| ID | Scenario | Status | Persona | Entry | Exit / next | Surfaces | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S01 | Capture input | current | user | `/capture` | S02 | `web/app.py` | core |
| S02 | Review result | current | user | S01 | end | `web/app.py` | core |

## DOT-граф

Канонический DOT хранится рядом.

## Инварианты baseline

- Current scenarios have entry and exit.
""",
        encoding="utf-8",
    )
    (product / "scenario-cards.md").write_text(
        """# Scenario Cards

## S01 — Capture input

- **Status:** current.
- **Persona:** user.
- **Entry:** `/capture`.
- **Exit / next:** S02.
- **Read before:** `web/app.py`.

### User story

Как user, я фиксирую ввод, чтобы получить результат.

### Happy path

1. Пользователь вводит текст.
2. Система сохраняет его.
3. Пользователь переходит к S02.

### Extension points

- `capture.input` — граница ввода.

### Regression checks

- Ввод не теряется.

## S02 — Review result

- **Status:** current.
- **Persona:** user.
- **Entry:** S01.
- **Exit / next:** end.
- **Read before:** `web/app.py`.

### User story

Как user, я проверяю результат, чтобы завершить работу.

### Happy path

1. Пользователь открывает результат.
2. Система показывает сохранённые данные.
3. Пользователь завершает сценарий.

### Extension points

- `review.result` — граница просмотра.

### Regression checks

- Результат остаётся доступен.
""",
        encoding="utf-8",
    )
    (product / "scenario-graph.dot").write_text(
        """digraph ProductScenarios {
  "S01: Capture input" -> "S02: Review result";
}
""",
        encoding="utf-8",
    )


def write_valid_pre_scan(product: Path) -> None:
    increments = product / "increments"
    increments.mkdir(exist_ok=True)
    (increments / "sample-pre-scan.md").write_text(
        """# Impact pre-scan — sample

## Назначение

Проверить затронутые сценарии.

## Evidence opened

| Evidence | Why opened | Signal |
| --- | --- | --- |
| `current-scenario-baseline.md` | Найти baseline | S01 |

## Candidate affected scenarios

| Scenario | Why candidate | Touched extension points | Evidence to read next |
| --- | --- | --- | --- |
| S01 | меняется capture | `capture.input` | `scenario-cards.md#S01` |

## Rejected scenarios

| Scenario | Why not affected | Evidence |
| --- | --- | --- |
| S02 | review не меняется | `scenario-cards.md#S02` |

## Cross-cutting checklist

| Area | Baseline scenario | Affected? | Rationale |
| --- | --- | --- | --- |
| Auth/session/legal | N/A | no | нет такой baseline-области |
| Search/recall/navigation | N/A | no | поиск не меняется |
| Settings/preferences/privacy | N/A | no | настройки не меняются |
| Operator/admin/runtime | N/A | no | runtime не меняется |

## Open decisions

- None.

## Recommendation

Proceed to impact with affected scenarios: S01.
""",
        encoding="utf-8",
    )


def write_valid_impact(product: Path) -> None:
    increments = product / "increments"
    increments.mkdir(exist_ok=True)
    (increments / "sample-impact.md").write_text(
        """# Increment Impact — sample

## Назначение инкремента

Добавляет встроенный сценарий.

## Pre-scan

- **Pre-scan:** [sample-pre-scan.md](sample-pre-scan.md).

## Тип изменения

- `adds` — добавляет новый сценарий.

## Affected scenarios

| Scenario card | Impact type | Touched extension points | Changed happy-path steps | Required artifact updates | Regression checks |
| --- | --- | --- | --- | --- | --- |
| S01 | adds | `capture.input` | Step 2 | baseline, cards, DOT, impact | capture regression |

## Added scenarios

| New scenario | Entry | Exit / next | Why this is not an island |
| --- | --- | --- | --- |
| S03 | S01 | S02 | встроен между существующими сценариями |

## DOT diff

```dot
"S01: Capture input" -> "S03: Sample" [label="increment: sample"];
"S03: Sample" -> "S02: Review result" [label="returns"];
```

## Обновления требований

| Scenario | FR/NFR/AC/Test plan | Change | Reason |
| --- | --- | --- | --- |
| S01 | AC1 | changed | новый handoff |

## Verification impact

- Повторить happy path S01.
""",
        encoding="utf-8",
    )


def test_plan_phase_fails_when_no_implementation_plan_exists(tmp_path: Path) -> None:
    plans = tmp_path / "docs" / "plans"
    plans.mkdir(parents=True)

    result = run_verify("--phase", "plan", str(tmp_path))

    assert result.returncode != 0
    assert "implementation plan" in result.stdout


def test_hardening_phase_fails_when_t_dependency_has_no_matching_task(tmp_path: Path) -> None:
    plans = tmp_path / "docs" / "plans"
    plans.mkdir(parents=True)
    write_task(plans / "example-implementation-plan.md", "T", "—")
    write_task(plans / "example-hardening-plan.md", "H", "T99")

    result = run_verify("--phase", "hardening", str(tmp_path))

    assert result.returncode != 0
    assert "Depends on T99" in result.stdout


def test_pdf_dry_run_excludes_engineering_plans_by_default(tmp_path: Path) -> None:
    product = tmp_path / "docs" / "product"
    scenarios = product / "scenarios"
    validation = product / "validation"
    plans = tmp_path / "docs" / "plans"
    scenarios.mkdir(parents=True)
    validation.mkdir()
    plans.mkdir(parents=True)
    (product / "overview.md").write_text("# Обзор\n\nПродуктовая задача.\n", encoding="utf-8")
    (scenarios / "01-core.md").write_text("# 01 — Core\n\nСценарий.\n", encoding="utf-8")
    write_task(plans / "example-implementation-plan.md", "T", "—")
    write_task(plans / "example-hardening-plan.md", "H", "T1")
    (validation / "verdict.md").write_text(
        "### Вердикт\n\nАртефакты целостны, непротиворечивы, замкнуты. Готовы к финальной упаковке.\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env.update(
        {
            "PRODUCT_WORKFLOW_DRY_RUN": "1",
            "WORK_DIR": str(tmp_path / "work"),
        }
    )
    result = subprocess.run(
        ["bash", str(BUILD_PDF), str(tmp_path), str(tmp_path / "out.pdf")],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    combined = (tmp_path / "work" / "combined.md").read_text(encoding="utf-8")
    assert "Продуктовая задача" in combined
    assert "### Вердикт" in combined
    assert "## T1." not in combined
    assert "## H1." not in combined


def test_pdf_dry_run_rejects_stale_validation_verdict(tmp_path: Path) -> None:
    product = tmp_path / "docs" / "product"
    scenarios = product / "scenarios"
    validation = product / "validation"
    scenarios.mkdir(parents=True)
    validation.mkdir()
    (product / "overview.md").write_text("# Обзор\n\nВерсия 1.\n", encoding="utf-8")
    verdict = validation / "verdict.md"
    verdict.write_text(
        "### Вердикт\n\nАртефакты целостны, непротиворечивы, замкнуты. Готовы к финальной упаковке.\n",
        encoding="utf-8",
    )
    overview = product / "overview.md"
    overview.write_text("# Обзор\n\nВерсия 2.\n", encoding="utf-8")
    os.utime(overview, (verdict.stat().st_mtime + 10, verdict.stat().st_mtime + 10))

    env = os.environ.copy()
    env.update({"PRODUCT_WORKFLOW_DRY_RUN": "1", "WORK_DIR": str(tmp_path / "work")})
    result = subprocess.run(
        ["bash", str(BUILD_PDF), str(tmp_path), str(tmp_path / "out.pdf")],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )

    assert result.returncode != 0
    assert "устарел" in result.stderr


def test_scenarios_phase_accepts_russian_product_headings(tmp_path: Path) -> None:
    product = tmp_path / "docs" / "product"
    scenarios = product / "scenarios"
    scenarios.mkdir(parents=True)
    (product / "overview.md").write_text(
        "| # | Название | Persona | Статус | Файл |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| 01 | Core | developer | current | [01-core.md](scenarios/01-core.md) |\n",
        encoding="utf-8",
    )
    (scenarios / "01-core.md").write_text(
        """# 01 — Core

- **Persona:** developer
- **Статус:** current

## Проблема

Описание.

## Цель

Описание.

## Не входит в сценарий

- Внешние интеграции.

## Пользовательский сценарий

### Основной сценарий

1. Пользователь начинает работу.

### Альтернативные сценарии

- A1. Альтернативный путь.

### Ошибочные сценарии

- E1. Ошибка.

## Функциональные требования

FR1. Система делает действие.

## Нефункциональные требования

NFR1. Ответ до 1 секунды.

## Архитектурные ограничения

AC1. Не менять публичный API.

## Критерии приёмки

AC-1. Проверяемое условие.

## План проверки

- **Unit:** N/A.
- **Integration:** N/A.
- **E2E:** N/A.
- **Migration / rollback:** N/A.
""",
        encoding="utf-8",
    )

    result = run_verify("--phase", "scenarios", str(tmp_path))

    assert result.returncode == 0, result.stdout


def test_baseline_phase_accepts_valid_fixture(tmp_path: Path) -> None:
    product = tmp_path / "docs" / "product"
    write_baseline_bundle(product)

    result = run_verify("--phase", "baseline", str(tmp_path))

    assert result.returncode == 0, result.stdout
    assert "OK   baseline" in result.stdout


def test_baseline_phase_rejects_card_not_present_in_baseline(tmp_path: Path) -> None:
    product = tmp_path / "docs" / "product"
    write_baseline_bundle(product)
    with (product / "scenario-cards.md").open("a", encoding="utf-8") as fh:
        fh.write(
            """
## S99 — Rogue card

- **Status:** current.
- **Persona:** user.
- **Entry:** `/rogue`.
- **Exit / next:** end.
- **Read before:** `web/app.py`.

### User story

Как user, я вижу rogue card.

### Happy path

1. Пользователь открывает rogue card.

### Extension points

- `rogue.card` — rogue extension.

### Regression checks

- Rogue card is rejected.
"""
        )

    result = run_verify("--phase", "baseline", str(tmp_path))

    assert result.returncode != 0
    assert "card S99 is not present in baseline" in result.stdout


def test_pre_scan_phase_accepts_valid_fixture(tmp_path: Path) -> None:
    product = tmp_path / "docs" / "product"
    write_baseline_bundle(product)
    write_valid_pre_scan(product)

    result = run_verify("--phase", "pre-scan", str(tmp_path))

    assert result.returncode == 0, result.stdout
    assert "OK   1 pre-scan files" in result.stdout


def test_pre_scan_phase_rejects_invalid_cross_cutting_area(tmp_path: Path) -> None:
    product = tmp_path / "docs" / "product"
    write_baseline_bundle(product)
    write_valid_pre_scan(product)
    pre_scan = product / "increments" / "sample-pre-scan.md"
    pre_scan.write_text(
        pre_scan.read_text(encoding="utf-8").replace("Auth/session/legal", "Billing/payments"),
        encoding="utf-8",
    )

    result = run_verify("--phase", "pre-scan", str(tmp_path))

    assert result.returncode != 0
    assert "unknown cross-cutting area" in result.stdout


def test_pre_scan_phase_accepts_new_scenario_candidate_with_marker(tmp_path: Path) -> None:
    product = tmp_path / "docs" / "product"
    write_baseline_bundle(product)
    write_valid_pre_scan(product)
    pre_scan = product / "increments" / "sample-pre-scan.md"
    pre_scan.write_text(
        pre_scan.read_text(encoding="utf-8")
        .replace("| S01 | меняется capture |", "| S03 | нужен new scenario для handoff |")
        .replace("affected scenarios: S01", "affected scenarios: S03"),
        encoding="utf-8",
    )

    result = run_verify("--phase", "pre-scan", str(tmp_path))

    assert result.returncode == 0, result.stdout


def test_pre_scan_phase_requires_file_when_explicit(tmp_path: Path) -> None:
    product = tmp_path / "docs" / "product"
    write_baseline_bundle(product)

    result = run_verify("--phase", "pre-scan", str(tmp_path))

    assert result.returncode != 0
    assert "no pre-scan files" in result.stdout


def test_impact_phase_accepts_valid_fixture(tmp_path: Path) -> None:
    product = tmp_path / "docs" / "product"
    write_baseline_bundle(product)
    write_valid_pre_scan(product)
    write_valid_impact(product)

    result = run_verify("--phase", "impact", str(tmp_path))

    assert result.returncode == 0, result.stdout
    assert "OK   1 impact files" in result.stdout


def test_impact_phase_rejects_unknown_added_entry(tmp_path: Path) -> None:
    product = tmp_path / "docs" / "product"
    write_baseline_bundle(product)
    write_valid_impact(product)
    impact = product / "increments" / "sample-impact.md"
    impact.write_text(
        impact.read_text(encoding="utf-8").replace("| S03 | S01 | S02 |", "| S03 | S99 | S02 |"),
        encoding="utf-8",
    )

    result = run_verify("--phase", "impact", str(tmp_path))

    assert result.returncode != 0
    assert "Entry references unknown scenario S99" in result.stdout


def test_impact_phase_rejects_empty_pre_scan_section(tmp_path: Path) -> None:
    product = tmp_path / "docs" / "product"
    write_baseline_bundle(product)
    write_valid_impact(product)
    impact = product / "increments" / "sample-impact.md"
    impact.write_text(
        impact.read_text(encoding="utf-8").replace(
            "## Pre-scan\n\n- **Pre-scan:** [sample-pre-scan.md](sample-pre-scan.md).",
            "## Pre-scan\n\n",
        ),
        encoding="utf-8",
    )

    result = run_verify("--phase", "impact", str(tmp_path))

    assert result.returncode != 0
    assert "Pre-scan must link" in result.stdout


def test_impact_phase_accepts_existing_scenario_change_without_added_rows(tmp_path: Path) -> None:
    product = tmp_path / "docs" / "product"
    write_baseline_bundle(product)
    write_valid_impact(product)
    impact = product / "increments" / "sample-impact.md"
    impact.write_text(
        impact.read_text(encoding="utf-8")
        .replace("`adds`", "`changes`")
        .replace("| S01 | adds |", "| S01 | changes |")
        .replace(
            "| New scenario | Entry | Exit / next | Why this is not an island |\n"
            "| --- | --- | --- | --- |\n"
            "| S03 | S01 | S02 | встроен между существующими сценариями |",
            "N/A — no added scenarios.",
        )
        .replace("| S01 | AC1 | changed | новый handoff |", "| S01 | AC1 | changed | existing flow update |"),
        encoding="utf-8",
    )

    result = run_verify("--phase", "impact", str(tmp_path))

    assert result.returncode == 0, result.stdout


def test_impact_phase_requires_file_when_explicit(tmp_path: Path) -> None:
    product = tmp_path / "docs" / "product"
    write_baseline_bundle(product)

    result = run_verify("--phase", "impact", str(tmp_path))

    assert result.returncode != 0
    assert "no impact files" in result.stdout
