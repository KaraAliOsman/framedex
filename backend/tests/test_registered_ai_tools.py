"""Numeric provenance, finite tool budgets and durable clarification behavior."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from ai_gateway import agent
from ai_gateway.engine_tools import EngineTools
from backend.tests.test_ai_agent import _patch, _doc
from dekopen_engine.design_operations import OperationError


def tools(**kwargs):
    return EngineTools(org_id=uuid4(), user_id=uuid4(), refs={}, product=None,
                       observed_refs=set(), goal="ajusta la ventana", **kwargs)


def test_wire_values_are_exact_and_derived_numbers_can_ground_an_operation(monkeypatch):
    service = tools()
    identity = uuid4()
    monkeypatch.setattr(service, "_execute", lambda *_: {
        "position_id": identity, "effective_date": date(2026, 10, 7), "width_mm": Decimal("1700.00")})
    output, fresh = service.call("calculate_position", {})
    assert fresh and output == {"position_id": str(identity), "effective_date": "2026-10-07", "width_mm": "1700.00"}
    service._check_operations([{"op": "set_module_width", "module": "m1", "width_mm": "1700"}])
    with pytest.raises(OperationError) as error:
        service._check_operations([{"op": "set_module_width", "module": "m1", "width_mm": "1777"}])
    assert error.value.code == "measure_ungrounded"


def test_cached_calls_do_not_consume_more_budget_or_leak_mutable_output(monkeypatch):
    service = tools(max_calls=1)
    calls = []
    monkeypatch.setattr(service, "_execute", lambda *args: calls.append(args) or {"width_mm": "1700"})
    output, fresh = service.call("calculate_position", {})
    output["width_mm"] = "INVENTED"
    cached, fresh = service.call("calculate_position", {})
    assert not fresh and cached["width_mm"] == "1700" and len(calls) == 1
    with pytest.raises(OperationError) as error:
        service.call("validate_position", {})
    assert error.value.code == "tool_budget_exceeded"


@pytest.mark.parametrize("op", [
    {"op": "set_module_width", "module": "m1", "width_mm": True},
    {"op": "set_module_width", "module": "m1", "width_mm": {"value": "1"}},
    {"op": "add_position", "system_id": "id", "template": "FIXED", "location": "Obra", "dims": {"width_mm": "1500", "height_mm": "1200"}},
])
def test_malformed_numeric_intent_and_silent_catalog_defaults_are_rejected(op):
    with pytest.raises(OperationError):
        tools()._check_operations([op])


def test_unobserved_entity_is_refused_before_repository_access(monkeypatch):
    service = tools()
    calls = []
    monkeypatch.setattr("projects.service.position_row", lambda *args: calls.append(args))
    output, _ = service.call("calculate_position", {"position_id": str(uuid4())})
    assert output["error"] == "unobserved_ref" and calls == []


def test_errors_and_client_history_cannot_supply_numeric_evidence(monkeypatch):
    service = tools()
    monkeypatch.setattr(service, "_execute", lambda *_: {"error": "unavailable", "detail": "1700 mm"})
    service.call("calculate_position", {})
    with pytest.raises(OperationError):
        service._check_operations([{"op": "set_module_width", "module": "m1", "width_mm": "1700"}])


def test_total_timeout_stops_before_a_provider_call(monkeypatch):
    calls = _patch(monkeypatch)
    clock = iter([0, agent.TOTAL_TIMEOUT_S + 1])
    monkeypatch.setattr(agent.time, "monotonic", lambda: next(clock))
    with pytest.raises(Exception) as error:
        agent.act(org_id=uuid4(), user_id=uuid4(), surface="dashboard", refs={},
                  goal="Revisa el proyecto", product=None, history=[], operation_key="timeout")
    assert getattr(error.value, "contract_code", None) == "ai_agent_timeout" and calls == []


def test_discount_proposal_requires_a_human_decision(monkeypatch):
    project = str(uuid4())
    _patch(monkeypatch, contexts={"project": {"surface": "project", "id": project}}, outputs=[_doc(
        reply="Revisa el descuento antes de aplicarlo.",
        steps=[{"kind": "artifact", "artifact": {"kind": "quote_draft", "title": "Descuento", "payload": {"discount_pct": "0.05", "confirmed": False}, "references": [project]}}])])
    result = agent.act(org_id=uuid4(), user_id=uuid4(), surface="project", refs={"project_id": project},
                       goal="Baja el precio un 5 %", product=None, history=[], operation_key="discount")
    assert result["state"] == "WAITING_FOR_APPROVAL", result
    assert result["artifacts"][0]["payload"]["discount_pct"] == "0.05"


def test_root_discount_draft_is_preserved_without_authorizing_a_write(monkeypatch):
    project, foreign = str(uuid4()), str(uuid4())
    _patch(monkeypatch, contexts={"project": {"surface": "project", "id": project}}, outputs=[_doc(
        reply="Revisa el descuento antes de aplicarlo.",
        artifact={"kind": "quote_draft", "title": "Descuento propuesto", "payload": {
            "discount_pct": "0.05", "confirmed": True, "base_price": None},
            "references": {"project_id": project, "foreign": foreign}})])
    result = agent.act(org_id=uuid4(), user_id=uuid4(), surface="project", refs={"project_id": project},
                       goal="Baja el precio un 5 %", product=None, history=[], operation_key="root-discount")
    assert result["state"] == "WAITING_FOR_APPROVAL"
    assert result["steps"] == []
    draft = result["artifacts"][0]
    assert draft["references"] == [project]
    assert draft["payload"] == {"discount_pct": "0.05", "confirmed": False, "base_price": None}


@pytest.mark.parametrize("title,payload", [
    ("Precio 1777 CLP", {"discount_pct": "0.05"}),
    ("Descuento propuesto", {"discount_pct": "0.05", "net": "1777"}),
])
def test_root_artifact_cannot_launder_an_invented_number(monkeypatch, title, payload):
    project = str(uuid4())
    _patch(monkeypatch, contexts={"project": {"surface": "project", "id": project}}, outputs=[_doc(
        reply="Revisa el proyecto.", artifact={"kind": "quote_draft", "title": title,
        "payload": payload, "references": {"project_id": project}})])
    result = agent.act(org_id=uuid4(), user_id=uuid4(), surface="project", refs={"project_id": project},
                       goal="Baja el precio un 5 %", product=None, history=[], operation_key="root-invention")
    assert result["artifacts"] == []


def test_restored_project_proposal_keeps_integer_counts_valid_for_apply():
    import json
    from ai_gateway.jobs import _decode
    from dekopen_engine.design_operations import validate_operation
    op = {"op": "duplicate_position", "position_id": str(uuid4()), "count": 4, "location": "Dormitorios"}
    decoded = _decode({"result": json.dumps({"steps": [{"kind": "project_ops", "ops": [op]}], "exact": 1.2345})})
    restored = decoded["result"]["steps"][0]["ops"][0]
    assert type(restored["count"]) is int
    assert validate_operation(restored) == op
    assert decoded["result"]["exact"] == Decimal("1.2345")


@pytest.mark.parametrize("rounds", [1, 6, 12])
def test_progress_never_retreats_during_long_native_tool_runs(monkeypatch, rounds):
    from jobs.registry import CURRENT_PHASE
    monkeypatch.setattr(agent, "MAX_ROUNDS", rounds)
    outputs = [_doc(reply="", tool_calls=[{"id": f"call_{index}", "name": "calculate_position", "arguments": {}}]) for index in range(rounds - 1)] + [_doc()]
    _patch(monkeypatch, outputs=outputs)
    checkpoints = []
    agent.act(org_id=uuid4(), user_id=uuid4(), surface="dashboard", refs={},
              goal="Revisa el proyecto", product=None, history=[], operation_key="long-native",
              progress=lambda value: checkpoints.append((value, CURRENT_PHASE.get())))
    values = [value for value, _ in checkpoints]
    assert values == sorted(values)
    assert next(value for value, phase in checkpoints if phase == "PREPARING_PROPOSAL") == 80
    assert all(value < 80 for value, phase in checkpoints if phase != "PREPARING_PROPOSAL" and value < 90)


@pytest.mark.parametrize("fresh,error", [(False, False), (True, True)])
def test_cached_or_failed_tool_output_cannot_promote_foreign_references(monkeypatch, fresh, error):
    foreign = str(uuid4())
    _patch(monkeypatch, outputs=[_doc(reply="", tool_calls=[{"id": "call_fixture", "name": "calculate_position", "arguments": {}}]),
        _doc(steps=[{"kind": "navigate", "path": f"/projects/{foreign}", "label": "Abrir proyecto"}])])
    output = {"project_id": foreign, **({"error": "not_found"} if error else {})}
    monkeypatch.setattr(EngineTools, "call", lambda *_: (output, fresh))
    result = agent.act(org_id=uuid4(), user_id=uuid4(), surface="dashboard", refs={},
                       goal="Revisa el proyecto", product=None, history=[], operation_key="cached-reference")
    assert result["steps"] == []

