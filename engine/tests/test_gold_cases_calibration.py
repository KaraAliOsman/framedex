"""Exact reference-window proposals and protection against invented outputs."""

from dataclasses import replace
from decimal import Decimal as D
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from dekopen_engine import ProfileRole, calculate_geometry
from dekopen_engine.calibration import (
    adjusted_params, measurement_comparison, measurements, physical_reference,
    propose_calibration,
)
from engine.tests.calibration_cases import calibration_cases
from engine.tests.catalog_families import family_params
from engine.tests.test_gold_cases_catalog_families import node


def test_calibration_golden_is_exact_and_frozen() -> None:
    frozen = json.loads(Path(__file__).with_name("golden_calibration.json").read_text(encoding="utf-8"))
    assert calibration_cases() == frozen
    assert frozen["hoja_mas_2"]["parameter"]["after"] == "9.00"
    assert frozen["refuerzo_menos_2"]["parameter"]["after"] == "32.00"
    assert frozen["vidrio_menos_2"]["parameter"]["after"] == "4.00"
    assert frozen["junquillo_menos_2"]["parameter"]["after"] == "7.00"


def test_proposals_require_human_choice_and_recalculate_all_affected_pieces() -> None:
    params = family_params("DEMO_60")
    root = node(width="1200", height="1100")
    before = params.model_dump_json()
    proposals = propose_calibration(root, params, finish="WHITE",
        measurement_key="profile_cuts:2:length_mm", target_mm=D("1104"))
    assert len(proposals) > 1  # One measurement cannot identify the physical cause.
    assert {item.parameter.field for item in proposals} >= {
        "sash_overlap_mm", "cut_rule.welding_loss_per_end_mm"}
    for item in proposals:
        assert item.result == calculate_geometry(root, adjusted_params(params, item.parameter, item.value),
            finish="WHITE")
        assert item.result.profile_cuts[2].length_mm == D("1104")
    selected = next(item for item in proposals if item.parameter.field == "sash_overlap_mm")
    assert selected.result.profile_cuts[3].length_mm == D("1004")
    assert selected.result.glasses[0].width_mm == D("972")
    assert selected.result.reinforcements[2].length_mm == D("1074")
    assert params.model_dump_json() == before


@pytest.mark.parametrize("target", [D("1102"), D("1102.005"), D("999999999999999999999999999999999999")])
def test_equal_unrepresentable_and_out_of_range_targets_make_no_proposals(target: D) -> None:
    assert propose_calibration(node(width="1200", height="1100"), family_params("DEMO_60"),
        finish="WHITE", measurement_key="profile_cuts:2:length_mm", target_mm=target) == ()


@pytest.mark.parametrize("target", [D("0"), D("-1"), D("NaN"), D("Infinity")])
def test_invalid_manual_measure_never_enters_comparison_or_proposals(target: D) -> None:
    params = family_params("DEMO_60")
    root = node()
    with pytest.raises(ValueError, match="decimal positivo"):
        propose_calibration(root, params, finish="WHITE", measurement_key="profile_cuts:0:length_mm", target_mm=target)
    with pytest.raises(ValueError, match="positiva y exacta"):
        measurement_comparison(calculate_geometry(root, params), {"profile_cuts:0:length_mm": target})


def test_stale_keys_and_non_decimal_input_are_rejected() -> None:
    params = family_params("DEMO_60")
    root = node()
    with pytest.raises(ValueError, match="despiece actual"):
        propose_calibration(root, params, finish="WHITE", measurement_key="profile_cuts:900:length_mm", target_mm=D("1"))
    with pytest.raises(ValueError, match="ya no pertenece"):
        measurement_comparison(calculate_geometry(root, params), {"removed": D("1")})
    with pytest.raises(ValueError, match="decimal positivo"):
        propose_calibration(root, params, finish="WHITE", measurement_key="profile_cuts:0:length_mm", target_mm=1)  # type: ignore[arg-type]


def test_comparison_preserves_quantities_angles_and_exact_signed_difference() -> None:
    result = calculate_geometry(node(width="1200", height="1100"), family_params("DEMO_60"))
    compared = measurement_comparison(result, {"profile_cuts:0:length_mm": D("1206.01"),
        "reinforcements:0:length_mm": D("1174"), "glasses:0:width_mm": D("970")})
    assert len({row["key"] for row in compared}) == len(compared) == len(measurements(result))
    assert compared[0]["difference_mm"] == "0.01"
    assert compared[0]["quantity"] == 2 and compared[0]["angle_left"] == "45.0"
    assert next(row for row in compared if row["key"] == "reinforcements:0:length_mm")["difference_mm"] == "-2.00"
    assert next(row for row in compared if row["key"] == "glasses:0:width_mm")["matches"] is True
    assert compared[1]["matches"] is None


def test_candidate_keeps_full_model_constraints_and_requires_a_current_profile() -> None:
    params = family_params("DEMO_60")
    proposal = propose_calibration(node(), params, finish="WHITE",
        measurement_key="reinforcements:0:length_mm", target_mm=D("974"))[0]
    with pytest.raises(ValidationError):
        adjusted_params(params, proposal.parameter, D("-1"))
    with pytest.raises(ValueError, match="ya no pertenece"):
        adjusted_params(params, replace(proposal.parameter, sku="removed"), D("1"))


def test_signed_bead_addition_and_finish_specific_glass_rule() -> None:
    params = family_params("DEMO_60")
    proposals = propose_calibration(node(width="1200", height="1100"), params, finish="FOILED",
        measurement_key="glasses:0:width_mm", target_mm=D("964"))
    assert len(proposals) == 1
    assert proposals[0].parameter.field == "glass_clearance_foil_mm"
    assert proposals[0].result.glasses[0].width_mm == D("964")
    bead = propose_calibration(node(width="1200", height="1100"), params, finish="WHITE",
        measurement_key="profile_cuts:4:length_mm", target_mm=D("967"))
    assert len(bead) == 1 and bead[0].value == D("-3")


def test_rounding_plateau_never_yields_an_approximate_cut() -> None:
    params = family_params("DEMO_60")
    articles = params.effective_profile_articles.copy()
    article = articles[ProfileRole.SASH]
    assert article.cut_rule is not None
    articles[ProfileRole.SASH] = article.model_copy(update={"cut_rule": article.cut_rule.model_copy(
        update={"cut_step_mm": D("5")})})
    params = type(params).model_validate({**params.model_dump(), "effective_profile_articles": articles})
    assert propose_calibration(node(width="1200", height="1100"), params, finish="WHITE",
        measurement_key="profile_cuts:2:length_mm", target_mm=D("1104")) == ()


def test_reference_keeps_every_physical_output() -> None:
    result = calculate_geometry(node(), family_params("DEMO_60"))
    reference = physical_reference(result)
    assert "assumptions" not in reference
    assert set(reference) == set(result.model_dump()) - {"assumptions"}
    assert reference["profile_cuts"] and reference["glasses"] and reference["fittings"]
