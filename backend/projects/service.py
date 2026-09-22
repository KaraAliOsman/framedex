"""Tenant-scoped project inputs; technical outputs belong exclusively to engine."""

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
import re
from uuid import uuid4

from django.db import connection
from psycopg import sql

from authentication.errors import contract_error
from dekopen_engine.documentary_canonical import documentary_canonical_json_v1
from dekopen_engine.models import EngineResult
from dekopen_engine.snapshot import calculation_response, calculation_hash, result_payload
from documents.repository import documentary_backend
from engine_api.adapter import (
    calculate_from_api,
    evaluate_assembly_from_api,
    parse_product_model,
    UnsupportedEngineContract,
)
from engine_api.repository import SystemParamsRepository, SystemNotFound, UnsupportedCatalogContract
from pricing.repository import audit_reason, commercial_backend, json_text, rows
from pricing.service import decoded
from projects.serializers import PositionWriteSerializer
from projects.typology import derive_typology

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


def _pricing_authority(org_id, project_id, revision):
    with commercial_backend():
        values = rows(
            "SELECT id FROM public.pricing_operations WHERE org_id=%s AND project_id=%s "
            "AND state='APPLIED' AND COALESCE(revision_code,'REV-A')=%s "
            "AND ((SELECT pricing_reset_at FROM public.projects WHERE id=%s) IS NULL "
            "OR approved_at > (SELECT pricing_reset_at FROM public.projects WHERE id=%s)) "
            "ORDER BY approved_at DESC,id DESC LIMIT 1",
            [org_id, project_id, revision, project_id, project_id],
        )
    return values[0] if values else None


def _priced(org_id, project_id, revision):
    return _pricing_authority(org_id, project_id, revision) is not None


def editable(org_id, project_id):
    project = project_row(org_id, project_id, lock=True)
    sealed = rows(
        "SELECT id FROM public.project_versions WHERE org_id=%s AND project_id=%s "
        "AND revision_code=%s",
        [org_id, project_id, project["current_revision"]],
    )
    if project["status"] != "DRAFT" or sealed:
        raise contract_error(409, "revision_required", "Esta revisión está cerrada para edición.")
    if _priced(org_id, project_id, project["current_revision"]):
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


def project_versions(org_id, project_id):
    return rows(
        "SELECT id,revision_code,authority_version,bom_hash,snapshot_sha256,"
        "production_allowed,documentary_complete,emitted_at "
        "FROM public.project_versions WHERE project_id=%s AND org_id=%s "
        "ORDER BY emitted_at,id",
        [project_id, org_id],
    )


def project_public(org_id, row, *, detail=False):
    authority = _pricing_authority(org_id, row["id"], row["current_revision"])
    value = {
        **row,
        "pricing_current": authority is not None,
        "current_pricing_operation_id": authority["id"] if authority else None,
    }
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
        value["versions"] = project_versions(org_id, row["id"])
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
    if not values:
        return project_public(org_id, current, detail=True)
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
        repository = SystemParamsRepository()
        params = repository.load_visible(design["system_id"], org_id)
        tree = design["parametric_tree"]
        if isinstance(tree, dict) and tree.get("version") == "product-v2":
            model = parse_product_model(tree)
            evaluation = evaluate_assembly_from_api(
                product=model,
                color=design["color"],
                params=params,
                coupler_articles=repository.load_coupler_articles(
                    design["system_id"], org_id
                ),
            )
            if evaluation.status.value != "VALID" or evaluation.bom is None:
                # Persisted positions are production-bound: a partial BOM must
                # never be stored or read back as authoritative.
                raise contract_error(
                    400,
                    "manufacturing_incomplete",
                    "El conjunto está incompleto: asigna acopladores y revisa cada módulo antes de guardar.",
                )
            design["nominal_width_mm"] = sum(
                (module.width_mm for module in model.assembly.modules),
                Decimal("0"),
            )
            design["nominal_height_mm"] = max(
                module.height_mm for module in model.assembly.modules
            )
            result = evaluation.bom
        else:
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
    try:
        return derive_typology(tree)
    except ValueError as error:
        raise contract_error(
            422,
            "typology_derivation_failed",
            "La apertura o división no permite determinar la tipología comercial.",
        ) from error


def save_position(org_id, project_id, data, *, position_id=None):
    editable(org_id, project_id)
    current = None
    if position_id:
        current = position_row(org_id, position_id, lock=True)
        if current["project_id"] != project_id:
            missing()
        unchanged(current, data["expected_updated_at"])
    design = data["design"]
    with connection.cursor() as cursor:
        cursor.execute("SELECT private.reserve_catalog_authority(%s,%s)",
                       [design["system_id"], org_id])
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


def _same_documentary_value(left, right):
    return documentary_canonical_json_v1(left) == documentary_canonical_json_v1(right)


def next_revision_code(value):
    match = re.fullmatch(r"REV-([A-Z]+)", value)
    if match is None:
        raise contract_error(409, "revision_sequence_invalid", "La secuencia de revisiones no es válida.")
    number = 0
    for character in match.group(1):
        number = number * 26 + ord(character) - ord("A") + 1
    number += 1
    suffix = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        suffix = chr(ord("A") + remainder) + suffix
    return f"REV-{suffix}"


def _latest_version(org_id, project_id):
    with documentary_backend():
        values = rows(
            "SELECT id,revision_code,authority_version,snapshot_json::text AS snapshot_json,"
            "bom_hash,snapshot_sha256,emitted_at FROM public.project_versions "
            "WHERE project_id=%s AND org_id=%s ORDER BY emitted_at DESC,id DESC LIMIT 1",
            [project_id, org_id],
        )
    return values[0] if values else None


def _assert_live_matches_version(org_id, project_id, version):
    snapshot = decoded(version["snapshot_json"])
    if not isinstance(snapshot, dict):
        raise contract_error(409, "revision_source_drift", "La revisión emitida no coincide con el proyecto.")
    with commercial_backend():
        live_project = rows(
            "SELECT * FROM public.projects WHERE id=%s AND org_id=%s",
            [project_id, org_id],
        )[0]
        live_positions = rows(
            "SELECT * FROM public.project_positions WHERE project_id=%s AND org_id=%s "
            "ORDER BY position_index",
            [project_id, org_id],
        )
    frozen_project = snapshot.get("project")
    frozen_positions = snapshot.get("positions")
    frozen_bom = snapshot.get("bom")
    pricing = snapshot.get("pricing")
    if not all(
        isinstance(value, (dict, list))
        for value in (frozen_project, frozen_positions, frozen_bom, pricing)
    ):
        raise contract_error(409, "revision_source_drift", "La revisión emitida no coincide con el proyecto.")
    project_fields = (
        "code",
        "name",
        "client_name",
        "client_rut",
        "client_email",
        "client_phone",
        "delivery_address",
        "notes_commercial",
        "total_price_net",
        "total_price_tax",
        "total_price_gross",
    )
    if not _same_documentary_value(
        {key: live_project[key] for key in project_fields},
        {key: frozen_project.get(key) for key in project_fields},
    ):
        raise contract_error(409, "revision_source_drift", "La revisión emitida no coincide con el proyecto.")
    frozen_by_id = {
        str(item.get("id")): item for item in frozen_positions if isinstance(item, dict)
    }
    bom_by_id = {
        str(item.get("position_id")): item.get("engine_result")
        for item in frozen_bom
        if isinstance(item, dict)
    }
    pricing_snapshot = pricing.get("input_snapshot")
    pricing_result = pricing.get("result")
    pricing_request = pricing.get("request")
    if not all(isinstance(value, dict) for value in (pricing_snapshot, pricing_result, pricing_request)):
        raise contract_error(409, "revision_source_drift", "La revisión emitida no coincide con el proyecto.")
    try:
        costs = {
            int(index): Decimal(str(amount)) for index, amount in pricing_snapshot["cost_lines"]
        }
        prices = {int(index): Decimal(str(amount)) for index, amount in pricing_result["lines"]}
        discount = Decimal(str(pricing_request["discount_pct"]))
    except (KeyError, TypeError, ValueError) as error:
        raise contract_error(
            409, "revision_source_drift", "La revisión emitida no coincide con el proyecto."
        ) from error
    indexes = {int(item["position_index"]) for item in live_positions}
    if (
        set(frozen_by_id) != {str(item["id"]) for item in live_positions}
        or set(costs) != indexes
        or set(prices) != indexes
    ):
        raise contract_error(409, "revision_source_drift", "La revisión emitida no coincide con el proyecto.")
    for position in live_positions:
        identity = str(position["id"])
        frozen = frozen_by_id[identity]
        live_input = {
            "id": identity,
            "position_index": position["position_index"],
            "quantity": position["quantity"],
            "typology": position["typology"],
            "system_id": position["system_id"],
            "width_mm": position["width_mm"],
            "height_mm": position["height_mm"],
            "color_interior": position["color_interior"],
            "color_exterior": position["color_exterior"],
            "location_tag": position["location_tag"] or "",
            "parametric_tree": decoded(position["parametric_tree"]),
        }
        frozen_input = {key: frozen.get(key) for key in live_input}
        stored_bom = decoded(position["bom_snapshot"])
        if isinstance(stored_bom, dict):
            stored_bom = {key: value for key, value in stored_bom.items() if key != "calculation_hash"}
        index = int(position["position_index"])
        if (
            not _same_documentary_value(live_input, frozen_input)
            or not _same_documentary_value(stored_bom, bom_by_id.get(identity))
            or Decimal(str(position["cost_net"]))
            != costs[index].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            or Decimal(str(position["price_net"]))
            != prices[index].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            or Decimal(str(position["discount_pct"])) != discount
        ):
            raise contract_error(
                409, "revision_source_drift", "La revisión emitida no coincide con el proyecto."
            )
    if Decimal(str(live_project["total_cost_net"])) != Decimal(
        str(pricing.get("applied_total_cost_net"))
    ):
        raise contract_error(409, "revision_source_drift", "La revisión emitida no coincide con el proyecto.")


def clone_project(org_id, actor_id, project_id, data):
    source = project_row(org_id, project_id, lock=True)
    unchanged(source, data["expected_updated_at"])
    latest = _latest_version(org_id, project_id)
    if source["status"] == "QUOTED":
        if latest is None or latest["revision_code"] != source["current_revision"]:
            raise contract_error(409, "revision_source_drift", "La revisión emitida no coincide con el proyecto.")
        _assert_live_matches_version(org_id, project_id, latest)
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


def clone_draft(org_id, actor_id, project_id, data):
    return clone_project(org_id, actor_id, project_id, data)


def reset_draft_pricing(org_id, project_id, expected_operation_id, reason):
    project = project_row(org_id, project_id, lock=True)
    if project["status"] != "DRAFT" or rows(
        "SELECT id FROM public.project_versions WHERE project_id=%s AND org_id=%s AND revision_code=%s",
        [project_id, org_id, project["current_revision"]],
    ):
        raise contract_error(409, "revision_required", "Esta revisión ya fue emitida.")
    current = _pricing_authority(org_id, project_id, project["current_revision"])
    if current is None or str(current["id"]) != str(expected_operation_id):
        raise contract_error(409, "stale_pricing_operation", "Recarga los precios del proyecto.")
    if not reason.strip():
        raise contract_error(400, "audit_reason_required", "Indica el motivo para revisar precios.")
    audit_reason(reason)
    with commercial_backend():
        rows("UPDATE public.project_positions SET cost_net=0,price_net=0,discount_pct=0,"
             "updated_at=clock_timestamp() WHERE project_id=%s AND org_id=%s RETURNING id",
             [project_id, org_id])
        rows("UPDATE public.projects SET pricing_reset_at=clock_timestamp(),total_cost_net=0,"
             "total_price_net=0,total_price_tax=0,total_price_gross=0,updated_at=clock_timestamp() "
             "WHERE id=%s AND org_id=%s RETURNING id", [project_id, org_id])
    return project_public(org_id, project_row(org_id, project_id), detail=True)


def start_successor(org_id, project_id, expected_current_revision=None):
    project = project_row(org_id, project_id, lock=True)
    latest = _latest_version(org_id, project_id)
    if latest is None:
        raise contract_error(409, "successor_requires_emission", "Emite la cotización antes de revisarla.")
    expected = expected_current_revision or latest["revision_code"]
    successor = next_revision_code(expected)
    if project["status"] == "DRAFT" and project["current_revision"] == successor and latest["revision_code"] == expected:
        return {
            **project_public(org_id, project_row(org_id, project_id), detail=True),
            "successor_created": False,
        }
    if project["status"] != "QUOTED" or project["current_revision"] != expected:
        raise contract_error(409, "successor_source_stale", "La revisión actual del proyecto no coincide con la esperada.")
    if latest["revision_code"] != project["current_revision"]:
        raise contract_error(409, "revision_source_drift", "La revisión emitida no coincide con el proyecto.")
    _assert_live_matches_version(org_id, project_id, latest)
    if project_versions(org_id, project_id)[-1]["revision_code"] != latest["revision_code"]:
        raise contract_error(409, "revision_sequence_invalid", "La secuencia de revisiones no es válida.")
    audit_reason(f"Open {successor}; invalidate {latest['revision_code']} live commercial authority")
    with commercial_backend():
        updated_positions = rows(
            "UPDATE public.project_positions SET cost_net=0.00,price_net=0.00,discount_pct=0.0000,"
            "updated_at=clock_timestamp() WHERE project_id=%s AND org_id=%s RETURNING id",
            [project_id, org_id],
        )
        updated_projects = rows(
            "UPDATE public.projects SET status='DRAFT',current_revision=%s,total_cost_net=0.00,"
            "total_price_net=0.00,total_price_tax=0.00,total_price_gross=0.00,"
            "updated_at=clock_timestamp() WHERE id=%s AND org_id=%s RETURNING id",
            [successor, project_id, org_id],
        )
    if not updated_positions or len(updated_projects) != 1:
        raise contract_error(403, "successor_permission_denied", "Tu rol no permite crear revisiones.")
    return {
        **project_public(org_id, project_row(org_id, project_id), detail=True),
        "successor_created": True,
    }
