#!/usr/bin/env python3
"""Validate structure, exact quotes and verdict consistency, not semantics."""
import hashlib
import json
import sys
from pathlib import Path


def validate(source, review):
    errors = []
    if not isinstance(source, dict) or set(source) != {"id", "text", "complete"}:
        return ["input must contain exactly id, text, complete"]
    if not isinstance(source["id"], str) or not source["id"].strip():
        errors.append("input.id must be a nonempty string")
    if source["text"] is not None and not isinstance(source["text"], str):
        errors.append("input.text must be a string or null")
    if type(source["complete"]) is not bool:
        errors.append("input.complete must be boolean")
    if errors:
        return errors
    if not isinstance(review, dict) or set(review) != {"task_id", "verdict", "checks", "next_action"}:
        return ["review must contain exactly task_id, verdict, checks, next_action"]
    if review["task_id"] != source["id"]:
        errors.append("task_id does not match input.id")
    checks = review["checks"]
    if not isinstance(checks, list) or len(checks) != 2:
        return errors + ["checks must contain exactly two entries"]
    ids, statuses = [], []
    for check in checks:
        if not isinstance(check, dict) or set(check) != {"criterion_id", "status", "evidence", "reason"}:
            errors.append("invalid check fields")
            continue
        ids.append(check["criterion_id"])
        status = check["status"]
        statuses.append(status)
        if status not in ("PASS", "FAIL", "UNDETERMINED"):
            errors.append("invalid status")
        if not isinstance(check["reason"], str) or not check["reason"].strip():
            errors.append("reason must be nonempty")
        quotes = check["evidence"]
        if not isinstance(quotes, list) or any(not isinstance(q, str) or not q.strip() for q in quotes):
            errors.append("evidence must be a list of nonempty strings")
        else:
            if any(q not in (source["text"] or "") for q in quotes):
                errors.append("evidence contains a quote absent from input")
            if status == "PASS" and not quotes:
                errors.append("PASS requires evidence")
        if not source["text"] or not source["text"].strip():
            if status != "UNDETERMINED":
                errors.append("missing text requires UNDETERMINED")
        if source["complete"] is False and status == "FAIL":
            errors.append("this policy does not allow FAIL for incomplete input")
    if sorted(ids, key=str) != ["R1", "R2"]:
        errors.append("criterion ids must be R1 and R2, exactly once")
    expected = "FAIL" if "FAIL" in statuses else "UNDETERMINED" if "UNDETERMINED" in statuses else "PASS"
    if review["verdict"] != expected:
        errors.append("verdict does not match checks")
    if review["next_action"] != {"PASS": "ACCEPT", "FAIL": "REFINE", "UNDETERMINED": "PROVIDE_INPUT"}[expected]:
        errors.append("next_action does not match verdict")
    return errors


def main():
    if len(sys.argv) != 3:
        print("Usage: check_review.py INPUT.json REVIEW.json", file=sys.stderr)
        return 2
    input_path, output_path = map(Path, sys.argv[1:])
    try:
        input_bytes, output_bytes = input_path.read_bytes(), output_path.read_bytes()
        errors = validate(json.loads(input_bytes), json.loads(output_bytes))
    except (OSError, ValueError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False))
        return 2
    result = {"valid": not errors, "errors": errors, "scope": "structure, exact quotes, consistency; semantics not verified"}
    skill_root = Path(__file__).resolve().parents[1]
    files = {"input": input_bytes, "review": output_bytes}
    for relative in ("SKILL.md", "references/criteria.md", "scripts/check_review.py"):
        files[relative] = (skill_root / relative).read_bytes()
    manifest = {"sha256": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}, "model": "not recorded by validator"}
    for name, value in (("validation.json", result), ("manifest.json", manifest)):
        destination = output_path.parent / name
        if destination.resolve() in (input_path.resolve(), output_path.resolve()):
            print("Artifact path collides with input/output", file=sys.stderr)
            return 2
        destination.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
