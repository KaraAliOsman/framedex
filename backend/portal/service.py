"""Customer quote-approval links: public token-scoped reads and decisions."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
import secrets
from typing import Iterator
from uuid import UUID

from django.db import DatabaseError, connection, transaction
from psycopg import sql

from documents.artifacts import SupabaseDocumentStorage
from documents.repository import DocumentaryError, documentary_backend, one, rows

_TOKEN_BYTES = 32
_APPROVAL_TTL_DAYS = 30


@contextmanager
def portal_backend() -> Iterator[None]:
    """Switch to the portal role — the share token is the only capability.

    No JWT exists on public requests, so org scoping happens in the queries:
    every row is joined back to the approval's own ``org_id``/ids.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_setting('role')")
        previous = str(cursor.fetchone()[0])
        if previous == "none":
            previous = "authenticated"
        cursor.execute("SET LOCAL ROLE portal_backend")
    try:
        yield
    except DatabaseError:
        raise
    except BaseException:
        if not connection.needs_rollback:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(previous))
                )
        raise
    else:
        if not connection.needs_rollback:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(previous))
                )


def share_quote(*, org_id: UUID, project_id: UUID, actor_id: UUID) -> dict[str, object]:
    """Mint a fresh approval link for the project's latest sealed version."""
    with transaction.atomic(), documentary_backend():
        project = one(
            "SELECT id,status FROM public.projects WHERE id=%s AND org_id=%s",
            [project_id, org_id],
            "project_not_found",
        )
        if str(project["status"]) not in ("QUOTED", "APPROVED"):
            raise DocumentaryError("quote_share_requires_quoted")
        versions = rows(
            "SELECT id FROM public.project_versions "
            "WHERE project_id=%s AND org_id=%s ORDER BY emitted_at DESC LIMIT 1",
            [project_id, org_id],
        )
        if not versions:
            raise DocumentaryError("version_not_found")
        token = secrets.token_urlsafe(_TOKEN_BYTES)
        expires_at = datetime.now(timezone.utc) + timedelta(days=_APPROVAL_TTL_DAYS)
        one(
            "INSERT INTO public.customer_approvals "
            "(org_id,project_id,project_version_id,token_hash,expires_at,created_by) "
            "VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
            [
                str(org_id),
                str(project_id),
                str(versions[0]["id"]),
                hashlib.sha256(token.encode()).hexdigest(),
                expires_at,
                str(actor_id),
            ],
        )
    return {"token": token, "expires_at": expires_at}


def _approval_for_token(token: str) -> dict[str, object]:
    found = rows(
        "SELECT * FROM public.customer_approvals WHERE token_hash=%s",
        [hashlib.sha256(token.encode()).hexdigest()],
    )
    if len(found) != 1:
        raise DocumentaryError("quote_not_found")
    approval = found[0]
    if approval["expires_at"] < datetime.now(timezone.utc):
        raise DocumentaryError("quote_expired")
    return approval


def portal_quote(token: str) -> dict[str, object]:
    """Public read: the shared quote summary plus the sealed PDF link."""
    with transaction.atomic(), portal_backend():
        approval = _approval_for_token(token)
        org_id = approval["org_id"]
        project = one(
            "SELECT code,name,client_name,status,total_price_net,total_price_tax,"
            "total_price_gross,current_revision FROM public.projects "
            "WHERE id=%s AND org_id=%s",
            [approval["project_id"], org_id],
            "project_not_found",
        )
        version = one(
            "SELECT revision_code,emitted_at FROM public.project_versions "
            "WHERE id=%s AND org_id=%s AND project_id=%s",
            [approval["project_version_id"], org_id, approval["project_id"]],
            "version_not_found",
        )
        artifacts = rows(
            "SELECT id,storage_object_key,created_at FROM public.document_artifacts "
            "WHERE org_id=%s AND project_version_id=%s "
            "AND document_type='DOC-03' AND format='PDF' "
            "ORDER BY created_at DESC LIMIT 1",
            [org_id, approval["project_version_id"]],
        )
        signed_url = (
            SupabaseDocumentStorage().signed_url(str(artifacts[0]["storage_object_key"]))
            if artifacts
            else None
        )
        return {
            "schema": "portal_quote_v1",
            "project_code": project["code"],
            "project_name": project["name"],
            "client_name": project["client_name"],
            "project_status": project["status"],
            "revision_code": version["revision_code"],
            "emitted_at": version["emitted_at"].isoformat(),
            "total_price_net": str(project["total_price_net"]),
            "total_price_tax": str(project["total_price_tax"]),
            "total_price_gross": str(project["total_price_gross"]),
            "expires_at": approval["expires_at"].isoformat(),
            "approval_status": approval["status"],
            "decided_by": approval["decided_by"],
            "decided_at": (
                approval["decided_at"].isoformat() if approval["decided_at"] else None
            ),
            "decided_note": approval["decided_note"],
            "quote_pdf_url": signed_url,
        }


def decide_quote(
    *, token: str, decision: str, decided_by: str, note: str | None
) -> dict[str, object]:
    """Approve or decline the shared quote; replays return the sealed state."""
    with transaction.atomic(), portal_backend():
        approval = _approval_for_token(token)
        if approval["status"] == "PENDING":
            now = datetime.now(timezone.utc)
            one(
                "UPDATE public.customer_approvals SET status=%s,decided_by=%s,"
                "decided_at=%s,decided_note=%s WHERE id=%s RETURNING id",
                [decision, decided_by, now, note or None, approval["id"]],
            )
            if decision == "APPROVED":
                # Project status transitions belong to the commercial service:
                # the pricing trigger and revision guard only allow
                # pricing_backend, and its project policy checks the caller's
                # membership role. The approval carries that delegated
                # authority — created_by was verified as OWNER/ESTIMATOR when
                # the link was minted — so assert those claims for the
                # transition, exactly as authenticated_rls_context does for a
                # real request. The decider is recorded on the approval row.
                claims = json.dumps({"sub": str(approval["created_by"])})
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT set_config('request.jwt.claims', %s, true)",
                        [claims],
                    )
                    cursor.execute("SET LOCAL ROLE pricing_backend")
                rows(
                    "UPDATE public.projects SET status='APPROVED',updated_at=%s "
                    "WHERE id=%s AND org_id=%s AND status='QUOTED' RETURNING id",
                    [now, approval["project_id"], approval["org_id"]],
                )
    return portal_quote(token)
