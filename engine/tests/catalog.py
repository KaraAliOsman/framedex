"""Canonical DEMO_60 test catalog; live DB parity is checked independently."""

from __future__ import annotations

from decimal import Decimal


from dekopen_engine import (
    HardwareComponent,
    HardwareKitRule,
    PanelRule,
    EffectiveProfileArticle,
    GlazingBeadRule,
    MaterialType,
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
        material=MaterialType.PVC,
        face_width_mm=d(face_width_mm),
        welding_loss_mm=d(welding_loss_mm),
        reinforcement_gap_mm=d(reinforcement_gap_mm),
        weight_kg_m=d("1.2000"),
        steel_weight_kg_m=d("1.7000"),
    )


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
            ProfileRole.THRESHOLD: EffectiveProfileArticle(
                sku="UMBRAL-ALU", role=ProfileRole.THRESHOLD, material=MaterialType.ALUMINIUM,
                face_width_mm=d("30.00"), welding_loss_mm=d("0.00"),
                reinforcement_gap_mm=d("0.00"), weight_kg_m=d("1.2000"),
                steel_weight_kg_m=d("1.7000"),
            ),
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
        sliding_glazing_deduction_width_mm=d("20.00"),
        sliding_glazing_deduction_height_mm=d("20.00"),
        door_leaf_side_clearance_mm=d("7.00"),
        available_hardware_kits=demo_hardware_kits(),
        available_panel_rules={
            "PANEL-SANDWICH-DEMO-24": PanelRule(
                sku="PANEL-SANDWICH-DEMO-24", name="Panel Sándwich Demo 24mm",
                kind="SANDWICH_PANEL", thickness_mm=d("24.00"), weight_kg_m2=d("10.0000"),
            ),
        },
    )


def demo_hardware_kits() -> list[HardwareKitRule]:
    """Approved synthetic fixtures. New ranges are not manufacturer specifications."""
    rows = [
        ("KIT-TURN", "Kit Practicable Demo 60", "TURN", "400", "1200", "500", "2400", "80", 0, 0),
        ("KIT-TILT-TURN", "Kit Vorne OB 100kg", "TILT_TURN", "450", "1400", "600", "2400", "100", 0, 1),
        ("KIT-SLIDING", "Kit Corredera Demo 60", "SLIDING", "400", "1500", "500", "2500", "120", 2, 0),
        ("KIT-AWNING-16", 'Kit Proyectante Compás 16" 45kg', "AWNING", "400", "1200", "400", "1000", "45", 0, 2),
        ("KIT-DOOR-MULTIPOINT", "Kit Puerta Entrada Multipunto Demo 60", "DOOR", "700", "1200", "1800", "2400", "120", 0, 0),
    ]
    contents = {
        "KIT-AWNING-16": [HardwareComponent(
            sku="DEMO-STAY-16", name='Compás a fricción 16"', qty=d("2"), unit="unit",
        )],
        "KIT-DOOR-MULTIPOINT": [HardwareComponent(
            sku="DEMO-LOCK-MULTIPOINT", name="Cerradura multipunto Demo", qty=d("1"), unit="unit",
        )],
    }
    return [HardwareKitRule(
        sku=sku, name=name, opening_type=opening, min_leaf_width_mm=d(min_w),
        max_leaf_width_mm=d(max_w), min_leaf_height_mm=d(min_h), max_leaf_height_mm=d(max_h),
        max_leaf_weight_kg=d(max_kg), rail_type=RailType.DUAL,
        carriages_qty=carriages, stay_arms_qty=stays, weight_kg=d("2.50"),
        contents=contents.get(sku, []),
    ) for sku, name, opening, min_w, max_w, min_h, max_h, max_kg, carriages, stays in rows]
