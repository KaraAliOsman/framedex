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
    from ingest.service import ImportError_, extract_for_import

    if context.created_by is None:
        raise ValueError("job_requires_actor")
    report(10)
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT set_config('request.jwt.claims', %s, true)",
                [json.dumps(_claims_for(str(context.created_by), context))],
            )
        try:
            output = extract_for_import(
                org_id=context.org_id,
                import_id=payload["import_id"],
                actor_id=context.created_by,
            )
        except ImportError_ as error:
            raise JobPermanentError(error.code) from error
    report(95)
    return output
