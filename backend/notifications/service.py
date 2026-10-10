"""Seal mail beside the business event; commit dispatch before touching SMTP.

SMTP cannot prove exactly-once delivery. A crash after dispatch begins is
UNCERTAIN and requires a person to check the mailbox before retrying.
"""

from __future__ import annotations

import base64
from contextlib import contextmanager
import hashlib
import logging
from uuid import UUID, uuid4

from django.conf import settings
from django.core.validators import validate_email
from django.db import transaction
from django.utils import timezone

from automations.service import _service_claims
from documents.repository import DocumentaryError, decoded, documentary_backend, one, rows, write
from documents.storage import SupabaseDocumentStorage
from jobs.service import enqueue, job_backend
from notifications import adapters, crypto, templates

logger = logging.getLogger(__name__)
_PUBLIC = "id,kind,recipient,subject,project_id,created_at,state,attempt,delivered_at,error_code"


@contextmanager
def mail_backend():
    with job_backend(), _service_claims():
        yield


def public(row: dict) -> dict:
    return {key: row.get(key) for key in _PUBLIC.split(",")}


def _log(row: dict, event: str, *, actor_id=None, error_code=None):
    write(
        "INSERT INTO public.mail_attempts(org_id,mail_id,attempt,event,actor_id,error_code) VALUES(%s,%s,%s,%s,%s,%s)",
        [
            str(row["org_id"]),
            str(row["id"]),
            row["attempt"],
            event,
            str(actor_id) if actor_id else None,
            error_code,
        ],
    )


def _queue_job(row: dict):
    enqueue(
        org_id=UUID(str(row["org_id"])),
        job_type="mail.deliver",
        payload={"mail_id": str(row["id"])},
        idempotency_key=f"mail:{row['id']}:{row['attempt']}",
        max_attempts=1,
        created_by=UUID(str(row["created_by"])),
    )


def seal_mail(
    *,
    org_id: UUID,
    actor_id: UUID,
    event_key: str,
    kind: str,
    recipient: str,
    message: dict,
    project_id=None,
) -> dict:
    validate_email(recipient)
    mail_id = uuid4()
    encrypted = crypto.seal(message, org_id=org_id, mail_id=mail_id)
    with transaction.atomic(), mail_backend():
        row = one(
            "INSERT INTO public.mail_outbox(id,org_id,event_key,kind,recipient,subject,content_ciphertext,project_id,created_by) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(org_id,event_key) DO UPDATE SET event_key=EXCLUDED.event_key RETURNING *",
            [
                str(mail_id),
                str(org_id),
                event_key,
                kind,
                recipient,
                message["subject"],
                encrypted,
                str(project_id) if project_id else None,
                str(actor_id),
            ],
        )
        if row["state"] == "QUEUED":
            _queue_job(row)
    return public(row)


def _logo(org: dict):
    if not org.get("brand_logo_key"):
        return None
    from documents.renderers import _logo_uri

    uri = _logo_uri(org)
    if not uri:
        raise DocumentaryError(
            "brand_logo_integrity_failed",
            detail="El logo sellado no pudo verificarse. Revisa la identidad antes de enviar.",
        )
    media, data = uri[5:].split(";base64,", 1)
    return base64.b64decode(data), media


def _pdf_attachment(row: dict, filename: str) -> dict:
    content = SupabaseDocumentStorage().download_bounded(
        str(row["storage_object_key"]), 10 * 1024 * 1024
    )
    if hashlib.sha256(content).hexdigest() != str(row["file_sha256"]):
        raise DocumentaryError("mail_attachment_integrity_failed")
    return {"filename": filename, "data": base64.b64encode(content).decode()}


def quote_source(*, org_id: UUID, project_id: UUID, lock=False) -> dict:
    with documentary_backend():
        project = one(
            "SELECT status,current_revision FROM public.projects WHERE id=%s AND org_id=%s"
            + (" FOR UPDATE" if lock else ""),
            [str(project_id), str(org_id)],
            "project_not_found",
        )
        if str(project["status"]) not in {"QUOTED", "APPROVED"}:
            raise DocumentaryError(
                "quote_share_requires_quoted",
                detail="Emite la cotización antes de enviarla al cliente.",
            )
        version = one(
            "SELECT id,revision_code,snapshot_json FROM public.project_versions WHERE org_id=%s AND project_id=%s ORDER BY emitted_at DESC,id DESC LIMIT 1",
            [str(org_id), str(project_id)],
            "version_not_found",
        )
        if str(version["revision_code"]) != str(project["current_revision"]):
            raise DocumentaryError(
                "quote_link_stale",
                detail="La revisión emitida fue reemplazada. Emite la revisión vigente antes de enviar.",
            )
        documents = rows(
            "SELECT storage_object_key,file_sha256 FROM public.document_artifacts "
            "WHERE org_id=%s AND project_version_id=%s AND document_type='DOC-01' AND format='PDF'",
            [str(org_id), str(version["id"])],
        )
    snapshot = decoded(version["snapshot_json"])
    project = snapshot["project"]
    return {
        "id": str(version["id"]),
        "kind": "QUOTE",
        "organization": snapshot.get("organization", {}),
        "reference": f"{project['code']} · {version['revision_code']}",
        "recipient": project.get("client_email") or "",
        "document": documents[0] if documents else None,
        "document_name": "cotizacion.pdf",
        "body": f"{project['client_name']}:\nSu cotización de {project['name']} está disponible para revisión. Puede consultar el documento adjunto y responder en el portal.",
    }


def payment_source(*, org_id: UUID, project_id: UUID, payment_id: UUID) -> dict:
    with documentary_backend():
        receipt = one(
            "SELECT r.*, p.voided_at FROM public.payment_receipts r JOIN public.project_payments p ON p.id=r.payment_id AND p.org_id=r.org_id "
            "WHERE r.org_id=%s AND r.project_id=%s AND r.payment_id=%s",
            [str(org_id), str(project_id), str(payment_id)],
            "payment_receipt_not_found",
        )
        if receipt["voided_at"]:
            raise DocumentaryError(
                "mail_payment_voided",
                detail="El pago fue anulado. No se puede enviar una confirmación de pago vigente.",
            )
    payload = decoded(receipt["payload_json"])
    from documents.renderers import _money

    project = payload["project"]
    return {
        "id": str(receipt["id"]),
        "kind": "PAYMENT",
        "organization": payload.get("organization", {}),
        "reference": f"{project['code']} · {receipt['receipt_code']}",
        "recipient": project.get("client_email") or "",
        "receipt": receipt,
        "document": receipt,
        "document_name": "comprobante.pdf",
        "body": f"{project['client_name']}:\nSe registró su pago por {_money(payload['payment']['amount'], project['currency'])}. Se adjunta el comprobante emitido al registrar el pago.",
    }


def preview(source: dict) -> dict:
    message = templates.render(
        source["kind"],
        organization=source["organization"],
        reference=source["reference"],
        body=source["body"],
        logo=_logo(source["organization"]),
    )
    document = source["document"]
    return {
        "source_id": source["id"],
        "recipient": source["recipient"],
        "reference": source["reference"],
        "html": templates.preview_html(message),
        "provider": settings.MAIL_PROVIDER,
        "document_url": SupabaseDocumentStorage().signed_url(str(document["storage_object_key"]))
        if document
        else None,
        "document_sha256": str(document["file_sha256"]) if document else None,
        "document_name": source["document_name"],
    }


def _validate_target(source: dict, data: dict):
    if (
        data["expected_source_id"] != UUID(source["id"])
        or data["expected_recipient"] != source["recipient"]
    ):
        raise DocumentaryError(
            "mail_preview_stale",
            detail="Los datos cambiaron. Revisa de nuevo el destinatario y el documento antes de enviar.",
        )
    if not source["recipient"]:
        raise DocumentaryError(
            "mail_recipient_missing",
            detail="La emisión no tiene correo de cliente. Corrígelo y emite una nueva revisión.",
        )
    validate_email(source["recipient"])
    if not source["document"]:
        raise DocumentaryError(
            "mail_document_required",
            detail="Prepara y revisa el PDF sellado de esta emisión antes de enviar el correo.",
        )
    if data["expected_document_sha256"] != str(source["document"]["file_sha256"]):
        raise DocumentaryError(
            "mail_preview_stale",
            detail="El documento no coincide con la vista revisada. Abre el PDF de nuevo antes de enviar.",
        )


def _existing_send(*, org_id: UUID, project_id: UUID, event_key: str, source: dict):
    """Retry one confirmed intent, never silently reuse another send's payload."""
    with mail_backend():
        rows("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", [f"{org_id}:{event_key}"])
        found = rows(
            "SELECT * FROM public.mail_outbox WHERE org_id=%s AND event_key=%s",
            [str(org_id), event_key],
        )
    if not found:
        return None
    row = found[0]
    message = crypto.open_message(row["content_ciphertext"], org_id=org_id, mail_id=row["id"])
    if (
        str(row["project_id"]) != str(project_id)
        or row["recipient"] != source["recipient"]
        or message.get("source_id") != source["id"]
        or message.get("document_sha256") != str(source["document"]["file_sha256"])
    ):
        raise DocumentaryError(
            "mail_operation_key_conflict",
            detail="Este intento pertenece a otro envío. Cierra la vista y revisa un correo nuevo.",
        )
    return public(row)


def send_quote(*, org_id: UUID, project_id: UUID, actor_id: UUID, role: str, data: dict,
               document_token: str | None = None) -> dict:
    from portal.service import share_quote

    with transaction.atomic():
        source = quote_source(org_id=org_id, project_id=project_id, lock=True)
        _validate_target(source, data)
        event_key = f"quote:{data['operation_key']}"
        existing = _existing_send(
            org_id=org_id, project_id=project_id, event_key=event_key, source=source
        )
        if existing:
            return existing
        link = ({"token": document_token} if document_token is not None else
                share_quote(org_id=org_id, project_id=project_id, actor_id=actor_id, role=role))
        url = f"{settings.DEKOPEN_PUBLIC_APP_URL}/cotizacion/{link['token']}"
        message = templates.render(
            "QUOTE",
            organization=source["organization"],
            reference=source["reference"],
            body=source["body"],
            action_url=url,
            logo=_logo(source["organization"]),
        )
        message["attachments"] = [_pdf_attachment(source["document"], source["document_name"])]
        message["source_id"] = source["id"]
        message["document_sha256"] = str(source["document"]["file_sha256"])
        message["quote_token_hash"] = hashlib.sha256(str(link["token"]).encode()).hexdigest()
        message["version_id"] = source["id"]
        return seal_mail(
            org_id=org_id,
            actor_id=actor_id,
            event_key=event_key,
            kind="QUOTE",
            recipient=source["recipient"],
            message=message,
            project_id=project_id,
        )


def send_payment(
    *, org_id: UUID, project_id: UUID, payment_id: UUID, actor_id: UUID, data: dict
) -> dict:
    with transaction.atomic():
        source = payment_source(org_id=org_id, project_id=project_id, payment_id=payment_id)
        _validate_target(source, data)
        event_key = f"payment:{data['operation_key']}"
        existing = _existing_send(
            org_id=org_id, project_id=project_id, event_key=event_key, source=source
        )
        if existing:
            return existing
        message = templates.render(
            "PAYMENT",
            organization=source["organization"],
            reference=source["reference"],
            body=source["body"],
            logo=_logo(source["organization"]),
        )
        message["attachments"] = [_pdf_attachment(source["receipt"], "comprobante.pdf")]
        message["payment_id"] = str(payment_id)
        message["source_id"] = source["id"]
        message["document_sha256"] = str(source["document"]["file_sha256"])
        return seal_mail(
            org_id=org_id,
            actor_id=actor_id,
            event_key=event_key,
            kind="PAYMENT",
            recipient=source["recipient"],
            message=message,
            project_id=project_id,
        )


def internal_event(
    *,
    org_id: UUID,
    actor_id: UUID,
    kind: str,
    event_key: str,
    reference: str,
    body: str,
    project_id=None,
):
    """A notification fault never rolls back an approval or workshop event."""
    try:
        with transaction.atomic(), mail_backend():
            org = one(
                "SELECT notification_email,internal_mail_enabled FROM public.tenancy_organizations WHERE id=%s",
                [str(org_id)],
            )
            if not org["internal_mail_enabled"] or not org["notification_email"]:
                return
            message = templates.render(
                kind,
                organization={},
                reference=reference,
                body=body,
                action_url=f"{settings.DEKOPEN_PUBLIC_APP_URL}/projects/{project_id}"
                if project_id
                else f"{settings.DEKOPEN_PUBLIC_APP_URL}/production",
            )
            seal_mail(
                org_id=org_id,
                actor_id=actor_id,
                event_key=event_key,
                kind=kind,
                recipient=org["notification_email"],
                message=message,
                project_id=project_id,
            )
    except Exception as error:
        # Do not log exception text, mail content, address or a portal token.
        logger.warning("internal_mail_queue_failed kind=%s type=%s", kind, type(error).__name__)


def approval_event(*, approval: dict, version_id: str):
    try:
        with transaction.atomic(), mail_backend():
            version = one(
                "SELECT snapshot_json,revision_code FROM public.project_versions WHERE id=%s AND org_id=%s",
                [version_id, str(approval["org_id"])],
            )
            project = decoded(version["snapshot_json"])["project"]
            internal_event(
                org_id=UUID(str(approval["org_id"])),
                actor_id=UUID(str(approval["created_by"])),
                kind="APPROVAL",
                event_key=f"approval:{approval['id']}",
                reference=f"{project['code']} · {version['revision_code']}",
                body=f"El cliente aprobó la cotización de {project['name']}. Revisa la obra antes de liberar a producción.",
                project_id=approval["project_id"],
            )
    except Exception as error:
        logger.warning("approval_mail_queue_failed type=%s", type(error).__name__)


def blocked_event(*, org_id: UUID, actor_id: UUID, step_id: UUID):
    try:
        with transaction.atomic(), mail_backend():
            event = one(
                "SELECT e.id,e.order_id,e.payload,s.label,o.order_code FROM public.production_step_events e "
                "JOIN public.production_steps s ON s.id=e.step_id AND s.org_id=e.org_id "
                "JOIN public.orders o ON o.id=e.order_id AND o.org_id=e.org_id "
                "WHERE e.org_id=%s AND e.step_id=%s ORDER BY e.created_at DESC,e.id DESC LIMIT 1",
                [str(org_id), str(step_id)],
            )
            payload = decoded(event["payload"])
            cause = str(
                payload.get("note")
                or (
                    "Control de calidad rechazado."
                    if payload.get("qc_result") == "FAIL"
                    else "Sin causa registrada; revisa la estación."
                )
            )
            internal_event(
                org_id=org_id,
                actor_id=actor_id,
                kind="ORDER_BLOCKED",
                event_key=f"blocked:{event['id']}",
                reference=str(event["order_code"]),
                body=f"La estación {event['label']} quedó bloqueada.\nCausa: {cause}\nEl encargado debe resolver la causa antes de continuar.",
            )
    except Exception as error:
        logger.warning("blocked_mail_queue_failed type=%s", type(error).__name__)


def _check_live(row: dict, message: dict):
    if row["kind"] == "QUOTE":
        active = rows(
            "SELECT a.id FROM public.customer_approvals a JOIN public.projects p ON p.id=a.project_id AND p.org_id=a.org_id "
            "JOIN public.project_versions v ON v.id=a.project_version_id AND v.org_id=a.org_id "
            "WHERE a.org_id=%s AND a.token_hash=%s AND a.status IN ('PENDING','APPROVED') "
            "AND private.quote_link_expires_at(a.id,a.org_id,a.expires_at)>now() AND p.current_revision=v.revision_code",
            [str(row["org_id"]), message["quote_token_hash"]],
        )
        if not active:
            raise ValueError("mail_quote_link_inactive")
    if row["kind"] == "PAYMENT":
        active = rows(
            "SELECT id FROM public.project_payments WHERE org_id=%s AND id=%s AND voided_at IS NULL",
            [str(row["org_id"]), message["payment_id"]],
        )
        if not active:
            raise ValueError("mail_payment_voided")


def _finish(row: dict, state: str, error_code=None):
    with transaction.atomic(), mail_backend():
        updated = rows(
            "UPDATE public.mail_outbox SET state=%s,error_code=%s,delivered_at=%s WHERE id=%s AND org_id=%s AND state='DISPATCHING' AND attempt=%s RETURNING *",
            [
                state,
                error_code,
                timezone.now() if state == "SENT" else None,
                str(row["id"]),
                str(row["org_id"]),
                row["attempt"],
            ],
        )
        if updated:
            _log(row, state, error_code=error_code)
            return public(updated[0])
        # A reconciled/recovered attempt owns the row now. A late worker
        # cannot overwrite its state or claim a delivery it no longer owns.
        return public(
            one(
                "SELECT * FROM public.mail_outbox WHERE id=%s AND org_id=%s",
                [str(row["id"]), str(row["org_id"])],
            )
        )


def dispatch(*, org_id: UUID, mail_id: UUID) -> dict:
    with transaction.atomic(), mail_backend():
        row = one(
            "SELECT * FROM public.mail_outbox WHERE org_id=%s AND id=%s FOR UPDATE",
            [str(org_id), str(mail_id)],
            "mail_not_found",
        )
        if row["state"] != "QUEUED":
            return public(row)
        message = None
        preflight_error = None
        try:
            message = crypto.open_message(row["content_ciphertext"], org_id=org_id, mail_id=mail_id)
            _check_live(row, message)
            adapters.mime_message(message, mail_id=mail_id, recipient=row["recipient"])
        except Exception as error:
            code = str(error) if isinstance(error, ValueError) else None
            preflight_error = (
                code
                if code in {"mail_quote_link_inactive", "mail_payment_voided"}
                else "mail_preflight_failed"
            )
        row = one(
            "UPDATE public.mail_outbox SET state='DISPATCHING',attempt=attempt+1,dispatch_started_at=now(),error_code=NULL WHERE id=%s AND org_id=%s RETURNING *",
            [str(mail_id), str(org_id)],
        )
        _log(row, "DISPATCHING")
    # No enclosing database transaction may span this network operation.
    if preflight_error:
        return _finish(row, "FAILED", preflight_error)
    try:
        adapters.deliver(message, mail_id=mail_id, recipient=row["recipient"])
    except Exception:
        return _finish(row, "UNCERTAIN", "mail_delivery_uncertain")
    return _finish(row, "SENT")


def reconcile_stale(*, org_id: UUID):
    with transaction.atomic(), mail_backend():
        for row in rows(
            "UPDATE public.mail_outbox SET state='UNCERTAIN',error_code='mail_worker_interrupted' WHERE org_id=%s AND state='DISPATCHING' AND dispatch_started_at < now()-interval '2 minutes' RETURNING *",
            [str(org_id)],
        ):
            _log(row, "UNCERTAIN", error_code="mail_worker_interrupted")


def recent(*, org_id: UUID, project_id=None) -> list:
    reconcile_stale(org_id=org_id)
    with documentary_backend():
        return rows(
            "SELECT "
            + _PUBLIC
            + " FROM public.mail_outbox WHERE org_id=%s"
            + (" AND project_id=%s" if project_id else "")
            + " ORDER BY created_at DESC LIMIT 50",
            [str(org_id), *([str(project_id)] if project_id else [])],
        )


def recover(*, org_id: UUID, mail_id: UUID, actor_id: UUID, expected_attempt: int) -> dict:
    reconcile_stale(org_id=org_id)
    # Member-facing RLS proves this row is visible before elevating the write.
    with documentary_backend():
        one(
            "SELECT id FROM public.mail_outbox WHERE org_id=%s AND id=%s",
            [str(org_id), str(mail_id)],
            "mail_not_found",
        )
    with transaction.atomic(), mail_backend():
        row = one(
            "SELECT * FROM public.mail_outbox WHERE org_id=%s AND id=%s FOR UPDATE",
            [str(org_id), str(mail_id)],
            "mail_not_found",
        )
        if row["state"] not in {"FAILED", "UNCERTAIN"} or row["attempt"] != expected_attempt:
            raise DocumentaryError(
                "mail_recovery_conflict",
                detail="El envío cambió o ya está en proceso. Actualiza la bandeja antes de continuar.",
            )
        row = one(
            "UPDATE public.mail_outbox SET state='QUEUED',error_code=NULL WHERE id=%s AND org_id=%s RETURNING *",
            [str(mail_id), str(org_id)],
        )
        _log(row, "REQUEUED", actor_id=actor_id)
        _queue_job(row)
    return public(row)
