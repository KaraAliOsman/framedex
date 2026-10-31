"""P14 · The assistant changes the person's own interface and splits
independent work into parallel sub-assistants — inside the same guards."""

import json
from uuid import uuid4

import pytest
from rest_framework.exceptions import APIException

from ai_gateway import agent, subagents
from projects import interface


def _envelope(output: str):
    return {"audit_id": str(uuid4()), "capability": "agent", "model": "m", "output": output,
            "tokens_prompt": 1, "tokens_completion": 1, "latency_ms": 1, "credits_debited": 1}


def _run(monkeypatch, steps, *, delegation=None, autonomy="draft", mode="work", role="ESTIMATOR"):
    calls, spawned, saved, outcomes = [], [], [], []
    output = json.dumps({"reply": "Listo.", "steps": steps, "warnings": []}, ensure_ascii=False)

    def fake_invoke(**kwargs):
        calls.append(kwargs)
        return _envelope(output)

    monkeypatch.setattr(agent, "build_context",
                        lambda org_id, surface, refs: {"surface": "dashboard", "organization": {"name": "Org"}})
    monkeypatch.setattr(agent.gateway, "invoke", fake_invoke)
    monkeypatch.setattr(agent.jobs, "create_job", lambda **kw: {"id": str(uuid4()), "transcript": []})
    monkeypatch.setattr(agent.jobs, "finish_job", lambda **kw: {"id": str(kw["job_id"]), "state": kw["state"]})
    monkeypatch.setattr(agent.jobs, "record_assistant_outcomes", lambda **kw: outcomes.extend(kw["entries"]))
    monkeypatch.setattr(interface, "get_preferences", lambda org, user: dict(interface.DEFAULTS))
    monkeypatch.setattr(interface, "save_preferences",
                        lambda org, user, changes: saved.append(changes) or {**interface.DEFAULTS, **changes})
    monkeypatch.setattr(subagents, "spawn", lambda **kw: spawned.append(kw) or {
        "children": [{"job_id": str(uuid4()), "label": t["label"], "goal": t["goal"]} for t in kw["step"]["tasks"]]})
    result = agent.act(org_id=uuid4(), user_id=uuid4(), surface="dashboard", refs={}, goal="Haz esto",
                       product=None, history=[], operation_key=f"goal-{uuid4()}", autonomy=autonomy,
                       role=role, interaction_mode=mode, delegation=delegation)
    return result, calls, spawned, saved, outcomes


def test_interface_clean_refuses_unknown_keys_and_values():
    assert interface.clean({"text_size": "large", "reduce_motion": True}) == {
        "text_size": "large", "reduce_motion": True}
    for bad in ({"color": "red"}, {"density": "huge"}, {"project_tab": "prices"}, "large"):
        with pytest.raises(APIException):
            interface.clean(bad)


def test_tasks_need_two_to_four_distinct_goals():
    one = {"goal": "Prepara la obra Casa Rodrigo", "label": "Casa Rodrigo"}
    two = {"goal": "Prepara la obra Oficina Ñuñoa", "label": "Oficina Ñuñoa"}
    assert subagents.tasks_from({"tasks": [one, two]}) == [one, two]
    assert subagents.tasks_from({"tasks": [one]}) is None
    assert subagents.tasks_from({"tasks": [one, one]}) is None
    assert subagents.tasks_from({"tasks": [one, two, *[{"goal": f"g{i}"} for i in range(3)]]}) is None
    assert subagents.tasks_from({"tasks": [one, {"goal": "x" * 601}]}) is None
    assert subagents.tasks_from({"tasks": "dos tareas"}) is None


def test_draft_applies_the_interface_with_undo_and_a_receipt(monkeypatch):
    result, calls, _, saved, outcomes = _run(monkeypatch, [
        {"kind": "interface", "preferences": {"text_size": "large", "density": "workshop"},
         "label": "Texto grande", "apply": True}])
    step = result["steps"][0]
    assert step["kind"] == "interface" and step["apply_requested"] is True
    assert saved == [{"text_size": "large", "density": "workshop"}]
    assert step["applied"]["previous"] == interface.DEFAULTS
    assert outcomes[0]["ops"] == ["interface"] and "operation_id" not in outcomes[0]
    assert calls[0]["input_payload"]["actions"]["may_delegate"] is False


def test_invalid_interface_is_rejected_never_saved(monkeypatch):
    result, _, _, saved, _ = _run(monkeypatch, [
        {"kind": "interface", "preferences": {"theme": "dark"}, "label": "Tema", "apply": True}])
    assert saved == []
    assert {"op": "interface", "reason": "preferences_invalid"} in result["rejected"]


def test_chat_only_proposes_the_interface(monkeypatch):
    result, _, _, saved, _ = _run(monkeypatch, [
        {"kind": "interface", "preferences": {"reduce_motion": True}, "label": "Menos movimiento", "apply": True}],
        mode="chat")
    assert saved == []
    assert all(not step.get("apply_requested") for step in result["steps"])


def test_draft_spawns_parallel_subtasks_with_the_session_factor(monkeypatch):
    tasks = [{"goal": "Cotiza la obra A con dos ventanas", "label": "Obra A"},
             {"goal": "Cotiza la obra B con una puerta", "label": "Obra B"}]
    result, calls, spawned, _, outcomes = _run(
        monkeypatch, [{"kind": "delegate", "tasks": tasks, "label": "Dos obras", "apply": True}],
        delegation={"session_aal": "aal2", "parent_ai_job_id": None})
    assert calls[0]["input_payload"]["actions"]["may_delegate"] is True
    assert len(spawned) == 1
    assert spawned[0]["session_aal"] == "aal2" and spawned[0]["autonomy"] == "draft"
    assert [child["label"] for child in result["steps"][0]["applied"]["children"]] == ["Obra A", "Obra B"]
    assert outcomes[0]["ops"] == ["delegate"]


def test_a_subtask_never_delegates_again(monkeypatch):
    tasks = [{"goal": "Tarea uno"}, {"goal": "Tarea dos"}]
    result, calls, spawned, _, _ = _run(
        monkeypatch, [{"kind": "delegate", "tasks": tasks, "label": "Otra vez", "apply": True}],
        delegation={"session_aal": "aal2", "parent_ai_job_id": str(uuid4())})
    assert calls[0]["input_payload"]["actions"]["may_delegate"] is False
    assert spawned == []
    assert {"op": "delegate", "reason": "delegation_not_allowed"} in [
        {"op": item["op"], "reason": item["reason"]} for item in result["rejected"]]


def test_operator_cannot_delegate(monkeypatch):
    tasks = [{"goal": "Tarea uno"}, {"goal": "Tarea dos"}]
    _, calls, spawned, _, _ = _run(
        monkeypatch, [{"kind": "delegate", "tasks": tasks, "label": "Dos", "apply": True}],
        delegation={"session_aal": "aal2"}, role="OPERATOR")
    assert calls[0]["input_payload"]["actions"]["may_delegate"] is False
    assert spawned == []
