"""Independent frozen dimensions and exact mass expectations for the Core Gate."""

from decimal import Decimal

import pytest

from dekopen_engine import (
    BayOpeningType, EffectiveProfileArticle, EngineResult, MaterialType, NodeType, ParametricNode,
    ProfileRole, SystemParams, calculate_geometry,
)
from dekopen_engine.geometry import SashGeometry
from dekopen_engine.glass import exact_glass_weight
from dekopen_engine.panel import exact_panel_weight
from dekopen_engine.weight import ExactLeafWeight, base_leaf_weight, with_hardware_weight

D = Decimal


def core_node(case: str) -> ParametricNode:
    width, height, opening = {
        "G5": ("2000.00", "2100.00", BayOpeningType.SLIDING_2L),
        "G6": ("1200.00", "800.00", BayOpeningType.AWNING),
        "G7": ("950.00", "2150.00", BayOpeningType.DOOR_ENTRY),
    }[case]
    return ParametricNode(
        id=case, type=NodeType.BAY, width_mm=D(width), height_mm=D(height),
        opening_type=opening,
        panel_article_sku="PANEL-SANDWICH-DEMO-24" if case == "G7" else None,
        glass_thickness_mm=None if case == "G7" else D("20.00"),
        glass_spec=None if case == "G7" else "4-12-4 Float Incoloro",
    )


def exact_weight_for_leaf(
    result: EngineResult, params: SystemParams, bay_id: str, leaf_id: str | None = None,
) -> ExactLeafWeight:
    cuts = [p for p in result.profile_cuts if p.bay_id == bay_id and p.leaf_id == leaf_id]
    steel = [p for p in result.reinforcements if p.bay_id == bay_id and p.leaf_id == leaf_id]
    panels = [p for p in result.panels if p.bay_id == bay_id and p.leaf_id == leaf_id]
    if panels:
        panel = panels[0]
        infill = exact_panel_weight(
            panel.width_mm, panel.height_mm, params.available_panel_rules[panel.sku],
        )
    else:
        glass = next(p for p in result.glasses if p.bay_id == bay_id and p.leaf_id == leaf_id)
        infill = exact_glass_weight(glass.width_mm, glass.height_mm, "4-12-4", D("20.00"))
    item = next(p for p in result.hardware_items if p.bay_id == bay_id and p.leaf_id == leaf_id)
    kit = next(k for k in params.available_hardware_kits if k.sku == item.kit_sku)
    return with_hardware_weight(base_leaf_weight(
        profile_cuts=cuts, reinforcements=steel, infill_weight_kg=infill, params=params,
    ), kit, params)


def assert_role(
    result: EngineResult, role: ProfileRole, cuts: list[tuple[str, int]],
    steel: list[tuple[str, int]],
) -> None:
    assert [(p.length_mm, p.qty) for p in result.profile_cuts if p.role is role] == [
        (D(length), qty) for length, qty in cuts
    ]
    assert [(p.length_mm, p.qty) for p in result.reinforcements if p.role is role] == [
        (D(length), qty) for length, qty in steel
    ]


def test_g3_hardware_resolved_shot06_preserves_standalone_geometry(
    demo_60_params: SystemParams, g3_node: ParametricNode,
) -> None:
    result = calculate_geometry(g3_node, demo_60_params)
    assert_role(result, ProfileRole.SASH, [("902", 2), ("1302", 2)],
                [("866", 2), ("1266", 2)])
    assert (result.glasses[0].width_mm, result.glasses[0].height_mm) == (D("776"), D("1176"))
    assert [(item.kit_sku, item.name, item.qty, item.unit) for item in result.hardware_items] == [
        ("KIT-TILT-TURN", "Kit Vorne OB 100kg", 1, "kit"),
    ]
    exact = exact_weight_for_leaf(result, demo_60_params, g3_node.id)
    assert (exact.pvc_weight_kg, exact.steel_weight_kg, exact.infill_weight_kg) == (
        D("5.2896"), D("7.2488"), D("18.251520"),
    )
    assert exact.total_weight_kg == D("33.289920")
    assert result.leaf_weights[0].total_weight_kg == D("33.29")
    kit = next(k for k in demo_60_params.available_hardware_kits if k.sku == "KIT-TILT-TURN")
    assert kit.max_leaf_weight_kg == D("100.00")
    assert exact.total_weight_kg <= kit.max_leaf_weight_kg
    assert not result.leaf_weights[0].used_fallback


def test_g5_complete_bom_exact(demo_60_params: SystemParams) -> None:
    result = calculate_geometry(core_node("G5"), demo_60_params)
    assert_role(result, ProfileRole.FRAME, [("2006", 2), ("2106", 2)],
                [("1970", 2), ("2070", 2)])
    assert_role(result, ProfileRole.SASH, [("966", 2), ("1956", 2)] * 2,
                [("930", 2), ("1920", 2)] * 2)
    assert_role(result, ProfileRole.GLAZING_BEAD, [("829", 2), ("1819", 2)] * 2, [])
    assert [(p.width_mm, p.height_mm, p.leaf_id) for p in result.glasses] == [
        (D("820"), D("1810"), "G5:L1"), (D("820"), D("1810"), "G5:L2"),
    ]
    assert [(p.kit_sku, p.leaf_id, p.qty) for p in result.hardware_items] == [
        ("KIT-SLIDING", "G5:L1", 1), ("KIT-SLIDING", "G5:L2", 1),
    ]
    for leaf_id in ("G5:L1", "G5:L2"):
        exact = exact_weight_for_leaf(result, demo_60_params, "G5", leaf_id)
        assert exact.total_weight_kg == D("48.8868")
        assert (exact.pvc_weight_kg, exact.steel_weight_kg, exact.infill_weight_kg) == (
            D("7.0128"), D("9.6900"), D("29.6840"),
        )
        assert len([p for p in result.profile_cuts if p.leaf_id == leaf_id]) == 4
    assert [w.total_weight_kg for w in result.leaf_weights] == [D("48.89"), D("48.89")]
    assert result.panels == []


def test_g6_complete_bom_exact(demo_60_params: SystemParams) -> None:
    result = calculate_geometry(core_node("G6"), demo_60_params)
    assert_role(result, ProfileRole.FRAME, [("1206", 2), ("806", 2)],
                [("1170", 2), ("770", 2)])
    assert_role(result, ProfileRole.SASH, [("1102", 2), ("702", 2)],
                [("1066", 2), ("666", 2)])
    assert_role(result, ProfileRole.GLAZING_BEAD, [("985", 2), ("585", 2)], [])
    assert (result.glasses[0].width_mm, result.glasses[0].height_mm) == (D("976"), D("576"))
    assert result.hardware_items[0].kit_sku == "KIT-AWNING-16"
    assert [(c.sku, c.qty) for c in result.hardware_items[0].contents] == [("DEMO-STAY-16", D("2"))]
    assert exact_weight_for_leaf(result, demo_60_params, "G6").total_weight_kg == D("23.96192")
    assert result.leaf_weights[0].total_weight_kg == D("23.96")
    assert result.panels == []


def test_g7_complete_bom_exact(demo_60_params: SystemParams) -> None:
    result = calculate_geometry(core_node("G7"), demo_60_params)
    assert_role(result, ProfileRole.FRAME, [("956", 1), ("2153", 2)],
                [("920", 1), ("2120", 2)])
    assert_role(result, ProfileRole.THRESHOLD, [("830", 1)], [])
    assert_role(result, ProfileRole.SASH, [("822", 2), ("2054", 2)],
                [("786", 2), ("2018", 2)])
    assert_role(result, ProfileRole.GLAZING_BEAD, [("705", 2), ("1937", 2)], [])
    frames = [p for p in result.profile_cuts if p.role is ProfileRole.FRAME]
    assert [(p.angle_left, p.angle_right) for p in frames] == [
        (D("45.0"), D("45.0")), (D("45.0"), D("90.0")),
    ]
    threshold = next(p for p in result.profile_cuts if p.role is ProfileRole.THRESHOLD)
    assert (threshold.sku, threshold.material, threshold.angle_left, threshold.angle_right) == (
        "UMBRAL-ALU", MaterialType.ALUMINIUM, D("90.0"), D("90.0"),
    )
    panel = result.panels[0]
    assert (panel.width_mm, panel.height_mm, panel.area_m2, panel.weight_kg) == (
        D("696"), D("1928"), D("1.3419"), D("13.42"),
    )
    assert all(p.sku == "JQ-10" and p.bay_id == "G7" and p.leaf_id == panel.leaf_id
               for p in result.profile_cuts if p.role is ProfileRole.GLAZING_BEAD)
    assert result.glasses == []
    assert result.hardware_items[0].kit_sku == "KIT-DOOR-MULTIPOINT"
    assert result.hardware_items[0].contents[0].sku == "DEMO-LOCK-MULTIPOINT"
    assert exact_weight_for_leaf(result, demo_60_params, "G7").total_weight_kg == D("32.35488")
    assert result.leaf_weights[0].total_weight_kg == D("32.35")


@pytest.mark.parametrize("field,case,axis,expected", [
    ("sliding_glazing_deduction_width_mm", "G5", "width_mm", "817.00"),
    ("sliding_glazing_deduction_height_mm", "G5", "height_mm", "1807.00"),
    ("door_leaf_side_clearance_mm", "G7", "width_mm", "690.00"),
])
def test_new_authorities_are_used_independently(
    demo_60_params: SystemParams, field: str, case: str, axis: str, expected: str,
) -> None:
    params = demo_60_params.model_copy(update={field: getattr(demo_60_params, field) + D("3.00")})
    result = calculate_geometry(core_node(case), params)
    piece = result.panels[0] if case == "G7" else result.glasses[0]
    assert getattr(piece, axis) == D(expected)


def test_awning_and_turn_share_rectangular_primitive(
    demo_60_params: SystemParams, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import dekopen_engine.geometry as geometry

    original = geometry.single_rectangular_sash_geometry
    calls: list[tuple[Decimal, Decimal]] = []

    def spy(w: Decimal, h: Decimal, article: EffectiveProfileArticle, params: SystemParams) -> SashGeometry:
        calls.append((w, h))
        return original(w, h, article, params)

    monkeypatch.setattr(geometry, "single_rectangular_sash_geometry", spy)
    node = core_node("G6")
    calculate_geometry(node, demo_60_params)
    # TURN kit has a 500 mm minimum height; the finished G6 height is 696 mm.
    calculate_geometry(node.model_copy(update={"opening_type": BayOpeningType.TURN_LEFT}), demo_60_params)
    assert calls == [(D("1080"), D("680"))] * 2
