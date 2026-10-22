"""Owner administration and real document previews, under verified claims."""

from copy import deepcopy
from datetime import timedelta
import hashlib
import secrets
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import httpx
from django.conf import settings
from django.utils import timezone

from authentication.errors import contract_error
from dekopen_engine.documentary_canonical import snapshot_sha256_v1
from documents.artifacts import _revision_snapshot
from documents.preferences import document_preferences
from documents.renderers import render_pdf_document
from documents.repository import documentary_backend
from notifications import service as mail, templates
from pricing.repository import rows
from projects import org_branding
from projects.rut import valid_rut


def get_company(org_id):
    return rows("SELECT * FROM private.company_settings(%s)", [org_id])[0]


def save_company(org_id, data):
    current = get_company(org_id)
    if data["tax_id"] != current["tax_id"] and not valid_rut(data["tax_id"]):
        raise contract_error(
            400, "company_rut_invalid", "Revisa el RUT legal y su dígito verificador."
        )
    rows(
        "SELECT private.save_company(%s,%s,%s,%s,%s,%s)",
        [
            org_id,
            data["name"],
            data["tax_id"],
            data["currency"],
            data["require_mfa"],
            data["expected_updated_at"],
        ],
    )
    return get_company(org_id)


def users(org_id):
    return {
        "items": rows("SELECT * FROM private.company_users(%s)", [org_id]),
        "invitations": rows(
            "SELECT id,email,role,created_at,expires_at,accepted_at,revoked_at,mail_id "
            "FROM public.organization_invitations WHERE org_id=%s ORDER BY created_at DESC,id",
            [org_id],
        ),
    }


def change_user(org_id, identity, data):
    rows(
        "SELECT private.change_company_user(%s,%s,%s,%s,%s)",
        [org_id, identity, data["role"], data["is_active"], data["expected_updated_at"]],
    )
    return users(org_id)


def provision_invited_account(email):
    """Provision authentication only; no membership until verified acceptance."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise contract_error(
            503, "invitation_auth_not_configured", "Configura Supabase antes de invitar usuarios."
        )
    try:
        response = httpx.post(
            settings.SUPABASE_URL.rstrip("/") + "/auth/v1/admin/users",
            headers={
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": "Bearer " + settings.SUPABASE_SERVICE_ROLE_KEY,
            },
            json={"email": email, "email_confirm": False},
            timeout=15,
        )
    except httpx.HTTPError as error:
        raise contract_error(
            503,
            "invitation_auth_unavailable",
            "No se pudo preparar el acceso. Reintenta la invitación.",
        ) from error
    if response.status_code >= 400:
        try:
            code = response.json().get("error_code")
        except ValueError:
            code = None
        if code not in ("email_exists", "user_already_exists"):
            raise contract_error(
                503,
                "invitation_auth_unavailable",
                "No se pudo preparar el acceso. Reintenta la invitación.",
            )


def invite(org_id, actor_id, data):
    # Existing operation reuses its sealed mail; never expose/regenerate capability.
    token = secrets.token_urlsafe(32)
    digest = hashlib.sha256(token.encode()).hexdigest()
    identity = rows(
        "SELECT private.create_company_invitation(%s,%s,%s,%s,%s) AS id",
        [org_id, data["operation_key"], data["email"], data["role"], digest],
    )[0]["id"]
    existing = rows(
        "SELECT mail_id FROM public.organization_invitations WHERE org_id=%s AND id=%s",
        [org_id, identity],
    )[0]
    if not existing["mail_id"]:
        provision_invited_account(data["email"])
        origin = settings.BILLING_FRONTEND_ORIGIN.rstrip("/")
        message = templates.render(
            "INVITATION",
            organization={},
            reference=get_company(org_id)["name"],
            body="Te invitaron a trabajar en esta empresa. Entra con el correo invitado y revisa el rol antes de aceptar. El enlace vence en siete días.",
            action_url=origin + "/invitation?" + urlencode({"token": token}),
        )
        message["invitation_id"] = str(identity)
        record = mail.seal_mail(
            org_id=org_id,
            actor_id=actor_id,
            event_key=f"invitation:{identity}",
            kind="INVITATION",
            recipient=data["email"],
            message=message,
        )
        rows(
            "SELECT private.link_company_invitation_mail(%s,%s,%s)",
            [org_id, identity, record["id"]],
        )
    return users(org_id)


def revoke_invitation(org_id, identity):
    rows("SELECT private.revoke_company_invitation(%s,%s)", [org_id, identity])
    return users(org_id)


def invitation(token):
    records = rows(
        "SELECT * FROM private.inspect_company_invitation(%s)",
        [hashlib.sha256(token.encode()).hexdigest()],
    )
    if not records:
        raise contract_error(
            404,
            "invitation_unavailable",
            "La invitación no está disponible para este correo o ya venció. Pide un nuevo enlace al dueño.",
        )
    return records[0]


def accept_invitation(token):
    invitation(token)
    identity = rows(
        "SELECT private.accept_company_invitation(%s) AS id",
        [hashlib.sha256(token.encode()).hexdigest()],
    )[0]["id"]
    return {"organization_id": identity}


def preview(org_id, data):
    with documentary_backend():
        _, reference = _revision_snapshot(data["version_id"], org_id)
        snapshot = deepcopy(reference)
        organization = org_branding.branding_for_snapshot(org_id=org_id)
    draft = data.get("branding", {})
    organization.update(
        {
            key: value
            for key, value in draft.items()
            if key
            not in (
                "notification_email",
                "internal_mail_enabled",
                "expected_updated_at",
                "document_preferences",
            )
        }
    )
    prefs = document_preferences(
        {
            **document_preferences(organization.get("document_preferences")),
            **draft.get("document_preferences", {}),
        }
    )
    organization["document_preferences"] = prefs
    from projects.brand_color import snapshot_preferences

    organization.update(snapshot_preferences(organization))
    snapshot["organization"] = organization
    snapshot["project"]["commercial_terms"] = prefs["commercial_terms"]
    snapshot["project"]["quotation_valid_days"] = prefs["quotation_valid_days"]
    snapshot["project"]["quotation_valid_until"] = (
        timezone.localdate(timezone=ZoneInfo("America/Santiago"))
        + timedelta(days=prefs["quotation_valid_days"])
    ).isoformat()
    # The preview always retains the exact sealed price and currency of reference.
    snapshot["quotation_alternatives"] = []
    content, _ = render_pdf_document(
        "DOC-01", snapshot, pdf_identifier=snapshot_sha256_v1(snapshot)
    )
    return content
