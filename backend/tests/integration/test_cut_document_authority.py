"""P13 sheet declarations and physical RT addresses under real PostgreSQL RLS."""

from copy import deepcopy
from decimal import Decimal
from uuid import uuid4

from django.db import DatabaseError, transaction
import pytest

from backend.tests.integration.test_shot09_documentary import documentary_tenant as documentary_tenant, as_user
from backend.tests.integration.test_shot08_pricing import owner_client
from backend.tests.integration.test_operator_station import setup_work
from documents.repository import documentary_backend, one, rows
from inventory.remnants import plan_remnant_addresses, record_produced_remnants
from inventory.sheet_formats import declare_format

pytestmark = pytest.mark.rls_integration


def sheet_body():
    return {"kind":"GLASS", "technical_sku":"VIDRIO-BASE", "sku":"LAMINA-P13",
            "width_mm":"2400.00", "height_mm":"1800.00", "edge_trim_mm":"10.00",
            "supplier":"Proveedor de prueba", "source":"Declaración DEMO P13 · 10-10-2026"}


def test_sheet_declaration_is_idempotent_scoped_and_not_physical_stock(documentary_tenant):
    org, other, users, _ = documentary_tenant
    manager, estimator = owner_client(users["WORKSHOP_MANAGER"]), owner_client(users["ESTIMATOR"])
    route = "/api/v1/inventory/sheet-formats/"
    headers = {"HTTP_X_ORGANIZATION_ID":str(org)}
    first = manager.post(route, sheet_body(), format="json", **headers)
    assert first.status_code == 201, first.data
    again = manager.post(route, sheet_body(), format="json", **headers)
    assert again.status_code == 200 and again.json() == first.json()
    visible = estimator.get(route, **headers)
    assert visible.status_code == 200, visible.data
    saved = visible.json()["items"][0]
    assert saved["width_mm"] == "2400.00" and saved["height_mm"] == "1800.00"
    assert saved["is_demo"] and saved["technical_sku"] == "VIDRIO-BASE"
    assert saved["source"] == sheet_body()["source"]
    assert one("SELECT count(*) AS n FROM inventory_movements WHERE org_id=%s", [org])["n"] == 0
    assert estimator.post(route, sheet_body(), format="json", **headers).status_code == 403
    assert manager.get(route, HTTP_X_ORGANIZATION_ID=str(other)).status_code == 403
    with as_user(users["WORKSHOP_MANAGER"]):
        assert rows("SELECT id FROM inventory_items WHERE org_id=%s", [other]) == []
        from production.service import _sheet_rules
        rules = _sheet_rules(org)
        rule = rules["by_glass"]["VIDRIO-BASE"][0]
        assert rule.sheet_width_mm == Decimal("2400.00")
        assert rule.edge_trim_mm == Decimal("10.00")
        assert "20" not in rules["by_thickness"]


@pytest.mark.parametrize("changes", [
    {"width_mm":"0"}, {"edge_trim_mm":"900"}, {"width_mm":"2400.001"},
    {"technical_sku":"NO-DECLARADO"}, {"source":""}, {"made_up":"field"},
])
def test_invalid_sheet_authority_never_writes(documentary_tenant, changes):
    org, _, users, _ = documentary_tenant
    client = owner_client(users["WORKSHOP_MANAGER"])
    response = client.post("/api/v1/inventory/sheet-formats/", {**sheet_body(), **changes},
                           format="json", HTTP_X_ORGANIZATION_ID=str(org))
    assert response.status_code in (400, 422), response.data
    assert one("SELECT count(*) AS n FROM inventory_items WHERE org_id=%s", [org])["n"] == 0


def test_sheet_declaration_rollback_and_rls_write_denial(documentary_tenant):
    org, other, users, _ = documentary_tenant
    data = {**sheet_body(), **{field:Decimal(sheet_body()[field])
                              for field in ("width_mm", "height_mm", "edge_trim_mm")}}
    with as_user(users["WORKSHOP_MANAGER"]), transaction.atomic():
        declare_format(org_id=org, data=data)
        transaction.set_rollback(True)
    assert rows("SELECT id FROM inventory_items WHERE org_id=%s", [org]) == []
    with as_user(users["ESTIMATOR"]), pytest.raises(DatabaseError), transaction.atomic():
        declare_format(org_id=org, data=data)
    with as_user(users["WORKSHOP_MANAGER"]), documentary_backend(), pytest.raises(DatabaseError), transaction.atomic():
        rows("INSERT INTO inventory_items(org_id,sku,name,category,unit) VALUES(%s,'RLS','RLS','GLASS','M2') RETURNING id", [other])


def planned_remnants():
    authority = one("SELECT id FROM profile_purchase_mappings WHERE org_id IS NULL LIMIT 1")["id"]
    return {"bars":{"workshop_cut_plan":[{"bar_index":1, "stock_authority_id":str(authority),
                    "stock_length_mm":"6000.00", "cuts":[]}]},
            "sheets":[{"sheet_index":1, "sheet_width_mm":"2400.00", "sheet_height_mm":"1800.00", "placements":[]}],
            "produced_bars":[{"bar_index":1, "stock_authority_id":str(authority), "remainder_mm":"2000.00"}],
            "produced_sheets":[{"sheet_index":1, "workshop_sku":"LAMINA-P13", "width_mm":"600.00", "height_mm":"400.00"}]}


def test_planned_addresses_are_not_stock_and_completion_replays_exactly(documentary_tenant):
    org, other, users, _ = documentary_tenant
    _, _, order, _ = setup_work(org, users)
    plan = planned_remnants()
    with as_user(users["WORKSHOP_MANAGER"]), documentary_backend():
        plan_remnant_addresses(org_id=org, order_id=order, plan=plan, rack_location="Rack 13")
        entries = [*plan["produced_bars"], *plan["produced_sheets"]]
        before = deepcopy(entries)
        assert [entry["code"] for entry in entries] == ["RT-000001", "RT-000002"]
        assert rows("SELECT id FROM inventory_remnants WHERE org_id=%s", [org]) == []
        plan_remnant_addresses(org_id=org, order_id=order, plan=plan, rack_location="Rack 13")
        assert entries == before
        args = {"org_id":org, "order_id":order, "produced_bars":plan["produced_bars"], "produced_sheets":plan["produced_sheets"]}
        assert record_produced_remnants(**args) == 2
        assert record_produced_remnants(**args) == 0
        saved = rows("SELECT id,rack_location,status,private.entity_code(org_id,'RT',id) AS code FROM inventory_remnants WHERE org_id=%s ORDER BY code", [org])
        assert [str(item["id"]) for item in saved] == [entry["id"] for entry in entries]
        assert [item["code"] for item in saved] == [entry["code"] for entry in entries]
        assert all(item["rack_location"] == "Rack 13" and item["status"] == "AVAILABLE" for item in saved)
        with pytest.raises(DatabaseError), transaction.atomic():
            plan_remnant_addresses(org_id=other, order_id=uuid4(), plan=planned_remnants(), rack_location="Otro tenant")


def test_planned_address_rolls_back_with_no_stock_or_counter_hole(documentary_tenant):
    org, _, users, _ = documentary_tenant
    plan = planned_remnants()
    with as_user(users["WORKSHOP_MANAGER"]), documentary_backend():
        with transaction.atomic():
            plan_remnant_addresses(org_id=org, order_id=uuid4(), plan=plan, rack_location="Rack 13")
            transaction.set_rollback(True)
        assert rows("SELECT code FROM entity_codes WHERE org_id=%s", [org]) == []
        plan_remnant_addresses(org_id=org, order_id=uuid4(), plan=planned_remnants(), rack_location="Rack 13")
        assert one("SELECT count(*) AS n FROM entity_codes WHERE org_id=%s", [org])["n"] == 2
        assert rows("SELECT id FROM inventory_remnants WHERE org_id=%s", [org]) == []
