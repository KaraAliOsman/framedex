"""Independent owner fixtures and adversarial boundaries for SHOT-07 BFD."""

from decimal import Decimal as D

import pytest
from pydantic import ValidationError

from dekopen_engine.cutting import (
    AmbiguousStockAuthority, CutMaterial, CutPiece, CuttingProfile,
    InvalidCutContract, MissingStockAuthority, PieceLongerThanUsableStock, StockRule, optimize_cut,
)


def saw() -> CuttingProfile:
    return CuttingProfile(id="demo-saw", code="DEMO", kerf_mm=D("4.00"),
                          head_trim_mm=D("15.00"), tail_trim_mm=D("15.00"))


def stock(length: str = "5800.00", sku: str = "PRO6004-FRAME-DEMO") -> StockRule:
    return StockRule(
        stock_authority_id="synthetic-proline", workshop_sku=sku,
        commercial_sku="DEMO-PROLINE-PRO6004-BAR-5800", manufacturer_name="Proline",
        supplier_name="DEMO-SUPPLIER", purchase_unit="BAR", material=CutMaterial.PVC,
        color="WHITE", stock_length_mm=D(length),
    )


def piece(length: str, index: int = 1, sku: str = "PRO6004-FRAME-DEMO") -> CutPiece:
    return CutPiece(piece_id=f"piece-{index}", source_kind="PROFILE", workshop_sku=sku,
                    material=CutMaterial.PVC, color="WHITE", length_mm=D(length),
                    role="FRAME", unit_index=1)


def test_proline_owner_fixture_separates_purchase_and_workshop() -> None:
    pieces = [piece(length, i) for i, length in enumerate(
        ["1006.00"] * 4 + ["806.00"] * 2)]
    result = optimize_cut(pieces, [stock()], saw())
    assert result.purchase_list[0].qty_bars == 1
    assert result.purchase_list[0].commercial_sku == "DEMO-PROLINE-PRO6004-BAR-5800"
    bar = result.workshop_cut_plan[0]
    assert len(result.workshop_cut_plan) == 1
    assert bar.stock_length_mm == D("5800.00")
    assert bar.productive_length_mm == D("5636.00")
    assert bar.kerf_total_mm == D("24.00")
    assert bar.process_consumed_mm == D("5690.00")
    assert bar.remainder_mm == D("110.00")
    assert bar.waste_mm == D("164.00")
    assert bar.yield_pct == D("97.1724")
    assert bar.waste_pct == D("2.8276")
    assert all(c.workshop_sku == "PRO6004-FRAME-DEMO" for c in bar.cuts)
    assert all(c.workshop_sku != result.purchase_list[0].commercial_sku for c in bar.cuts)
    assert optimize_cut(list(reversed(pieces)), [stock()], saw()).model_dump_json() == (
        result.model_dump_json())
    assert optimize_cut(pieces, [stock()], saw()).model_dump_json() == result.model_dump_json()


@pytest.mark.parametrize(("length", "remaining"), [("5766.00", "0.00"),
                                                       ("5765.99", "0.01")])
def test_exact_fit_and_under(length: str, remaining: str) -> None:
    bar = optimize_cut([piece(length)], [stock()], saw()).workshop_cut_plan[0]
    assert bar.remainder_mm == D(remaining)
    assert bar.kerf_total_mm == D("4.00")  # One piece and final piece both consume kerf.


def test_overflow_one_hundredth() -> None:
    with pytest.raises(PieceLongerThanUsableStock):
        optimize_cut([piece("5766.01")], [stock()], saw())


def test_both_trims_once_per_new_bar() -> None:
    profile = saw().model_copy(update={"head_trim_mm": D("11"), "tail_trim_mm": D("19")})
    bars = optimize_cut([piece("4000", 1), piece("4000", 2)], [stock()], profile).workshop_cut_plan
    assert len(bars) == 2
    assert [b.remainder_mm for b in bars] == [D("1766"), D("1766")]
    assert all(b.head_trim_mm == D("11") and b.tail_trim_mm == D("19") for b in bars)


def test_best_fit_and_lowest_index_tie() -> None:
    profile = saw().model_copy(update={"kerf_mm": D("1"), "head_trim_mm": D("0"),
                                      "tail_trim_mm": D("0")})
    bars = optimize_cut([piece(x, i) for i, x in enumerate(["60", "50", "38"])],
                        [stock("100")], profile).workshop_cut_plan
    assert [[c.length_mm for c in b.cuts] for b in bars] == [[D("60"), D("38")], [D("50")]]
    tied = optimize_cut([piece(x, i) for i, x in enumerate(["60", "60", "38"])],
                        [stock("100")], profile).workshop_cut_plan
    assert [[c.length_mm for c in b.cuts] for b in tied] == [[D("60"), D("38")], [D("60")]]


def test_stock_missing_and_ambiguous_fail_closed() -> None:
    with pytest.raises(MissingStockAuthority):
        optimize_cut([piece("100")], [], saw())
    with pytest.raises(AmbiguousStockAuthority):
        optimize_cut([piece("100")], [stock(), stock()], saw())


@pytest.mark.parametrize("field,value", [("material", CutMaterial.ALUMINIUM),
                                        ("material", CutMaterial.STEEL), ("color", "FOILED")])
def test_physical_groups_never_mix(field: str, value: object) -> None:
    other_piece = piece("100", 2).model_copy(update={field: value})
    other_stock = stock().model_copy(update={field: value, "stock_authority_id": "other"})
    result = optimize_cut([piece("100", 1), other_piece], [stock(), other_stock], saw())
    assert len(result.workshop_cut_plan) == 2


def test_explicit_shared_stock_preserves_both_workshop_skus() -> None:
    result = optimize_cut([piece("100", 1), piece("100", 2, "OTHER-WORKSHOP")],
                          [stock(), stock(sku="OTHER-WORKSHOP")], saw())
    assert len(result.workshop_cut_plan) == 1
    assert {c.workshop_sku for c in result.workshop_cut_plan[0].cuts} == {
        "PRO6004-FRAME-DEMO", "OTHER-WORKSHOP"}


def test_duplicate_and_invalid_piece_identity() -> None:
    with pytest.raises(InvalidCutContract, match="Duplicate piece identity"):
        optimize_cut([piece("100"), piece("100")], [stock()], saw())
    for identity in ("", " ", " leading"):
        with pytest.raises(ValidationError):
            CutPiece.model_validate({**piece("100").model_dump(), "piece_id": identity})


@pytest.mark.parametrize("value", ["0", "-0.01"])
def test_stock_and_piece_must_be_positive(value: str) -> None:
    with pytest.raises(ValidationError):
        stock(value)
    with pytest.raises(ValidationError):
        piece(value)


@pytest.mark.parametrize("field", ["kerf_mm", "head_trim_mm", "tail_trim_mm"])
def test_negative_cutting_parameters_rejected(field: str) -> None:
    with pytest.raises(ValidationError):
        CuttingProfile.model_validate({**saw().model_dump(), field: D("-0.01")})


def test_missing_kerf_and_excessive_trims_rejected() -> None:
    raw = saw().model_dump(exclude={"kerf_mm"})
    with pytest.raises(ValidationError):
        CuttingProfile.model_validate(raw)
    with pytest.raises(InvalidCutContract, match="Trims exceed stock"):
        optimize_cut([piece("1")], [stock("10")], saw())


def test_two_physical_stocks_for_one_workshop_sku_are_ambiguous() -> None:
    other = stock().model_copy(update={"commercial_sku": "SECOND-STOCK"})
    for rules in ([stock(), other], [other, stock()]):
        with pytest.raises(AmbiguousStockAuthority):
            optimize_cut([piece("100")], rules, saw())


def test_purchase_aggregation_and_canonical_order_independent_of_inputs() -> None:
    from itertools import permutations

    a = stock().model_copy(update={"commercial_sku": "A-STOCK"})
    z = stock(sku="Z-WORKSHOP").model_copy(update={"commercial_sku": "Z-STOCK"})
    pieces = [piece("4000", 1), piece("4000", 2), piece("3000", 3, "Z-WORKSHOP")]
    expected = optimize_cut(pieces, [a, z], saw())
    assert [(line.commercial_sku, line.qty_bars) for line in expected.purchase_list] == [
        ("A-STOCK", 2), ("Z-STOCK", 1)]
    assert [bar.bar_index for bar in expected.workshop_cut_plan] == [1, 2, 3]
    for permuted in permutations(pieces):
        for rules in ([a, z], [z, a]):
            assert optimize_cut(list(permuted), rules, saw()).model_dump_json() == (
                expected.model_dump_json())
