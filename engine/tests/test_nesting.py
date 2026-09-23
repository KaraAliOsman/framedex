from decimal import Decimal

import pytest

from dekopen_engine.nesting import (
    NestPiece,
    PieceLargerThanUsableSheet,
    SheetRule,
    nest_rects,
)


def _piece(pid: str, w: str, h: str, **kwargs) -> NestPiece:
    return NestPiece(
        piece_id=pid, workshop_sku="DVH4",
        width_mm=Decimal(w), height_mm=Decimal(h), **kwargs,
    )


RULE = SheetRule(
    workshop_sku="DVH4", purchasing_sku="DVH-4-12-4",
    sheet_width_mm=Decimal("2000"), sheet_height_mm=Decimal("1600"),
    edge_trim_mm=Decimal("5"),
)


def test_nests_pieces_on_one_sheet_with_exact_yield():
    pieces = [_piece("a", "810", "630"), _piece("b", "810", "630", unit_index=2)]
    result = nest_rects(pieces, RULE)
    assert len(result.layouts) == 1
    assert result.unplaced == []
    layout = result.layouts[0]
    assert layout.sheet_index == 1
    assert layout.productive_area_mm2 == Decimal("810") * Decimal("630") * 2
    expected = (
        Decimal("810") * Decimal("630") * 2
        / (Decimal("2000") * Decimal("1600")) * Decimal("100")
    ).quantize(Decimal("0.0001"))
    assert layout.yield_pct == expected
    assert result.purchase_list[0].qty_sheets == 1
    for placement in layout.placements:
        assert placement.x_mm >= Decimal("5")
        assert placement.y_mm >= Decimal("5")
        assert placement.x_mm + placement.width_mm <= Decimal("2000") - Decimal("5")
        assert placement.y_mm + placement.height_mm <= Decimal("1600") - Decimal("5")


def test_placements_never_overlap():
    pieces = [_piece(f"p{i}", "900", "700", unit_index=i) for i in range(1, 5)]
    result = nest_rects(pieces, RULE)
    rects = [
        (p.x_mm, p.y_mm, p.x_mm + p.width_mm, p.y_mm + p.height_mm)
        for layout in result.layouts for p in layout.placements
    ]
    for i, a in enumerate(rects):
        for b in rects[i + 1:]:
            overlap = not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])
            assert not overlap, f"placements overlap: {a} vs {b}"


def test_opens_new_sheet_when_first_is_full():
    pieces = [_piece("a", "1900", "1500"), _piece("b", "1900", "1500", unit_index=2)]
    result = nest_rects(pieces, RULE)
    assert len(result.layouts) == 2
    assert result.purchase_list[0].qty_sheets == 2


def test_rotates_when_rotation_is_the_only_fit():
    rule = SheetRule(
        workshop_sku="DVH4", purchasing_sku="X",
        sheet_width_mm=Decimal("1000"), sheet_height_mm=Decimal("2000"),
    )
    result = nest_rects([_piece("r", "1900", "500")], rule)
    assert result.unplaced == []
    assert result.layouts[0].placements[0].rotated is True


def test_no_rotation_leaves_piece_unplaced():
    rule = SheetRule(
        workshop_sku="DVH4", purchasing_sku="X",
        sheet_width_mm=Decimal("1000"), sheet_height_mm=Decimal("2000"),
    )
    piece = _piece("r", "1900", "500", allow_rotation=False)
    result = nest_rects([piece], rule)
    assert result.unplaced == [piece]
    assert result.layouts == []


def test_oversized_piece_goes_to_unplaced():
    piece = _piece("big", "3000", "2000")
    result = nest_rects([piece], RULE)
    assert result.unplaced == [piece]


def test_edge_trim_reduces_usable_area():
    rule = SheetRule(
        workshop_sku="DVH4", purchasing_sku="X",
        sheet_width_mm=Decimal("1000"), sheet_height_mm=Decimal("1000"),
        edge_trim_mm=Decimal("600"),
    )
    with pytest.raises(PieceLargerThanUsableSheet):
        nest_rects([_piece("a", "100", "100")], rule)


def test_duplicate_identity_is_rejected():
    pieces = [_piece("dup", "100", "100"), _piece("dup", "200", "200")]
    with pytest.raises(ValueError, match="Duplicate"):
        nest_rects(pieces, RULE)


def test_result_is_deterministic():
    pieces = [
        _piece("a", "810", "630"), _piece("b", "900", "700"),
        _piece("c", "400", "300"), _piece("d", "810", "630", unit_index=2),
    ]
    first = nest_rects(pieces, RULE)
    second = nest_rects(list(reversed(pieces)), RULE)
    assert first.model_dump_json() == second.model_dump_json()
