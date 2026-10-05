"""The baseline cannot pass by describing edits that never reached the graph."""

from copy import deepcopy
from decimal import Decimal
import json

import pytest

from ai_gateway.evals.outcomes import classify, evaluate, summarize
from ai_gateway.evals.run import Recorder, load_cases


def product(*, opening="FIXED"):
    return {"version": "product-v2", "assembly": {"couplings": [], "modules": [{
        "id": "m", "width_mm": "1500.00", "height_mm": "1200.00",
        "tree": {"id": "b", "type": "BAY", "opening_type": opening},
    }]}}


def verdict(case_id, before, after, *, result=None, truth=None, changes=None):
    case = next(c for c in load_cases() if c["id"] == case_id)
    return evaluate(case, before=before, after=after, result=result or {},
                    truth=truth or {}, changed_tables=changes or [])


def test_owner_suite_is_complete_and_keeps_typo_and_orientation():
    cases = load_cases()
    assert [c["id"] for c in cases] == ([f"E{i:02}" for i in range(1, 14)] +
                                       [f"J{i:02}" for i in range(1, 9)] +
                                       [f"F{i:02}" for i in range(1, 4)] + ["G01", "G02"])
    assert cases[10]["request"] == "aser la bentana 20 cm mas ancha"
    assert cases[1]["expected"] == "fixed_tilt_left"


def test_saying_dimensions_cannot_replace_the_edit():
    before = product()
    assert not verdict("E03", before, before, result={"reply": "Listo: 1800 × 1350 mm."})["passed"]
    after = deepcopy(before)
    after["assembly"]["modules"][0].update(width_mm="1800.00", height_mm="1350.00")
    assert verdict("E03", before, after)["passed"]


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


def test_technical_weight_is_exact_and_unknown_requires_cause():
    before = product()
    truth = {"right_leaf_weight": "24.35"}
    assert verdict("E09", before, before, result={"reply": "La hoja pesa 24,35 kg."}, truth=truth)["passed"]
    assert not verdict("E09", before, before, result={"reply": "La hoja pesa 24,34 kg."}, truth=truth)["passed"]
    assert verdict("E09", before, before, result={"reply": "Sin dato: falta la masa del perfil."})["passed"]
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
