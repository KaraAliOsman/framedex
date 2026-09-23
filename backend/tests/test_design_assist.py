"""Design assist: provider output is validated against the live product before
it becomes an op — index bounds, enums, ranges; rejected ops are reported,
never silently applied."""

import json
from decimal import Decimal
from uuid import uuid4

import pytest
from rest_framework.exceptions import APIException

from ai_gateway.providers import MockProvider
from projects import design_assist


def _product(modules=2, couplings=1):
    return {
        "modules": [{"width_mm": "1200", "height_mm": "1500"} for _ in range(modules)],
        "couplings": [{"angle_deg": "22.5"} for _ in range(couplings)],
    }


def _position():
    return {"id": uuid4(), "project_id": uuid4(), "system_id": uuid4()}


def _catalog(**overrides):
    catalog = {
        "glass_skus": {"GLASS-4MM", "DVH-4-12-4"},
        "panel_skus": {"PANEL-SANDWICH-24"},
        "thicknesses": {Decimal("4"), Decimal("24")},
    }
    catalog.update(overrides)
    return catalog


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


def _patch_invoke(monkeypatch, output, catalog=None):
    captured = {}

    def fake_invoke(**kwargs):
        captured["input"] = kwargs["input_payload"]
        return _envelope(output)

    monkeypatch.setattr(design_assist.gateway, "invoke", fake_invoke)
    monkeypatch.setattr(design_assist, "_catalog", lambda system_id, org_id: catalog or _catalog())
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
        system_id=uuid4(),
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
        system_id=uuid4(),
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
        system_id=uuid4(),
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
        system_id=uuid4(),
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
        prompt="todo al límite: 99 módulos de 1200 mm",
        system_id=uuid4(),
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
        system_id=uuid4(),
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
            system_id=uuid4(),
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
            system_id=uuid4(),
            operation_key="assist-8",
        )
    assert error.value.get_codes() == "design_assist_product_invalid"


def test_structural_ops_validate_against_the_evolving_assembly(monkeypatch):
    _patch_invoke(
        monkeypatch,
        {
            "ops": [
                {"op": "set_module_count", "count": 12},
                {"op": "add_unit", "side": "right"},
                {"op": "set_opening", "module": 11, "opening": "FIXED"},
                {"op": "set_opening", "module": 12, "opening": "FIXED"},
            ]
        },
    )
    out = design_assist.assist(
        org_id=uuid4(),
        user_id=uuid4(),
        position=_position(),
        product=_product(modules=11, couplings=10),
        prompt="doce más uno",
        system_id=uuid4(),
        operation_key="assist-9",
    )
    assert [op["op"] for op in out["ops"]] == [
        "set_module_count",
        "set_opening",
    ]
    assert [item["reason"] for item in out["rejected"]] == [
        "lado_invalido",
        "apertura_invalida",
    ]


def test_remove_unit_shifts_the_validation_surface(monkeypatch):
    _patch_invoke(
        monkeypatch,
        {
            "ops": [
                {"op": "remove_unit", "module": 0},
                {"op": "set_opening", "module": 1, "opening": "AWNING"},
                {"op": "set_opening", "module": 2, "opening": "AWNING"},
                {"op": "add_unit", "side": "left"},
                {"op": "set_opening", "module": 2, "opening": "FIXED"},
            ]
        },
    )
    out = design_assist.assist(
        org_id=uuid4(),
        user_id=uuid4(),
        position=_position(),
        product=_product(modules=3, couplings=2),
        prompt="reacomoda",
        system_id=uuid4(),
        operation_key="assist-10",
    )
    assert [op["op"] for op in out["ops"]] == [
        "remove_unit",
        "set_opening",
        "add_unit",
        "set_opening",
    ]
    assert out["ops"][3]["module"] == 2
    assert [item["reason"] for item in out["rejected"]] == ["apertura_invalida"]


def test_catalog_skus_are_enforced(monkeypatch):
    _patch_invoke(
        monkeypatch,
        {
            "ops": [
                {"op": "set_glass", "module": 0, "sku": "GLASS-4MM"},
                {"op": "set_glass", "module": 0, "sku": "PANEL-MADE-UP"},
                {"op": "set_panel", "module": 1, "sku": "PANEL-SANDWICH-24"},
                {"op": "set_panel", "module": 1, "sku": "NO-EXISTE"},
                {"op": "set_panel", "module": 1, "sku": None},
            ]
        },
    )
    out = design_assist.assist(
        org_id=uuid4(),
        user_id=uuid4(),
        position=_position(),
        product=_product(),
        prompt="vidrios y panel",
        system_id=uuid4(),
        operation_key="assist-11",
    )
    assert [op["op"] for op in out["ops"]] == ["set_glass", "set_panel", "set_panel"]
    assert [item["reason"] for item in out["rejected"]] == [
        "vidrio_invalido",
        "panel_invalido",
    ]


def test_total_width_floor_tracks_the_simulated_module_count(monkeypatch):
    _patch_invoke(
        monkeypatch,
        {
            "ops": [
                {"op": "set_total_width", "width_mm": "300"},
                {"op": "set_module_count", "count": 1},
                {"op": "set_total_width", "width_mm": "300"},
            ]
        },
    )
    out = design_assist.assist(
        org_id=uuid4(),
        user_id=uuid4(),
        position=_position(),
        product=_product(modules=3, couplings=2),
        system_id=uuid4(),
        prompt="deja 1 módulo de 300 mm",
        operation_key="assist-13",
    )
    # 300 mm is below the 150×3 floor first; after shrinking to one module the
    # same total clears the floor — the simulated count decides, not the
    # submitted summary's count.
    assert [op["op"] for op in out["ops"]] == ["set_module_count", "set_total_width"]
    assert [item["reason"] for item in out["rejected"]] == ["ancho_invalido"]


def test_thickness_must_match_a_glazing_bead_rule(monkeypatch):
    _patch_invoke(
        monkeypatch,
        {
            "ops": [
                {"op": "set_glass_thickness", "module": 0, "mm": "24"},
                {"op": "set_glass_thickness", "module": 0, "mm": "9"},
            ]
        },
    )
    out = design_assist.assist(
        org_id=uuid4(),
        user_id=uuid4(),
        position=_position(),
        product=_product(),
        prompt="espesores",
        system_id=uuid4(),
        operation_key="assist-12",
    )
    assert [op["op"] for op in out["ops"]] == ["set_glass_thickness"]
    assert [item["reason"] for item in out["rejected"]] == ["espesor_invalido"]


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
        {"op": "set_coupling_angle", "coupling": i, "angle_deg": 22.5} for i in range(4)
    ]


def test_undeclared_dimensions_are_rejected_not_invented(monkeypatch):
    """Trust boundary: the model may only cite numbers the user wrote. A
    prompt like 'más ancha' declares no width — a model-invented 2400 must be
    rejected, never applied."""
    _patch_invoke(
        monkeypatch,
        {
            "ops": [
                {"op": "set_total_width", "width_mm": 2400},
                {"op": "set_height", "height_mm": 1500},
                {"op": "set_module_count", "count": 5},
                {"op": "equalize_widths"},
            ]
        },
    )
    out = design_assist.assist(
        org_id=uuid4(),
        user_id=uuid4(),
        position=_position(),
        product=_product(modules=3, couplings=2),
        prompt="hazla más ancha y pareja",
        system_id=uuid4(),
        operation_key="assist-g1",
    )
    assert [op["op"] for op in out["ops"]] == ["equalize_widths"]
    assert [item["reason"] for item in out["rejected"]] == [
        "ancho_no_declarado",
        "alto_no_declarado",
        "cantidad_no_declarada",
    ]


def test_declared_units_ground_numeric_ops(monkeypatch):
    """'2,4 metros' declares 2400 mm; 'tres módulos' declares count 3 —
    Chilean-locale parsing must recognize both as user-entered values."""
    _patch_invoke(
        monkeypatch,
        {
            "ops": [
                {"op": "set_total_width", "width_mm": "2400"},
                {"op": "set_module_count", "count": 3},
                {"op": "set_height", "height_mm": "1500"},
            ]
        },
    )
    out = design_assist.assist(
        org_id=uuid4(),
        user_id=uuid4(),
        position=_position(),
        product=_product(modules=2, couplings=1),
        prompt="tres módulos de 2,4 metros de ancho y 1500 mm de alto",
        system_id=uuid4(),
        operation_key="assist-g2",
    )
    assert [op["op"] for op in out["ops"]] == [
        "set_total_width",
        "set_module_count",
        "set_height",
    ]
    assert out["rejected"] == []


def test_unit_suffixed_literal_does_not_declare_its_raw_value(monkeypatch):
    """'240 cm' declares 2400 mm only — a provider proposing width 240 must
    not pass grounding on the token's unconverted literal."""
    _patch_invoke(
        monkeypatch,
        {"ops": [{"op": "set_total_width", "width_mm": "240"}]},
    )
    out = design_assist.assist(
        org_id=uuid4(),
        user_id=uuid4(),
        position=_position(),
        product=_product(modules=1, couplings=0),
        prompt="ancho total 240 cm",
        system_id=uuid4(),
        operation_key="assist-g3",
    )
    assert out["ops"] == []
    assert out["rejected"][0]["reason"] == "ancho_no_declarado"
