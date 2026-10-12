"""Positive/negative source-detector contracts, also run by make lint."""
from __future__ import annotations

import unittest

from check_guards import design_violations


class DesignGuardTests(unittest.TestCase):
    def test_every_style_guard_rejects_an_offending_fragment(self) -> None:
        fragments = {
            "inline-color": ".x {color: #123456}",
            "gradient": ".x {background: linear-gradient(red,blue)}",
            "blur": ".x {filter: blur(2px)}",
            "heavy-weight": ".x {font-weight: 700}",
            "literal-font-size": ".x {font-size: 9px}",
            "literal-layer": ".x {z-index: 999}",
            "radius-over-4": ".x {border-radius: .5rem}",
            "shadow-outside-scale": ".x {box-shadow: 0 1px 6px black}",
            "motion-over-280": ".x {transition: opacity .3s}",
            "display-tofixed": "<span>{price.toFixed(2)}</span>",
            "native-pattern": '<input pattern="[0-9]+"/>',
            "unvalidated-form": '<form onSubmit={save}><input /></form>',
            "raw-enum-render": "<span>{project.status}</span>",
            "emoji-copy": '<p>Listo \U0001f600</p>',
            "exclamation-copy": '<p>¡Listo!</p>',
            "english-copy": '<button>Save</button>',
        }
        for rule, source in fragments.items():
            with self.subTest(rule=rule):
                self.assertTrue(any(f"|{rule}|" in key for key in design_violations("sample.tsx", source)))

    def test_canonical_styles_and_spanish_domain_copy_pass(self) -> None:
        source = '.x {color: var(--text-primary); border-radius: var(--r-1); box-shadow: var(--e2); transition: opacity var(--t-state); font-size: var(--type-body); z-index: var(--z-dialog)}<button>Guardar</button><span>{domainLabel(project.status)}</span>'
        self.assertEqual(design_violations("sample.tsx", source), {})

    def test_duplicating_a_baselined_fragment_is_a_new_violation(self) -> None:
        source = '.x {border-radius: 8px}'
        baseline = design_violations("sample.css", source)
        repeated = design_violations("sample.css", source + source)
        self.assertTrue(repeated - baseline)


def run_detector_tests() -> None:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(DesignGuardTests)
    result = unittest.TestResult()
    suite.run(result)
    if not result.wasSuccessful():
        raise AssertionError(result.errors + result.failures)


if __name__ == "__main__":
    unittest.main()
