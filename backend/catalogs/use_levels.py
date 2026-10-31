"""Use permissions from actual catalog cells, independent of workshop setup.

Quotation accepts suggested values. Physical output needs confirmation and a
verification bound to the current technical fingerprint. Issued revisions
retain this decision; release must never re-evaluate the mutable catalog.
"""

from decimal import Decimal
import hashlib
import json

from authentication.errors import contract_error
from authentication.rls import authenticated_read, catalog_backend
from dekopen_engine.models import MaterialType, ProfileRole
from catalogs.evidence import list_evidence
from catalogs.value_origins import RULE_FIELDS, cells, latest_versions, resolve_origin, index_versions, index_evidence
from engine_api.repository import SystemNotFound, SystemParamsRepository, UnsupportedCatalogContract
from pricing.repository import json_text, rows

LEVELS = ("DRAWABLE", "QUOTABLE", "MANUFACTURABLE", "MACHINE_READY")
RESOURCES = {"profile_systems": "systems", "profile_articles": "articles",
    "glazing_bead_matrix": "glazing", "hardware_kits": "hardware-kits"}


def _catalog(org_id, system_id):
    with catalog_backend():
        found = rows("SELECT to_jsonb(s)::text AS data FROM public.profile_systems s "
            "WHERE id=%s AND (org_id=%s OR (org_id IS NULL AND is_global))", [system_id, org_id])
        if not found:
            raise SystemNotFound(system_id)
        system = json.loads(found[0]["data"], parse_float=Decimal)
        grouped = {"profile_systems": [system]}
        for table in ("profile_articles", "glazing_bead_matrix", "hardware_kits"):
            active = " AND t.is_active" if table != "profile_articles" else ""
            found = rows(f"SELECT to_jsonb(t)::text AS data FROM public.{table} t "
                "WHERE t.system_id=%s AND (t.org_id=%s OR (t.org_id IS NULL AND %s))" + active + " ORDER BY t.id",
                [system_id, org_id, system["is_global"]])
            grouped[table] = [json.loads(item["data"], parse_float=Decimal) for item in found]
        setup = rows("SELECT verified_at,verified_by,verified_hash FROM public.catalog_series_setup "
            "WHERE system_id=%s AND org_id=%s", [system_id, org_id])
    return system, grouped, setup[0] if setup else {}


def _fingerprint(grouped):
    identity = {"id", "sku", "role", "material", "section", "section_revision", "is_active", "system_family"}
    payload = {table: [{key: value for key, value in row.items() if key in RULE_FIELDS | identity}
        for row in records] for table, records in grouped.items()}
    return "sha256:" + hashlib.sha256(json_text(payload).encode("utf-8")).hexdigest()


def technical_fingerprint(org_id, system_id):
    """P03 records this only after a human verifies the engine's test window."""
    _, grouped, _ = _catalog(org_id, system_id)
    return _fingerprint(grouped)


def _pending(field, rule, action, required_for, *, origin=None, resource="systems", row_id=None):
    return {"field": field, "rule": rule, "origin": origin, "action": action,
        "required_for": list(required_for), "resource": resource, "row_id": str(row_id) if row_id else None}


def series_use(org_id, system_id, *, params=None, result=None, priced=False, effective_date=None, demo_prices=None):
    """Full-series coverage or an exact engine-resolved position.

    ``priced`` is internal evidence from position_cost after every consumed
    cost resolved. It never stands in for missing catalog prices in discovery.
    Unused colors/articles cannot block a successfully priced position.
    """
    system, grouped, setup = _catalog(org_id, system_id)
    pending = []
    profiles = grouped["profile_articles"]
    drawn = [item for item in profiles if result is None or item["sku"] in {cut.sku for cut in result.profile_cuts}]
    drawable = bool(system["is_active"] and drawn
        and all(item.get("role") and item.get("face_width_mm") is not None for item in drawn))
    if not drawable:
        pending.append(_pending("face_width_mm", "profiles", "Completa los roles y anchos visibles de los perfiles.", LEVELS, row_id=system_id))
    technical = True
    try:
        params = params or SystemParamsRepository().load_visible(system_id, org_id)
        if result is None and (not params.glazing_bead_rules or params.rebate_depth_mm is None
                or params.end_milling_overlap_mm is None):
            technical = False
    except (SystemNotFound, UnsupportedCatalogContract, ValueError):
        technical = False
    if not technical:
        pending.append(_pending("rules", "calculation_rules", "Completa las reglas de cálculo y el junquillo por espesor.", LEVELS[1:], row_id=system_id))
    if params is not None and result is None:
        unwelded = {ProfileRole.GLAZING_BEAD, ProfileRole.RAIL, ProfileRole.THRESHOLD, ProfileRole.CHANNEL,
            ProfileRole.SILL, ProfileRole.FRAME_EXTENSION, ProfileRole.COVER_TRIM, ProfileRole.ADDITIONAL}
        for role, article in params.effective_profile_articles.items():
            row = next((item for item in profiles if item["sku"] == article.sku), None)
            if row is None:
                continue
            missing = []
            if params.uses_legacy_rules:
                if params.material is MaterialType.PVC and role not in unwelded:
                    missing = [field for field in ("welding_loss_mm", "reinforcement_gap_mm") if getattr(article, field) is None]
            else:
                if article.cut_rule is None:
                    missing.append("cut_rule")
                if params.material is MaterialType.PVC and role not in unwelded and article.reinforcement_rule is None:
                    missing.append("reinforcement_rule")
            pending.extend(_pending(field, "calculation_rules", "Completa esta regla de cálculo.", LEVELS[1:],
                resource="articles", row_id=row["id"]) for field in missing)

    synthetic = bool(system["is_demo"] and system["is_global"] and system["org_id"] is None)
    with catalog_backend():
        versions = index_versions(latest_versions(org_id, system_id))
    with authenticated_read():
        evidence = index_evidence(list_evidence(org_id=org_id, system_id=system_id))
    suggested_count = 0
    for table, records in grouped.items():
        for row in records:
            for field, value in cells(row):
                origin = resolve_origin(table, row, field, value, versions, evidence)["origin"]
                if origin == "SUGGESTED":
                    suggested_count += 1
                if not synthetic and origin in (None, "SUGGESTED"):
                    pending.append(_pending(field, "confirm_suggested" if origin else "confirm_value",
                        "Confirma este valor antes de fabricar.", LEVELS[2:], origin=origin,
                        resource=RESOURCES[table], row_id=row["id"]))

    fingerprint = _fingerprint(grouped)
    verified = bool(setup.get("verified_at") and setup.get("verified_by") and setup.get("verified_hash") == fingerprint)
    if not verified and not synthetic:
        pending.append(_pending("verified_at", "test_window", "Verifica la serie con una ventana de prueba.", LEVELS[2:], row_id=system_id))

    if not (priced and result is not None):
        from pricing.coverage import catalog_coverage
        # Coverage returns presence/ambiguity only; no confidential costs leave
        # this projection. Technical mappings use the member's existing grants.
        with authenticated_read():
            coverage = catalog_coverage(org_id, system_id=system_id, effective_date=effective_date,
                demo_prices=demo_prices)
        if not coverage:
            pending.append(_pending("prices", "prices", "Añade los precios del taller.", ["QUOTABLE"], row_id=system_id))
        for item in coverage:
            if not item["active_cost_items"]:
                pending.append(_pending("prices", item["sku"], item["blocker"], ["QUOTABLE"], row_id=system_id))

    # CNC is an additional physical capability; station scheduling and machine
    # configuration retain their existing, more specific production checks.
    from production.service import _resolve_process_profile
    process, via = _resolve_process_profile(org_id, {}, system)
    mapping = (process or {}).get("operation_station_map")
    stations = (process or {}).get("stations") or []
    codes = {item["code"] for item in stations}
    required_ops = {"SAW_CUT"}
    if any(item["role"] in ("MULLION_V", "MULLION_H") for item in profiles):
        required_ops.add("END_MACHINING")
    if rows("SELECT 1 FROM public.handle_requirement_policies WHERE system_id=%s "
            "AND (org_id IS NULL OR org_id=%s) LIMIT 1", [system_id, org_id]):
        required_ops.add("HANDLE_PREP")
    if via in (None, "generic_fallback") or not mapping or any(mapping.get(op) not in codes for op in required_ops):
        pending.append(_pending("process_profile_id", "cnc_operations", "Completa el mapa de operaciones para máquina.", ["MACHINE_READY"], row_id=system_id))
    capabilities = [{"level": level, "ok": not any(level in item["required_for"] for item in pending),
        "pending": [item for item in pending if level in item["required_for"]]} for level in LEVELS]
    return {"level": next((item["level"] for item in reversed(capabilities) if item["ok"]), None),
        "levels": capabilities, "pending": pending, "suggested_count": suggested_count,
        "verified": verified, "is_example": synthetic,
        "scope": "PRICED_POSITION" if priced and result is not None else "SERIES"}


def require_use(org_id, system_id, level, **kwargs):
    if level not in LEVELS:
        raise ValueError("Unknown catalog use level")
    usage = series_use(org_id, system_id, **kwargs)
    selected = next(item for item in usage["levels"] if item["level"] == level)
    if not selected["ok"]:
        label = {"DRAWABLE": "dibujar", "QUOTABLE": "cotizar", "MANUFACTURABLE": "fabricar", "MACHINE_READY": "máquina"}[level]
        raise contract_error(422, "catalog_use_incomplete", f"Completa la serie antes de {label}.",
            extra={"required_level": level, "pending": selected["pending"]})
    return usage
