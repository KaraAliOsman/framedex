"""One chosen sealed solution for collection, forecast and manufacture.

The offer remains the project revision. A choice is an additive record, never
an edit to an issued snapshot. Personal evidence stays in the commercial role.
"""

from uuid import UUID
from django.db import connection

from documents.artifacts import _revision_snapshot
from documents.repository import DocumentaryError, one, rows


def lock_quote(org_id, project_id):
    """Serialize a decision with purchase/release claims for this project."""
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',
                           [f'quote-decision:{org_id}:{project_id}'])


def choice(org_id, offering_id):
    found = rows("SELECT * FROM private.quotation_choice(%s,%s)", [org_id, offering_id])
    return found[0] if found else None


def resolve_option(org_id, offering, revision):
    """Resolve the full immutable authority, checking the offered four blocks."""
    offering, snapshot = _revision_snapshot(UUID(str(offering["id"])), UUID(str(org_id)))
    if revision == offering["revision_code"]:
        return offering, snapshot
    selected = one("SELECT id FROM public.project_versions WHERE org_id=%s AND project_id=%s AND revision_code=%s",
                   [org_id, offering["project_id"], revision], "quote_option_not_offered")
    version, full = _revision_snapshot(UUID(str(selected["id"])), UUID(str(org_id)))
    blocks = {key: full[key] for key in ("revision", "project", "positions", "pricing")}
    if blocks not in snapshot.get("alternatives", []):
        raise DocumentaryError("quote_option_not_offered", detail="La opción ya no pertenece a esta propuesta. Consulte nuevamente el enlace.")
    return version, full


def selected_version(org_id, offering):
    selected = choice(org_id, offering["id"])
    if selected and selected["kind"] == "APPROVED":
        version = one("SELECT id,project_id,revision_code,snapshot_json::text AS snapshot_json FROM public.project_versions WHERE org_id=%s AND id=%s",
                      [org_id, selected["selected_version_id"]], "version_not_found")
        # Resolution verifies both the complete snapshot hash and its inclusion.
        return resolve_option(org_id, offering, version["revision_code"])[0]
    return offering
