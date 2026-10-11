"""Private, revision-bound field visits and transactional offline commands.

The phone records evidence. Only office roles can release replacements, buy
material or accept a motor rectification. A QR is an address, never authority.
"""

from copy import deepcopy
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import base64
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from django.db import connection, transaction
from PIL import Image, UnidentifiedImageError

from authentication.errors import contract_error
from dekopen_engine.documentary_canonical import documentary_sha256_v1
from dekopen_engine.warranty import warranty_deadline
from documents.repository import decoded, documentary_backend, json_text, one, rows
from documents.storage import SupabaseDocumentStorage
from production import service
from projects.clients import validate_rut

READERS = ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER", "INSTALLER")
SUPERVISORS = ("OWNER", "WORKSHOP_MANAGER")
CHECKS = ("installed", "levelled", "sealed", "adjusted", "clean")


@contextmanager
def _role_scope(role):
    from authentication.rls import tx_aborted

    previous = one("SELECT current_setting('role') AS role")["role"]
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('role',%s,true)", [role])
    try:
        yield
    finally:
        if not tx_aborted():
            with connection.cursor() as cursor:
                cursor.execute("SELECT set_config('role',%s,true)", [previous])


def _project_call(function, *args, **kwargs):
    # Project mutations use their existing authenticated grants and tenant RLS.
    # Do not grant their authority-reservation functions to the field role.
    with _role_scope("authenticated"):
        return function(*args, **kwargs)


def reject(detail, code="field_invalid", status=422):
    raise contract_error(status, code, detail)


def public(value):
    # Exact strings, including datetime/Decimal, match the generated client.
    import json

    return json.loads(json_text(value))


def phone(value):
    """Physical projection only; sealed commercial rule authority stays server-side."""
    if isinstance(value, dict):
        return {
            k: phone(v)
            for k, v in value.items()
            if k not in ("cost_rate", "selling_rate", "total_cost", "total_price", "document_preferences")
            and not k.startswith(("cost_", "pricing_", "price_net", "selling_"))
        }
    if isinstance(value, list):
        return [phone(v) for v in value]
    return value


def live_role(org, actor):
    found = rows("SELECT private.field_actor_role(%s,%s) AS role", [org, actor])
    if not found or found[0]["role"] not in READERS:
        reject("Tu acceso a terreno cambió. Vuelve a iniciar sesión.", "field_permission", 403)
    return found[0]["role"]


def visit_row(org, visit_id, actor, *, lock=False):
    role = live_role(org, actor)
    result = one(
        "SELECT * FROM public.field_visits WHERE org_id=%s AND id=%s"
        + (" FOR UPDATE" if lock else ""),
        [org, visit_id],
        "field_visit_not_found",
    )
    if role == "INSTALLER" and str(result["assigned_to"]) != str(actor):
        reject(
            "Esta visita está asignada a otra persona. Pide al encargado tu agenda.",
            "field_permission",
            403,
        )
    result["context_json"] = decoded(result["context_json"])
    return result, role


def _code(org, prefix, visit_id=None):
    return one("SELECT private.field_next_code(%s,%s,%s) AS code", [org, prefix, visit_id])["code"]


def _version(org, version_id):
    return one(
        "SELECT id,project_id,revision_code,snapshot_json,bom_hash,snapshot_sha256 "
        "FROM public.project_versions WHERE org_id=%s AND id=%s",
        [org, version_id],
        "version_not_found",
    )


def _physical(position):
    design = position.get("design")
    if not design:
        design = {
            "system_id": str(position["system_id"]),
            "color": position.get("color_interior") or "WHITE",
            "nominal_width_mm": str(position.get("width_mm") or position.get("nominal_width_mm")),
            "nominal_height_mm": str(
                position.get("height_mm") or position.get("nominal_height_mm")
            ),
            "parametric_tree": position["parametric_tree"],
        }
    # Never carry costs, commercial dossiers or full sealed snapshots to phone.
    engine = position.get("engine_result") or position.get("bom_snapshot") or {}
    return {
        "position_id": str(position.get("position_id") or position.get("id")),
        "position_index": position["position_index"],
        "location_tag": position.get("location_tag") or "Sin ubicación · pedir al encargado",
        "is_demo": bool(position.get("is_demo") or position.get("system_demo")),
        "design": public(design),
        "quantity": position["quantity"],
        "materials": {
            key: engine.get(key) or []
            for key in (
                "profile_cuts",
                "reinforcements",
                "glasses",
                "panels",
                "hardware_items",
                "fittings",
            )
        },
    }


def _context(org, data):
    from projects.service import project_row, positions

    project = project_row(org, data["project_id"])
    version_id = data.get("project_version_id")
    if version_id:
        version = _version(org, version_id)
        if str(version["project_id"]) != str(project["id"]):
            reject("La revisión no pertenece a esta obra.")
        snapshot = decoded(version["snapshot_json"])
        boms = {str(b["position_id"]): b["engine_result"] for b in snapshot.get("bom") or []}
        source = [{**p, "engine_result": boms.get(str(p["id"]), {})} for p in snapshot["positions"]]
        from dekopen_engine.inventory import purchase_source_ledger
        ledger = purchase_source_ledger(snapshot)
        requirements = rows("SELECT id,source_trace FROM public.purchase_requirement_lines WHERE org_id=%s AND project_version_id=%s", [org,version_id])
        revision = version["revision_code"]
        project_authority = snapshot["project"]
        fingerprint = version["snapshot_sha256"]
        organization = {
            k: v
            for k, v in (snapshot.get("organization") or {}).items()
            if k
            in (
                "name",
                "tax_id",
                "commercial_name",
                "giro",
                "brand_schema",
                "brand_address",
                "brand_phone",
                "brand_email",
                "brand_logo_key",
                "brand_logo_sha256",
                "brand_effective_color",
                "brand_primary_color",
                "document_attribution",
                "document_preferences",
            )
        }
    else:
        if data["kind"] != "MEASUREMENT" or project["status"] != "DRAFT":
            reject("Elige una revisión emitida; solo la medición admite un borrador.")
        source = positions(org, project["id"])
        revision = project["current_revision"]
        project_authority = project
        fingerprint = None
        organization = {}
        ledger, requirements = {}, []
    offered = {p["position_id"]: p for p in map(_physical, source)}
    selected = []
    for choice in data["units"]:
        p = offered.get(str(choice["position_id"]))
        if not p or choice["unit_index"] > int(p["quantity"]):
            reject("La unidad no existe en la revisión de esta obra.")
        unit = {
            **deepcopy(p),
            "unit_index": choice["unit_index"],
            "order_id": None,
            "order_code": None,
            "label_code": None,
            "pieces": [],
            "mounting_rules": [],
            "requirement_ids": [str(r["id"]) for r in requirements if any(entry in ledger and ledger[entry][0]==str(choice["position_id"]) for entry in decoded(r["source_trace"]))],
        }
        if choice.get("order_id"):
            order = one(
                "SELECT id,project_id,project_version_id,order_code,status,payload_json "
                "FROM public.orders WHERE org_id=%s AND id=%s AND order_type='WORKSHOP_OT' FOR UPDATE",
                [org, choice["order_id"]],
                "work_order_not_found",
            )
            payload = decoded(order["payload_json"])
            if (
                str(order["project_id"]) != str(project["id"])
                or str(order["project_version_id"]) != str(version_id)
                or str(payload["position_id"]) != str(choice["position_id"])
            ):
                reject("La OT no corresponde a esta posición y revisión.")
            manifest = (payload.get("packing") or {}).get("units") or []
            physical = next((u for u in manifest if u["unit_index"] == choice["unit_index"]), None)
            if not physical:
                reject("Falta el bulto embalado. Completa Embalaje antes de planificar.")
            if data["kind"] == "DELIVERY" and order["status"] not in ("COMPLETED", "DISPATCHED"):
                reject("La OT todavía no está lista para despacho.")
            if data["kind"] in ("INSTALLATION", "SERVICE") and order["status"] not in (
                "DISPATCHED",
                "INSTALLED",
            ):
                reject("Despacha la OT con su guía antes de planificar la instalación.")
            from production.trace import trace_work_order

            trace = trace_work_order(org_id=org, order_id=order["id"], actor_role="INSTALLER")
            unit.update(
                order_id=str(order["id"]),
                order_code=order["order_code"],
                label_code=physical["label_code"],
                qr_value=physical.get("qr_value") or f"DEKOPEN|{order['order_code']}|{physical['label_code']}|{physical['unit_index']}",
                pieces=trace.get("pieces") or [],
            )
        elif data["kind"] != "MEASUREMENT":
            reject("Elige la OT y el bulto que se visitará.")
        from projects.mounting import public_rules

        unit["mounting_rules"] = public_rules(org, unit["design"]["system_id"])
        selected.append(unit)
    if len({(u["position_id"], u["unit_index"]) for u in selected}) != len(selected):
        reject("No repitas una unidad en la misma visita.")
    address = data.get("address") or project_authority.get("delivery_address")
    if not address:
        reject("Falta la dirección de obra. Complétala antes de agendar.")
    return {
        "project_code": project["code"],
        "project_name": project_authority["name"],
        "revision_code": revision,
        "snapshot_sha256": fingerprint,
        "project_version_id": str(version_id) if version_id else None,
        "approved_at": approval_date(org, version_id) if version_id else None,
        "organization": organization,
        "address": address,
        "contact_name": project_authority.get("client_name") or "Sin contacto · pedir al encargado",
        "contact_phone": project_authority.get("client_phone"),
        "units": selected,
        "warranty_terms": {
            k: (project_authority.get("commercial_terms") or {}).get(k)
            for k in ("warranty", "warranty_days", "warranty_start")
        },
    }


def schedule(org, actor, data):
    with transaction.atomic(), documentary_backend():
        role = live_role(org, actor)
        if role not in SUPERVISORS and not (role == "ESTIMATOR" and data["kind"] == "MEASUREMENT"):
            reject(
                "El encargado agenda las salidas; el estimador agenda mediciones.",
                "field_permission",
                403,
            )
        # Scheduler replays also retain live membership and exact request bytes.
        rows(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
            [f"field:{org}:{actor}:{data['operation_key']}"],
        )
        old = rows(
            "SELECT request_hash,response_json FROM public.field_receipts WHERE org_id=%s AND actor_id=%s AND operation_key=%s",
            [org, actor, data["operation_key"]],
        )
        fingerprint = documentary_sha256_v1({"schedule": data})
        if old:
            visit_row(org, decoded(old[0]["response_json"])["visit"]["id"], actor)
            if old[0]["request_hash"] != fingerprint:
                reject(
                    "Esta operación ya tenía otros datos. Crea una operación nueva.",
                    "field_key_conflict",
                    409,
                )
            return decoded(old[0]["response_json"])
        target = rows(
            "SELECT user_id,role::text FROM public.tenancy_memberships WHERE org_id=%s AND user_id=%s "
            "AND is_active AND role IN ('INSTALLER','OWNER','WORKSHOP_MANAGER','ESTIMATOR')",
            [org, data["assigned_to"]],
        )
        if not target:
            reject("El responsable no tiene acceso activo a terreno.")
        if target[0]["role"] == "ESTIMATOR" and data["kind"] != "MEASUREMENT":
            reject(
                "El estimador se asigna a mediciones; elige un responsable de terreno para esta visita."
            )
        context = _context(org, data)
        # Do not allow overlapping live visits for the same physical unit.
        rows(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
            [f"field:project:{org}:{data['project_id']}"],
        )
        previous = rows(
            "SELECT context_json FROM public.field_visits WHERE org_id=%s AND project_id=%s "
            "AND kind=%s AND status IN ('SCHEDULED','ACTIVE')",
            [org, data["project_id"], data["kind"]],
        )
        keys = {(u["position_id"], u["unit_index"]) for u in context["units"]}
        if any(
            keys
            & {(u["position_id"], u["unit_index"]) for u in decoded(v["context_json"])["units"]}
            for v in previous
        ):
            reject(
                "Una unidad ya tiene una visita abierta de este tipo. Abre esa visita o cancélala.",
                "field_visit_overlap",
                409,
            )
        if data["kind"] == "DELIVERY":
            grouped = {}
            for unit in context["units"]:
                grouped.setdefault(unit["order_id"], []).append(unit["unit_index"])
            for order_id, indexes in sorted(grouped.items()):
                service.schedule_delivery(
                    org_id=org,
                    order_id=UUID(order_id),
                    actor_id=actor,
                    scheduled_date=data["planned_on"].isoformat(),
                    time_window="AM",
                    address=context["address"],
                    installer_name=data["team"],
                    unit_indexes=indexes,
                    notes=f"Vehículo: {data.get('vehicle') or 'Sin dato'}",
                )
        visit = one(
            "INSERT INTO public.field_visits(org_id,project_id,project_version_id,assigned_to,code,kind,planned_on,team,vehicle,context_json,created_by) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s) RETURNING *",
            [
                org,
                data["project_id"],
                data.get("project_version_id"),
                data["assigned_to"],
                _code(org, "VIS"),
                data["kind"],
                data["planned_on"],
                data["team"],
                data.get("vehicle"),
                json_text(context),
                actor,
            ],
        )
        output = {"visit": visit_public(visit), "applied": True}
        _receipt(org, actor, data["operation_key"], visit["id"], fingerprint, output)
        return public(output)


def _events(org, visit_id):
    return [
        {**e, "payload_json": decoded(e["payload_json"])}
        for e in rows(
            "SELECT id,sequence,kind,payload_json,created_at FROM public.field_events WHERE org_id=%s AND visit_id=%s ORDER BY sequence",
            [org, visit_id],
        )
    ]


def visit_public(visit):
    context = decoded(visit["context_json"])
    return phone(public(
        {
            **{
                k: visit[k]
                for k in (
                    "id",
                    "code",
                    "project_id",
                    "project_version_id",
                    "assigned_to",
                    "kind",
                    "planned_on",
                    "team",
                    "vehicle",
                    "status",
                )
            },
            "context": phone(context),
            "events": phone(_events(visit["org_id"], visit["id"])),
            "assets": [
                {**asset, "payload_json": decoded(asset["payload_json"])}
                for asset in rows(
                    "SELECT id,position_id,unit_index,kind,file_sha256,created_at,payload_json FROM public.field_assets "
                    "WHERE org_id=%s AND visit_id=%s ORDER BY created_at",
                    [visit["org_id"], visit["id"]],
                )
            ],
        }
    ))


def workspace(org, actor):
    with documentary_backend():
        role = live_role(org, actor)
        visits = [
            visit_public(v)
            for v in rows(
                "SELECT * FROM public.field_visits WHERE org_id=%s ORDER BY planned_on,code", [org]
            )
        ]
        cases = public(
            rows(
                "SELECT i.*,v.context_json FROM public.field_incidents i JOIN public.field_visits v ON v.id=i.visit_id "
                "AND v.org_id=i.org_id WHERE i.org_id=%s ORDER BY i.created_at DESC",
                [org],
            )
        )
        for case in cases:
            context = decoded(case.pop("context_json"))
            case["context"] = phone(context)
            case["evidence"] = phone(decoded(case.pop("evidence_json")))
            case["resolution"] = decoded(case.pop("resolution_json"))
            case["warranty"] = warranty(org, context, case.get("order_id"), case["unit_index"])
        choices, people = [], []
        if role != "INSTALLER":
            from projects.service import positions

            for p in rows(
                "SELECT id,code,name,current_revision,status FROM public.projects WHERE org_id=%s "
                "AND status<>'CANCELLED' ORDER BY updated_at DESC LIMIT 200",
                [org],
            ):
                versions = rows(
                    "SELECT id,revision_code FROM public.project_versions WHERE org_id=%s AND project_id=%s ORDER BY emitted_at DESC",
                    [org, p["id"]],
                )
                choices.append(
                    {
                        **p,
                        "versions": versions,
                        "positions": [_physical(v) for v in positions(org, p["id"])],
                        "orders": [
                            {
                                **{k: v for k, v in o.items() if k != "payload_json"},
                                "packing": (decoded(o["payload_json"]).get("packing") or {}),
                            }
                            for o in rows(
                                "SELECT id,order_code,project_version_id,payload_json,status FROM public.orders "
                                "WHERE org_id=%s AND project_id=%s AND order_type='WORKSHOP_OT' AND status IN ('COMPLETED','DISPATCHED','INSTALLED')",
                                [org, p["id"]],
                            )
                        ],
                    }
                )
            people = rows(
                "SELECT * FROM private.field_people(%s)",
                [org],
            )
        return public(
            {
                "visits": visits,
                "incidents": cases,
                "projects": choices,
                "assignees": people,
                "role": role,
            }
        )


def approval_date(org, version_id):
    approvals = rows(
        "SELECT COALESCE(c.decided_at,ca.decided_at) AS decided_at FROM public.customer_approvals ca "
        "LEFT JOIN LATERAL private.quotation_choice(ca.org_id,ca.project_version_id) c ON true "
        "WHERE ca.org_id=%s AND ((c.kind='APPROVED' AND c.selected_version_id=%s) "
        "OR (c.kind IS NULL AND ca.status='APPROVED' AND ca.project_version_id=%s)) "
        "AND COALESCE(c.decided_at,ca.decided_at) IS NOT NULL ORDER BY decided_at LIMIT 1",
        [org, version_id, version_id],
    )
    return approvals[0]["decided_at"] if approvals else None


def warranty(org, context, order_id, unit_index=None):
    terms = context.get("warranty_terms") or {}
    days, event = terms.get("warranty_days"), terms.get("warranty_start")
    start = None
    # A sealed warranty needs approved commercial authority, not just issuance.
    approved_at = context.get("approved_at")
    if approved_at and event == "APPROVAL":
        start = datetime.fromisoformat(approved_at) if isinstance(approved_at, str) else approved_at
    elif approved_at and order_id and event == "DELIVERY":
        delivered = rows(
            "SELECT c.issued_at FROM public.delivery_confirmations c JOIN public.deliveries d ON d.id=c.delivery_id AND d.org_id=c.org_id "
            "WHERE c.org_id=%s AND c.order_id=%s AND (%s IS NULL OR d.unit_indexes IS NULL OR %s=ANY(d.unit_indexes)) ORDER BY c.issued_at",
            [org, order_id, unit_index, unit_index],
        )
        if delivered:
            start = delivered[0]["issued_at"]
    elif approved_at and order_id and event == "INSTALLATION":
        acts = rows(
            "SELECT created_at FROM public.field_assets WHERE org_id=%s AND kind='ACT' "
            "AND payload_json->>'kind'='INSTALLATION' AND EXISTS(SELECT 1 FROM jsonb_array_elements(payload_json->'context'->'units') u "
            "WHERE u->>'order_id'=%s AND (%s IS NULL OR (u->>'unit_index')::int=%s)) ORDER BY created_at",
            [org, str(order_id), unit_index, unit_index],
        )
        if acts:
            start = acts[0]["created_at"]
    started = (
        start.astimezone(ZoneInfo("America/Santiago")).date()
        if isinstance(start, datetime)
        else start
    )
    deadline = warranty_deadline(started, days)
    return public(
        {
            "days": days,
            "start_event": event,
            "started_on": started,
            "expires_on": deadline,
            "reason": None
            if deadline
            else "Sin dato · falta plazo sellado, aprobación o hecho de inicio acreditado.",
            "text": terms.get("warranty"),
        }
    )


def image_bytes(raw, *, signature=False):
    try:
        data = base64.b64decode(raw, validate=True)
        if not 1 <= len(data) <= (200_000 if signature else 1_500_000):
            raise ValueError()
        with Image.open(BytesIO(data)) as im:
            if im.format not in ("PNG", "JPEG") or (signature and im.format != "PNG"):
                raise ValueError()
            if im.width < 1 or im.height < 1 or im.width * im.height > 4_000_000:
                raise ValueError()
            media = "image/png" if im.format == "PNG" else "image/jpeg"
            im.verify()
        with Image.open(BytesIO(data)) as im:
            im.load()
        return data, media
    except (ValueError, UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise contract_error(
            422,
            "field_image_invalid",
            "La imagen no es válida o excede el límite. Toma otra foto de hasta 1,5 MB.",
        ) from error


def _asset(org, actor, visit, unit, kind, content, media, key, payload):
    digest = sha256(content).hexdigest()
    object_key = f"{org}/field/{visit['id']}/{kind.lower()}/{key}/{digest}.{'pdf' if kind == 'ACT' else 'png' if media == 'image/png' else 'jpg'}"
    SupabaseDocumentStorage().upload_immutable(object_key, content, media)
    return one(
        "INSERT INTO public.field_assets(org_id,visit_id,position_id,unit_index,kind,storage_object_key,media_type,file_sha256,byte_size,payload_json,created_by) "
        "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s) RETURNING id,file_sha256",
        [
            org,
            visit["id"],
            unit["position_id"],
            unit["unit_index"],
            kind,
            object_key,
            media,
            digest,
            len(content),
            json_text(payload),
            actor,
        ],
    )


def _photo(org, actor, visit, unit, data):
    if not data.get("photo_b64"):
        reject("Toma una foto de esta posición antes de guardar.")
    content, media = image_bytes(data["photo_b64"])
    return _asset(
        org,
        actor,
        visit,
        unit,
        "PHOTO",
        content,
        media,
        data["operation_key"],
        {
            "caption": data.get("note") or "Registro en obra",
            "revision_code": visit["context_json"]["revision_code"],
        },
    )


def _unit(visit, data):
    u = next(
        (
            u
            for u in visit["context_json"]["units"]
            if u["position_id"] == str(data.get("position_id"))
            and u["unit_index"] == data.get("unit_index")
        ),
        None,
    )
    if not u:
        reject("La posición y unidad no pertenecen a esta visita.")
    return u


def scan_unit(unit, text, org):
    if not text:
        reject("Escanea la etiqueta o ingresa el código físico antes de guardar.")
    from production.trace import _scan_address, trace_piece

    address = _scan_address(text)
    if address and address["order"] != unit["order_id"]:
        reject("La etiqueta pertenece a otra OT. Escanea el bulto de esta posición.")
    if text == unit.get("label_code"):
        return {"label_code": text, "unit_index": unit["unit_index"]}
    if text.startswith("DEKOPEN|"):
        parts = text.split("|")
        if (
            len(parts) == 4
            and parts[1] == unit.get("order_code")
            and parts[2] == unit.get("label_code")
            and text == unit.get("qr_value")
        ):
            return {"label_code": parts[2], "unit_index": unit["unit_index"]}
    if not unit.get("order_id"):
        reject("Esta medición aún no tiene una etiqueta de producción.")
    # Qualify manual piece codes; never use an unbounded cross-order search.
    from urllib.parse import urlencode

    query = (
        text
        if address or text.startswith("DEKOPEN|")
        else "/production?" + urlencode({"order": unit["order_id"], "piece": text})
    )
    trace = trace_piece(org_id=org, piece_id=query)
    matches = [
        m
        for m in trace["matches"]
        if str(m["work_order"]["id"]) == unit["order_id"]
        and (m["location"].get("piece") or {}).get("unit_index") == unit["unit_index"]
    ]
    if not matches:
        reject("La etiqueta no pertenece a esta unidad de la OT.")
    if len(matches) != 1:
        reject("Escanea el QR de una pieza exacta, con su identidad.")
    piece = matches[0]["location"]["piece"]
    return {
        "piece_id": piece.get("piece_id"),
        "piece_code": piece.get("piece_label"),
        "unit_index": unit["unit_index"],
        "order_id": unit["order_id"],
    }


def _append(org, actor, visit_id, kind, payload):
    return one(
        "INSERT INTO public.field_events(org_id,visit_id,sequence,kind,payload_json,actor_id) "
        "SELECT %s,%s,COALESCE(MAX(sequence),0)+1,%s,%s::jsonb,%s FROM public.field_events WHERE visit_id=%s AND org_id=%s RETURNING id",
        [org, visit_id, kind, json_text(payload), actor, visit_id, org],
    )


def _receipt(org, actor, key, visit_id, fingerprint, output):
    one(
        "INSERT INTO public.field_receipts(org_id,actor_id,operation_key,visit_id,request_hash,response_json) "
        "VALUES(%s,%s,%s,%s,%s,%s::jsonb) RETURNING operation_key",
        [org, actor, key, visit_id, fingerprint, json_text(output)],
    )


def command(org, actor, visit_id, data):
    with transaction.atomic(), documentary_backend():
        # Authorization and assignment precede even a replay after close.
        visit, role = visit_row(org, visit_id, actor, lock=True)
        action = data["kind"]
        if action in ("RESOLVE", "DEPART") and role not in SUPERVISORS:
            reject(
                "El dueño o jefe de taller autoriza remakes, compras y servicios.",
                "field_permission",
                403,
            )
        if action in ("CANCEL", "DIAGNOSE", "CLOSE") and role == "INSTALLER" and action == "CANCEL":
            reject("El encargado cancela las salidas.", "field_permission", 403)
        if role == "ESTIMATOR" and action not in ("MEASURE", "DIAGNOSE", "INCIDENT", "CANCEL"):
            reject(
                "El estimador revisa las medidas; el instalador confirma el trabajo físico.",
                "field_permission",
                403,
            )
        rows(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
            [f"field:{org}:{actor}:{data['operation_key']}"],
        )
        fingerprint = documentary_sha256_v1({"visit_id": visit_id, "command": data})
        existing = rows(
            "SELECT request_hash,response_json FROM public.field_receipts WHERE org_id=%s AND actor_id=%s AND operation_key=%s",
            [org, actor, data["operation_key"]],
        )
        if existing:
            if existing[0]["request_hash"] != fingerprint:
                reject(
                    "Esta operación ya contenía otros datos. Revisa el pendiente antes de reenviarlo.",
                    "field_key_conflict",
                    409,
                )
            return decoded(existing[0]["response_json"])
        if visit["status"] in ("CLOSED", "CANCELLED") and action not in (
            "INCIDENT",
            "DIAGNOSE",
            "RESOLVE",
            "CLOSE",
        ):
            reject(
                "Esta visita está cerrada. Agenda otra para registrar un trabajo nuevo.",
                "field_visit_closed",
                409,
            )
        payload = {"note": data.get("note") or ""}
        if action in ("LOAD", "CHECK", "MEASURE", "INCIDENT"):
            unit = _unit(visit, data)
            payload.update(position_id=unit["position_id"], unit_index=unit["unit_index"])
            if action in ("LOAD", "CHECK"):
                if visit["kind"] != ("DELIVERY" if action == "LOAD" else "INSTALLATION"):
                    reject("El registro no corresponde al tipo de visita.")
                payload["scan"] = scan_unit(unit, data.get("scan") or "", org)
            if action == "LOAD":
                if any(e["kind"] == "DEPART" for e in _events(org, visit_id)):
                    reject("El vehículo ya salió. La carga queda conservada en su guía.")
                payload["loaded"] = True
            else:
                payload["photo"] = _photo(org, actor, visit, unit, data)
            if action == "CHECK":
                checks = data.get("checks") or {}
                if set(checks) != set(CHECKS) or not all(
                    isinstance(checks[k], bool) for k in CHECKS
                ):
                    reject("Completa las cinco comprobaciones de esta posición.")
                payload["checks"] = checks
            if action == "MEASURE":
                from projects.mounting import SURVEYS, derive_design

                try:
                    surveys = SURVEYS.validate_json(json_text(data.get("measurements") or []))
                except ValueError as error:
                    raise contract_error(
                        422,
                        "field_measurement_invalid",
                        "Revisa las tres medidas por eje y su regla de montaje.",
                    ) from error
                if not surveys or any(
                    len(s.widths_mm) != 3 or len(s.heights_mm) != 3 or s.origin != "SITE"
                    for s in surveys
                ):
                    reject("Mide el vano en tres puntos por eje y declara que son medidas de obra.")
                tree = unit["design"]["parametric_tree"]
                targets = (
                    {m["id"] for m in tree["assembly"]["modules"]}
                    if tree.get("version") == "product-v2"
                    else {None}
                )
                if {s.module_id for s in surveys} != targets or len(surveys) != len(targets):
                    reject("Mide cada marco del conjunto antes de enviar la posición a revisión.")
                design, evidence = derive_design(
                    org, unit["design"], surveys, sealed_rules=unit["mounting_rules"]
                )
                from projects.service import calculate_design

                calculate_design(org, design)
                payload.update(
                    measurements=[s.model_dump(mode="json") for s in surveys],
                    design=design,
                    evidence=evidence,
                    binding=documentary_sha256_v1(unit["design"]),
                    review_status="PENDING",
                )
            if action == "INCIDENT":
                kind = data.get("incident_kind")
                if kind not in (
                    "DAMAGE",
                    "MEASURE",
                    "MISSING",
                    "ADJUSTMENT",
                    "WARRANTY",
                    "SERVICE",
                ):
                    reject("Elige el tipo de incidencia.")
                piece = scan_unit(unit, data["scan"], org) if data.get("scan") else None
                case = one(
                    "INSERT INTO public.field_incidents(org_id,visit_id,order_id,position_id,code,kind,unit_index,piece_identity,description,evidence_json,created_by) "
                    "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s) RETURNING id,code",
                    [
                        org,
                        visit_id,
                        unit["order_id"],
                        unit["position_id"],
                        _code(org, "INC", visit_id),
                        kind,
                        unit["unit_index"],
                        (piece or {}).get("piece_id"),
                        data.get("note") or reject("Describe qué ocurrió en esta posición."),
                        json_text(
                            {
                                "photo": payload["photo"],
                                "piece": piece,
                                "materials": unit["materials"],
                            }
                        ),
                        actor,
                    ],
                )
                payload["incident"] = case
            rows(
                "UPDATE public.field_visits SET status='ACTIVE' WHERE org_id=%s AND id=%s AND status='SCHEDULED' RETURNING id",
                [org, visit_id],
            )
        elif action == "DEPART":
            payload = depart(org, actor, visit, data)
        elif action == "DELIVER":
            payload = deliver(org, actor, visit, data)
        elif action == "RECEIVE":
            payload = receive(org, actor, visit, data)
        elif action == "RESOLVE":
            payload = resolve(org, actor, visit, data)
        elif action in ("DIAGNOSE", "CLOSE"):
            case = _case(org, visit, data)
            if not data.get("note"):
                reject("Registra el diagnóstico o la causa del cierre.")
            if action == "CLOSE" and case["status"] not in ("PLANNED", "RESOLVED"):
                reject("Primero resuelve o agenda la incidencia antes de cerrarla.")
            if action == "CLOSE":
                resolution = decoded(case["resolution_json"])
                if resolution.get("service_visit_id"):
                    sv, _ = visit_row(org, resolution["service_visit_id"], actor)
                    if sv["status"] != "CLOSED":
                        reject("Cierra la visita de servicio antes de cerrar la incidencia.")
                if resolution.get("remake_order_id"):
                    order = one(
                        "SELECT status FROM public.orders WHERE org_id=%s AND id=%s",
                        [org, resolution["remake_order_id"]],
                    )
                    if order["status"] != "INSTALLED":
                        reject(
                            "La reposición todavía no está instalada. Completa su flujo antes de cerrar."
                        )
                if resolution.get("purchase_order_id"):
                    order = one(
                        "SELECT status FROM public.orders WHERE org_id=%s AND id=%s",
                        [org, resolution["purchase_order_id"]],
                    )
                    if order["status"] != "FULFILLED":
                        reject("Recibe la compra antes de cerrar el faltante.")
                if resolution.get("corrective_project_id"):
                    corrective = rows(
                        "SELECT id,status FROM public.orders WHERE org_id=%s AND project_id=%s AND order_type='WORKSHOP_OT'",
                        [org, resolution["corrective_project_id"]],
                    )
                    if not corrective or any(o["status"] != "INSTALLED" for o in corrective):
                        reject(
                            "Libera e instala la OT correctiva antes de cerrar la incidencia de medida."
                        )
                    payload["corrective_orders"] = [str(o["id"]) for o in corrective]
            rows(
                "UPDATE public.field_incidents SET diagnosis=%s,status=%s WHERE org_id=%s AND id=%s RETURNING id",
                [data["note"], "CLOSED" if action == "CLOSE" else case["status"], org, case["id"]],
            )
            payload["incident_id"] = str(case["id"])
        elif action == "CANCEL":
            if visit["status"] not in ("SCHEDULED", "ACTIVE"):
                reject("La visita ya está cerrada.")
            if visit["kind"] == "DELIVERY" and any(
                e["kind"] == "DEPART" for e in _events(org, visit_id)
            ):
                reject(
                    "El vehículo ya salió con una guía. Registra el retorno del viaje en Producción antes de reagendar."
                )
            if visit["kind"] == "DELIVERY":
                for order_id in sorted({u["order_id"] for u in visit["context_json"]["units"]}):
                    service.cancel_scheduled_delivery(org_id=org, order_id=UUID(order_id), actor_id=actor)
            rows(
                "UPDATE public.field_visits SET status='CANCELLED' WHERE org_id=%s AND id=%s RETURNING id",
                [org, visit_id],
            )
        else:
            reject("La operación de terreno no está reconocida.")
        event = _append(org, actor, visit_id, action, payload)
        fresh, _ = visit_row(org, visit_id, actor)
        output = {
            "applied": True,
            "operation_key": str(data["operation_key"]),
            "event_id": str(event["id"]),
            "result": public(phone(payload)),
            "visit": visit_public(fresh),
        }
        _receipt(org, actor, data["operation_key"], visit_id, fingerprint, output)
        return public(output)


def depart(org, actor, visit, data):
    if visit["kind"] != "DELIVERY" or not data.get("confirmed"):
        reject("Revisa la carga y confirma la salida del vehículo.")
    loaded = {
        (e["payload_json"].get("position_id"), e["payload_json"].get("unit_index"))
        for e in _events(org, visit["id"])
        if e["kind"] == "LOAD"
    }
    grouped = {}
    for unit in visit["context_json"]["units"]:
        if (unit["position_id"], unit["unit_index"]) not in loaded:
            reject("Escanea y confirma cada bulto de la carga antes de emitir la guía.")
        grouped.setdefault(unit["order_id"], []).append(unit["unit_index"])
    notes = []
    for order_id, indexes in sorted(grouped.items()):
        order = service.dispatch_work_order(
            org_id=org,
            order_id=UUID(order_id),
            actor_id=actor,
            unit_indexes=indexes,
            note=f"Carga comprobada en {visit['code']}",
        )
        service.transition_delivery(
            org_id=org, order_id=UUID(order_id), actor_id=actor, to_status="ON_ROUTE"
        )
        notes.extend(order.get("dispatch_notes") or [])
    rows(
        "UPDATE public.field_visits SET status='ACTIVE' WHERE org_id=%s AND id=%s RETURNING id",
        [org, visit["id"]],
    )
    return {"dispatch_notes": notes, "note": "Bultos comprobados y vehículo en ruta"}


def deliver(org, actor, visit, data):
    if visit["kind"] != "DELIVERY" or not data.get("confirmed"):
        reject("Revise la entrega antes de confirmar la recepción del cliente.")
    if not data.get("receiver_name") or not data.get("receiver_rut"):
        reject("Declare nombre y RUT del receptor.")
    validate_rut(data["receiver_rut"])
    image_bytes(data.get("signature_b64") or "", signature=True)
    from production.confirmations import confirm_delivery

    grouped = {}
    for unit in visit["context_json"]["units"]:
        grouped.setdefault(unit["order_id"], set()).add(unit["unit_index"])
    sealed = []
    for order_id, indexes in sorted(grouped.items()):
        trip = one(
            "SELECT id,unit_indexes FROM public.deliveries WHERE org_id=%s AND order_id=%s AND status='ON_ROUTE' FOR UPDATE",
            [org, order_id],
            "delivery_not_found",
        )
        manifest = one(
            "SELECT payload_json FROM public.orders WHERE org_id=%s AND id=%s", [org, order_id]
        )
        actual = service._delivery_unit_set(
            trip, service._manifest_unit_indexes(decoded(manifest["payload_json"]))
        )
        if actual != indexes:
            reject("La carga del viaje cambió. Revisa la visita y sus bultos antes de firmar.")
        result = confirm_delivery(
            org_id=org,
            order_id=UUID(order_id),
            actor_id=actor,
            receiver_name=data["receiver_name"],
            receiver_rut=data["receiver_rut"],
            signature_b64=data["signature_b64"],
            payment=None,
        )
        sealed.append(result)
    rows(
        "UPDATE public.field_visits SET status='CLOSED' WHERE org_id=%s AND id=%s RETURNING id",
        [org, visit["id"]],
    )
    return {
        "confirmations": public(sealed),
        "note": data.get("note") or "Entrega recibida por el cliente",
    }


def receive(org, actor, visit, data):
    if visit["kind"] not in ("INSTALLATION", "SERVICE"):
        reject("Esta visita no admite acta de instalación o servicio.")
    if not data.get("confirmed") or not data.get("receiver_name") or not data.get("receiver_rut"):
        reject("El cliente debe revisar y confirmar nombre, RUT y firma antes de sellar.")
    validate_rut(data["receiver_rut"])
    signature, media = image_bytes(data.get("signature_b64") or "", signature=True)
    events = _events(org, visit["id"])
    units = visit["context_json"]["units"]
    checks = []
    for unit in units:
        if visit["kind"] == "INSTALLATION":
            delivered = rows(
                "SELECT d.unit_indexes FROM public.deliveries d JOIN public.delivery_confirmations c "
                "ON c.delivery_id=d.id AND c.org_id=d.org_id WHERE d.org_id=%s AND d.order_id=%s AND d.status='DELIVERED'",
                [org, unit["order_id"]],
            )
            if not any(
                d["unit_indexes"] is None or unit["unit_index"] in d["unit_indexes"]
                for d in delivered
            ):
                reject(
                    "Esta unidad todavía no tiene entrega firmada. Registra su recepción de despacho antes de instalar."
                )
        matching = [
            e
            for e in events
            if e["kind"] == "CHECK"
            and e["payload_json"].get("position_id") == unit["position_id"]
            and e["payload_json"].get("unit_index") == unit["unit_index"]
        ]
        if visit["kind"] == "INSTALLATION" and (
            not matching or not all(matching[-1]["payload_json"]["checks"].values())
        ):
            reject(
                "Completa las cinco comprobaciones y la foto de cada unidad antes de pedir la firma."
            )
        if matching:
            checks.append(matching[-1]["payload_json"])
    if visit["kind"] == "SERVICE":
        unit = units[0]
        checks = [
            {
                "position_id": unit["position_id"],
                "unit_index": unit["unit_index"],
                "photo": _photo(org, actor, visit, unit, data),
                "note": data.get("note"),
            }
        ]
        if not data.get("note"):
            reject("Describe el servicio realizado antes de pedir la firma.")
    sig = _asset(
        org,
        actor,
        visit,
        units[0],
        "SIGNATURE",
        signature,
        media,
        data["operation_key"],
        {"receiver_name": data["receiver_name"], "receiver_rut": data["receiver_rut"]},
    )
    payload = {
        "act_code": _code(org, "ACT", visit["id"]),
        "kind": visit["kind"],
        "visit_code": visit["code"],
        "context": visit["context_json"],
        "receiver_name": data["receiver_name"],
        "receiver_rut": data["receiver_rut"],
        "signature": sig,
        "checks": checks,
        "observations": data.get("note") or "Sin observaciones declaradas",
        "issued_at": datetime.now(ZoneInfo("America/Santiago")).isoformat(),
        "order_ids": sorted({u["order_id"] for u in units if u["order_id"]}),
        "incidents": public(
            rows(
                "SELECT code,kind,description,status FROM public.field_incidents WHERE org_id=%s AND visit_id=%s ORDER BY created_at",
                [org, visit["id"]],
            )
        ),
    }
    from production.field_pdf import render_field_act

    pdf = render_field_act(payload, signature)
    asset = _asset(
        org, actor, visit, units[0], "ACT", pdf, "application/pdf", data["operation_key"], payload
    )
    rows(
        "UPDATE public.field_visits SET status='CLOSED' WHERE org_id=%s AND id=%s RETURNING id",
        [org, visit["id"]],
    )
    # Partial installation leaves the source OT dispatched. A whole-order
    # completion still passes the existing signed-delivery/manifest guards.
    if visit["kind"] == "INSTALLATION":
        for order_id in payload["order_ids"]:
            source = one(
                "SELECT payload_json FROM public.orders WHERE org_id=%s AND id=%s FOR UPDATE",
                [org, order_id],
            )
            manifest = service._manifest_unit_indexes(decoded(source["payload_json"]))
            installed = set()
            for a in rows(
                "SELECT payload_json FROM public.field_assets WHERE org_id=%s AND kind='ACT' AND payload_json->>'kind'='INSTALLATION' AND payload_json->'order_ids' ? %s",
                [org, order_id],
            ):
                p = decoded(a["payload_json"])
                installed.update(
                    u["unit_index"]
                    for u in p["context"]["units"]
                    if u["order_id"] == order_id and p["checks"]
                )
            if manifest and manifest <= installed:
                service.confirm_installation(
                    str(org),
                    order_id,
                    str(actor),
                    note=f"Acta {payload['act_code']}; incidencias conservadas",
                )
    return {"act": asset, "act_code": payload["act_code"], "signature": sig}


def _case(org, visit, data):
    return one(
        "SELECT * FROM public.field_incidents WHERE org_id=%s AND visit_id=%s AND id=%s FOR UPDATE",
        [org, visit["id"], data.get("incident_id")],
        "field_incident_not_found",
    )


def resolve(org, actor, visit, data):
    case = _case(org, visit, data)
    if not data.get("confirmed") or not data.get("note"):
        reject("Revisa el diagnóstico y confirma explícitamente la solución.")
    if case["status"] != "OPEN":
        reject(
            "La incidencia ya tiene una solución. Abre su trazabilidad.", "field_case_resolved", 409
        )
    action = data.get("resolution_kind")
    if action == "REMAKE":
        if case["kind"] != "DAMAGE" or not case["order_id"]:
            reject(
                "Solo un daño con OT admite reposición idéntica. Una medida distinta requiere rectificación revisada."
            )
        result = service.create_field_remake(
            org_id=org,
            order_id=case["order_id"],
            actor_id=actor,
            incident_id=case["id"],
            unit_index=case["unit_index"],
            note=data["note"],
        )
        resolution = {"remake_order_id": result["id"], "remake_code": result["order_code"]}
    elif action == "PURCHASE":
        if case["kind"] != "MISSING" or not visit["project_version_id"]:
            reject("La compra requiere un faltante en una revisión sellada.")
        from purchasing.field_purchase import replacement_order

        resolution = replacement_order(org, actor, visit["project_version_id"], case, data)
    elif action == "SERVICE":
        if not data.get("planned_on") or not data.get("assigned_to"):
            reject("Declara fecha y responsable de la visita de servicio.")
        unit = next(
            u
            for u in visit["context_json"]["units"]
            if u["position_id"] == str(case["position_id"])
            and u["unit_index"] == case["unit_index"]
        )
        scheduled = schedule(
            org,
            actor,
            {
                "operation_key": uuid4(),
                "project_id": visit["project_id"],
                "project_version_id": visit["project_version_id"],
                "kind": "SERVICE",
                "assigned_to": data["assigned_to"],
                "planned_on": data["planned_on"],
                "team": data.get("team") or visit["team"],
                "address": visit["context_json"]["address"],
                "units": [
                    {
                        "position_id": case["position_id"],
                        "unit_index": case["unit_index"],
                        "order_id": unit["order_id"],
                    }
                ],
            },
        )
        resolution = {
            "service_visit_id": scheduled["visit"]["id"],
            "service_code": scheduled["visit"]["code"],
        }
    else:
        reject("Elige reposición, compra o servicio; las medidas se revisan en Rectificación.")
    resolution.update(diagnosis=data["note"], confirmed_by=str(actor))
    rows(
        "UPDATE public.field_incidents SET status='PLANNED',diagnosis=%s,resolution_json=%s::jsonb WHERE org_id=%s AND id=%s RETURNING id",
        [data["note"], json_text(resolution), org, case["id"]],
    )
    return {"incident_id": str(case["id"]), "resolution": resolution}


def asset_access(org, actor, asset_id):
    with documentary_backend():
        asset = one(
            "SELECT * FROM public.field_assets WHERE org_id=%s AND id=%s",
            [org, asset_id],
            "field_asset_not_found",
        )
        visit_row(org, asset["visit_id"], actor)
        return {
            "id": str(asset_id),
            "signed_url": SupabaseDocumentStorage().signed_url(asset["storage_object_key"], 600),
            "file_sha256": asset["file_sha256"],
            "expires_in": 600,
        }


def review_measurement(org, actor, visit_id, data, tenant):
    """D07 stays closed in production. A frozen source opens a corrective draft."""
    from projects.mounting import binding, rectify, SURVEYS, derive_design, append_measurement
    from projects.service import (
        project_row,
        position_row,
        position_public,
        save_position,
        create_project,
        calculate_design,
    )

    with transaction.atomic(), documentary_backend():
        visit, role = visit_row(org, visit_id, actor, lock=True)
        if role not in ("OWNER", "ESTIMATOR"):
            reject(
                "El estimador revisa las medidas y su variación de venta.", "field_permission", 403
            )
        event = one(
            "SELECT * FROM public.field_events WHERE org_id=%s AND visit_id=%s AND id=%s AND kind='MEASURE'",
            [org, visit_id, data["measurement_event_id"]],
            "field_measurement_not_found",
        )
        measured = decoded(event["payload_json"])
        newer = rows(
            "SELECT id FROM public.field_events WHERE org_id=%s AND visit_id=%s AND sequence>%s AND kind='MEASURE' "
            "AND payload_json->>'position_id'=%s AND (payload_json->>'unit_index')::int=%s",
            [org, visit_id, event["sequence"], measured["position_id"], measured["unit_index"]],
        )
        if newer:
            reject(
                "Hay una medición posterior. Revisa la evidencia más reciente.",
                "field_measurement_stale",
                409,
            )
        applied = rows(
            "SELECT payload_json FROM public.field_events WHERE org_id=%s AND visit_id=%s AND kind='RESOLVE' "
            "AND payload_json->>'measurement_event_id'=%s",
            [org, visit_id, str(event["id"])],
        )
        if applied:
            return public(decoded(applied[0]["payload_json"]))
        project = project_row(org, visit["project_id"], lock=True)
        unit = _unit(visit, measured)
        if project["status"] in ("DRAFT", "QUOTED", "APPROVED"):
            position = position_row(org, unit["position_id"], lock=True)
            live = position_public(position)["design"]
            if binding(live) != binding(unit["design"]):
                reject(
                    "El diseño cambió después de agendar. Crea una visita con la revisión actual.",
                    "field_measurement_stale",
                    409,
                )
            proposal = _project_call(
                rectify,
                org,
                tenant,
                unit["position_id"],
                {
                    "design": live,
                    "measurements": measured["measurements"],
                    "expected_updated_at": position["updated_at"],
                    "expected_current_revision": project["current_revision"],
                    "reason": data["reason"],
                    "confirmed": data["confirmed"],
                    "proposal_token": data.get("proposal_token"),
                },
            )
            proposal["project_id"] = str(project["id"])
            proposal["project_code"] = project["code"]
        else:
            if not visit["project_version_id"]:
                reject("Falta una revisión fuente sellada para la corrección.")
            snapshot = decoded(_version(org, visit["project_version_id"])["snapshot_json"])
            design, evidence = derive_design(
                org, unit["design"], SURVEYS.validate_json(json_text(measured["measurements"]))
            )
            bom = calculate_design(org, design)
            from pricing.serializers import PriceRequestSerializer
            from pricing.service import preview
            from documents.views import validate
            from dekopen_engine.finishes import finish_selling_delta
            from dekopen_engine.commercial import PricingError

            price_change = {
                "before_net": None,
                "after_net": None,
                "delta_net": None,
                "currency": None,
                "reason": None,
            }
            with _role_scope("pricing_backend"):
                raw = snapshot["pricing"]["request"]
                pricing_request = validate(
                    PriceRequestSerializer,
                    {**raw, "project_id": project["id"], "reason": data["reason"]},
                )
                pseudo = []
                for sealed in snapshot["positions"]:
                    physical = _physical(sealed)
                    pseudo.append(
                        {
                            "id": UUID(physical["position_id"]),
                            "project_id": project["id"],
                            "position_index": physical["position_index"],
                            "quantity": physical["quantity"],
                            "width_mm": Decimal(physical["design"]["nominal_width_mm"]),
                            "height_mm": Decimal(physical["design"]["nominal_height_mm"]),
                            "system_id": physical["design"]["system_id"],
                            "parametric_tree": physical["design"]["parametric_tree"],
                            "color_interior": physical["design"]["color"],
                            "color_exterior": physical["design"]["color"],
                            "bom_snapshot": sealed.get("engine_result")
                            or sealed.get("bom_snapshot")
                            or {},
                            "location_tag": physical["location_tag"],
                            "price_net": sealed.get("price_net"),
                        }
                    )
                changed = [
                    {
                        **p,
                        "width_mm": design["nominal_width_mm"],
                        "height_mm": design["nominal_height_mm"],
                        "parametric_tree": design["parametric_tree"],
                        "bom_snapshot": bom,
                    }
                    if str(p["id"]) == unit["position_id"]
                    else p
                    for p in pseudo
                ]
                try:
                    before = preview(
                        org, tenant, pricing_request, simulate=True, proposed_positions=pseudo
                    )
                    after = preview(
                        org, tenant, pricing_request, simulate=True, proposed_positions=changed
                    )
                    price_change.update(
                        before_net=str(before["project_net"]),
                        after_net=str(after["project_net"]),
                        delta_net=str(
                            finish_selling_delta(
                                Decimal(str(before["project_net"])),
                                Decimal(str(after["project_net"])),
                            )
                        ),
                        currency=pricing_request["currency"],
                    )
                except PricingError as error:
                    from pricing.service import pricing_public_detail

                    price_change["reason"] = pricing_public_detail(error.code)
            proposal = {
                "design": public(design),
                "measurements": evidence,
                "price_change": price_change,
                "applied": False,
                "revision_code": "REV-A",
                "project_id": None,
                "project_code": None,
                "scope": "Borrador correctivo de una unidad. El Δ compara la geometría de la posición en la revisión fuente; la nueva venta requiere revisión propia.",
            }
            token = documentary_sha256_v1(
                {"org": org, "visit": visit_id, "event": event["id"], "proposal": proposal}
            )
            proposal["proposal_token"] = token
            if data["confirmed"]:
                if data.get("proposal_token") != token:
                    reject(
                        "La propuesta cambió. Revísala otra vez.", "field_measurement_stale", 409
                    )
                from projects.service import METADATA

                source = snapshot["project"]
                draft = _project_call(
                    create_project,
                    org,
                    actor,
                    {
                        **{k: source.get(k) or "" for k in METADATA},
                        "name": f"Corrección {visit['code']} · {source['name']}"[:250],
                    },
                )
                from projects.serializers import PositionWriteSerializer

                serializer = PositionWriteSerializer(
                    data={
                        "location_tag": unit["location_tag"],
                        "quantity": 1,
                        "design": public(design),
                    }
                )
                serializer.is_valid(raise_exception=True)
                position = _project_call(
                    save_position, org, draft["id"], serializer.validated_data, apply_defaults=False
                )
                append_measurement(
                    org,
                    position_row(org, position["id"]),
                    "REV-A",
                    evidence,
                    "SITE",
                    data["reason"],
                    price_change,
                )
                proposal.update(
                    applied=True,
                    project_id=str(draft["id"]),
                    project_code=draft["code"],
                    position_id=str(position["id"]),
                )
        if proposal["applied"]:
            result = {
                **public(proposal),
                "measurement_event_id": str(event["id"]),
                "source_order_id": unit["order_id"],
                "source_unit_index": unit["unit_index"],
                "source_version_id": str(visit["project_version_id"])
                if visit["project_version_id"]
                else None,
            }
            _append(org, actor, visit_id, "RESOLVE", result)
            history = _events(org, visit_id)
            reviewed = {
                e["payload_json"].get("measurement_event_id")
                for e in history
                if e["kind"] == "RESOLVE"
            }
            accepted_units = {
                (e["payload_json"].get("position_id"), e["payload_json"].get("unit_index"))
                for e in history
                if e["kind"] == "MEASURE" and str(e["id"]) in reviewed
            }
            if visit["kind"] == "MEASUREMENT" and all(
                (u["position_id"], u["unit_index"]) in accepted_units
                for u in visit["context_json"]["units"]
            ):
                rows(
                    "UPDATE public.field_visits SET status='CLOSED' WHERE org_id=%s AND id=%s RETURNING id",
                    [org, visit_id],
                )
            rows(
                "UPDATE public.field_incidents SET status='PLANNED',resolution_json=%s::jsonb,diagnosis=%s "
                "WHERE org_id=%s AND visit_id=%s AND position_id=%s AND unit_index=%s AND kind='MEASURE' AND status='OPEN' RETURNING id",
                [
                    json_text(
                        {
                            "corrective_project_id": proposal["project_id"],
                            "project_code": proposal["project_code"],
                        }
                    ),
                    data["reason"],
                    org,
                    visit_id,
                    unit["position_id"],
                    unit["unit_index"],
                ],
            )
            return result
        return public(proposal)
