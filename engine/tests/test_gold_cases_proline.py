"""Proline PRO6004 against the owner's real work order N° 385 (0.00 mm).

Each expected value is printed in that order (pages 6 and 7); the parameters
in `proline_catalog.py` were read back from it. A mismatch is a real defect.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from dekopen_engine import BayOpeningType, EngineResult, NodeType, ParametricNode, ProfileRole, calculate_geometry
from engine.tests.proline_catalog import pro6004_params


def d(value: str) -> Decimal:
    return Decimal(value)


def bay(case_id: str, opening: BayOpeningType) -> ParametricNode:
    return ParametricNode(
        id=case_id,
        type=NodeType.BAY,
        opening_type=opening,
        glass_thickness_mm=d("20.00"),
        glass_spec="4-12-4",  # «DVH 4 INC + 12 SS + 4 INC» in the order
    )


def split(case_id: str, width: str, height: str, left: ParametricNode, right: ParametricNode) -> ParametricNode:
    return ParametricNode(
        id=case_id,
        type=NodeType.SPLIT_V,
        width_mm=d(width),
        height_mm=d(height),
        split_offset_mm=d(width) / 2,
        mullion_profile_sku="PRO03",
        children=[left, right],
    )


def cuts(result: EngineResult, role: ProfileRole, bay_id: str | None = None) -> list[tuple[Decimal, int]]:
    return sorted(
        (cut.length_mm, cut.qty)
        for cut in result.profile_cuts
        if cut.role is role and (bay_id is None or cut.bay_id == bay_id)
    )


def steel(result: EngineResult, role: ProfileRole) -> list[Decimal]:
    return sorted(piece.length_mm for piece in result.reinforcements if piece.role is role)


def glass(result: EngineResult, bay_id: str) -> tuple[Decimal, Decimal]:
    pane = next(item for item in result.glasses if item.bay_id == bay_id)
    return pane.width_mm, pane.height_mm


def test_item_04_two_outer_sashes_with_transom_1193_x_1350() -> None:
    result = calculate_geometry(
        split("i04", "1193", "1350", bay("l", BayOpeningType.TURN_LEFT), bay("r", BayOpeningType.TURN_RIGHT)),
        pro6004_params(sash_sku="PRO521"),
    )
    assert cuts(result, ProfileRole.FRAME) == [(d("1199.00"), 2), (d("1356.00"), 2)]
    assert cuts(result, ProfileRole.MULLION_V) == [(d("1350.00"), 1)]
    assert cuts(result, ProfileRole.SASH, "l") == [(d("554.50"), 2), (d("1284.00"), 2)]
    assert cuts(result, ProfileRole.GLAZING_BEAD, "l") == [(d("428.50"), 2), (d("1158.00"), 2)]
    assert steel(result, ProfileRole.FRAME) == [d("1085.00"), d("1242.00")]
    assert steel(result, ProfileRole.MULLION_V) == [d("1330.00")]
    assert steel(result, ProfileRole.SASH) == [d("408.50"), d("408.50"), d("1138.00"), d("1138.00")]
    assert glass(result, "l") == glass(result, "r") == (d("418.50"), d("1148.00"))


def test_item_05_fixed_and_inner_sash_1193_x_1358() -> None:
    result = calculate_geometry(
        split("i05", "1193", "1358", bay("fix", BayOpeningType.FIXED), bay("turn", BayOpeningType.TURN_RIGHT)),
        pro6004_params(sash_sku="PRO02"),
    )
    assert cuts(result, ProfileRole.FRAME) == [(d("1199.00"), 2), (d("1364.00"), 2)]
    assert cuts(result, ProfileRole.MULLION_V) == [(d("1358.00"), 1)]
    assert cuts(result, ProfileRole.SASH, "turn") == [(d("554.50"), 2), (d("1292.00"), 2)]
    assert cuts(result, ProfileRole.GLAZING_BEAD, "fix") == [(d("532.50"), 2), (d("1270.00"), 2)]
    assert steel(result, ProfileRole.FRAME) == [d("1085.00"), d("1250.00")]
    assert steel(result, ProfileRole.MULLION_V) == [d("1338.00")]
    assert steel(result, ProfileRole.SASH) == [d("489.70"), d("1227.20")]
    assert glass(result, "fix") == (d("522.50"), d("1260.00"))
    assert glass(result, "turn") == (d("418.50"), d("1156.00"))


@pytest.mark.xfail(strict=True, reason="The inner Pro02 sash takes a bead 13 mm longer than the "
                   "outer Pro521; bead rules are per glass thickness, not per sash profile yet.")
def test_item_05_inner_sash_bead_follows_its_sash_profile() -> None:
    result = calculate_geometry(
        split("i05", "1193", "1358", bay("fix", BayOpeningType.FIXED), bay("turn", BayOpeningType.TURN_RIGHT)),
        pro6004_params(sash_sku="PRO02"),
    )
    assert cuts(result, ProfileRole.GLAZING_BEAD, "turn") == [(d("441.50"), 2), (d("1179.00"), 2)]


def test_item_05_two_fixed_panes_2385_x_900() -> None:
    result = calculate_geometry(
        split("a05", "2385", "900", bay("f1", BayOpeningType.FIXED), bay("f2", BayOpeningType.FIXED)),
        pro6004_params(),
    )
    assert cuts(result, ProfileRole.FRAME) == [(d("906.00"), 2), (d("2391.00"), 2)]
    assert cuts(result, ProfileRole.GLAZING_BEAD, "f1") == [(d("812.00"), 2), (d("1128.50"), 2)]
    assert steel(result, ProfileRole.FRAME) == [d("792.00"), d("2277.00")]
    assert glass(result, "f1") == glass(result, "f2") == (d("1118.50"), d("802.00"))
