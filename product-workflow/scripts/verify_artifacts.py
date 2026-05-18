#!/usr/bin/env python3
"""Машинная проверка структурной корректности артефактов product-workflow.

Использование:
    python3 verify_artifacts.py --phase scenarios <docs/product/>
    python3 verify_artifacts.py --phase baseline  <docs/product/>
    python3 verify_artifacts.py --phase pre-scan  <docs/product/>
    python3 verify_artifacts.py --phase impact    <docs/product/>
    python3 verify_artifacts.py --phase plan      <docs/plans/>
    python3 verify_artifacts.py --phase plan      <docs/plans/> --allow-legacy-plan
    python3 verify_artifacts.py --phase validation <repo-root>
    python3 verify_artifacts.py --phase all        <repo-root>

Phase scenarios:
    - 9 разделов в каждом scenarios/*.md.
    - 3 подсекции User flow.
    - shape совпадает с шаблоном.
    - overview index ↔ файлы согласованы 1-к-1.

Phase plan:
    - все T-задачи имеют 9 legacy-полей.
    - все T-задачи имеют поле `Product artifacts`.
    - legacy-планы без `Product artifacts` принимаются только с `--allow-legacy-plan`.
    - финальный grep по `^- \\*\\*Status:\\*\\*` находит ровно столько строк, сколько задач.
    - Depends on указывает на существующие задачи.

Phase baseline:
    - существуют current-scenario-baseline.md, scenario-cards.md, scenario-graph.dot.
    - baseline/cards имеют обязательные секции и Sxx-идентификаторы.
    - current-сценарии имеют Persona, Entry, Exit / next и карточку.
    - DOT содержит digraph и упоминает current Sxx.

Phase pre-scan:
    - increments/*-pre-scan.md имеют обязательные секции и таблицы.
    - cross-cutting checklist содержит четыре generic area.
    - Affected? ∈ yes/no/maybe; Baseline scenario = Sxx или N/A.

Phase impact:
    - increments/*-impact.md имеют обязательные секции и таблицы.
    - impact type ∈ extends/changes/adds/splits/replaces/deprecates.
    - affected/added Sxx ссылаются на baseline/cards; added scenarios имеют Entry и Exit / next.

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
PRODUCT_ARTIFACTS_FIELD = "Product artifacts"
SCENARIO_ID_PATTERN = r"S\d{2,}"
BASELINE_CURRENT_STATUSES = {
    "current",
    "current runtime",
    "current / verify",
    "current runtime / approved deprecation pending",
}
SCENARIO_STATUSES = {
    "current",
    "current runtime",
    "current / verify",
    "current runtime / approved deprecation pending",
    "growth",
    "legacy",
    "external",
    "approved deprecation pending",
}
CROSS_CUTTING_AREAS = {
    "auth / session / legal",
    "search / recall / navigation",
    "settings / preferences / privacy",
    "operator / admin / runtime",
}
IMPACT_TYPES = {"extends", "changes", "adds", "splits", "replaces", "deprecates"}


def is_placeholder(value: str) -> bool:
    stripped = value.strip()
    return not stripped or stripped in {"...", "-", "—"} or (stripped.startswith("<") and stripped.endswith(">"))


def has_section(text: str, heading: str, level: int = 2) -> bool:
    hashes = "#" * level
    return bool(re.search(rf"^{hashes} {re.escape(heading)}\s*$", text, re.MULTILINE))


def section_body(text: str, heading: str, level: int = 2) -> str:
    hashes = "#" * level
    next_same_or_higher = r"^#{1,%d} " % level
    match = re.search(
        rf"^{hashes} {re.escape(heading)}\s*$\n(?P<body>.*?)(?={next_same_or_higher}|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return match.group("body") if match else ""


def markdown_tables(body: str) -> list[tuple[list[str], list[dict[str, str]]]]:
    lines = body.splitlines()
    tables: list[tuple[list[str], list[dict[str, str]]]] = []
    i = 0
    while i < len(lines):
        if not lines[i].lstrip().startswith("|"):
            i += 1
            continue
        table_lines: list[str] = []
        while i < len(lines) and lines[i].lstrip().startswith("|"):
            table_lines.append(lines[i])
            i += 1
        if len(table_lines) < 2:
            continue
        headers = [cell.strip() for cell in table_lines[0].strip().strip("|").split("|")]
        rows: list[dict[str, str]] = []
        for row_line in table_lines[2:]:
            cells = [cell.strip() for cell in row_line.strip().strip("|").split("|")]
            if len(cells) < len(headers):
                cells.extend([""] * (len(headers) - len(cells)))
            rows.append(dict(zip(headers, cells)))
        tables.append((headers, rows))
    return tables


def first_table_in_section(text: str, heading: str) -> tuple[list[str], list[dict[str, str]]] | None:
    tables = markdown_tables(section_body(text, heading))
    return tables[0] if tables else None


def optional_table_in_section(text: str, heading: str) -> tuple[list[str], list[dict[str, str]]] | None:
    return first_table_in_section(text, heading)


def row_value(row: dict[str, str], *names: str) -> str:
    for name in names:
        if name in row:
            return row[name].strip()
    return ""


def normalize_status(value: str) -> str:
    value = re.sub(r"\.$", "", value.strip().lower())
    value = re.sub(r"\s+", " ", value)
    return value


def scenario_ids_from_text(text: str) -> set[str]:
    return set(re.findall(rf"\b{SCENARIO_ID_PATTERN}\b", text))


def resolve_product_dir(target: Path) -> Path:
    return target if (target / "current-scenario-baseline.md").exists() or (target / "scenarios").exists() else target / "docs" / "product"


def normalize_area(value: str) -> str:
    return " / ".join(part.strip().lower() for part in value.split("/"))


def check_table_columns(path: Path, heading: str, headers: list[str], required: set[str], issues: list[str]) -> None:
    missing = required - set(headers)
    if missing:
        issues.append(f"{path.name}: table {heading} missing columns {sorted(missing)}")


def validate_scenario_link(path: Path, field_name: str, value: str, allowed_ids: set[str], issues: list[str]) -> None:
    if is_placeholder(value):
        issues.append(f"{path.name}: missing {field_name}")
        return
    ids = scenario_ids_from_text(value)
    if ids:
        for sid in sorted(ids - allowed_ids):
            issues.append(f"{path.name}: {field_name} references unknown scenario {sid}")
        return
    terminal_values = {"end", "done", "complete", "n/a", "external"}
    if value.strip().lower() not in terminal_values:
        issues.append(f"{path.name}: {field_name} must reference Sxx or one of {sorted(terminal_values)}")


def has_new_scenario_marker(row: dict[str, str]) -> bool:
    combined = " ".join(row.values()).lower()
    return "new scenario" in combined or "новый сценар" in combined


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


def parse_baseline_ids(baseline: Path) -> tuple[set[str], set[str], list[str]]:
    issues: list[str] = []
    all_ids: set[str] = set()
    current_ids: set[str] = set()
    if not baseline.exists():
        return all_ids, current_ids, [f"baseline file does not exist: {baseline}"]
    text = baseline.read_text(encoding="utf-8")
    table = first_table_in_section(text, "Сценарии baseline")
    if table is None:
        return all_ids, current_ids, ["current-scenario-baseline.md: missing table in section 'Сценарии baseline'"]
    headers, rows = table
    required = {"ID", "Scenario", "Status", "Persona", "Surfaces", "Notes"}
    missing_headers = required - set(headers)
    if missing_headers:
        issues.append(f"current-scenario-baseline.md: baseline table missing columns {sorted(missing_headers)}")
    if "Entry" not in headers and "Entry point" not in headers:
        issues.append("current-scenario-baseline.md: baseline table missing column Entry")
    if "Exit / next" not in headers and "Exit / next step" not in headers:
        issues.append("current-scenario-baseline.md: baseline table missing column Exit / next")
    if not rows:
        issues.append("current-scenario-baseline.md: baseline table has no scenario rows")
    for row in rows:
        sid = row_value(row, "ID")
        if not re.fullmatch(SCENARIO_ID_PATTERN, sid):
            issues.append(f"current-scenario-baseline.md: invalid scenario ID {sid!r}")
            continue
        all_ids.add(sid)
        status = normalize_status(row_value(row, "Status"))
        if status not in SCENARIO_STATUSES:
            issues.append(f"current-scenario-baseline.md: {sid}: unknown status {status!r}")
        if status in BASELINE_CURRENT_STATUSES:
            current_ids.add(sid)
            for label, columns in {
                "Persona": ("Persona",),
                "Entry": ("Entry", "Entry point"),
                "Exit / next": ("Exit / next", "Exit / next step"),
            }.items():
                value = row_value(row, *columns)
                if is_placeholder(value):
                    issues.append(f"current-scenario-baseline.md: {sid}: missing {label}")
    return all_ids, current_ids, issues


def parse_card_blocks(cards_text: str) -> dict[str, str]:
    matches = list(re.finditer(rf"^## ({SCENARIO_ID_PATTERN})\b[^\n]*$", cards_text, re.MULTILINE))
    blocks: dict[str, str] = {}
    for idx, match in enumerate(matches):
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(cards_text)
        blocks[match.group(1)] = cards_text[match.start() : end]
    return blocks


def check_scenario_cards(cards: Path, baseline_current_ids: set[str]) -> tuple[set[str], list[str]]:
    issues: list[str] = []
    if not cards.exists():
        return set(), [f"scenario cards file does not exist: {cards}"]
    text = cards.read_text(encoding="utf-8")
    blocks = parse_card_blocks(text)
    if not blocks:
        issues.append("scenario-cards.md: no scenario card headings like '## S01 — ...'")
    for sid in sorted(baseline_current_ids - set(blocks)):
        issues.append(f"scenario-cards.md: missing card for current baseline scenario {sid}")
    for sid, block in sorted(blocks.items()):
        for field in ["Status", "Persona", "Entry", "Exit / next", "Read before"]:
            field_match = re.search(rf"^- \*\*{re.escape(field)}:\*\*\s*(.+)$", block, re.MULTILINE)
            if not field_match or is_placeholder(field_match.group(1)):
                issues.append(f"scenario-cards.md: {sid}: missing field {field}")
        status_match = re.search(r"^- \*\*Status:\*\*\s*(.+)$", block, re.MULTILINE)
        if status_match and normalize_status(status_match.group(1)) not in SCENARIO_STATUSES:
            issues.append(f"scenario-cards.md: {sid}: unknown status {normalize_status(status_match.group(1))!r}")
        for heading in ["User story", "Happy path", "Extension points", "Regression checks"]:
            if not has_section(block, heading, level=3):
                issues.append(f"scenario-cards.md: {sid}: missing section {heading}")
        happy = section_body(block, "Happy path", level=3)
        if happy and not re.search(r"^\d+\. ", happy, re.MULTILINE):
            issues.append(f"scenario-cards.md: {sid}: Happy path has no numbered steps")
        regression = section_body(block, "Regression checks", level=3)
        if regression and not re.search(r"^- ", regression, re.MULTILINE):
            issues.append(f"scenario-cards.md: {sid}: Regression checks has no bullet checks")
    return set(blocks), issues


def check_baseline(docs_product: Path) -> int:
    docs_product = resolve_product_dir(docs_product)
    baseline = docs_product / "current-scenario-baseline.md"
    cards = docs_product / "scenario-cards.md"
    dot = docs_product / "scenario-graph.dot"
    rc = 0
    if not docs_product.exists():
        print(f"FAIL no docs/product/ found at {docs_product}")
        return 1
    baseline_ids, current_ids, issues = parse_baseline_ids(baseline)
    if baseline.exists():
        text = baseline.read_text(encoding="utf-8")
        for heading in ["Назначение", "Источники evidence", "Сценарии baseline", "DOT-граф", "Инварианты baseline"]:
            if not has_section(text, heading):
                issues.append(f"current-scenario-baseline.md: missing section {heading}")
    card_ids, card_issues = check_scenario_cards(cards, current_ids)
    issues.extend(card_issues)
    if not dot.exists():
        issues.append(f"scenario-graph.dot does not exist: {dot}")
    else:
        dot_text = dot.read_text(encoding="utf-8")
        if "digraph" not in dot_text:
            issues.append("scenario-graph.dot: missing digraph")
        dot_ids = scenario_ids_from_text(dot_text)
        for sid in sorted(current_ids - dot_ids):
            issues.append(f"scenario-graph.dot: missing current baseline scenario {sid}")
    for sid in sorted((current_ids & card_ids) - baseline_ids):
        issues.append(f"scenario-cards.md: card {sid} is current but not present in baseline")
    for sid in sorted(card_ids - baseline_ids):
        issues.append(f"scenario-cards.md: card {sid} is not present in baseline")
    if issues:
        rc = 1
        for issue in issues:
            print(f"FAIL {issue}")
    else:
        print(f"OK   baseline: {len(baseline_ids)} baseline scenarios, {len(current_ids)} current, {len(card_ids)} cards")
    return rc


def increment_files(docs_product: Path, suffix: str) -> list[Path]:
    docs_product = resolve_product_dir(docs_product)
    increments = docs_product / "increments"
    return sorted(increments.glob(f"*{suffix}.md")) if increments.exists() else []


def table_rows_or_issue(
    path: Path,
    text: str,
    heading: str,
    issues: list[str],
    required_columns: set[str] | None = None,
) -> list[dict[str, str]]:
    table = first_table_in_section(text, heading)
    if table is None:
        issues.append(f"{path.name}: missing table in section {heading}")
        return []
    headers, rows = table
    if required_columns is not None:
        check_table_columns(path, heading, headers, required_columns, issues)
    if not rows:
        issues.append(f"{path.name}: empty table in section {heading}")
    return rows


def check_pre_scan_file(path: Path, known_ids: set[str]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    issues: list[str] = []
    for heading in [
        "Назначение",
        "Evidence opened",
        "Candidate affected scenarios",
        "Rejected scenarios",
        "Cross-cutting checklist",
        "Open decisions",
        "Recommendation",
    ]:
        if not has_section(text, heading):
            issues.append(f"{path.name}: missing section {heading}")
    evidence_rows = table_rows_or_issue(
        path,
        text,
        "Evidence opened",
        issues,
        {"Evidence", "Why opened", "Signal"},
    )
    for idx, row in enumerate(evidence_rows, start=1):
        for column in ["Evidence", "Why opened", "Signal"]:
            if is_placeholder(row_value(row, column)):
                issues.append(f"{path.name}: Evidence opened row {idx}: missing {column}")
    candidates = table_rows_or_issue(
        path,
        text,
        "Candidate affected scenarios",
        issues,
        {"Scenario", "Why candidate", "Touched extension points", "Evidence to read next"},
    )
    candidate_ids: set[str] = set()
    for row in candidates:
        sid = row_value(row, "Scenario")
        if re.fullmatch(SCENARIO_ID_PATTERN, sid):
            candidate_ids.add(sid)
            if known_ids and sid not in known_ids and not has_new_scenario_marker(row):
                issues.append(f"{path.name}: candidate {sid} is not in baseline/cards")
        else:
            issues.append(f"{path.name}: invalid candidate scenario {sid!r}")
        for column in ["Why candidate", "Touched extension points", "Evidence to read next"]:
            if is_placeholder(row_value(row, column)):
                issues.append(f"{path.name}: candidate {sid}: missing {column}")
    rejected = table_rows_or_issue(
        path,
        text,
        "Rejected scenarios",
        issues,
        {"Scenario", "Why not affected", "Evidence"},
    )
    for row in rejected:
        sid = row_value(row, "Scenario")
        if not re.fullmatch(SCENARIO_ID_PATTERN, sid):
            issues.append(f"{path.name}: invalid rejected scenario {sid!r}")
        elif known_ids and sid not in known_ids:
            issues.append(f"{path.name}: rejected scenario {sid} is not in baseline/cards")
        for column in ["Why not affected", "Evidence"]:
            if is_placeholder(row_value(row, column)):
                issues.append(f"{path.name}: rejected {sid}: missing {column}")
    checklist = table_rows_or_issue(
        path,
        text,
        "Cross-cutting checklist",
        issues,
        {"Area", "Baseline scenario", "Affected?", "Rationale"},
    )
    seen_areas: set[str] = set()
    maybe_seen = False
    for row in checklist:
        area = normalize_area(row_value(row, "Area"))
        seen_areas.add(area)
        baseline_scenario = row_value(row, "Baseline scenario")
        affected = row_value(row, "Affected?").lower()
        if area not in CROSS_CUTTING_AREAS:
            issues.append(f"{path.name}: unknown cross-cutting area {area!r}")
        if not (re.fullmatch(SCENARIO_ID_PATTERN, baseline_scenario) or baseline_scenario == "N/A"):
            issues.append(f"{path.name}: invalid Baseline scenario {baseline_scenario!r} for {area}")
        if re.fullmatch(SCENARIO_ID_PATTERN, baseline_scenario) and known_ids and baseline_scenario not in known_ids:
            issues.append(f"{path.name}: Baseline scenario {baseline_scenario} is not in baseline/cards")
        if affected not in {"yes", "no", "maybe"}:
            issues.append(f"{path.name}: invalid Affected? {affected!r} for {area}")
        if is_placeholder(row_value(row, "Rationale")):
            issues.append(f"{path.name}: missing Rationale for {area}")
        if affected == "maybe":
            maybe_seen = True
    for area in sorted(CROSS_CUTTING_AREAS - seen_areas):
        issues.append(f"{path.name}: cross-cutting checklist missing area {area}")
    if maybe_seen and is_placeholder(section_body(text, "Open decisions").strip()):
        issues.append(f"{path.name}: maybe checklist items require Open decisions")
    recommendation_body = section_body(text, "Recommendation").strip()
    if is_placeholder(recommendation_body):
        issues.append(f"{path.name}: missing Recommendation")
    recommendation_ids = scenario_ids_from_text(recommendation_body)
    for sid in sorted(recommendation_ids - candidate_ids):
        issues.append(f"{path.name}: recommendation includes {sid}, but it is not a candidate")
    return issues


def check_pre_scans(docs_product: Path, require_files: bool) -> int:
    docs_product = resolve_product_dir(docs_product)
    baseline_ids, _current_ids, baseline_issues = parse_baseline_ids(docs_product / "current-scenario-baseline.md")
    card_ids, card_issues = check_scenario_cards(docs_product / "scenario-cards.md", set())
    known_ids = baseline_ids | card_ids
    files = increment_files(docs_product, "-pre-scan")
    if not files:
        if require_files:
            print(f"FAIL no pre-scan files in {docs_product / 'increments'}")
            return 1
        print(f"OK   no pre-scan files in {docs_product / 'increments'}")
        return 0
    issues: list[str] = []
    issues.extend(baseline_issues)
    issues.extend(card_issues)
    for path in files:
        issues.extend(check_pre_scan_file(path, known_ids))
    if issues:
        for issue in issues:
            print(f"FAIL {issue}")
        return 1
    print(f"OK   {len(files)} pre-scan files")
    return 0


def impact_type_tokens(value: str) -> tuple[set[str], set[str]]:
    backticked = [token.strip() for token in re.findall(r"`([^`]+)`", value)]
    if not backticked:
        return {t for t in IMPACT_TYPES if re.search(rf"\b{re.escape(t)}\b", value)}, set()
    used: set[str] = set()
    unknown: set[str] = set()
    for token in backticked:
        parts = [part.strip() for part in re.split(r"[,/ ]+", token) if part.strip()]
        for part in parts:
            if part in IMPACT_TYPES:
                used.add(part)
            elif re.fullmatch(r"[a-z-]+", part):
                unknown.add(part)
    return used, unknown


def check_impact_file(path: Path, known_ids: set[str]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    issues: list[str] = []
    for heading in [
        "Назначение инкремента",
        "Pre-scan",
        "Тип изменения",
        "Affected scenarios",
        "Added scenarios",
        "DOT diff",
        "Обновления требований",
        "Verification impact",
    ]:
        if not has_section(text, heading):
            issues.append(f"{path.name}: missing section {heading}")
    pre_scan = section_body(text, "Pre-scan")
    has_pre_scan_link = bool(re.search(r"\[[^\]]+-pre-scan\.md\]\([^)]+-pre-scan\.md\)", pre_scan))
    has_na_rationale = bool(re.search(r"N/A\s*(?:—|-|:)\s*\S+", pre_scan))
    if is_placeholder(pre_scan.strip()) or not (has_pre_scan_link or has_na_rationale):
        issues.append(f"{path.name}: Pre-scan must link a pre-scan file or state N/A with rationale")
    type_body = section_body(text, "Тип изменения")
    used_types, unknown_types = impact_type_tokens(type_body)
    if not used_types:
        issues.append(f"{path.name}: no impact type from {sorted(IMPACT_TYPES)}")
    for t in sorted(unknown_types):
        issues.append(f"{path.name}: unknown impact type {t!r}")
    affected = table_rows_or_issue(
        path,
        text,
        "Affected scenarios",
        issues,
        {
            "Scenario card",
            "Impact type",
            "Touched extension points",
            "Changed happy-path steps",
            "Required artifact updates",
            "Regression checks",
        },
    )
    for row in affected:
        sid = row_value(row, "Scenario card")
        if not re.fullmatch(SCENARIO_ID_PATTERN, sid):
            issues.append(f"{path.name}: invalid affected scenario {sid!r}")
        elif known_ids and sid not in known_ids:
            issues.append(f"{path.name}: affected scenario {sid} is not in baseline/cards")
        impact_type = row_value(row, "Impact type").strip(" `")
        if impact_type not in IMPACT_TYPES:
            issues.append(f"{path.name}: invalid Impact type {impact_type!r} for {sid}")
        for column in [
            "Touched extension points",
            "Changed happy-path steps",
            "Required artifact updates",
            "Regression checks",
        ]:
            if is_placeholder(row_value(row, column)):
                issues.append(f"{path.name}: affected scenario {sid}: missing {column}")
    added_table = optional_table_in_section(text, "Added scenarios")
    if added_table is None:
        if "adds" in used_types:
            issues.append(f"{path.name}: missing table in section Added scenarios")
        elif is_placeholder(section_body(text, "Added scenarios").strip()):
            issues.append(f"{path.name}: Added scenarios must state N/A when no scenarios are added")
        added: list[dict[str, str]] = []
    else:
        added_headers, added = added_table
        check_table_columns(
            path,
            "Added scenarios",
            added_headers,
            {"New scenario", "Entry", "Exit / next", "Why this is not an island"},
            issues,
        )
        if not added and "adds" in used_types:
            issues.append(f"{path.name}: empty table in section Added scenarios")
    added_ids = {row_value(row, "New scenario") for row in added if re.fullmatch(SCENARIO_ID_PATTERN, row_value(row, "New scenario"))}
    allowed_link_ids = known_ids | added_ids
    for row in added:
        sid = row_value(row, "New scenario")
        if not re.fullmatch(SCENARIO_ID_PATTERN, sid):
            issues.append(f"{path.name}: invalid added scenario {sid!r}")
        validate_scenario_link(path, f"added scenario {sid} Entry", row_value(row, "Entry"), allowed_link_ids, issues)
        validate_scenario_link(path, f"added scenario {sid} Exit / next", row_value(row, "Exit / next"), allowed_link_ids, issues)
        if is_placeholder(row_value(row, "Why this is not an island")):
            issues.append(f"{path.name}: added scenario {sid}: missing Why this is not an island")
    requirement_rows = table_rows_or_issue(
        path,
        text,
        "Обновления требований",
        issues,
        {"Scenario", "FR/NFR/AC/Test plan", "Change", "Reason"},
    )
    for row in requirement_rows:
        sid = row_value(row, "Scenario")
        if not re.fullmatch(SCENARIO_ID_PATTERN, sid):
            issues.append(f"{path.name}: invalid requirement update scenario {sid!r}")
        elif known_ids and sid not in known_ids and sid not in added_ids:
            issues.append(f"{path.name}: requirement update scenario {sid} is not in baseline/cards or added scenarios")
        for column in ["FR/NFR/AC/Test plan", "Change", "Reason"]:
            if is_placeholder(row_value(row, column)):
                issues.append(f"{path.name}: requirement update {sid}: missing {column}")
    dot_body = section_body(text, "DOT diff")
    if dot_body and "->" not in dot_body:
        issues.append(f"{path.name}: DOT diff has no edges")
    return issues


def check_impacts(docs_product: Path, require_files: bool) -> int:
    docs_product = resolve_product_dir(docs_product)
    baseline_ids, _current_ids, baseline_issues = parse_baseline_ids(docs_product / "current-scenario-baseline.md")
    card_ids, card_issues = check_scenario_cards(docs_product / "scenario-cards.md", set())
    known_ids = baseline_ids | card_ids
    files = increment_files(docs_product, "-impact")
    if not files:
        if require_files:
            print(f"FAIL no impact files in {docs_product / 'increments'}")
            return 1
        print(f"OK   no impact files in {docs_product / 'increments'}")
        return 0
    issues: list[str] = []
    issues.extend(baseline_issues)
    issues.extend(card_issues)
    for path in files:
        issues.extend(check_impact_file(path, known_ids))
    if issues:
        for issue in issues:
            print(f"FAIL {issue}")
        return 1
    print(f"OK   {len(files)} impact files")
    return 0


def check_task_block(text: str, prefix: str, allow_legacy_plan: bool) -> tuple[int, list[str]]:
    """Returns (count_tasks, list of issues)."""
    task_headers = re.findall(rf"^## ({prefix}\d+)\. ", text, re.MULTILINE)
    issues: list[str] = []
    uses_product_artifacts = bool(re.search(r"^- \*\*Product artifacts:\*\*", text, re.MULTILINE))
    require_product_artifacts = uses_product_artifacts or not allow_legacy_plan
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
        if require_product_artifacts and not re.search(
            rf"^- \*\*{re.escape(PRODUCT_ARTIFACTS_FIELD)}:\*\*",
            block,
            re.MULTILINE,
        ):
            issues.append(f"{tid}: missing field {PRODUCT_ARTIFACTS_FIELD}")
    return len(task_headers), issues


def check_plan_file(path: Path, prefix: str, allow_legacy_plan: bool) -> int:
    if not path.exists():
        print(f"FAIL plan file does not exist: {path}")
        return 1
    text = path.read_text(encoding="utf-8")
    count, issues = check_task_block(text, prefix, allow_legacy_plan)
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
    uses_product_artifacts = bool(re.search(r"^- \*\*Product artifacts:\*\*", text, re.MULTILINE))
    if rc == 0:
        if uses_product_artifacts:
            print(f"OK   all {prefix}-tasks have legacy fields + Product artifacts")
        else:
            print(f"OK   all {prefix}-tasks have 9 legacy required fields")
            print("WARN Product artifacts field not found; legacy plan format accepted")
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
    p.add_argument(
        "--phase",
        choices=["scenarios", "baseline", "pre-scan", "impact", "plan", "hardening", "validation", "all"],
        required=True,
    )
    p.add_argument(
        "--allow-legacy-plan",
        action="store_true",
        help="accept T/H plans that predate the Product artifacts field",
    )
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

    if args.phase in ("baseline", "all"):
        rc |= check_baseline(target)

    if args.phase in ("pre-scan", "all"):
        rc |= check_pre_scans(target, require_files=args.phase == "pre-scan")

    if args.phase in ("impact", "all"):
        rc |= check_impacts(target, require_files=args.phase == "impact")

    if args.phase in ("plan", "all"):
        plans_dir = target if any(target.glob("*implementation-plan*.md")) else target / "docs" / "plans"
        if plans_dir.exists():
            implementation_files = sorted(plans_dir.glob("*implementation-plan*.md"))
            if not implementation_files:
                print(f"FAIL no implementation plan files in {plans_dir}")
                rc = 1
            for f in implementation_files:
                rc |= check_plan_file(f, "T", args.allow_legacy_plan)
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
                rc |= check_plan_file(f, "H", args.allow_legacy_plan)
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
