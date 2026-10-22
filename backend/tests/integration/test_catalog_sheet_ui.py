"""Tenant names and atomic exact cost edits needed by the series sheet UI."""

from decimal import Decimal
from uuid import uuid4

from django.db import connection, transaction
import pytest

from authentication.errors import ContractAPIException
from catalogs import series
from pricing.repository import admin_write, one

from .test_catalog_series_sheet import address, create
from .test_catalog_use_levels import fixture_write, priced_series
from .test_shot08_pricing import owner_client
from .test_shot09_documentary import as_user, documentary_tenant as documentary_tenant

pytestmark = pytest.mark.rls_integration


def test_price_sheet_includes_all_calculator_identities_without_requiring_kit_supplier_mapping(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet = priced_series(org, actor)
        prices = series.series_sheet(org, sheet["id"], can_view_prices=True)["tabs"]["prices"]["items"]
        assert {item["sku"] for item in prices} == {
            "PRO-F", "PRO-S", "PRO-B", "STEEL-F", "STEEL-S", "GLASS-24", "PRO-TURN", "SCREW-F", "SCREW-S"}
        kit_price = next(item for item in prices if item["sku"] == "PRO-TURN")
        response = series.edit_prices(org, sheet["id"], {"revision": sheet["revision"],
            "reason": "Precio de kit declarado por el taller sintético", "changes": [{"id": kit_price["id"],
                "previous_unit_cost": Decimal(kit_price["unit_cost"]), "unit_cost": Decimal("1234.5678")}]})
        assert next(item for item in response["tabs"]["prices"]["items"]
            if item["sku"] == "PRO-TURN")["unit_cost"] == "1234.5678"
        assert series.price_history(org, sheet["id"], kit_price["id"])["items"][0]["value"] == "1234.5678"


def test_rejected_batch_addresses_the_cross_field_error_and_rolls_back_other_rows(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet = create(org, actor)
    kit = sheet["tabs"]["hardware"][0]
    rule = address(sheet, field="rebate_depth_mm")
    client = owner_client(actor)
    result = client.patch(f"/api/v1/catalogs/series/{sheet['id']}/cells/", {
        "revision": sheet["revision"], "changes": [{**rule, "value": "4.25"},
            {"resource": "hardware-kits", "row_id": str(kit["id"]), "field": "max_leaf_width_mm", "value": "0.01"}]},
        format="json", HTTP_X_ORGANIZATION_ID=str(org))
    assert result.status_code == 400, result.data
    assert result.json()["error"]["resource"] == "hardware-kits"
    assert result.json()["error"]["row_id"] == str(kit["id"])
    assert "El máximo debe ser mayor o igual al mínimo." in result.json()["error"]["fields"]["max_leaf_width_mm"]
    with as_user(actor):
        assert series.series_sheet(org, sheet["id"])["revision"] == sheet["revision"]


def test_actor_names_are_current_tenant_members_and_inactive_actors_have_no_name(documentary_tenant):
    org, other, users, foreign = documentary_tenant
    actor = users["OWNER"]
    with connection.cursor() as cursor:
        for user_id, name in ((actor, "Juan del taller"), (foreign, "Persona de otra empresa")):
            cursor.execute("INSERT INTO auth.users(id,email,raw_user_meta_data) VALUES(%s,%s,%s::jsonb)",
                [user_id, f"{user_id}@example.invalid", '{"full_name":"' + name + '"}'])
    with as_user(actor):
        sheet = create(org, actor)
        cell = address(sheet, field="rebate_depth_mm")
        confirmed = series.confirm_cells(org, sheet["id"], actor, {"revision": sheet["revision"], "cells": [cell]})
        found = next(item for item in confirmed["cells"] if item["field"] == cell["field"])
        assert found["actor_name"] == "Juan del taller"
        assert series.history(org, sheet["id"], cell)["items"][0]["actor_name"] == "Juan del taller"
        assert str(foreign) not in series._actor_names(org)
    with as_user(foreign):
        assert series._actor_names(other) == {str(foreign): "Persona de otra empresa"}
    with connection.cursor() as cursor:
        cursor.execute("UPDATE public.tenancy_memberships SET is_active=false WHERE org_id=%s AND user_id=%s", [org, actor])
    with as_user(users["ESTIMATOR"]):
        history = series.history(org, sheet["id"], cell)["items"]
        assert history[0]["set_by"] == actor
        assert history[0]["actor_name"] is None


def test_price_batch_is_exact_audited_and_never_overwrites_another_change(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet = priced_series(org, actor)
        prices = series.price_items(org, sheet["id"])
    first, second = prices[:2]
    client = owner_client(actor)
    path = f"/api/v1/catalogs/series/{sheet['id']}/prices/"
    headers = {"HTTP_X_ORGANIZATION_ID": str(org)}
    changes = [{"id": str(item["id"]), "previous_unit_cost": item["unit_cost"], "unit_cost": "1234.5678"}
        for item in (first, second)]
    payload = {"revision": sheet["revision"], "changes": changes, "reason": "Precio explícito del taller sintético"}
    result = client.patch(path, payload, format="json", **headers)
    assert result.status_code == 200, result.data
    prices = {item["id"]: item for item in result.json()["tabs"]["prices"]["items"]}
    assert prices[str(first["id"])]["unit_cost"] == "1234.5678"
    assert prices[str(second["id"])]["unit_cost"] == "1234.5678"
    history = client.get(path + str(first["id"]) + "/history/", **headers)
    assert history.status_code == 200, history.data
    assert history.json()["items"][0]["value"] == "1234.5678"
    assert Decimal(history.json()["items"][0]["previous_value"]) == Decimal(first["unit_cost"])
    assert history.json()["items"][0]["reason"] == payload["reason"]
    rejected = client.patch(path, payload, format="json", **headers)
    assert rejected.status_code == 409, rejected.data
    with as_user(actor):
        assert one("SELECT unit_cost FROM public.cost_list_items WHERE id=%s", [first["id"]])["unit_cost"] == Decimal("1234.5678")
    for role in ("ESTIMATOR", "WORKSHOP_MANAGER", "INSTALLER"):
        assert owner_client(users[role]).patch(path, payload, format="json", **headers).status_code == 403
        assert owner_client(users[role]).get(path + str(first["id"]) + "/history/", **headers).status_code == 403


def test_price_batch_rejects_missing_duplicate_stale_and_invalid_cells_without_partial_write(documentary_tenant):
    org, _, users, _ = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet = priced_series(org, actor)
        prices = series.price_items(org, sheet["id"])
        first, second = prices[:2]
        base = {"revision": sheet["revision"], "reason": "Edición de prueba"}
        change = {"id": first["id"], "previous_unit_cost": Decimal(first["unit_cost"]), "unit_cost": Decimal("0")}
        for changes in ([change, change], [change, {**change, "id": uuid4()}],
                [change, {"id": second["id"], "previous_unit_cost": Decimal("0.0001"), "unit_cost": Decimal("1")} ]):
            with pytest.raises(ContractAPIException), transaction.atomic():
                series.edit_prices(org, sheet["id"], {**base, "changes": changes})
            assert one("SELECT unit_cost FROM public.cost_list_items WHERE id=%s", [first["id"]])["unit_cost"] == Decimal(first["unit_cost"])
    client = owner_client(actor)
    path = f"/api/v1/catalogs/series/{sheet['id']}/prices/"
    for value in ("-1", "0.00001", "10000000000.0000"):
        result = client.patch(path, {**base, "changes": [{**change, "id": str(change["id"]),
            "previous_unit_cost": str(change["previous_unit_cost"]), "unit_cost": value}]},
            format="json", HTTP_X_ORGANIZATION_ID=str(org))
        assert result.status_code == 400, result.data


def test_price_batch_and_history_reject_real_foreign_and_other_series_costs(documentary_tenant):
    org, other, users, foreign = documentary_tenant
    actor = users["OWNER"]
    with as_user(actor):
        sheet = priced_series(org, actor)
        first = series.price_items(org, sheet["id"])[0]
        separate = create(org, actor)
        with fixture_write():
            one("INSERT INTO public.profile_purchase_mappings(org_id,profile_article_id,commercial_sku,manufacturer_name,purchase_unit) "
                "VALUES(%s,%s,'OTHER-SERIES-BAR','SYNTHETIC separate series','BAR') RETURNING id",
                [org, separate["tabs"]["profiles"][0]["id"]])
        unrelated = admin_write("cost-items", org, {"cost_list_id": first["cost_list_id"],
            "sku": "OTHER-SERIES-BAR", "item_type": "SYNTHETIC", "unit": "BAR", "unit_cost": Decimal("987.6543")},
            "Synthetic separate-series price")
        assert unrelated["id"] in {item["id"] for item in series.price_items(org, separate["id"])}
    with as_user(foreign):
        foreign_sheet = priced_series(other, foreign)
        foreign_price = series.price_items(other, foreign_sheet["id"])[0]
    client = owner_client(actor)
    path = f"/api/v1/catalogs/series/{sheet['id']}/prices/"
    headers = {"HTTP_X_ORGANIZATION_ID": str(org)}
    change = {"id": str(first["id"]), "previous_unit_cost": first["unit_cost"], "unit_cost": "0.0000"}
    for forbidden in (unrelated, foreign_price):
        payload = {"revision": sheet["revision"], "reason": "Comprobar aislamiento del lote", "changes": [change,
            {"id": str(forbidden["id"]), "previous_unit_cost": str(forbidden["unit_cost"]), "unit_cost": "1.0000"}]}
        result = client.patch(path, payload, format="json", **headers)
        assert result.status_code == 404, result.data
        assert client.get(path + str(forbidden["id"]) + "/history/", **headers).status_code == 404
        with as_user(actor):
            assert one("SELECT unit_cost FROM public.cost_list_items WHERE id=%s", [first["id"]])["unit_cost"] == Decimal(first["unit_cost"])
    foreign_path = f"/api/v1/catalogs/series/{foreign_sheet['id']}/prices/"
    assert client.patch(foreign_path, {**payload, "revision": foreign_sheet["revision"]}, format="json", **headers).status_code == 404
    result = client.patch(path, {"revision": sheet["revision"], "reason": "Precio cero explícito", "changes": [change]}, format="json", **headers)
    assert result.status_code == 200, result.data
    assert next(item for item in result.json()["tabs"]["prices"]["items"] if item["id"] == str(first["id"]))["unit_cost"] == "0.0000"
