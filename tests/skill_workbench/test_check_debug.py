import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("check_debug", ROOT / "skill-workbench/scripts/check_debug.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DebugReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "output.json").write_text('{}')
        self.report = dict(status="PASS", summary="Checked output", artifacts=["output.json"],
                           decisions=[], limitations=[], checks=[dict(name="schema", status="PASS",
                           detail="Validator exited 0", evidence=["output.json"])])

    def test_valid_report(self):
        self.assertEqual([], module.validate(self.report, self.root))

    def test_missing_evidence_file(self):
        (self.root / "output.json").unlink()
        self.assertTrue(module.validate(self.report, self.root))

    def test_path_escape_and_symlink(self):
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "private.txt"
            target.write_text("private")
            (self.root / "link").symlink_to(target)
            for name in [str(target), "../private.txt", "link"]:
                with self.subTest(name=name):
                    report = copy.deepcopy(self.report)
                    report['artifacts'].append(name)
                    self.assertTrue(module.validate(report, self.root))

    def test_unrun_cannot_pass(self):
        self.report['checks'][0].update(status='NOT_RUN', evidence=[])
        self.assertTrue(module.validate(self.report, self.root))
        self.report['status'] = 'NOT_RUN'
        self.assertEqual([], module.validate(self.report, self.root))

    def test_executed_check_needs_evidence(self):
        self.report['checks'][0]['evidence'] = []
        self.assertTrue(module.validate(self.report, self.root))

    def test_malformed_reports_are_rejected(self):
        for report in [None, [], {}, dict(self.report, status=[]), dict(self.report, checks=[None]),
                       dict(self.report, artifacts=[{}]), dict(self.report, decisions=[{}])]:
            with self.subTest(report=report):
                self.assertTrue(module.validate(report, self.root))

    def test_no_semantic_claim(self):
        self.report['checks'][0]['detail'] = 'An intentionally false assertion can still be well-formed.'
        self.assertEqual([], module.validate(self.report, self.root))


if __name__ == '__main__':
    unittest.main()
