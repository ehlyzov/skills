# Skill Improvements V1 Evidence

Branch: `skill-improvements-evidence-v1`

Scope: focused Codex compatibility and verifiable behavior improvements for `product-workflow` and `service-knowledge-contour`.

## Baseline before changes

| Command | Result |
| --- | --- |
| `python3 -m py_compile product-workflow/scripts/verify_artifacts.py` | pass |
| `bash -n product-workflow/scripts/build_pdf.sh service-knowledge-contour/bin/*.sh` | pass |
| `pytest -q tests/product_workflow service-knowledge-contour/tests` | pass, 23 passed |
| `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py product-workflow` | pass |
| `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py service-knowledge-contour` | pass |

## Improvement proofs

| Improvement | Prior weakness | Change | Proof artifact | Verification command | Result |
| --- | --- | --- | --- | --- | --- |
| Product mode selection | Small planning requests could be pulled into the full 9-phase PRD pipeline. | Added explicit `quick-plan`, `baseline-only`, `increment-impact`, `full-prd`, `pdf-package`, and `post-implementation-check` modes. | `docs/evidence/pressure-scenarios/product-quick-plan.md`, `product-workflow/evals/evals.json` | `pytest -q tests/test_skill_improvements_v1.py` | pass, 5 passed |
| Codex no-subagent fallback | A self-review could be mislabeled as independent verification when Codex had no child-agent mechanism. | Added explicit fallback policy: label fallback, do not call it independent verification. | `docs/evidence/pressure-scenarios/product-codex-fallback.md`, `product-workflow/evals/evals.json` | `pytest -q tests/test_skill_improvements_v1.py` | pass, 5 passed |
| Contour task-preflight | Ordinary feature/debug work could accidentally trigger bootstrap or refresh overhead. | Added `task-preflight` as a read-only context mode for existing contours. | `docs/evidence/pressure-scenarios/contour-task-preflight.md` | `pytest -q tests/test_skill_improvements_v1.py` | pass, 5 passed |
| Contour script installation policy | `bin/*` support scripts could be interpreted as mandatory installation payload for every target service task. | Clarified that scripts are mandatory for the skill package/toolchain, not copied during task-preflight or lightweight read-only work. | `docs/evidence/pressure-scenarios/contour-script-policy.md` | `pytest -q tests/test_skill_improvements_v1.py` | pass, 5 passed |

## RED evidence

`pytest -q tests/test_skill_improvements_v1.py` failed before the skill updates with 5 failing assertions: missing product modes, missing Codex fallback policy, missing contour task-preflight, missing eval cases, and missing evidence artifacts.

## Post-change verification

| Command | Result |
| --- | --- |
| `pytest -q tests/test_skill_improvements_v1.py` | pass, 5 passed |
| `python3 -m py_compile product-workflow/scripts/verify_artifacts.py` | pass |
| `bash -n product-workflow/scripts/build_pdf.sh service-knowledge-contour/bin/*.sh` | pass |
| `pytest -q tests/product_workflow service-knowledge-contour/tests tests/test_skill_improvements_v1.py` | pass, 28 passed |
| `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py product-workflow` | pass |
| `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py service-knowledge-contour` | pass |
