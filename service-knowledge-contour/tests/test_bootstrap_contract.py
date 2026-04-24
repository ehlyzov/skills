import os
import shutil
import subprocess
import tempfile
import unittest
import json
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


class BootstrapContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        shutil.copytree(PACKAGE_ROOT / "bin", self.root / "bin")
        subprocess.run(
            ["bash", str(self.root / "bin" / "bootstrap.sh"), str(self.root)],
            check=True,
            cwd=self.root,
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_bootstrap_keeps_english_scaffold_and_stronger_agents_contract(self) -> None:
        agents = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("## Non-negotiables", agents)
        self.assertIn("Read the relevant files before editing.", agents)
        self.assertIn("Use `docs/service/VERIFY.md` as the canonical verification contract.", agents)
        self.assertIn("Do not duplicate architecture or verification truth in startup docs.", agents)

        claude = (self.root / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("Use `AGENTS.md` as the startup contract.", claude)

        service_map = (self.root / "docs/service/SERVICE_MAP.md").read_text(encoding="utf-8")
        verify = (self.root / "docs/service/VERIFY.md").read_text(encoding="utf-8")
        hotspots = (self.root / "docs/service/generated/hotspots.md").read_text(encoding="utf-8")
        self.assertIn("## Service purpose", service_map)
        self.assertIn("## Fastest local setup path", verify)
        self.assertIn("# Generated hotspots", hotspots)

    def test_russian_manual_edits_do_not_break_refresh_audit_or_prune(self) -> None:
        (self.root / "docs/service/SERVICE_MAP.md").write_text(
            "\n".join(
                [
                    "# SERVICE_MAP",
                    "",
                    "## Назначение сервиса",
                    "Короткое описание сервиса на русском языке.",
                    "",
                    "## Точки входа",
                    "- `main.py`",
                    "",
                    "## Модули верхнего уровня",
                    "- `service`",
                    "",
                    "## Границы и инварианты",
                    "- Не изменять публичный контракт без обновления проверки.",
                    "",
                    "## Критические интеграции",
                    "- Внешний API.",
                    "",
                    "## Опасные зоны",
                    "- Миграции и устаревшие пути.",
                    "",
                    "## Generated overlays",
                    "- `docs/service/generated/change-surface.json`",
                    "- `docs/service/generated/hotspots.md`",
                    "",
                    "## Триггеры пересмотра",
                    "Обновлять документ при изменении топологии, точек входа или границ.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (self.root / "docs/service/VERIFY.md").write_text(
            "\n".join(
                [
                    "# VERIFY",
                    "",
                    "## Быстрый локальный запуск",
                    "- Add after repository inspection or record an unresolved fact in docs/service/knowledge-gaps.yaml.",
                    "- Add after repository inspection or record an unresolved fact in docs/service/knowledge-gaps.yaml.",
                    "",
                    "## Узкая проверка",
                    "- Add after repository inspection or record an unresolved fact in docs/service/knowledge-gaps.yaml.",
                    "",
                    "## Полная локальная проверка",
                    "- Add after repository inspection or record an unresolved fact in docs/service/knowledge-gaps.yaml.",
                    "",
                    "## Проверки только в CI",
                    "Перечислить проверки, которые нельзя воспроизвести локально.",
                    "",
                    "## Дополнительные проверки по риску",
                    "Добавить проверки для hotspot-изменений и миграций.",
                    "",
                    "## Обязательные доказательства изменения",
                    "- changed surface;",
                    "- commands run;",
                    "- observed results;",
                    "- what was not verified locally;",
                    "- risk notes.",
                    "",
                    "## Что нельзя проверить локально",
                    "Зафиксировать внешние зависимости и недоступные окружения.",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        subprocess.run(
            ["bash", str(self.root / "bin" / "refresh_contour.sh"), str(self.root)],
            check=True,
            cwd=self.root,
        )
        subprocess.run(
            ["bash", str(self.root / "bin" / "audit_contour.sh"), str(self.root)],
            check=True,
            cwd=self.root,
        )
        prune = subprocess.run(
            ["bash", str(self.root / "bin" / "prune_contour.sh"), str(self.root)],
            check=True,
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertIn('"prune_candidates"', prune.stdout)

    def test_promote_learning_classifies_russian_input(self) -> None:
        cases = [
            ("Нужно описать точку входа, границы сервиса и интеграции.", "structural"),
            ("Нужно зафиксировать проверки, тесты и то, что не проверяется локально.", "verification"),
            ("Нужен ранбук восстановления после инцидента и процедура перезапуска.", "operational"),
            ("Нужно записать решение, альтернативы и компромисс.", "decision"),
            ("Нужно описать термин и его определение.", "terminology"),
            ("Сборка падает только в CI, нужно записать команду и результат проверки.", "verification"),
            ("Роут API изменил контракт, зависимость и конфиг воркера.", "structural"),
            ("После алерта нужен регламент отката и восстановления.", "operational"),
            ("Договорились выбрать этот подход из двух вариантов и записать причину.", "decision"),
            ("Неясно, что означает это понятие, нужна расшифровка в глоссарии.", "terminology"),
            ("Решили добавить проверку в CI и зафиксировать команду запуска.", "verification"),
        ]
        for text, expected in cases:
            result = subprocess.run(
                ["bash", str(self.root / "bin" / "promote_learning.sh"), "--input", text],
                check=True,
                cwd=self.root,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(expected, payload["classification"])

        forced = subprocess.run(
            [
                "bash",
                str(self.root / "bin" / "promote_learning.sh"),
                "--input",
                "Это русскоязычная заметка.",
                "--type",
                "verification",
            ],
            check=True,
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertEqual("verification", json.loads(forced.stdout)["classification"])

    def test_startup_only_updates_startup_files_without_touching_canon(self) -> None:
        service_map = self.root / "docs/service/SERVICE_MAP.md"
        verify = self.root / "docs/service/VERIFY.md"
        service_map.write_text("custom service map\n", encoding="utf-8")
        verify.write_text("custom verify\n", encoding="utf-8")
        (self.root / "AGENTS.md").write_text("old agents\n", encoding="utf-8")
        (self.root / "CLAUDE.md").write_text("old claude\n", encoding="utf-8")

        env = os.environ.copy()
        env["FORCE"] = "1"
        subprocess.run(
            ["bash", str(self.root / "bin" / "bootstrap.sh"), "--startup-only", str(self.root)],
            check=True,
            cwd=self.root,
            env=env,
        )

        self.assertIn("Read the relevant files before editing.", (self.root / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertIn("Use `AGENTS.md` as the startup contract.", (self.root / "CLAUDE.md").read_text(encoding="utf-8"))
        self.assertEqual("custom service map\n", service_map.read_text(encoding="utf-8"))
        self.assertEqual("custom verify\n", verify.read_text(encoding="utf-8"))

    def test_refresh_includes_working_tree_changes(self) -> None:
        subprocess.run(["git", "init"], check=True, cwd=self.root, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True, cwd=self.root)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True, cwd=self.root)
        (self.root / "package.json").write_text('{"scripts":{"test":"node test.js"}}\n', encoding="utf-8")
        subprocess.run(["git", "add", "."], check=True, cwd=self.root)
        subprocess.run(["git", "commit", "-m", "baseline"], check=True, cwd=self.root, capture_output=True, text=True)

        (self.root / "package.json").write_text('{"scripts":{"test":"node test.js","lint":"eslint ."}}\n', encoding="utf-8")
        subprocess.run(
            ["bash", str(self.root / "bin" / "refresh_contour.sh"), str(self.root), "--base", "HEAD"],
            check=True,
            cwd=self.root,
        )

        payload = json.loads((self.root / "docs/service/generated/change-surface.json").read_text(encoding="utf-8"))
        self.assertIn("package.json", payload["changed_files"])
        self.assertEqual(["docs/service/VERIFY.md"], payload["triggers"][0]["update"])

    def test_audit_warns_when_triggered_canon_update_is_missing(self) -> None:
        subprocess.run(["git", "init"], check=True, cwd=self.root, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True, cwd=self.root)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True, cwd=self.root)
        (self.root / "package.json").write_text('{"scripts":{"test":"node test.js"}}\n', encoding="utf-8")
        subprocess.run(["git", "add", "."], check=True, cwd=self.root)
        subprocess.run(["git", "commit", "-m", "baseline"], check=True, cwd=self.root, capture_output=True, text=True)

        (self.root / "package.json").write_text('{"scripts":{"test":"node test.js","lint":"eslint ."}}\n', encoding="utf-8")
        subprocess.run(
            ["bash", str(self.root / "bin" / "refresh_contour.sh"), str(self.root), "--base", "HEAD"],
            check=True,
            cwd=self.root,
        )
        subprocess.run(
            ["bash", str(self.root / "bin" / "audit_contour.sh"), str(self.root)],
            check=True,
            cwd=self.root,
        )

        report = json.loads((self.root / "docs/service/generated/health-report.json").read_text(encoding="utf-8"))
        self.assertIn(
            "contour trigger fired but docs/service/VERIFY.md was not changed",
            report["warnings"],
        )


if __name__ == "__main__":
    unittest.main()
