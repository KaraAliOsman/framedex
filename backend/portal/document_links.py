"""One encrypted, revocable capability per immutable PDF/revision slot."""

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from uuid import UUID, uuid4

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings

from documents.repository import DocumentaryError, one, rows


def _cipher():
    return AESGCM(hashlib.sha256(("document-link:v1:" + settings.MAIL_ENCRYPTION_KEY).encode()).digest())


def document_portal_url(*, org_id: UUID, version: dict, actor_id: UUID) -> str:
    """Caller holds the documentary role, transaction and artifact-slot lock.

    A failed artifact upload rolls this creation back. Existing artifact slots
    return before this function and never acquire a different QR.
    """
    version_id = str(version["id"])
    found = rows("SELECT id,token_ciphertext FROM public.document_portal_links WHERE org_id=%s AND project_version_id=%s", [str(org_id), version_id])
    if found:
        row = found[0]
        raw = base64.b64decode(row["token_ciphertext"], validate=True)
        aad = f"document-link:v1:{org_id}:{version_id}:{row['id']}".encode()
        token = _cipher().decrypt(raw[:12], raw[12:], aad).decode()
    else:
        token = secrets.token_urlsafe(32)
        approval = one(
            "INSERT INTO public.customer_approvals(org_id,project_id,project_version_id,token_hash,expires_at,created_by,link_source) "
            "VALUES(%s,%s,%s,%s,%s,%s,'DOCUMENT') RETURNING id",
            [str(org_id), str(version["project_id"]), version_id, hashlib.sha256(token.encode()).hexdigest(),
             datetime.now(timezone.utc) + timedelta(days=30), str(actor_id)],
        )
        row_id = uuid4()
        nonce = secrets.token_bytes(12)
        aad = f"document-link:v1:{org_id}:{version_id}:{row_id}".encode()
        ciphertext = base64.b64encode(nonce + _cipher().encrypt(nonce, token.encode(), aad)).decode()
        one("INSERT INTO public.document_portal_links(id,org_id,project_version_id,approval_id,token_ciphertext) VALUES(%s,%s,%s,%s,%s) RETURNING id",
            [str(row_id), str(org_id), version_id, str(approval["id"]), ciphertext])
    from urllib.parse import urlparse
    base = settings.DEKOPEN_PUBLIC_APP_URL.rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme not in ("https", "http") or not parsed.netloc:
        raise DocumentaryError("document_portal_url_invalid")
    return f"{base}/cotizacion/{token}"
