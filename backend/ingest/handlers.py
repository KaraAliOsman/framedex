"""Extraction job — document bytes become reviewable candidates off-request."""

from __future__ import annotations

import json
from typing import Any

from django.db import connection, transaction

from jobs.handlers import _claims_for
from jobs.registry import JobContext, JobPermanentError, ProgressReporter, register
from ingest.serializers import ExtractPayloadSerializer


@register(
    "ingest.document.extract",
    roles=("OWNER", "ESTIMATOR"),
    payload_serializer=ExtractPayloadSerializer,
    label="Extraer posiciones del documento",
)
def extract_document_job(
    payload: dict[str, Any], context: JobContext, report: ProgressReporter
) -> dict[str, Any]:
    from ingest.service import ImportError_, extract_for_import, mark_import_failed

    if context.created_by is None:
        raise ValueError("job_requires_actor")
    report(10)
    try:
        # Re-verify the uploader's membership at run time — a queued job must
        # not outlive revoked access. Claims stay scoped to this transaction.
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT set_config('request.jwt.claims', %s, true)",
                    [json.dumps(_claims_for(str(context.created_by), context))],
                )
                cursor.execute(
                    "SELECT 1 FROM public.tenancy_memberships "
                    "WHERE user_id=%s AND org_id=%s AND is_active",
                    [str(context.created_by), str(context.org_id)],
                )
                member = cursor.fetchone()
        if member is None:
            raise ImportError_("import_membership_revoked")
        # The provider call and its audit/debit commit independently — no
        # handler-wide transaction may wrap them, or a retry re-bills OCR.
        output = extract_for_import(
            org_id=context.org_id,
            import_id=payload["import_id"],
            actor_id=context.created_by,
        )
    except Exception as error:
        permanent = isinstance(error, ImportError_)
        if permanent or context.attempt >= context.max_attempts:
            # Terminal failure — the import must reach FAILED so the UI stops
            # polling; recorded outside the failed transaction so it survives.
            code = error.code if permanent else "import_extract_failed"
            try:
                mark_import_failed(
                    org_id=context.org_id,
                    import_id=payload["import_id"],
                    code=code,
                )
            except Exception:  # noqa: BLE001 — job_runs already records the error
                pass
        if permanent:
            raise JobPermanentError(error.code) from error
        raise
    report(95)
    return output
