"""Authenticated original-source access and immutable import chronology."""

import json

from documents.storage import SupabaseDocumentStorage
from ingest.catalog_service import _get
from pricing.repository import json_text, rows
from authentication.rls import catalog_backend


def original_source(org_id, import_id):
    row = _get(org_id, import_id)
    return row, SupabaseDocumentStorage().download(row["storage_path"])


def timeline(org_id, import_id):
    _get(org_id, import_id)  # Import RLS includes its commercial read boundary.
    values = rows("SELECT e.*, private.catalog_reviewer_label(e.actor_id,e.org_id) AS actor "
                  "FROM public.catalog_import_events e WHERE org_id=%s AND import_id=%s "
                  "ORDER BY created_at,id", [org_id, import_id])
    return {"items": [{"id": str(row["id"]), "action": row["action"],
        "actor_id": str(row["actor_id"]), "actor": row["actor"] or "Revisor técnico",
        "created_at": row["created_at"].isoformat(),
        "details": json.loads(row["details"]) if isinstance(row["details"], str) else row["details"]}
        for row in values]}


def record_review(*, org_id, import_id, actor_id, items, review_token, errors):
    with catalog_backend():
        rows("INSERT INTO public.catalog_import_events(org_id,import_id,actor_id,action,details) "
             "VALUES(%s,%s,%s,'REVIEW',%s::jsonb) RETURNING id", [org_id, import_id, actor_id,
            json_text({"review_token": review_token, "items": items, "errors": errors})])
