"""Recheck saved outputs; this does not invoke an LLM or grade reasoning."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "review-task-brief"
RUN = Path(__file__).parent / "independent-2026-10-17"
spec = importlib.util.spec_from_file_location("validator", SKILL / "scripts/check_review.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    expected = json.loads((RUN / "expectations.json").read_text())
    protocol = json.loads((RUN / "protocol.json").read_text())
    assert sha(RUN / "expectations.json") == protocol["expectations_sha256"]
    # Ignore macOS Finder metadata accidentally captured in the initial protocol.
    skill_files = ("SKILL.md", "references/criteria.md", "scripts/check_review.py")
    for name in skill_files:
        assert sha(SKILL / name) == protocol["skill_sha256"][name]
    rows = []
    for name, expectation in expected.items():
        folder = RUN / "runs" / name
        source = json.loads((folder / "input.json").read_text())
        review = json.loads((folder / "review.json").read_text())
        manifest = json.loads((folder / "manifest.json").read_text())
        for key in ("input", "review"):
            assert sha(folder / (key + ".json")) == manifest["sha256"][key]
        for key in skill_files:
            assert sha(SKILL / key) == manifest["sha256"][key]
        actual = {c["criterion_id"]: c["status"] for c in review["checks"]}
        actual.update(verdict=review["verdict"], next_action=review["next_action"])
        rows.append(dict(case=name, expected=expectation, actual=actual,
                         matches=actual == expectation,
                         validation_errors=validator.validate(source, review)))
    report = dict(cases=len(rows), matches_original_expectations=sum(r["matches"] for r in rows),
                  structurally_valid=sum(not r["validation_errors"] for r in rows),
                  skill_and_expectations_unchanged=True, rows=rows)
    (RUN / "comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, ensure_ascii=False))
    # The known disagreement is a reported observation, not a hidden test failure.
    return 1 if any(r["validation_errors"] for r in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
