"""Regression tests for canonical checker CLI target semantics."""

from contextlib import redirect_stdout
import importlib
from io import StringIO
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, call, patch


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))
check_dod = importlib.import_module("check_dod")


class CheckDodCliTests(unittest.TestCase):
    def invoke(self, target: str) -> tuple[list[object], str]:
        pipeline = Mock()
        output = StringIO()
        with (
            patch.object(check_dod, "configure_output"),
            patch.object(check_dod, "check_constitutional_guards") as guards,
            patch.object(check_dod, "check_linters") as linters,
            patch.object(check_dod, "check_typechecks") as typechecks,
            patch.object(check_dod, "check_live_gates") as live_gates,
            patch.object(check_dod, "check_build") as build,
            redirect_stdout(output),
        ):
            pipeline.attach_mock(guards, "guards")
            pipeline.attach_mock(linters, "linters")
            pipeline.attach_mock(typechecks, "typechecks")
            pipeline.attach_mock(live_gates, "live_gates")
            pipeline.attach_mock(build, "build")
            check_dod.main([target])
        return pipeline.mock_calls, output.getvalue()

    def test_gauntlet_is_an_explicit_alias_for_the_full_all_pipeline(self):
        all_calls, all_output = self.invoke("all")
        alias_calls, alias_output = self.invoke("gauntlet")

        expected = [
            call.guards(),
            call.linters(),
            call.typechecks(),
            call.live_gates(tests=True, database=True),
            call.build(),
        ]
        self.assertEqual(all_calls, expected)
        self.assertEqual(alias_calls, expected)
        self.assertIn("canonical repository fail-closed checker", all_output)
        self.assertIn("alias for 'all'", alias_output)
        self.assertIn("Do not run both", alias_output)
        self.assertIn("target 'all' completed", alias_output)
        self.assertNotIn("SHOT-09", all_output + alias_output)

    def test_make_gauntlet_delegates_to_the_canonical_dod_target(self):
        makefile = (SCRIPTS_DIR.parent / "Makefile").read_text(encoding="utf-8")

        self.assertIn("dod:\n\tpython scripts/check_dod.py all", makefile)
        self.assertIn("gauntlet:\n\t@echo", makefile)
        self.assertIn("\n\t$(MAKE) dod", makefile)
        self.assertNotIn("python scripts/check_dod.py gauntlet", makefile)

    def test_database_target_uses_repository_wide_runtime_labels(self):
        calls, output = self.invoke("database")

        self.assertEqual(calls, [call.live_gates(tests=False, database=True)])
        self.assertIn("Repository live database gate completed", output)
        self.assertNotIn("SHOT-09", output)


if __name__ == "__main__":
    unittest.main()
