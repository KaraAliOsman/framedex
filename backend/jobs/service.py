"""Enqueue/read orchestration for the durable job queue."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator
from uuid import UUID

from django.db import connection
from psycopg import sql

from jobs import registry, repository


@contextmanager
def job_backend() -> Iterator[None]:
    """job_runs is a service-owned table — only ``service_role`` holds its
    grants. Same save/restore pattern as ``documentary_backend`` so the
    enqueue can run inside a request transaction without widening tenant
    grants on the queue."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_setting('role')")
        previous = str(cursor.fetchone()[0])
        if previous == "none":
            previous = "authenticated"
        cursor.execute("SET LOCAL ROLE service_role")
    try:
        yield
    finally:
        if not connection.needs_rollback:
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(previous)))


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
    role: str | None = None,
) -> tuple[dict[str, object], bool]:
    spec = registry.spec_for(job_type)
    if spec is None:
        raise JobServiceError("job_type_unknown")
    serializer = spec.payload_serializer(data=payload)
    if not serializer.is_valid():
        raise JobServiceError("job_payload_invalid")
    validated = dict(serializer.validated_data)
    if spec.authorize is not None and role is not None and not spec.authorize(validated, role):
        raise JobServiceError("job_permission_denied")
    job, created = repository.insert_job(
        org_id=org_id,
        job_type=job_type,
        payload=validated,
        idempotency_key=idempotency_key,
        max_attempts=max_attempts,
        run_after=run_after or datetime.now(timezone.utc),
        created_by=created_by,
    )
    # A replayed enqueue asks for a runnable job: a terminal row no longer
    # satisfies that, so requeue it in place. SUCCEEDED stays deduped — the
    # original result is the answer.
    job_id = job.get("id")
    if (
        not created
        and idempotency_key is not None
        and job.get("state") in ("FAILED", "CANCELED")
        and job_id is not None
    ):
        requeued = repository.requeue_terminal(
            job_id=UUID(str(job_id)),
            run_after=run_after or datetime.now(timezone.utc),
        )
        if requeued is not None:
            return requeued, True
    return job, created


def get(*, org_id: UUID, job_id: UUID) -> dict[str, object] | None:
    return repository.get_job(org_id=org_id, job_id=job_id)


def list_recent(
    *, org_id: UUID, job_type: str | None, state: str | None, limit: int
) -> list[dict[str, object]]:
    return repository.list_jobs(org_id=org_id, job_type=job_type, state=state, limit=limit)
