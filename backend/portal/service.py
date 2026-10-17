"""Customer quote-approval links: public token-scoped reads and decisions."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import logging
import secrets
from typing import Iterator
from uuid import UUID
from zoneinfo import ZoneInfo

from django.db import DatabaseError, connection, transaction
from psycopg import sql

from authentication.rls import tx_aborted
from documents.artifacts import SupabaseDocumentStorage, generate_artifact
from documents.renderers import finish_label, frozen_glass_specs
from documents.repository import (
    DocumentaryError,
    decoded,
    documentary_backend,
    one,
    rows,
    write,
)
from documents.agreements import choice

logger = logging.getLogger(__name__)

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
        if not tx_aborted():
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(previous))
                )
        raise
    else:
        if not tx_aborted():
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(previous))
                )


def share_quote(
    *, org_id: UUID, project_id: UUID, actor_id: UUID, role: str
) -> dict[str, object]:
    """Mint a fresh approval link for the project's latest sealed version."""
    with documentary_backend():
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
    # The client-facing quotation is DOC-01 (the commercial offer). Generate it
    # before minting: generation is slot-idempotent, and a failure must not
    # strand an approval whose token nobody ever saw.
    generate_artifact(
        org_id=org_id,
        actor_id=actor_id,
        role=role,
        project_version_id=versions[0]["id"],
        order_id=None,
        document_type="DOC-01",
        file_format="PDF",
    )
    token = secrets.token_urlsafe(_TOKEN_BYTES)
    expires_at = datetime.now(timezone.utc) + timedelta(days=_APPROVAL_TTL_DAYS)
    with transaction.atomic(), documentary_backend():
        # A fresh share supersedes every outstanding link for this revision —
        # otherwise pending tokens accumulate and stay concurrently valid.
        rows(
            "UPDATE public.customer_approvals SET status='REVOKED',revoked_at=%s,"
            "revoked_by=%s WHERE org_id=%s AND project_id=%s "
            "AND project_version_id=%s AND status='PENDING' AND link_source='SHARE' RETURNING id",
            [
                datetime.now(timezone.utc),
                str(actor_id),
                str(org_id),
                str(project_id),
                str(versions[0]["id"]),
            ],
        )
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


def revoke_link(
    *, org_id: UUID, project_id: UUID, approval_id: UUID, actor_id: UUID
) -> dict[str, object]:
    """Kill a PENDING link. Decided links stay on the record — revocation is
    an off switch for an unanswered share, not a way to un-decide a client."""
    with documentary_backend():
        approval = one(
            "SELECT id,status FROM public.customer_approvals "
            "WHERE id=%s AND org_id=%s AND project_id=%s",
            [str(approval_id), str(org_id), str(project_id)],
            "approval_not_found",
        )
        if str(approval["status"]) == "REVOKED":
            return approval
        if str(approval["status"]) != "PENDING":
            raise DocumentaryError("approval_not_pending")
        return one(
            "UPDATE public.customer_approvals SET status='REVOKED',revoked_at=%s,"
            "revoked_by=%s WHERE id=%s AND status='PENDING' RETURNING id,status",
            [datetime.now(timezone.utc), str(actor_id), str(approval_id)],
        )


def list_approvals(*, org_id: UUID, project_id: UUID) -> list[dict[str, object]]:
    """The org-side record of every link minted for a project: who it went
    to (the token stays opaque — the link URL is the capability), which
    revision it carried, and how the client answered."""
    with documentary_backend():
        project = one(
            "SELECT id,current_revision FROM public.projects WHERE id=%s AND org_id=%s",
            [str(project_id), str(org_id)],
            "project_not_found",
        )
        return [
            {
                "id": str(row["id"]),
                "link_source": row["link_source"],
                "status": str(row["status"]),
                "decision_kind": row.get('decision_kind'),
                "selected_revision": row.get('selected_revision'),
                "position_index": row.get('position_index'),
                "evidence": decoded(row['evidence']) if row.get('evidence') else None,
                "revision_code": str(row["revision_code"]),
                "decided_by": row["decided_by"],
                "decided_at": row["decided_at"].isoformat()
                if row["decided_at"]
                else None,
                "expires_at": row["expires_at"].isoformat(),
                "original_expires_at": row["original_expires_at"].isoformat(),
                "link_state": ("SUPERSEDED" if str(row["revision_code"]) != str(project["current_revision"])
                    else "REVOKED" if row["status"] == "REVOKED"
                    else "EXPIRED" if row["expires_at"] <= datetime.now(timezone.utc) or _validity_expired(row["valid_until"])
                    else row["status"] if row["status"] in ("APPROVED", "DECLINED", "CHANGES_REQUESTED")
                    else "VIEWED" if row["view_count"] else "ACTIVE"),
                "created_at": row["created_at"].isoformat(),
                "revoked_at": row["revoked_at"].isoformat()
                if row["revoked_at"]
                else None,
                "decided_note": row["decided_note"],
                "view_count": int(row["view_count"] or 0),
                "last_viewed_at": row["last_viewed_at"].isoformat()
                if row["last_viewed_at"]
                else None,
            }
            for row in rows(
                "SELECT a.id,CASE WHEN a.status='REVOKED' THEN a.status ELSE COALESCE(c.kind,a.status) END AS status,a.link_source,"
                "COALESCE(d.evidence->>'name',a.decided_by) AS decided_by,COALESCE(c.decided_at,a.decided_at) AS decided_at,"
                "COALESCE(d.evidence->>'note',a.decided_note) AS decided_note,d.evidence,c.kind AS decision_kind,"
                "selected.revision_code AS selected_revision,"
                "(SELECT (p->>'position_index')::integer FROM jsonb_array_elements(selected.snapshot_json->'positions') p "
                "WHERE p->>'id'=d.position_id::text) AS position_index,"
                "private.quote_link_expires_at(a.id,a.org_id,a.expires_at) AS expires_at,"
                "a.expires_at AS original_expires_at,a.created_at,a.revoked_at,a.view_count,a.last_viewed_at,"
                "v.revision_code,v.snapshot_json->'project'->>'quotation_valid_until' AS valid_until "
                "FROM public.customer_approvals a "
                "JOIN public.project_versions v "
                "ON v.id = a.project_version_id "
                "LEFT JOIN LATERAL private.quotation_choice(a.org_id,v.id) c ON true "
                "LEFT JOIN public.quote_decisions d ON d.org_id=a.org_id AND d.offering_version_id=v.id "
                "LEFT JOIN public.project_versions selected ON selected.id=c.selected_version_id AND selected.org_id=a.org_id "
                "WHERE a.org_id=%s AND a.project_id=%s "
                "ORDER BY a.created_at DESC",
                [str(org_id), str(project_id)],
            )
        ]


def _validity_expired(value: object) -> bool:
    """Sealed ``quotation_valid_until`` — a malformed date is a data defect,
    not a crash: the public read must surface a contract error, not a 500."""
    if not value:
        return False
    try:
        return date.fromisoformat(str(value)) < datetime.now(ZoneInfo("America/Santiago")).date()
    except ValueError:
        raise DocumentaryError("quotation_valid_until_invalid") from None


def _approval_for_token(token: str) -> dict[str, object]:
    found = rows(
        "SELECT * FROM public.customer_approvals WHERE token_hash=%s",
        [hashlib.sha256(token.encode()).hexdigest()],
    )
    if len(found) != 1:
        raise DocumentaryError("quote_not_found")
    approval = found[0]
    _scope_org(approval["org_id"])
    deadline = one("SELECT private.quote_link_expires_at(%s,%s,%s) AS expires_at",
                   [approval["id"], approval["org_id"], approval["expires_at"]])
    approval["expires_at"] = deadline["expires_at"]
    if approval["status"] == "REVOKED":
        raise DocumentaryError("quote_revoked", extra=_dead_contact(approval))
    if approval["expires_at"] < datetime.now(timezone.utc):
        raise DocumentaryError("quote_expired", extra=_dead_contact(approval))
    return approval


def _dead_contact(approval):
    version = _bound_version(approval)
    organization = _sealed_organization(version)
    return {'organization': organization}


def _scope_org(org_id: object) -> None:
    """Bind the portal role to the approval's tenant for this transaction.

    Portal policies on every other table require ``org_id`` to equal the
    ``app.portal_org_id`` GUC — the token lookup is the only query that runs
    unscoped, and it only touches the token's own row by hash.
    """
    rows("SELECT set_config('app.portal_org_id', %s, true)", [str(org_id)])


def _bound_version(approval: dict[str, object]) -> dict[str, object]:
    return one(
        "SELECT id,org_id,project_id,revision_code,emitted_at,snapshot_sha256,bom_hash,snapshot_json::text AS snapshot_json "
        "FROM public.project_versions "
        "WHERE id=%s AND org_id=%s AND project_id=%s",
        [approval["project_version_id"], approval["org_id"], approval["project_id"]],
        "version_not_found",
    )


def _sealed_project(version: dict[str, object]) -> dict[str, object]:
    """The immutable project payload captured when the revision was sealed."""
    snapshot = decoded(version["snapshot_json"])
    sealed = snapshot.get("project") if isinstance(snapshot, dict) else None
    return sealed if isinstance(sealed, dict) else {}


def _live_project(approval: dict[str, object], *, for_update: bool = False) -> dict[str, object]:
    return one(
        "SELECT status,current_revision FROM public.projects "
        "WHERE id=%s AND org_id=%s" + (" FOR UPDATE" if for_update else ""),
        [approval["project_id"], approval["org_id"]],
        "project_not_found",
    )


def _sealed_positions(version: dict[str, object]) -> list[dict[str, object]]:
    """The proposal's position cards — immutable snapshot rows, not live data."""
    snapshot = decoded(version["snapshot_json"])
    values = snapshot.get("positions") if isinstance(snapshot, dict) else None
    if not isinstance(values, list):
        return []
    positions = []
    for value in values:
        if not isinstance(value, dict):
            continue
        glass_specs: list[str] = []
        finish = ""
        try:
            glass_specs = frozen_glass_specs(value)
            finish = finish_label(value.get("color_interior"), value.get("color_exterior"), value.get("resolved_finish"))
        except DocumentaryError:
            glass_specs = []
            finish = ""
        positions.append({
            'system_name': str(value.get('system_name') or 'Serie sellada'),
            'is_demo': bool(value.get('is_demo')),
            "id": str(value.get("id") or ""),
            "position_index": value.get("position_index"),
            "quantity": value.get("quantity"),
            "typology": value.get("typology"),
            "location_tag": value.get("location_tag"),
            "width_mm": str(value.get("width_mm") or ""),
            "height_mm": str(value.get("height_mm") or ""),
            "opening_measurements": [{'module_index':index+1,
                'width_mm':item['result']['width']['opening_mm'],'height_mm':item['result']['height']['opening_mm'],
                'rule_name':item['rule']['name'],'synthetic':item['rule']['synthetic']}
                for index,item in enumerate((value.get('measurements') or {}).get('measurements') or [])],
            "color_interior": value.get("color_interior"),
            "color_exterior": value.get("color_exterior"),
            # Customer rendering needs the sealed samples, not the workshop's
            # commercial profile/stock bindings. Keep the issued authority intact.
            **({"resolved_finish": {**value["resolved_finish"], "profile_skus": {}}}
               if value.get("resolved_finish") else {}),
            "glass_specs": glass_specs,
            "commercial_hardware": [{key: item.get(key) for key in ("handle_name", "handle_color", "options", "synthetic")}
                for item in value.get("commercial_hardware") or []],
            "finish": finish or None,
            # Unpriced legacy lines stay null — a "$0" reads as free, never as
            # "not priced".
            "price_net": (
                str(value["price_net"]) if value.get("price_net") is not None else None
            ),
            "discount_pct": str(value.get("discount_pct") or "0"),
            "parametric_tree": value.get("parametric_tree"),
            "opening_leaves": [{**{key: leaf.get(key) for key in (
                "bay_id", "leaf_id", "opening", "use", "x_mm", "y_mm", "width_mm", "height_mm")},
                "source": "Revisión emitida",
                "handle": ({**{key: leaf["handle"].get(key) for key in (
                    "side", "x_mm", "y_mm", "height_from_bottom_mm", "minimum_height_from_bottom_mm",
                    "maximum_height_from_bottom_mm", "minimum_from_top_mm", "maximum_from_top_mm")},
                    "source": "Revisión emitida"} if isinstance(leaf.get("handle"), dict) else None),
                **({"advanced": {**{key: leaf["advanced"].get(key) for key in (
                    "recipe_code", "recipe_name", "scheme", "synthetic", "kind", "profile_role", "profile_face_mm",
                    "glass_x_mm", "glass_y_mm", "glass_width_mm", "glass_height_mm", "track", "plane_offset_mm",
                    "travel", "travel_mm", "lift_mm", "parallel_offset_mm", "pivot_x_mm", "pivot_y_mm",
                    "opening_angle_deg", "fold_group", "fold_index", "stack_side", "pass_through", "pass_open_plan",
                    "packet_pitch_mm", "balance", "closed_plan", "open_plan", "open_plan_polygon")},
                    "source": "Revisión emitida"}} if isinstance(leaf.get("advanced"), dict) else {})}
                for leaf in value.get("opening_leaves") or []],
        })
    return positions


def _sealed_organization(version: dict[str, object]) -> dict[str, object]:
    """The issuer's white-label identity for the proposal page — commercial
    name, contact lines and a signed logo URL, all from the sealed snapshot
    so a later rebrand can't rewrite a live quote."""
    snapshot = decoded(version["snapshot_json"])
    org = snapshot.get("organization") if isinstance(snapshot, dict) else None
    if not isinstance(org, dict):
        return {}
    logo_url = None
    logo_key = org.get("brand_logo_key")
    if logo_key:
        try:
            logo_url = SupabaseDocumentStorage().signed_url(str(logo_key))
        except Exception:
            logo_url = None
    result = {
        "portal_heading": (org.get("document_preferences") or {}).get("portal_heading", ""),
        "portal_intro": (org.get("document_preferences") or {}).get("portal_intro", ""),
        "name": org.get("name"),
        "tax_id": org.get("tax_id"),
        "commercial_name": org.get("commercial_name"),
        "brand_address": org.get("brand_address"),
        "brand_phone": org.get("brand_phone"),
        "brand_email": org.get("brand_email"),
        "brand_logo_url": logo_url,
    }
    if org.get("brand_schema") == 1:
        result.update(
            {
                "brand_schema": 1,
                "brand_primary_color": org.get("brand_primary_color", "#075F5A"),
                "portal_attribution": org.get("portal_attribution", True),
            }
        )
    return result


def portal_quote(token: str, *, track: bool = True) -> dict[str, object]:
    from portal.proposal_service import read
    return read(token, track=track)


def _transition_project_approved(
    *, approval: dict[str, object], version_id: str, now: datetime
) -> None:
    """Move the live project to APPROVED and queue its material forecast.

    Runs inside the caller's atomic block. The pricing trigger only allows
    pricing_backend and its project policy checks the caller's membership
    role, so the transition asserts the claims the approval delegated:
    created_by was verified as OWNER/ESTIMATOR when the approval was minted.
    The status guard makes the write atomic — a concurrent decision that
    commits first turns this into a no-op.
    """
    claims = json.dumps({"sub": str(approval["created_by"])})
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('request.jwt.claims', %s, true)", [claims])
        cursor.execute("SET LOCAL ROLE pricing_backend")
    updated = rows(
        "UPDATE public.projects SET status='APPROVED',updated_at=%s "
        "WHERE id=%s AND org_id=%s AND status='QUOTED' RETURNING id",
        [now, approval["project_id"], approval["org_id"]],
    )
    if len(updated) != 1:
        # Under the FOR UPDATE lock the only way the guard misses is the
        # projects policy rejecting the claims principal — the link's
        # creator left the org. The customer's decision still seals; the
        # project stays QUOTED for staff to approve off-channel instead of
        # failing a customer click with a 500.
        logger.warning(
            "portal_approval_transition_denied",
            extra={
                "approval_id": str(approval["id"]),
                "created_by": str(approval["created_by"]),
            },
        )
        return
    # §08: an approved quote queues the material forecast for the version it
    # decided — the job carries the approval's minted actor as its principal.
    from automations.service import emit

    emit(
        "automation.prep_forecast",
        org_id=UUID(str(approval["org_id"])),
        actor_id=UUID(str(approval["created_by"])),
        idempotency_key=f"auto:prep:{version_id}",
        version_id=version_id,
    )
    from notifications.service import approval_event

    approval_event(approval=approval, version_id=version_id)


def approve_internal(*, org_id, project_id, actor_id, actor_label, note):
    # Serialize off-channel approval with public decisions on the same project.
    with transaction.atomic():
        from documents.agreements import lock_quote
        lock_quote(org_id, project_id)
        return _approve_internal(org_id=org_id, project_id=project_id,
            actor_id=actor_id, actor_label=actor_label, note=note)


def _approve_internal(
    *,
    org_id: UUID,
    project_id: UUID,
    actor_id: UUID,
    actor_label: str,
    note: str | None,
) -> dict[str, object]:
    """Staff records that the customer approved the quote off-channel.

    Mints an already-APPROVED approval row bound to the project's latest
    sealed version — the same audit shape a customer decision leaves — and
    runs the same project transition. Outstanding pending links for the
    revision are revoked: the deal is decided, so no token should stay live.
    """
    with documentary_backend():
        project = one(
            "SELECT id,status,current_revision FROM public.projects "
            "WHERE id=%s AND org_id=%s FOR UPDATE",
            [str(project_id), str(org_id)],
            "project_not_found",
        )
        live_status = str(project["status"])
        if live_status == "APPROVED":
            return {"project_status": "APPROVED"}
        if live_status != "QUOTED":
            raise DocumentaryError("quote_approve_requires_quoted")
        versions = rows(
            "SELECT id,revision_code FROM public.project_versions "
            "WHERE project_id=%s AND org_id=%s "
            "ORDER BY emitted_at DESC,id DESC LIMIT 1",
            [str(project_id), str(org_id)],
        )
        if not versions:
            raise DocumentaryError("version_not_found")
        if choice(org_id, versions[0]['id']):
            raise DocumentaryError('quote_already_decided', detail='El cliente ya respondió esta propuesta. Crea una revisión nueva para acordar otras condiciones.')
        if str(project["current_revision"]) != str(versions[0]["revision_code"]):
            raise DocumentaryError("quote_approve_revision_mismatch")

    now = datetime.now(timezone.utc)
    with transaction.atomic(), documentary_backend():
        write(
            "UPDATE public.customer_approvals SET status='REVOKED',revoked_at=%s,"
            "revoked_by=%s WHERE org_id=%s AND project_id=%s "
            "AND project_version_id=%s AND status='PENDING'",
            [now, str(actor_id), str(org_id), str(project_id),
             str(versions[0]["id"])],
        )
        internal_token = secrets.token_urlsafe(_TOKEN_BYTES)
        approval = one(
            "INSERT INTO public.customer_approvals "
            "(org_id,project_id,project_version_id,token_hash,status,decided_by,"
            "decided_at,decided_note,expires_at,created_by) "
            "VALUES (%s,%s,%s,%s,'APPROVED',%s,%s,%s,%s,%s) "
            "RETURNING id,org_id,project_id,created_by",
            [
                str(org_id),
                str(project_id),
                str(versions[0]["id"]),
                hashlib.sha256(internal_token.encode()).hexdigest(),
                actor_label,
                now,
                note or None,
                now + timedelta(days=_APPROVAL_TTL_DAYS),
                str(actor_id),
            ],
        )
        _transition_project_approved(
            approval=approval, version_id=str(versions[0]["id"]), now=now
        )
    return {"project_status": "APPROVED"}


def decide_quote(
    *, token: str, decision: str, decided_by: str, note: str | None = None,
    decided_rut: str | None = None, **consent,
) -> dict[str, object]:
    from portal.proposal_service import decide
    return decide(token=token, decision=decision, decided_by=decided_by,
                  note=note, decided_rut=decided_rut, **consent)
