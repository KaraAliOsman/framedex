from copy import deepcopy
from decimal import Decimal

import pytest

from catalogs.family_templates import family_template, family_templates, validate_family_templates
from catalogs.value_origins import cells, resolve_origin, index_versions, index_evidence
from uuid import uuid4


def test_four_versioned_families_are_suggested_without_prices_or_supplier_identifiers():
    templates = family_templates()
    assert {item["id"] for item in templates} == {
        "pvc-casement-60-70", "pvc-sliding-60-80", "aluminium-casement-rpt", "aluminium-sliding-latam"}
    for item in templates:
        assert item["origin"] == "SUGGESTED" and item["version"] == 1 and item["prices"] == []
        assert "revisar con fabricante" in item["source_ref"]
        assert "face_width_mm" not in item["profile_defaults"]["FRAME"]
        assert not {"sku", "supplier", "unit_cost"} & item["profile_defaults"]["FRAME"].keys()
    pvc = family_template("pvc-casement-60-70")
    assert pvc["profile_defaults"]["FRAME"]["cut_rule"]["welding_loss_per_end_mm"] == "3.00"
    assert pvc["reinforcement_defaults"]["cut_deduction_mm"] == "30.00"
    assert pvc["system"]["glass_clearance_white_mm"] == "5.00"


@pytest.mark.parametrize("change", ["origin", "price", "negative", "family", "unknown", "duplicate"])
def test_template_schema_refuses_invalid_or_misrepresented_data(change):
    payload = {"schema_version": 1, "templates": family_templates()}
    first = payload["templates"][0]
    if change == "origin":
        first["origin"] = "MANUAL"
    elif change == "price":
        first["prices"] = [{"unit_cost": "1000"}]
    elif change == "negative":
        first["profile_defaults"]["FRAME"]["cut_rule"]["welding_loss_per_end_mm"] = "-1"
    elif change == "family":
        first["system"]["system_family"] = "INVENTED"
    elif change == "unknown":
        first["glazing_defaults"]["invented_rule"] = "5"
    else:
        payload["templates"].append(deepcopy(first))
    with pytest.raises(ValueError):
        validate_family_templates(payload)


def test_template_versions_are_explicit_and_callers_cannot_mutate_shared_defaults():
    first = family_template("pvc-casement-60-70", 1)
    first["system"]["depth_mm"] = "900"
    assert family_template("pvc-casement-60-70", 1)["system"]["depth_mm"] == "60.00"
    with pytest.raises(ValueError):
        family_template("pvc-casement-60-70", 2)


def test_cell_paths_flatten_rules_but_keep_ordered_tables_and_exclude_source_labels():
    assert dict(cells({"name": "Series", "depth_mm": Decimal("60"),
        "cut_rule": {"source": "reference", "welding_loss_per_end_mm": Decimal("3")},
        "dimensional_limits": [{"opening_type": "FIXED"}], "rebate_depth_mm": None})) == {
            "depth_mm": Decimal("60"), "cut_rule.welding_loss_per_end_mm": Decimal("3"),
            "dimensional_limits": [{"opening_type": "FIXED"}]}


def test_stale_or_synthetic_evidence_cannot_turn_a_cell_into_a_manual_value():
    row = {"id": "row", "depth_mm": Decimal("60"), "data_provenance": "IMPORT"}
    evidence = {"authority_table": "profile_systems", "row_id": "row", "field_name": "depth_mm",
        "review_state": "REVIEWED", "extraction_method": "MANUAL", "canonical_value": "61",
        "source_page": 14, "source_document": "Manual.pdf", "reviewed_by": "actor", "reviewed_at": "now"}
    assert resolve_origin("profile_systems", row, "depth_mm", Decimal("60"), [], [evidence])["origin"] is None
    evidence["canonical_value"] = "60"
    assert resolve_origin("profile_systems", row, "depth_mm", Decimal("60"), [], [evidence])["origin"] == "MANUAL"
    evidence["extraction_method"] = "HUMAN_CORRECTION"
    assert resolve_origin("profile_systems", row, "depth_mm", Decimal("60"), [], [evidence])["origin"] is None
    evidence["extraction_method"] = "MANUAL"
    row["data_provenance"] = "SEED_SYNTHETIC"
    assert resolve_origin("profile_systems", row, "depth_mm", Decimal("60"), [], [evidence])["origin"] is None


@pytest.mark.parametrize("value", [Decimal("60"), Decimal("60.01"), None])
def test_indexed_origins_keep_exact_value_checks_row_table_isolation_and_evidence_order(value):
    row_id = uuid4()
    row = {"id": str(row_id), "depth_mm": value, "data_provenance": "IMPORT"}
    version = {"authority_table": "profile_systems", "row_id": row_id, "field_name": "depth_mm",
        "value_numeric": Decimal("60"), "origin": "SUGGESTED", "source_ref": "Plantilla",
        "set_by": "actor", "set_at": "now", "id": uuid4()}
    versions = [{**version, "row_id": uuid4()}, {**version, "authority_table": "profile_articles"}, version]
    evidence = [{"authority_table": "profile_systems", "row_id": row_id, "field_name": "depth_mm",
        "review_state": "REVIEWED", "extraction_method": "MANUAL", "canonical_value": '"60.01"',
        "source_ref": ref, "source_document": "Manual.pdf", "reviewed_by": "reviewer", "reviewed_at": "now"}
        for ref in ("Página 1", "Página 2")]
    linear = resolve_origin("profile_systems", row, "depth_mm", value, versions, evidence)
    indexed = resolve_origin("profile_systems", row, "depth_mm", value, index_versions(versions), index_evidence(evidence))
    assert indexed == linear
    assert indexed["origin"] == ("SUGGESTED" if value == Decimal("60") else "MANUAL" if value is not None else None)
    if indexed["origin"] == "MANUAL":
        assert indexed["source_ref"] == "Página 2"
