"""Per-cell origins and append-only history on the existing catalog values."""

from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import json

from django.db import connection

from authentication.errors import contract_error
from authentication.rls import catalog_backend, tx_aborted
from catalogs.provenance import _equivalent, evidence_matches
from pricing.repository import json_text, rows

TABLES = {"profile_systems": "SYSTEM", "profile_articles": "PROFILE",
    "glazing_bead_matrix": "GLAZING", "hardware_kits": "HARDWARE"}
# Same root fields as private.catalog_rule_cells. Objects are individual cells;
# an ordered rule table remains one value until the table is explicitly edited.
RULE_FIELDS = frozenset("""depth_mm chamber_count sash_overlap_mm glass_clearance_white_mm
    glass_clearance_foil_mm pulley_height_mm central_overlap_mm sliding_lateral_clearance_mm
    sliding_end_add_mm corner_bracket_loss_mm hook_depth_mm door_threshold_mm
    door_bottom_clearance_mm door_leaf_side_clearance_mm rail_type rail_count rebate_depth_mm
    end_milling_overlap_mm sliding_glazing_deduction_width_mm sliding_glazing_deduction_height_mm
    sliding_parameters dimensional_limits opening_capabilities paired_leaf_rule finish_authority
    finishes face_width_mm commercial_length_mm welding_loss_mm reinforcement_gap_mm weight_kg_m
    steel_weight_kg_m reinforcement_sku cut_rule reinforcement_rule coupling_rule glass_thickness_mm
    bead_article_id bead_width_mm gasket_interior_mm gasket_exterior_mm cut_add_mm opening_type
    min_leaf_width_mm max_leaf_width_mm min_leaf_height_mm max_leaf_height_mm max_leaf_weight_kg
    weight_kg carriages_qty carriage_capacity_kg stay_arms_qty contents class_authority""".split())


def cells(values, prefix=""):
    for key, value in values.items():
        if (not prefix and key not in RULE_FIELDS) or key == "source" or value is None:
            continue
        field = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            yield from cells(value, field)
        else:
            yield field, value


def _stored_value(version, *, previous=False):
    numeric = version.get("previous_numeric" if previous else "value_numeric")
    if numeric is not None:
        return numeric
    value = version.get("previous_json" if previous else "value_json")
    # psycopg decodes JSONB; SELECTs here request text to preserve exact decimals.
    return json.loads(value, parse_float=Decimal) if isinstance(value, str) else value


def latest_versions(org_id, system_id):
    return rows("SELECT DISTINCT ON (authority_table,row_id,field_name) *,"
        "value_json::text AS value_json,previous_json::text AS previous_json "
        "FROM public.catalog_value_history WHERE org_id=%s AND system_id=%s "
        "ORDER BY authority_table,row_id,field_name,version DESC", [org_id, system_id])


def cell_history(org_id, system_id, table, row_id, field_name):
    history = rows("SELECT *,value_json::text AS value_json,previous_json::text AS previous_json "
        "FROM public.catalog_value_history WHERE org_id=%s AND system_id=%s AND authority_table=%s "
        "AND row_id=%s AND field_name=%s ORDER BY version DESC",
        [org_id, system_id, table, row_id, field_name])
    return [{**item, "value": _stored_value(item), "previous_value": _stored_value(item, previous=True)}
        for item in history]


def index_versions(versions):
    return {(item["authority_table"], str(item["row_id"]), item["field_name"]): item for item in versions}


def index_evidence(evidence):
    grouped = {}
    for item in evidence:
        grouped.setdefault((item["authority_table"], str(item["row_id"])), []).append(item)
    return grouped


def resolve_origin(table, row, field_name, value, versions, evidence=()):
    current = (versions.get((table, str(row["id"]), field_name)) if isinstance(versions, dict) else
        next((item for item in versions if item["authority_table"] == table
        and str(item["row_id"]) == str(row["id"]) and item["field_name"] == field_name), None))
    if current is not None and _equivalent(value, _stored_value(current)):
        return {"origin": current["origin"], "source_ref": current["source_ref"],
            "set_by": current["set_by"], "set_at": current["set_at"], "version_id": current["id"]}
    synthetic = row.get("is_demo") or row.get("data_provenance") == "SEED_SYNTHETIC"
    if not synthetic:
        if isinstance(evidence, dict):
            evidence = evidence.get((table, str(row["id"])), ())
        matching = [item for item in evidence if item["authority_table"] == table
            and str(item["row_id"]) == str(row["id"])
            and (field_name == item["field_name"] or field_name.startswith(item["field_name"] + "."))
            and item["review_state"] == "REVIEWED" and item.get("extraction_method") != "HUMAN_CORRECTION"
            and (item.get("source_ref") or item.get("source_page") or item.get("source_url"))
            and evidence_matches(row, item)]
        if matching:
            item = matching[-1]
            return {"origin": "MANUAL", "source_ref": item.get("source_ref") or item["source_document"],
                "set_by": item["reviewed_by"], "set_at": item["reviewed_at"], "version_id": None}
        if row.get("technical_reviewed_at") and not row.get("review_pending"):
            return {"origin": "WORKSHOP", "source_ref": "Revisión histórica del taller",
                "set_by": row.get("technical_reviewed_by"), "set_at": row["technical_reviewed_at"], "version_id": None}
    return {"origin": None, "source_ref": None, "set_by": None, "set_at": None, "version_id": None}


@contextmanager
def annotated_cells(annotations):
    """Stamp only this write; a pooled connection never keeps a template origin."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_setting('app.catalog_value_origins',true)")
        previous = cursor.fetchone()[0]
        cursor.execute("SELECT set_config('app.catalog_value_origins',%s,true)", [json_text(annotations)])
    try:
        yield
    finally:
        if not tx_aborted():
            with connection.cursor() as cursor:
                cursor.execute("SELECT set_config('app.catalog_value_origins',%s,true)", [previous or ""])


def record_origin(*, org_id, system_id, table, row, field_name, origin, source_ref, actor_id, evidence_id=None):
    if table not in TABLES or origin not in {"MANUAL", "WORKSHOP", "SUGGESTED"}:
        raise contract_error(400, "catalog_value_invalid", "El origen del valor no es válido.")
    values = dict(cells(row))
    if field_name not in values:
        raise contract_error(400, "catalog_cell_missing", "Completa este valor antes de confirmarlo.")
    value = values[field_name]
    numeric = None
    if not isinstance(value, (bool, dict, list, tuple)):
        try:
            numeric = Decimal(str(value))
            if not numeric.is_finite():
                raise ValueError("Nonfinite catalog value")
        except InvalidOperation:
            pass
    with catalog_backend():
        result = rows("INSERT INTO public.catalog_value_history(org_id,system_id,authority_table,row_id,field_name,"
            "value_numeric,value_json,origin,source_ref,evidence_id,set_by,version) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,1) RETURNING id,version",
            [org_id, system_id, table, row["id"], field_name, numeric,
                None if numeric is not None else json_text(value), origin, source_ref, evidence_id, actor_id])
    return result[0]


def engine_origins(org_id, system_id):
    """Project matching current versions; never resurrect a removed/stale value."""
    from dekopen_engine.models import CatalogValueOrigin
    versions = latest_versions(org_id, system_id)
    found = {}
    for table in TABLES:
        ids = list({str(item["row_id"]) for item in versions if item["authority_table"] == table})
        if not ids:
            continue
        for item in rows(f"SELECT to_jsonb(t)::text AS data FROM public.{table} t WHERE id=ANY(%s::uuid[]) AND org_id=%s", [ids, org_id]):
            row = json.loads(item["data"], parse_float=Decimal)
            found[(table, str(row["id"]))] = row
    result = []
    for version in versions:
        table = version["authority_table"]
        row = found.get((table, str(version["row_id"])))
        if row is None:
            continue
        current = dict(cells(row)).get(version["field_name"])
        if current is None or not _equivalent(current, _stored_value(version)):
            continue
        key = (str(Decimal(str(row["glass_thickness_mm"])).normalize()) if table == "glazing_bead_matrix"
            else row.get("sku", ""))
        field = "bead_profile_id" if version["field_name"] == "bead_article_id" else version["field_name"]
        value = str(current) if isinstance(current, (str, Decimal, int)) and not isinstance(current, bool) else json_text(current)
        result.append(CatalogValueOrigin(scope=TABLES[table], key=key,
            rule=field, value=value, origin=version["origin"]))
    return tuple(result)
