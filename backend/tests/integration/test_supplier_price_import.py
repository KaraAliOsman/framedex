"""The reviewed whole file is applied atomically by its tenant's owner."""

from datetime import date
from decimal import Decimal
import json
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
import pytest

from pricing.repository import admin_write, one, rows
from backend.tests.test_supplier_prices import MAPPING, csv_file
from .test_shot08_pricing import (as_user, commercial_rows as commercial_rows, owner_client)

pytestmark = pytest.mark.rls_integration
BASE = "/api/v1/pricing/supplier-prices/"


def new_list(org):
    return admin_write("cost-lists", org, {"supplier_name": "Proveedor sintético", "currency": "CLP",
        "valid_from": date(2026, 10, 21), "is_active": True}, "Lista para prueba de mapeo")["id"]


def upload(**overrides):
    return {"file": SimpleUploadedFile("precios.csv", csv_file()), "mapping": json.dumps(MAPPING),
        "decimal_separator": ",", "reason": "Precios revisados por el dueño", "apply": "false", **overrides}


def test_preview_ten_rows_changes_nothing_and_click_imports_every_row_with_audit(commercial_rows):
    org, _, users = commercial_rows
    with as_user(users["OWNER"]):
        list_id = new_list(org)
    client = owner_client(users["OWNER"])
    inspected = client.post(BASE + "inspect/", {"file": upload()["file"]}, format="multipart")
    assert inspected.status_code == 200 and inspected.json()["total"] == 12
    preview = client.post(BASE + "review/", upload(cost_list_id=str(list_id)), format="multipart")
    assert preview.status_code == 200, preview.data
    assert len(preview.json()["items"]) == 10 and preview.json()["total"] == 12
    assert all(item["origin"] == "WORKSHOP" for item in preview.json()["items"])
    assert rows("SELECT id FROM public.cost_list_items WHERE cost_list_id=%s", [list_id]) == []
    applied = client.post(BASE + "review/", upload(cost_list_id=str(list_id), apply="true",
        review_token=preview.json()["review_token"]), format="multipart")
    assert applied.status_code == 200 and applied.json()["applied"], applied.data
    with as_user(users["OWNER"]):
        saved = rows("SELECT id,sku,unit_cost FROM public.cost_list_items WHERE cost_list_id=%s ORDER BY sku", [list_id])
        assert len(saved) == 12 and saved[0]["sku"] == "000" and saved[-1]["unit_cost"] == Decimal("1234.5678")
        audit = one("SELECT reason,actor_user_id FROM public.price_audit_logs WHERE entity_id=%s", [saved[-1]["id"]])
        assert "precios.csv" in audit["reason"] and "SHA256" in audit["reason"]
        assert audit["actor_user_id"] == users["OWNER"]


@pytest.mark.parametrize("change", ["missing", "file", "mapping", "list", "reason"])
def test_confirmation_is_bound_to_the_exact_review_and_cannot_write_partial_rows(commercial_rows, change):
    org, _, users = commercial_rows
    with as_user(users["OWNER"]):
        list_id, other_list = new_list(org), new_list(org)
    client = owner_client(users["OWNER"])
    preview = client.post(BASE + "review/", upload(cost_list_id=str(list_id)), format="multipart").json()
    changes = {"missing": {"review_token": ""},
        "file": {"file": SimpleUploadedFile("precios.csv", csv_file(price="2,0000"))},
        "mapping": {"decimal_separator": "."}, "list": {"cost_list_id": str(other_list)},
        "reason": {"reason": "Otro motivo"}}[change]
    response = client.post(BASE + "review/", upload(cost_list_id=str(list_id), apply="true",
        review_token=preview["review_token"]) | changes, format="multipart")
    assert response.status_code in (400, 409, 422), response.data
    assert rows("SELECT id FROM public.cost_list_items WHERE cost_list_id IN (%s,%s)", [list_id, other_list]) == []


def test_duplicate_existing_code_rejects_the_whole_file(commercial_rows):
    org, _, users = commercial_rows
    with as_user(users["OWNER"]):
        list_id = new_list(org)
        admin_write("cost-items", org, {"cost_list_id": list_id, "sku": "011", "item_type": "PROFILE",
            "unit": "BAR", "unit_cost": Decimal("9")}, "Costo existente")
    client = owner_client(users["OWNER"])
    response = client.post(BASE + "review/", upload(cost_list_id=str(list_id)), format="multipart")
    assert response.status_code == 422 and "011" in response.json()["error"]["detail"]
    assert one("SELECT count(*) AS n FROM public.cost_list_items WHERE cost_list_id=%s", [list_id])["n"] == 1


def test_cost_lists_and_raw_previews_never_cross_tenants_or_roles(commercial_rows):
    org, other, users = commercial_rows
    foreign = uuid4()
    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO public.tenancy_memberships(org_id,user_id,role) VALUES(%s,%s,'OWNER')", [other, foreign])
    with as_user(foreign):
        foreign_list = new_list(other)
    with as_user(users["OWNER"]):
        list_id = new_list(org)
    for role in ("ESTIMATOR", "WORKSHOP_MANAGER", "INSTALLER"):
        result = owner_client(users[role]).post(BASE + "inspect/", {"file": upload()["file"]}, format="multipart")
        assert result.status_code == 403
    result = owner_client(users["OWNER"]).post(BASE + "review/", upload(cost_list_id=str(list_id)),
        format="multipart", HTTP_X_ORGANIZATION_ID=str(other))
    assert result.status_code == 403
    result = owner_client(users["OWNER"]).post(BASE + "review/", upload(cost_list_id=str(foreign_list)), format="multipart")
    assert result.status_code == 422 and result.json()["error"]["code"] == "cost_list_not_found"
