import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("validator", ROOT / "review-task-brief/scripts/check_review.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.source = {"id": "test", "text": "Добавить CSV. В файле есть столбец id.", "complete": True}
        self.review = {
            "task_id": "test", "verdict": "PASS", "next_action": "ACCEPT",
            "checks": [
                {"criterion_id": "R1", "status": "PASS", "evidence": ["Добавить CSV."], "reason": "Задан результат."},
                {"criterion_id": "R2", "status": "PASS", "evidence": ["В файле есть столбец id."], "reason": "Есть проверяемое условие."},
            ],
        }

    def test_accepts_consistent_review(self):
        self.assertEqual([], validator.validate(self.source, self.review))

    def test_rejects_fabricated_quote(self):
        self.review["checks"][0]["evidence"] = ["Несуществующая цитата"]
        self.assertIn("evidence contains a quote absent from input", validator.validate(self.source, self.review))

    def test_rejects_duplicate_criterion(self):
        self.review["checks"][1]["criterion_id"] = "R1"
        self.assertTrue(validator.validate(self.source, self.review))

    def test_rejects_inconsistent_verdict(self):
        self.review["verdict"] = "FAIL"
        self.assertTrue(validator.validate(self.source, self.review))

    def test_rejects_inconsistent_action(self):
        self.review["next_action"] = "REFINE"
        self.assertTrue(validator.validate(self.source, self.review))

    def test_rejects_success_without_input(self):
        self.source["text"] = None
        self.assertTrue(validator.validate(self.source, self.review))

    def test_accepts_missing_input(self):
        self.source.update(text=None, complete=False)
        self.review.update(verdict="UNDETERMINED", next_action="PROVIDE_INPUT")
        for check in self.review["checks"]:
            check.update(status="UNDETERMINED", evidence=[], reason="Текст задачи отсутствует.")
        self.assertEqual([], validator.validate(self.source, self.review))

    def test_rejects_extra_fields(self):
        self.review["approved_for_production"] = True
        self.assertTrue(validator.validate(self.source, self.review))

    def test_does_not_claim_to_check_semantics(self):
        wrong = copy.deepcopy(self.review)
        wrong["checks"][0]["reason"] = "Здесь намеренно неверное смысловое обоснование."
        self.assertEqual([], validator.validate(self.source, wrong))


if __name__ == "__main__":
    unittest.main()
