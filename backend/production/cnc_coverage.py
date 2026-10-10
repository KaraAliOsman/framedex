"""CNC coverage from immutable revision inputs; never from today's catalog."""

from __future__ import annotations

import json

from dekopen_engine.manufacturing import ManufacturingFactsV1
from dekopen_engine.models import SystemParams
from dekopen_engine.models import HardwareItem
from dekopen_engine.hardware_machining import hardware_operations
from dekopen_engine.operations import ManufacturingOperation


def freeze_profile_sections(params: SystemParams, skus: set[str]) -> dict[str, object]:
    articles = {article.sku: article for article in params.effective_profile_articles.values()}
    for rule in params.glazing_bead_rules.values():
        articles[rule.bead_article.sku] = rule.bead_article
    sections = {}
    for sku in sorted(skus):
        article = articles.get(sku)
        section = article.section if article else None
        if section is not None:
            sections[sku] = {**section.model_dump(mode="python"),
                "orientation_declared": "orientation" in section.model_fields_set,
                "origin_declared": "local_origin" in section.model_fields_set,
                "catalog_system": params.system_code,
                "synthetic": params.system_code.startswith("DEMO"),
                "authority_source": section.drawing_ref or f"Sección declarada de {sku}"}
    return sections


def sealed_sections(snapshot, position_id, units):
    by_position = {str(p.get("id")): p.get("profile_sections") or {}
                   for p in snapshot.get("positions") or []
                   if isinstance(p, dict) and (not position_id or str(p.get("id")) == position_id)}
    return {member.member_id: by_position.get(unit.position_id, {}).get(member.workshop_sku)
            for unit in units for member in unit.members}


def declared_gaps(snapshot, position_id, units: list[ManufacturingFactsV1],
                  ops: list[ManufacturingOperation], issues):
    """One declaration per physical unit/target, with explicit absence cause.

Legacy drain/closing annotations have perimeter coordinates but no emitter.
A HANDLE_PREP point is emitted as a reference; incomplete pattern remains
declared-unemitted for execution even when the reference exists elsewhere.
"""
    gaps = []
    for position in snapshot.get("positions") or []:
        if position_id and str(position.get("id")) != position_id:
            continue
        for unit in units:
            if unit.position_id != str(position.get("id")):
                continue
            bom = next((b for b in snapshot.get("bom") or [] if str(b.get("position_id")) == unit.position_id), {})
            items = [HardwareItem.model_validate_json(json.dumps(item)) for item in
                     (bom.get("engine_result") or {}).get("hardware_items") or []]
            if unit.module_id is not None:
                prefix = unit.module_id + "|"
                items = [item for item in items if item.bay_id.startswith(prefix)]
            unit_issues = []
            hardware_operations(items=items, fact_units=[unit], issues=unit_issues)
            gaps.extend({**issue, "reason_code": "authority_incomplete",
                         "position_id": unit.position_id, "position_index": unit.position_index,
                         "unit_index": unit.repetition_index}
                        for issue in unit_issues if issue.get("code") == "declared_intent_not_emitted")
            for annotation in position.get("workshop_annotations") or []:
                if unit.module_id is not None and not str(annotation.get("bay_id")).startswith(unit.module_id + "|"):
                    continue
                for field, kind, name in (("bottom_drain_holes_mm", "DRAINAGE", "Drenaje"),
                                         ("closing_points_perimeter_mm", "LOCK_PREP", "Puntos de cierre")):
                    if annotation.get(field):
                        gaps.append({"kind": kind, "name": name,
                            "bay_id": annotation.get("bay_id"), "leaf_id": annotation.get("leaf_id"),
                            "position_id": unit.position_id, "unit_index": unit.repetition_index,
                            "position_index": unit.position_index,
                            "reason_code": "emitter_not_implemented",
                            "detail": "Emisor no implementado para esta declaración sellada. No se generó trabajo de máquina.",
                            "source": "Anotación de taller de la revisión emitida"})
            for handle in unit.handles:
                matching = [op for op in ops if op.host == handle.host_member_id and op.kind.value == "HANDLE_PREP"]
                if not matching or any(op.detail.get("feature") == "point_prep" for op in matching):
                    gaps.append({"kind": "HANDLE_PREP", "name": "Preparación de manilla",
                        "member_id": handle.host_member_id, "position_id": unit.position_id,
                        "position_index": unit.position_index,
                        "unit_index": unit.repetition_index,
                        "reason_code": "rule_missing", "detail": "Solo se selló el punto de manilla; faltan patrón de agujeros y profundidad.",
                        "source": "Regla de manilla de la revisión emitida"})
    return gaps
