"""Catalog review facts. Historical geometry remains readable and unchanged."""

from decimal import Decimal
from typing import Any

from .models import MaterialType, ProfileRole, ProfileSection, SystemParams


def section_review_facts(section: ProfileSection | None) -> dict[str, Any]:
    """Exact section bounds and review gates, without inferring missing facts.

    Screen fitting is a renderer concern; a coordinate unit is one mm, never
    a claim that a fitted thumbnail is physically 1:1. These stricter review
    gates do not change the historical ProfileSection transport or its cuts.
    """
    if section is None:
        return {"state": "UNKNOWN", "valid": False, "reasons": ["section_missing"],
                "bounds": None, "orientation": None, "local_origin": None,
                "interpretation_declared": False}
    xs = [p.x_mm for p in section.polygon]
    ys = [p.y_mm for p in section.polygon]
    min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
    width, height = max_x - min_x, max_y - min_y
    reasons = []
    declared = {"orientation", "local_origin"}.issubset(section.model_fields_set)
    if not declared:
        reasons.append("section_interpretation_missing")
    depth = width if section.orientation in ("EXTERIOR_LEFT", "EXTERIOR_RIGHT") else height
    if depth != section.depth_mm:
        reasons.append("section_depth_mismatch")
    origin = section.local_origin
    anchor = {
        "TOP_LEFT": (min_x, min_y), "TOP_RIGHT": (max_x, min_y),
        "BOTTOM_LEFT": (min_x, max_y), "BOTTOM_RIGHT": (max_x, max_y),
    }.get(origin)
    if origin == "CENTROID":
        area2 = Decimal(0)
        x_sum = Decimal(0)
        y_sum = Decimal(0)
        points = section.polygon
        for index, a in enumerate(points):
            b = points[(index + 1) % len(points)]
            cross = a.x_mm * b.y_mm - b.x_mm * a.y_mm
            area2 += cross
            x_sum += (a.x_mm + b.x_mm) * cross
            y_sum += (a.y_mm + b.y_mm) * cross
        # Testing the numerator keeps the 0.00 mm tolerance exact even when
        # the centroid's rational coordinate has a repeating decimal.
        anchor = (x_sum, y_sum)
    if anchor != (Decimal(0), Decimal(0)):
        reasons.append("section_origin_mismatch")
    return {"state": "PASS" if not reasons else "BLOCK", "valid": not reasons,
            "reasons": reasons, "interpretation_declared": declared,
            "bounds": {"min_x_mm": str(min_x), "max_x_mm": str(max_x),
                       "min_y_mm": str(min_y), "max_y_mm": str(max_y),
                       "width_mm": str(width), "height_mm": str(height)},
            "orientation": section.orientation if declared else None,
            "local_origin": origin if declared else None}


def process_authority_gate(process_facts: object) -> dict[str, Any]:
    """The same declared-process gate at catalog, seal and release time.

    Callers choose current catalog facts or frozen revision facts explicitly.
    An inactive work center is a station blocker, not a missing process; it
    must never rewrite this decision or reinterpret an issued revision.
    """
    declared = isinstance(process_facts, dict) and process_facts.get("resolved_via") not in (
        None, "generic_fallback"
    ) and isinstance(process_facts.get("profile"), dict)
    return {"state": "PASS" if declared else "BLOCK", "ok": declared,
            "reasons": [] if declared else ["production_process_unresolved"]}


def fabrication_authority_gate(
    params: SystemParams, *, profile_skus: set[str] | None = None,
    hardware_skus: set[str] | None = None,
) -> dict[str, Any]:
    """One rule for catalog coverage and the articles consumed by a position.

    A catalog checks every effective role; a seal supplies its consumed SKUs.
    These are explicit scopes of the same predicate, never a numeric fallback.
    """
    missing: list[str] = []
    if params.rebate_depth_mm is None:
        missing.append("rebate_depth_mm")
    if params.end_milling_overlap_mm is None:
        missing.append("end_milling_overlap_mm")
    for role, article in params.effective_profile_articles.items():
        if profile_skus is not None and article.sku not in profile_skus:
            continue
        if params.uses_legacy_rules:
            if params.material is MaterialType.PVC and role is not ProfileRole.THRESHOLD and (
                article.welding_loss_mm is None or article.reinforcement_gap_mm is None
            ):
                missing.append(article.sku)
        elif article.cut_rule is None or (
            params.material is MaterialType.PVC
            and role not in (ProfileRole.GLAZING_BEAD, ProfileRole.RAIL, ProfileRole.THRESHOLD,
                            ProfileRole.CHANNEL, ProfileRole.SILL, ProfileRole.FRAME_EXTENSION,
                            ProfileRole.COVER_TRIM, ProfileRole.ADDITIONAL)
            and article.reinforcement_rule is None
        ):
            missing.append(article.sku)
        if role in (ProfileRole.SASH, ProfileRole.SLIDING_SASH, ProfileRole.DOOR_SASH) and (
            article.weight_kg_m is None or (
                (bool(article.reinforcement_sku) or article.reinforcement_rule is not None)
                and article.steel_weight_kg_m is None
            )
        ):
            missing.append(article.sku)
    for kit in params.available_hardware_kits:
        if hardware_skus is not None and kit.sku not in hardware_skus:
            continue
        if kit.class_authority is None:
            incomplete = kit.weight_kg is None
        else:
            rules = (*kit.class_authority.components,
                     *(rule for option in kit.class_authority.options for rule in option.components),
                     *(color.component for handle in kit.class_authority.handles for color in handle.colors))
            incomplete = any(rule.weight_kg is None and rule.weight_kg_m is None for rule in rules)
        if incomplete:
            missing.append(kit.sku)
    return {"state": "BLOCK" if missing else "PASS", "ok": not missing,
            "missing": sorted(set(missing))}
