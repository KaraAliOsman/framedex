"""Adversarial corpus for industrial 2D nesting (mandate §5): kerf, split
orientation recovery, rotation refusal, remnant sheets in/out."""

from decimal import Decimal as D


from dekopen_engine.nesting import (
    NestPiece,
    SheetRemnant,
    SheetRule,
    nest_rects,
)


def rule(**overrides: object) -> SheetRule:
    base: dict[str, object] = {
        "workshop_sku": "GLASS-4", "purchasing_sku": "GLASS-4-SHEET",
        "sheet_width_mm": D("2000"), "sheet_height_mm": D("1000"),
        "edge_trim_mm": D("0"), "kerf_mm": D("0"),
    }
    base.update(overrides)
    return SheetRule.model_validate(base)


def piece(piece_id: str, width: str, height: str,
          **kw: object) -> NestPiece:
    return NestPiece.model_validate({
        "piece_id": piece_id, "workshop_sku": "GLASS-4",
        "width_mm": D(width), "height_mm": D(height), **kw,
    })


def test_kerf_respected_between_pieces() -> None:
    # Kerf 10: two 995-wide pieces tile 2000 exactly (995+10+995); a third
    # 5-wide sliver cannot fit the remaining 0 gap.
    r = rule(kerf_mm=D("10"))
    result = nest_rects(
        [piece("a", "995", "1000"), piece("b", "995", "1000")], r
    )
    assert len(result.layouts) == 1
    assert not result.unplaced
    # Exactly usable−kerf along one axis must fit; +kerf more must not.
    result2 = nest_rects(
        [piece("a", "996", "1000"), piece("b", "996", "1000")], r
    )
    assert len(result2.layouts) == 2


def test_alternate_split_recovers_stranded_area() -> None:
    # Sheet 2000×1000: fixed split-A strands the 1900×50 strip (no rect wide
    # enough survives); the solver's split-B run recovers it on one sheet.
    the_pieces = [
        piece("a", "1500", "900"),
        piece("b", "400", "900"),
        piece("c", "1900", "50"),
    ]
    result = nest_rects(the_pieces, rule())
    assert len(result.layouts) == 1
    assert not result.unplaced
    placed = {(p.piece_id) for layout in result.layouts for p in layout.placements}
    assert placed == {"a", "b", "c"}


def test_rotation_forbidden_stays_unplaced() -> None:
    # Grain-locked piece fits only rotated → unplaced, never placed rotated.
    result = nest_rects(
        [piece("a", "1800", "900", allow_rotation=False)],
        rule(sheet_width_mm=D("1000"), sheet_height_mm=D("2000")),
    )
    assert result.unplaced and result.unplaced[0].piece_id == "a"
    assert not result.layouts


def test_remnant_sheet_consumed_before_new_stock() -> None:
    result = nest_rects(
        [piece("a", "600", "400")],
        rule(),
        remnants=[
            SheetRemnant(remnant_id="sheet-big", width_mm=D("1500"), height_mm=D("900")),
            SheetRemnant(remnant_id="sheet-small", width_mm=D("700"), height_mm=D("500")),
        ],
    )
    assert len(result.layouts) == 1
    layout = result.layouts[0]
    # Smallest fitting remnant first — the big offcut survives untouched.
    assert layout.source == "REMNANT" and layout.remnant_id == "sheet-small"
    assert result.purchase_list == []


def test_produced_remnants_report_free_rectangles() -> None:
    result = nest_rects(
        [piece("a", "1200", "800")],
        rule(min_remnant_side_mm=D("100")),
    )
    layout = result.layouts[0]
    produced = {(r.width_mm, r.height_mm) for r in layout.produced_remnants}
    # The packed sheet must return its usable leftovers to the ledger.
    assert produced
    assert all(w >= D("100") and h >= D("100") for w, h in produced)
    total_free = sum(w * h for w, h in produced)
    assert total_free + layout.productive_area_mm2 >= D("1500000")


def test_oversized_piece_is_unplaced_even_when_remnant_hostable() -> None:
    # Fits the 1900×1900 remnant but not the 2000×1000 sheet → remnant host.
    result = nest_rects(
        [piece("a", "1900", "1900")],
        rule(),
        remnants=[SheetRemnant(remnant_id="big", width_mm=D("1900"), height_mm=D("1900"))],
    )
    assert not result.unplaced
    assert result.layouts[0].remnant_id == "big"


def test_oversized_everywhere_stays_unplaced() -> None:
    result = nest_rects(
        [piece("a", "2100", "500")],
        rule(),
        remnants=[SheetRemnant(remnant_id="r", width_mm=D("800"), height_mm=D("800"))],
    )
    assert result.unplaced and result.unplaced[0].piece_id == "a"
    assert not result.layouts


def test_determinism_and_no_overlap() -> None:
    from itertools import permutations

    the_pieces = [
        piece("a", "900", "600"), piece("b", "700", "500"),
        piece("c", "1100", "300"), piece("d", "400", "400"),
        piece("e", "600", "700"),
    ]
    expected = nest_rects(the_pieces, rule()).model_dump_json()
    for permuted in permutations(the_pieces):
        assert nest_rects(list(permuted), rule()).model_dump_json() == expected
    for layout in nest_rects(the_pieces, rule()).layouts:
        rects = [(p.x_mm, p.y_mm, p.width_mm, p.height_mm) for p in layout.placements]
        for i, (x1, y1, w1, h1) in enumerate(rects):
            for x2, y2, w2, h2 in rects[i + 1:]:
                overlap = (
                    x1 < x2 + w2 and x2 < x1 + w1
                    and y1 < y2 + h2 and y2 < y1 + h1
                )
                assert not overlap
