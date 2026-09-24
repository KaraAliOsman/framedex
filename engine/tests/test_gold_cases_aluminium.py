"""Golden cases for the mechanically jointed (aluminium) geometry path.

PVC adds a per-end weld allowance so fused corners land on finished size;
aluminium loses `corner_bracket_loss_mm` per mitred end to the corner bracket
that seats inside the profile. These cases pin the exact cut values.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from dekopen_engine import (
    BayOpeningType,
    EngineResult,
    MaterialType,
    NodeType,
    ParametricNode,
    ProfileRole,
    SystemParams,
    calculate_geometry,
)

from engine.tests.catalog import alu_65_params, d


def _assert_exact_mm(actual: Decimal, expected: str) -> None:
    discrepancy_mm = abs(actual - Decimal(expected))
    assert discrepancy_mm == Decimal("0.00"), (
        f"expected {expected} mm, got {actual} mm; discrepancy={discrepancy_mm} mm"
    )


def _profile_lengths(result: EngineResult, role: ProfileRole) -> list[Decimal]:
    return sorted(cut.length_mm for cut in result.profile_cuts if cut.role is role)


@pytest.fixture
def alu_params() -> SystemParams:
    return alu_65_params()


@pytest.fixture
def fixed_node() -> ParametricNode:
    return ParametricNode(
        id="B1", type=NodeType.BAY, opening_type=BayOpeningType.FIXED,
        width_mm=d("1000.00"), height_mm=d("1000.00"),
        glass_spec="4-16-4", glass_thickness_mm=d("24.00"),
        glass_article_sku="DVH-24",
    )


@pytest.fixture
def turn_node() -> ParametricNode:
    return ParametricNode(
        id="B1", type=NodeType.BAY, opening_type=BayOpeningType.TURN_LEFT,
        width_mm=d("800.00"), height_mm=d("1200.00"),
        glass_spec="4-16-4", glass_thickness_mm=d("24.00"),
        glass_article_sku="DVH-24",
    )


def test_alu_fixed_loses_corner_bracket_per_end(
    alu_params: SystemParams, fixed_node: ParametricNode,
) -> None:
    assert alu_params.material is MaterialType.ALUMINIUM
    result = calculate_geometry(fixed_node, alu_params)

    # Frame cut = nominal - 2 x corner_bracket_loss (2.00 mm per end).
    frame_lengths = _profile_lengths(result, ProfileRole.FRAME)
    assert len(frame_lengths) == 2
    for actual in frame_lengths:
        _assert_exact_mm(actual, "996.00")

    # Mechanically jointed profiles carry no welded-steel reinforcement.
    assert result.reinforcements == []

    # Glass = clear + 2 x (rebate depth 20.00 - clearance 4.00): it seats into the rebate.
    glass = result.glasses[0]
    _assert_exact_mm(glass.width_mm, "922.00")
    _assert_exact_mm(glass.height_mm, "922.00")

    # Bead cut = glass + cut_add (7.00 mm).
    bead_lengths = _profile_lengths(result, ProfileRole.GLAZING_BEAD)
    assert len(bead_lengths) == 2
    for actual in bead_lengths:
        _assert_exact_mm(actual, "929.00")


def test_alu_turn_sash_loses_corner_bracket_per_end(
    alu_params: SystemParams, turn_node: ParametricNode,
) -> None:
    result = calculate_geometry(turn_node, alu_params)

    frame_lengths = _profile_lengths(result, ProfileRole.FRAME)
    assert frame_lengths == [Decimal("796.00"), Decimal("1196.00")]

    # Finished sash = clear + 2 x sash overlap (6.00); cut = finished - 2 x 2.00.
    sash_lengths = _profile_lengths(result, ProfileRole.SASH)
    assert sash_lengths == [Decimal("698.00"), Decimal("1098.00")]

    assert result.reinforcements == []
