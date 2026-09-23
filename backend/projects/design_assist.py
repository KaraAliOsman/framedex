"""Design assist: natural-language intent → validated typed product ops.

The provider never touches the product — it proposes index-based operations;
this service validates every one against the actual assembly (index bounds,
enum and range checks) before the response exists. Rejected ops are reported,
never silently dropped: low-confidence intent must not mutate a position."""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from ai_gateway import service as gateway
from authentication.errors import contract_error
from engine_api.repository import SystemParamsRepository
from pricing.repository import rows

CAPABILITY = "design_assist"

OPENINGS = {
    "FIXED",
    "TURN_LEFT",
    "TURN_RIGHT",
    "TILT_TURN_LEFT",
    "TILT_TURN_RIGHT",
    "SLIDING_2L",
    "AWNING",
    "DOOR_ENTRY",
}

MAX_MODULE_COUNT = 12
MAX_OPS = 50

# The ops contract the provider must emit — sent as the system prompt so any
# OpenAI-compatible model produces exactly this document shape. Every op the
# model returns is validated server-side against the live product before it
# reaches the client, so the prompt constrains intent, never trust.
DESIGN_ASSIST_SYSTEM = """Eres el asistente de diseño de DEKOPEN, un editor profesional de ventanas y puertas de aluminio/PVC.

Recibes un JSON con:
- "prompt": la intención del usuario en lenguaje natural (español chileno).
- "product": el conjunto actual — "modules" (unidades) y "couplings" (uniones entre unidades), índices 0-based.
- "ops_contract": la lista de operaciones permitidas.
- "catalog": los SKU y espesores que existen en el catálogo del cliente.

Respondes SOLO un JSON: {"ops": [...], "notes": "resumen breve en español"}.

Operaciones:
- set_module_count {count}: redefine la cantidad de unidades (reparte el ancho).
- add_unit {side}: agrega una unidad, side "left"|"right".
- remove_unit {module}: elimina la unidad en ese índice.
- set_module_width {module, width_mm}: ancho de una unidad en mm.
- set_total_width {width_mm}: ancho total, reparte proporcional.
- set_height {height_mm}: alto de todas las unidades.
- equalize_widths: anchos iguales.
- equalize_angles: ángulos iguales entre uniones.
- set_coupling_angle {coupling, angle_deg}: ángulo de una unión (0 = recto).
- set_opening {module, opening}: apertura — FIXED, TURN_LEFT, TURN_RIGHT, TILT_TURN_LEFT, TILT_TURN_RIGHT, SLIDING_2L, AWNING, DOOR_ENTRY.
- set_glass {module, sku}: vidrio del catálogo.
- set_glass_thickness {module, mm}: espesor del catálogo.
- set_panel {module, sku|null}: panel del catálogo, null lo quita.

Reglas:
- Solo ops de ops_contract; solo SKU y espesores del catalog; nada de valores inventados.
- Índices válidos: 0..len(modules)-1 y 0..len(couplings)-1.
- Las medidas numéricas (count, width_mm, height_mm, angle_deg, mm) solo pueden citar números que el usuario escribió en "prompt"; si el usuario no declaró una medida, no la inventes — explícalo en "notes".
- Si la intención es ambigua, propón menos ops y explícalo en "notes"; nunca adivines medidas que el usuario no pidió.
- Sin texto fuera del JSON."""


def _number(value: Any) -> Decimal | None:
    if isinstance(value, bool):
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return result if result.is_finite() else None


def _in_range(value: Any, low: Decimal, high: Decimal) -> bool:
    parsed = _number(value)
    return parsed is not None and low <= parsed <= high


def _summary(product: Any) -> dict | None:
    """The client-submitted product surface — the same modules and couplings
    the returned ops will be applied against, so index bounds are derived
    here and can never drift against a stale persisted copy."""
    if not isinstance(product, dict):
        return None
    modules_raw = product.get("modules")
    if not isinstance(modules_raw, list) or not 1 <= len(modules_raw) <= MAX_MODULE_COUNT:
        return None
    couplings_raw = product.get("couplings") or []
    if not isinstance(couplings_raw, list) or len(couplings_raw) > MAX_MODULE_COUNT:
        return None
    return {
        "modules": [
            {
                "index": index,
                "width_mm": module.get("width_mm") if isinstance(module, dict) else None,
                "height_mm": module.get("height_mm") if isinstance(module, dict) else None,
            }
            for index, module in enumerate(modules_raw)
        ],
        "couplings": [
            {
                "index": index,
                "angle_deg": coupling.get("angle_deg") if isinstance(coupling, dict) else None,
            }
            for index, coupling in enumerate(couplings_raw)
        ],
    }


def _catalog(system_id: UUID, org_id: UUID) -> dict:
    """The selected system's authoritative material surface — a SKU is a
    catalog identifier, never free text, so proposed glass, panels and
    thicknesses must resolve against the same options the estimator sees.
    load_visible scopes to the org: a system the tenant cannot see is the
    same 404 the design-options surface returns."""
    repository = SystemParamsRepository()
    params = repository.load_visible(system_id, org_id)
    glass_rows = rows(
        "SELECT DISTINCT ON (technical_sku) technical_sku "
        "FROM public.glass_purchase_mappings "
        "WHERE system_id=%s AND (org_id=%s OR org_id IS NULL) "
        "ORDER BY technical_sku, org_id NULLS LAST, version DESC",
        [system_id, org_id],
    )
    return {
        "glass_skus": {item["technical_sku"] for item in glass_rows},
        "panel_skus": set(params.available_panel_rules),
        "thicknesses": set(params.glazing_bead_rules),
    }


_NUMBER_WORDS = {
    "un": 1,
    "uno": 1,
    "una": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
    "once": 11,
    "doce": 12,
}
_MEASURE_RE = re.compile(
    r"(\d+(?:[.,]\d+)*)\s*(mm|mil[ií]metros?|cm|metros?|mts?|m)\b",
    re.IGNORECASE,
)
_BARE_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)*")
_WORD_NUMBER_RE = re.compile(
    r"\b(uno?|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce)\b",
    re.IGNORECASE,
)


def _parse_number(token: str) -> Decimal | None:
    """Chilean-locale number: '.' groups thousands (2.400 → 2400), ',' is the
    decimal mark (2,4 → 2.4). A lone '.' with three trailing digits reads as
    thousands so '2.400' means 2400, matching how users write medidas."""
    try:
        if "." in token and "," in token:
            normalized = token.replace(".", "").replace(",", ".")
        elif token.count(".") == 1 and len(token.rsplit(".", 1)[1]) == 3:
            normalized = token.replace(".", "")
        else:
            normalized = token.replace(",", ".")
        value = Decimal(normalized)
    except ArithmeticError:
        return None
    return value if value.is_finite() else None


def _declared_values(prompt: str) -> set[Decimal]:
    """Every number the user actually wrote — the grounding set numeric ops
    must cite. The model proposes structure; it may never introduce a
    measurement the request did not contain. Unit-suffixed measures normalize
    to mm, bare numbers count literally, number words cover counts."""
    values: set[Decimal] = set()
    for token, unit in _MEASURE_RE.findall(prompt):
        number = _parse_number(token)
        if number is None:
            continue
        unit = unit.lower()
        if unit == "cm":
            factor = Decimal(10)
        elif unit.startswith("mm") or unit.startswith("mil"):
            factor = Decimal(1)
        else:  # m, mt, mts, metro, metros
            factor = Decimal(1000)
        values.add(number * factor)
    # Unit-suffixed spans are consumed by the first pass — their raw tokens
    # must not re-enter the set unconverted ('240 cm' declares 2400mm, not 240).
    for token in _BARE_NUMBER_RE.findall(_MEASURE_RE.sub("", prompt)):
        number = _parse_number(token)
        if number is not None:
            values.add(number)
    for word in _WORD_NUMBER_RE.findall(prompt):
        values.add(Decimal(_NUMBER_WORDS[word.lower()]))
    return values


def _validate_ops(
    ops: Any, summary: dict, catalog: dict, declared: set[Decimal]
) -> tuple[list[dict], list[dict]]:
    """Validate each op against a simulated assembly that evolves in op order —
    structural ops mutate the module/coupling counts every later op is checked
    against, so a proposal can never address a module that stopped existing or
    grow the assembly past MAX_MODULE_COUNT."""
    state = {"modules": len(summary["modules"]), "couplings": len(summary["couplings"])}

    def module_index(value: Any) -> bool:
        return (
            isinstance(value, int) and not isinstance(value, bool) and 0 <= value < state["modules"]
        )

    def coupling_index(value: Any) -> bool:
        return (
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value < state["couplings"]
        )

    def reject(item: Any, reason: str) -> dict:
        return {"op": item.get("op") if isinstance(item, dict) else None, "reason": reason}

    accepted: list[dict] = []
    rejected: list[dict] = []
    if not isinstance(ops, list):
        return [], [{"op": None, "reason": "formato_invalido"}]
    for item in ops[:MAX_OPS]:
        if not isinstance(item, dict) or not isinstance(item.get("op"), str):
            rejected.append(reject(item, "formato_invalido"))
            continue
        name = item["op"]
        if name == "set_module_count":
            if not (
                isinstance(item.get("count"), int)
                and not isinstance(item["count"], bool)
                and Decimal(item["count"]) in declared
            ):
                rejected.append(reject(item, "cantidad_no_declarada"))
            elif 1 <= item["count"] <= MAX_MODULE_COUNT:
                accepted.append({"op": name, "count": item["count"]})
                state["modules"] = item["count"]
                state["couplings"] = max(0, item["count"] - 1)
            else:
                rejected.append(reject(item, "cantidad_invalida"))
        elif name == "add_unit":
            if item.get("side") in ("left", "right") and state["modules"] < MAX_MODULE_COUNT:
                accepted.append({"op": name, "side": item["side"]})
                state["modules"] += 1
                state["couplings"] = state["modules"] - 1
            else:
                rejected.append(reject(item, "lado_invalido"))
        elif name == "remove_unit":
            if module_index(item.get("module")) and state["modules"] > 1:
                accepted.append({"op": name, "module": item["module"]})
                state["modules"] -= 1
                state["couplings"] = state["modules"] - 1
            else:
                rejected.append(reject(item, "modulo_invalido"))
        elif name == "set_module_width":
            if _number(item.get("width_mm")) not in declared:
                rejected.append(reject(item, "ancho_no_declarado"))
            elif module_index(item.get("module")) and _in_range(
                item.get("width_mm"), Decimal("150"), Decimal("6000")
            ):
                accepted.append(
                    {
                        "op": name,
                        "module": item["module"],
                        "width_mm": str(_number(item["width_mm"])),
                    }
                )
            else:
                rejected.append(reject(item, "ancho_invalido"))
        elif name == "set_total_width":
            if _number(item.get("width_mm")) not in declared:
                rejected.append(reject(item, "ancho_no_declarado"))
            elif _in_range(
                item.get("width_mm"),
                Decimal("150") * state["modules"],
                Decimal("30000"),
            ):
                accepted.append({"op": name, "width_mm": str(_number(item["width_mm"]))})
            else:
                rejected.append(reject(item, "ancho_invalido"))
        elif name == "set_height":
            if _number(item.get("height_mm")) not in declared:
                rejected.append(reject(item, "alto_no_declarado"))
            elif _in_range(item.get("height_mm"), Decimal("200"), Decimal("4000")):
                accepted.append({"op": name, "height_mm": str(_number(item["height_mm"]))})
            else:
                rejected.append(reject(item, "alto_invalido"))
        elif name == "equalize_widths":
            accepted.append({"op": name})
        elif name == "equalize_angles":
            accepted.append({"op": name})
        elif name == "set_coupling_angle":
            if coupling_index(item.get("coupling")) and _in_range(
                item.get("angle_deg"), Decimal("-90"), Decimal("90")
            ):
                accepted.append(
                    {
                        "op": name,
                        "coupling": item["coupling"],
                        "angle_deg": str(_number(item["angle_deg"])),
                    }
                )
            else:
                rejected.append(reject(item, "angulo_invalido"))
        elif name == "set_opening":
            if module_index(item.get("module")) and item.get("opening") in OPENINGS:
                accepted.append(
                    {
                        "op": name,
                        "module": item["module"],
                        "opening": item["opening"],
                    }
                )
            else:
                rejected.append(reject(item, "apertura_invalida"))
        elif name == "set_glass_thickness":
            if (
                module_index(item.get("module"))
                and _number(item.get("mm")) in catalog["thicknesses"]
            ):
                accepted.append(
                    {
                        "op": name,
                        "module": item["module"],
                        "mm": str(_number(item["mm"])),
                    }
                )
            else:
                rejected.append(reject(item, "espesor_invalido"))
        elif name == "set_glass":
            if module_index(item.get("module")) and item.get("sku") in catalog["glass_skus"]:
                accepted.append({"op": name, "module": item["module"], "sku": item["sku"]})
            else:
                rejected.append(reject(item, "vidrio_invalido"))
        elif name == "set_panel":
            if module_index(item.get("module")) and (
                item.get("sku") is None or item["sku"] in catalog["panel_skus"]
            ):
                accepted.append({"op": name, "module": item["module"], "sku": item.get("sku")})
            else:
                rejected.append(reject(item, "panel_invalido"))
        else:
            rejected.append(reject(item, "operacion_desconocida"))
    for item in ops[MAX_OPS:]:
        rejected.append(reject(item, "limite_operaciones"))
    return accepted, rejected


def assist(
    *,
    org_id: UUID,
    user_id: UUID,
    position: dict,
    product: Any,
    prompt: str,
    operation_key: str,
    system_id: UUID,
) -> dict:
    summary = _summary(product)
    if summary is None:
        raise contract_error(
            400,
            "design_assist_product_invalid",
            "El producto del asistente no tiene una estructura válida.",
        )
    catalog = _catalog(system_id, org_id)
    envelope = gateway.invoke(
        org_id=org_id,
        user_id=user_id,
        capability=CAPABILITY,
        operation_key=operation_key,
        tool_name="design_assist",
        # Transport controls ride in provider_options — they are server-side
        # config, not client input, so they never touch the audited payload or
        # its replay hash (a prompt edit must not break idempotent retries).
        provider_options={
            "system": DESIGN_ASSIST_SYSTEM,
            "json_output": True,
        },
        input_payload={
            "prompt": prompt,
            "position_id": str(position["id"]),
            "system_id": str(system_id),
            "product": summary,
            "ops_contract": sorted(
                {
                    "add_unit",
                    "equalize_angles",
                    "equalize_widths",
                    "remove_unit",
                    "set_coupling_angle",
                    "set_glass",
                    "set_glass_thickness",
                    "set_height",
                    "set_module_count",
                    "set_module_width",
                    "set_opening",
                    "set_panel",
                    "set_total_width",
                }
            ),
            "catalog": {
                "glass_skus": sorted(catalog["glass_skus"]),
                "panel_skus": sorted(catalog["panel_skus"]),
                "glazing_thicknesses": [
                    str(thickness) for thickness in sorted(catalog["thicknesses"])
                ],
            },
        },
    )
    try:
        document = json.loads(envelope["output"])
    except (json.JSONDecodeError, TypeError):
        raise contract_error(
            502,
            "design_assist_bad_output",
            "El asistente devolvió una respuesta inválida.",
        ) from None
    if not isinstance(document, dict):
        raise contract_error(
            502,
            "design_assist_bad_output",
            "El asistente devolvió una respuesta inválida.",
        )
    ops, rejected = _validate_ops(document.get("ops"), summary, catalog, _declared_values(prompt))
    return {
        "audit_id": envelope["audit_id"],
        "model": envelope["model"],
        "credits_debited": envelope["credits_debited"],
        "ops": ops,
        "rejected": rejected,
        "notes": document.get("notes") if isinstance(document.get("notes"), str) else None,
    }
