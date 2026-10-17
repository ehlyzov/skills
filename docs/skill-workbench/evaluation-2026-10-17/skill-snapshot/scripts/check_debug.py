#!/usr/bin/env python3
"""Validate debug report structure and local references, never reasoning quality."""
import json
import sys
from pathlib import Path

STATUSES = ("PASS", "FAIL", "BLOCKED", "NOT_RUN")


def text(value):
    return isinstance(value, str) and bool(value.strip())


def strings(value):
    return isinstance(value, list) and all(text(x) for x in value)


def validate(report, root):
    root = Path(root).resolve()
    errors = []
    fields = {"status", "summary", "artifacts", "decisions", "checks", "limitations"}
    if not isinstance(report, dict) or set(report) != fields:
        return ["report must contain exactly: " + ", ".join(sorted(fields))]
    if report["status"] not in STATUSES:
        errors.append("invalid run status")
    if not text(report["summary"]):
        errors.append("summary must be nonempty")
    if not strings(report["limitations"]):
        errors.append("limitations must be a list of nonempty strings")
    artifacts = report["artifacts"]
    if not strings(artifacts):
        return errors + ["artifacts must be a list of nonempty relative paths"]
    if len(set(artifacts)) != len(artifacts):
        errors.append("duplicate artifact path")
    for name in artifacts:
        path = Path(name)
        resolved = (root / path).resolve()
        if path.is_absolute() or not resolved.is_relative_to(root) or not resolved.is_file():
            errors.append("artifact must be an existing file within the run directory: " + name)

    def evidence(value, where, required=False):
        if not strings(value) or any(x not in artifacts for x in value):
            errors.append(where + ": evidence must reference listed artifacts")
        elif required and not value:
            errors.append(where + ": executed check requires evidence")

    if not isinstance(report["decisions"], list):
        errors.append("decisions must be a list")
    else:
        for item in report["decisions"]:
            if not isinstance(item, dict) or set(item) != {"decision", "basis", "evidence", "assumptions"}:
                errors.append("invalid decision fields")
                continue
            if not text(item["decision"]) or not text(item["basis"]) or not strings(item["assumptions"]):
                errors.append("decision needs decision, basis, and a string list of assumptions")
            evidence(item["evidence"], "decision")
    if not isinstance(report["checks"], list):
        return errors + ["checks must be a list"]
    statuses = []
    for item in report["checks"]:
        if not isinstance(item, dict) or set(item) != {"name", "status", "detail", "evidence"}:
            errors.append("invalid check fields")
            continue
        status = item["status"]
        statuses.append(status)
        if status not in STATUSES or not text(item["name"]) or not text(item["detail"]):
            errors.append("check needs valid status, name, and detail")
        evidence(item["evidence"], "check", required=status in ("PASS", "FAIL"))
    if report["status"] == "PASS" and (not statuses or any(s != "PASS" for s in statuses)):
        errors.append("overall PASS requires at least one check and all required checks PASS")
    return errors


def main():
    if len(sys.argv) != 2:
        print("Usage: check_debug.py RUN/debug.json", file=sys.stderr)
        return 1
    path = Path(sys.argv[1])
    try:
        errors = validate(json.loads(path.read_text()), path.parent)
    except (OSError, ValueError, RuntimeError) as exc:
        errors = [str(exc)]
    print(json.dumps({"valid": not errors, "errors": errors,
                      "scope": "report structure, status consistency, local references; not semantics"},
                     ensure_ascii=False))
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
