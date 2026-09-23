"""Registered job handlers. Each wraps an existing domain service so the
durable queue reuses the same authority checks as the synchronous API.

Backend roles like documentary_backend evaluate auth.uid() through the
transaction-local request.jwt.claims GUC — the worker re-establishes it per
job from the row's created_by actor."""

from __future__ import annotations

import json
from typing import Any

from django.db import connection, transaction

from jobs.registry import JobContext, ProgressReporter, register
from documents.serializers import ArtifactRequestSerializer


def _claims_for(actor_id: str, context: JobContext) -> dict[str, Any]:
    return {
        "sub": actor_id,
        "aud": "authenticated",
        "role": "authenticated",
        "aal": "aal1",
        "app_metadata": {},
        "user_metadata": {},
        "session_id": f"job-{context.job_id}",
    }


@register(
    "document.artifact.generate",
    roles=("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER"),
    payload_serializer=ArtifactRequestSerializer,
    label="Emitir documento",
)
def generate_artifact_job(
    payload: dict[str, Any], context: JobContext, report: ProgressReporter
) -> dict[str, Any]:
    from authentication.tenancy import MembershipRepository, resolve_tenant_context
    from documents.artifacts import generate_artifact

    if context.created_by is None:
        raise ValueError("job_requires_actor")
    report(5)
    memberships = MembershipRepository().list_active_for_user(context.created_by)
    tenant = resolve_tenant_context(memberships, str(context.org_id))
    role = tenant.active_organization.role

    report(15)
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT set_config('request.jwt.claims', %s, true)",
                [json.dumps(_claims_for(str(context.created_by), context))],
            )
        output, created = generate_artifact(
            org_id=context.org_id,
            actor_id=context.created_by,
            role=role,
            project_version_id=payload["project_version_id"],
            order_id=payload.get("order_id"),
            document_type=payload["document_type"],
            file_format=payload["format"],
        )
    report(95)
    return {"artifact": output, "created": created}
