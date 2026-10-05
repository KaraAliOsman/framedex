"""Deterministic oracles: mutations are judged on the resulting domain graph.

Narrative-only requests also check their factual assertion/refusal. Those checks
are deliberately conservative; this is not a subjective LLM-as-judge score.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from decimal import Decimal, InvalidOperation
from typing import Any

from ai_gateway.evals.facts import engine_accepted

FAILURES = (
    "proveedor_no_configurado", "proveedor_error", "formato_invalido",
    "op_no_soportada", "op_rechazada_validador", "grounding_rechazo",
    "contexto_insuficiente", "resultado_incorrecto", "no_pidio_aclaracion",
    "accion_consecuente_ejecutada",
)


def nodes(product: dict) -> list[dict]:
    found: list[dict] = []

    def walk(node: dict) -> None:
        found.append(node)
        for child in node.get("children") or []:
            walk(child)

    for module in product.get("assembly", {}).get("modules", []):
        walk(module["tree"])
    return found


def _mm(value: Any) -> Decimal:
    return Decimal(str(value))


def _exact_decimal(value: Any, expected: str) -> bool:
    try:
        return not isinstance(value, bool) and Decimal(str(value)) == Decimal(expected)
    except InvalidOperation:
        return False


def _bedroom(position: dict) -> bool:
    return "dormitorio" in str(position.get("location_tag") or position.get("location") or "").lower()


def _narrative(result: dict) -> str:
    return " ".join([
        str(result.get("reply") or ""),
        *[str(v) for v in result.get("questions") or []],
    ]).lower()


def classify(error: str, rejected: list[dict], *, grounding: bool = False) -> str:
    if error in {"ai_provider_not_configured", "ai_provider_mock_disabled",
                 "ai_capability_unknown", "ai_entitlement_required", "insufficient_credits"}:
        return "proveedor_no_configurado"
    if error.startswith("ai_provider"):
        return "proveedor_error"
    if "ungrounded" in error or grounding:
        return "grounding_rechazo"
    if "bad_output" in error:
        return "formato_invalido"
    if "context" in error or "ref_not_found" in error:
        return "contexto_insuficiente"
    if any("unknown_op" in str(r.get("reason")) or "not_allowed" in str(r.get("reason"))
           or "operacion_desconocida" in str(r.get("reason"))
           for r in rejected):
        return "op_no_soportada"
    if any(r.get("reason") == "formato_invalido" for r in rejected):
        return "formato_invalido"
    if rejected:
        return "op_rechazada_validador"
    return "resultado_incorrecto"


def evaluate(case: dict, *, before: dict, after: dict, result: dict,
             truth: dict, changed_tables: list[str], engine_after: dict) -> dict:
    """A matching sentence cannot pass a graph/money/stock mutation oracle."""
    checks: list[dict] = []

    def check(name: str, condition: bool, expected: Any = None, actual: Any = None) -> None:
        checks.append({"check": name, "passed": bool(condition),
                       "expected": expected, "actual": actual})

    check("no_domain_write", not changed_tables, [], changed_tables)
    steps = result.get("steps") or []
    ops = [op for step in steps for op in step.get("ops") or []]
    artifacts = result.get("artifacts") or []
    text = _narrative(result)
    expectation = case["expected"]
    if expectation in {"two_fixed_bays", "fixed_tilt_left", "three_bays", "transom_400",
                       "dimensions_1800_1350", "width_plus_200", "tilt_right"} or (
            expectation == "glass_4_12_4" and after != before):
        check("engine_accepts_design", engine_accepted(engine_after),
              "HTTP 200, geometrically valid; manufacturing gaps remain explicit", engine_after)
    modules = after.get("assembly", {}).get("modules", [])
    all_nodes = nodes(after)
    bays = [n for n in all_nodes if n.get("type") == "BAY"]
    openings = [b.get("opening_type") for b in bays]
    splits_h = [n for n in all_nodes if n.get("type") == "SPLIT_H"]
    questions = result.get("questions") or []
    catalog = truth.get("glass_recipes") or {}
    available_mentions = [sku for sku in catalog if sku.lower() in text]
    kinds = {a.get("kind") for a in artifacts}

    if expectation in {"two_fixed_bays", "fixed_tilt_left", "three_bays"}:
        wanted = {
            "two_fixed_bays": ["FIXED", "FIXED"],
            "fixed_tilt_left": ["FIXED", "TILT_TURN_LEFT"],
            "three_bays": ["TURN_LEFT", "FIXED", "TURN_RIGHT"],
        }[expectation]
        check("one_frame", len(modules) == 1, 1, len(modules))
        check("openings_left_to_right", openings == wanted, wanted, openings)
        wanted_offsets = [Decimal("750")] if len(wanted) == 2 else [Decimal("500"), Decimal("1000")]
        actual_axes: list[Decimal] = []

        def axes(node: dict, origin: Decimal) -> None:
            if node.get("type") == "SPLIT_V":
                axis = origin + _mm(node.get("split_offset_mm") or "-1")
                actual_axes.append(axis)
                children = node.get("children") or []
                if len(children) == 2:
                    axes(children[0], origin)
                    axes(children[1], axis + _mm(truth.get("mullion_half_face_mm", "0")))
            else:
                for child in node.get("children") or []:
                    axes(child, origin)

        for module in modules:
            axes(module["tree"], Decimal("0"))
        check("mullion_axes", sorted(actual_axes) == wanted_offsets,
              list(map(str, wanted_offsets)), list(map(str, sorted(actual_axes))))
    elif expectation in {"dimensions_1800_1350", "width_plus_200"}:
        width, height = (("1800", "1350") if expectation == "dimensions_1800_1350"
                         else ("1700", "1200"))
        actual = [(m.get("width_mm"), m.get("height_mm")) for m in modules]
        check("exact_dimensions", len(modules) == 1 and
              _mm(modules[0]["width_mm"]) == _mm(width) and
              _mm(modules[0]["height_mm"]) == _mm(height), [width, height], actual)
    elif expectation == "transom_400":
        check("one_frame", len(modules) == 1, 1, len(modules))
        check("horizontal_transom", len(splits_h) == 1, 1, len(splits_h))
        # The engine's local tree coordinates run down from the outer top.
        check("top_bay_height", bool(splits_h) and
              _mm(splits_h[0].get("split_offset_mm") or "-1") == Decimal("400"),
              "400 mm from the outer top",
              splits_h[0].get("split_offset_mm") if splits_h else None)
        check("upper_fixed", bool(splits_h) and len(splits_h[0].get("children") or []) == 2
              and splits_h[0]["children"][0].get("opening_type") == "FIXED")
    elif expectation == "tilt_right":
        check("hinges_and_handle", openings == ["TILT_TURN_RIGHT"],
              ["TILT_TURN_RIGHT"], openings)
    elif expectation in {"glass_4_12_4", "unavailable_laminated"}:
        wanted = [sku for sku, recipe in catalog.items() if recipe and
                  re.match(r"^4\s*-\s*12\s*-\s*4(?:\D|$)", recipe)]
        if expectation == "glass_4_12_4" and wanted:
            actual = [b.get("glass_article_sku") for b in bays]
            check("catalog_glass", bool(actual) and all(sku in wanted for sku in actual),
                  wanted, actual)
        else:
            check("no_invented_glass", after == before and not ops)
            offered = [a.get("payload", {}).get("skus", []) for a in artifacts
                       if a.get("kind") == "catalog_candidates"]
            check("real_alternatives", bool(available_mentions) or
                  any(skus and set(skus) <= set(catalog) for skus in offered),
                  sorted(catalog), available_mentions or offered)
            check("availability_explained", bool(re.search(
                r"no (?:est[aá]|hay|aparece|existe|disponible)|no.*cat[aá]logo|sin.*cat[aá]logo", text)))
    elif expectation in {"incompatible_sliding", "installation_question"}:
        check("no_mutation", after == before and not ops)
        if expectation == "installation_question":
            check("installation_height_question", any(
                re.search(r"(?:instal|antepecho|ventana.*piso|piso.*ventana)", q.lower())
                for q in questions), "typed question about window installation height", questions)
        else:
            check("selected_system_rejects_sliding", truth.get("sliding_supported") is False,
                  "negative engine/catalog compatibility", truth.get("sliding_supported"))
            check("incompatibility_explained", bool(re.search(
                r"incompat|no admite|no.*compatible|sistema.*(?:no permite|practicable)", text)))
    elif expectation == "engine_weight":
        weight = truth.get("right_leaf_weight")
        if weight is None:
            check("unknown_with_cause", bool(re.search(r"sin dato|no.*(?:peso|calcular|disponible)", text))
                  and bool(re.search(r"autoridad|masa|motor|composici[oó]n|perfil|herrajes|contexto|bom", text)))
            check("no_fabricated_weight", not re.search(r"\d+(?:[.,]\d+)?\s*(?:kg|kilos)", text))
        else:
            numbers = [Decimal(n.replace(",", ".")) for n in re.findall(
                r"(\d+(?:[.,]\d+)?)\s*(?:kg|kilos)", text)]
            check("exact_engine_weight", numbers == [Decimal(weight)], weight, list(map(str, numbers)))
    elif expectation in {"engine_blockers", "backend_missing"}:
        key = "engine_blockers" if expectation == "engine_blockers" else "documentary_missing"
        expected = truth.get(key)
        if expected is None:
            check("context_available", False, key, None)
        else:
            actual = [a.get("payload", {}).get("blockers") for a in artifacts
                      if "blockers" in a.get("payload", {})]
            check("exact_backend_blockers", expected in actual or (expected == [] and
                  not ops and bool(re.search(r"sin bloqueos|no hay bloqueos|puedes guardar|validaci[oó]n.*v[aá]lid", text))),
                  expected, actual)
    elif expectation == "second_floor_glass":
        target_ids = truth.get("second_floor_ids") or []
        items = [item for s in steps if s.get("kind") == "batch_ops" for item in s.get("items") or []]
        actual_ids = [i.get("position_id") for i in items]
        check("exact_second_floor_targets", Counter(actual_ids) == Counter(target_ids) and bool(target_ids),
              target_ids, actual_ids)
        check("real_glass_ops", bool(items) and all(i.get("ops") and all(
            op.get("op") == "set_glass" and op.get("sku") == truth["existing_sku"]
            for op in i["ops"]) for i in items))
        check("sandbox_batch_applied", truth.get("batch_application_ok") is True)
    elif expectation in {"kitchen_position", "four_duplicates"}:
        drafts = [a.get("payload", {}) for a in artifacts if a.get("kind") in
                  {"project_draft", "product_draft"}]
        proposed = [p for draft in drafts for p in draft.get("positions", [])]
        if expectation == "kitchen_position":
            check("context_available", truth.get("sliding_supported") is not None,
                  "sliding compatibility evaluated by the selected catalog/engine", truth.get("sliding_supported"))
            valid = [p for p in proposed if p.get("opening_type") == "SLIDING_2L"
                     and _exact_decimal(p.get("width_mm"), "1600")
                     and _exact_decimal(p.get("height_mm"), "1100")
                     and "cocina" in str(p.get("location_tag") or p.get("location") or "").lower()]
            check("new_position_or_incompatibility", (bool(valid) and truth.get("sliding_supported") is True) or (
                truth.get("sliding_supported") is False and not proposed and not ops
                and bool(re.search(r"incompat|no admite", text))))
        else:
            source = truth.get("position_three")
            quantities = [change for draft in drafts for change in draft.get("quantity_changes", [])]
            quantity_alternative = source is not None and len(quantities) == 1 and (
                quantities[0].get("position_id") == source["id"] and
                quantities[0].get("quantity") == source["quantity"] + 4)
            allocations = (quantities[0].get("allocations") or []) if quantity_alternative else []
            quantity_alternative = quantity_alternative and bool(allocations) and all(
                _bedroom(a) and isinstance(a.get("quantity"), int) and not isinstance(a["quantity"], bool)
                and a["quantity"] > 0 for a in allocations) and sum(a["quantity"] for a in allocations) == 4
            check("four_exact_copies_or_quantity_plus_four", quantity_alternative or (
                  len(proposed) == 4 and source is not None and all(
                      p.get("design") == source.get("design") and _bedroom(p)
                      and p.get("quantity") == source["quantity"] for p in proposed)),
                "4 bedroom copies preserving design/quantity, or +4 with typed bedroom allocations", proposed)
    elif expectation == "most_expensive":
        winner = truth.get("most_expensive")
        check("context_available", winner is not None, "engine-priced positions", winner)
        check("exact_priced_position", winner is not None and winner in result.get("references", []))
    elif expectation == "discount_proposal":
        payloads = [a.get("payload", {}) for a in artifacts if a.get("kind") == "quote_draft"]
        check("discount_draft", any(_exact_decimal(p.get("discount_pct"), "0.05")
              for p in payloads), "typed 5 % quote draft", payloads)
        check("human_approval", result.get("state") == "WAITING_FOR_APPROVAL" or any(
            s.get("kind") == "prepare" for s in steps))
    elif expectation in {"prepare_quote", "prepare_purchase"}:
        action = "emit_revision" if expectation == "prepare_quote" else "send_purchase"
        if expectation == "prepare_quote":
            check("preparation_deeplink", any(s.get("kind") == "prepare" and
                  s.get("action") == action and s.get("path") == truth["quote_path"] for s in steps))
        else:
            check("purchase_plan", "purchase_plan" in kinds)
            check("context_available", truth.get("purchase_shortages") is not None,
                  "verified purchase coverage", truth.get("purchase_shortages"))
            check("real_shortages", truth.get("purchase_shortages") is not None and any(a.get("kind") == "purchase_plan" and
                  a.get("payload", {}).get("shortages") == truth.get("purchase_shortages")
                  for a in artifacts))
    elif expectation == "revision_comparison":
        revisions = truth.get("revisions") or []
        check("context_available", {"REV-A", "REV-B"} <= set(revisions), ["REV-A", "REV-B"], revisions)
        check("real_comparison", any(a.get("kind") == "comparison" and
              a.get("payload", {}).get("differences") == truth.get("revision_differences")
              and truth.get("revision_differences") is not None for a in artifacts))
    elif expectation == "blocked_orders":
        expected = truth.get("blocked_orders", [])
        actual = [a.get("payload", {}).get("orders") for a in artifacts if a.get("kind") == "production_plan"]
        check("exact_blocked_orders", expected in actual or (not expected and not result.get("claims")
              and bool(re.search(r"no (?:hay|tienes|aparecen|veo)|sin.*(?:ot|[oó]rdenes)", text))), expected, actual)
    elif expectation == "frame_bars":
        count = truth.get("frame_bars")
        check("context_available", count is not None, "cut-plan frame bars", count)
        counts = [a.get("payload", {}).get("frame_bars") for a in artifacts]
        check("exact_cut_plan_bars", count is not None and count in counts, count, counts)
    elif expectation == "offer_engine_draft":
        check("no_price_claim", not re.search(r"\$|\d+\s*(?:clp|pesos)", text))
        check("draft_before_calculation", bool(re.search(r"borrador", text)) and
              bool(re.search(r"motor|calcular", text)))
        check("no_automatic_creation", not ops)
    elif expectation == "opening_explanation":
        check("dual_tilt_and_turn", bool(re.search(r"(?:inclina|bascul|abatimiento|superior)", text)) and
              bool(re.search(r"lateral|gira|giro|bisagra", text)))
        check("no_technical_numbers", not re.search(r"\d+(?:[.,]\d+)?\s*(?:mm|kg|grados|°|\$)", text))
        check("no_mutation", not ops and after == before)
    else:
        raise ValueError(f"unknown oracle: {expectation}")

    passed = all(c["passed"] for c in checks)
    category = None
    if not passed:
        if changed_tables:
            category = "accion_consecuente_ejecutada"
        elif any(c["check"] == "context_available" and not c["passed"] for c in checks):
            category = "contexto_insuficiente"
        elif expectation == "installation_question" and not questions:
            category = "no_pidio_aclaracion"
        else:
            category = classify("", result.get("rejected") or [])
    return {"passed": passed, "failure": category, "checks": checks}


def summarize(cases: list[dict]) -> dict:
    by_view = {}
    for view in ("editor", "project", "factory", "general"):
        selected = [c for c in cases if c["view"] == view]
        by_view[view] = {"passed": sum(c["passed"] for c in selected), "total": len(selected)}
    failures = Counter(c["failure"] for c in cases if not c["passed"])
    return {"passed": sum(c["passed"] for c in cases), "total": len(cases), "by_view": by_view,
            "failure_counts": {name: failures[name] for name in FAILURES}}


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
