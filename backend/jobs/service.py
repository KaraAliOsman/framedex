"""Enqueue/read orchestration for the durable job queue."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from jobs import registry, repository


class JobServiceError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def enqueue(
    *,
    org_id: UUID,
    job_type: str,
    payload: dict[str, object],
    idempotency_key: str | None = None,
    max_attempts: int = 3,
    run_after: datetime | None = None,
    created_by: UUID | None = None,
) -> tuple[dict[str, object], bool]:
    spec = registry.spec_for(job_type)
    if spec is None:
        raise JobServiceError("job_type_unknown")
    serializer = spec.payload_serializer(data=payload)
    if not serializer.is_valid():
        raise JobServiceError("job_payload_invalid")
    return repository.insert_job(
        org_id=org_id,
        job_type=job_type,
        payload=dict(serializer.validated_data),
        idempotency_key=idempotency_key,
        max_attempts=max_attempts,
        run_after=run_after or datetime.now(timezone.utc),
        created_by=created_by,
    )


def get(*, org_id: UUID, job_id: UUID) -> dict[str, object] | None:
    return repository.get_job(org_id=org_id, job_id=job_id)


def list_recent(
    *, org_id: UUID, job_type: str | None, state: str | None, limit: int
) -> list[dict[str, object]]:
    return repository.list_jobs(org_id=org_id, job_type=job_type, state=state, limit=limit)
