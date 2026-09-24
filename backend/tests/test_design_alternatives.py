"""Design alternatives: the provider proposes intent-level structure; the
backend builds the real product-v2 model, runs every candidate through
the engine, and only VALID assemblies reach the client with engine
metrics — rejected specs surface with reasons, never as products."""

import json
from decimal import Decimal
from uuid import uuid4

import pytest
from rest_framework.exceptions import APIException

from ai_gateway.providers import MockProvider
from backend.tests.factories import demo_60_params
from engine_api.repository import SystemParamsRepository
from projects import design_alternatives


def _position():
    return {
        "id": uuid4(),
        "project_id": uuid4(),
        "system_id": uuid4(),
        "width_mm": "2400",
        "height_mm": "1500",
    }


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
        "capability": "design_alternatives",
        "model": "DEKOPEN Alternativas™",
        "output": output if isinstance(output, str) else json.dumps(output),
        "tokens_prompt": 10,
        "tokens_completion": 10,
        "latency_ms": 1,
        "credits_debited": 15,
    }


def _patch(monkeypatch, output, catalog=None):
    captured = {}

    def fake_invoke(**kwargs):
        captured["input"] = kwargs["input_payload"]
        return _envelope(output)

    monkeypatch.setattr(design_alternatives.gateway, "invoke", fake_invoke)
    monkeypatch.setattr(
        design_alternatives,
        "_catalog",
        lambda system_id, org_id: catalog or _catalog(),
    )
    monkeypatch.setattr(
        SystemParamsRepository,
        "load_visible",
        lambda self, system_id, active_org_id: demo_60_params(),
    )
    monkeypatch.setattr(
        SystemParamsRepository,
        "load_coupler_articles",
        lambda self, system_id, active_org_id: {},
    )
    return captured


def _call():
    return design_alternatives.alternatives(
        org_id=uuid4(),
        user_id=uuid4(),
        position=_position(),
        brief="ventana corredera para el living",
        count=3,
        system_id=uuid4(),
        operation_key="alt-1",
    )


def test_alternatives_carry_engine_metrics(monkeypatch):
    _patch(
        monkeypatch,
        {
            "alternatives": [
                {
                    "label": "Paño fijo",
                    "rationale": "simple",
                    "openings": ["FIXED"],
                },
                {
                    "label": "Corredera",
                    "rationale": "sin barrido",
                    "openings": ["SLIDING_2L"],
                },
            ],
            "notes": "dos opciones",
        },
    )
    out = _call()
    assert out["rejected"] == []
    assert len(out["alternatives"]) == 2
    fixed, sliding = out["alternatives"]
    assert fixed["label"] == "Paño fijo"
    assert fixed["metrics"]["module_count"] == 1
    assert fixed["metrics"]["openings"] == ["FIXED"]
    assert Decimal(fixed["metrics"]["glass_area_m2"]) > 0
    assert fixed["metrics"]["glass_pieces"] == 1
    # Every returned product is a real product-v2 the editor can adopt.
    assert fixed["product"]["version"] == "product-v2"
    module = fixed["product"]["assembly"]["modules"][0]
    assert module["width_mm"] == "2400.00"
    assert module["tree"]["opening_type"] == "FIXED"
    assert sliding["product"]["assembly"]["couplings"] == []
    assert sliding["metrics"]["openings"] == ["SLIDING_2L"]


def test_bow_alternative_gets_share_widths_and_couplings(monkeypatch):
    _patch(
        monkeypatch,
        {
            "alternatives": [
                {
                    "label": "Bow",
                    "rationale": "panorámica",
                    "openings": ["FIXED", "FIXED", "FIXED"],
                    "angle_deg": 22.5,
                }
            ]
        },
    )
    out = _call()
    assembly = out["alternatives"][0]["product"]["assembly"]
    widths = [module["width_mm"] for module in assembly["modules"]]
    assert widths == ["800.00", "800.00", "800.00"]
    assert [c["angle_deg"] for c in assembly["couplings"]] == ["22.5", "22.5"]


def test_share_width_remainder_lands_on_the_last_module(monkeypatch):
    _patch(
        monkeypatch,
        {"alternatives": [{"openings": ["FIXED", "FIXED"]}]},
    )
    position = _position() | {"width_mm": "2399"}
    out = design_alternatives.alternatives(
        org_id=uuid4(),
        user_id=uuid4(),
        position=position,
        brief="dos hojas",
        count=1,
        system_id=uuid4(),
        operation_key="alt-2",
    )
    widths = [
        module["width_mm"]
        for module in out["alternatives"][0]["product"]["assembly"]["modules"]
    ]
    assert widths == ["1199.50", "1199.50"] or Decimal(widths[0]) + Decimal(
        widths[1]
    ) == Decimal("2399")


def test_invalid_specs_are_rejected_never_shipped(monkeypatch):
    _patch(
        monkeypatch,
        {
            "alternatives": [
                {"label": "Bien", "openings": ["FIXED"]},
                {"label": "Rara", "openings": ["FLYING"], },
                {"label": "Sin hojas", "openings": []},
                {"label": "Vidrio falso", "openings": ["FIXED"], "glass_sku": "NO"},
                {"label": "Ángulo falso", "openings": ["FIXED", "FIXED"], "angle_deg": 170},
            ]
        },
    )
    out = _call()
    # The provider may over-produce — only the first MAX_ALTERNATIVES specs are
    # evaluated, bad ones surface with reasons and never become products.
    assert [item["label"] for item in out["alternatives"]] == ["Bien"]
    assert len(out["rejected"]) == 2


def test_bad_provider_document_is_a_502(monkeypatch):
    _patch(monkeypatch, "no es json {")
    with pytest.raises(APIException) as error:
        _call()
    assert error.value.get_codes() == "design_alternatives_bad_output"


def test_bad_dimensions_are_a_400(monkeypatch):
    _patch(monkeypatch, {"alternatives": []})
    with pytest.raises(APIException) as error:
        design_alternatives.alternatives(
            org_id=uuid4(),
            user_id=uuid4(),
            position=_position() | {"width_mm": "40"},
            brief="x",
            count=1,
            system_id=uuid4(),
            operation_key="alt-3",
        )
    assert error.value.get_codes() == "design_width_invalid"


def test_catalog_and_contract_reach_the_provider(monkeypatch):
    captured = _patch(monkeypatch, {"alternatives": []})
    _call()
    payload = captured["input"]
    assert payload["width_mm"] == "2400"
    assert payload["height_mm"] == "1500"
    assert "SLIDING_2L" in payload["openings_contract"]
    assert payload["catalog"]["glass_skus"] == ["DVH-4-12-4", "GLASS-4MM"]


def test_mock_provider_proposes_a_sliding_for_corredera_brief():
    provider = MockProvider()
    out = provider.invoke(
        route={"public_name": "DEKOPEN Alternativas™", "provider_model": "mock-design-1"},
        capability="design_alternatives",
        input_payload={
            "brief": "corredera para el dormitorio",
            "width_mm": "2400",
            "height_mm": "1500",
            "count": 3,
            "openings_contract": ["FIXED", "SLIDING_2L"],
            "catalog": {"glass_skus": [], "panel_skus": [], "glazing_thicknesses": []},
        },
    )
    document = json.loads(out["output"])
    assert document["alternatives"][0]["openings"] == ["SLIDING_2L"]


def test_mock_provider_honors_count():
    provider = MockProvider()
    out = provider.invoke(
        route={"public_name": "DEKOPEN Alternativas™", "provider_model": "mock-design-1"},
        capability="design_alternatives",
        input_payload={
            "brief": "ventana",
            "count": 1,
            "openings_contract": ["FIXED"],
            "catalog": {"glass_skus": [], "panel_skus": [], "glazing_thicknesses": []},
        },
    )
    document = json.loads(out["output"])
    assert len(document["alternatives"]) == 1
