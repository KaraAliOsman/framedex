"""Synthetic reference-window corrections, never manufacturer catalog facts."""

from decimal import Decimal as D

from dekopen_engine.calibration import measurement_comparison, propose_calibration
from dekopen_engine.snapshot import JsonValue, result_payload
from engine.tests.catalog_families import family_params
from engine.tests.test_gold_cases_catalog_families import node


def calibration_cases() -> dict[str, JsonValue]:
    params = family_params("DEMO_60")
    root = node(width="1200", height="1100")
    cases: dict[str, JsonValue] = {}
    for key, measurement, target, field in (
        ("hoja_mas_2", "profile_cuts:2:length_mm", "1104", "sash_overlap_mm"),
        ("refuerzo_menos_2", "reinforcements:0:length_mm", "1174", "reinforcement_rule.cut_deduction_mm"),
        ("vidrio_menos_2", "glasses:0:width_mm", "968", "glass_clearance_white_mm"),
        ("junquillo_menos_2", "profile_cuts:4:length_mm", "977", "cut_add_mm"),
    ):
        proposal = next(item for item in propose_calibration(root, params, finish="WHITE",
            measurement_key=measurement, target_mm=D(target)) if item.parameter.field == field)
        cases[key] = {"parameter": {"resource": proposal.parameter.resource,
            "field": field, "sku": proposal.parameter.sku,
            "glass_thickness_mm": str(proposal.parameter.glass_thickness_mm) if proposal.parameter.glass_thickness_mm else None,
            "before": str(proposal.parameter.previous), "after": str(proposal.value)},
            "measurement": measurement, "target_mm": target,
            "comparison": list[JsonValue](measurement_comparison(proposal.result, {measurement: D(target)})),
            "result": result_payload(proposal.result)}
    return cases
