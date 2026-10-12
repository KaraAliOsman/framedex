"""Prepare a real AI letter; only a reviewed human send seals the outbox.

The provider writes a template without digits. All amounts/dates are inserted
after validation from the engine projection; no provider numeric truth exists.
"""

import hashlib
import json
import re

from django.db import transaction

from ai_gateway import service as gateway
from authentication.errors import contract_error
from documents.repository import decoded, documentary_backend
from documents.renderers import _cldate, _money
from notifications import templates
from notifications.service import _logo, mail_backend, public, seal_mail
from pricing.repository import one, rows
from projects import org_branding
from projects.payments import _deal, collection_projection
from projects.service import project_row

PLACEHOLDERS = {"cliente", "proyecto", "monto", "vencimiento"}


def bind_template(template, values):
    if not isinstance(template, str) or not 40 <= len(template) <= 2400:
        raise ValueError("collection_ai_template_invalid")
    keys = set(re.findall(r"\{([^{}]+)\}", template))
    if keys != PLACEHOLDERS or re.search(r"[\d$\[\]]|(?:CLP|USD|UF|%)", template):
        raise ValueError("collection_ai_numeric_authority_rejected")
    stripped = re.sub(r"\{[^{}]+\}", "", template)
    if "{" in stripped or "}" in stripped:
        raise ValueError("collection_ai_template_invalid")
    return re.sub(r"\{([^{}]+)\}", lambda match: values[match[1]], template)


def source(*, org_id, project_id, lock=False):
    project = project_row(org_id, project_id, lock=lock)
    deal = _deal(org_id, project_id, project)
    with documentary_backend():
        ledger = rows("SELECT id,amount,voided_at,simulated FROM public.project_payments "
                      "WHERE org_id=%s AND project_id=%s ORDER BY recorded_at,id", [str(org_id), str(project_id)])
    projection = collection_projection(org_id=org_id, project_id=project_id, deal=deal, payments=ledger)
    if not deal or not deal.get("sealed_revision") or str(project["current_revision"]) != deal["sealed_revision"]:
        raise contract_error(409, "collection_reminder_revision_invalid", "Emite la revisión vigente antes de preparar un recordatorio.")
    if projection.overdue <= 0 or projection.includes_simulation:
        raise contract_error(409, "collection_reminder_not_due", "No hay cuotas vencidas cobrables en este acuerdo. Los pagos simulados no se comunican como dinero real.")
    # Client identity belongs to the agreement, not to a mutable successor.
    with documentary_backend():
        version = one("SELECT snapshot_json FROM public.project_versions WHERE org_id=%s AND id=%s",
                      [str(org_id), deal["version_id"]])
    sealed = decoded(version["snapshot_json"])["project"]
    recipient = sealed.get("client_email") or ""
    if not recipient:
        raise contract_error(422, "collection_reminder_recipient_missing", "La revisión emitida no tiene correo de cliente. Completa los datos y emite una nueva revisión.")
    values = {"cliente": sealed["client_name"], "proyecto": sealed["name"],
              "monto": _money(projection.overdue, deal["currency"]),
              "vencimiento": _cldate(projection.oldest_due_on.isoformat())}
    fingerprint = hashlib.sha256(json.dumps({"revision": deal["sealed_revision"],
        "template_schema": 2,
        "version": deal["version_id"], "recipient": recipient, "values": values,
        "collected": str(projection.collected)}, sort_keys=True).encode()).hexdigest()
    return {"source_hash": fingerprint, "values": values, "recipient": recipient,
            "reference": f"{sealed['code']} · {deal['sealed_revision']}",
            "organization": org_branding.branding_for_snapshot(org_id=org_id)}


def _public(row):
    payload = decoded(row["payload_json"])
    with documentary_backend():
        sent = rows("SELECT id FROM public.mail_outbox WHERE org_id=%s AND event_key=%s",
                    [str(row["org_id"]), f"collection:{row['id']}"])
    return {"id": str(row["id"]), "recipient": payload["recipient"],
            "body": payload["body"], "reference": payload["reference"],
            "prepared_by_ai": True, "sent": bool(sent)}


def prepare(*, org_id, project_id, actor_id):
    current = source(org_id=org_id, project_id=project_id)
    with documentary_backend():
        existing = rows("SELECT * FROM public.collection_reminders WHERE org_id=%s AND project_id=%s AND source_hash=%s",
                        [str(org_id), str(project_id), current["source_hash"]])
    if existing:
        return _public(existing[0])
    envelope = gateway.invoke(org_id=org_id, user_id=actor_id, capability="context_assist",
        operation_key=f"collection:{project_id}:{current['source_hash']}", tool_name="collection_reminder",
        input_payload={"purpose": "recordatorio de cuotas vencidas", "template_schema": 2},
        provider_options={"json_output": True, "system":
            'Devuelve solo JSON {"template":"..."}. Redacta un correo breve en español de Chile, profesional, '
            'tratando de usted. Solicita revisar un pago pendiente sin amenazas. Incluye exactamente los marcadores '
            '{cliente}, {proyecto}, {monto} y {vencimiento}. No escribas cifras, porcentajes, monedas, '
            'plazos propios, URLs ni datos supuestos. No incluyas asunto, firma, corchetes ni marcadores '
            'de nombre/cargo/contacto. Termina con Gracias. Se sustituyen las cuatro variables con autoridades del sistema después.'})
    try:
        template = json.loads(envelope["output"])["template"]
        body = bind_template(template, current["values"])
    except (KeyError, TypeError, ValueError):
        raise contract_error(502, "collection_reminder_ai_invalid", "La IA no devolvió un borrador verificable. Reintenta preparar el mensaje; no se envió correo.") from None
    with transaction.atomic():
        fresh = source(org_id=org_id, project_id=project_id, lock=True)
        if fresh["source_hash"] != current["source_hash"]:
            raise contract_error(409, "collection_reminder_stale", "El saldo cambió mientras se preparaba el mensaje. Revisa la cobranza y prepara de nuevo.")
        with documentary_backend():
            inserted = rows("INSERT INTO public.collection_reminders(org_id,project_id,source_hash,payload_json,audit_id,actor_id) "
                      "VALUES(%s,%s,%s,%s::jsonb,%s,%s) ON CONFLICT(org_id,project_id,source_hash) DO NOTHING RETURNING *",
                      [str(org_id), str(project_id), current["source_hash"], json.dumps({**current, "body": body}),
                       envelope["audit_id"], str(actor_id)])
            row = inserted[0] if inserted else one("SELECT * FROM public.collection_reminders WHERE org_id=%s AND project_id=%s AND source_hash=%s",
                [str(org_id), str(project_id), current["source_hash"]])
    return _public(row)


def send(*, org_id, project_id, actor_id, data):
    if not data["confirmed"]:
        raise contract_error(400, "collection_reminder_confirmation_required", "Revisa el mensaje y confirma su envío.")
    event_key = f"collection:{data['reminder_id']}"
    with transaction.atomic():
        project_row(org_id, project_id, lock=True)
        with documentary_backend():
            row = one("SELECT * FROM public.collection_reminders WHERE id=%s AND org_id=%s AND project_id=%s",
                      [str(data["reminder_id"]), str(org_id), str(project_id)], "collection_reminder_not_found")
        with mail_backend():
            existing = rows("SELECT * FROM public.mail_outbox WHERE org_id=%s AND event_key=%s",
                            [str(org_id), event_key])
        if existing:
            return public(existing[0])
        current = source(org_id=org_id, project_id=project_id)
        if row["source_hash"] != current["source_hash"]:
            raise contract_error(409, "collection_reminder_stale", "El saldo o el acuerdo cambió. Prepara un recordatorio nuevo antes de enviarlo.")
        payload = decoded(row["payload_json"])
        message = templates.render("COLLECTION", organization=payload["organization"],
            reference=payload["reference"], body=payload["body"], logo=_logo(payload["organization"]))
        message["collection_reminder_id"] = str(row["id"])
        return seal_mail(org_id=org_id, actor_id=actor_id, event_key=event_key, kind="COLLECTION",
            recipient=payload["recipient"], message=message, project_id=project_id)
