"""P08 · each window the agent creates from a request cites its phrase.

Measures and quantity must be written in that phrase; non-numeric choices
the request does not state become assumptions computed by the server."""

import json
from decimal import Decimal
from uuid import uuid4

from ai_gateway import agent, origins
from ai_gateway.providers import _recorded_round

REQUEST = (
    "Cotiza esto para Rodrigo Soto: Hola, necesito cotizar 2 ventanas oscilobatientes para el living "
    "de 1,20 por 1,40, una del baño chiquita de 60 x 60 fija, una para el dormitorio de 1,20 x 1,00 "
    "y otra para la cocina de 90 x 1,10. Todo en PVC blanco, termopanel. ¿Cuánto sería con instalación?"
)
SYSTEM, GLASS = str(uuid4()), "GLASS-24"
USUAL = {"system_id": {"value": SYSTEM, "source": "company"},
         "glass_article_sku": {"value": GLASS, "source": "company"},
         "color": {"value": "WHITE", "source": "company"}}


def _window(location, width, height, *, quantity=1, template="FIXED", quote=None, **extra):
    op = {"op": "add_position", "system_id": SYSTEM, "template": template,
          "dims": {"width_mm": width, "height_mm": height}, "location": location,
          "quantity": quantity, "glass_sku": GLASS, "color": "WHITE", **extra}
    if quote is not None:
        op["origin"] = {"quote": quote}
    return op


def test_measures_read_millimetres_centimetres_and_metres():
    assert {Decimal("1200"), Decimal("1400")} <= origins.measures_mm("de 1,20 por 1,40")
    assert {Decimal("600")} <= origins.measures_mm("60 x 60")
    assert {Decimal("900"), Decimal("1100")} <= origins.measures_mm("90 x 1,10")
    assert {Decimal("1800"), Decimal("1400")} <= origins.measures_mm("1800 mm por 1400")
    assert Decimal("2500") in origins.measures_mm("2,5 m")
    assert origins.counts("dos ventanas y 3 más") >= {2, 3}


def test_locate_tolerates_case_accents_and_spaces_only():
    span = origins.locate("una del BANO chiquita  de 60 x 60 fija", [REQUEST])
    assert span is not None and REQUEST[span["start"]:span["end"]] == span["quote"]
    assert span["quote"].startswith("una del baño")
    assert origins.locate("una del baño de 70 x 60 fija", [REQUEST]) is None


def test_a_window_whose_measures_are_not_in_its_phrase_is_refused():
    kept, cited, refused = origins.bind([
        _window("Baño", "600", "700", quote="una del baño chiquita de 60 x 60 fija"),
        _window("Living", "1200", "1400", quantity=3,
                quote="2 ventanas oscilobatientes para el living de 1,20 por 1,40"),
        _window("Pasillo", "500", "500", quote="una para el pasillo de 50 x 50"),
    ], [REQUEST])
    assert kept == [] and cited == []
    assert [item["reason"] for item in refused] == [
        "origin_measure_missing", "origin_quantity_missing", "origin_missing"]


def test_without_a_cited_phrase_the_server_finds_the_sentence_that_states_it():
    kept, cited, refused = origins.bind([_window("Cocina", "900", "1100")], [REQUEST])
    assert refused == [] and len(kept) == 1 and "origin" not in kept[0]
    assert cited[0]["quote"] == "otra para la cocina de 90 x 1,10"


def test_other_operations_pass_through_without_their_origin_key():
    kept, cited, refused = origins.bind([{"op": "set_quantity", "position_id": "p", "quantity": 4, "origin": "x"}],
                                        [REQUEST])
    assert kept == [{"op": "set_quantity", "position_id": "p", "quantity": 4}]
    assert cited == [] and refused == []


def test_assumptions_list_unstated_openings_and_group_the_usual_values():
    ops = [
        _window("Living", "1200", "1400", quantity=2, template="TILT_TURN_LEFT",
                quote="2 ventanas oscilobatientes para el living de 1,20 por 1,40"),
        _window("Dormitorio", "1200", "1000", template="TILT_TURN_LEFT",
                quote="una para el dormitorio de 1,20 x 1,00"),
        {**_window("Baño", "600", "600", quote="una del baño chiquita de 60 x 60 fija"), "glass_sku": "LAM-33",
         "origin": {"quote": "una del baño chiquita de 60 x 60 fija",
                    "reasons": {"glass_article_sku": "Tu regla pide vidrio de seguridad en baños.",
                                "template": "Uso 2 hojas"}}},
    ]
    kept, cited, _ = origins.bind(ops, [REQUEST])
    found = origins.assumptions(cited, kept, USUAL, {SYSTEM: "PRO6004 · Proline", "WHITE": "Blanco",
                                                     "TILT_TURN_LEFT": "Oscilobatiente izquierda"}, REQUEST)
    flagged = [(item["location"], item["field"]) for item in found if item["source"] == "agent"]
    assert flagged == [("Dormitorio", "opening"), ("Baño", "glass")]
    glass = next(item for item in found if item["field"] == "glass" and item["source"] == "agent")
    assert glass["reason"] == "Tu regla pide vidrio de seguridad en baños."
    usual = {item["field"]: item for item in found if item["source"] == "usual"}
    assert usual["series"]["locations"] == ["Living", "Dormitorio", "Baño"]
    assert usual["glass"]["locations"] == ["Living", "Dormitorio"]
    # «Blanco» is written in the request: the finish is stated, not assumed.
    assert "color" not in usual


def test_attach_binds_each_origin_to_the_window_the_preview_created():
    kept, cited, _ = origins.bind([
        {"op": "duplicate_position", "position_id": "old", "count": 2, "location": "Copia"},
        _window("Cocina", "900", "1100", quote="otra para la cocina de 90 x 1,10"),
    ], [REQUEST])
    simulation = {"diff": [
        {"kind": "add", "after": {"id": "copy-1"}}, {"kind": "add", "after": {"id": "copy-2"}},
        {"kind": "add", "after": {"id": "new-1", "location_tag": "Cocina"}},
    ]}
    bound = origins.attach(cited, kept, simulation)
    assert bound[0]["position_id"] == "new-1" and bound[0]["location"] == "Cocina"
    assert "op_index" not in bound[0] and "reasons" not in bound[0]


def test_recorded_request_replays_start_then_project_with_usual_values():
    payload = {"goal": REQUEST, "context": {"usual": USUAL}, "observations": []}
    start = _recorded_round(payload)
    assert start["steps"][0]["kind"] == "create_project"
    assert start["tool_calls"][0]["arguments"]["system_id"] == SYSTEM
    payload["observations"] = [
        {"surface": "create_project", "context": {"project_id": str(uuid4())}},
        {"surface": "list_catalog_options", "context": {
            "opening_choices": [{"label": "Oscilobatiente de una hoja"}], "openings": ["FIXED"]}},
    ]
    project = _recorded_round(payload)
    ops = project["steps"][0]["ops"]
    assert {op["system_id"] for op in ops} == {SYSTEM}
    assert {op["glass_sku"] for op in ops} == {GLASS}
    assert [op["template"] for op in ops] == [
        "Oscilobatiente de una hoja", "FIXED", "Oscilobatiente de una hoja", "FIXED"]
    assert _recorded_round({"goal": "otra cosa", "context": {}, "observations": []}) is None


def _patch_agent(monkeypatch, outputs, previews):
    calls = []

    def fake_invoke(**kwargs):
        calls.append(kwargs)
        return {"audit_id": str(uuid4()), "capability": "agent", "model": "mock", "output": outputs.pop(0)
                if len(outputs) > 1 else outputs[0], "tokens_prompt": 1, "tokens_completion": 1,
                "latency_ms": 1, "credits_debited": 1}

    def fake_call(self, name, arguments, *, validation=False):
        if name == "preview_project_operations":
            previews.append(arguments["ops"])
            adds = [{"kind": "add", "after": {"id": f"p{i}", "location_tag": op["location"]}}
                    for i, op in enumerate(arguments["ops"]) if op.get("op") == "add_position"]
            return {"valid": True, "ops": arguments["ops"], "diff": adds, "project_id": "proj"}, True
        return {}, False

    project_id = str(uuid4())
    monkeypatch.setattr(agent, "build_context", lambda org_id, surface, refs: {
        "surface": "project", "id": project_id, "editable": True, "usual": USUAL})
    monkeypatch.setattr(agent.gateway, "invoke", fake_invoke)
    monkeypatch.setattr(agent.EngineTools, "call", fake_call)
    monkeypatch.setattr(agent, "_origin_labels", lambda org_id, ops: {SYSTEM: "PRO6004 · Proline", "WHITE": "Blanco"})
    monkeypatch.setattr(agent.jobs, "create_job", lambda **kw: {"id": str(uuid4()), "transcript": []})
    monkeypatch.setattr(agent.jobs, "finish_job", lambda **kw: None)
    monkeypatch.setattr("ai_gateway.postconditions.build_receipt", lambda **kw: {})
    monkeypatch.setattr(agent.jobs, "set_receipt", lambda **kw: None)
    return project_id, calls


def test_agent_step_carries_origins_assumptions_and_refuses_uncited_windows(monkeypatch):
    previews: list = []
    doc = {"reply": "Agregué las ventanas del mensaje.", "warnings": [], "steps": [{
        "kind": "project_ops", "apply": True, "ops": [
            _window("Cocina", "900", "1100", quote="otra para la cocina de 90 x 1,10"),
            _window("Pasillo", "500", "500", quote="un pasillo de 50 x 50"),
        ]}]}
    project_id, _ = _patch_agent(monkeypatch, [json.dumps(doc, ensure_ascii=False)], previews)
    result = agent.act(org_id=uuid4(), user_id=uuid4(), surface="project", refs={"project_id": project_id},
                       goal=REQUEST, product=None, history=[], operation_key="p08", autonomy="propose",
                       role="ESTIMATOR", interaction_mode="work")
    assert [op["location"] for op in previews[0]] == ["Cocina"]
    assert all("origin" not in op for op in previews[0])
    step = result["steps"][0]
    assert step["origins"][0]["position_id"] == "p0"
    assert step["origins"][0]["quote"] == "y otra para la cocina de 90 x 1,10" or \
        step["origins"][0]["quote"] == "otra para la cocina de 90 x 1,10"
    assert [item["field"] for item in step["assumptions"] if item["source"] == "agent"] == ["opening"]
    assert step["sources"][0] == {"kind": "request", "text": REQUEST}
    assert {"op": "add_position", "reason": "origin_missing", "location": "Pasillo"} in result["rejected"]
