"""Design alternatives: a brief → engine-validated candidate products.

The provider proposes intent-level structure only — a label, a rationale,
an opening per module, an optional bow angle. The backend constructs the
real product-v2 model from catalog-approved materials, runs every
candidate through the engine, and returns only VALID assemblies with
their computed metrics. A candidate the engine cannot evaluate is
reported as rejected with its issue codes — it never reaches the client
as a usable product, and no number in the response comes from the model."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any
from uuid import UUID

from ai_gateway import service as gateway
from authentication.errors import contract_error
from engine_api.adapter import evaluate_assembly_from_api, parse_product_model
from engine_api.repository import SystemParamsRepository
from projects.design_assist import OPENINGS, _catalog

CAPABILITY = "design_alternatives"
MAX_ALTERNATIVES = 3
MAX_MODULE_COUNT = 12
MIN_DIMENSION_MM = Decimal("150")
MAX_WIDTH_MM = Decimal("6000")
MAX_HEIGHT_MM = Decimal("4000")
ZERO = Decimal("0")

ALTERNATIVES_SYSTEM = """Eres el diseñador de alternativas de DEKOPEN, un editor profesional de ventanas y puertas de aluminio/PVC.

Recibes un JSON con:
- "brief": la intención del usuario en lenguaje natural (español chileno).
- "width_mm" y "height_mm": las medidas fijas de la posición — nunca las cambies.
- "count": cuántas alternativas distintas proponer.
- "openings_contract": las aperturas permitidas por módulo.
- "catalog": los SKU y espesores que existen en el catálogo del cliente.

Respondes SOLO un JSON: {"alternatives": [...], "notes": "resumen breve en español"}.

Cada alternativa:
- "label": nombre corto en español ("Corredera 2 hojas").
- "rationale": una frase — por qué sirve para el brief.
- "openings": una lista de aperturas, UNA por módulo (su largo define los módulos; entre 1 y 12).
- "angle_deg": opcional, solo para conjuntos en quiebre (bow) — el mismo ángulo en cada unión.
- "glass_sku": opcional, SOLO un valor de catalog.glass_skus.
- "panel_sku": opcional, SOLO un valor de catalog.panel_skus.

Reglas:
- Alternativas realmente distintas entre sí (estructura, no solo nombres).
- Solo aperturas de openings_contract; solo SKU del catalog; nada de valores inventados.
- Si el brief pide algo concreto (corredera, puerta, arco), una alternativa debe reflejarlo.
- Sin texto fuera del JSON."""


def _dimensions(width: Any, height: Any) -> tuple[Decimal, Decimal]:
    try:
        width_mm = Decimal(str(width))
        height_mm = Decimal(str(height))
    except ArithmeticError:
        raise contract_error(
            400, "design_dims_invalid", "Las medidas de la posición no son válidas."
        ) from None
    if not MIN_DIMENSION_MM <= width_mm <= MAX_WIDTH_MM:
        raise contract_error(
            400, "design_width_invalid", "El ancho de la posición no es válido."
        )
    if not MIN_DIMENSION_MM <= height_mm <= MAX_HEIGHT_MM:
        raise contract_error(
            400, "design_height_invalid", "El alto de la posición no es válido."
        )
    return width_mm, height_mm


def _default_thickness(catalog: dict) -> Decimal:
    thicknesses = sorted(Decimal(str(t)) for t in catalog["thicknesses"])
    return thicknesses[0] if thicknesses else Decimal("4.00")


def _build_product(
    spec: dict,
    *,
    width_mm: Decimal,
    height_mm: Decimal,
    catalog: dict,
) -> tuple[dict | None, str | None]:
    """Intent spec → product-v2 payload. Every opening is checked against
    the contract set and every SKU against the org-visible catalog before
    the model exists — the engine still has the last word afterwards."""
    openings = spec.get("openings")
    if (
        not isinstance(openings, list)
        or not openings
        or len(openings) > MAX_MODULE_COUNT
        or any(opening not in OPENINGS for opening in openings)
    ):
        return None, "aperturas_invalidas"
    glass_sku = spec.get("glass_sku")
    if glass_sku is not None and glass_sku not in catalog["glass_skus"]:
        return None, "vidrio_desconocido"
    panel_sku = spec.get("panel_sku")
    if panel_sku is not None and panel_sku not in catalog["panel_skus"]:
        return None, "panel_desconocido"
    angle = spec.get("angle_deg")
    if angle is not None:
        try:
            angle = Decimal(str(angle))
        except ArithmeticError:
            return None, "angulo_invalido"
        if not Decimal("-90") <= angle <= Decimal("90"):
            return None, "angulo_invalido"
    thickness = _default_thickness(catalog)
    quantum = Decimal("0.01")
    share = (width_mm / len(openings)).quantize(quantum)
    remaining = width_mm
    modules = []
    couplings = []
    for index, opening in enumerate(openings, start=1):
        module_width = remaining if index == len(openings) else share
        remaining -= share
        tree = {
            "id": f"m{index}",
            "type": "BAY",
            "opening_type": opening,
            "glass_thickness_mm": str(thickness),
            "glass_spec": "4",
        }
        if glass_sku:
            tree["glass_article_sku"] = glass_sku
        if panel_sku:
            tree["panel_article_sku"] = panel_sku
        modules.append(
            {
                "id": f"m{index}",
                "width_mm": str(module_width.quantize(quantum)),
                "height_mm": str(height_mm.quantize(quantum)),
                "tree": tree,
            }
        )
        if index > 1:
            couplings.append(
                {
                    "id": f"c{index - 1}",
                    "angle_deg": str((angle or ZERO).quantize(Decimal("0.1"))),
                    "coupler_profile_sku": None,
                }
            )
    return {"version": "product-v2", "assembly": {"modules": modules, "couplings": couplings}}, None


def _metrics(evaluation, model) -> dict:
    """The card surface — every figure comes from the engine's own BOM and
    evaluation, never from the provider document."""
    bom = evaluation.bom
    modules = model.assembly.modules
    metrics = {
        "module_count": len(modules),
        "openings": [
            str(module.tree.opening_type.value) for module in modules
        ],
        "plan_width_mm": str(evaluation.plan.width_mm) if evaluation.plan else None,
        "plan_height_mm": str(evaluation.plan.height_mm) if evaluation.plan else None,
        "status": evaluation.status.value,
        "warnings": sorted(
            {
                str(issue.code)
                for issue in evaluation.issues
            }
            | {
                str(issue.code)
                for module_eval in evaluation.modules
                for issue in module_eval.issues
            }
        ),
    }
    if bom is None:
        return metrics
    metrics.update(
        {
            "glass_pieces": len(bom.glasses),
            "glass_area_m2": str(
                sum((piece.area_m2 for piece in bom.glasses), ZERO).quantize(
                    Decimal("0.01")
                )
            ),
            "profile_cuts": len(bom.profile_cuts),
            "reinforcements": len(bom.reinforcements),
            "hardware_items": len(bom.hardware_items),
            "total_weight_kg": str(
                sum((leaf.total_weight_kg for leaf in bom.leaf_weights), ZERO).quantize(
                    Decimal("0.01")
                )
            ),
        }
    )
    return metrics


def alternatives(
    *,
    org_id: UUID,
    user_id: UUID,
    position: dict,
    brief: str,
    count: int,
    operation_key: str,
    system_id: UUID,
) -> dict:
    count = max(1, min(MAX_ALTERNATIVES, int(count)))
    width_mm, height_mm = _dimensions(position["width_mm"], position["height_mm"])
    catalog = _catalog(system_id, org_id)
    repository = SystemParamsRepository()
    params = repository.load_visible(system_id, org_id)
    coupler_articles = repository.load_coupler_articles(system_id, org_id)
    envelope = gateway.invoke(
        org_id=org_id,
        user_id=user_id,
        capability=CAPABILITY,
        operation_key=operation_key,
        tool_name="design_alternatives",
        provider_options={
            "system": ALTERNATIVES_SYSTEM,
            "json_output": True,
        },
        input_payload={
            "brief": brief,
            "position_id": str(position["id"]),
            "system_id": str(system_id),
            "width_mm": str(width_mm),
            "height_mm": str(height_mm),
            "count": count,
            "openings_contract": sorted(OPENINGS),
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
            "design_alternatives_bad_output",
            "El asistente devolvió una respuesta inválida.",
        ) from None
    if not isinstance(document, dict):
        raise contract_error(
            502,
            "design_alternatives_bad_output",
            "El asistente devolvió una respuesta inválida.",
        )
    raw_alternatives = document.get("alternatives")
    if not isinstance(raw_alternatives, list):
        raw_alternatives = []
    accepted: list[dict] = []
    rejected: list[dict] = []
    for spec in raw_alternatives[:MAX_ALTERNATIVES]:
        if not isinstance(spec, dict):
            rejected.append({"label": None, "reasons": ["formato_invalido"]})
            continue
        label = str(spec.get("label") or "")[:80] or "Alternativa"
        product_payload, reason = _build_product(
            spec,
            width_mm=width_mm,
            height_mm=height_mm,
            catalog=catalog,
        )
        if reason is not None:
            rejected.append({"label": label, "reasons": [reason]})
            continue
        try:
            model = parse_product_model(product_payload)
            evaluation = evaluate_assembly_from_api(
                product=model,
                color="WHITE",
                params=params,
                coupler_articles=coupler_articles,
            )
        except ValueError:
            rejected.append({"label": label, "reasons": ["producto_invalido"]})
            continue
        # The same gate the save path applies: warnings are a readiness flag
        # the card can show, INVALID or a partial BOM can never be offered as
        # a usable product.
        if (
            evaluation.status.value == "INVALID"
            or evaluation.bom is None
            or any(module_eval.result is None for module_eval in evaluation.modules)
        ):
            codes = sorted(
                {
                    str(issue.code)
                    for issue in evaluation.issues
                    if str(issue.severity.value) == "error"
                }
                | {
                    str(issue.code)
                    for module_eval in evaluation.modules
                    for issue in module_eval.issues
                    if str(issue.severity.value) == "error"
                }
            ) or ["evaluacion_invalida"]
            rejected.append({"label": label, "reasons": codes})
            continue
        accepted.append(
            {
                "label": label,
                "rationale": str(spec.get("rationale") or "")[:400] or None,
                "product": json.loads(model.model_dump_json()),
                "metrics": _metrics(evaluation, model),
            }
        )
    return {
        "audit_id": envelope["audit_id"],
        "model": envelope["model"],
        "credits_debited": envelope["credits_debited"],
        "alternatives": accepted,
        "rejected": rejected,
        "notes": document.get("notes") if isinstance(document.get("notes"), str) else None,
    }
