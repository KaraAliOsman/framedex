"""Design assist: provider output is validated against the live product before
it becomes an op — index bounds, enums, ranges; rejected ops are reported,
never silently applied."""

import json
from uuid import uuid4

import pytest
from rest_framework.exceptions import APIException

from ai_gateway.providers import MockProvider
from projects import design_assist


def _product(modules=2, couplings=1):
    return {
        "modules": [
            {"width_mm": "1200", "height_mm": "1500"} for _ in range(modules)
        ],
        "couplings": [{"angle_deg": "22.5"} for _ in range(couplings)],
    }


def _position():
    return {"id": uuid4(), "project_id": uuid4()}


def _envelope(output):
    return {
        "audit_id": str(uuid4()),
        "capability": "design_assist",
        "model": "DEKOPEN Diseñador™",
        "output": output if isinstance(output, str) else json.dumps(output),
        "tokens_prompt": 10,
        "tokens_completion": 10,
        "latency_ms": 1,
        "credits_debited": 10,
    }


def _patch_invoke(monkeypatch, output):
    captured = {}

    def fake_invoke(**kwargs):
        captured["input"] = kwargs["input_payload"]
        return _envelope(output)

    monkeypatch.setattr(design_assist.gateway, "invoke", fake_invoke)
    return captured


def test_assist_returns_validated_ops(monkeypatch):
    _patch_invoke(
        monkeypatch,
        {
            "ops": [
                {"op": "set_module_count", "count": 3},
                {"op": "equalize_widths"},
                {"op": "set_opening", "module": 1, "opening": "SLIDING_2L"},
            ],
            "notes": "3 módulos correderas",
        },
    )
    out = design_assist.assist(
        org_id=uuid4(),
        user_id=uuid4(),
        position=_position(),
        product=_product(modules=3, couplings=2),
        prompt="3 módulos correderas",
        operation_key="assist-1",
    )
    assert len(out["ops"]) == 3
    assert out["rejected"] == []
    assert out["model"] == "DEKOPEN Diseñador™"
    assert out["notes"] == "3 módulos correderas"


def test_assist_audits_the_submitted_product(monkeypatch):
    captured = _patch_invoke(monkeypatch, {"ops": [], "notes": "nada"})
    design_assist.assist(
        org_id=uuid4(),
        user_id=uuid4(),
        position=_position(),
        product=_product(),
        prompt="iguala anchos",
        operation_key="assist-2",
    )
    assert captured["input"]["product"]["modules"][0]["width_mm"] == "1200"
    assert captured["input"]["product"]["modules"][1]["index"] == 1
    assert "set_module_count" in captured["input"]["ops_contract"]


def test_out_of_bounds_module_is_rejected(monkeypatch):
    _patch_invoke(
        monkeypatch,
        {"ops": [{"op": "set_opening", "module": 5, "opening": "FIXED"}], "notes": ""},
    )
    out = design_assist.assist(
        org_id=uuid4(),
        user_id=uuid4(),
        position=_position(),
        product=_product(modules=2),
        prompt="fijo en el quinto",
        operation_key="assist-3",
    )
    assert out["ops"] == []
    assert out["rejected"][0]["reason"] == "apertura_invalida"


def test_unknown_op_is_rejected_not_applied(monkeypatch):
    _patch_invoke(
        monkeypatch,
        {"ops": [{"op": "delete_project"}, {"op": "set_height", "height_mm": 1600}]},
    )
    out = design_assist.assist(
        org_id=uuid4(),
        user_id=uuid4(),
        position=_position(),
        product=_product(),
        prompt="borra todo y alto 1600",
        operation_key="assist-4",
    )
    assert [op["op"] for op in out["ops"]] == ["set_height"]
    assert out["rejected"][0]["reason"] == "operacion_desconocida"


def test_ranges_and_enums_enforced(monkeypatch):
    _patch_invoke(
        monkeypatch,
        {
            "ops": [
                {"op": "set_module_count", "count": 99},
                {"op": "set_coupling_angle", "coupling": 0, "angle_deg": 120},
                {"op": "set_opening", "module": 0, "opening": "ROTATE"},
                {"op": "set_module_width", "module": 0, "width_mm": 1200},
            ]
        },
    )
    out = design_assist.assist(
        org_id=uuid4(),
        user_id=uuid4(),
        position=_position(),
        product=_product(),
        prompt="todo al límite",
        operation_key="assist-5",
    )
    assert [op["op"] for op in out["ops"]] == ["set_module_width"]
    assert out["ops"][0]["width_mm"] == "1200"
    assert len(out["rejected"]) == 3


def test_last_module_cannot_be_removed(monkeypatch):
    _patch_invoke(monkeypatch, {"ops": [{"op": "remove_unit", "module": 0}]})
    out = design_assist.assist(
        org_id=uuid4(),
        user_id=uuid4(),
        position=_position(),
        product=_product(modules=1, couplings=0),
        prompt="quita el módulo",
        operation_key="assist-6",
    )
    assert out["ops"] == []
    assert out["rejected"][0]["reason"] == "modulo_invalido"


def test_bad_provider_document_is_a_502(monkeypatch):
    _patch_invoke(monkeypatch, "no es json {")
    with pytest.raises(APIException) as error:
        design_assist.assist(
            org_id=uuid4(),
            user_id=uuid4(),
            position=_position(),
            product=_product(),
            prompt="x",
            operation_key="assist-7",
        )
    assert error.value.get_codes() == "design_assist_bad_output"


def test_invalid_product_summary_is_a_400(monkeypatch):
    _patch_invoke(monkeypatch, {"ops": []})
    with pytest.raises(APIException) as error:
        design_assist.assist(
            org_id=uuid4(),
            user_id=uuid4(),
            position=_position(),
            product={"modules": []},
            prompt="x",
            operation_key="assist-8",
        )
    assert error.value.get_codes() == "design_assist_product_invalid"


def test_mock_provider_emits_ops_for_spanish_intent():
    provider = MockProvider()
    out = provider.invoke(
        route={"public_name": "DEKOPEN Diseñador™", "provider_model": "mock-design-1"},
        capability="design_assist",
        input_payload={
            "prompt": "3 módulos corredera, ancho total de 2400, iguales",
            "product": _product(modules=3, couplings=2),
        },
    )
    document = json.loads(out["output"])
    ops = [op["op"] for op in document["ops"]]
    assert "set_module_count" in ops
    assert "set_total_width" in ops
    assert "equalize_widths" in ops
    assert ops.count("set_opening") == 3


def test_mock_provider_bows_angles_and_empty_notes():
    provider = MockProvider()
    out = provider.invoke(
        route={"public_name": "DEKOPEN Diseñador™", "provider_model": "mock-design-1"},
        capability="design_assist",
        input_payload={
            "prompt": "convierte en arco",
            "product": _product(modules=5, couplings=4),
        },
    )
    document = json.loads(out["output"])
    assert document["ops"] == [
        {"op": "set_coupling_angle", "coupling": i, "angle_deg": 22.5}
        for i in range(4)
    ]
