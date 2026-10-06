"""Class expansion, boundary failures and picking are frozen manufacturing math."""

from decimal import Decimal as D
import json
from pathlib import Path
from typing import Any

import pytest

from dekopen_engine.geometry import calculate_geometry, compute_geometry
from dekopen_engine.hardware import evaluate_hardware_candidates, resolve_hardware_evaluations, NoCompatibleHardwareKit, AmbiguousHardwareKit, HardwareCandidateEvaluation
from dekopen_engine.hardware_classes import expand_hardware, hardware_cost, hardware_price_delta, hardware_picking
from dekopen_engine.hardware_machining import hardware_operations
from dekopen_engine.hardware_proposals import split_hardware_bay
from dekopen_engine.models import BayOpeningType, HardwareSelection, HardwareMachiningRule, HardwareKitRule, ParametricNode, SystemParams
from dekopen_engine.weight import ExactLeafWeight
from engine.tests.hardware_cases import hardware_cases, hardware_case_inputs
from engine.tests.test_manufacturing import project


def context() -> tuple[SystemParams, ParametricNode, dict[tuple[str, str], D], list[HardwareKitRule]]:
    _, params, node, rates = hardware_case_inputs()[0]
    kits = [kit for kit in params.available_hardware_kits if kit.opening_type == "TILT_TURN"]
    return params, node, rates, kits


def candidates(width: str = "900", height: str = "1400", weight: str = "20", **kwargs: Any) -> list[HardwareCandidateEvaluation]:
    params, _, _, kits = context()
    return evaluate_hardware_candidates(opening=BayOpeningType.TILT_TURN_LEFT,
        width_mm=D(width), height_mm=D(height), base_weight=ExactLeafWeight(D(weight), D(0), D(0)),
        params=params.model_copy(update={"available_hardware_kits": kits}), **kwargs)


def test_four_reviewed_goldens_and_heavy_sliding() -> None:
    frozen = json.loads(Path(__file__).with_name("golden_hardware_classes.json").read_text(encoding="utf-8"))
    assert hardware_cases() == frozen
    assert len(frozen) == 4
    assert all(item["resolution"]["class_code"] == "HEAVY"
        for item in frozen["corredera-pesada"]["bom"]["hardware_items"])
    low = frozen["oscilobatiente-pequena"]["bom"]["hardware_items"][0]["contents"]
    high = frozen["oscilobatiente-alta"]["bom"]["hardware_items"][0]["contents"]
    assert D(next(item["qty"] for item in high if "Punto de cierre" in item["name"])) > D(next(item["qty"] for item in low if "Punto de cierre" in item["name"]))


@pytest.mark.parametrize("height,count", [("800", 2), ("800.0000000001", 3), ("1400", 3), ("1400.0000000001", 4)])
def test_count_thresholds_length_and_mass_are_exact(height: str, count: int) -> None:
    _, _, _, kits = context()
    expansion = expand_hardware(kits[0], width_mm=D(900), height_mm=D(height), base_weight_kg=D(20))
    point = next(item for item in expansion.contents if "Punto de cierre" in item.name)
    rod = next(item for item in expansion.contents if "Cremona" in item.name)
    assert point.qty == count
    assert rod.cut_length_mm == D(height)-D(150)
    assert rod.weight_kg == (D(height)-D(150))/D(1000)*D("0.2500")
    assert rod.price_quantity == rod.cut_length_mm/D(1000)
    assert all(item.weight_kg is not None for item in expansion.contents)
    assert expansion.hardware_weight_kg == sum(item.weight_kg for item in expansion.contents if item.weight_kg is not None)


def test_class_priority_exact_mass_and_ambiguity() -> None:
    standard = candidates()[0]
    assert standard.expansion is not None
    mass = standard.expansion.hardware_weight_kg
    assert mass is not None
    exact = candidates(weight=str(standard.kit.max_leaf_weight_kg-mass))
    assert exact[0].compatible
    overweight = candidates(weight=str(standard.kit.max_leaf_weight_kg-mass+D("0.0000000001")))
    assert not overweight[0].compatible
    heavy = resolve_hardware_evaluations(overweight, opening=BayOpeningType.TILT_TURN_LEFT)[0].class_authority
    normal = resolve_hardware_evaluations(exact, opening=BayOpeningType.TILT_TURN_LEFT)[0].class_authority
    assert heavy is not None and normal is not None
    assert heavy.class_code == "HEAVY"
    assert normal.class_code == "STANDARD"
    assert exact[1].kit.class_authority is not None
    tied = exact[1].kit.class_authority.model_copy(update={"priority": 0})
    duplicate = exact[1].kit.model_copy(update={"class_authority": tied})
    from dataclasses import replace
    with pytest.raises(AmbiguousHardwareKit):
        resolve_hardware_evaluations([exact[0], replace(exact[1], kit=duplicate)], opening=BayOpeningType.TILT_TURN_LEFT)


@pytest.mark.parametrize("kwargs,axis,message", [
    ({"width":"1400","height":"800"}, "ratio", "Reduce el ancho"),
    ({"width":"400","height":"490"}, "stay", "compás"),
    ({"width":"100"}, "size", "ancho"),
    ({"height":"2600"}, "size", "alto"),
    ({"weight":"300"}, "weight", "kg"),
    ({"requested_handle_height_mm":D(5)}, "handle", "Manilla a 5 mm"),
    ({"selection":HardwareSelection(handle_code="NOT-IN-CATALOG")}, "handle", "no está declarada"),
    ({"selection":HardwareSelection(color_code="PURPLE")}, "handle", "color"),
    ({"selection":HardwareSelection(option_codes=["RC-UNKNOWN"])}, "option", "no está declarada"),
])
def test_every_constraint_reports_real_axis_and_action(kwargs: dict[str, Any], axis: str, message: str) -> None:
    evaluated = candidates(**kwargs)
    with pytest.raises(NoCompatibleHardwareKit) as caught:
        resolve_hardware_evaluations(evaluated, opening=BayOpeningType.TILT_TURN_LEFT,
            leaf_width_mm=D(kwargs.get("width","900")), leaf_height_mm=D(kwargs.get("height","1400")))
    assert caught.value.context["axis"] == axis
    assert message.casefold() in str(caught.value).casefold()


def test_options_replace_hinges_without_double_count_and_exact_cost() -> None:
    params, node, rates, _ = context()
    original = calculate_geometry(node, params)
    result = calculate_geometry(node.model_copy(update={"hardware_selection": HardwareSelection(handle_code="KEY", color_code="BLACK", option_codes=["OCULTAS", "MICRO"])}), params)
    kit = result.hardware_items[0]
    assert kit.resolution is not None
    assert kit.resolution.handle_name == "Con llave"
    assert kit.resolution.handle_color == "Negra"
    assert not any("Tapa de bisagra" in item.name for item in kit.contents)
    assert len([item for item in kit.contents if item.category == "HINGE"]) == 1
    expected = D(0)
    for component in kit.contents:
        assert component.price_quantity is not None and component.price_unit is not None
        expected += component.price_quantity*rates[(component.sku,component.price_unit)]
    assert hardware_cost([kit], rates) == expected
    assert hardware_price_delta(hardware_cost(original.hardware_items,rates), expected) == expected-hardware_cost(original.hardware_items,rates)


def test_missing_component_mass_never_certifies_a_class() -> None:
    params, node, _, kits = context()
    for kit in kits:
        assert kit.class_authority is not None
        kit.class_authority.components[0].weight_kg = None
    result = compute_geometry(node, params.model_copy(update={"available_hardware_kits":kits}), diagnostic=True)
    assert result.result is None
    assert all(candidate.weight_match is None for candidate in result.leaves[0].candidates)
    assert "missing_hardware_component_mass" in result.leaves[0].candidates[0].exact_total_weight.weight_unknown_reasons[0]


def test_twelve_position_picking_matches_component_sums() -> None:
    kits = []
    expected: dict[tuple[str, D | None, str | None], D] = {}
    for index in range(12):
        _, params, node, _ = hardware_case_inputs()[index%4]
        for item in calculate_geometry(node,params).hardware_items:
            kits.append((item, index%3+1, f"Posición {index+1}"))
            for component in item.contents:
                key = (component.sku,component.cut_length_mm,component.source)
                expected[key] = expected.get(key,D(0))+component.qty*item.qty*(index%3+1)
    picking = hardware_picking(kits)
    assert {(row["sku"],row["cut_length_mm"],row["source"]):row["quantity"] for row in picking} == expected
    assert any(row["cut_length_mm"] is not None for row in picking)


def test_declared_machining_is_never_invented_and_emission_covers_count() -> None:
    params, node, _, _ = context()
    computation, facts = project(node,params)
    assert computation.result is not None
    item = computation.result.hardware_items[0]
    gaps: list[dict[str, object]] = []
    assert hardware_operations(items=[item],fact_units=[facts],issues=gaps) == []
    assert {gap["component_sku"] for gap in gaps} == {c.sku for c in item.contents if c.machining}
    hinge = next(c for c in item.contents if c.category == "HINGE")
    hinge.machining = [HardwareMachiningRule(code="TEST", name="Bisagras", kind="HINGE_PREP", host_side="HINGE", host_scope="LEAF",
        positions_mm=[D(200),D(1000)], covered_quantity=int(hinge.qty),face="INSIDE_FACE",tool_id="drill",depth_mm=D(4),source="Fuente de ensayo")]
    gaps = []
    ops = hardware_operations(items=[item],fact_units=[facts],issues=gaps)
    assert len(ops) == 2 and all(op.kind.value == "HINGE_PREP" for op in ops)
    assert not any(gap["component_sku"] == hinge.sku for gap in gaps)
    hinge.machining[0].covered_quantity = 1
    gaps = []
    assert hardware_operations(items=[item],fact_units=[facts],issues=gaps) == []
    assert any("cobertura" in str(gap["detail"]) for gap in gaps)


def test_too_heavy_leaf_can_offer_only_engine_accepted_split() -> None:
    params, node, _, _ = context()
    node = node.model_copy(update={"width_mm":D(1500),"height_mm":D(2300)})
    calculation = compute_geometry(node,params,diagnostic=True)
    alternative = split_hardware_bay(node,params,bay_id=node.id,dimensions=calculation.node_dimensions)
    assert alternative is not None
    tree, result = alternative
    assert len(tree.children) == len(result.hardware_items) == 2
    assert all(item.resolution is not None and item.resolution.exact_leaf_weight_kg is not None for item in result.hardware_items)


def test_catalog_limit_diagnostic_offers_split_without_accepting_invalid_bom() -> None:
    from dekopen_engine.catalog_rules import CatalogRuleError
    params,node,_,_ = context()
    invalid = node.model_copy(update={"width_mm":D(1800),"height_mm":D(2300)})
    with pytest.raises(CatalogRuleError):
        calculate_geometry(invalid,params)
    facts = compute_geometry(invalid,params,diagnostic=True,diagnose_catalog_limits=True)
    assert facts.result is None and facts.catalog_violations
    alternative = split_hardware_bay(invalid,params,bay_id=node.id,dimensions=facts.node_dimensions)
    assert alternative is not None
    assert len(alternative[1].hardware_items)==2


def test_height_failure_keeps_editable_diagnostic_but_never_validates() -> None:
    params,node,_,_ = context()
    bad = node.model_copy(update={"handle_height_mm":D(5)})
    facts = compute_geometry(bad,params,diagnostic=True)
    assert facts.result is None
    assert facts.leaves[0].candidates[0].expansion is not None
    with pytest.raises(NoCompatibleHardwareKit,match="Manilla"):
        calculate_geometry(bad,params)
