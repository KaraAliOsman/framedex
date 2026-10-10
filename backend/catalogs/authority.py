"""Shared current-catalog review predicate; the seal retains its decision."""

from pricing.repository import rows
from dekopen_engine.catalog_authority import fabrication_authority_gate, process_authority_gate


def manufacturing_review_gate(system_id, org_id, *, consumed=None):
    """Global authority stays platform-managed; tenant claims need review.

    ``consumed=None`` assesses full coverage. A position passes the exact SKUs
    it consumes; unrelated articles cannot retroactively invalidate a quote.
    """
    values = []
    for table, key, name in (
        ("profile_systems", "id", "name"), ("profile_articles", "system_id", "name"),
        ("infill_articles", "system_id", "name"), ("hardware_kits", "system_id", "name"),
        ("glazing_bead_matrix", "system_id", "'Regla de junquillo'::text"),
    ):
        found = rows(f"SELECT id,{name} AS label" +
            (",sku" if table in ("profile_articles", "infill_articles", "hardware_kits") else "") +
            f" FROM public.{table} WHERE {key}=%s AND org_id=%s "
            "AND (data_provenance='LEGACY_UNVERIFIED' OR review_pending)", [system_id, org_id])
        for row in found:
            if consumed is not None and row.get("sku") and row["sku"] not in consumed:
                continue
            values.append({"table": table, "id": str(row["id"]), "label": str(row["label"])})
    return {"state": "BLOCK" if values else "PASS", "ok": not values, "pending": values}


def catalog_authority_gate(*, system_id, org_id, params, process_facts,
                           profile_skus=None, hardware_skus=None, panel_skus=None):
    """The catalog and emission share this predicate, with explicit scopes.

    A sealed decision is self-contained: release uses it and the sealed process
    without querying this module or any mutable catalog row.
    """
    consumed = None if profile_skus is None else profile_skus | (hardware_skus or set()) | (panel_skus or set())
    review = manufacturing_review_gate(system_id, org_id, consumed=consumed)
    fabrication = fabrication_authority_gate(params, profile_skus=profile_skus, hardware_skus=hardware_skus)
    process = process_authority_gate(process_facts)
    return {"scope": "CATALOG_COVERAGE" if consumed is None else "CONSUMED_POSITION",
        "review": review, "fabrication": fabrication, "process": process,
        "ok": review["ok"] and fabrication["ok"] and process["ok"]}
