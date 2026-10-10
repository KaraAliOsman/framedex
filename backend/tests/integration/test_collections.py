"""Real PostgreSQL capability, ledger, simulator and tenant boundaries."""

from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from decimal import Decimal as D
from uuid import UUID, uuid4

import pytest
from django.db import DatabaseError, transaction, close_old_connections
from django.utils import timezone
from rest_framework.test import APIClient

from backend.tests.integration.test_shot09_documentary import (
    documentary_tenant as documentary_tenant, _seed_project, _freeze, as_user,
    documentary_committed_tenant as documentary_committed_tenant,
)
from documents.repository import decoded, documentary_backend
from pricing.repository import one, rows, json_text
from projects import collection_settings, credit_notes, fiscal_adapter, invoices, payments, payment_links, simulated_flow, receipts
from projects.provider_scope import provider_scope

pytestmark = pytest.mark.rls_integration


class Storage:
    def upload_immutable(self, *args):
        pass
    def delete_object(self, *args):
        pass


@pytest.fixture
def deal(documentary_tenant, monkeypatch, settings):
    org, other, users, outsider = documentary_tenant
    monkeypatch.setattr(receipts, "SupabaseDocumentStorage", Storage)
    monkeypatch.setattr(invoices, "SupabaseDocumentStorage", Storage)
    monkeypatch.setattr(credit_notes, "SupabaseDocumentStorage", Storage)
    settings.BILLING_FRONTEND_ORIGIN = "http://127.0.0.1:5173"
    project, _, op = _seed_project(org, users["OWNER"])
    with as_user(users["OWNER"]), documentary_backend():
        rows("UPDATE public.project_documentary_inputs SET commercial_terms=%s::jsonb WHERE project_id=%s RETURNING project_id",
            [json_text({"payment_schedule": [{"label": "Anticipo", "share": "0.5", "due_on": "2026-10-01"},
                                          {"label": "Saldo", "share": "0.5", "due_event": "DELIVERY"}]}), str(project)])
    version = _freeze(org, users["OWNER"], project, op)
    return org, other, users, outsider, project, version


def test_capability_replay_creates_one_payment_receipt_and_zero_balance(deal):
    org, _, users, _, project, _ = deal
    with as_user(users["ESTIMATOR"]):
        initial = payments.list_payments(org_id=org, project_id=project)
        assert len(initial["schedule"]) == 2
        deposit, balance = [D(item["amount"]) for item in initial["schedule"]]
        recorded = payments.record_payment(org_id=org, project_id=project, actor_id=users["ESTIMATOR"],
            data={"operation_key": str(uuid4()), "kind": "ANTICIPO", "amount": deposit, "method": "TRANSFER", "recorded_on": date(2026, 10, 1)})
        assert recorded["receipt"]["receipt_code"].startswith("RC-")
        data = {"operation_key": str(uuid4()), "kind": "SALDO", "amount": balance,
                "payer_email": "payer@example.test", "simulated": True}
        first = simulated_flow.create_link(org_id=org, project_id=project, actor_id=users["ESTIMATOR"], data=data)["link"]
        replay = simulated_flow.create_link(org_id=org, project_id=project, actor_id=users["ESTIMATOR"], data=data)["link"]
        assert first == replay
    token = first["url"].split("token=")[1]
    client = APIClient()
    path = f"/api/v1/projects/flow/simulated/{first['id']}/"
    for invalid in ("wrong-token-for-test-only", "inválido"):
        denied = client.post(path, {"token": invalid, "outcome": "PAID"}, format="json")
        assert denied.status_code == 404
    for _ in range(2):
        result = client.post(path, {"token": token, "outcome": "PAID"}, format="json")
        assert result.status_code == 200, result.data
        assert result.data["status"] == "PAID"
    with as_user(users["OWNER"]):
        final = payments.list_payments(org_id=org, project_id=project)
        assert D(final["balance"]) == 0 and final["status"] == "PAID"
        assert final["includes_simulation"] is True
        assert len(final["payments"]) == 2
        assert len({p["receipt_id"] for p in final["payments"]}) == 2
        assert final["payments"][1]["actor_label"] == "Simulador Flow"


def test_oversized_expired_and_rebound_simulations_are_rejected_without_ledger_change(deal):
    org, _, users, _, project, _ = deal
    with as_user(users["ESTIMATOR"]):
        total = D(payments.list_payments(org_id=org, project_id=project)["balance"])
        data = {"operation_key": str(uuid4()), "kind": "SALDO", "amount": total + 1,
                "payer_email": "payer@example.test", "simulated": True}
        with pytest.raises(Exception) as error:
            simulated_flow.create_link(org_id=org, project_id=project, actor_id=users["ESTIMATOR"], data=data)
        assert error.value.contract_code == "payment_exceeds_balance"
        data["amount"] = total
        link = simulated_flow.create_link(org_id=org, project_id=project, actor_id=users["ESTIMATOR"], data=data)["link"]
        with pytest.raises(Exception) as error:
            simulated_flow.create_link(org_id=org, project_id=project, actor_id=users["ESTIMATOR"], data={**data, "amount": total-1})
        assert error.value.contract_code == "payment_operation_conflict"
    token = link["url"].split("token=")[1]
    # Time moves; immutable link identity is never edited to manufacture expiry.
    from unittest.mock import patch
    with patch("projects.simulated_flow.timezone.now", return_value=timezone.now()+timedelta(days=8)):
        with pytest.raises(Exception) as error:
            simulated_flow.confirm(link_id=UUID(link["id"]), token=token, outcome="PAID")
        assert error.value.contract_code == "payment_link_expired"
    with as_user(users["OWNER"]):
        assert payments.list_payments(org_id=org, project_id=project)["payments"] == []


def test_fiscal_simulations_are_separate_immutable_replayed_and_tenant_scoped(deal):
    org, other, users, outsider, project, _ = deal
    with as_user(users["OWNER"]):
        emitted = invoices.issue_invoice(org_id=org, project=payments.project_row(org, project), actor_id=users["OWNER"], document_kind="BOLETA")
        for scenario in ("ACCEPTED", "WARNINGS", "REJECTED"):
            data={"invoice_id": UUID(emitted["id"]), "operation_key": str(uuid4()), "scenario": scenario}
            first=fiscal_adapter.simulate(org_id=org, project_id=project, actor_id=users["OWNER"], actor_label="Owner", data=data)
            replay=fiscal_adapter.simulate(org_id=org, project_id=project, actor_id=users["OWNER"], actor_label="Owner", data=data)
            assert replay == first and first["folio"].startswith("SIM-") and first["dte_type"] == 39
        with documentary_backend():
            assert one("SELECT count(*) AS n FROM public.project_dtes WHERE org_id=%s", [str(org)])["n"] == 0
            with pytest.raises(DatabaseError), transaction.atomic():
                rows("UPDATE public.project_fiscal_simulations SET status='REJECTED' WHERE org_id=%s RETURNING id", [str(org)])
    with as_user(outsider), documentary_backend():
        assert rows("SELECT id FROM public.project_fiscal_simulations WHERE org_id=%s", [str(org)]) == []
        assert collection_settings.preferences(other) == collection_settings.DEFAULTS


def test_provider_scope_restores_claims_and_role_after_nested_documents(deal):
    _, _, users, _, _, _ = deal
    with as_user(users["OWNER"]):
        previous = one("SELECT current_setting('role') AS role,current_setting('request.jwt.claims') AS claims,auth.uid() AS uid")
        with provider_scope(), documentary_backend():
            trusted = one("SELECT current_setting('role') AS role,auth.uid() AS uid")
            assert trusted == {"role": "service_role", "uid": None}
        assert one("SELECT current_setting('role') AS role,current_setting('request.jwt.claims') AS claims,auth.uid() AS uid") == previous
        with pytest.raises(ValueError):
            with provider_scope():
                raise ValueError("callback failure")
        assert one("SELECT current_setting('role') AS role,current_setting('request.jwt.claims') AS claims,auth.uid() AS uid") == previous


def test_collection_reload_distinguishes_partial_credit_from_annulment(deal):
    org, _, users, _, project, _ = deal
    with as_user(users["OWNER"]):
        document = invoices.issue_invoice(org_id=org, project=payments.project_row(org, project),
                                          actor_id=users["OWNER"], document_kind="BOLETA")
        credit_notes.issue_credit_note(org_id=org, project=payments.project_row(org, project),
            actor_id=users["OWNER"], invoice_id=UUID(document["id"]), reason="Corrección parcial", amount=D("1"))
        summary = payments.list_payments(org_id=org, project_id=project)
        credit = summary["invoices"][0]["credit_note"]
        assert credit["partial"] is True and D(credit["credit_amount_gross"]) == 1


def test_two_public_callbacks_converge_on_one_sealed_payment(documentary_committed_tenant, monkeypatch, settings):
    org, _, users, _ = documentary_committed_tenant
    monkeypatch.setattr(receipts, "SupabaseDocumentStorage", Storage)
    settings.BILLING_FRONTEND_ORIGIN = "http://127.0.0.1:5173"
    project, _, operation = _seed_project(org, users["OWNER"])
    _freeze(org, users["OWNER"], project, operation)
    with as_user(users["ESTIMATOR"]):
        amount = payments.list_payments(org_id=org, project_id=project)["balance"]
        link = simulated_flow.create_link(org_id=org, project_id=project, actor_id=users["ESTIMATOR"],
            data={"operation_key": str(uuid4()), "kind": "SALDO", "amount": D(amount),
                  "payer_email": "payer@example.test", "simulated": True})["link"]
    token = link["url"].split("token=")[1]
    barrier = Barrier(2)
    def callback():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return simulated_flow.confirm(link_id=UUID(link["id"]), token=token, outcome="PAID")
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(callback) for _ in range(2)]
        assert [f.result(timeout=30)["status"] for f in futures] == ["PAID", "PAID"]
    with as_user(users["OWNER"]):
        final = payments.list_payments(org_id=org, project_id=project)
        assert len(final["payments"]) == 1 and D(final["balance"]) == 0
        assert final["payments"][0]["receipt_id"] is not None


def test_preferences_owner_only_and_callback_revision_replacement(deal, monkeypatch):
    org, other, users, outsider, project, _ = deal
    with as_user(users["ESTIMATOR"]):
        with pytest.raises(DatabaseError), transaction.atomic():
            collection_settings.save(org_id=org, actor_id=users["ESTIMATOR"], data=collection_settings.DEFAULTS)
        amount = D(payments.list_payments(org_id=org, project_id=project)["balance"])
        link = simulated_flow.create_link(org_id=org, project_id=project, actor_id=users["ESTIMATOR"],
            data={"operation_key": str(uuid4()), "kind": "SALDO", "amount": amount,
                  "payer_email": "payer@example.test", "simulated": True})["link"]
    with as_user(outsider):
        with pytest.raises(DatabaseError), transaction.atomic():
            collection_settings.save(org_id=org, actor_id=outsider, data=collection_settings.DEFAULTS)
        assert collection_settings.preferences(other) == collection_settings.DEFAULTS
    real_deal = simulated_flow._deal
    monkeypatch.setattr(simulated_flow, "_deal", lambda *args: {**real_deal(*args), "sealed_revision": "REV-B"})
    with pytest.raises(Exception) as error:
        simulated_flow.confirm(link_id=UUID(link["id"]), token=link["url"].split("token=")[1], outcome="PAID")
    assert error.value.contract_code == "payment_link_stale"
    with as_user(users["OWNER"]):
        assert payments.list_payments(org_id=org, project_id=project)["payments"] == []


@pytest.mark.parametrize("early_status", [1, 2])
def test_verified_flow_callback_before_create_response_preserves_status_and_sealed_client(
    documentary_committed_tenant, monkeypatch, settings, early_status
):
    org, _, users, _ = documentary_committed_tenant
    monkeypatch.setattr(receipts, "SupabaseDocumentStorage", Storage)
    settings.BILLING_FRONTEND_ORIGIN = "http://127.0.0.1:5173"
    settings.BILLING_CALLBACK_ORIGIN = "https://callback.example.test"
    project, _, operation = _seed_project(org, users["OWNER"])
    version = _freeze(org, users["OWNER"], project, operation)
    key = str(uuid4())
    with as_user(users["OWNER"]):
        amount = D(payments.list_payments(org_id=org, project_id=project)["balance"])
        payment_links.save_integration(org_id=org, data={
            "api_key": "test-only-key", "secret_key": "test-only-secret", "enabled": True,
        })

    class Client:
        api_url = "https://sandbox.flow.cl/api"

        def payment_status(self, token):
            assert token == "test-only-token"
            return {"flowOrder": 99, "status": early_status, "commerceOrder": key,
                    "amount": str(amount), "currency": "CLP"}

        def create_payment(self, **kwargs):
            assert kwargs["timeout_seconds"] > 0
            link_id = UUID(kwargs["confirmation_url"].rstrip("/").split("/")[-1])
            # The provider can notify before its create response reaches us.
            result = payment_links.confirm_link(link_id=link_id, token="test-only-token")
            assert result["link"]["status"] in ("DISPATCHING", "PAID")
            return {"flowOrder": 99, "token": "test-only-token", "url": "https://sandbox.flow.cl/pay"}

        def redirect_url(self, response):
            return "https://sandbox.flow.cl/pay?token=test-only-token"

    monkeypatch.setattr(payment_links, "_client", lambda _: Client())
    with as_user(users["OWNER"]):
        created = payment_links.create_link(org_id=org, project_id=project, actor_id=users["OWNER"],
            data={"operation_key": key, "kind": "SALDO", "amount": amount, "payer_email": "payer@example.test"})
        assert created["link"]["status"] == ("PAID" if early_status == 2 else "PENDING")
        if early_status == 1:
            assert created["link"]["url"] == "https://sandbox.flow.cl/pay?token=test-only-token"
        link_id = UUID(created["link"]["id"])
    early_status = 2
    payment_links.confirm_link(link_id=link_id, token="test-only-token")
    with as_user(users["OWNER"]), documentary_backend():
        final = payments.list_payments(org_id=org, project_id=project)
        assert len(final["payments"]) == 1 and D(final["balance"]) == 0
        receipt = decoded(one("SELECT payload_json FROM public.payment_receipts WHERE org_id=%s AND project_id=%s", [org, project])["payload_json"])
        assert receipt["project"]["revision_code"] == version["revision_code"]
        assert receipt["project"]["client_name"] == "Cliente Demo"
        assert receipt["payment"]["actor_label"] == "Flow verificado"


def test_two_verified_flow_callbacks_settle_once(documentary_committed_tenant, monkeypatch, settings):
    org, _, users, _ = documentary_committed_tenant
    monkeypatch.setattr(receipts, "SupabaseDocumentStorage", Storage)
    settings.BILLING_FRONTEND_ORIGIN = "http://127.0.0.1:5173"
    settings.BILLING_CALLBACK_ORIGIN = "https://callback.example.test"
    project, _, operation = _seed_project(org, users["OWNER"])
    _freeze(org, users["OWNER"], project, operation)
    key = str(uuid4())

    class Client:
        api_url = "https://sandbox.flow.cl/api"

        def create_payment(self, **kwargs):
            return {"flowOrder": 101, "token": "test-only-token", "url": "https://sandbox.flow.cl/pay"}

        def redirect_url(self, response):
            return "https://sandbox.flow.cl/pay?token=test-only-token"

        def payment_status(self, token):
            return {"flowOrder": 101, "status": 2, "commerceOrder": key,
                    "amount": str(amount), "currency": "CLP"}

    monkeypatch.setattr(payment_links, "_client", lambda _: Client())
    with as_user(users["OWNER"]):
        amount = D(payments.list_payments(org_id=org, project_id=project)["balance"])
        payment_links.save_integration(org_id=org, data={"api_key": "test-only-key", "secret_key": "test-only-secret", "enabled": True})
        link = payment_links.create_link(org_id=org, project_id=project, actor_id=users["OWNER"],
            data={"operation_key": key, "kind": "SALDO", "amount": amount, "payer_email": "payer@example.test"})["link"]
    barrier = Barrier(2)
    def callback():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return payment_links.confirm_link(link_id=UUID(link["id"]), token="test-only-token")
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(callback) for _ in range(2)]
        assert [f.result(timeout=30)["link"]["status"] for f in futures] == ["PAID", "PAID"]
    with as_user(users["OWNER"]):
        final = payments.list_payments(org_id=org, project_id=project)
        assert len(final["payments"]) == 1 and D(final["balance"]) == 0
