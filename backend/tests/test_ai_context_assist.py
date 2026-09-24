"""Contextual Ask: typed projections, server-owned context, answer contract."""

import json
from uuid import uuid4

import pytest
from rest_framework.exceptions import APIException

from ai_gateway import assist, context


def _org_row(**over):
    row = {
        "name": "Demo Org",
        "subscription_tier": "PRO",
        "credits_balance": 500,
        "currency": "CLP",
    }
    row.update(over)
    return row


def _envelope(output: str):
    return {
        "audit_id": str(uuid4()),
        "capability": "context_assist",
        "model": "mock-context-1",
        "output": output,
        "tokens_prompt": 10,
        "tokens_completion": 10,
        "latency_ms": 1,
        "credits_debited": 2,
    }


def _patch(monkeypatch, *, rows_impl=None, output=None):
    calls = []
    monkeypatch.setattr(
        context,
        "rows",
        rows_impl
        or (lambda sql, params=None: [_org_row()] if "tenancy_organizations" in sql else []),
    )
    monkeypatch.setattr(
        assist.gateway,
        "invoke",
        lambda **kwargs: calls.append(kwargs) or _envelope(output or _good_output()),
    )
    return calls


def _good_output() -> str:
    return json.dumps(
        {
            "answer": "El contexto muestra el estado actual del proyecto.",
            "actions": [{"kind": "navigate", "path": "/projects", "label": "Ver proyectos"}],
            "warnings": [],
        },
        ensure_ascii=False,
    )


def test_ask_dashboard_projects_context_into_payload(monkeypatch):
    org_id = uuid4()

    def fake_rows(sql, params=None):
        if "tenancy_organizations" in sql:
            return [_org_row()]
        if "SELECT " in sql and "count(*)" in sql:
            return [
                {
                    "projects": 4,
                    "positions": 9,
                    "work_orders_open": 2,
                    "clients": 1,
                    "profile_systems": 3,
                }
            ]
        if "ORDER BY updated_at DESC LIMIT 5" in sql:
            return [
                {
                    "code": "OB-1",
                    "name": "Edificio Sur",
                    "client_name": "Concesionaria X",
                    "status": "DRAFT",
                }
            ]
        return []

    calls = _patch(monkeypatch, rows_impl=fake_rows)
    result = assist.ask(
        org_id=org_id,
        user_id=uuid4(),
        surface="dashboard",
        refs={},
        question="¿Cuántos proyectos hay?",
        operation_key="ask-1",
    )
    assert result["answer"] == "El contexto muestra el estado actual del proyecto."
    assert result["actions"] == [
        {"kind": "navigate", "path": "/projects", "label": "Ver proyectos"}
    ]
    payload = calls[0]["input_payload"]
    assert payload["surface"] == "dashboard"
    assert payload["context"]["counts"]["projects"] == 4
    assert payload["context"]["recent_projects"][0]["code"] == "OB-1"
    assert payload["context"]["organization"]["name"] == "Demo Org"


def test_ask_unknown_surface_rejected(monkeypatch):
    _patch(monkeypatch)
    with pytest.raises(APIException) as error:
        assist.ask(
            org_id=uuid4(),
            user_id=uuid4(),
            surface="payroll",
            refs={},
            question="hola",
            operation_key="ask-1",
        )
    assert error.value.get_codes() == "ai_surface_unknown"
    assert error.value.status_code == 400


def test_ask_missing_ref_rejected_before_provider(monkeypatch):
    def fake_rows(sql, params=None):
        if "tenancy_organizations" in sql:
            return [_org_row()]
        if "FROM public.projects" in sql:
            return []
        return []

    calls = _patch(monkeypatch, rows_impl=fake_rows)
    with pytest.raises(APIException) as error:
        assist.ask(
            org_id=uuid4(),
            user_id=uuid4(),
            surface="project",
            refs={"project_id": str(uuid4())},
            question="¿estado?",
            operation_key="ask-1",
        )
    assert error.value.get_codes() == "ai_context_not_found"
    assert error.value.status_code == 404
    # The entity miss happens before any provider call — no debit.
    assert calls == []


def test_ask_missing_ref_field_rejected_before_provider(monkeypatch):
    calls = _patch(monkeypatch)
    with pytest.raises(APIException) as error:
        assist.ask(
            org_id=uuid4(),
            user_id=uuid4(),
            surface="project",
            refs={},
            question="hola",
            operation_key="ask-1",
        )
    assert error.value.get_codes() == "ai_context_ref_required"
    assert error.value.status_code == 400
    assert calls == []


def test_ask_malformed_output_refused(monkeypatch):
    _patch(monkeypatch, output="no soy json")
    with pytest.raises(APIException) as error:
        assist.ask(
            org_id=uuid4(),
            user_id=uuid4(),
            surface="dashboard",
            refs={},
            question="hola",
            operation_key="ask-1",
        )
    assert error.value.get_codes() == "ai_assist_bad_output"
    assert error.value.status_code == 502


def test_ask_actions_allowlist_strips_bad_paths(monkeypatch):
    output = json.dumps(
        {
            "answer": "ok",
            "actions": [
                {"kind": "navigate", "path": "javascript:alert(1)", "label": "evil"},
                {"kind": "navigate", "path": "https://evil.example/x", "label": "evil"},
                {"kind": "navigate", "path": "//evil.example", "label": "evil"},
                {"kind": "delete_project", "path": "/projects", "label": "bad kind"},
                {"kind": "navigate", "path": "/projects/abc", "label": "Ver proyecto"},
            ],
            "warnings": "not-a-list",
        }
    )
    _patch(monkeypatch, output=output)
    result = assist.ask(
        org_id=uuid4(),
        user_id=uuid4(),
        surface="dashboard",
        refs={},
        question="hola",
        operation_key="ask-1",
    )
    assert result["actions"] == [
        {"kind": "navigate", "path": "/projects/abc", "label": "Ver proyecto"}
    ]
    assert result["warnings"] == []


def test_ask_project_surface_builds_projected_context(monkeypatch):
    org_id = uuid4()
    project_id = uuid4()

    def fake_rows(sql, params=None):
        if "tenancy_organizations" in sql:
            return [_org_row()]
        if "FROM public.projects WHERE id=%s AND org_id=%s" in sql:
            return [
                {
                    "id": project_id,
                    "code": "OB-1",
                    "name": "Edificio Sur",
                    "client_name": "Concesionaria X",
                    "status": "DRAFT",
                    "current_revision": "REV-A",
                    "total_price_net": "100.00",
                    "total_price_tax": "19.00",
                    "total_price_gross": "119.00",
                }
            ]
        if "FROM public.project_positions" in sql:
            return [
                {
                    "position_index": 1,
                    "location_tag": "Fachada",
                    "typology": "VENTANA",
                    "width_mm": "1200.00",
                    "height_mm": "1400.00",
                }
            ]
        if "FROM public.project_versions" in sql:
            return [
                {
                    "revision_code": "REV-A",
                    "documentary_complete": True,
                    "production_allowed": True,
                }
            ]
        if "FROM public.project_payments" in sql:
            return [{"count": 1, "collected": "50.00"}]
        return []

    calls = _patch(monkeypatch, rows_impl=fake_rows)
    assist.ask(
        org_id=org_id,
        user_id=uuid4(),
        surface="project",
        refs={"project_id": str(project_id)},
        question="¿cuánto se ha cobrado?",
        operation_key="ask-1",
    )
    ctx = calls[0]["input_payload"]["context"]
    assert ctx["code"] == "OB-1"
    assert ctx["payments"]["payments_collected"] == "50.00"
    assert ctx["latest_version"]["revision"] == "REV-A"
    assert ctx["positions"][0]["typology"] == "VENTANA"


def test_mock_provider_context_assist_shape():
    from ai_gateway.providers import MockProvider

    out = MockProvider().invoke(
        route={
            "id": uuid4(),
            "capability": "context_assist",
            "public_name": "DEKOPEN Asistente Contextual™",
            "provider": "MOCK",
            "provider_model": "mock-context-1",
            "prompt_version": "v1.0",
            "credits_cost": 2,
            "enabled": True,
        },
        capability="context_assist",
        input_payload={
            "question": "hola",
            "surface": "dashboard",
            "context": {
                "surface": "dashboard",
                "organization": {"name": "Demo", "plan": "PRO"},
                "counts": {"projects": 2, "work_orders_open": 1},
            },
        },
    )
    document = json.loads(out["output"])
    assert document["answer"].startswith("Estás en la superficie 'dashboard'")
    assert document["actions"] == []
    assert "2 proyectos" in document["answer"]


def test_ask_answer_citing_uncited_number_refused(monkeypatch):
    """§5: a number nowhere in the context or the question is an invention —
    the answer is refused rather than passed off as an explanation."""
    _patch(
        monkeypatch,
        output=json.dumps(
            {
                "answer": "El consumo estimado es 3,2 barras.",
                "actions": [],
                "warnings": [],
            },
            ensure_ascii=False,
        ),
    )
    with pytest.raises(APIException) as error:
        assist.ask(
            org_id=uuid4(),
            user_id=uuid4(),
            surface="dashboard",
            refs={},
            question="¿cuántas barras necesito?",
            operation_key="ask-1",
        )
    assert error.value.get_codes() == "ai_assist_ungrounded"
    assert error.value.status_code == 502


def test_ask_answer_may_cite_context_and_question_numbers(monkeypatch):
    """A projected value is a citation; the user's own number in the question
    grounds too ('2.400' in a 2.400 mm paño). Both must come through."""

    def fake_rows(sql, params=None):
        if "tenancy_organizations" in sql:
            return [_org_row()]
        if "count(*)" in sql:
            return [
                {
                    "projects": 4,
                    "positions": 9,
                    "work_orders_open": 2,
                    "clients": 20,
                    "profile_systems": 3,
                }
            ]
        return []

    _patch(
        monkeypatch,
        rows_impl=fake_rows,
        output=json.dumps(
            {
                "answer": "Tienes ~20 clientes y preguntas por un paño de 2.400 mm.",
                "actions": [],
                "warnings": [],
            },
            ensure_ascii=False,
        ),
    )
    result = assist.ask(
        org_id=uuid4(),
        user_id=uuid4(),
        surface="dashboard",
        refs={},
        question="¿qué paño de 2.400 mm conviene?",
        operation_key="ask-1",
    )
    assert result["answer"].startswith("Tienes ~20 clientes")


def test_mock_provider_refuses_when_disabled(monkeypatch):
    """§9: a production stack can never answer silently with fabricated
    content — MOCK off fails visibly instead of serving."""
    from ai_gateway.providers import ProviderError, provider_for

    monkeypatch.setenv("AI_GATEWAY_MOCK_ENABLED", "0")
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)
    with pytest.raises(ProviderError) as failure:
        provider_for({"provider": "MOCK"})
    assert failure.value.code == "ai_provider_mock_disabled"
    monkeypatch.setenv("AI_GATEWAY_MOCK_ENABLED", "1")
    provider_for({"provider": "MOCK"})


def test_provider_timeout_env_overrides_and_fails_visibly(monkeypatch):
    from ai_gateway.providers import HttpProvider, ProviderError

    monkeypatch.setenv("AI_GATEWAY_TO_API_KEY", "k")
    monkeypatch.setenv("AI_GATEWAY_TO_BASE_URL", "https://9.9.9.9/v1")
    monkeypatch.setenv("AI_GATEWAY_TO_TIMEOUT_S", "12.5")
    assert HttpProvider(provider="TO").timeout == 12.5
    monkeypatch.setenv("AI_GATEWAY_TO_TIMEOUT_S", "abc")
    with pytest.raises(ProviderError) as failure:
        HttpProvider(provider="TO")
    assert failure.value.code == "ai_provider_unavailable"
    monkeypatch.setenv("AI_GATEWAY_TO_TIMEOUT_S", "0")
    with pytest.raises(ProviderError):
        HttpProvider(provider="TO")


def test_ask_navigation_actions_grounded_to_context_ids(monkeypatch):
    """A provider can propose navigation — but only to entities the context
    literally carries: a deep link to an id it never saw is dropped, not
    passed through. Root section paths stay allowed."""
    org_id, project_id, intruder_id = uuid4(), uuid4(), uuid4()

    def fake_rows(sql, params=None):
        if "tenancy_organizations" in sql:
            return [_org_row()]
        if "FROM public.projects" in sql:
            return [
                {
                    "id": project_id,
                    "code": "PRJ-1",
                    "name": "P",
                    "client_name": "C",
                    "status": "DRAFT",
                    "current_revision": None,
                    "total_price_net": 0,
                    "total_price_tax": 0,
                    "total_price_gross": 0,
                }
            ]
        if "FROM public.project_payments" in sql:
            return [{"count": 0, "collected": 0}]
        return []

    output = json.dumps(
        {
            "answer": "Ok.",
            "actions": [
                {
                    "kind": "navigate",
                    "path": f"/projects/{project_id}",
                    "label": "Este proyecto",
                },
                {
                    "kind": "navigate",
                    "path": f"/projects/{intruder_id}",
                    "label": "Otro proyecto",
                },
                {"kind": "navigate", "path": "/production", "label": "Producción"},
            ],
            "warnings": [],
        },
        ensure_ascii=False,
    )
    _patch(monkeypatch, rows_impl=fake_rows, output=output)
    result = assist.ask(
        org_id=org_id,
        user_id=uuid4(),
        surface="project",
        refs={"project_id": str(project_id)},
        question="navega",
        operation_key="ask-ids",
    )
    paths = [a["path"] for a in result["actions"]]
    assert paths == [f"/projects/{project_id}", "/production"]
