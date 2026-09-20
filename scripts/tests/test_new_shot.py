"""Exercise the scaffold CLI in an isolated repository layout."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class NewShotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dekopen-scaffold-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "scripts").mkdir()
        (self.root / "docs/PRD").mkdir(parents=True)
        self.script = self.root / "scripts/new_shot.py"
        source = Path(__file__).resolve().parents[1] / "new_shot.py"
        shutil.copyfile(source, self.script)
        self.roadmap = self.root / "docs/PRD/PLAN_SHOTS.md"
        self.roadmap.write_text(
            "Mention **SHOT-24** outside a table.\n"
            "| **SHOT-24** | 4 | PRD-16 | Retazos QR | Reserva → consumo |\n",
            encoding="utf-8",
        )

    def invoke(self, *args):
        return subprocess.run(
            [sys.executable, str(self.script), *args],
            cwd=self.root,
            env={**os.environ, "PYTHONIOENCODING": "ascii"},
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def test_success_uses_roadmap_and_does_not_overwrite_existing_plan(self):
        result = self.invoke("shot-24")
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = self.root / "docs/plans/PLAN_SHOT-24.md"
        text = plan.read_text(encoding="utf-8")
        self.assertIn("**Source PRD:** PRD-16", text)
        self.assertIn("**Acceptance gate:** Reserva → consumo", text)
        self.assertIn("Constitution Rule 19", text)
        self.assertNotIn("APROBADO", text)
        plan.write_text("Owner decision must survive.\n", encoding="utf-8")
        self.assertEqual(self.invoke("SHOT-24").returncode, 0)
        self.assertEqual(plan.read_text(encoding="utf-8"), "Owner decision must survive.\n")

    def test_invalid_ids_and_argument_counts_never_create_plans(self):
        for args in [
            (),
            ("SHOT-00",),
            ("SHOT-25",),
            ("SHOT-99",),
            ("SHOT-1",),
            ("BAD",),
            ("SHOT-24", "extra"),
        ]:
            with self.subTest(args=args):
                self.assertNotEqual(self.invoke(*args).returncode, 0)
                self.assertFalse((self.root / "docs/plans").exists())

    def test_missing_or_incomplete_authority_never_creates_a_plan(self):
        for content in ["", "Only mention **SHOT-24**", "| **SHOT-24** | 4 | | QR | Gate |"]:
            with self.subTest(content=content):
                self.roadmap.write_text(content, encoding="utf-8")
                self.assertNotEqual(self.invoke("SHOT-24").returncode, 0)
                self.assertFalse((self.root / "docs/plans").exists())
        self.roadmap.unlink()
        self.assertNotEqual(self.invoke("SHOT-24").returncode, 0)
        self.assertFalse((self.root / "docs/plans").exists())


if __name__ == "__main__":
    unittest.main()
