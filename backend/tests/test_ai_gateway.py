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
        operation_key="op-1",
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
        operation_key="op-1",
        input_payload={"x": 1},
        tool_name="editor_command",
    )
    assert out["audit_id"] == str(audit_id)
    assert debited[0]["audit_id"] == audit_id


def test_unknown_capability_rejected(monkeypatch):
    _patch_env(monkeypatch, rows_impl=lambda sql, params=None: [])
    with pytest.raises(APIException) as failure:
        service.invoke(
            org_id=uuid4(), user_id=uuid4(), capability="nonexistent", operation_key="op-1", input_payload={}
        )
    assert failure.value.contract_code == "ai_capability_unknown"


def test_starter_tier_refused_before_provider(monkeypatch):
    called = []

    def fake_rows(sql, params=None):
        if "FROM public.ai_routes" in sql:
            return [_route()]
        return []

    _patch_env(monkeypatch, org=_org(subscription_tier="STARTER"), rows_impl=fake_rows)
    monkeypatch.setattr(
        service, "provider_for", lambda route: called.append(route) or MockProvider()
    )
    with pytest.raises(APIException) as failure:
        service.invoke(
            org_id=uuid4(),
            user_id=uuid4(),
            capability="nlp_command",
            operation_key="op-1",
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
            operation_key="op-1",
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
            operation_key="op-1",
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
            operation_key="op-1",
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
        operation_key="op-1",
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


def test_replay_returns_stored_response_without_provider_or_debit(monkeypatch):
    stored = {
        "capability": "nlp_command",
        "model": "DEKOPEN Neural Core™",
        "output": "respuesta anterior",
        "tokens_prompt": 7,
        "tokens_completion": 11,
        "latency_ms": 42,
        "credits_debited": 5,
    }
    audit_id = uuid4()
    called = []

    def fake_rows(sql, params=None):
        if "FROM public.ai_audit_logs" in sql:
            return [
                {
                    "id": audit_id,
                    "tool_name": "nlp_command",
                    "state_hash_before": service._input_hash({"x": 1}),
                    "output_payload": stored,
                }
            ]
        return []

    debited = _patch_env(monkeypatch, rows_impl=fake_rows)
    monkeypatch.setattr(
        service, "provider_for", lambda route: called.append(route) or MockProvider()
    )
    out = service.invoke(
        org_id=uuid4(),
        user_id=uuid4(),
        capability="nlp_command",
        operation_key="op-1",
        input_payload={"x": 1},
    )
    assert out == {"audit_id": str(audit_id), **stored}
    assert called == []
    assert debited == []


def test_replay_with_different_payload_conflicts(monkeypatch):
    stored = {"capability": "nlp_command", "output": "otra"}

    def fake_rows(sql, params=None):
        if "FROM public.ai_audit_logs" in sql:
            return [
                {
                    "id": uuid4(),
                    "tool_name": "nlp_command",
                    "state_hash_before": service._input_hash({"original": 1}),
                    "output_payload": stored,
                }
            ]
        return []

    _patch_env(monkeypatch, rows_impl=fake_rows)
    with pytest.raises(APIException) as failure:
        service.invoke(
            org_id=uuid4(),
            user_id=uuid4(),
            capability="nlp_command",
            operation_key="op-1",
            input_payload={"distinto": 2},
        )
    assert failure.value.contract_code == "ai_operation_conflict"


def test_oversized_provider_output_is_a_provider_error(monkeypatch):
    _patch_env(monkeypatch)

    def huge(**kwargs):
        return {
            "output": "x" * (service.MAX_OUTPUT_CHARS + 1),
            "tokens_prompt": 1,
            "tokens_completion": 1,
            "latency_ms": 1,
        }

    monkeypatch.setattr(
        service, "provider_for", lambda route: type("P", (), {"invoke": staticmethod(huge)})()
    )
    with pytest.raises(ProviderError) as failure:
        service.invoke(
            org_id=uuid4(),
            user_id=uuid4(),
            capability="nlp_command",
            operation_key="op-1",
            input_payload={},
        )
    assert failure.value.code == "ai_provider_output_too_large"


def test_malformed_provider_body_is_a_provider_error(monkeypatch):
    from ai_gateway.providers import HttpProvider

    class _Response:
        status_code = 200
        content = b'{"unexpected": true}'
        headers = {}

        def raise_for_status(self):
            return None

        def json(self):
            return ["not", "an", "object"]

    monkeypatch.setenv("AI_GATEWAY_TESTP_API_KEY", "k")
    monkeypatch.setenv("AI_GATEWAY_TESTP_BASE_URL", "https://p.example")
    monkeypatch.setattr(
        "httpx.post", lambda *a, **k: _Response()
    )
    with pytest.raises(ProviderError) as failure:
        HttpProvider(provider="TESTP").invoke(
            route=_route(), capability="nlp_command", input_payload={}
        )
    assert failure.value.code == "ai_provider_error"


def test_input_payload_size_capped():
    from ai_gateway.serializers import AiInvokeRequestSerializer

    serializer = AiInvokeRequestSerializer(
        data={
            "capability": "nlp_command",
            "operation_key": "op-123456",
            "input_payload": {"blob": "x" * 70_000},
        }
    )
    assert not serializer.is_valid()
    assert "input_payload" in serializer.errors


def test_http_provider_caps_body_size(monkeypatch):
    from ai_gateway.providers import HttpProvider, MAX_BODY_BYTES

    class _Response:
        status_code = 200
        content = b"x" * (MAX_BODY_BYTES + 1)
        headers = {}

        def raise_for_status(self):
            return None

        def json(self):
            return {}

    monkeypatch.setenv("AI_GATEWAY_TESTP2_API_KEY", "k")
    monkeypatch.setenv("AI_GATEWAY_TESTP2_BASE_URL", "https://p.example")
    monkeypatch.setattr("httpx.post", lambda *a, **k: _Response())
    with pytest.raises(ProviderError) as failure:
        HttpProvider(provider="TESTP2").invoke(
            route=_route(), capability="nlp_command", input_payload={}
        )
    assert failure.value.code == "ai_provider_output_too_large"


def test_replay_with_different_tool_name_conflicts(monkeypatch):
    stored = {"capability": "nlp_command", "output": "respuesta"}

    def fake_rows(sql, params=None):
        if "FROM public.ai_audit_logs" in sql:
            return [
                {
                    "id": uuid4(),
                    "tool_name": "editor_command",
                    "state_hash_before": service._input_hash({"x": 1}),
                    "output_payload": stored,
                }
            ]
        return []

    _patch_env(monkeypatch, rows_impl=fake_rows)
    with pytest.raises(APIException) as failure:
        service.invoke(
            org_id=uuid4(),
            user_id=uuid4(),
            capability="nlp_command",
            operation_key="op-1",
            input_payload={"x": 1},
            tool_name="catalog_import",
        )
    assert failure.value.contract_code == "ai_operation_conflict"


def test_http_provider_rejects_internal_urls(monkeypatch):
    from ai_gateway.providers import HttpProvider

    monkeypatch.setenv("AI_GATEWAY_INT_API_KEY", "k")
    for bad in ("http://provider.example", "https://127.0.0.1", "https://10.0.0.4",
                "https://[fd00::1]", "provider.example"):
        monkeypatch.setenv("AI_GATEWAY_INT_BASE_URL", bad)
        with pytest.raises(ProviderError) as failure:
            HttpProvider(provider="INT")
        assert failure.value.code == "ai_provider_unavailable", bad


def test_non_string_provider_output_is_a_provider_error(monkeypatch):
    from ai_gateway.providers import HttpProvider

    class _Response:
        status_code = 200
        content = b'{"output": {"answer": "x"}}'
        headers = {}

        def raise_for_status(self):
            return None

        def json(self):
            return {"output": {"answer": "x"}, "usage": {"prompt_tokens": 3}}

    monkeypatch.setenv("AI_GATEWAY_OBJ_API_KEY", "k")
    monkeypatch.setenv("AI_GATEWAY_OBJ_BASE_URL", "https://p.example")
    monkeypatch.setattr("httpx.post", lambda *a, **k: _Response())
    with pytest.raises(ProviderError) as failure:
        HttpProvider(provider="OBJ").invoke(
            route=_route(), capability="nlp_command", input_payload={}
        )
    assert failure.value.code == "ai_provider_error"
