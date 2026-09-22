"""Manual project inputs cannot supply technical results, costs or tenant IDs."""

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from rest_framework.exceptions import APIException

from backend.tests.factories import ORG_A_ID, demo_60_params
from backend.tests.test_engine_api import g1_request
from documents.serializers import WorkshopAnnotationSerializer
from engine_api.repository import SystemParamsRepository
from engine_api.serializers import EngineCalculateRequestSerializer
from pricing.serializers import DraftPositionSerializer
from projects.serializers import PositionWriteSerializer, ProjectWriteSerializer
from projects.service import calculate_design, next_revision_code, unchanged
from projects import service
from projects.typology import derive_typology


@pytest.mark.parametrize(
    "key,value",
    [
        ("org_id", "00000000-0000-0000-0000-000000000001"),
        ("total_cost_net", "10"),
        ("total_price_gross", "1"),
        ("status", "APPROVED"),
    ],
)
def test_project_rejects_tenant_price_and_state_injection(key, value):
    serializer = ProjectWriteSerializer(data={"name": "Casa", "client_name": "Cliente", key: value})
    assert not serializer.is_valid()


@pytest.mark.parametrize("dimension", [1000, 1000.0, "249.99", "NaN", "Infinity"])
def test_position_requires_exact_valid_dimension(dimension):
    design = {**g1_request(), "nominal_width_mm": dimension}
    serializer = PositionWriteSerializer(
        data={"location_tag": "Cocina", "quantity": 1, "design": design}
    )
    assert not serializer.is_valid()


def test_position_rejects_client_bom():
    serializer = PositionWriteSerializer(
        data={
            "location_tag": "Cocina",
            "quantity": 1,
            "design": g1_request(),
            "bom": {},
        }
    )
    assert not serializer.is_valid()


def test_persisted_quotation_inputs_are_white_only_without_narrowing_engine_types():
    foiled = {**g1_request(), "color": "FOILED"}
    assert EngineCalculateRequestSerializer(data=foiled).is_valid()
    assert not PositionWriteSerializer(
        data={"location_tag": "Cocina", "quantity": 1, "design": foiled}
    ).is_valid()
    assert not DraftPositionSerializer(
        data={**foiled, "position_index": 1, "quantity": 1, "typology": "FIXED"}
    ).is_valid()
    assert not WorkshopAnnotationSerializer(
        data={"bay_id": "B1", "finish_class": "FOILED"}
    ).is_valid()


def test_calculation_matches_engine_and_inputs_are_not_changed(monkeypatch):
    monkeypatch.setattr(SystemParamsRepository, "load_visible", lambda *_: demo_60_params())
    serializer = PositionWriteSerializer(
        data={"location_tag": "Cocina", "quantity": 1, "design": g1_request()}
    )
    assert serializer.is_valid(), serializer.errors
    design = serializer.validated_data["design"]
    before = deepcopy(design)
    result = calculate_design(ORG_A_ID, design)
    assert result["glasses"][0]["width_mm"] == "910.00"
    assert result["glasses"][0]["height_mm"] == "910.00"
    assert result["calculation_hash"].startswith("sha256:")
    assert design == before
    assert isinstance(design["nominal_width_mm"], Decimal)


def test_stale_edit_is_a_conflict_not_last_writer_wins():
    current = datetime(2026, 9, 18, 12, 0, 1, tzinfo=timezone.utc)
    prior = datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.utc)
    unchanged({"updated_at": current}, current)
    with pytest.raises(APIException) as caught:
        unchanged({"updated_at": current}, prior)
    assert caught.value.status_code == 409


def test_invalid_engine_geometry_returns_domain_error_without_raw_tree_details(monkeypatch):
    monkeypatch.setattr(SystemParamsRepository, "load_visible", lambda *_: demo_60_params())

    def reject(**kwargs):
        raise ValueError("SPLIT_V node-private produces a non-positive BAY width")

    monkeypatch.setattr(service, "calculate_from_api", reject)
    with pytest.raises(APIException) as caught:
        calculate_design(ORG_A_ID, g1_request())
    assert caught.value.status_code == 400
    assert "SPLIT_V" not in str(caught.value)
    assert "node-private" not in str(caught.value)
    assert "divisiones" in str(caught.value)


@pytest.mark.parametrize(
    "opening,typology",
    [
        ("FIXED", "FIXED"),
        ("TURN_LEFT", "TURN"),
        ("TURN_RIGHT", "TURN"),
        ("TILT_TURN_LEFT", "TILT_TURN"),
        ("TILT_TURN_RIGHT", "TILT_TURN"),
        ("SLIDING_2L", "SLIDING_2L"),
        ("AWNING", "AWNING"),
        ("DOOR_ENTRY", "DOOR_ENTRY"),
    ],
)
def test_undivided_typology_is_derived_from_opening(opening, typology):
    assert derive_typology({"id": "B1", "type": "BAY", "opening_type": opening}) == typology


@pytest.mark.parametrize("split_type", ["SPLIT_V", "SPLIT_H"])
def test_any_structural_division_is_composite(split_type):
    tree = {
        "id": "S1",
        "type": split_type,
        "children": [
            {"id": "B1", "type": "BAY", "opening_type": "FIXED"},
            {"id": "B2", "type": "BAY", "opening_type": "TURN_LEFT"},
        ],
    }
    assert derive_typology(tree) == "COMPOSITE"
    tree["children"][1]["opening_type"] = "FIXED"
    assert derive_typology(tree) == "COMPOSITE"


def test_revision_sequence_is_excel_style_without_skips():
    assert next_revision_code("REV-A") == "REV-B"
    assert next_revision_code("REV-Z") == "REV-AA"
    assert next_revision_code("REV-AA") == "REV-AB"


def test_assembly_save_requires_manufacturing_complete(monkeypatch):
    from backend.tests.factories import SYSTEM_ID
    from backend.tests.test_engine_assembly import bow_product

    monkeypatch.setattr(
        SystemParamsRepository, "load_visible", lambda *_: demo_60_params()
    )
    monkeypatch.setattr(
        SystemParamsRepository, "load_coupler_articles", lambda *_: {}
    )
    design = {
        "system_id": SYSTEM_ID,
        "nominal_width_mm": Decimal("2100.00"),
        "nominal_height_mm": Decimal("1400.00"),
        "color": "WHITE",
        "parametric_tree": bow_product(),
    }
    with pytest.raises(APIException) as caught:
        calculate_design(ORG_A_ID, design)
    assert caught.value.status_code == 400
    assert "acopladores" in str(caught.value)


def test_valid_assembly_saves_with_prefixed_bom(monkeypatch):
    from backend.tests.factories import SYSTEM_ID
    from backend.tests.test_engine_assembly import COUPLER_ARTICLE, bow_product

    monkeypatch.setattr(
        SystemParamsRepository, "load_visible", lambda *_: demo_60_params()
    )
    monkeypatch.setattr(
        SystemParamsRepository,
        "load_coupler_articles",
        lambda *_: {"ACOPLE-60": COUPLER_ARTICLE},
    )
    design = {
        "system_id": SYSTEM_ID,
        "nominal_width_mm": Decimal("2100.00"),
        "nominal_height_mm": Decimal("1400.00"),
        "color": "WHITE",
        "parametric_tree": bow_product(coupler_sku="ACOPLE-60"),
    }
    result = calculate_design(ORG_A_ID, design)
    assert result["calculation_hash"].startswith("sha256:")
    assert design["nominal_width_mm"] == Decimal("2100.00")
    assert any(
        (cut["bay_id"] or "").startswith("m1|") for cut in result["profile_cuts"]
    )


def test_assembly_save_rejects_conflicting_nominal_dimensions(monkeypatch):
    from backend.tests.factories import SYSTEM_ID
    from backend.tests.test_engine_assembly import COUPLER_ARTICLE, bow_product

    monkeypatch.setattr(
        SystemParamsRepository, "load_visible", lambda *_: demo_60_params()
    )
    monkeypatch.setattr(
        SystemParamsRepository,
        "load_coupler_articles",
        lambda *_: {"ACOPLE-60": COUPLER_ARTICLE},
    )
    design = {
        "system_id": SYSTEM_ID,
        "nominal_width_mm": Decimal("2200.00"),
        "nominal_height_mm": Decimal("1400.00"),
        "color": "WHITE",
        "parametric_tree": bow_product(coupler_sku="ACOPLE-60"),
    }
    with pytest.raises(APIException) as caught:
        calculate_design(ORG_A_ID, design)
    assert caught.value.status_code == 400
    assert caught.value.get_codes() == "validation_error"
