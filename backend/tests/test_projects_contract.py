"""Manual project inputs cannot supply technical results, costs or tenant IDs."""

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from rest_framework.exceptions import APIException

from backend.tests.factories import ORG_A_ID, demo_60_params
from backend.tests.test_engine_api import g1_request
from engine_api.repository import SystemParamsRepository
from projects.serializers import PositionWriteSerializer, ProjectWriteSerializer
from projects.service import calculate_design, unchanged
from projects import service


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
