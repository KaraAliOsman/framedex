"""One human intent seals the exact reviewed DOC-01, activates its QR and queues mail.

All callers hold an outer REPEATABLE READ transaction with verified tenant claims.
The preview has no customer_approvals row, so its printed QR is inactive until issue.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from contextlib import contextmanager
from contextvars import ContextVar
import logging
import secrets
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from dekopen_engine.documentary_canonical import (
    documentary_canonical_json_v1,
    file_sha256,
    snapshot_sha256_v1,
)
from dekopen_engine.quotation import payment_amounts
from documents.preferences import document_preferences
from documents.renderers import render_pdf_document
from documents.repository import DocumentaryError, decoded, documentary_backend, one, rows
from documents.service import compose_revision, lock_revision_inputs, persist_revision
from documents.storage import SupabaseDocumentStorage
from notifications import crypto
from notifications.service import public as mail_public, send_quote
from portal.document_links import document_portal_url, portal_url
from projects.rut import valid_rut
from pricing.repository import commercial_backend

logger = logging.getLogger(__name__)
_provisional = ContextVar("quotation_provisional_uploads", default=None)


@contextmanager
def provisional_uploads():
    """Remove only fresh attempt-owned objects if upload or DB commit fails."""
    files = []
    context = _provisional.set(files)
    try:
        yield
    except BaseException:
        for storage, key in reversed(files):
            try:
                storage.delete_object(key)
            except Exception:
                # Capabilities and storage paths never enter diagnostic logs.
                logger.warning("quotation_provisional_cleanup_failed")
        raise
    finally:
        _provisional.reset(context)


def _upload(storage, key, content):
    files = _provisional.get()
    if files is not None:
        files.append((storage, key))
    storage.upload_immutable(key, content, "application/pdf")


def _requirements(snapshot: dict) -> None:
    project = snapshot["project"]
    terms = project.get("commercial_terms") or {}
    missing = []
    for field, label in [
        ("client_name", "Nombre del cliente"),
        ("delivery_address", "Dirección de obra"),
    ]:
        if not str(project.get(field) or "").strip():
            missing.append({"field": field, "label": label})
    if not valid_rut(project.get("client_rut")):
        missing.append({"field": "client_rut", "label": "RUT válido del cliente (módulo 11)"})
    try:
        validate_email(project.get("client_email") or "")
    except ValidationError:
        missing.append({"field": "client_email", "label": "Correo válido del cliente"})
    until = project.get("quotation_valid_until")
    today = datetime.now(ZoneInfo("America/Santiago")).date()
    if not until or date.fromisoformat(str(until)) < today:
        missing.append({"field": "quotation_valid_until", "label": "Vigencia desde hoy"})
    schedule = terms.get("payment_schedule") or []
    if not str(project.get("payment_terms") or "").strip() or not schedule:
        missing.append({"field": "payment_schedule", "label": "Condiciones y calendario de pagos"})
    else:
        # The engine validates shares and assigns rounding; text never supplies money.
        payment_amounts(
            Decimal(str(project["total_price_gross"])),
            [Decimal(str(item["share"])) for item in schedule],
            project["currency"],
        )
        if any(not str(item.get("label") or "").strip() for item in schedule):
            missing.append({"field": "payment_schedule", "label": "Nombre de cada hito de pago"})
    for field, label in [
        ("delivery_text", "Plazo de entrega"),
        ("installation_text", "Alcance de instalación"),
        ("exclusions", "Exclusiones"),
        ("warranty", "Garantía"),
    ]:
        if not str(terms.get(field) or "").strip():
            missing.append({"field": field, "label": label})
    if missing:
        raise DocumentaryError(
            "quotation_fields_required",
            detail=f"No se puede preparar el PDF: falta {missing[0]['label'].lower()}. Completa el campo indicado.",
            extra={"missing_fields": missing},
        )


def save_customer(*, org_id: UUID, project_id: UUID, data: dict) -> dict:
    """Before issuance, complete only the customer/address declaration, never pricing.

    Generic project edits keep their historical pricing lock. This narrow writer
    cannot alter geometry, computed values, issued revisions or price evidence.
    """
    if not valid_rut(data["client_rut"]):
        raise DocumentaryError(
            "quotation_client_rut_invalid",
            detail="El RUT del cliente no coincide con su dígito verificador. Revisa el RUT; se valida con módulo 11.",
        )
    with commercial_backend():
        project = one(
            "SELECT * FROM public.projects WHERE id=%s AND org_id=%s FOR UPDATE",
            [str(project_id), str(org_id)],
            "project_not_found",
        )
        with documentary_backend():
            sealed = rows(
                "SELECT id FROM public.project_versions WHERE project_id=%s AND org_id=%s AND revision_code=%s",
                [str(project_id), str(org_id), project["current_revision"]],
            )
        if project["status"] != "DRAFT" or sealed:
            raise DocumentaryError(
                "revision_not_available",
                detail="La revisión ya está sellada. Abre una sucesora para cambiar cliente o dirección de obra.",
            )
        if project["updated_at"] != data["expected_updated_at"]:
            raise DocumentaryError(
                "quotation_preview_stale",
                detail="Otra persona actualizó la obra. Recarga el proyecto antes de guardar cliente y dirección.",
            )
        row = one(
            "UPDATE public.projects SET client_name=%s,client_rut=%s,client_email=%s,delivery_address=%s,updated_at=clock_timestamp() "
            "WHERE id=%s AND org_id=%s RETURNING updated_at",
            [
                data["client_name"],
                data["client_rut"],
                data["client_email"],
                data["delivery_address"],
                str(project_id),
                str(org_id),
            ],
        )
        return {"updated_at": row["updated_at"]}


def _preview_row(*, org_id: UUID, project_id: UUID, actor_id: UUID, preview_id: UUID) -> dict:
    return one(
        "SELECT * FROM public.quotation_previews WHERE id=%s AND org_id=%s AND project_id=%s AND created_by=%s",
        [str(preview_id), str(org_id), str(project_id), str(actor_id)],
        "quotation_preview_not_found",
    )


def _preview_public(row: dict) -> dict:
    snapshot = decoded(row["snapshot_json"])
    project = snapshot["project"]
    return {
        "id": row["id"],
        "revision_code": row["revision_code"],
        "snapshot_sha256": row["snapshot_sha256"],
        "bom_hash": row["bom_hash"],
        "file_sha256": row["file_sha256"],
        "byte_size": row["byte_size"],
        "document_date": row["document_date"],
        "expires_at": row["expires_at"],
        "recipient": project["client_email"],
        "client_name": project["client_name"],
        "currency": project["currency"],
        "total_price_gross": str(project["total_price_gross"]),
        "production_allowed": snapshot["production_allowed"],
        "documentary_complete": snapshot["documentary_complete"],
        "valid_until": str(project["quotation_valid_until"]),
        "pdf_url": SupabaseDocumentStorage().signed_url(
            str(row["storage_object_key"]), expires_in=300
        ),
    }


def prepare_preview(
    *, org_id: UUID, actor_id: UUID, project_id: UUID, pricing_operation_id: UUID
) -> dict:
    lock_revision_inputs(
        org_id=org_id, project_id=project_id, pricing_operation_id=pricing_operation_id
    )
    now = datetime.now(timezone.utc)
    prepared = compose_revision(
        org_id=org_id,
        actor_id=actor_id,
        project_id=project_id,
        pricing_operation_id=pricing_operation_id,
        sealed_at=now,
        allow_incomplete_workshop=True,
    )
    snapshot = prepared.snapshot
    _requirements(snapshot)
    snapshot_hash = snapshot_sha256_v1(snapshot)
    preview_id, token = uuid4(), secrets.token_urlsafe(32)
    content, _ = render_pdf_document(
        "DOC-01", decoded(documentary_canonical_json_v1(snapshot).decode()), pdf_identifier=snapshot_hash, portal_url=portal_url(token)
    )
    content_hash = file_sha256(content)
    object_key = f"org_{org_id}/projects/{project_id}/previews/{preview_id}/{content_hash}.pdf"
    storage = SupabaseDocumentStorage()
    _upload(storage, object_key, content)
    with documentary_backend():
        prefs = document_preferences(snapshot["organization"]["document_preferences"])
        expires_at = now + timedelta(minutes=prefs["quotation_preview_minutes"])
        row = one(
            "INSERT INTO public.quotation_previews(id,org_id,project_id,pricing_operation_id,created_by,revision_code,"
            "snapshot_json,snapshot_sha256,bom_hash,storage_object_key,file_sha256,byte_size,token_ciphertext,document_date,expires_at) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *",
            [
                str(preview_id),
                str(org_id),
                str(project_id),
                str(pricing_operation_id),
                str(actor_id),
                snapshot["revision"],
                documentary_canonical_json_v1(snapshot).decode(),
                snapshot_hash,
                snapshot["bom_hash"],
                object_key,
                content_hash,
                len(content),
                crypto.seal({"token": token}, org_id=org_id, mail_id=preview_id),
                now,
                expires_at,
            ],
        )
        return _preview_public(row)


def preview_access(*, org_id: UUID, actor_id: UUID, project_id: UUID, preview_id: UUID) -> dict:
    with documentary_backend():
        row = _preview_row(
            org_id=org_id, project_id=project_id, actor_id=actor_id, preview_id=preview_id
        )
        if row["expires_at"] <= datetime.now(timezone.utc):
            raise DocumentaryError(
                "quotation_preview_expired",
                detail="La revisión del PDF venció. Prepara y revisa una vista previa nueva.",
            )
        return _preview_public(row)


def _issue_public(receipt: dict, preview: dict, *, org_id: UUID, token: str, created: bool) -> dict:
    with documentary_backend():
        version = one(
            "SELECT revision_code,bom_hash,snapshot_sha256,production_allowed,documentary_complete,emitted_at "
            "FROM public.project_versions WHERE id=%s AND org_id=%s",
            [str(receipt["project_version_id"]), str(org_id)],
        )
        mail = one(
            "SELECT id,kind,recipient,subject,project_id,created_at,state,attempt,delivered_at,error_code "
            "FROM public.mail_outbox WHERE id=%s AND org_id=%s",
            [str(receipt["mail_id"]), str(org_id)],
        )
    return {
        **version,
        "id": receipt["project_version_id"],
        "created": created,
        "pricing_operation_id": preview["pricing_operation_id"],
        "artifact_id": receipt["artifact_id"],
        "approval_id": receipt["approval_id"],
        "path": f"/cotizacion/{token}",
        "file_sha256": preview["file_sha256"],
        "mail": mail_public(mail),
    }


def issue_preview(*, org_id: UUID, actor_id: UUID, project_id: UUID, role: str, data: dict) -> dict:
    if not data["confirmed"]:
        raise DocumentaryError("documentary_freeze_confirmation_required")
    with documentary_backend():
        preview = _preview_row(
            org_id=org_id, project_id=project_id, actor_id=actor_id, preview_id=data["preview_id"]
        )
        snapshot = decoded(preview["snapshot_json"])
        if (
            data["expected_document_sha256"] != str(preview["file_sha256"])
            or data["expected_snapshot_sha256"] != str(preview["snapshot_sha256"])
            or data["expected_recipient"] != snapshot["project"]["client_email"]
        ):
            raise DocumentaryError(
                "quotation_preview_stale",
                detail="La confirmación no coincide con el PDF revisado. Revisa una vista previa nueva.",
            )
        token = crypto.open_message(
            preview["token_ciphertext"], org_id=org_id, mail_id=preview["id"]
        )["token"]
    lock_revision_inputs(
        org_id=org_id, project_id=project_id, pricing_operation_id=preview["pricing_operation_id"]
    )
    with documentary_backend():
        rows(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
            [f"quotation-issue:{preview['id']}"],
        )
        receipts = rows(
            "SELECT * FROM public.quotation_issues WHERE org_id=%s AND preview_id=%s",
            [str(org_id), str(preview["id"])],
        )
        if receipts:
            return _issue_public(receipts[0], preview, org_id=org_id, token=token, created=False)
    if preview["expires_at"] <= datetime.now(timezone.utc):
        raise DocumentaryError(
            "quotation_preview_expired",
            detail="La revisión del PDF venció. Prepara y revisa una vista previa nueva.",
        )
    prepared = compose_revision(
        org_id=org_id,
        actor_id=actor_id,
        project_id=project_id,
        pricing_operation_id=preview["pricing_operation_id"],
        sealed_at=preview["document_date"],
        allow_incomplete_workshop=True,
    )
    _requirements(prepared.snapshot)
    if snapshot_sha256_v1(prepared.snapshot) != str(preview["snapshot_sha256"]):
        raise DocumentaryError(
            "quotation_preview_stale",
            detail="La obra, los precios o las condiciones cambiaron desde la vista previa. Revisa el PDF nuevo antes de emitir.",
        )
    storage = SupabaseDocumentStorage()
    content = storage.download(str(preview["storage_object_key"]))
    if len(content) != preview["byte_size"] or file_sha256(content) != str(preview["file_sha256"]):
        raise DocumentaryError(
            "quotation_preview_integrity_failed",
            detail="El PDF revisado no conserva su huella. Prepara una vista previa nueva.",
        )
    version = persist_revision(prepared=prepared)
    version_id = UUID(version["id"])
    object_key = f"org_{org_id}/projects/{project_id}/{version['revision_code']}/{version_id}/doc-01_pdf_{preview['file_sha256']}.pdf"
    _upload(storage, object_key, content)
    with documentary_backend():
        document_portal_url(
            org_id=org_id,
            actor_id=actor_id,
            version={"id": version_id, "project_id": project_id},
            prepared_token=token,
        )
        approval = one(
            "SELECT approval_id FROM public.document_portal_links WHERE org_id=%s AND project_version_id=%s",
            [str(org_id), str(version_id)],
        )
        artifact = one(
            "INSERT INTO public.document_artifacts(org_id,project_id,project_version_id,artifact_scope,artifact_scope_id,"
            "document_type,format,bom_hash,revision_snapshot_sha256,storage_bucket,storage_object_key,file_sha256,media_type,byte_size,created_by) "
            "VALUES(%s,%s,%s,'PROJECT_REVISION',%s,'DOC-01','PDF',%s,%s,'documents',%s,%s,'application/pdf',%s,%s) RETURNING id",
            [
                str(org_id),
                str(project_id),
                str(version_id),
                str(version_id),
                version["bom_hash"],
                version["snapshot_sha256"],
                object_key,
                preview["file_sha256"],
                len(content),
                str(actor_id),
            ],
        )
    mail = send_quote(
        org_id=org_id,
        actor_id=actor_id,
        project_id=project_id,
        role=role,
        document_token=token,
        data={
            "operation_key": preview["id"],
            "expected_source_id": version_id,
            "expected_recipient": data["expected_recipient"],
            "expected_document_sha256": preview["file_sha256"],
        },
    )
    with documentary_backend():
        receipt = one(
            "INSERT INTO public.quotation_issues(org_id,project_id,preview_id,project_version_id,artifact_id,approval_id,mail_id,created_by) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *",
            [
                str(org_id),
                str(project_id),
                str(preview["id"]),
                str(version_id),
                str(artifact["id"]),
                str(approval["approval_id"]),
                str(mail["id"]),
                str(actor_id),
            ],
        )
        return _issue_public(receipt, preview, org_id=org_id, token=token, created=True)
