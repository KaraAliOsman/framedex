"""Human access controls; emitted identities and client decisions stay immutable."""

from datetime import datetime, timedelta, timezone
import hashlib
from uuid import UUID

from documents.repository import DocumentaryError, documentary_backend, one, rows
from notifications import crypto
from portal import service


def _locked_link(*, org_id, project_id, approval_id):
    project = one("SELECT current_revision FROM public.projects WHERE id=%s AND org_id=%s FOR UPDATE",
                  [str(project_id), str(org_id)], "project_not_found")
    approval = one("SELECT a.*,v.revision_code FROM public.customer_approvals a "
        "JOIN public.project_versions v ON v.id=a.project_version_id AND v.org_id=a.org_id "
        "WHERE a.id=%s AND a.org_id=%s AND a.project_id=%s FOR UPDATE OF a",
        [str(approval_id), str(org_id), str(project_id)], "approval_not_found")
    if str(approval["revision_code"]) != str(project["current_revision"]):
        raise DocumentaryError("quote_link_stale")
    return approval


def change_deadline(*, org_id: UUID, project_id: UUID, approval_id: UUID, actor_id: UUID, data: dict):
    if not data["confirmed"]:
        raise DocumentaryError("quote_link_confirmation_required", detail="Confirma el cambio de vencimiento del enlace indicado.")
    now = datetime.now(timezone.utc)
    if not now < data["expires_at"] <= now + timedelta(days=365):
        raise DocumentaryError("quote_link_deadline_invalid", detail="Elige un vencimiento futuro dentro de 365 días. La vigencia comercial del PDF conserva su fecha sellada.")
    with documentary_backend():
        approval = _locked_link(org_id=org_id, project_id=project_id, approval_id=approval_id)
        if approval["status"] != "PENDING":
            raise DocumentaryError("approval_not_pending")
        current = one("SELECT private.quote_link_expires_at(%s,%s,%s) AS expires_at",
                      [str(approval_id), str(org_id), approval["expires_at"]])["expires_at"]
        if current == data["expires_at"]:
            return service.list_approvals(org_id=org_id, project_id=project_id)
        if current != data["expected_expires_at"]:
            raise DocumentaryError("quote_link_control_stale", detail="El vencimiento cambió. Recarga el historial antes de confirmar otro cambio.")
        one("INSERT INTO public.quote_link_deadlines(org_id,project_id,approval_id,expires_at,created_by) "
            "VALUES(%s,%s,%s,%s,%s) RETURNING id", [str(org_id), str(project_id), str(approval_id), data["expires_at"], str(actor_id)])
        return service.list_approvals(org_id=org_id, project_id=project_id)


def regenerate(*, org_id: UUID, project_id: UUID, approval_id: UUID, actor_id: UUID, role: str, confirmed: bool):
    if not confirmed:
        raise DocumentaryError("quote_link_confirmation_required", detail="Confirma la revocación del enlace anterior y la creación del nuevo.")
    with documentary_backend():
        approval = _locked_link(org_id=org_id, project_id=project_id, approval_id=approval_id)
        found = rows("SELECT * FROM public.quote_link_regenerations WHERE org_id=%s AND source_approval_id=%s",
                     [str(org_id), str(approval_id)])
        if found:
            saved = found[0]
            token = crypto.open_message(saved["token_ciphertext"], org_id=org_id, mail_id=saved["id"])["token"]
            fresh = one("SELECT expires_at FROM public.customer_approvals WHERE id=%s AND org_id=%s",
                        [str(saved["approval_id"]), str(org_id)])
            return {"token": token, "path": f"/cotizacion/{token}", "expires_at": fresh["expires_at"]}
        if approval["status"] not in ("PENDING", "REVOKED"):
            raise DocumentaryError("approval_not_pending")
        service.revoke_link(org_id=org_id, project_id=project_id, approval_id=approval_id, actor_id=actor_id)
        link = service.share_quote(org_id=org_id, project_id=project_id, actor_id=actor_id, role=role)
        fresh = one("SELECT id FROM public.customer_approvals WHERE org_id=%s AND project_id=%s AND token_hash=%s",
                    [str(org_id), str(project_id), hashlib.sha256(link["token"].encode()).hexdigest()])
        from uuid import uuid4
        receipt_id = uuid4()
        one("INSERT INTO public.quote_link_regenerations(id,org_id,project_id,source_approval_id,approval_id,token_ciphertext,created_by) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id", [str(receipt_id), str(org_id), str(project_id), str(approval_id), str(fresh["id"]),
            crypto.seal({"token": link["token"]}, org_id=org_id, mail_id=receipt_id), str(actor_id)])
        return {**link, "path": f"/cotizacion/{link['token']}"}
