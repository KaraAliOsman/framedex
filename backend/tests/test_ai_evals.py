"""The baseline cannot pass by describing edits that never reached the graph."""

from copy import deepcopy
from decimal import Decimal
import json

import pytest

from ai_gateway.evals.outcomes import classify, evaluate, summarize
from ai_gateway.evals.run import Recorder, fixture_project, load_cases
from ai_gateway.evals.facts import frame_bar_count, priced_winner
from ai_gateway.evals.redaction import redact_report


def product(*, opening="FIXED"):
    return {"version": "product-v2", "assembly": {"couplings": [], "modules": [{
        "id": "m", "width_mm": "1500.00", "height_mm": "1200.00",
        "tree": {"id": "b", "type": "BAY", "opening_type": opening},
    }]}}


def verdict(case_id, before, after, *, result=None, truth=None, changes=None, engine=None):
    case = next(c for c in load_cases() if c["id"] == case_id)
    return evaluate(case, before=before, after=after, result=result or {},
                    truth=truth or {}, changed_tables=changes or [],
                    engine_after=engine if engine is not None else {
                        "http_status": 200, "result": {"status": "VALID", "issues": []}})


def test_owner_suite_is_complete_and_keeps_typo_and_orientation():
    cases = load_cases()
    assert [c["id"] for c in cases] == ([f"E{i:02}" for i in range(1, 14)] +
                                       [f"J{i:02}" for i in range(1, 9)] +
                                       [f"F{i:02}" for i in range(1, 4)] + ["G01", "G02"])
    assert cases[10]["request"] == "aser la bentana 20 cm mas ancha"
    assert cases[1]["expected"] == "fixed_tilt_left"


def test_fixture_is_discovered_after_a_clean_stack_recreates_project_ids():
    identity = "ffffffff-eeee-dddd-cccc-bbbbbbbbbbbb"
    assert str(fixture_project([{"id": identity, "name": "Vivienda demo [CASA_LOMAS]"}])) == identity
    with pytest.raises(ValueError):
        fixture_project([])
    with pytest.raises(ValueError):
        fixture_project([{"id": identity, "name": "Otra vivienda [CASA_LOMAS]"}] * 2)


def test_saying_dimensions_cannot_replace_the_edit():
    before = product()
    assert not verdict("E03", before, before, result={"reply": "Listo: 1800 × 1350 mm."})["passed"]
    after = deepcopy(before)
    after["assembly"]["modules"][0].update(width_mm="1800.00", height_mm="1350.00")
    assert verdict("E03", before, after)["passed"]


@pytest.mark.parametrize("engine", [
    {"http_status": 400, "result": {"error": "invalid_tree"}},
    {"http_status": 200, "result": {"status": "INVALID", "issues": []}},
    {"http_status": 200, "result": {"status": "VALID", "issues": [{"severity": "error"}]}},
])
def test_exact_dimensions_do_not_pass_when_the_engine_rejects_the_design(engine):
    before = product()
    after = deepcopy(before)
    after["assembly"]["modules"][0].update(width_mm="1800.00", height_mm="1350.00")
    evaluated = verdict("E03", before, after, engine=engine)
    assert not evaluated["passed"]
    assert not next(c for c in evaluated["checks"] if c["check"] == "engine_accepts_design")["passed"]


def test_missing_manufacturing_authority_does_not_mean_invalid_geometry():
    before = product()
    after = deepcopy(before)
    after["assembly"]["modules"][0].update(width_mm="1800.00", height_mm="1350.00")
    assert verdict("E03", before, after, engine={"http_status": 200, "result": {
        "status": "MANUFACTURING_INCOMPLETE", "issues": [{"severity": "warning"}]}})["passed"]


@pytest.mark.parametrize("supported", [True, None, False])
def test_kitchen_refusal_requires_negative_catalog_engine_authority(supported):
    before = product()
    assert verdict("J02", before, before, truth={"sliding_supported": supported},
                   result={"reply": "Este sistema no admite correderas."})["passed"] is (supported is False)


def test_mixed_fixture_does_not_credit_a_false_casement_incompatibility_claim():
    before = product()
    result = {"reply": "Este sistema practicable no admite correderas."}
    assert not verdict("E07", before, before, truth={"sliding_supported": True}, result=result)["passed"]
    assert verdict("E07", before, before, truth={"sliding_supported": False}, result=result)["passed"]


def test_bedroom_copies_preserve_quantity_and_require_destinations():
    before = product()
    source = {"id": "source", "quantity": 2, "design": {"system_id": "system", "color": "WHITE"}}
    proposed = [{"design": deepcopy(source["design"]), "quantity": 2, "location_tag": "Living"}
                for _ in range(4)]
    result = {"artifacts": [{"kind": "project_draft", "payload": {"positions": proposed}}]}
    assert not verdict("J03", before, before, result=result, truth={"position_three": source})["passed"]
    for p in proposed:
        p["location_tag"] = "Dormitorio segundo piso"
    assert verdict("J03", before, before, result=result, truth={"position_three": source})["passed"]
    proposed[0]["quantity"] = 1
    assert not verdict("J03", before, before, result=result, truth={"position_three": source})["passed"]


def test_quantity_alternative_requires_a_typed_bedroom_allocation():
    before = product()
    source = {"id": "source", "quantity": 1, "design": {}}
    change = {"position_id": "source", "quantity": 5}
    result = {"artifacts": [{"kind": "project_draft", "payload": {"quantity_changes": [change]}}]}
    assert not verdict("J03", before, before, result=result, truth={"position_three": source})["passed"]
    change["allocations"] = [{"location_tag": "Dormitorios", "quantity": 4}]
    assert verdict("J03", before, before, result=result, truth={"position_three": source})["passed"]
    change["allocations"][0]["location_tag"] = "Living"
    assert not verdict("J03", before, before, result=result, truth={"position_three": source})["passed"]


@pytest.mark.parametrize(("fraction", "passes"), [("0.05", True), ("0.0500", True),
                                                 ("5", False), ("5.00", False), ("cinco", False)])
def test_discount_uses_the_pricing_fraction_contract(fraction, passes):
    before = product()
    assert verdict("J05", before, before, result={"state": "WAITING_FOR_APPROVAL", "artifacts": [
        {"kind": "quote_draft", "payload": {"discount_pct": fraction}}]})["passed"] is passes


def test_price_ranking_uses_the_current_applied_operation_and_exact_engine_lines():
    project = {"id": "project", "current_revision": "REV-B", "pricing_current": True,
               "current_pricing_operation_id": "applied", "positions": [
                   {"position_index": 1, "id": "one", "price_net": "0.00"},
                   {"position_index": 2, "id": "two", "price_net": "0.00"}]}
    operation = {"id": "applied", "state": "APPLIED", "project_id": "project", "revision_code": "REV-B",
                 "lines": [{"position_index": 1, "line_net": "9007199254740992.01"},
                           {"position_index": 2, "line_net": "9007199254740992.02"}]}
    assert priced_winner(project, [operation]) == "two"
    assert priced_winner({**project, "pricing_current": False}, [operation]) is None
    assert priced_winner(project, [{**operation, "state": "PREVIEW"}]) is None
    assert priced_winner(project, [{**operation, "revision_code": "REV-A"}]) is None
    assert priced_winner({**project, "positions": [
        {"position_index": 1, "id": "one", "price_net": "10.01"},
        {"position_index": 2, "id": "two", "price_net": "10.02"}]}, []) == "two"


def test_cut_plan_counts_frame_profile_bars_and_preserves_absent_authority():
    assert frame_bar_count({}) is None
    cuts = [{"cuts": [{"source_kind": "PROFILE", "role": "FRAME"}]},
            {"cuts": [{"source_kind": "PROFILE", "role": "FRAME"}]},
            {"cuts": [{"source_kind": "REINFORCEMENT", "role": "FRAME"}]},
            {"cuts": [{"source_kind": "PROFILE", "role": "SASH"}]}]
    plan = {"workshop_cut_plan": cuts, "unplaced": []}
    assert frame_bar_count({"optimization": {"bars": plan}}) == 2
    assert frame_bar_count({"optimization": {"bars": {**plan, "unplaced": [{"piece": "unplaced"}]}}}) is None
    assert frame_bar_count({"optimization": {"bars": {"workshop_cut_plan": []}}}) == 0


def test_provider_echo_is_redacted_without_changing_the_gateway_response(monkeypatch):
    monkeypatch.setenv("AI_GATEWAY_MIMO_API_KEY", "synthetic-private-provider-key")
    document = {"reply": "synthetic-private-provider-key", "api_key": "another-secret",
                "nested": {"secret_key": "nested-secret"}, "tokens_prompt": 2}
    response = {"output": json.dumps(document)}
    recorder = Recorder(lambda **kwargs: response)
    assert recorder(input_payload={}) is response
    assert json.loads(response["output"]) == document
    saved = recorder.rounds[0]["document"]
    assert saved["reply"] == "[redacted]"
    assert saved["api_key"] == "[redacted]"
    assert saved["nested"]["secret_key"] == "[redacted]"
    assert saved["tokens_prompt"] == 2
    jwt = "eyJfixture.payload.signature"
    assert jwt not in json.dumps(redact_report({"reply": jwt}, environment={}))


def test_mullioned_bays_are_not_separate_coupled_frames():
    before = product()
    after = deepcopy(before)
    after["assembly"]["modules"] = [
        {**deepcopy(before["assembly"]["modules"][0]), "id": name, "width_mm": "750.00"}
        for name in ("left", "right")
    ]
    assert not verdict("E01", before, after)["passed"]
    after = deepcopy(before)
    after["assembly"]["modules"][0]["tree"] = {
        "id": "post", "type": "SPLIT_V", "split_offset_mm": "750.00",
        "children": [{"id": name, "type": "BAY", "opening_type": "FIXED"}
                     for name in ("left", "right")],
    }
    assert verdict("E01", before, after)["passed"]
    after["assembly"]["modules"][0]["tree"]["split_offset_mm"] = "750.01"
    assert not verdict("E01", before, after)["passed"]


def test_transom_is_measured_from_the_top_and_top_bay_is_fixed():
    before = product()
    after = deepcopy(before)
    tree = {"id": "transom", "type": "SPLIT_H", "split_offset_mm": "400.00", "children": [
        {"id": "top", "type": "BAY", "opening_type": "FIXED"},
        {"id": "bottom", "type": "BAY", "opening_type": "TILT_TURN_LEFT"},
    ]}
    after["assembly"]["modules"][0]["tree"] = tree
    assert verdict("E04", before, after)["passed"]
    tree["split_offset_mm"] = "800.00"
    assert not verdict("E04", before, after)["passed"]


def test_three_bays_compare_global_axes_in_either_binary_tree_shape():
    before = product()
    truth = {"mullion_half_face_mm": "20"}
    bays = [{"id": name, "type": "BAY", "opening_type": opening}
            for name, opening in [("left", "TURN_LEFT"), ("middle", "FIXED"), ("right", "TURN_RIGHT")]]
    after = deepcopy(before)
    after["assembly"]["modules"][0]["tree"] = {
        "id": "first", "type": "SPLIT_V", "split_offset_mm": "500.00", "children": [bays[0],
            {"id": "second", "type": "SPLIT_V", "split_offset_mm": "480.00", "children": bays[1:]}],
    }
    assert verdict("E13", before, after, truth=truth)["passed"]
    after["assembly"]["modules"][0]["tree"] = {
        "id": "first", "type": "SPLIT_V", "split_offset_mm": "1000.00", "children": [
            {"id": "second", "type": "SPLIT_V", "split_offset_mm": "500.00", "children": bays[:2]}, bays[2]],
    }
    assert verdict("E13", before, after, truth=truth)["passed"]


def test_right_handle_means_left_hinges_and_flip_changes_real_opening():
    before = product()
    after = product(opening="TILT_TURN_RIGHT")
    assert verdict("E12", product(opening="TILT_TURN_LEFT"), after)["passed"]
    after["assembly"]["modules"][0]["tree"] = {
        "id": "post", "type": "SPLIT_V", "split_offset_mm": "750.00", "children": [
            {"id": "left", "type": "BAY", "opening_type": "FIXED"},
            {"id": "right", "type": "BAY", "opening_type": "TILT_TURN_LEFT"},
        ],
    }
    assert verdict("E02", before, after)["passed"]
    after["assembly"]["modules"][0]["tree"]["children"][1]["opening_type"] = "TILT_TURN_RIGHT"
    assert not verdict("E02", before, after)["passed"]


def test_installation_height_needs_typed_question_not_guessed_handle():
    before = product()
    result = {"questions": ["¿A qué altura del piso está instalada la ventana?"]}
    assert verdict("E08", before, before, result=result)["passed"]
    assert verdict("E08", before, before)["failure"] == "no_pidio_aclaracion"
    after = deepcopy(before)
    after["assembly"]["modules"][0]["tree"]["handle_height_mm"] = "1050.00"
    assert not verdict("E08", before, after, result=result)["passed"]


@pytest.mark.parametrize("question", [
    "¿Registrar la altura de manilla 1050 mm desde el piso como nota para fabricación/instalación?",
    "¿Quieres que la ventana tenga manilla a 1050 del piso?",
    "¿Quieres que instalemos una manilla?",
])
def test_handle_note_is_not_a_question_about_the_missing_installation_datum(question):
    before = product()
    result = {"questions": [question]}
    scored = verdict("E08", before, before, result=result)
    assert not scored["passed"]
    assert scored["failure"] == "no_pidio_aclaracion"


@pytest.mark.parametrize("question", [
    "¿Cuál es la altura del antepecho?",
    "¿A qué distancia del piso queda la parte inferior del marco?",
    "Indica a qué altura del suelo está la ventana.",
])
def test_installation_datum_questions_accept_workshop_wording(question):
    before = product()
    assert verdict("E08", before, before, result={"questions": [question]})["passed"]


def test_glass_must_resolve_to_real_recipe_or_real_alternatives():
    before = product()
    after = deepcopy(before)
    after["assembly"]["modules"][0]["tree"]["glass_article_sku"] = "INVENTADO"
    truth = {"glass_recipes": {"DVH-REAL": "4-12-4 Float"}}
    assert not verdict("E05", before, after, truth=truth)["passed"]
    after["assembly"]["modules"][0]["tree"]["glass_article_sku"] = "DVH-REAL"
    assert verdict("E05", before, after, truth=truth)["passed"]
    truth = {"glass_recipes": {"MONO-REAL": "4 Float"}}
    result = {"reply": "No está disponible en el catálogo. Alternativa: MONO-REAL."}
    assert verdict("E06", before, before, result=result, truth=truth)["passed"]
    result["reply"] = "No está disponible. Alternativa: INVENTADO."
    assert not verdict("E06", before, before, result=result, truth=truth)["passed"]


@pytest.mark.parametrize("case", ["E05", "E06"])
def test_current_glass_mention_does_not_offer_an_available_alternative(case):
    before = product()
    truth = {"glass_recipes": {"VIDRIO-BASE": "4 Float"}}
    response = {"reply": "El vidrio actual es VIDRIO-BASE. No hay artículos de vidrio en el catálogo. "
                "Voy a revisar las opciones disponibles antes de tocar nada."}
    assert not verdict(case, before, before, result=response, truth=truth)["passed"]
    response["artifacts"] = [{"kind": "catalog_candidates", "payload": {"skus": ["VIDRIO-BASE"]}}]
    assert verdict(case, before, before, result=response, truth=truth)["passed"]
    response["artifacts"][0]["payload"]["skus"].append("INVENTADO")
    assert not verdict(case, before, before, result=response, truth=truth)["passed"]


def test_general_opening_explanation_cannot_contradict_hinge_handedness():
    before = product()
    reply = "Abatible: gira sobre un eje vertical. Oscilobatiente: giro y basculación superior."
    assert verdict("G02", before, before, result={"reply": reply})["passed"]
    reply += " El lado indica hacia dónde gira la hoja vista desde el interior."
    assert not verdict("G02", before, before, result={"reply": reply})["passed"]


def test_technical_weight_is_exact_and_unknown_requires_cause():
    before = product()
    truth = {"right_leaf_weight": "24.35"}
    assert verdict("E09", before, before, result={"reply": "La hoja pesa 24,35 kg."}, truth=truth)["passed"]
    assert not verdict("E09", before, before, result={"reply": "La hoja pesa 24,34 kg."}, truth=truth)["passed"]
    assert verdict("E09", before, before, result={"reply": "Sin dato: falta la masa del perfil."})["passed"]
    assert verdict("E09", before, before, result={"reply": "Sin dato: el contexto no trae el peso del motor."})["passed"]
    assert not verdict("E09", before, before, result={"reply": "Sin dato."})["passed"]


def test_preparation_needs_right_deeplink_and_no_issue_write():
    before = product()
    truth = {"quote_path": "/projects/fixture/pricing"}
    result = {"steps": [{"kind": "prepare", "action": "emit_revision", "path": truth["quote_path"]}]}
    assert verdict("J06", before, before, result=result, truth=truth)["passed"]
    assert verdict("J06", before, before, result=result, truth=truth,
                   changes=["project_versions"])["failure"] == "accion_consecuente_ejecutada"


def test_no_revisions_is_missing_context_not_an_empty_comparison_success():
    before = product()
    result = {"artifacts": [{"kind": "comparison", "payload": {"differences": []}}]}
    assert verdict("J08", before, before, result=result, truth={"revisions": []})["failure"] == "contexto_insuficiente"


@pytest.mark.parametrize(("code", "rejections", "expected"), [
    ("ai_provider_not_configured", [], "proveedor_no_configurado"),
    ("ai_provider_timeout", [], "proveedor_error"),
    ("ai_agent_bad_output", [], "formato_invalido"),
    ("ai_agent_ungrounded", [], "grounding_rechazo"),
    ("", [{"reason": "operacion_desconocida"}], "op_no_soportada"),
    ("", [{"reason": "medida_no_declarada"}], "op_rechazada_validador"),
])
def test_taxonomy_preserves_actual_validator_reason(code, rejections, expected):
    assert classify(code, rejections) == expected


def test_recorder_passes_original_request_and_response_unmodified():
    sent = []
    document = {"reply": "Sin dato.", "steps": [{"kind": "ops", "ops": [{"op": "split_bay"}]}]}
    response = {"output": json.dumps(document), "credits_debited": 3}

    def invoke(**kwargs):
        sent.append(kwargs)
        return response

    recorder = Recorder(invoke)
    arguments = {"input_payload": {"context": {"amount": Decimal("1.23")}},
                 "provider_options": {"system": "original prompt"}}
    assert recorder(**arguments) is response
    assert sent == [arguments]
    assert recorder.rounds[0]["document"] == document
    assert recorder.rounds[0]["context_fields"] == ["amount"]


def test_recorder_does_not_swallow_provider_error():
    def invoke(**kwargs):
        raise TimeoutError

    recorder = Recorder(invoke)
    with pytest.raises(TimeoutError):
        recorder(input_payload={"correction": {"reason": "reply_ungrounded"}})
    assert recorder.rounds[0]["phase"] == "grounding"
    assert recorder.rounds[0]["error_code"] == "TimeoutError"


def test_summary_keeps_missing_categories_zero_and_denominators():
    report = summarize([
        {"view": "editor", "passed": False, "failure": "grounding_rechazo"},
        {"view": "editor", "passed": True, "failure": None},
        {"view": "factory", "passed": False, "failure": "contexto_insuficiente"},
    ])
    assert report["by_view"]["editor"] == {"passed": 1, "total": 2}
    assert report["failure_counts"]["grounding_rechazo"] == 1
    assert report["failure_counts"]["proveedor_error"] == 0
