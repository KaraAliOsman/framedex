"""A native simulation and its artifact share one bounded observation."""
from uuid import UUID

import pytest

from ai_gateway.engine_tools import EngineTools
from dekopen_engine.design_operations import OperationError


def test_explicit_and_contextual_project_simulation_reuse_verified_result(monkeypatch):
    identity = "00000000-0000-4000-8000-000000000001"
    tools = EngineTools(org_id=UUID(identity), user_id=UUID(identity),
                        refs={"project_id": identity}, product=None,
                        observed_refs=frozenset({identity}), goal="Low-E", max_calls=1)
    executed = []

    def execute(name, arguments):
        executed.append((name, arguments))
        return {"valid": True, "diff": ["verified"]}

    monkeypatch.setattr(tools, "_execute", execute)
    ops = [{"op": "apply_to_positions", "filter": {"location_contains": "2º piso"},
            "ops": [{"op": "set_glass", "module": "*", "sku": "declared-lowe"}]}]
    first, fresh = tools.call("preview_project_operations", {"project_id": identity, "ops": ops})
    assert fresh
    artifact, fresh = tools.call("preview_project_operations", {"ops": ops})
    assert not fresh and artifact == first
    artifact["diff"].clear()
    replay, _ = tools.call("preview_project_operations", {"ops": ops})
    assert replay["diff"] == ["verified"]
    assert len(executed) == len(tools.calls) == 1
    with pytest.raises(OperationError, match="El trabajo agotó"):
        tools.call("preview_project_operations", {"project_id": identity, "ops": []})
