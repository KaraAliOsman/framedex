"""A review stamp is not a certificate. Evidence must match current values."""

from decimal import Decimal, InvalidOperation
import json

from dekopen_engine.catalog_authority import section_review_facts
from dekopen_engine.models import ProfileSection
from pricing.repository import json_text, rows


def section_facts(row):
    try:
        value = row.get("section")
        model = ProfileSection.model_validate_json(json_text(value)) if value is not None else None
        return section_review_facts(model)
    except (ValueError, TypeError):
        return {"state": "BLOCK", "valid": False, "reasons": ["section_invalid"],
                "bounds": None, "orientation": None, "local_origin": None,
                "interpretation_declared": False}


def _equivalent(left, right):
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(_equivalent(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_equivalent(a, b) for a, b in zip(left, right, strict=True))
    if left is None or right is None or isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    try:
        a, b = Decimal(str(left)), Decimal(str(right))
        if a.is_finite() and b.is_finite():
            return a == b
    except InvalidOperation:
        pass
    return left == right


def _value(row, field):
    # The interchange labels differ from storage for these identity fields.
    aliases = {"system_code": "code", "sliding.pulley_height_mm": "pulley_height_mm",
        "sliding.central_overlap_mm": "central_overlap_mm",
        "sliding.lateral_clearance_mm": "sliding_lateral_clearance_mm",
        "sliding.end_add_mm": "sliding_end_add_mm",
        "sliding.glazing_deduction_width_mm": "sliding_glazing_deduction_width_mm",
        "sliding.glazing_deduction_height_mm": "sliding_glazing_deduction_height_mm",
        "sliding.rail_type": "rail_type"}
    if field.startswith("sliding.") and row.get("sliding_parameters"):
        return row["sliding_parameters"].get(field.removeprefix("sliding."))
    return row.get(aliases.get(field, field))


def evidence_matches(row, evidence):
    value = evidence.get("canonical_value")
    if isinstance(value, str):
        try:
            value = json.loads(value, parse_float=Decimal)
        except ValueError:
            pass  # PostgreSQL JSONB string values may already be decoded.
    if value is None:
        legacy = evidence.get("value_text")
        if legacy is None:
            return False
        try:
            value = json.loads(legacy, parse_float=Decimal)
        except (ValueError, TypeError):
            value = legacy
    return _equivalent(_value(row, evidence["field_name"]), value)


def decorate(resource, records, org_id):
    """Add read projections after the optimistic revision was calculated."""
    if not records or "data_provenance" not in records[0]:
        return
    ids = [str(row["id"]) for row in records]
    evidence = rows("SELECT * FROM public.catalog_parameter_evidence WHERE authority_table=%s "
                    "AND row_id=ANY(%s::uuid[]) AND (org_id IS NULL OR org_id=%s) "
                    "ORDER BY declared_at,id", [resource.table, ids, org_id])
    for row in records:
        current = [ev for ev in evidence if str(ev["row_id"]) == str(row["id"])]
        matching = [ev for ev in current if ev["review_state"] == "REVIEWED"
                    and evidence_matches(row, ev) and
                    (ev.get("source_page") or ev.get("source_ref") or ev.get("source_url")) and
                    ev.get("extraction_method") != "HUMAN_CORRECTION"]
        # Every present numeric or structured technical authority needs its
        # own evidence. Human review alone never promotes a row to VERIFIED.
        required = [key for key in resource.fields if row.get(key) is not None and (
            key.endswith(("_mm", "_kg", "_kg_m", "_kg_m2")) or key in (
                "section", "cut_rule", "reinforcement_rule", "class_authority",
                "dimensional_limits", "opening_capabilities", "sliding_parameters",
                "contents", "coupling_rule", "paired_leaf_rule", "extra_authority",
                "finish_authority", "chamber_count"))]
        covered = {ev["field_name"] for ev in matching}
        missing = [key for key in required if key not in covered]
        if "section" in row:
            row["section_facts"] = section_facts(row)
        synthetic = row.get("is_demo") or row.get("data_provenance") == "SEED_SYNTHETIC"
        if resource.table != "profile_systems" and not synthetic:
            parent = rows("SELECT is_demo FROM public.profile_systems WHERE id=%s", [row.get("system_id")])
            synthetic = bool(parent and parent[0]["is_demo"])
        reviewed = bool(row.get("technical_reviewed_at") and not row.get("review_pending"))
        reviewer = None
        if reviewed:
            people = rows("SELECT private.catalog_reviewer_label(%s,%s) AS label",
                          [row["technical_reviewed_by"], org_id])
            reviewer = people[0]["label"] if people else None
        valid_section = row.get("section_facts", {}).get("valid", True)
        verified = reviewed and bool(required) and not missing and valid_section
        state = ("DEMO" if synthetic else "VERIFIED" if verified else "REVIEWED" if reviewed
                 else "UNKNOWN" if row.get("data_provenance") == "LEGACY_UNVERIFIED" else "DECLARED")
        row["authority_provenance"] = {"state": state, "evidence_count": len(current),
            "current_evidence_count": len(matching), "missing_fields": missing,
            "reviewed_at": row.get("technical_reviewed_at"),
            "reviewer": reviewer or ("Revisor técnico del catálogo" if reviewed else None),
            "reason": ("Datos sintéticos; sin certificación del fabricante" if synthetic else
                       "Revisión técnica con evidencia vigente" if verified else
                       "La revisión técnica no certifica valores sin evidencia vigente" if reviewed else
                       "Fuente o revisión técnica pendiente")}
