"""Tenant-scoped project inputs; technical outputs belong exclusively to engine."""

from uuid import uuid4
from copy import deepcopy

from django.db import connection
from psycopg import sql

from authentication.errors import contract_error
from dekopen_engine.models import EngineResult
from dekopen_engine.snapshot import calculation_response, calculation_hash, result_payload
from engine_api.adapter import calculate_from_api, UnsupportedEngineContract
from engine_api.repository import SystemParamsRepository, SystemNotFound, UnsupportedCatalogContract
from pricing.repository import commercial_backend, json_text, rows
from pricing.service import decoded
from projects.serializers import PositionWriteSerializer

METADATA = (
    "name",
    "client_name",
    "client_rut",
    "client_email",
    "client_phone",
    "delivery_address",
    "notes_commercial",
    "notes_internal",
)
PROJECT_COLUMNS = (
    "id",
    "code",
    *METADATA,
    "status",
    "current_revision",
    "total_price_net",
    "total_price_tax",
    "total_price_gross",
    "updated_at",
)
POSITION_COLUMNS = (
    "id",
    "project_id",
    "position_index",
    "location_tag",
    "quantity",
    "typology",
    "system_id",
    "width_mm",
    "height_mm",
    "color_interior",
    "color_exterior",
    "parametric_tree",
    "bom_snapshot",
    "updated_at",
)


def missing():
    raise contract_error(404, "project_not_found", "El proyecto o vano no está disponible.")


def project_row(org_id, project_id, *, lock=False):
    values = rows(
        f"SELECT {','.join(PROJECT_COLUMNS)} FROM public.projects "
        "WHERE id=%s AND org_id=%s" + (" FOR UPDATE" if lock else ""),
        [project_id, org_id],
    )
    if not values:
        missing()
    return values[0]


def _priced(org_id, project_id):
    with commercial_backend():
        return bool(
            rows(
                "SELECT id FROM public.pricing_operations WHERE org_id=%s "
                "AND project_id=%s AND state='APPLIED' LIMIT 1",
                [org_id, project_id],
            )
        )


def editable(org_id, project_id):
    project = project_row(org_id, project_id, lock=True)
    if project["status"] != "DRAFT" or rows(
        "SELECT id FROM public.project_versions WHERE org_id=%s AND project_id=%s",
        [org_id, project_id],
    ):
        raise contract_error(409, "revision_required", "Esta revisión está cerrada para edición.")
    if _priced(org_id, project_id):
        raise contract_error(
            409,
            "commercial_revision_required",
            "El proyecto tiene precios aplicados y requiere una revisión.",
        )
    return project


def unchanged(row, expected):
    if row["updated_at"] != expected:
        raise contract_error(
            409, "stale_edit", "Otra persona guardó cambios. Recarga antes de reemplazarlos."
        )


def position_public(row):
    design = {
        "system_id": row["system_id"],
        "nominal_width_mm": str(row["width_mm"]),
        "nominal_height_mm": str(row["height_mm"]),
        "color": row["color_interior"],
        "parametric_tree": decoded(row["parametric_tree"]),
    }
    stored = decoded(row["bom_snapshot"])
    try:
        payload = {key: value for key, value in stored.items() if key != "calculation_hash"}
        result = EngineResult.model_validate_json(json_text(payload))
        safe = result_payload(result)
        expected = calculation_hash({**design, "system_id": str(design["system_id"])}, safe)
        # SHOT-08 stored EngineResult before calculation_hash was part of this
        # persistence boundary. Preserve that exact result; do not recalculate.
        if "calculation_hash" in stored and stored["calculation_hash"] != expected:
            raise ValueError("Stored calculation identity mismatch")
    except (KeyError, TypeError, ValueError) as error:
        raise contract_error(
            409,
            "stored_calculation_invalid",
            "El cálculo guardado requiere revisión antes de continuar.",
        ) from error
    return {
        **{
            key: row[key]
            for key in (
                "id",
                "project_id",
                "position_index",
                "location_tag",
                "quantity",
                "typology",
                "updated_at",
            )
        },
        "design": design,
        "bom": {**safe, "calculation_hash": expected},
    }


def positions(org_id, project_id):
    return [
        position_public(row)
        for row in rows(
            f"SELECT {','.join(POSITION_COLUMNS)} FROM public.project_positions "
            "WHERE org_id=%s AND project_id=%s ORDER BY position_index",
            [org_id, project_id],
        )
    ]


def project_public(org_id, row, *, detail=False):
    value = {**row, "pricing_current": _priced(org_id, row["id"])}
    for key in METADATA:
        value[key] = value[key] or ""
    for key in ("total_price_net", "total_price_tax", "total_price_gross"):
        value[key] = str(value[key])
    value["position_count"] = rows(
        "SELECT count(id) AS count FROM public.project_positions WHERE project_id=%s AND org_id=%s",
        [row["id"], org_id],
    )[0]["count"]
    if detail:
        value["positions"] = positions(org_id, row["id"])
    return value


def list_projects(org_id):
    return [
        project_public(org_id, row)
        for row in rows(
            f"SELECT {','.join(PROJECT_COLUMNS)} FROM public.projects "
            "WHERE org_id=%s ORDER BY updated_at DESC,id",
            [org_id],
        )
    ]


def create_project(org_id, actor_id, data):
    identity = uuid4()
    # The code is an opaque human-readable reference, never an internal DB ID input.
    code = f"P-{identity.hex[:12].upper()}"
    values = {key: data.get(key, "") for key in METADATA}
    rows(
        "INSERT INTO public.projects(id,org_id,code,created_by," + ",".join(METADATA) + ") "
        "VALUES(" + ",".join(["%s"] * (4 + len(METADATA))) + ") RETURNING id",
        [identity, org_id, code, actor_id, *values.values()],
    )
    return project_public(org_id, project_row(org_id, identity), detail=True)


def update_project(org_id, project_id, data):
    current = editable(org_id, project_id)
    unchanged(current, data["expected_updated_at"])
    values = {key: data[key] for key in METADATA if key in data}
    query = sql.SQL(
        "UPDATE public.projects SET {},updated_at=clock_timestamp() "
        "WHERE id=%s AND org_id=%s RETURNING id"
    ).format(
        sql.SQL(",").join(sql.SQL("{}=%s").format(sql.Identifier(key)) for key in values),
    )
    rows(query, [*values.values(), project_id, org_id])
    return project_public(org_id, project_row(org_id, project_id), detail=True)


def position_row(org_id, position_id, *, lock=False):
    result = rows(
        f"SELECT {','.join(POSITION_COLUMNS)} FROM public.project_positions "
        "WHERE id=%s AND org_id=%s" + (" FOR UPDATE" if lock else ""),
        [position_id, org_id],
    )
    if not result:
        missing()
    return result[0]


def calculate_design(org_id, design):
    try:
        params = SystemParamsRepository().load_visible(design["system_id"], org_id)
        result = calculate_from_api(
            params=params,
            **{
                key: design[key]
                for key in (
                    "parametric_tree",
                    "nominal_width_mm",
                    "nominal_height_mm",
                    "color",
                )
            },
        )
    except SystemNotFound as error:
        raise contract_error(
            404, "system_not_found", "La serie no está disponible para este taller."
        ) from error
    except (UnsupportedEngineContract, UnsupportedCatalogContract) as error:
        raise contract_error(
            422,
            "technical_authority_required",
            "Revisa las compatibilidades del catálogo de esta serie.",
        ) from error
    except ValueError as error:
        raise contract_error(
            400,
            "validation_error",
            "El diseño no es válido. Revisa medidas, divisiones y aperturas.",
        ) from error
    return calculation_response({**design, "system_id": str(design["system_id"])}, result)


def _typology(tree):
    if tree.get("type") == "ROOT":
        tree = tree["children"][0]
    opening = tree.get("opening_type")
    if tree.get("children"):
        raise contract_error(
            422,
            "composite_pricing_contract_required",
            "La clasificación comercial de un vano con divisiones requiere definición.",
        )
    return {
        "TURN_LEFT": "TURN",
        "TURN_RIGHT": "TURN",
        "TILT_TURN_LEFT": "TILT_TURN",
        "TILT_TURN_RIGHT": "TILT_TURN",
    }.get(opening, opening)


def save_position(org_id, project_id, data, *, position_id=None):
    editable(org_id, project_id)
    current = None
    if position_id:
        current = position_row(org_id, position_id, lock=True)
        if current["project_id"] != project_id:
            missing()
        unchanged(current, data["expected_updated_at"])
    design = data["design"]
    bom = calculate_design(org_id, design)
    values = [
        data["location_tag"],
        data["quantity"],
        _typology(design["parametric_tree"]),
        design["system_id"],
        design["nominal_width_mm"],
        design["nominal_height_mm"],
        design["color"],
        design["color"],
        json_text(design["parametric_tree"]),
        json_text(bom),
    ]
    if current:
        rows(
            "UPDATE public.project_positions SET location_tag=%s,quantity=%s,typology=%s,"
            "system_id=%s,width_mm=%s,height_mm=%s,color_interior=%s,color_exterior=%s,"
            "parametric_tree=%s::jsonb,bom_snapshot=%s::jsonb,updated_at=clock_timestamp() "
            "WHERE id=%s AND org_id=%s RETURNING id",
            [*values, position_id, org_id],
        )
    else:
        index = rows(
            "SELECT COALESCE(MAX(position_index),0)+1 AS next_index "
            "FROM public.project_positions WHERE project_id=%s AND org_id=%s",
            [project_id, org_id],
        )[0]["next_index"]
        position_id = uuid4()
        rows(
            "INSERT INTO public.project_positions(location_tag,quantity,typology,system_id,"
            "width_mm,height_mm,color_interior,color_exterior,parametric_tree,bom_snapshot,"
            "id,project_id,org_id,position_index) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s) RETURNING id",
            [*values, position_id, project_id, org_id, index],
        )
    rows(
        "UPDATE public.projects SET updated_at=clock_timestamp() WHERE id=%s AND org_id=%s "
        "RETURNING id",
        [project_id, org_id],
    )
    return position_public(position_row(org_id, position_id))


def delete_position(org_id, position_id, expected):
    original = position_row(org_id, position_id)
    editable(org_id, original["project_id"])
    current = position_row(org_id, position_id, lock=True)
    unchanged(current, expected)
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM public.project_positions WHERE id=%s AND org_id=%s", [position_id, org_id]
        )
        cursor.execute(
            "UPDATE public.projects SET updated_at=clock_timestamp() WHERE id=%s AND org_id=%s",
            [original["project_id"], org_id],
        )


def clone_draft(org_id, actor_id, project_id, data):
    """Copy editable inputs into a new draft, under the existing write contract.

    Applied/frozen sources remain closed until successor semantics are approved.
    No prices, audits, orders or historical evidence are copied.
    """
    source = editable(org_id, project_id)
    unchanged(source, data["expected_updated_at"])
    source_positions = positions(org_id, project_id)
    metadata = {key: source[key] or "" for key in METADATA}
    metadata["name"] = data.get("name", "Copia de " + source["name"][:246])
    copied = create_project(org_id, actor_id, metadata)
    for position in source_positions:
        serializer = PositionWriteSerializer(
            data={
                "location_tag": position["location_tag"] or "",
                "quantity": position["quantity"],
                "design": deepcopy(position["design"]),
            }
        )
        serializer.is_valid(raise_exception=True)
        save_position(org_id, copied["id"], serializer.validated_data)
    return project_public(org_id, project_row(org_id, copied["id"]), detail=True)
