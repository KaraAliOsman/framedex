"""Finish authority changes manufacturing and cost, without rewriting history."""

from copy import deepcopy
from decimal import Decimal as D
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from dekopen_engine.catalog_rules import CatalogRuleError
from dekopen_engine.finish_models import FinishAuthority
from dekopen_engine.finishes import finish_surcharge, prepare_finish, finish_selling_delta
from dekopen_engine.geometry import calculate_geometry, compute_geometry
from dekopen_engine.snapshot import calculation_response
from dekopen_engine.weight import MissingFabricationAuthority
from engine.tests.finish_cases import finish_cases, finish_context


def test_reviewed_finish_goldens_and_forced_steel() -> None:
    frozen = json.loads(Path(__file__).with_name("golden_finishes.json").read_text(encoding="utf-8"))
    assert finish_cases() == frozen
    assert frozen["pvc-blanco"]["bom"]["reinforcements"] == []
    foiled = frozen["pvc-nogal-exterior"]["bom"]
    assert sum(piece["qty"] for piece in foiled["reinforcements"]) == 4
    assert foiled["finish"]["interior"]["code"] == "WHITE"
    assert foiled["finish"]["exterior"]["code"] == "WALNUT"
    assert all(cut["commercial_sku"].endswith("-WHITE_WALNUT") for cut in foiled["profile_cuts"])
    assert D(frozen["pvc-nogal-exterior"]["surcharge"]) == sum(D(cut["length_mm"])*cut["qty"] for cut in foiled["profile_cuts"])*D("0.75")
    assert D(frozen["pvc-antracita-interior"]["surcharge"]) == D(12500)
    assert D(frozen["pvc-coextruido"]["surcharge"]) == D(6500)


@pytest.mark.parametrize("baseline,proposed,expected", [
    ("100000.123456789123456789123456789", "106500.123456789123456789123456789", "6500"),
    ("500000", "500000", "0"),
    ("106500.123456789123456789123456789", "100000.123456789123456789123456789", "-6500"),
])
def test_gold_finish_selling_delta_keeps_signed_long_precision(baseline: str, proposed: str, expected: str) -> None:
    assert finish_selling_delta(D(baseline), D(proposed)) == D(expected)


def test_invalid_pair_and_finish_size_explain_cause_action_and_source() -> None:
    params, node = finish_context()
    with pytest.raises(CatalogRuleError, match="interior/exterior no está permitida") as error:
        calculate_geometry(node, params, finish="CREAM_WALNUT")
    assert error.value.params["source"]
    with pytest.raises(CatalogRuleError, match="supera 6000") as error:
        calculate_geometry(node.model_copy(update={"width_mm": D(6001)}), params, finish="WHITE_WALNUT")
    assert error.value.code == "finish_size_exceeded"
    assert error.value.params["maximum_mm"] == "6000"


def test_missing_profile_sku_or_reinforcement_never_falls_back() -> None:
    params, node = finish_context()
    with pytest.raises(MissingFabricationAuthority, match="falta el SKU"):
        calculate_geometry(node, params.model_copy(update={"finish_profile_skus": {}}), finish="WHITE_WALNUT")
    articles = {role: article.model_copy(update={"reinforcement_rule": None}) for role, article in params.effective_profile_articles.items()}
    with pytest.raises(MissingFabricationAuthority, match="exige refuerzo"):
        prepare_finish(params.model_copy(update={"effective_profile_articles": articles}), "WHITE_WALNUT")


@pytest.mark.parametrize("field,value", [("linear_rgb", ["1.00000001", "0", "0"]),
    ("linear_rgb", [0.1, "0", "0"]), ("gloss", "-0.0001"), ("source", " "),
    ("texture_path", "/catalog-assets/../secret")])
def test_untrusted_color_authority_is_exact_and_bounded(field: str, value: object) -> None:
    params, _ = finish_context()
    assert params.finish_authority is not None
    raw = deepcopy(params.finish_authority.model_dump(mode="json"))
    raw["colors"][0][field] = value
    with pytest.raises(ValidationError):
        FinishAuthority.model_validate_json(json.dumps(raw))


def test_currency_and_declared_zero_and_unknown_lead_time() -> None:
    params, node = finish_context("DEMO_ALU_PRACTICABLE")
    result = calculate_geometry(node, params, finish="ANODIZED_SILVER")
    assert result.finish is not None and params.finish_authority is not None
    assert result.finish.combination.extra_lead_days is None
    with pytest.raises(ValueError, match="moneda"):
        finish_surcharge(result, D(100), "USD")
    raw = params.finish_authority.model_dump(mode="json")
    raw["combinations"][0]["surcharge"]["amount"] = "0.0000000001"
    with pytest.raises(ValidationError, match="importe cero"):
        FinishAuthority.model_validate_json(json.dumps(raw))


def test_optimizer_keeps_bicolor_profiles_and_declared_steel_separate() -> None:
    from dekopen_engine.cutting import pieces_from_result, CutMaterial
    params, node = finish_context()
    result = calculate_geometry(node, params, finish="WHITE_WALNUT")
    pieces = pieces_from_result(result, color="WHITE_WALNUT", reinforcement_skus={})
    assert {piece.color for piece in pieces if piece.material == CutMaterial.PVC} == {"WHITE_WALNUT"}
    assert {piece.color for piece in pieces if piece.material == CutMaterial.STEEL} == {"WHITE"}


@pytest.mark.parametrize("case,system,finish", [
    ("pvc-blanco", "DEMO_60", "WHITE"),
    ("pvc-nogal-exterior", "DEMO_60", "WHITE_WALNUT"),
    ("pvc-antracita-interior", "DEMO_60", "ANTHRACITE_WHITE"),
    ("pvc-coextruido", "DEMO_60", "COEX_GREY"),
    ("aluminio-ral", "DEMO_ALU_PRACTICABLE", "WHITE_RAL7016"),
    ("aluminio-anodizado", "DEMO_ALU_PRACTICABLE", "ANODIZED_SILVER"),
    ("aluminio-madera", "DEMO_ALU_PRACTICABLE", "WOOD_WALNUT"),
])
def test_inspector_and_layout_geometry_keep_the_reviewed_finish_bom_and_hash(
    case: str, system: str, finish: str,
) -> None:
    params, node = finish_context(system)
    frozen = json.loads(Path(__file__).with_name("golden_finishes.json").read_text(encoding="utf-8"))
    diagnostic = compute_geometry(node, params, diagnostic=True, finish=finish)
    strict = calculate_geometry(node, params, finish=finish)
    assert diagnostic.result is not None
    assert diagnostic.result.model_dump(mode="json") == frozen[case]["bom"]
    request = {"system_id": system, "color": finish, "nominal_width_mm": "900.00",
        "nominal_height_mm": "850.00", "parametric_tree": {"id": "vano", "type": "BAY"}}
    assert calculation_response(request, diagnostic.result) == calculation_response(request, strict)


def test_handle_color_compatibility_checks_catalog_code() -> None:
    from dekopen_engine.finishes import finish_result
    from engine.tests.hardware_cases import hardware_case_inputs
    _, hardware_params, hardware_node, _ = hardware_case_inputs()[0]
    hardware = calculate_geometry(hardware_node, hardware_params).hardware_items
    params, node = finish_context()
    result = calculate_geometry(node, params, finish="WHITE_WALNUT")
    selected = result.model_copy(update={"hardware_items": hardware})
    assert finish_result(selected, params, "WHITE_WALNUT").hardware_items
    forbidden = []
    for item in hardware:
        assert item.resolution is not None
        forbidden.append(item.model_copy(update={"resolution": item.resolution.model_copy(update={"handle_color_code": "BRONZE"})}))
    with pytest.raises(CatalogRuleError, match="manilla no está permitido"):
        finish_result(selected.model_copy(update={"hardware_items": forbidden}), params, "WHITE_WALNUT")
