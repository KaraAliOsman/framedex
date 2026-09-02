from __future__ import annotations

from decimal import Decimal

import pytest

from dekopen_engine import (
    BayOpeningType,
    EffectiveProfileArticle,
    GlazingBeadRule,
    MaterialType,
    NodeType,
    ParametricNode,
    ProfileRole,
    RailType,
    SystemParams,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def _article(
    *,
    sku: str,
    role: ProfileRole,
    face_width_mm: str,
    welding_loss_mm: str,
    reinforcement_gap_mm: str,
) -> EffectiveProfileArticle:
    return EffectiveProfileArticle(
        sku=sku,
        role=role,
        face_width_mm=d(face_width_mm),
        welding_loss_mm=d(welding_loss_mm),
        reinforcement_gap_mm=d(reinforcement_gap_mm),
        weight_kg_m=d("1.2000"),
        steel_weight_kg_m=d("1.7000"),
    )


@pytest.fixture(scope="session")
def demo_60_params() -> SystemParams:
    frame = _article(
        sku="MARCO",
        role=ProfileRole.FRAME,
        face_width_mm="60.00",
        welding_loss_mm="6.00",
        reinforcement_gap_mm="15.00",
    )
    sash = _article(
        sku="HOJA",
        role=ProfileRole.SASH,
        face_width_mm="75.00",
        welding_loss_mm="6.00",
        reinforcement_gap_mm="15.00",
    )
    mullion_v = _article(
        sku="POSTE-V",
        role=ProfileRole.MULLION_V,
        face_width_mm="80.00",
        welding_loss_mm="0.00",
        reinforcement_gap_mm="5.00",
    )
    mullion_h = _article(
        sku="POSTE-H",
        role=ProfileRole.MULLION_H,
        face_width_mm="80.00",
        welding_loss_mm="0.00",
        reinforcement_gap_mm="5.00",
    )
    bead_24 = _article(
        sku="JQ-24",
        role=ProfileRole.GLAZING_BEAD,
        face_width_mm="24.00",
        welding_loss_mm="0.00",
        reinforcement_gap_mm="15.00",
    )
    bead_14 = _article(
        sku="JQ-14",
        role=ProfileRole.GLAZING_BEAD,
        face_width_mm="14.00",
        welding_loss_mm="0.00",
        reinforcement_gap_mm="15.00",
    )
    bead_10 = _article(
        sku="JQ-10",
        role=ProfileRole.GLAZING_BEAD,
        face_width_mm="10.00",
        welding_loss_mm="0.00",
        reinforcement_gap_mm="15.00",
    )

    return SystemParams(
        system_code="DEMO_60",
        depth_mm=d("60.00"),
        material=MaterialType.PVC,
        effective_profile_articles={
            ProfileRole.FRAME: frame,
            ProfileRole.SASH: sash,
            ProfileRole.MULLION_V: mullion_v,
            ProfileRole.MULLION_H: mullion_h,
        },
        glazing_bead_rules={
            d("4.00"): GlazingBeadRule(
                glass_thickness_mm=d("4.00"),
                bead_article=bead_24,
                bead_width_mm=d("24.00"),
                gasket_interior_mm=d("3.00"),
                gasket_exterior_mm=d("3.00"),
                cut_add_mm=d("9.00"),
            ),
            d("5.00"): GlazingBeadRule(
                glass_thickness_mm=d("5.00"),
                bead_article=bead_24,
                bead_width_mm=d("24.00"),
                gasket_interior_mm=d("2.50"),
                gasket_exterior_mm=d("2.50"),
                cut_add_mm=d("9.00"),
            ),
            d("6.00"): GlazingBeadRule(
                glass_thickness_mm=d("6.00"),
                bead_article=bead_24,
                bead_width_mm=d("24.00"),
                gasket_interior_mm=d("2.00"),
                gasket_exterior_mm=d("2.00"),
                cut_add_mm=d("9.00"),
            ),
            d("20.00"): GlazingBeadRule(
                glass_thickness_mm=d("20.00"),
                bead_article=bead_14,
                bead_width_mm=d("14.00"),
                gasket_interior_mm=d("3.00"),
                gasket_exterior_mm=d("3.00"),
                cut_add_mm=d("9.00"),
            ),
            d("24.00"): GlazingBeadRule(
                glass_thickness_mm=d("24.00"),
                bead_article=bead_10,
                bead_width_mm=d("10.00"),
                gasket_interior_mm=d("3.00"),
                gasket_exterior_mm=d("3.00"),
                cut_add_mm=d("9.00"),
            ),
        },
        rebate_depth_mm=d("20.00"),
        end_milling_overlap_mm=d("0.00"),
        sash_overlap_mm=d("8.00"),
        glass_clearance_white_mm=d("5.00"),
        glass_clearance_foil_mm=d("5.00"),
        pulley_height_mm=d("12.00"),
        central_overlap_mm=d("40.00"),
        sliding_lateral_clearance_mm=d("0.00"),
        sliding_end_add_mm=d("6.00"),
        corner_bracket_loss_mm=d("0.00"),
        hook_depth_mm=d("0.00"),
        door_threshold_mm=d("30.00"),
        door_bottom_clearance_mm=d("20.00"),
        rail_type=RailType.DUAL,
        pvc_weight_kg_m=d("1.2000"),
        steel_weight_kg_m=d("1.7000"),
        hardware_kit_weight_kg=d("2.50"),
        available_hardware_kits=[],
    )


def bay_node(
    *,
    case_id: str,
    width_mm: str,
    height_mm: str,
    opening_type: BayOpeningType,
    glass_thickness_mm: str,
    glass_spec: str,
) -> ParametricNode:
    return ParametricNode(
        id=case_id,
        type=NodeType.BAY,
        width_mm=d(width_mm),
        height_mm=d(height_mm),
        opening_type=opening_type,
        glass_thickness_mm=d(glass_thickness_mm),
        glass_spec=glass_spec,
    )


@pytest.fixture(scope="session")
def g1_node() -> ParametricNode:
    return bay_node(
        case_id="g1",
        width_mm="1000.00",
        height_mm="1000.00",
        opening_type=BayOpeningType.FIXED,
        glass_thickness_mm="4.00",
        glass_spec="4",
    )


@pytest.fixture(scope="session")
def g2_node() -> ParametricNode:
    return bay_node(
        case_id="g2",
        width_mm="800.00",
        height_mm="1200.00",
        opening_type=BayOpeningType.TURN_LEFT,
        glass_thickness_mm="24.00",
        glass_spec="4-16-4",
    )


@pytest.fixture(scope="session")
def g3_node() -> ParametricNode:
    return bay_node(
        case_id="g3",
        width_mm="1000.00",
        height_mm="1400.00",
        opening_type=BayOpeningType.TILT_TURN_LEFT,
        glass_thickness_mm="20.00",
        glass_spec="4-12-4",
    )


@pytest.fixture(scope="session")
def g4_node() -> ParametricNode:
    return ParametricNode(
        id="g4",
        type=NodeType.SPLIT_V,
        width_mm=d("1800.00"),
        height_mm=d("1500.00"),
        split_offset_mm=d("900.00"),
        mullion_profile_sku="POSTE-V",
        children=[
            ParametricNode(
                id="bay_fixed",
                type=NodeType.BAY,
                opening_type=BayOpeningType.FIXED,
                glass_thickness_mm=d("24.00"),
                glass_spec="4-16-4 Float Incoloro",
            ),
            ParametricNode(
                id="bay_ob",
                type=NodeType.BAY,
                opening_type=BayOpeningType.TILT_TURN_RIGHT,
                glass_thickness_mm=d("20.00"),
                glass_spec="4-12-4 Float Incoloro",
            ),
        ],
    )
