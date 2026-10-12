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


class OfferedOptions:
    """Verified authorities shared only within one live capability request.

    No token, consent or revocation is cached between requests. Both complete
    hashes and the literal four offered blocks remain mandatory.
    """

    def __init__(self, org_id, offering):
        self.org_id = org_id
        version, self.snapshot = _revision_snapshot(UUID(str(offering["id"])), UUID(str(org_id)))
        if str(version["project_id"]) != str(offering["project_id"]):
            raise DocumentaryError("quote_option_not_offered")
        self.offering = version
        self.verified = {version["revision_code"]: (self.offering, self.snapshot)}

    def resolve(self, revision):
        if revision in self.verified:
            return self.verified[revision]
        selected = one("SELECT id FROM public.project_versions WHERE org_id=%s AND project_id=%s AND revision_code=%s",
                       [self.org_id, self.offering["project_id"], revision], "quote_option_not_offered")
        version, full = _revision_snapshot(UUID(str(selected["id"])), UUID(str(self.org_id)))
        blocks = {key: full[key] for key in ("revision", "project", "positions", "pricing")}
        if blocks not in self.snapshot.get("alternatives", []):
            raise DocumentaryError("quote_option_not_offered", detail="La opción ya no pertenece a esta propuesta. Consulte nuevamente el enlace.")
        result = (version, full)
        self.verified[revision] = result
        return result


def resolve_option(org_id, offering, revision):
    """Resolve full immutable authority without retaining it across calls."""
    return OfferedOptions(org_id, offering).resolve(revision)


def selected_version(org_id, offering):
    selected = choice(org_id, offering["id"])
    if selected and selected["kind"] == "APPROVED":
        version = one("SELECT id,project_id,revision_code,snapshot_json::text AS snapshot_json FROM public.project_versions WHERE org_id=%s AND id=%s",
                      [org_id, selected["selected_version_id"]], "version_not_found")
        # Resolution verifies both the complete snapshot hash and its inclusion.
        return resolve_option(org_id, offering, version["revision_code"])[0]
    return offering
