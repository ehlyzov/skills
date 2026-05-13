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
