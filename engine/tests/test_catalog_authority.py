from decimal import Decimal
import json

import pytest

from dekopen_engine.catalog_authority import process_authority_gate, section_review_facts
from dekopen_engine.models import ProfileSection


def section(**changes: object) -> ProfileSection:
    value = {"source": "POLYGON", "depth_mm": "60.00", "orientation": "EXTERIOR_DOWN",
             "local_origin": "TOP_LEFT", "polygon": [
                 {"x_mm": "0", "y_mm": "0"}, {"x_mm": "74.01", "y_mm": "0"},
                 {"x_mm": "74.01", "y_mm": "60"}, {"x_mm": "0", "y_mm": "60"}]}
    return ProfileSection.model_validate_json(json.dumps({**value, **changes}))


def test_review_measures_exact_declared_geometry() -> None:
    facts = section_review_facts(section())
    assert facts["valid"] and facts["state"] == "PASS"
    assert Decimal(facts["bounds"]["width_mm"]) == Decimal("74.01")
    assert Decimal(facts["bounds"]["height_mm"]) == Decimal("60")


def test_one_hundredth_depth_error_blocks_verification() -> None:
    assert section_review_facts(section(depth_mm="60.01"))["reasons"] == ["section_depth_mismatch"]


def test_origin_and_orientation_are_declared_review_authority() -> None:
    assert section_review_facts(section(local_origin="BOTTOM_RIGHT"))["reasons"] == ["section_origin_mismatch"]
    assert section_review_facts(section(orientation="EXTERIOR_LEFT", depth_mm="74.01"))["valid"]
    legacy = section().model_dump(mode="json")
    legacy.pop("orientation")
    legacy.pop("local_origin")
    model = ProfileSection.model_validate_json(json.dumps(legacy))
    assert model.depth_mm == Decimal("60")  # Historical load is still allowed.
    facts = section_review_facts(model)
    assert not facts["valid"] and facts["orientation"] is None
    assert "section_interpretation_missing" in facts["reasons"]


def test_unknown_section_is_not_an_invented_box() -> None:
    assert section_review_facts(None)["bounds"] is None


def test_crossing_section_remains_invalid_at_the_model_boundary() -> None:
    with pytest.raises(ValueError):
        section(polygon=[{"x_mm": "0", "y_mm": "0"}, {"x_mm": "74", "y_mm": "60"},
                         {"x_mm": "74", "y_mm": "0"}, {"x_mm": "0", "y_mm": "60"}])


@pytest.mark.parametrize("facts", [None, {}, {"profile": {}, "resolved_via": "generic_fallback"},
                                  {"profile": None, "resolved_via": "system_declared"}])
def test_undeclared_process_never_becomes_a_release_authority(facts: object) -> None:
    assert not process_authority_gate(facts)["ok"]


def test_declared_frozen_process_does_not_consult_mutable_catalog() -> None:
    assert process_authority_gate({"profile": {"id": "frozen", "version": 2},
                                   "resolved_via": "system_declared"})["ok"]
