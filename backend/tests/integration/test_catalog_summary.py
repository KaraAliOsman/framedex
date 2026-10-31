"""Catalog discovery keeps exact v2 gates without rebuilding legacy diagnostics."""

import pytest

from catalogs import readiness, service
from catalogs.use_levels import series_use
from catalogs import use_levels

from .test_catalog_series_sheet import create
from .test_shot08_pricing import owner_client
from .test_shot09_documentary import as_user, documentary_tenant as documentary_tenant

pytestmark = pytest.mark.rls_integration


def test_summary_preserves_exact_levels_tenant_scope_and_price_blockers(documentary_tenant, monkeypatch):
    org, other, users, foreign = documentary_tenant
    with as_user(users["OWNER"]):
        sheet = create(org, users["OWNER"])
        expected = series_use(org, sheet["id"])
    def unexpected_legacy(*args, **kwargs):
        raise AssertionError("summary must not rebuild the deprecated workshop ladder")
    monkeypatch.setattr(readiness, "catalog_readiness", unexpected_legacy)
    client = owner_client(users["OWNER"])
    result = client.get("/api/v1/catalogs/systems/?summary=true", HTTP_X_ORGANIZATION_ID=str(org))
    assert result.status_code == 200, result.data
    found = next(item for item in result.json()["items"] if item["id"] == str(sheet["id"]))
    assert found["usage"] == expected
    assert found["usage"]["level"] == "DRAWABLE"
    assert not found["readiness"]["quote_ready"]
    assert any(item["field"] == "prices" for item in found["usage"]["pending"])
    assert "levels" not in found["readiness"]
    foreign_result = owner_client(foreign).get("/api/v1/catalogs/systems/?summary=true", HTTP_X_ORGANIZATION_ID=str(other))
    assert foreign_result.status_code == 200, foreign_result.data
    assert str(sheet["id"]) not in {item["id"] for item in foreign_result.json()["items"]}


def test_default_list_still_requests_legacy_diagnostics_and_filters_are_strict(documentary_tenant, monkeypatch):
    org, _, users, _ = documentary_tenant
    calls = []
    def legacy(system_id, org_id):
        calls.append((system_id, org_id))
        return {"quote_ready": False, "scope": "LEGACY-COMPAT", "reasons": ["technical_catalog"]}
    monkeypatch.setattr(readiness, "catalog_readiness", legacy)
    with as_user(users["OWNER"]):
        found = service.list_rows(service.SYSTEMS, org)
    assert found and len(calls) == len(found)
    assert all(item["readiness"]["scope"] == "LEGACY-COMPAT" for item in found)
    client = owner_client(users["OWNER"])
    for path in ("systems/?summary=maybe", "systems/?is_demo=maybe", "systems/?owned_only=maybe", "systems/?system_id=unknown",
            "articles/?summary=true", "articles/?is_demo=false"):
        result = client.get("/api/v1/catalogs/" + path, HTTP_X_ORGANIZATION_ID=str(org))
        assert result.status_code == 400, result.data


def test_example_filter_runs_before_levels_and_preserves_tenant_visibility(documentary_tenant, monkeypatch):
    org, other, users, foreign = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet = create(org, actor)
    original = use_levels.series_use
    evaluated = []
    def measured(org_id, system_id, **kwargs):
        evaluated.append(str(system_id))
        return original(org_id, system_id, **kwargs)
    monkeypatch.setattr(use_levels, "series_use", measured)
    client = owner_client(actor)
    path = "/api/v1/catalogs/systems/?summary=true&is_demo="
    real = client.get(path + "false", HTTP_X_ORGANIZATION_ID=str(org))
    assert real.status_code == 200, real.data
    visible = {item["id"] for item in real.json()["items"]}
    assert str(sheet["id"]) in visible
    assert all(not item["is_demo"] for item in real.json()["items"])
    assert set(evaluated) == visible and len(evaluated) == len(visible)
    evaluated.clear()
    examples = client.get(path + "true", HTTP_X_ORGANIZATION_ID=str(org))
    assert examples.status_code == 200, examples.data
    assert examples.json()["items"]
    assert all(item["is_demo"] for item in examples.json()["items"])
    assert str(sheet["id"]) not in evaluated
    other_result = owner_client(foreign).get(path + "false", HTTP_X_ORGANIZATION_ID=str(other))
    assert other_result.status_code == 200, other_result.data
    assert str(sheet["id"]) not in {item["id"] for item in other_result.json()["items"]}
    owned = client.get(path + "false&owned_only=true", HTTP_X_ORGANIZATION_ID=str(org))
    assert owned.status_code == 200, owned.data
    assert {item["id"] for item in owned.json()["items"]} == {str(sheet["id"])}
    assert all(not item["is_global"] and not item["read_only"] for item in owned.json()["items"])
