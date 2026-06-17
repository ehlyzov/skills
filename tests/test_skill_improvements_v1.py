from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_product_workflow_documents_focused_codex_modes() -> None:
    skill = read("product-workflow/SKILL.md")

    for mode in [
        "quick-plan",
        "baseline-only",
        "increment-impact",
        "full-prd",
        "pdf-package",
        "post-implementation-check",
    ]:
        assert mode in skill

    assert "Phase 0 gate is mandatory" in skill
    assert "does not block quick-plan" in skill


def test_product_workflow_documents_codex_no_subagent_fallback() -> None:
    skill = read("product-workflow/SKILL.md")

    assert "Codex no-subagent fallback" in skill
    assert "must be labeled as fallback" in skill
    assert "must not be called independent verification" in skill


def test_service_contour_documents_task_preflight_and_script_policy() -> None:
    skill = read("service-knowledge-contour/SKILL.md")

    assert "Mode 0: task-preflight" in skill
    assert "do not bootstrap or refresh" in skill
    assert "scripts are mandatory for this skill package" in skill
    assert "do not copy or install bin/* into a target service" in skill


def test_product_eval_set_covers_focused_v1_cases() -> None:
    payload = json.loads(read("product-workflow/evals/evals.json"))
    names = {item["name"] for item in payload["evals"]}

    assert {
        "quick-plan-does-not-require-full-phase0",
        "full-prd-requires-phase0-gate",
        "codex-no-subagent-fallback-is-labeled",
    } <= names


def test_evidence_artifacts_exist_for_each_focused_v1_improvement() -> None:
    evidence = read("docs/evidence/skill-improvements-v1.md")

    for phrase in [
        "Product mode selection",
        "Codex no-subagent fallback",
        "Contour task-preflight",
        "Contour script installation policy",
    ]:
        assert phrase in evidence

    scenario_dir = REPO_ROOT / "docs" / "evidence" / "pressure-scenarios"
    for name in [
        "product-quick-plan.md",
        "product-full-prd-gate.md",
        "product-codex-fallback.md",
        "contour-task-preflight.md",
        "contour-script-policy.md",
    ]:
        text = (scenario_dir / name).read_text(encoding="utf-8")
        assert "## User prompt" in text
        assert "## Prior risk" in text
        assert "## Expected new behavior" in text
