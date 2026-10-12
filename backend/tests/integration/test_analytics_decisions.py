"""Every metric executes its versioned SQL over a hand-calculated oracle.

4 emissions: A/B of one work, one decline and one pending work. A selects B.
Approval 1/4; FIXED 1/3 and SLIDING 0/1. Decisions: 48h and 72h → 60h.
B has net900/cost500; original42×10 + 3×20 +20 =500, remake3×10 +0.5×20 =40.
Bars plan (300+400)/(6000+3000); real600/9000, useful8000/9000.
Stations elapsed1h and3h →2h, distinct from paid3h and0.5h.
1/2 OT and1/2 installations punctual. 2 warranties (1 open) plus1 damage.
"""

from copy import deepcopy
from decimal import Decimal, localcontext
from uuid import uuid4

from django.db import connection, DatabaseError, transaction
import pytest
from authentication.errors import ContractAPIException
from analytics import reports, metrics
from documents.repository import rows, documentary_backend
from backend.tests.integration.analytics_fixture import START, END, seed_analytics, report_body
from backend.tests.integration.test_shot09_documentary import (
    documentary_tenant as documentary_tenant,
    as_user,
)
from backend.tests.integration.test_shot08_pricing import owner_client

pytestmark = pytest.mark.rls_integration


@pytest.fixture
def oracle(documentary_tenant):
    org, other, users, other_user = documentary_tenant
    fixture = seed_analytics(org, users)
    return org, other, users, other_user, fixture


def read(oracle):
    org, _, users, _, _ = oracle
    with as_user(users["WORKSHOP_MANAGER"]), documentary_backend():
        return metrics.workspace(org, START, END)


# This is a test per metric, rather than a mocked projection. Every execution
# runs emissions/orders/materials/steps/remnants/visits/incidents.sql under RLS.
@pytest.mark.parametrize(
    "key,expected",
    [
        ("emitted", "4"),
        ("approved", "1"),
        ("rejected", "1"),
        ("conversion", (1, 4)),
        ("conversion_estimator:", (1, 4)),
        ("decision_time", "60"),
        ("rejection_reason:", "1"),
        ("quoted_margin:", (4, 9)),
        ("real_margin:", "0.4"),
        ("delta_profit:", "-40"),
        ("driver_materials:", "10"),
        ("driver_waste:", "10"),
        ("driver_labor:", "-10"),
        ("driver_other:", "-10"),
        ("driver_remake:", "-40"),
        ("driver_discount:", "-100"),
        ("deviation_typology:", "-40"),
        ("planned_waste", (7, 90)),
        ("actual_waste", (1, 15)),
        ("utilization", (8, 9)),
        ("remnant_use", "1"),
        ("station_time:", "2"),
        ("orders_on_time", "0.5"),
        ("remake_cause:", "1"),
        ("installations_on_time", "0.5"),
        ("open_warranties", "1"),
    ],
)
def test_versioned_sql_metric_manual_oracle(oracle, key, expected):
    output = read(oracle)
    found = [
        m
        for m in output["metrics"]
        if m["key"] == key or (key.endswith(":") and m["key"].startswith(key))
    ]
    assert len(found) == 1, key
    with localcontext() as context:
        context.prec = 256
        value = (
            Decimal(expected[0]) / Decimal(expected[1])
            if isinstance(expected, tuple)
            else Decimal(expected)
        )
        assert Decimal(found[0]["value"]) == value
    assert found[0]["reason"] is None
    assert found[0]["source"] and found[0]["formula"]
    assert "private_signature" not in str(output)


def test_sql_typology_pipeline_and_incident_groups(oracle):
    output = read(oracle)
    items = output["metrics"]
    typology = {
        m["label"].split(" · ")[-1]: m["value"]
        for m in items
        if m["key"].startswith("conversion_typology:")
    }
    with localcontext() as context:
        context.prec = 256
        assert Decimal(typology["Fijo"]) == Decimal(1) / Decimal(3)
    assert Decimal(typology["Corredera 2 hojas"]) == 0
    pipeline = {m["label"]: Decimal(m["value"]) for m in items if m["key"].startswith("pipeline:")}
    assert pipeline == {
        "¿Cuánto hay en aprobada?": Decimal("1071"),
        "¿Cuánto hay en cotizada?": Decimal("1428"),
    }
    kinds = {m["label"]: m["value"] for m in items if m["key"].startswith("incidents_kind:")}
    assert kinds == {"Incidencias · Daño": "1", "Incidencias · Garantía": "2"}
    assert [m["value"] for m in items if m["key"].startswith("incidents_typology:")] == ["3"]
    work = output["works"][0]
    assert work["revision"] == "REV-B" and work["net"] == "900"
    for item in items:
        if item["key"].startswith("driver_"):
            assert sum(Decimal(d["value"]) for d in item["details"]) == Decimal(item["value"])
            if not item["key"].startswith("driver_discount:"):
                assert any("movement=" in d["href"] for d in item["details"])


def test_rls_other_organization_cost_roles_and_live_revocation(oracle):
    org, other, users, other_user, fixture = oracle
    for actor in (users["ESTIMATOR"], users["INSTALLER"], other_user):
        with as_user(actor):
            assert (
                rows("SELECT id FROM public.production_actual_reports WHERE org_id=%s", [org]) == []
            )
        client = owner_client(actor)
        assert (
            client.get("/api/v1/analytics/decision/", HTTP_X_ORGANIZATION_ID=str(org)).status_code
            == 403
        )
    with as_user(other_user), documentary_backend():
        assert metrics.workspace(other, START, END)["empty"]
        with pytest.raises(ContractAPIException):
            reports.order_read(other, fixture["orders"][0])
    for key in ("OWNER", "WORKSHOP_MANAGER"):
        response = owner_client(users[key]).get(
            "/api/v1/analytics/decision/",
            {"start": START, "end": END},
            HTTP_X_ORGANIZATION_ID=str(org),
        )
        assert response.status_code == 200 and len(response.json()["works"]) == 1
    rows(
        "UPDATE public.tenancy_memberships SET is_active=false WHERE org_id=%s AND user_id=%s RETURNING org_id",
        [org, users["WORKSHOP_MANAGER"]],
    )
    assert (
        owner_client(users["WORKSHOP_MANAGER"])
        .get("/api/v1/analytics/decision/", HTTP_X_ORGANIZATION_ID=str(org))
        .status_code
        == 403
    )


def test_sql_incomplete_sources_do_not_fabricate_totals(oracle):
    org, _, users, _, fixture = oracle
    with as_user(users["WORKSHOP_MANAGER"]), documentary_backend():
        data = reports.load(org, START, END)
        for change in ("valuation", "position", "station", "bars", "currency"):
            changed = deepcopy(data)
            selected = next(row for row in changed["emissions"] if row["decision"] == "APPROVED")
            if change == "valuation":
                changed["orders"][0]["evidence_json"]["materials"][0]["unit_cost"] = None
            if change == "position":
                selected["snapshot_json"]["positions"].append(
                    {"id": str(uuid4()), "typology": "FIXED", "position_index": 2}
                )
            if change == "station":
                changed["orders"][0]["evidence_json"]["labor"][0]["hours"] = None
            if change == "bars":
                changed["orders"][0]["evidence_json"]["bars"]["complete"] = False
            if change == "currency":
                selected["snapshot_json"]["project"]["currency"] = None
            if change in ("valuation", "position", "station", "currency"):
                assert metrics.margins(changed)[1][0]["real_margin"] is None
            elif change == "bars":
                assert (
                    next(
                        m
                        for m in metrics.production(changed, START, END)
                        if m["key"] == "actual_waste"
                    )["value"]
                    is None
                )
        # A later ledger movement invalidates the saved closure, without editing it.
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL session_replication_role=replica")
        cursor.execute(
            "INSERT INTO public.inventory_movements(org_id,item_id,movement_type,quantity,order_id) SELECT org_id,item_id,'SCRAP',1,order_id FROM public.inventory_movements WHERE id=%s",
            [fixture["movements"][0]],
        )
        cursor.execute("SET LOCAL session_replication_role=origin")
    output = read(oracle)
    assert output["works"][0]["real_margin"] is None and "cambiaron" in output["works"][0]["reason"]


def test_preview_confirmation_replay_correction_and_immutability(oracle):
    org, _, users, _, fixture = oracle
    order, actor = fixture["orders"][0], users["WORKSHOP_MANAGER"]
    with as_user(actor), documentary_backend():
        current = reports.order_read(org, order)
        data = report_body(current)
        preview = reports.save_report(org, actor, order, data, preview=True)
        assert preview["result"]["cost"] == current["result"]["cost"]
        assert reports.order_read(org, order)["revision"] == 1
        with pytest.raises(ContractAPIException):
            reports.save_report(org, actor, order, {**data, "confirmed": False})
        first = reports.save_report(org, actor, order, data)
        assert reports.save_report(org, actor, order, data) == first
        with pytest.raises(ContractAPIException):
            reports.save_report(org, actor, order, {**data, "other_cost": "21"})
        newer = report_body(reports.order_read(org, order))
        newer["other_cost"] = "21"
        second = reports.save_report(org, actor, order, newer)
        assert second["revision"] == 3 and Decimal(second["result"]["cost"]) == 501
        assert reports.save_report(org, actor, order, data) == first
        with pytest.raises(ContractAPIException):
            reports.save_report(org, actor, order, {**newer, "request_key": uuid4()})
        with pytest.raises(ContractAPIException):
            reports.save_report(org, actor, order, {**report_body(second), "currency": "USD"})
        for statement in (
            "UPDATE public.production_actual_reports SET reason='forged' WHERE org_id=%s",
            "DELETE FROM public.production_actual_reports WHERE org_id=%s",
        ):
            with pytest.raises(DatabaseError), transaction.atomic():
                rows(statement, [org])


def test_csv_formula_escape_date_filter_and_owner_preference(oracle):
    org, _, users, _, _ = oracle
    owner, manager = owner_client(users["OWNER"]), owner_client(users["WORKSHOP_MANAGER"])
    assert (
        manager.put(
            "/api/v1/analytics/preferences/",
            {"period_days": 60},
            format="json",
            HTTP_X_ORGANIZATION_ID=str(org),
        ).status_code
        == 403
    )
    response = owner.put(
        "/api/v1/analytics/preferences/",
        {"period_days": 60},
        format="json",
        HTTP_X_ORGANIZATION_ID=str(org),
    )
    assert response.status_code == 200 and response.json() == {"period_days": 60}
    assert (
        owner.get(
            "/api/v1/analytics/decision/",
            {"start": "2026-10-31", "end": "2026-10-01"},
            HTTP_X_ORGANIZATION_ID=str(org),
        ).status_code
        == 422
    )
    response = manager.get(
        "/api/v1/analytics/decision/export/",
        {"start": START, "end": END},
        HTTP_X_ORGANIZATION_ID=str(org),
    )
    assert response.status_code == 200 and response.content.startswith(b"\xef\xbb\xbf")
    assert "-40" in response.content.decode("utf-8")
