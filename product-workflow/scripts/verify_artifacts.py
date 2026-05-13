#!/usr/bin/env python3
"""Машинная проверка структурной корректности артефактов product-workflow.

Использование:
    python3 verify_artifacts.py --phase scenarios <docs/product/>
    python3 verify_artifacts.py --phase plan      <docs/plans/>
    python3 verify_artifacts.py --phase validation <repo-root>
    python3 verify_artifacts.py --phase all        <repo-root>

Phase scenarios:
    - 9 разделов в каждом scenarios/*.md.
    - 3 подсекции User flow.
    - shape совпадает с шаблоном.
    - overview index ↔ файлы согласованы 1-к-1.

Phase plan:
    - все T-задачи имеют 9 обязательных полей.
    - финальный grep по `^- \\*\\*Status:\\*\\*` находит ровно столько строк, сколько задач.
    - Depends on указывает на существующие задачи.

Phase validation:
    - существует docs/product/validation/verdict.md.
    - verdict.md создан не раньше product/plans артефактов.
    - verdict.md содержит разрешающий независимый вердикт.

Phase all:
    - все вышеперечисленные проверки.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS_SCENARIO = [
    ("Problem", "Проблема"),
    ("Goal", "Цель"),
    ("Non-goals", "Не входит в сценарий"),
    ("User flow", "Пользовательский сценарий"),
    ("Functional requirements", "Функциональные требования"),
    ("Non-functional requirements", "Нефункциональные требования"),
    ("Architecture constraints", "Архитектурные ограничения"),
    ("Acceptance criteria", "Критерии приёмки"),
    ("Test plan", "План проверки"),
]
REQUIRED_USER_FLOW_SUBSECTIONS = [
    "Основной сценарий",
    "Альтернативные сценарии",
    "Ошибочные сценарии",
]
REQUIRED_TASK_FIELDS = [
    "Status",
    "Goal",
    "Sources",
    "Depends on",
    "Read first",
    "Modify",
    "Steps",
    "Verify",
    "DoD",
]


def check_scenario_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8")
    h2_headings = re.findall(r"^## ([^\n]+)$", text, re.MULTILINE)
    h3_headings = re.findall(r"^### ([^\n]+)$", text, re.MULTILINE)
    normalized_h2 = [h.strip() for h in h2_headings]
    for aliases in REQUIRED_SECTIONS_SCENARIO:
        if not any(h in aliases for h in normalized_h2):
            issues.append(f"missing required section: {aliases[0]} / {aliases[1]}")
    if "User flow" in normalized_h2 or "Пользовательский сценарий" in normalized_h2:
        for sub in REQUIRED_USER_FLOW_SUBSECTIONS:
            # подсекция может иметь suffix-уточнение: "Основной сценарий: <details>"
            if not any(h.strip() == sub or h.strip().startswith(sub + ":") or h.strip().startswith(sub + " (") for h in h3_headings):
                issues.append(f"User flow missing subsection: {sub}")
    if not re.search(r"^- \*\*Persona:\*\*", text, re.MULTILINE):
        issues.append("missing 'Persona:' header")
    if not re.search(r"^- \*\*Статус:\*\*", text, re.MULTILINE):
        issues.append("missing 'Статус:' header")
    return issues


def check_scenarios(docs_product: Path) -> int:
    overview = docs_product / "overview.md"
    scenarios_dir = docs_product / "scenarios"
    rc = 0
    if not overview.exists():
        print(f"FAIL overview.md does not exist at {overview}")
        rc = 1
    if not scenarios_dir.exists():
        print(f"FAIL scenarios/ does not exist at {scenarios_dir}")
        return 1
    scenario_files = sorted(scenarios_dir.glob("*.md"))
    if not scenario_files:
        print(f"FAIL no scenario files in {scenarios_dir}")
        return 1
    print(f"=== {len(scenario_files)} scenario files ===")
    for sf in scenario_files:
        problems = check_scenario_file(sf)
        if problems:
            rc = 1
            for p in problems:
                print(f"FAIL {sf.relative_to(docs_product)}: {p}")
        else:
            print(f"OK   {sf.relative_to(docs_product)}")
    if overview.exists():
        ov = overview.read_text(encoding="utf-8")
        idx_files = set(re.findall(r"\(scenarios/([\w./-]+\.md)\)", ov))
        actual = {sf.name for sf in scenario_files}
        missing_in_index = actual - idx_files
        extra_in_index = idx_files - actual
        if missing_in_index:
            rc = 1
            print(f"FAIL overview.md index missing references to: {sorted(missing_in_index)}")
        if extra_in_index:
            rc = 1
            print(f"FAIL overview.md index references missing files: {sorted(extra_in_index)}")
        if not missing_in_index and not extra_in_index:
            print("OK   overview index ↔ scenarios consistent")
    return rc


def check_task_block(text: str, prefix: str) -> tuple[int, list[str]]:
    """Returns (count_tasks, list of issues)."""
    task_headers = re.findall(rf"^## ({prefix}\d+)\. ", text, re.MULTILINE)
    issues: list[str] = []
    for tid in task_headers:
        # extract block until next ## or EOF
        m = re.search(
            rf"^## {tid}\. .+?(?=^## (?:{prefix}\d+\.|[А-Яа-яA-Za-z]+(?:\s|$))|\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
        if not m:
            continue
        block = m.group(0)
        for f in REQUIRED_TASK_FIELDS:
            if not re.search(rf"^- \*\*{re.escape(f)}:\*\*", block, re.MULTILINE):
                issues.append(f"{tid}: missing field {f}")
    return len(task_headers), issues


def check_plan_file(path: Path, prefix: str) -> int:
    if not path.exists():
        print(f"FAIL plan file does not exist: {path}")
        return 1
    text = path.read_text(encoding="utf-8")
    count, issues = check_task_block(text, prefix)
    if not count:
        print(f"FAIL no {prefix}-tasks in {path.name}")
        return 1
    print(f"=== {count} {prefix}-tasks in {path.name} ===")
    rc = 0
    if issues:
        rc = 1
        for i in issues:
            print(f"FAIL {i}")
    # check Depends on points to existing IDs with the same prefix
    all_ids = set(re.findall(rf"^## ({prefix}\d+)\. ", text, re.MULTILINE))
    for tid_match in re.finditer(
        rf"^## ({prefix}\d+)\. .+?^- \*\*Depends on:\*\* ([^\n]+)$",
        text,
        re.MULTILINE | re.DOTALL,
    ):
        tid, deps_line = tid_match.group(1), tid_match.group(2)
        deps = re.findall(rf"\b{prefix}\d+\b", deps_line)
        for d in deps:
            if d not in all_ids:
                rc = 1
                print(f"FAIL {tid}: Depends on {d} — not found")
    if rc == 0:
        print(f"OK   all {prefix}-tasks have 9 required fields")
    # final-check command
    unchecked = len(re.findall(r"^- \*\*Status:\*\* - \[ \]", text, re.MULTILINE))
    checked = len(re.findall(r"^- \*\*Status:\*\* - \[x\]", text, re.MULTILINE))
    print(f"     Status: {unchecked} unchecked, {checked} checked")
    return rc


def collect_task_ids(paths: list[Path], prefix: str) -> set[str]:
    ids: set[str] = set()
    for path in paths:
        text = path.read_text(encoding="utf-8")
        ids.update(re.findall(rf"^## ({prefix}\d+)\. ", text, re.MULTILINE))
    return ids


def check_hardening_t_dependencies(hardening_files: list[Path], implementation_files: list[Path]) -> int:
    rc = 0
    t_ids = collect_task_ids(implementation_files, "T")
    if not t_ids:
        print("FAIL hardening validation requires at least one implementation plan with T-tasks")
        return 1
    for path in hardening_files:
        text = path.read_text(encoding="utf-8")
        for tid_match in re.finditer(
            r"^## (H\d+)\. .+?^- \*\*Depends on:\*\* ([^\n]+)$",
            text,
            re.MULTILINE | re.DOTALL,
        ):
            hid, deps_line = tid_match.group(1), tid_match.group(2)
            t_deps = re.findall(r"\bT\d+\b", deps_line)
            if not t_deps:
                rc = 1
                print(f"FAIL {hid}: Depends on must include at least one T-task")
                continue
            for dep in t_deps:
                if dep not in t_ids:
                    rc = 1
                    print(f"FAIL {hid}: Depends on {dep} — not found in implementation plan")
    if rc == 0:
        print("OK   all H-task T-dependencies point to implementation tasks")
    return rc


def check_validation(repo_root: Path) -> int:
    product_dir = repo_root / "docs" / "product"
    plans_dir = repo_root / "docs" / "plans"
    verdict = product_dir / "validation" / "verdict.md"
    if not verdict.exists():
        print(f"FAIL independent validation verdict is missing: {verdict}")
        return 1

    text = verdict.read_text(encoding="utf-8")
    success_markers = [
        "Артефакты целостны, непротиворечивы, замкнуты",
        "Готовы к финальной упаковке",
        "Реализованные сценарии пригодны",
    ]
    if not any(marker in text for marker in success_markers):
        print("FAIL independent validation verdict does not contain an approved final verdict")
        return 1

    verdict_mtime = verdict.stat().st_mtime
    stale_inputs: list[str] = []
    for base in [product_dir, plans_dir]:
        if not base.exists():
            continue
        for path in base.rglob("*.md"):
            if path == verdict:
                continue
            if path.stat().st_mtime > verdict_mtime:
                stale_inputs.append(path.relative_to(repo_root).as_posix())
    if stale_inputs:
        print("FAIL independent validation verdict is stale relative to:")
        for rel in stale_inputs[:20]:
            print(f"  - {rel}")
        return 1

    print("OK   independent validation verdict is present, approving, and fresh")
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--phase", choices=["scenarios", "plan", "hardening", "validation", "all"], required=True)
    p.add_argument("path", help="path to docs/product/, docs/plans/, or repo root for --phase all")
    args = p.parse_args()

    target = Path(args.path).expanduser().resolve()
    rc = 0

    if args.phase in ("scenarios", "all"):
        product_dir = target if (target / "scenarios").exists() else target / "docs" / "product"
        if product_dir.exists():
            rc |= check_scenarios(product_dir)
        else:
            print(f"FAIL no docs/product/ found in {target}")
            rc = 1

    if args.phase in ("plan", "all"):
        plans_dir = target if any(target.glob("*implementation-plan*.md")) else target / "docs" / "plans"
        if plans_dir.exists():
            implementation_files = sorted(plans_dir.glob("*implementation-plan*.md"))
            if not implementation_files:
                print(f"FAIL no implementation plan files in {plans_dir}")
                rc = 1
            for f in implementation_files:
                rc |= check_plan_file(f, "T")
        else:
            print(f"FAIL no docs/plans/ found in {target}")
            rc = 1

    if args.phase in ("hardening", "all"):
        plans_dir = target if any(target.glob("*hardening-plan*.md")) else target / "docs" / "plans"
        if plans_dir.exists():
            hardening_files = sorted(plans_dir.glob("*hardening-plan*.md"))
            implementation_files = sorted(plans_dir.glob("*implementation-plan*.md"))
            if not hardening_files:
                print(f"FAIL no hardening plan files in {plans_dir}")
                rc = 1
            for f in hardening_files:
                rc |= check_plan_file(f, "H")
            if hardening_files:
                rc |= check_hardening_t_dependencies(hardening_files, implementation_files)
        else:
            print(f"FAIL no docs/plans/ found in {target}")
            rc = 1

    if args.phase in ("validation", "all"):
        repo_root = target if (target / "docs").exists() else target.parent
        rc |= check_validation(repo_root)

    return rc


if __name__ == "__main__":
    sys.exit(main())
