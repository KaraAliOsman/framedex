"""Agent loop: server-side queries, validated steps, grounded replies."""

import json
from uuid import uuid4

import pytest
from rest_framework.exceptions import APIException

from ai_gateway import agent


def _envelope(output: str, *, debited: int = 3):
    return {
        "audit_id": str(uuid4()),
        "capability": "agent",
        "model": "mimo-v2.6-pro",
        "output": output,
        "tokens_prompt": 10,
        "tokens_completion": 10,
        "latency_ms": 1,
        "credits_debited": debited,
    }


def _doc(**over):
    doc = {"reply": "Encontré el proyecto.", "steps": [], "warnings": []}
    doc.update(over)
    return json.dumps(doc, ensure_ascii=False)


def _patch(monkeypatch, *, contexts=None, outputs=None, invoke_fail=None):
    """Patch the gateway and context builder; `outputs` is consumed per round."""
    calls = []
    contexts = contexts or {"dashboard": {"surface": "dashboard", "organization": {"name": "Org"}}}
    outputs = list(outputs or [_doc()])

    def fake_build(org_id, surface, refs):
        if surface in contexts:
            return contexts[surface]
        raise agent._ContextError("ai_context_not_found")

    def fake_invoke(**kwargs):
        calls.append(kwargs)
        if invoke_fail is not None:
            raise invoke_fail
        if len(outputs) > 1:
            return _envelope(outputs.pop(0))
        return _envelope(outputs[0])

    monkeypatch.setattr(agent, "build_context", fake_build)
    monkeypatch.setattr(agent.gateway, "invoke", fake_invoke)
    monkeypatch.setattr(
        agent.jobs,
        "create_job",
        lambda **kw: {"id": str(uuid4()), "transcript": []},
    )
    monkeypatch.setattr(
        agent.jobs,
        "finish_job",
        lambda **kw: {"id": str(kw["job_id"]), "state": kw["state"]},
    )
    return calls


def test_agent_simple_reply_and_navigate(monkeypatch):
    project_id = uuid4()
    contexts = {
        "dashboard": {
            "surface": "dashboard",
            "organization": {"name": "Org"},
            "recent_projects": [{"id": str(project_id), "code": "OB-1"}],
        },
        "project": {"surface": "project", "id": str(project_id), "code": "OB-1"},
    }
    output = _doc(
        steps=[
            {
                "kind": "navigate",
                "path": f"/projects/{project_id}",
                "label": "Abrir proyecto",
            }
        ]
    )
    calls = _patch(monkeypatch, contexts=contexts, outputs=[output])
    result = agent.act(
        org_id=uuid4(),
        user_id=uuid4(),
        surface="dashboard",
        refs={},
        goal="¿Dónde está el proyecto OB-1?",
        product=None,
        history=[],
        operation_key="goal-1",
    )
    assert result["reply"] == "Encontré el proyecto."
    assert result["steps"] == [
        {"kind": "navigate", "tool": "navigate", "path": f"/projects/{project_id}", "label": "Abrir proyecto"}
    ]
    # The caller's own surface counts as provenance.
    assert result["queries"] == [{"surface": "dashboard", "tool": "get_dashboard", "status": "ok"}]
    assert calls[0]["capability"] == "agent"
    assert calls[0]["tool_name"] == "agent"
    assert calls[0]["input_payload"]["actions"]["ops_available"] is False
    assert calls[0]["input_payload"]["actions"]["prepare_routes"]["emit_revision"] == (
        "/projects/{project_id}/pricing"
    )
    assert calls[0]["input_payload"]["product"] is None


def test_agent_query_loop_feeds_observation_and_accumulates_credits(monkeypatch):
    project_id = uuid4()
    contexts = {
        "dashboard": {"surface": "dashboard", "organization": {"name": "Org"}},
        "production": {
            "surface": "production",
            "organization": {"name": "Org"},
            "orders": [{"id": str(project_id), "code": "OT-9", "status": "BLOCKED"}],
        },
    }
    outputs = [
        _doc(reply="", steps=[{"kind": "query", "surface": "production"}]),
        _doc(
            reply="Hay 1 orden bloqueada: OT-9.",
            steps=[
                {
                    "kind": "navigate",
                    "path": f"/production/{project_id}",
                    "label": "Ver OT-9",
                }
            ],
        ),
    ]
    calls = _patch(monkeypatch, contexts=contexts, outputs=outputs)
    result = agent.act(
        org_id=uuid4(),
        user_id=uuid4(),
        surface="dashboard",
        refs={},
        goal="¿Qué órdenes están bloqueadas?",
        product=None,
        history=[],
        operation_key="goal-2",
    )
    assert len(calls) == 2
    assert calls[0]["operation_key"].endswith(":r0")
    assert calls[1]["operation_key"].endswith(":r1")
    # The second round carried the executed observation back to the model.
    observations = calls[1]["input_payload"]["observations"]
    assert observations[0]["surface"] == "production"
    assert observations[0]["context"]["orders"][0]["code"] == "OT-9"
    # The navigate step is grounded in the observed entity.
    assert result["steps"][0]["path"] == f"/production/{project_id}"
    assert result["queries"] == [
        {"surface": "dashboard", "tool": "get_dashboard", "status": "ok"},
        {"surface": "production", "tool": "get_production_state", "status": "ok"},
    ]
    assert result["credits_debited"] == 6


def test_agent_query_error_becomes_observation_not_crash(monkeypatch):
    contexts = {
        "dashboard": {"surface": "dashboard", "organization": {"name": "Org"}},
        # "project" absent → _ContextError
    }
    outputs = [
        _doc(
            reply="",
            steps=[
                {"kind": "query", "surface": "project", "refs": {"project_id": str(uuid4())}}
            ],
        ),
        _doc(reply="No encontré ese proyecto en tu organización."),
    ]
    _patch(monkeypatch, contexts=contexts, outputs=outputs)
    result = agent.act(
        org_id=uuid4(),
        user_id=uuid4(),
        surface="dashboard",
        refs={},
        goal="abre el proyecto xyz",
        product=None,
        history=[],
        operation_key="goal-3",
    )
    assert result["queries"] == [
        {"surface": "dashboard", "tool": "get_dashboard", "status": "ok"},
        {"surface": "project", "tool": "get_project", "status": "error"},
    ]


def test_agent_navigate_rejects_ungrounded_uuid(monkeypatch):
    contexts = {"dashboard": {"surface": "dashboard", "organization": {"name": "Org"}}}
    ghost = uuid4()
    output = _doc(
        steps=[
            {"kind": "navigate", "path": f"/projects/{ghost}", "label": "Inventado"},
            {"kind": "navigate", "tool": "navigate", "path": "/projects", "label": "Proyectos"},
        ]
    )
    _patch(monkeypatch, contexts=contexts, outputs=[output])
    result = agent.act(
        org_id=uuid4(),
        user_id=uuid4(),
        surface="dashboard",
        refs={},
        goal="ve al proyecto",
        product=None,
        history=[],
        operation_key="goal-4",
    )
    # The hallucinated-UUID step drops; the safe one survives.
    assert result["steps"] == [
        {"kind": "navigate", "tool": "navigate", "path": "/projects", "label": "Proyectos"}
    ]


def test_agent_navigate_rejects_disallowed_path(monkeypatch):
    contexts = {"dashboard": {"surface": "dashboard", "organization": {"name": "Org"}}}
    output = _doc(
        steps=[
            {"kind": "navigate", "path": "https://evil.example/x", "label": "x"},
            {"kind": "navigate", "path": "/admin/secret", "label": "x"},
        ]
    )
    _patch(monkeypatch, contexts=contexts, outputs=[output])
    result = agent.act(
        org_id=uuid4(),
        user_id=uuid4(),
        surface="dashboard",
        refs={},
        goal="x",
        product=None,
        history=[],
        operation_key="goal-5",
    )
    assert result["steps"] == []


def test_agent_prepare_requires_allowlisted_action(monkeypatch):
    project_id = uuid4()
    contexts = {
        "project": {
            "surface": "project",
            "organization": {"name": "Org"},
            "id": str(project_id),
        }
    }
    output = _doc(
        steps=[
            {
                "kind": "prepare",
                "action": "emit_revision",
                "path": f"/projects/{project_id}/pricing",
                "label": "Emitir revisión",
            },
            # Right action, wrong route — a prepare can never deep-link
            # somewhere its label doesn't mean.
            {
                "kind": "prepare",
                "action": "emit_revision",
                "path": f"/projects/{project_id}",
                "label": "Emitir revisión",
            },
            {
                "kind": "prepare",
                "action": "delete_org",
                "path": f"/projects/{project_id}",
                "label": "Borrar todo",
            },
        ]
    )
    _patch(monkeypatch, contexts=contexts, outputs=[output])
    result = agent.act(
        org_id=uuid4(),
        user_id=uuid4(),
        surface="project",
        refs={"project_id": str(project_id)},
        goal="emite la revisión",
        product=None,
        history=[],
        operation_key="goal-6",
    )
    assert result["steps"] == [
        {
            "kind": "prepare",
            "tool": "generate_document_preview",
            "action": "emit_revision",
            "path": f"/projects/{project_id}/pricing",
            "label": "Emitir revisión",
        }
    ]


def test_agent_ungrounded_reply_refused(monkeypatch):
    contexts = {"dashboard": {"surface": "dashboard", "organization": {"name": "Org"}}}
    _patch(
        monkeypatch,
        contexts=contexts,
        outputs=[_doc(reply="Tienes 47 proyectos por $1.234.567.")],
    )
    with pytest.raises(APIException) as error:
        agent.act(
            org_id=uuid4(),
            user_id=uuid4(),
            surface="dashboard",
            refs={},
            goal="cuántos hay",
            product=None,
            history=[],
            operation_key="goal-7",
        )
    assert error.value.get_codes() == "ai_agent_ungrounded"
    assert error.value.status_code == 502


def test_agent_bad_output_refused(monkeypatch):
    contexts = {"dashboard": {"surface": "dashboard", "organization": {"name": "Org"}}}
    _patch(monkeypatch, contexts=contexts, outputs=["no json at all"])
    with pytest.raises(APIException) as error:
        agent.act(
            org_id=uuid4(),
            user_id=uuid4(),
            surface="dashboard",
            refs={},
            goal="x",
            product=None,
            history=[],
            operation_key="goal-8",
        )
    assert error.value.get_codes() == "ai_agent_bad_output"


def test_agent_ops_step_validated_through_design_contract(monkeypatch):
    position_id = uuid4()
    system_id = uuid4()
    product = {
        "id": "pos",
        "modules": [{"id": "m1", "width_mm": 1200, "ref": "m1"}],
        "couplings": [],
    }
    contexts = {
        "position": {
            "surface": "position",
            "organization": {"name": "Org"},
            "id": str(position_id),
            "system_id": str(system_id),
        }
    }
    output = _doc(
        steps=[
            {
                "kind": "ops",
                "label": "Ajustar ancho",
                "ops": [
                    {"op": "set_module_width", "module": "m1", "width_mm": 1400},
                    {"op": "set_module_width", "module": "m1", "width_mm": 9999},
                ],
            }
        ]
    )
    calls = _patch(monkeypatch, contexts=contexts, outputs=[output])

    summary = {"modules": [{"ref": "m1", "width_mm": 1200}], "couplings": []}
    validated_ops = [{"op": "set_module_width", "module": "m1", "width_mm": 1400}]
    dropped = [{"op": "set_module_width", "reason": "ancho_no_declarado"}]

    monkeypatch.setattr(agent.design_assist, "_summary", lambda p: summary)
    monkeypatch.setattr(
        agent.projects_service, "position_row", lambda *a, **k: {"system_id": system_id}
    )
    monkeypatch.setattr(
        agent.design_assist, "_catalog", lambda sid, oid: {"systems": [], "glass": []}
    )
    monkeypatch.setattr(
        agent.design_assist, "_declared_values", lambda goal: set()
    )
    monkeypatch.setattr(
        agent.design_assist,
        "_validate_ops",
        lambda ops, s, c, d: (validated_ops, dropped),
    )
    result = agent.act(
        org_id=uuid4(),
        user_id=uuid4(),
        surface="position",
        refs={"position_id": str(position_id)},
        goal="cambia el ancho a 1400",
        product=product,
        history=[],
        operation_key="goal-9",
    )
    assert result["steps"] == [
        {"kind": "ops", "tool": "preview_commands", "ops": validated_ops, "label": "Ajustar ancho"}
    ]
    assert result["rejected"] == dropped
    # The provider sees the live product wire — without it the model has no
    # real refs to emit ops against.
    assert calls[0]["input_payload"]["product"] == product
    assert calls[0]["input_payload"]["actions"]["ops_available"] is True


def test_agent_ops_step_dropped_off_position_surface(monkeypatch):
    contexts = {"dashboard": {"surface": "dashboard", "organization": {"name": "Org"}}}
    output = _doc(
        steps=[{"kind": "ops", "ops": [{"op": "set_height", "height_mm": 1500}]}]
    )
    _patch(monkeypatch, contexts=contexts, outputs=[output])
    result = agent.act(
        org_id=uuid4(),
        user_id=uuid4(),
        surface="dashboard",
        refs={},
        goal="cambia el alto",
        product=None,
        history=[],
        operation_key="goal-10",
    )
    assert result["steps"] == []


def test_agent_provider_error_propagates(monkeypatch):
    from ai_gateway.providers import ProviderError

    _patch(
        monkeypatch,
        contexts={"dashboard": {"surface": "dashboard"}},
        invoke_fail=ProviderError("provider_unavailable"),
    )
    with pytest.raises(ProviderError):
        agent.act(
            org_id=uuid4(),
            user_id=uuid4(),
            surface="dashboard",
            refs={},
            goal="x",
            product=None,
            history=[],
            operation_key="goal-11",
        )


def test_agent_queries_same_surface_per_entity(monkeypatch):
    """A comparison needs the same surface once per entity — dedupe is
    (surface, refs), never the surface alone."""
    project_a, project_b = uuid4(), uuid4()
    contexts = {
        "dashboard": {
            "surface": "dashboard",
            "organization": {"name": "Org"},
            "projects": [{"id": str(project_a)}, {"id": str(project_b)}],
        },
    }
    outputs = [
        _doc(reply="", steps=[
            {"kind": "query", "surface": "project",
             "refs": {"project_id": str(project_a)}},
            {"kind": "query", "surface": "project",
             "refs": {"project_id": str(project_b)}},
            {"kind": "query", "surface": "project",
             "refs": {"project_id": str(project_a)}},  # exact dup — skipped
        ]),
        _doc(reply="Comparé ambos proyectos."),
    ]
    _patch(monkeypatch, contexts=contexts, outputs=outputs)
    seen = []

    def fake_build(org_id, surface, refs):
        if surface == "project":
            seen.append(refs["project_id"])
            return {"surface": "project", "id": refs["project_id"]}
        return contexts[surface]

    monkeypatch.setattr(agent, "build_context", fake_build)
    result = agent.act(
        org_id=uuid4(), user_id=uuid4(), surface="dashboard", refs={},
        goal="Compara los dos proyectos recientes", product=None,
        history=[], operation_key="goal-cmp",
    )
    assert seen == [str(project_a), str(project_b)]
    assert [q["surface"] for q in result["queries"]] == [
        "dashboard", "project", "project",
    ]


def test_agent_query_unobserved_ref_is_error_not_fetch(monkeypatch):
    """A hallucinated id must not reach the projection layer — it becomes an
    error observation so the model learns to use only ids it was shown."""
    ghost = uuid4()
    contexts = {"dashboard": {"surface": "dashboard",
                            "organization": {"name": "Org"}}}
    outputs = [
        _doc(reply="", steps=[
            {"kind": "query", "surface": "project",
             "refs": {"project_id": str(ghost)}},
        ]),
        _doc(reply="Ese proyecto no aparece en tu contexto."),
    ]
    calls = _patch(monkeypatch, contexts=contexts, outputs=outputs)
    result = agent.act(
        org_id=uuid4(), user_id=uuid4(), surface="dashboard", refs={},
        goal="Dime el proyecto fantasma", product=None,
        history=[], operation_key="goal-ghost",
    )
    assert result["reply"] == "Ese proyecto no aparece en tu contexto."
    observations = calls[1]["input_payload"]["observations"]
    assert observations[0]["error"] == "ai_context_ref_unobserved"


def test_agent_query_malformed_refs_are_skipped_not_crash(monkeypatch):
    """Model output is untrusted: a non-dict refs value or a non-scalar ref
    must be rejected by shape validation before the (surface, refs) key is
    computed — never a TypeError bubbling out of _query_key."""
    contexts = {"dashboard": {"surface": "dashboard",
                            "organization": {"name": "Org"}}}
    outputs = [
        _doc(reply="Sin datos.", steps=[
            {"kind": "query", "surface": "project", "refs": "abc"},
            {"kind": "query", "surface": "project",
             "refs": {"project_id": ["a", "b"]}},
            {"kind": "query", "surface": "project",
             "refs": {"project_id": True}},
        ]),
    ]
    calls = _patch(monkeypatch, contexts=contexts, outputs=outputs)
    result = agent.act(
        org_id=uuid4(), user_id=uuid4(), surface="dashboard", refs={},
        goal="pruébalo", product=None, history=[], operation_key="goal-badrefs",
    )
    assert result["reply"] == "Sin datos."
    # No malformed query reached the fetch layer — one round, no fetch calls.
    assert len(calls) == 1
    assert [q["surface"] for q in result["queries"]] == ["dashboard"]
