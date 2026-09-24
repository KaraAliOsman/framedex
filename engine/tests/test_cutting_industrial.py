"""Adversarial corpus for the industrial cutting tiers (mandate §4).

Fixtures follow audit spec D: stock alternatives, remnant pools, angle
feasibility, lexicographic cost, strategy comparison, determinism and mass
conservation. Every number here is an exact Decimal boundary.
"""

from decimal import Decimal as D
from itertools import permutations

import pytest

from dekopen_engine.cutting import (
    CutPiece,
    CuttingProfile,
    PieceLongerThanUsableStock,
    RemnantBar,
    StockRule,
    CutMaterial,
    optimize_cut,
)


def saw(**overrides) -> CuttingProfile:
    base = dict(id="saw-1", code="SAW", kerf_mm=D("0"), head_trim_mm=D("0"),
                tail_trim_mm=D("0"))
    return CuttingProfile(**{**base, **overrides})


def stock(**overrides) -> StockRule:
    base = dict(
        stock_authority_id="auth-a", workshop_sku="FRAME-A",
        commercial_sku="STOCK-A", manufacturer_name="MFG",
        supplier_name="SUP", purchase_unit="BAR", material=CutMaterial.PVC,
        color="WHITE", stock_length_mm=D("6000"),
    )
    return StockRule(**{**base, **overrides})


def piece(length: str, index: int, sku: str = "FRAME-A", **kw) -> CutPiece:
    return CutPiece(
        piece_id=f"p{index}", source_kind="PROFILE", workshop_sku=sku,
        material=CutMaterial.PVC, color="WHITE", length_mm=D(length),
        role="FRAME", unit_index=1, **kw,
    )


def remnant(remnant_id: str, length: str, authority: str = "auth-a") -> RemnantBar:
    return RemnantBar(remnant_id=remnant_id, stock_authority_id=authority,
                      length_mm=D(length))


def pieces(*lengths: str, sku: str = "FRAME-A") -> list[CutPiece]:
    return [piece(length, i, sku) for i, length in enumerate(lengths)]


# ── 1. Boundary arithmetic ────────────────────────────────────────────────

@pytest.mark.parametrize(
    ("length", "usable"),
    [("1000", "1000"), ("996", "1000"), ("1001", "1000"), ("997", "1000")],
)
def test_boundary_vs_usable_and_kerf(length: str, usable: str) -> None:
    profile = saw(kerf_mm=D("4"))
    rule = stock(stock_length_mm=D(usable))
    if D(length) + D("4") <= D(usable):
        result = optimize_cut([piece(length, 0)], [rule], profile)
        assert len(result.workshop_cut_plan) == 1
    else:
        with pytest.raises(PieceLongerThanUsableStock):
            optimize_cut([piece(length, 0)], [rule], profile)


def test_mass_conservation_per_bar() -> None:
    profile = saw(kerf_mm=D("4"), head_trim_mm=D("15"), tail_trim_mm=D("15"))
    result = optimize_cut(
        pieces("2100", "1900", "1500", "900", "800", "700"),
        [stock()], profile,
    )
    for bar in result.workshop_cut_plan:
        assert (
            bar.productive_length_mm + bar.kerf_total_mm
            + bar.head_trim_mm + bar.tail_trim_mm + bar.remainder_mm
        ) == bar.stock_length_mm


# ── 2. BFD counterexample → deep tier recovers the optimal pattern ────────

def test_deep_tier_beats_bfd_fragmentation() -> None:
    # usable 6000, kerf 0: BFD yields {3000,3000},{3000,2000},{2000,2000,1400},
    # {800,800} → 4 bars; optimal {3000,3000},{2000,2000,2000},
    # {3000,1400,800,800} → 3 bars.
    the_pieces = pieces(
        "3000", "3000", "3000", "2000", "2000", "2000", "1400", "800", "800"
    )
    rule = stock(stock_length_mm=D("6000"))
    fast = optimize_cut(the_pieces, [rule], saw(), strategy="fast")
    assert len(fast.workshop_cut_plan) == 4
    deep = optimize_cut(the_pieces, [rule], saw(), strategy="deep")
    assert len(deep.workshop_cut_plan) == 3
    auto = optimize_cut(the_pieces, [rule], saw(), strategy="auto")
    assert auto.metrics is not None and auto.metrics.bars == 3
    assert auto.strategy_comparison is not None
    assert auto.strategy_comparison["chosen"] == "deep"
    assert auto.strategy_comparison["fast"]["bars"] == 4
    assert auto.strategy_comparison["deep"]["bars"] == 3


def test_auto_prefers_fast_when_equal() -> None:
    result = optimize_cut(pieces("2000", "2000"), [stock()], saw(),
                          strategy="auto")
    assert result.strategy_comparison is not None
    assert result.strategy_comparison["chosen"] == "fast"
    assert result.metrics is not None and result.metrics.purchased_bars == 1


# ── 3. Remnant pool ────────────────────────────────────────────────────────

def test_remnant_value_trap_uses_smallest_fitting_remnant() -> None:
    # One 600 piece; remnants 5900 and 700. The 700 remnant must be consumed —
    # burning the 5900 for a 600mm piece would destroy usable stock.
    result = optimize_cut(
        pieces("600"), [stock()],
        saw(kerf_mm=D("0"), min_keep_remnant_mm=D("500")),
        remnants=[remnant("r-big", "5900"), remnant("r-small", "700")],
    )
    assert len(result.workshop_cut_plan) == 1
    bar = result.workshop_cut_plan[0]
    assert bar.source == "REMNANT" and bar.remnant_id == "r-small"
    assert result.purchase_list == []
    assert result.metrics is not None
    assert result.metrics.purchased_bars == 0 and result.metrics.remnant_bars == 1


def test_remnant_packs_multiple_pieces_and_marks_reusable_drop() -> None:
    result = optimize_cut(
        pieces("2000", "2000", "1500"), [stock()],
        saw(kerf_mm=D("0"), min_keep_remnant_mm=D("500")),
        remnants=[remnant("r1", "4000")],
    )
    bar = result.workshop_cut_plan[0]
    assert bar.source == "REMNANT"
    assert [c.length_mm for c in bar.cuts] == [D("2000"), D("2000")]
    # 4000 remnant − 4000 productive = 0 remainder; the 1500 buys a new bar.
    assert result.workshop_cut_plan[1].source == "NEW"
    assert result.workshop_cut_plan[1].remainder_mm == D("4500")
    assert result.workshop_cut_plan[1].remainder_reusable is True
    assert result.metrics is not None
    assert result.metrics.reusable_remnant_mm == D("4500")


def test_remnant_remainder_below_keep_is_process_waste() -> None:
    result = optimize_cut(
        pieces("5800"), [stock()],
        saw(kerf_mm=D("0"), min_keep_remnant_mm=D("500")),
        remnants=[remnant("r1", "5900")],
    )
    bar = result.workshop_cut_plan[0]
    assert bar.remainder_mm == D("100") and bar.remainder_reusable is False
    assert result.metrics is not None
    assert result.metrics.process_waste_mm == D("100")
    assert result.metrics.reusable_remnant_mm == D("0")


def test_remnant_of_other_identity_is_never_consumed() -> None:
    result = optimize_cut(
        pieces("600"), [stock()], saw(),
        remnants=[remnant("foreign", "700", authority="auth-other")],
    )
    assert result.workshop_cut_plan[0].source == "NEW"
    assert result.metrics is not None and result.metrics.remnant_bars == 0


def test_piece_fitting_only_a_remnant_is_hostable() -> None:
    # 6200 exceeds the 6000 variant but fits a 6400 remnant — honest host.
    result = optimize_cut(
        pieces("6200"), [stock()], saw(),
        remnants=[remnant("r1", "6400")],
    )
    assert result.workshop_cut_plan[0].remnant_id == "r1"


# ── 4. Stock-length alternatives ───────────────────────────────────────────

def test_longer_variant_wins_when_it_halves_the_bar_count() -> None:
    # 12×3200: 6000 fits 1/bar → 12 bars; 6500 fits 2/bar → 6 bars.
    rule = stock(alternative_lengths_mm=[D("6500")])
    result = optimize_cut(pieces(*["3200"] * 12), [rule], saw())
    assert result.metrics is not None and result.metrics.purchased_bars == 6
    assert {b.stock_length_mm for b in result.workshop_cut_plan} == {D("6500")}
    assert result.purchase_list == [
        result.purchase_list[0].model_copy(update={"stock_length_mm": D("6500")})
    ]
    assert result.purchase_list[0].qty_bars == 6


def test_variant_choice_prefers_fewer_then_less_scrap() -> None:
    # 2×2900 on 6000 → 1 bar, 200 scrap; on 5800 → 1 bar, 0 scrap (kerf 0).
    rule = stock(stock_length_mm=D("5800"), alternative_lengths_mm=[D("6000")])
    result = optimize_cut(pieces("2900", "2900"), [rule], saw())
    assert {b.stock_length_mm for b in result.workshop_cut_plan} == {D("5800")}


def test_variant_that_cannot_host_every_piece_is_never_picked() -> None:
    # A 5000 piece with 4000/6000 variants must buy the 6000 — the empty
    # plan a 4000 "packs" is not a plan, it drops the required cut.
    rule = stock(stock_length_mm=D("4000"), alternative_lengths_mm=[D("6000")])
    result = optimize_cut(pieces("5000"), [rule], saw())
    assert result.metrics is not None and result.metrics.unplaced == 0
    assert len(result.workshop_cut_plan) == 1
    assert result.workshop_cut_plan[0].stock_length_mm == D("6000")
    assert result.workshop_cut_plan[0].cuts[0].length_mm == D("5000")


def test_mixed_variants_beat_one_size_for_split_capacity() -> None:
    # {6100, 5500} on [5800, 6400]: the only single-variant plan is 2×6400
    # (12800 mm); mixed 1×5800 (5500) + 1×6400 (6100) = 12200 mm.
    rule = stock(stock_length_mm=D("5800"), alternative_lengths_mm=[D("6400")])
    result = optimize_cut(pieces("6100", "5500"), [rule], saw())
    assert result.metrics is not None and result.metrics.unplaced == 0
    lengths = sorted(b.stock_length_mm for b in result.workshop_cut_plan)
    assert lengths == [D("5800"), D("6400")]


def test_remnant_only_piece_beyond_capacity_is_unplaced_not_dropped() -> None:
    # Both pieces fit only the 6400 remnant, which hosts one. The second is
    # reported unplaced — never a phantom purchase, never vanished.
    result = optimize_cut(
        pieces("6200", "6200"), [stock(stock_length_mm=D("6000"))], saw(),
        remnants=[remnant("r1", "6400")],
    )
    assert [b.source for b in result.workshop_cut_plan] == ["REMNANT"]
    assert result.workshop_cut_plan[0].remnant_id == "r1"
    assert len(result.unplaced) == 1
    assert result.unplaced[0].reason == "remnant_capacity_exhausted"
    assert result.metrics is not None and result.metrics.unplaced == 1


# ── 5. Saw feasibility ─────────────────────────────────────────────────────

def test_angle_beyond_saw_limit_is_unplaced_with_reason() -> None:
    profile = saw(max_angle_deg=D("45"))
    result = optimize_cut(
        [piece("1000", 0, angle_left=D("30"), angle_right=D("60")),
         piece("1000", 1, angle_left=D("30"), angle_right=D("30"))],
        [stock()], profile,
    )
    assert len(result.unplaced) == 1
    assert result.unplaced[0].reason == "angle_exceeds_saw"
    assert result.unplaced[0].piece.piece_id == "p0"
    assert len(result.workshop_cut_plan) == 1
    assert result.metrics is not None and result.metrics.unplaced == 1


def test_no_limit_means_angles_pass() -> None:
    result = optimize_cut(
        [piece("1000", 0, angle_left=D("80"))], [stock()], saw(),
    )
    assert not result.unplaced


# ── 6. Determinism + plan seed ─────────────────────────────────────────────

def test_plan_seed_is_stable_under_permutation() -> None:
    the_pieces = pieces("520", "480", "330", "330", "170")
    seeds = set()
    for permuted in permutations(the_pieces):
        result = optimize_cut(list(permuted), [stock()], saw(), strategy="auto")
        seeds.add(result.plan_seed)
        assert result.model_dump_json() == optimize_cut(
            the_pieces, [stock()], saw(), strategy="auto",
        ).model_dump_json()
    assert len(seeds) == 1


def test_seed_changes_with_inputs() -> None:
    a = optimize_cut(pieces("520"), [stock()], saw()).plan_seed
    b = optimize_cut(pieces("521"), [stock()], saw()).plan_seed
    assert a != b


# ── 7. Deep tier state cap falls back honestly ─────────────────────────────

def test_deep_falls_back_when_state_space_explodes() -> None:
    # 30 distinct lengths → pattern/state space far exceeds the cap; the deep
    # tier must return a plan (BFD fallback), never crash.
    lengths = [str(100 + 13 * i) for i in range(30)]
    result = optimize_cut(
        pieces(*lengths), [stock(stock_length_mm=D("6000"))],
        saw(), strategy="deep",
    )
    assert result.metrics is not None
    assert result.metrics.unplaced == 0
    for bar in result.workshop_cut_plan:
        assert (
            bar.productive_length_mm + bar.kerf_total_mm
            + bar.head_trim_mm + bar.tail_trim_mm + bar.remainder_mm
        ) == bar.stock_length_mm
