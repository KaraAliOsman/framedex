"""Seed-shape regression: a leaf without a leaf_id (single-module leafed
position) must fold its closing points into the bay-level annotation row —
a second (bay, None) row collides with the opening row at freeze
('Duplicate annotation target')."""

from decimal import Decimal as D
from types import SimpleNamespace

from documents.service import _seed_workshop_defaults


def _config() -> SimpleNamespace:
    return SimpleNamespace(
        R07=SimpleNamespace(width_trigger_mm=D("800"), required_bottom_drains=3),
        R08=SimpleNamespace(max_spacing_mm=D("700")),
    )


def _computation(openings, leaves) -> SimpleNamespace:
    return SimpleNamespace(openings=openings, leaves=leaves)


def test_leaf_without_identity_folds_closing_points_into_bay_row() -> None:
    computation = _computation(
        [SimpleNamespace(bay_id="B1", width_mm=D("1200"))],
        [SimpleNamespace(
            bay_id="B1",
            leaf_id=None,
            finished_width_mm=D("1100"),
            finished_height_mm=D("1200"),
        )],
    )
    output = _seed_workshop_defaults(
        [(None, computation, {})], [], _config(),
    )
    assert len(output) == 1
    row = output[0]
    assert (row["bay_id"], row["leaf_id"]) == ("B1", None)
    closing = row["closing_points_perimeter_mm"]
    assert isinstance(closing, list) and len(closing) >= 2
    perimeter = (D("1100") + D("1200")) * 2
    assert D(str(closing[-1])) < perimeter


def test_leaf_with_identity_keeps_its_own_annotation_row() -> None:
    computation = _computation(
        [SimpleNamespace(bay_id="B1", width_mm=D("1200"))],
        [SimpleNamespace(
            bay_id="B1",
            leaf_id="L1",
            finished_width_mm=D("1100"),
            finished_height_mm=D("1200"),
        )],
    )
    output = _seed_workshop_defaults(
        [(None, computation, {})], [], _config(),
    )
    assert {(row["bay_id"], row["leaf_id"]) for row in output} == {
        ("B1", None),
        ("B1", "L1"),
    }


def test_assembly_leaf_scoped_row_keeps_module_prefix() -> None:
    computation = _computation(
        [SimpleNamespace(bay_id="B1", width_mm=D("1200"))],
        [SimpleNamespace(
            bay_id="B1",
            leaf_id="L1",
            finished_width_mm=D("1100"),
            finished_height_mm=D("1200"),
        )],
    )
    output = _seed_workshop_defaults(
        [("M1", computation, {})], [], _config(),
    )
    assert (output[1]["bay_id"], output[1]["leaf_id"]) == ("M1|B1", "M1|L1")


def test_existing_bay_row_blocks_leafless_fold() -> None:
    computation = _computation(
        [SimpleNamespace(bay_id="B1", width_mm=D("1200"))],
        [SimpleNamespace(
            bay_id="B1",
            leaf_id=None,
            finished_width_mm=D("1100"),
            finished_height_mm=D("1200"),
        )],
    )
    existing = [{
        "bay_id": "B1",
        "leaf_id": None,
        "bottom_drain_holes_mm": ["300"],
        "closing_points_perimeter_mm": None,
        "continuous_width_mm": "1200",
        "finish_class": "WHITE",
        "has_coupler": False,
    }]
    output = _seed_workshop_defaults(
        [(None, computation, {})], existing, _config(),
    )
    # No second (B1, None) row may be produced — the operator's row governs.
    assert output == existing
