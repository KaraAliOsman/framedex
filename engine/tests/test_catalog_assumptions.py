"""Suggested values are visible only where calculation actually consumes them."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest

from dekopen_engine.geometry import calculate_geometry
from dekopen_engine.models import CatalogValueOrigin, ParametricNode, ProfileRole, SystemParams
from dekopen_engine.product import evaluate_product
from engine.tests.test_product import COUPLER_ARTICLE, bow_3, with_couplers


def origin(scope: str, key: str, rule: str, value: str = "5.00", **kwargs: str) -> CatalogValueOrigin:
    return CatalogValueOrigin.model_validate({"scope": scope, "key": key, "rule": rule,
        "value": value, "origin": "SUGGESTED", **kwargs})


def test_fixed_excludes_unconsumed_leaf_door_color_and_other_bead_rules(demo_60_params: SystemParams, g1_node: ParametricNode) -> None:
    params = demo_60_params.model_copy(update={"value_origins": (
        origin("SYSTEM", "", "glass_clearance_white_mm", "3.00"),
        origin("SYSTEM", "", "glass_clearance_foil_mm"),
        origin("SYSTEM", "", "door_threshold_mm"),
        origin("SYSTEM", "", "sash_overlap_mm"),
        origin("SYSTEM", "", "depth_mm"),
        origin("PROFILE", "MARCO", "welding_loss_mm", "6.00"),
        origin("PROFILE", "HOJA", "welding_loss_mm"),
        origin("GLAZING", "4", "cut_add_mm", "9.00"),
        origin("GLAZING", "24", "cut_add_mm"),
        origin("HARDWARE", "UNUSED", "max_leaf_weight_kg"),
    )})
    result = calculate_geometry(g1_node, params)
    assert {item.rule for item in result.assumptions} == {
        "SYSTEM:glass_clearance_white_mm", "PROFILE:MARCO:welding_loss_mm", "GLAZING:4:cut_add_mm"}
    assert all(item.origin == "SUGGESTED" for item in result.assumptions)
    assert result.model_dump(exclude={"assumptions"}) == calculate_geometry(g1_node, demo_60_params).model_dump()


def test_insulating_glass_uses_total_package_for_bead_not_net_glass(demo_60_params: SystemParams, g2_node: ParametricNode) -> None:
    params = demo_60_params.model_copy(update={"value_origins": (
        origin("GLAZING", "24", "cut_add_mm"), origin("GLAZING", "8", "cut_add_mm"),
    )})
    result = calculate_geometry(g2_node, params)
    assert result.glasses[0].thickness_net_mm == Decimal("8")
    assert [item.rule for item in result.assumptions] == ["GLAZING:24:cut_add_mm"]


def test_confirmed_values_never_become_assumptions(demo_60_params: SystemParams, g1_node: ParametricNode) -> None:
    params = demo_60_params.model_copy(update={"value_origins": (
        origin("SYSTEM", "", "glass_clearance_white_mm", origin="WORKSHOP"),
        origin("PROFILE", "MARCO", "face_width_mm", origin="MANUAL"),
    )})
    assert "assumptions" not in calculate_geometry(g1_node, params).model_dump()


def test_structured_cut_does_not_report_unused_legacy_welding(demo_60_params: SystemParams, g1_node: ParametricNode) -> None:
    from dekopen_engine.models import ProfileCutRule

    frame = demo_60_params.effective_profile_articles[ProfileRole.FRAME]
    frame = frame.model_copy(update={"cut_rule": ProfileCutRule(angle_degrees=45,
        welding_loss_per_end_mm=Decimal("3"), joint_deduction_per_end_mm=Decimal("0"),
        meeting_deduction_mm=Decimal("0"), cut_step_mm=Decimal("0.01"), rounding="UP", source="Test")})
    params = demo_60_params.model_copy(update={
        "effective_profile_articles": {**demo_60_params.effective_profile_articles, ProfileRole.FRAME: frame},
        "value_origins": (origin("PROFILE", "MARCO", "cut_rule.welding_loss_per_end_mm", "3.00"),
            origin("PROFILE", "MARCO", "welding_loss_mm", "6.00"))})
    result = calculate_geometry(g1_node, params)
    assert [item.rule for item in result.assumptions] == ["PROFILE:MARCO:cut_rule.welding_loss_per_end_mm"]


def test_assembly_and_modules_preserve_deduplicated_assumptions(demo_60_params: SystemParams) -> None:
    params = demo_60_params.model_copy(update={"value_origins": (
        origin("SYSTEM", "", "glass_clearance_white_mm", "3.00"),
        origin("SYSTEM", "", "depth_mm", "60.00"))})
    result = evaluate_product(with_couplers(bow_3()), params, coupler_articles={"ACOPLE-60": COUPLER_ARTICLE})
    assert result.bom is not None
    assert [item.rule for item in result.bom.assumptions] == ["SYSTEM:depth_mm", "SYSTEM:glass_clearance_white_mm"]
    assert len(result.modules) == 3


def test_failed_or_concurrent_calculations_do_not_leak_trace(demo_60_params: SystemParams, g1_node: ParametricNode) -> None:
    params = demo_60_params.model_copy(update={"value_origins": (
        origin("SYSTEM", "", "glass_clearance_white_mm"),)})
    with pytest.raises(ValueError):
        calculate_geometry(g1_node.model_copy(update={"width_mm": Decimal("1")}), params)
    with ThreadPoolExecutor(max_workers=2) as executor:
        suggested = executor.submit(calculate_geometry, g1_node, params)
        baseline = executor.submit(calculate_geometry, g1_node, demo_60_params)
        assert len(suggested.result().assumptions) == 1
        assert "assumptions" not in baseline.result().model_dump()
    assert "assumptions" not in calculate_geometry(g1_node, demo_60_params).model_dump()


def test_round_trip_retains_origins_and_legacy_serialization(demo_60_params: SystemParams, g1_node: ParametricNode) -> None:
    assert "value_origins" not in demo_60_params.model_dump()
    params = demo_60_params.model_copy(update={"value_origins": (
        origin("SYSTEM", "", "glass_clearance_white_mm"),)})
    restored = SystemParams.model_validate_json(params.model_dump_json())
    assert restored.value_origins == params.value_origins
    assert calculate_geometry(g1_node, restored).assumptions == calculate_geometry(g1_node, params).assumptions
