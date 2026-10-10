"""Entity-level work, under caller claims and existing domain read roles.

    Sealed quotations supply validity and sale. The payment ledger supplies
    receipts; the pure engine computes the balance. No cost or private pricing
    result is returned by this projection, including to estimators.
"""

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from dekopen_engine.work_queue import consequence, money_sum, outstanding, queue_order
from documents.repository import DocumentaryError, documentary_backend, rows
from pricing.repository import commercial_backend
from pricing.service import decoded
from engine_api.adapter import evaluate_assembly_from_api, parse_product_model
from engine_api.repository import SystemParamsRepository, SystemNotFound, UnsupportedCatalogContract

COMMERCIAL_ROLES = {"OWNER", "ESTIMATOR"}


def local_today(org_id):
    zone = rows("SELECT timezone FROM public.tenancy_organizations WHERE id=%s", [org_id])
    # A disappeared organization must never acquire invented working dates.
    if not zone:
        raise DocumentaryError("organization_not_found")
    return datetime.now(timezone.utc).astimezone(ZoneInfo(zone[0]["timezone"])).date()


def quotation_rows(org_id):
    with documentary_backend():
        return rows("""
            SELECT p.id,p.code,p.name,p.client_name,p.status::text,p.current_revision,
                   v.id AS version_id,v.emitted_at,
                   v.snapshot_json->'project'->>'quotation_valid_until' AS valid_until,
                   v.snapshot_json->'project'->>'total_price_gross' AS total,
                   v.snapshot_json->'project'->>'currency' AS currency,
                   a.status AS response_status,a.decided_note,a.decided_at,
                   a.view_count,a.last_viewed_at,a.expires_at,
                   a.created_at AS shared_at
            FROM public.projects p
            JOIN public.project_versions v ON v.project_id=p.id AND v.org_id=p.org_id
                 AND v.revision_code=p.current_revision
            LEFT JOIN LATERAL (
                SELECT
                  (array_agg(status ORDER BY (status='APPROVED') DESC,
                    (status='DECLINED') DESC,decided_at DESC NULLS LAST,id DESC))[1] AS status,
                  (array_agg(decided_note ORDER BY (status='APPROVED') DESC,
                    (status='DECLINED') DESC,decided_at DESC NULLS LAST,id DESC))[1] AS decided_note,
                  max(decided_at) AS decided_at,sum(view_count) AS view_count,
                  max(last_viewed_at) AS last_viewed_at,
                  max(private.quote_link_expires_at(ca.id,ca.org_id,ca.expires_at)) AS expires_at,
                  max(created_at) AS created_at
                FROM public.customer_approvals ca
                WHERE ca.org_id=p.org_id AND ca.project_id=p.id
                  AND ca.project_version_id=v.id AND ca.status<>'REVOKED'
            ) a ON true
            WHERE p.org_id=%s AND p.status<>'CANCELLED'
            ORDER BY v.emitted_at DESC,p.code
        """, [org_id])


def quote_public(row, today):
    validity = row["valid_until"]
    expired = validity is not None and date.fromisoformat(validity) < today
    state = ("expired" if expired and row["status"] == "QUOTED" else
             "approved" if row["status"] in {"APPROVED", "IN_PRODUCTION", "COMPLETED"} else
             "response" if row["response_status"] == "DECLINED" else
             "unshared" if row["shared_at"] is None else
             "link_expired" if row["expires_at"] < datetime.now(timezone.utc) else "pending")
    return {
        "project_id": str(row["id"]), "project_code": row["code"], "project_name": row["name"],
        "client_name": row["client_name"], "revision_code": row["current_revision"],
        "state": state, "valid_until": validity,
        "phase": row["status"],
        "view_count": int(row["view_count"] or 0),
        "last_viewed_at": row["last_viewed_at"].isoformat() if row["last_viewed_at"] else None,
        "response_note": row["decided_note"],
        "total": row["total"], "currency": row["currency"],
        "source": "Total y vigencia de la revisión emitida; vistas y respuesta de sus enlaces vigentes.",
        "href": f"/projects/{row['id']}?section=quote",
    }


def quotations(org_id, *, query="", attention="", phase="", currency="", offset=0, limit=50):
    today = local_today(org_id)
    items = [quote_public(row, today) for row in quotation_rows(org_id)]
    needle = query.strip().casefold()
    if needle:
        items = [item for item in items if needle in " ".join(
            str(item[key]) for key in ("project_code", "project_name", "client_name", "revision_code")
        ).casefold()]
    if attention:
        items = [item for item in items if quote_attention(item, attention, today)]
    if phase:
        items = [item for item in items if item["phase"] == phase]
    if currency:
        items = [item for item in items if item["currency"] == (None if currency == "unknown" else currency)]
    return {"items": items[offset:offset + limit], "total": len(items), "offset": offset,
            "limit": limit, "today": today.isoformat()}


def quote_attention(item, kind, today):
    if kind == "expiring":
        return (item["state"] in {"pending", "unshared", "link_expired"}
                and item["valid_until"] is not None
                and today <= date.fromisoformat(item["valid_until"]) <= today + timedelta(days=3))
    if kind == "viewed":
        return item["state"] == "pending" and item["view_count"] > 0
    if kind == "response":
        return item["state"] == "response"
    return item["state"] == kind


def action(kind, entity_id, code, name, title, reason, verb, href, *,
           due_on=None, blocking=False, amount=None, currency=None, source=None, operation_id=None,
           balance_total=None, balance_collected=None):
    return {"key": f"{kind}:{entity_id}", "kind": kind, "entity_code": code,
            "entity_name": name, "title": title, "reason": reason, "verb": verb, "href": href,
            "due_on": due_on.isoformat() if due_on else None, "blocking": blocking,
            "amount": str(amount) if amount is not None else None, "currency": currency,
            "balance_total": str(balance_total) if balance_total is not None else None,
            "balance_collected": str(balance_collected) if balance_collected is not None else None,
            "source": source, "operation_id": str(operation_id) if operation_id else None}


def price_actions(org_id, user_id, role):
    if role not in COMMERCIAL_ROLES:
        return []
    with commercial_backend():
        operations = rows("""
            SELECT o.id,o.project_id,p.code,p.name,o.state,o.reason,o.revision_code
            FROM public.pricing_operations o
            JOIN public.projects p ON p.id=o.project_id AND p.org_id=o.org_id
            WHERE o.org_id=%s AND (
                (%s='OWNER' AND o.state='PENDING' AND p.status='DRAFT'
                 AND o.revision_code=p.current_revision)
                OR (o.requested_by=%s AND o.approved_by IS DISTINCT FROM o.requested_by
                    AND o.state IN ('APPLIED','REJECTED') AND NOT EXISTS (
                        SELECT 1 FROM public.pricing_attention_receipts r
                        WHERE r.org_id=o.org_id AND r.operation_id=o.id AND r.user_id=%s)))
            ORDER BY o.created_at,o.id
        """, [org_id, role, user_id, user_id])
    return [action(
        "price_pending" if row["state"] == "PENDING" else "price_decision", row["id"],
        row["code"], row["name"],
        "Decide el acuerdo de precio" if row["state"] == "PENDING" else
        "Precio aprobado" if row["state"] == "APPLIED" else "Precio rechazado",
        row["reason"], "Revisar y decidir" if row["state"] == "PENDING" else "Leer decisión",
        "/projects/" + str(row["project_id"]) + "/pricing?" + urlencode({"operation": row["id"]}),
        blocking=row["state"] == "PENDING", operation_id=row["id"],
        source="Operación de precio y recibo del solicitante; " + row["revision_code"],
    ) for row in operations]


def commercial_actions(org_id, today, role):
    result, pipeline = [], []
    source_rows = quotation_rows(org_id)
    quotes = [quote_public(row, today) for row in source_rows]
    for item in quotes:
        if quote_attention(item, "expiring", today):
            result.append(action("quote_expiring", item["project_id"], item["project_code"],
                item["project_name"], "Cierra la cotización antes de que venza",
                "La vigencia comercial termina dentro de tres días. El enlace no extiende ese plazo.",
                "Revisar cotización", item["href"], due_on=date.fromisoformat(item["valid_until"]),
                source=item["source"]))
        if quote_attention(item, "viewed", today):
            result.append(action("quote_viewed", item["project_id"], item["project_code"],
                item["project_name"], "Contacta al cliente que vio la propuesta",
                f"{item['client_name']} abrió la revisión y todavía no responde.",
                "Revisar seguimiento", item["href"], source=item["source"]))
        if quote_attention(item, "response", today):
            result.append(action("quote_response", item["project_id"], item["project_code"],
                item["project_name"], "Revisa la respuesta del cliente",
                item["response_note"] or "El cliente rechazó la propuesta sin un motivo registrado.",
                "Revisar cambios", item["href"], blocking=True, source=item["source"]))
        if item["state"] == "expired":
            result.append(action("quote_expired", item["project_id"], item["project_code"],
                item["project_name"], "Renueva la cotización vencida",
                "La revisión emitida conserva sus condiciones. Prepara una sucesora para renovarlas.",
                "Preparar revisión", item["href"], due_on=date.fromisoformat(item["valid_until"]),
                source=item["source"]))

    if role == "OWNER":
        by_phase = defaultdict(list)
        unknown = defaultdict(int)
        with documentary_backend():
            receipts = rows("SELECT project_id,amount FROM public.project_payments "
                            "WHERE org_id=%s AND voided_at IS NULL", [org_id])
        payments = defaultdict(list)
        for row in receipts:
            payments[str(row["project_id"])].append(Decimal(str(row["amount"])))
        for row in source_rows:
            if row["status"] not in {"QUOTED", "APPROVED", "IN_PRODUCTION", "COMPLETED"}:
                continue
            phase = (row["status"], row["currency"])
            if row["total"] is None or row["currency"] is None:
                unknown[phase] += 1
                continue
            total = Decimal(row["total"])
            by_phase[phase].append(total)
            if row["status"] != "QUOTED":
                collected = money_sum(payments[str(row["id"])])
                balance = outstanding(total, collected)
                if balance > 0:
                    result.append(action("receivable", row["id"], row["code"], row["name"],
                        "Gestiona el saldo por cobrar", "La venta sellada tiene pagos pendientes. "
                        "Sin fecha de cobro declarada, no se presenta como vencida.",
                        "Abrir cobranza", f"/projects/{row['id']}?section=payments", amount=balance,
                        currency=row["currency"], balance_total=total, balance_collected=collected,
                        source="Total sellado de " + row["current_revision"] +
                        " menos pagos vigentes. No incluye recibos anulados."))
        for (status, currency) in sorted(set(by_phase) | set(unknown), key=str):
            values = by_phase[(status, currency)]
            pipeline.append({"phase": status, "currency": currency,
                "amount": str(money_sum(values)) if values else None,
                "count": len(values) + unknown[(status, currency)], "unknown_count": unknown[(status, currency)],
                "href": "/quotes?" + urlencode({"phase": status, "currency": currency or "unknown"}),
                "source": "Suma exacta del motor de los totales de las revisiones vigentes emitidas, "
                          "separada por moneda. No son ingresos ni una nueva cotización."})
    return result, pipeline


def position_actions(org_id):
    with commercial_backend():
        pending = rows("""
        SELECT p.id,p.project_id,p.position_index,p.location_tag,pr.code,pr.name,
               p.system_id,p.parametric_tree,p.color_interior,survey.state AS survey_state
        FROM public.project_positions p
        JOIN public.projects pr ON pr.id=p.project_id AND pr.org_id=p.org_id
        LEFT JOIN LATERAL (
            SELECT state FROM public.position_measurements m
            WHERE m.org_id=p.org_id AND m.position_id=p.id AND m.revision_code=pr.current_revision
            ORDER BY m.generation DESC LIMIT 1
        ) survey ON true
        WHERE p.org_id=%s AND pr.status='DRAFT'
          AND (survey.state<>'CONFIRMED' OR p.parametric_tree->>'version'='product-v2')
    """, [org_id])
    result = [action("position_blocked", row["id"], row["code"], row["name"],
        "Confirma las medidas de fabricación", f"Posición {row['position_index']} · "
        f"{row['location_tag'] or 'Sin ubicación'}: el levantamiento espera confirmación.",
        "Confirmar medidas", f"/projects/{row['project_id']}/positions/{row['id']}/edit",
        blocking=True, source="Última generación del levantamiento de la revisión actual.")
        for row in pending if row['survey_state'] is not None and row['survey_state'] != 'CONFIRMED']
    repository = SystemParamsRepository()
    authorities = {}
    for row in pending:
        tree = decoded(row['parametric_tree'])
        if tree.get('version') != 'product-v2':
            continue
        try:
            system = row['system_id']
            if system not in authorities:
                authorities[system] = (repository.load_visible(system,org_id),
                                      repository.load_coupler_articles(system,org_id))
            params, couplers = authorities[system]
            evaluation = evaluate_assembly_from_api(product=parse_product_model(tree),
                color=row['color_interior'],params=params,coupler_articles=couplers)
            if evaluation.status.value == 'VALID':
                continue
            # Engine reasons may contain English diagnostics, raw enums or
            # dimensions. The editor owns their positioned, formatted detail;
            # Hoy supplies a business cause and the exact resolver instead.
            reason = ('La geometría o la combinación elegida no es válida. Revisa Qué falta en la posición.'
                if evaluation.status.value == 'INVALID' else
                'Faltan definiciones o autoridad técnica para fabricar el conjunto. Revisa Qué falta en la posición.')
        except (SystemNotFound, UnsupportedCatalogContract, ValueError):
            reason = 'El diseño guardado requiere revisar su serie y la autoridad técnica vigente.'
        result.append(action('position_engine_blocked',row['id'],row['code'],row['name'],
            'Completa la definición de fabricación',
            f"Posición {row['position_index']} · {row['location_tag'] or 'Sin ubicación'}: {reason}",
            'Revisar posición',f"/projects/{row['project_id']}/positions/{row['id']}/edit",
            blocking=True,source='Evaluación del motor sobre el diseño guardado y el catálogo visible; no modifica la BOM ni una emisión.'))
    return result


def workshop_actions(org_id, role, today):
    result = []
    with documentary_backend():
        deliveries = rows("""
            SELECT d.id,d.order_id,d.status,d.scheduled_date,d.address,d.installer_name,
                   o.order_code,o.status AS order_status
            FROM public.deliveries d
            JOIN public.orders o ON o.id=d.order_id AND o.org_id=d.org_id
            WHERE d.org_id=%s AND d.scheduled_date<=%s AND o.status NOT IN ('INSTALLED','CANCELLED')
              AND (d.status IN ('SCHEDULED','ON_ROUTE','FAILED')
                   OR (d.status='DELIVERED' AND o.status='DISPATCHED'))
            ORDER BY d.scheduled_date,o.order_code,d.id
        """, [org_id, today])
        if role in {"OWNER", "WORKSHOP_MANAGER", "OPERATOR"}:
            orders = rows("""
                SELECT o.id,o.order_code,o.status::text,o.payload_json->>'remake_of' AS remake_of,
                    EXISTS(
                      SELECT 1 FROM jsonb_array_elements(COALESCE(
                        o.payload_json->'optimization'->'stock_reservations','[]'::jsonb)) r
                      WHERE COALESCE((r->>'short')::numeric,0)>0) AS short,
                    jsonb_typeof(o.payload_json->'optimization')='object' AS optimized,
                    o.payload_json ? 'packing' AS packed,
                    step.label,step.note,step.status AS step_status,
                    commitment.scheduled_date
                FROM public.orders o
                LEFT JOIN LATERAL (
                    SELECT label,note,status FROM public.production_steps s
                    WHERE s.org_id=o.org_id AND s.order_id=o.id AND s.status<>'DONE'
                    ORDER BY s.sequence LIMIT 1
                ) step ON true
                LEFT JOIN LATERAL (
                    SELECT scheduled_date FROM public.deliveries d
                    WHERE d.org_id=o.org_id AND d.order_id=o.id AND d.status IN ('SCHEDULED','ON_ROUTE')
                    ORDER BY scheduled_date LIMIT 1
                ) commitment ON true
                WHERE o.org_id=%s AND o.order_type='WORKSHOP_OT'
                  AND o.status NOT IN ('CANCELLED','INSTALLED','DISPATCHED')
                ORDER BY o.order_code
            """, [org_id])
        else:
            orders = []
    for row in deliveries:
        install = row["status"] == "DELIVERED"
        result.append(action("installation" if install else "delivery", row["id"], row["order_code"],
            row["address"], "Cierra la instalación" if install else "Completa la entrega comprometida",
            row["address"] + (f" · {row['installer_name']}" if row["installer_name"] else ""),
            "Abrir instalación" if install else "Abrir entrega",
            "/production?" + urlencode({"order": row["order_id"]}), due_on=row["scheduled_date"],
            blocking=row["status"] == "FAILED", source="Agenda de entrega y estado de la OT."))
    for row in orders:
        href = "/production?" + urlencode({"order": row["id"]})
        due = row["scheduled_date"]
        if row["status"] == "HOLD" or row["step_status"] == "BLOCKED":
            result.append(action("work_order_blocked", row["id"], row["order_code"], "Orden de trabajo",
                "Resuelve el bloqueo de la OT", row["note"] or "La estación mantiene la orden en espera.",
                "Resolver bloqueo", href, due_on=due, blocking=True,
                source="Estado de la OT y primera estación pendiente."))
        elif row["short"] and row['status'] != 'COMPLETED':
            result.append(action("work_order_shortage", row["id"], row["order_code"], "Orden de trabajo",
                "Completa el material de la OT", "La reserva del plan de corte registra material faltante.",
                "Revisar faltante", href, due_on=due, blocking=True,
                source="Reservas de stock de la optimización del motor."))
        elif not row["optimized"] and row["status"] in {"RELEASED", "IN_PROGRESS"}:
            result.append(action("work_order_plan", row["id"], row["order_code"], "Orden de trabajo",
                "Prepara el plan de corte", "La OT no tiene una optimización guardada.",
                "Optimizar corte", href, due_on=due, blocking=True, source="Plan sellado de la OT."))
        elif row["status"] == "COMPLETED":
            result.append(action("dispatch_ready", row["id"], row["order_code"], "Orden de trabajo",
                "Prepara el despacho", "Las estaciones terminaron. " +
                ("El embalaje está registrado." if row["packed"] else "Falta registrar el embalaje."),
                "Preparar despacho", href, due_on=due, source="Estaciones de producción y embalaje."))
        elif row["label"]:
            result.append(action("station_work", row["id"], row["order_code"], row["label"],
                "Continúa en " + row["label"].lower(), "Es la primera estación pendiente de esta OT.",
                "Abrir estación", href, due_on=due, source="Secuencia de estaciones del motor."))
        if row["remake_of"]:
            result.append(action("remake", row["id"], row["order_code"], "Reposición",
                "Completa la reposición", "Una reposición abierta espera continuar su secuencia de fabricación.",
                "Abrir reposición", href, due_on=due, blocking=True,
                source="Vínculo inmutable con la OT de origen."))
    return result


def daily_work(org_id, user_id, role):
    today = local_today(org_id)
    actions, pipeline = price_actions(org_id, user_id, role), []
    if role in COMMERCIAL_ROLES:
        commercial, pipeline = commercial_actions(org_id, today, role)
        actions.extend(commercial)
        actions.extend(position_actions(org_id))
    if role in {"OWNER", "WORKSHOP_MANAGER", "INSTALLER", "OPERATOR"}:
        actions.extend(workshop_actions(org_id, role, today))
    ordered = queue_order(actions, today=today)
    for item in ordered:
        item["consequence"] = consequence(
            date.fromisoformat(item["due_on"]) if item["due_on"] else None,
            today=today, blocking=item["blocking"])
    return {"today": today.isoformat(), "actions": ordered, "pipeline": pipeline,
            "source": "Compromisos vencidos, bloqueos, trabajo de hoy y seguimiento; orden determinista del motor."}
