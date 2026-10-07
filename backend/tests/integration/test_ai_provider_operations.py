"""Paid exchanges, concurrent budgets and private reads on real PostgreSQL."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from django.db import close_old_connections, connection, DatabaseError, transaction
import pytest

from ai_gateway import configuration, service, usage
from ai_gateway.providers import ProviderError
from authentication.errors import ContractAPIException
from authentication.types import SupabaseUser, VerifiedSupabaseToken
from backend.tests.integration.test_shot08_pricing import (
    committed_commercial_rows as committed_commercial_rows,
    as_user,
    owner_client,
)
from billing.wallet import financial_transaction, locked_org
from jobs import registry, worker
from pricing.repository import rows

pytestmark = pytest.mark.rls_integration

ROUTE = {"capability": "agent", "provider": "MIMO", "provider_model": "synthetic-model",
         "credits_cost": 5, "input_usd_per_million": Decimal("1.25"),
         "output_usd_per_million": Decimal("3.50")}
RESULT = {"output": '{"reply":"Revisado","steps":[],"warnings":[]}',
          "tokens_prompt": 91, "tokens_completion": 132, "latency_ms": 20,
          "usage_known": True, "model": "synthetic-model"}


def start(org, actor, key=None):
    return usage.begin(org_id=org, user_id=actor, route=ROUTE,
                       operation_key=key or str(uuid4()), input_hash="a" * 64)


def test_physical_usage_survives_domain_and_wallet_rollback(committed_commercial_rows, caplog):
    org, _, users = committed_commercial_rows
    key = str(uuid4())
    with transaction.atomic():
        with financial_transaction(org):
            locked_org(org)
        reservation = start(org, users["ESTIMATOR"], key)
        usage.finish(reservation, result=RESULT)
        usage.note(org, reservation["id"], "calculate_position")
        rows("UPDATE public.tenancy_organizations SET name='rolled back domain' WHERE id=%s RETURNING id", [org])
        transaction.set_rollback(True)
    record = rows("SELECT * FROM public.ai_provider_usage WHERE id=%s", [reservation["id"]])[0]
    assert record["status"] == "SUCCEEDED"
    assert record["estimated_cost_usd"] == Decimal("0.00057575")
    assert rows("SELECT name FROM public.tenancy_organizations WHERE id=%s", [org])[0]["name"] != "rolled back domain"
    assert rows("SELECT * FROM public.ai_audit_logs WHERE org_id=%s", [org]) == []
    with pytest.raises(ContractAPIException) as conflict:
        start(org, users["ESTIMATOR"], key)
    assert conflict.value.contract_code == "ai_operation_in_progress"
    assert len(usage.list_work(org)[0]["trace"]) == 1
    assert "synthetic-private-key" not in caplog.text


def test_budget_reservation_serializes_parallel_calls_and_commits_owner_notice(committed_commercial_rows):
    org, _, users = committed_commercial_rows
    rows("INSERT INTO public.ai_settings(org_id,monthly_budget_credits) VALUES(%s,5) RETURNING org_id", [org])
    def reserve():
        close_old_connections()
        try:
            return start(org, users["ESTIMATOR"])
        except ContractAPIException as error:
            assert error.contract_code == "ai_budget_exceeded"
            return None
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=3) as pool:
        found = list(pool.map(lambda _: reserve(), range(3)))
    assert sum(item is not None for item in found) == 1
    summary = usage.summary(org)
    assert summary["budget_blocked"] and summary["budget_notice_at"]
    assert summary["tokens_prompt"] is None
    assert summary["capacity_credits"] == 5


def test_actual_wallet_debit_allows_durable_trace_and_next_round_before_rollback(committed_commercial_rows, monkeypatch):
    org, _, users = committed_commercial_rows
    original = usage.independent
    def bounded(call):
        def run():
            with connection.cursor() as cursor:
                cursor.execute("SET statement_timeout='5s'")
            return call()
        return original(run)
    monkeypatch.setattr(usage, "independent", bounded)
    monkeypatch.setattr(service, "provider_for", lambda _: SimpleNamespace(invoke=lambda **_: dict(RESULT)))
    with transaction.atomic():
        with as_user(users["ESTIMATOR"]):
            result = service.invoke(org_id=org, user_id=users["ESTIMATOR"], capability="agent",
                tool_name="agent", input_payload={"goal": "synthetic contract"}, operation_key=str(uuid4()))
        assert rows("SELECT credits_balance FROM public.tenancy_organizations WHERE id=%s", [org])[0]["credits_balance"] < 500
        usage.note(org, result["usage_id"], "get_context")
        reservation = start(org, users["ESTIMATOR"])
        usage.finish(reservation, result=RESULT)
        transaction.set_rollback(True)
    assert rows("SELECT credits_balance FROM public.tenancy_organizations WHERE id=%s", [org])[0]["credits_balance"] == 500
    assert rows("SELECT * FROM public.ai_audit_logs WHERE org_id=%s", [org]) == []
    assert len(usage.list_work(org)) == 2


def test_failed_paid_format_keeps_tokens_price_and_cannot_repay(committed_commercial_rows, monkeypatch):
    org, _, users = committed_commercial_rows
    calls = []
    def fail(**kwargs):
        calls.append(kwargs)
        error = ProviderError("ai_provider_error")
        error.usage = RESULT
        raise error
    monkeypatch.setattr(service, "provider_for", lambda _: SimpleNamespace(invoke=fail))
    key = str(uuid4())
    for _ in range(2):
        with pytest.raises((ProviderError, ContractAPIException)):
            service.invoke(org_id=org, user_id=users["ESTIMATOR"], capability="agent",
                           tool_name="agent", input_payload={"goal": "synthetic-private-input"}, operation_key=key)
    assert len(calls) == 1
    records = rows("SELECT * FROM public.ai_provider_usage WHERE org_id=%s", [org])
    assert records[0]["status"] == "FAILED" and records[0]["tokens_prompt"] == 91
    assert usage.summary(org)["credits_debited"] == 0
    assert usage.summary(org)["capacity_credits"] > 0
    assert records[0]["estimated_cost_usd"] is None  # no invented tariff


def test_retry_retains_each_failure_and_preserves_terminal_history(committed_commercial_rows):
    org, other, users = committed_commercial_rows
    key = str(uuid4())
    first = start(org, users["ESTIMATOR"], key)
    usage.finish(first, error_code="ai_provider_auth")
    second = start(org, users["ESTIMATOR"], key)
    assert second["attempt"] == 2 and second["id"] != first["id"]
    usage.finish(second, result=RESULT)
    with pytest.raises(DatabaseError), transaction.atomic():
        rows("UPDATE public.ai_provider_usage SET tokens_prompt=0 WHERE id=%s RETURNING id", [first["id"]])
    with pytest.raises(DatabaseError), transaction.atomic():
        rows("INSERT INTO public.ai_usage_events(org_id,usage_id,tool_name,status) VALUES(%s,%s,'calculate_position','OK') RETURNING id", [other, first["id"]])
    with financial_transaction(other):
        assert rows("SELECT * FROM public.ai_provider_usage WHERE id=%s", [first["id"]]) == []


def test_owner_settings_mfa_and_actor_scope_never_expose_credentials(committed_commercial_rows, monkeypatch):
    org, other, users = committed_commercial_rows
    monkeypatch.setenv("AI_GATEWAY_MIMO_API_KEY", "synthetic-private-key")
    monkeypatch.setenv("AI_GATEWAY_MIMO_BASE_URL", "https://provider.example/v1")
    for actor in (users["ESTIMATOR"], users["WORKSHOP_MANAGER"]):
        record = start(org, actor)
        usage.finish(record, result=RESULT)
    headers = {"HTTP_X_ORGANIZATION_ID": str(org)}
    owner = owner_client(users["OWNER"])
    response = owner.get("/api/v1/ai/settings/", **headers)
    assert response.status_code == 200, response.data
    assert "synthetic-private-key" not in response.content.decode()
    assert "provider.example" not in response.content.decode()
    assert all(route["credential_configured"] for route in response.json()["routes"])
    assert len(owner.get("/api/v1/ai/usage/", **headers).json()) == 2
    estimator = owner_client(users["ESTIMATOR"])
    assert estimator.get("/api/v1/ai/settings/", **headers).status_code == 403
    own = estimator.get("/api/v1/ai/usage/", **headers)
    assert own.status_code == 200 and len(own.json()) == 1
    assert own.json()[0]["user_id"] == str(users["ESTIMATOR"])
    assert owner.get("/api/v1/ai/usage/", HTTP_X_ORGANIZATION_ID=str(other)).status_code == 403
    owner.force_authenticate(user=SupabaseUser(id=users["OWNER"], email="owner@fixture.local"),
        token=VerifiedSupabaseToken(access_token="verified-token", user_id=users["OWNER"], email="owner@fixture.local",
            aal="aal1", claims={"sub": str(users["OWNER"]), "role": "authenticated", "aal": "aal1"}))
    assert owner.get("/api/v1/ai/settings/", **headers).status_code == 403


def test_first_failed_oracle_persists_then_success_can_clear_it(committed_commercial_rows, monkeypatch):
    org, _, users = committed_commercial_rows
    from engine_api.repository import SystemParamsRepository
    monkeypatch.setattr(SystemParamsRepository, "list_visible", lambda *_: [SimpleNamespace(id=uuid4())])
    import projects.ops_registry as operations
    monkeypatch.setattr(operations, "catalog_for", lambda *_: {"params": SimpleNamespace(finishes={"WHITE": {}})})
    monkeypatch.setattr(operations, "calculate_product", lambda *_: {"status": "MANUFACTURING_INCOMPLETE", "issues": []})
    output = {**RESULT, "credits_debited": 5, "test_mode": False, "usage_id": None}
    monkeypatch.setattr(service, "invoke", lambda **_: {**output, "output": '{"ops":[{"op":"set_height","height_mm":"1350"}],"notes":""}'})
    import dekopen_engine.design_operations as engine_ops
    monkeypatch.setattr(engine_ops, "apply_operations", lambda *_args, **_kwargs: {"product": {"assembly": {"modules": [{"width_mm": "1799", "height_mm": "1350"}]}}})
    with pytest.raises(ContractAPIException) as failure:
        with transaction.atomic():
            configuration.probe(org, users["OWNER"], {"operation_key": str(uuid4())})
    assert failure.value.contract_code == "ai_connection_oracle_failed"
    route = rows("SELECT * FROM public.ai_capability_routes WHERE org_id=%s", [org])[0]
    assert route["connection_state"] == "ERROR"
    # invoke's model is a public label, never the transport model to save.
    assert route["provider_model"] == configuration.effective_model(service._route("design_assist"))
    monkeypatch.setattr(engine_ops, "apply_operations", lambda *_args, **_kwargs: {"product": {"assembly": {"modules": [{"width_mm": "1800", "height_mm": "1350"}]}}})
    assert configuration.probe(org, users["OWNER"], {"operation_key": str(uuid4())})["passed"]
    assert rows("SELECT connection_state FROM public.ai_capability_routes WHERE org_id=%s", [org])[0]["connection_state"] == "CONNECTED"


def test_probe_cannot_connect_a_configuration_changed_during_the_call(committed_commercial_rows, monkeypatch):
    org, _, users = committed_commercial_rows
    from engine_api.repository import SystemParamsRepository
    import projects.ops_registry as operations
    import dekopen_engine.design_operations as engine_ops
    monkeypatch.setattr(SystemParamsRepository, "list_visible", lambda *_: [SimpleNamespace(id=uuid4())])
    monkeypatch.setattr(operations, "catalog_for", lambda *_: {"params": SimpleNamespace(finishes={"WHITE": {}})})
    monkeypatch.setattr(operations, "calculate_product", lambda *_: {"status": "MANUFACTURING_INCOMPLETE", "issues": []})
    monkeypatch.setattr(engine_ops, "apply_operations", lambda *_args, **_kwargs: {"product": {"assembly": {"modules": [{"width_mm": "1800", "height_mm": "1350"}]}}})
    def invoke(**_):
        def change():
            rows("INSERT INTO public.ai_capability_routes(org_id,capability,provider,provider_model) VALUES(%s,'design_assist','MIMO','new-model') RETURNING capability", [org])
        usage.independent(change)
        return {**RESULT, "credits_debited": 5, "test_mode": False, "usage_id": None,
                "output": '{"ops":[{"op":"set_height","height_mm":"1350"}],"notes":""}'}
    monkeypatch.setattr(service, "invoke", invoke)
    with pytest.raises(ContractAPIException) as failure:
        configuration.probe(org, users["OWNER"], {"operation_key": str(uuid4())})
    assert failure.value.contract_code == "ai_settings_conflict"
    route = rows("SELECT * FROM public.ai_capability_routes WHERE org_id=%s", [org])[0]
    assert route["provider_model"] == "new-model" and route["connection_state"] == "UNTESTED"
    assert route["checked_at"] is None


def test_saved_configuration_does_not_inherit_previous_success(committed_commercial_rows, monkeypatch):
    org, _, users = committed_commercial_rows
    monkeypatch.setenv("AI_GATEWAY_MIMO_API_KEY", "synthetic-private-key")
    monkeypatch.setenv("AI_GATEWAY_MIMO_BASE_URL", "https://provider.example/v1")
    route = service._route("design_assist", org)
    reservation = usage.begin(org_id=org, user_id=users["OWNER"], route=route,
                              operation_key=str(uuid4()), input_hash="b" * 64)
    usage.finish(reservation, result={**RESULT, "model": configuration.effective_model(route)})
    before = configuration.get(org)
    assert before["routes"][0]["state"] == "CONNECTED"
    fields = ("capability", "provider", "provider_model", "timeout_s", "retries", "tools_mode", "input_usd_per_million", "output_usd_per_million")
    after = configuration.save(org, users["OWNER"], {"expected_revision": before["revision"],
        "monthly_budget_credits": None, "routes": [{key: route[key] for key in fields} for route in before["routes"]]})
    assert after["routes"][0]["state"] == "UNTESTED"
    assert after["routes"][0]["checked_at"] is None


def test_monthly_budget_counts_old_debits_without_duplicating_new_exchanges(committed_commercial_rows, monkeypatch):
    org, _, users = committed_commercial_rows
    monkeypatch.setattr(service, "provider_for", lambda _: SimpleNamespace(invoke=lambda **_: dict(RESULT)))
    with monkeypatch.context() as old_transport:
        old_transport.setattr(usage, "begin", lambda **_: None)
        with as_user(users["ESTIMATOR"]):
            old = service.invoke(org_id=org, user_id=users["ESTIMATOR"], capability="agent",
                operation_key=str(uuid4()), input_payload={"goal": "legacy audited exchange"})
    summary = usage.summary(org)
    assert summary["capacity_credits"] == old["credits_debited"]
    assert summary["tokens_prompt"] is None and summary["estimated_cost_usd"] is None
    assert summary["users"][0]["capacity_credits"] == old["credits_debited"]
    # Old transports did not create ai_settings either.
    rows("INSERT INTO public.ai_settings(org_id,monthly_budget_credits) VALUES(%s,%s) ON CONFLICT DO NOTHING RETURNING org_id", [org, old["credits_debited"]])
    with pytest.raises(ContractAPIException) as failure:
        start(org, users["ESTIMATOR"])
    assert failure.value.contract_code == "ai_budget_exceeded"
    rows("UPDATE public.ai_settings SET monthly_budget_credits=NULL WHERE org_id=%s RETURNING org_id", [org])
    key = str(uuid4())
    with as_user(users["ESTIMATOR"]):
        new = service.invoke(org_id=org, user_id=users["ESTIMATOR"], capability="agent",
            operation_key=key, input_payload={"goal": "new audited exchange"})
        assert service.invoke(org_id=org, user_id=users["ESTIMATOR"], capability="agent",
            operation_key=key, input_payload={"goal": "new audited exchange"})["audit_id"] == new["audit_id"]
    summary = usage.summary(org)
    assert summary["calls"] == 2
    assert summary["capacity_credits"] == summary["credits_debited"] == old["credits_debited"] + new["credits_debited"]


def test_progress_commits_before_domain_rollback_and_lost_lease_aborts(committed_commercial_rows, monkeypatch):
    org, _, _ = committed_commercial_rows
    job = rows("INSERT INTO public.job_runs(org_id,type,state,locked_by,locked_at,payload,attempt) VALUES(%s,'ai.agent.run','RUNNING','worker-test',now(),'{}',1) RETURNING *", [org])[0]
    observed = []
    def handler(_payload, _context, report):
        with transaction.atomic():
            rows("UPDATE public.tenancy_organizations SET name='domain-rollback' WHERE id=%s RETURNING id", [org])
            with registry.progress_phase("CALCULATING_ENGINE"):
                report(45)
            def read():
                return rows("SELECT progress,phase FROM public.job_runs WHERE id=%s", [job["id"]])[0]
            observed.append(usage.independent(read))
            raise registry.JobPermanentError("synthetic-failure")
    monkeypatch.setattr(registry, "spec_for", lambda _: SimpleNamespace(run=handler))
    worker._execute(job, worker_id="worker-test")
    assert observed == [{"progress": Decimal("45.00"), "phase": "CALCULATING_ENGINE"}]
    assert rows("SELECT name FROM public.tenancy_organizations WHERE id=%s", [org])[0]["name"] != "domain-rollback"
    from jobs.repository import LockLostError, report_progress
    with pytest.raises(LockLostError):
        report_progress(job_id=job["id"], worker_id="different-worker", progress=99, phase="PREPARING_PROPOSAL")
    assert rows("SELECT progress FROM public.job_runs WHERE id=%s", [job["id"]])[0]["progress"] == Decimal("45.00")
