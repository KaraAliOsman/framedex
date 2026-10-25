"""Proline PRO6004 as the owner's workshop cuts it.

Source: the owner's work order N° 385 (NuveraPro, 29-10-2025), pages 1, 6 and 7:
Pro01 frame 60/64, Pro02 inner window sash 80 mm, Pro521 outer window sash
80 mm, Pro03 transom 80 mm, Pro05 bead 19/20-22, Pro-R1 / Pro-R19 steel. Every
value below is read back from those printed cuts; none is a manufacturer
certification.
"""

from __future__ import annotations

from decimal import Decimal

from dekopen_engine import (
    EffectiveProfileArticle,
    GlazingBeadRule,
    MaterialType,
    ProfileRole,
    RailType,
    SystemParams,
)
from engine.tests.catalog import demo_hardware_kits


def d(value: str) -> Decimal:
    return Decimal(value)


def _article(sku: str, role: ProfileRole, face: str, weld: str, steel_gap: str) -> EffectiveProfileArticle:
    return EffectiveProfileArticle(
        sku=sku,
        role=role,
        material=MaterialType.PVC,
        face_width_mm=d(face),
        commercial_length_mm=d("5800.00"),
        welding_loss_mm=d(weld),
        reinforcement_gap_mm=d(steel_gap),
        weight_kg_m=d("1.2000"),
        steel_weight_kg_m=d("1.7000"),
    )


def pro6004_params(*, sash_sku: str = "PRO02") -> SystemParams:
    """`PRO02` is the inner window sash; `PRO521` the outer one (deeper steel)."""
    sash_gap = {"PRO02": "29.40", "PRO521": "70.00"}[sash_sku]
    bead = _article("PRO05", ProfileRole.GLAZING_BEAD, "19.00", "0.00", "0.00")
    return SystemParams(
        system_code="PRO6004",
        finishes=("WHITE",),
        depth_mm=d("60.00"),
        material=MaterialType.PVC,
        effective_profile_articles={
            ProfileRole.FRAME: _article("PRO01", ProfileRole.FRAME, "64.00", "6.00", "54.00"),
            ProfileRole.SASH: _article(sash_sku, ProfileRole.SASH, "80.00", "6.00", sash_gap),
            ProfileRole.MULLION_V: _article("PRO03", ProfileRole.MULLION_V, "80.00", "0.00", "10.00"),
            ProfileRole.MULLION_H: _article("PRO03", ProfileRole.MULLION_H, "80.00", "0.00", "10.00"),
        },
        glazing_bead_rules={
            d("20.00"): GlazingBeadRule(
                glass_thickness_mm=d("20.00"),
                bead_article=bead,
                bead_width_mm=d("19.00"),
                gasket_interior_mm=d("3.00"),
                gasket_exterior_mm=d("3.00"),
                cut_add_mm=d("10.00"),
            ),
        },
        rebate_depth_mm=d("20.00"),
        end_milling_overlap_mm=d("64.00"),
        sash_overlap_mm=d("28.00"),
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
        sliding_glazing_deduction_width_mm=d("20.00"),
        sliding_glazing_deduction_height_mm=d("20.00"),
        door_leaf_side_clearance_mm=d("7.00"),
        available_hardware_kits=demo_hardware_kits(),
    )
