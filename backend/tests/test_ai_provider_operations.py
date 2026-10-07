import json
from datetime import datetime, timezone
from uuid import uuid4

import httpx
import pytest

from ai_gateway import providers
from ai_gateway.contracts import AGENT_SCHEMA
from ai_gateway.engine_tools import TOOLS, EngineTools
from ai_gateway.operations_serializers import AiSettingsSaveSerializer
from ai_gateway.usage import month_start
from dekopen_engine.design_operations import OperationError


def provider(monkeypatch):
    monkeypatch.setenv("AI_GATEWAY_MIMO_API_KEY", "synthetic-private-key")
    monkeypatch.setenv("AI_GATEWAY_MIMO_BASE_URL", "https://provider.example/v1")
    monkeypatch.delenv("AI_GATEWAY_MIMO_MODEL", raising=False)
    monkeypatch.setattr(providers, "_resolve_provider_hosts", lambda _: ["93.184.216.34"])
    return providers.OpenAICompatibleProvider(provider="MIMO")


def reply(content='{"reply":"Revisado","steps":[],"warnings":[]}', calls=None):
    return {"choices": [{"message": {"content": content, "tool_calls": calls}}],
            "usage": {"prompt_tokens": 91, "completion_tokens": 132}}


def invoke(subject, handler, **options):
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        return subject.invoke(route={"provider_model": "verified-model", "tools_mode": "AUTO", **options.pop("route", {})},
                              capability="agent", input_payload={"goal": "synthetic goal"},
                              provider_options=options, operation_key="tenant:operation", client=client)


@pytest.mark.parametrize("status,attempts,code", [(401, 1, "ai_provider_auth"), (403, 1, "ai_provider_auth"),
    (400, 1, "ai_provider_rejected"), (404, 1, "ai_provider_rejected"), (429, 3, "ai_provider_quota"), (503, 3, "ai_provider_error")])
def test_two_retries_only_transient_and_no_key_or_goal_in_logs(monkeypatch, caplog, status, attempts, code):
    subject, requests = provider(monkeypatch), []
    monkeypatch.setattr(providers.time, "sleep", lambda _: None)
    def handler(request):
        requests.append(request)
        return httpx.Response(status, json={"error": {"message": "synthetic-private-key synthetic goal"}})
    with pytest.raises(providers.ProviderError) as failure:
        invoke(subject, handler)
    assert failure.value.code == code
    assert len(requests) == attempts
    assert {request.headers["Idempotency-Key"] for request in requests} == {"tenant:operation"}
    assert "synthetic-private-key" not in caplog.text
    assert "synthetic goal" not in caplog.text


def test_retry_backoff_and_success_usage(monkeypatch):
    subject, seen, delays = provider(monkeypatch), [], []
    monkeypatch.setattr(providers.time, "sleep", delays.append)
    def handler(request):
        seen.append(request)
        return httpx.Response(503, json={}) if len(seen) < 3 else httpx.Response(200, json=reply())
    result = invoke(subject, handler)
    assert result["retries"] == 2 and delays == [0.25, 0.5]
    assert result["tokens_prompt"] == 91 and result["tokens_completion"] == 132
    assert all(request.headers["Idempotency-Key"] == seen[0].headers["Idempotency-Key"] for request in seen)


def test_native_tools_and_paired_observations_use_registry(monkeypatch):
    subject, bodies = provider(monkeypatch), []
    calls = [{"id": "call_fixture", "type": "function", "function": {"name": "validate_position", "arguments": "{}"}}]
    history = [{"role": "assistant", "content": None, "tool_calls": calls},
               {"role": "tool", "tool_call_id": "call_fixture", "content": '{"status":"VALID"}'}]
    def handler(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json=reply("Voy a consultar el motor.", calls))
    result = invoke(subject, handler, tools=TOOLS, tool_choice="auto", tool_messages=history, response_schema=AGENT_SCHEMA)
    assert bodies[0]["tools"] == [{"type": "function", "function": tool} for tool in TOOLS]
    assert bodies[0]["messages"][1:3] == history
    assert json.loads(result["output"])["tool_calls"] == [{"id": "call_fixture", "name": "validate_position", "arguments": {}}]
    assert json.loads(result["output"])["reply"] == ""


@pytest.mark.parametrize("output,passed", [(' {"reply":"Revisado","steps":[],"warnings":[]} ', True),
    ('{"reply":"Revisado","secret_field":"injected"}', False), ('{"reply": 15}', False), ('[]', False)])
def test_explicit_support_rejection_falls_back_to_validated_schema(monkeypatch, output, passed):
    subject, bodies = provider(monkeypatch), []
    def handler(request):
        body = json.loads(request.content)
        bodies.append(body)
        if "tools" in body:
            return httpx.Response(400, json={"error": {"code": "unsupported_parameter", "param": "tools"}})
        return httpx.Response(200, json=reply(output))
    if passed:
        result = invoke(subject, handler, tools=TOOLS, json_output=True, response_schema=AGENT_SCHEMA)
        assert result["fallback"] is True
    else:
        with pytest.raises(providers.ProviderError) as failure:
            invoke(subject, handler, tools=TOOLS, json_output=True, response_schema=AGENT_SCHEMA)
        assert failure.value.code == "ai_provider_error"
        assert failure.value.usage["tokens_prompt"] == 91
    assert len(bodies) == 2 and "tools" not in bodies[1]
    assert "Contrato JSON estricto" in bodies[1]["messages"][0]["content"]


def test_arbitrary_bad_request_never_hides_model_error_as_fallback(monkeypatch):
    subject, seen = provider(monkeypatch), []
    def handler(request):
        seen.append(request)
        return httpx.Response(400, json={"error": {"code": "model_not_found", "param": "tools"}})
    with pytest.raises(providers.ProviderError) as failure:
        invoke(subject, handler, tools=TOOLS, response_schema=AGENT_SCHEMA)
    assert failure.value.code == "ai_provider_rejected" and len(seen) == 1


def test_whole_deadline_cannot_restart_on_retry(monkeypatch):
    subject = provider(monkeypatch)
    now = [0.0]
    monkeypatch.setattr(providers.time, "monotonic", lambda: now[0])
    def handler(request):
        now[0] += 0.9
        raise httpx.ReadTimeout("synthetic timeout", request=request)
    with pytest.raises(providers.ProviderError) as failure:
        invoke(subject, handler, timeout_s=1)
    assert failure.value.code == "ai_provider_timeout"


@pytest.mark.parametrize("debug", ["1", "true", "0", "false"])
def test_debug_cannot_enable_test_provider(monkeypatch, debug):
    monkeypatch.setenv("DEBUG", debug)
    monkeypatch.delenv("AI_GATEWAY_MOCK_ENABLED", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    assert providers._mock_enabled() is False
    with pytest.raises(providers.ProviderError) as failure:
        providers.provider_for({"provider": "MOCK"})
    assert failure.value.code == "ai_provider_mock_disabled"
    monkeypatch.setenv("AI_GATEWAY_MOCK_ENABLED", "1")
    assert isinstance(providers.provider_for({"provider": "MOCK"}), providers.MockProvider)


def test_tenant_model_overrides_bootstrap_model(monkeypatch):
    subject = provider(monkeypatch)
    subject._model = "bootstrap-model"
    assert subject._requested_model({"provider_model": "chosen-model", "tenant_model": True}) == "chosen-model"


def test_month_uses_chilean_calendar_at_utc_boundary():
    start = month_start(datetime(2026, 10, 1, 1, tzinfo=timezone.utc))
    assert (start.month, start.day, start.hour) == (9, 1, 0)
    assert start.tzinfo.key == "America/Santiago"


def test_settings_rejects_credentials_duplicate_routes_and_partial_tariff():
    route = {"provider": "MIMO", "provider_model": "primalabs-ai/MiMo-V2.6-Pro", "timeout_s": 60,
             "retries": 2, "tools_mode": "AUTO", "input_usd_per_million": None, "output_usd_per_million": None}
    from ai_gateway.usage import CAPABILITIES
    data = {"expected_revision": 1, "monthly_budget_credits": 5, "routes": [{**route, "capability": cap} for cap in CAPABILITIES]}
    assert AiSettingsSaveSerializer(data=data).is_valid()
    assert not AiSettingsSaveSerializer(data={**data, "api_key": "synthetic-private-key"}).is_valid()
    assert not AiSettingsSaveSerializer(data={**data, "routes": [data["routes"][0]] * 4}).is_valid()
    assert not AiSettingsSaveSerializer(data={**data, "routes": [{**row, "input_usd_per_million": "1.25"} for row in data["routes"]]}).is_valid()


def test_native_arguments_validate_declared_schema(monkeypatch):
    tools = EngineTools(org_id=uuid4(), user_id=uuid4(), refs={}, product=None, observed_refs=set(), goal="", max_calls=6)
    with pytest.raises(OperationError) as failure:
        tools.call("simulate_ops", {"ops": "not an array"})
    assert failure.value.code == "tool_arguments_invalid"
