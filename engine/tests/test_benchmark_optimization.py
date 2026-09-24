"""§13 benchmark stability — the evidence corpus must keep beating the
pinned legacy algorithms. A regression in the industrial tiers flips one of
these cells and fails here, so the PR benchmark stays honest over time."""

import re

from engine.scripts.benchmark_optimization import run_benchmark


def _row(report: str, case: str) -> str:
    for line in report.splitlines():
        if line.startswith(f"| {case}"):
            return line
    raise AssertionError(f"case row missing: {case}")


def _cells(row: str) -> list[str]:
    return [cell.strip() for cell in row.strip().strip("|").split("|")]


def test_benchmark_report_covers_the_mandate_corpus() -> None:
    report = run_benchmark()
    for case in (
        "tiny-pieces-40",
        "almost-stock",
        "bfd-fragmentation",
        "mixed-colors",
        "material-mix",
        "angled-saw-limit†",
        "reinforcement-vs-pvc",
        "variant-lengths",
        "remnant-pool",
        "large-batch-200",
        "oversize-honest†",
        "shared-commercial-sku",
        "panel-grid-24",
        "awkward-mix-15",
        "rotation-critical",
        "kerf-correctness†",
        "alternate-split-win",
        "remnant-sheets",
        "large-batch-100",
    ):
        _row(report, case)


def test_deep_tier_and_variants_stay_better_than_legacy() -> None:
    report = run_benchmark()
    # The BFD counterexample stays at the proven optimum (3 bars, zero waste).
    cells = _cells(_row(report, "bfd-fragmentation"))
    assert cells[1] == "4" and cells[2].startswith("3")
    # Variant stock keeps halving the purchase (6 vs 12).
    cells = _cells(_row(report, "variant-lengths"))
    assert cells[1] == "12" and cells[2].startswith("6")
    # The remnant pool keeps displacing every new-bar purchase.
    cells = _cells(_row(report, "remnant-pool"))
    assert "(0 new)" in cells[2] and cells[6] == "3"
    # The alternate guillotine split keeps saving the second sheet.
    cells = _cells(_row(report, "alternate-split-win"))
    assert cells[1] == "2" and cells[2] == "1"
    # Remnant sheets keep being consumed before new stock.
    cells = _cells(_row(report, "remnant-sheets"))
    assert cells[6] == "2"


def test_benchmark_totals_stay_at_or_above_evidence_floor() -> None:
    report = run_benchmark()
    total = _cells(_row(report, "**TOTAL**"))
    # Bar waste reduction never drops below the recorded 46.3% improvement.
    match = re.search(r"(\d+\.\d)%", total[5])
    assert match is not None and float(match.group(1)) >= 46.0
