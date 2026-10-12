"""Manufacturing regressions for reviewed family and per-profile authorities."""

import json
from decimal import Decimal as D
from pathlib import Path

import pytest
from pydantic import ValidationError

from dekopen_engine import (
    BayOpeningType, NodeType, ParametricNode, ProfileRole, SystemFamily,
    calculate_geometry, evaluate_product, make_single_unit,
)
from dekopen_engine.catalog_rules import (
    CatalogRuleError, reinforcement_required, rounded_profile_cut, validate_leaf_limits,
)
from dekopen_engine.weight import MissingFabricationAuthority
from engine.tests.catalog_families import family_cases, family_params


def node(opening: BayOpeningType = BayOpeningType.TURN_LEFT, width: str = "1000", height: str = "1400") -> ParametricNode:
    return ParametricNode(id="leaf", type=NodeType.BAY, opening_type=opening,
        width_mm=D(width), height_mm=D(height), glass_thickness_mm=D("24"),
        glass_spec="4-16-4 Float Incoloro")


def test_family_golden_is_exact_and_frozen() -> None:
    frozen = json.loads(Path(__file__).with_name("golden_catalog_families.json").read_text(encoding="utf-8"))
    assert family_cases() == frozen
    for code in ("DEMO_60", "DEMO_70"):
        cuts = frozen[f"{code}-WHITE"]["profile_cuts"]
        assert {cut["role"] for cut in cuts} >= {"FRAME", "SASH", "MULLION_V", "GLAZING_BEAD"}
    assert {cut["role"] for cut in frozen["DEMO_CORREDERA_60-WHITE"]["profile_cuts"]} >= {
        "SLIDING_SASH", "INTERLOCK", "RAIL"}


def test_casement_rejects_sliding_and_product_reports_error() -> None:
    params = family_params("DEMO_60")
    with pytest.raises(CatalogRuleError, match="Elige un sistema de corredera"):
        calculate_geometry(node(BayOpeningType.SLIDING_2L), params)
    product = make_single_unit(width_mm=D("1000"), height_mm=D("1400"),
        opening=BayOpeningType.SLIDING_2L, glass_thickness_mm=D("24"), glass_spec="4-16-4 Float Incoloro")
    result = evaluate_product(product, params)
    assert result.status.value == "INVALID"
    assert result.issues[0].code == "system_family_incompatible"
    assert result.bom is None


def test_new_family_never_accepts_flat_sliding_values() -> None:
    params = family_params("DEMO_60")
    with pytest.raises(ValidationError, match="parámetros de corredera"):
        type(params).model_validate({**params.model_dump(), "central_overlap_mm": D("40")})


def test_900_mm_white_vs_foiled_reinforcement_golden() -> None:
    params = family_params("DEMO_60")
    white = calculate_geometry(node(BayOpeningType.FIXED, "900", "900"), params)
    foil = calculate_geometry(node(BayOpeningType.FIXED, "900", "900"), params, is_foiled=True)
    assert white.reinforcements == [] and white.fittings == []
    assert [(piece.length_mm, piece.qty) for piece in foil.reinforcements] == [(D("876"), 2), (D("876"), 2)]
    assert sum(piece.qty for piece in foil.fittings) == 16
    assert all(piece.kind == "REINFORCEMENT_SCREW" for piece in foil.fittings)
    article = params.effective_profile_articles[ProfileRole.FRAME]
    assert reinforcement_required(article, D("900"), finish="DARK", is_foiled=True)
    assert reinforcement_required(article, D("1000"), finish="WHITE", is_foiled=False)


@pytest.mark.parametrize(("mode", "expected"), [("UP", "900.50"), ("DOWN", "900.00"), ("NEAREST", "900.00")])
def test_exact_profile_rounding_and_meeting_deduction(mode: str, expected: str) -> None:
    article = family_params("DEMO_60").effective_profile_articles[ProfileRole.FRAME]
    assert article.cut_rule is not None
    rule = article.cut_rule.model_copy(update={"cut_step_mm": D("0.50"), "rounding": mode, "meeting_deduction_mm": D("1")})
    assert rounded_profile_cut(D("901.24"), article.model_copy(update={"cut_rule": rule})) == D(expected)


def test_limits_are_exact_with_source_and_unknown_does_not_certify() -> None:
    params = family_params("DEMO_60")
    validate_leaf_limits(params, BayOpeningType.TURN_LEFT, bay_id="leaf", width_mm=D("1600"), height_mm=D("2500"))
    with pytest.raises(CatalogRuleError) as error:
        validate_leaf_limits(params, BayOpeningType.TURN_LEFT, bay_id="leaf", width_mm=D("1600.01"), height_mm=D("2500"))
    assert "semilla" in error.value.params["source"]
    with pytest.raises(CatalogRuleError):
        validate_leaf_limits(params, BayOpeningType.TURN_LEFT, bay_id="leaf", width_mm=D("1000"), height_mm=D("1400"), weight_kg=D("150.0001"), check_weight=True)
    with pytest.raises(MissingFabricationAuthority):
        validate_leaf_limits(params, BayOpeningType.TURN_LEFT, bay_id="leaf", width_mm=D("1000"), height_mm=D("1400"), check_weight=True)


def test_missing_cut_rule_never_uses_legacy_pvc_allowance() -> None:
    params = family_params("DEMO_60")
    articles = dict(params.effective_profile_articles)
    articles[ProfileRole.FRAME] = articles[ProfileRole.FRAME].model_copy(update={"cut_rule": None})
    with pytest.raises(MissingFabricationAuthority, match="regla de corte"):
        calculate_geometry(node(), params.model_copy(update={"effective_profile_articles": articles}))


def test_door_and_facade_family_compatibility() -> None:
    params = family_params("DEMO_60")
    with pytest.raises(CatalogRuleError):
        calculate_geometry(node(), params.model_copy(update={"system_family": SystemFamily.FACADE_FIXED}))
    with pytest.raises(CatalogRuleError):
        calculate_geometry(node(), params.model_copy(update={"system_family": SystemFamily.DOOR}))
