"""AI gateway invoke: entitlement prechecks, white-label responses, audit binding."""

import json
from contextlib import contextmanager
from uuid import uuid4

import pytest
from rest_framework.exceptions import APIException

from ai_gateway import service
from ai_gateway.providers import MockProvider, ProviderError


@contextmanager
def _atomic():
    yield


def _route(**over):
    route = {
        "id": uuid4(),
        "capability": "nlp_command",
        "public_name": "DEKOPEN Neural Core™",
        "provider": "MOCK",
        "provider_model": "mock-neural-1",
        "prompt_version": "v1.0",
        "credits_cost": 5,
        "enabled": True,
    }
    route.update(over)
    return route


def _org(**over):
    org = {
        "id": uuid4(),
        "subscription_tier": "PRO",
        "subscription_active": True,
        "credits_balance": 500,
    }
    org.update(over)
    return org


def _patch_env(monkeypatch, *, org=None, route=None, rows_impl=None, provider=None):
    monkeypatch.setattr(service.wallet, "financial_transaction", lambda org_id: _atomic())
    monkeypatch.setattr(
        service.wallet,
        "reconcile",
        lambda org_id: org if org is not None else _org(),
    )
    debited: list[dict] = []
    monkeypatch.setattr(
        service.wallet,
        "debit",
        lambda org_id, credits, audit_id: debited.append(
            {"org_id": org_id, "credits": credits, "audit_id": audit_id}
        ),
    )

    def default_rows(sql, params=None):
        if "FROM public.ai_routes" in sql:
            return [route] if route is not None else [_route()]
        if "INSERT INTO public.ai_audit_logs" in sql:
            return [{"id": uuid4()}]
        return []

    monkeypatch.setattr(service, "rows", rows_impl or default_rows)
    if provider is not None:
        monkeypatch.setattr(service, "provider_for", lambda route: provider)
    return debited


def test_invoke_debits_and_returns_white_label(monkeypatch):
    debited = _patch_env(monkeypatch)
    out = service.invoke(
        org_id=uuid4(),
        user_id=uuid4(),
        capability="nlp_command",
        input_payload={"texto": "divide en dos"},
    )
    assert out["model"] == "DEKOPEN Neural Core™"
    assert out["credits_debited"] == 5
    assert out["output"].startswith("DEKOPEN Neural Core™ [nlp_command]")
    assert len(debited) == 1
    assert debited[0]["credits"] == 5
    # Provider internals never leak into the response.
    assert "provider" not in out
    assert "provider_model" not in out
    assert "mock-neural-1" not in json.dumps(out)


def test_invoke_binds_audit_to_debit(monkeypatch):
    audit_id = uuid4()

    def fake_rows(sql, params=None):
        if "FROM public.ai_routes" in sql:
            return [_route()]
        if "INSERT INTO public.ai_audit_logs" in sql:
            assert params[3] == "mock-neural-1"  # model_used is the real model
            assert params[8] == 5  # points_debited
            assert len(params[12]) == 64  # state hash
            return [{"id": audit_id}]
        return []

    debited = _patch_env(monkeypatch, rows_impl=fake_rows)
    out = service.invoke(
        org_id=uuid4(),
        user_id=uuid4(),
        capability="nlp_command",
        input_payload={"x": 1},
        tool_name="editor_command",
    )
    assert out["audit_id"] == str(audit_id)
    assert debited[0]["audit_id"] == audit_id


def test_unknown_capability_rejected(monkeypatch):
    _patch_env(monkeypatch, rows_impl=lambda sql, params=None: [])
    with pytest.raises(APIException) as failure:
        service.invoke(
            org_id=uuid4(), user_id=uuid4(), capability="nonexistent", input_payload={}
        )
    assert failure.value.contract_code == "ai_capability_unknown"


def test_starter_tier_refused_before_provider(monkeypatch):
    called = []

    def fake_rows(sql, params=None):
        return [_route()]

    _patch_env(monkeypatch, org=_org(subscription_tier="STARTER"), rows_impl=fake_rows)
    monkeypatch.setattr(
        service, "provider_for", lambda route: called.append(route) or MockProvider()
    )
    with pytest.raises(APIException) as failure:
        service.invoke(
            org_id=uuid4(),
            user_id=uuid4(),
            capability="nlp_command",
            input_payload={},
        )
    assert failure.value.contract_code == "ai_entitlement_required"
    assert called == []


def test_inactive_subscription_refused(monkeypatch):
    _patch_env(monkeypatch, org=_org(subscription_active=False))
    with pytest.raises(APIException) as failure:
        service.invoke(
            org_id=uuid4(),
            user_id=uuid4(),
            capability="nlp_command",
            input_payload={},
        )
    assert failure.value.contract_code == "ai_entitlement_required"


def test_insufficient_balance_cancels_before_provider_call(monkeypatch):
    called = []
    _patch_env(monkeypatch, org=_org(credits_balance=4))
    monkeypatch.setattr(
        service, "provider_for", lambda route: called.append(route) or MockProvider()
    )
    with pytest.raises(APIException) as failure:
        service.invoke(
            org_id=uuid4(),
            user_id=uuid4(),
            capability="nlp_command",
            input_payload={},
        )
    assert failure.value.contract_code == "insufficient_credits"
    assert called == []  # the provider request never existed


def test_no_debit_when_provider_fails(monkeypatch):
    debited = _patch_env(monkeypatch)

    def boom(**kwargs):
        raise ProviderError("ai_provider_error")

    monkeypatch.setattr(
        service, "provider_for", lambda route: type("P", (), {"invoke": staticmethod(boom)})()
    )
    with pytest.raises(ProviderError):
        service.invoke(
            org_id=uuid4(),
            user_id=uuid4(),
            capability="nlp_command",
            input_payload={},
        )
    assert debited == []


def test_http_provider_requires_environment(monkeypatch):
    from ai_gateway.providers import HttpProvider

    monkeypatch.delenv("AI_GATEWAY_ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AI_GATEWAY_ANTHROPIC_BASE_URL", raising=False)
    with pytest.raises(ProviderError) as failure:
        HttpProvider(provider="ANTHROPIC")
    assert failure.value.code == "ai_provider_unavailable"


def test_mock_provider_is_deterministic():
    provider = MockProvider()
    route = _route()
    first = provider.invoke(route=route, capability="nlp_command", input_payload={"a": 1})
    second = provider.invoke(route=route, capability="nlp_command", input_payload={"a": 1})
    assert first["output"] == second["output"]
    assert first["tokens_prompt"] >= 1


def test_invoke_response_never_echoes_payload_secrets(monkeypatch):
    _patch_env(monkeypatch)
    out = service.invoke(
        org_id=uuid4(),
        user_id=uuid4(),
        capability="vision_ocr",
        input_payload={"imagen": "datos"},
    )
    assert out["capability"] == "vision_ocr"
    assert set(out) == {
        "audit_id",
        "capability",
        "model",
        "output",
        "tokens_prompt",
        "tokens_completion",
        "latency_ms",
        "credits_debited",
    }
