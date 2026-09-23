"""Raw access to public.job_runs — a service-owned table reached only as the
connection owner. Every query binds org_id explicitly; RLS is never relied on
here because worker claims and service reads bypass it by design."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from uuid import UUID

from django.db import connection, DatabaseError

from pricing.repository import json_text, rows

STALE_LOCK_SECONDS = 600

_JSON_COLUMNS = frozenset({"payload", "result", "error"})


def _decode(record: dict[str, object]) -> dict[str, object]:
    for key in record.keys() & _JSON_COLUMNS:
        if isinstance(record[key], str):
            record[key] = json.loads(record[key])
    return record


def insert_job(
    *,
    org_id: UUID,
    job_type: str,
    payload: dict[str, object],
    idempotency_key: str | None,
    max_attempts: int,
    run_after: datetime,
    created_by: UUID | None,
) -> tuple[dict[str, object], bool]:
    """Insert a queued job; on idempotency conflict return the live row."""
    try:
        record = rows(
            """
            INSERT INTO public.job_runs
                (org_id, type, payload, idempotency_key, max_attempts, run_after, created_by)
            VALUES (%s, %s, %s::jsonb, %s, %s, %s, %s)
            RETURNING *
            """,
            [
                str(org_id),
                job_type,
                json_text(payload),
                idempotency_key,
                max_attempts,
                run_after,
                str(created_by) if created_by else None,
            ],
        )
        return _decode(record[0]), True
    except DatabaseError as error:
        if getattr(getattr(error, "__cause__", None), "sqlstate", None) != "23505":
            raise
    if idempotency_key is None:
        raise DatabaseError("job_idempotency_conflict_unresolved")
    existing = get_job_by_key(org_id=org_id, job_type=job_type, key=idempotency_key)
    if existing is None:
        raise DatabaseError("job_idempotency_conflict_unresolved")
    return existing, False


def get_job(*, org_id: UUID, job_id: UUID) -> dict[str, object] | None:
    record = rows(
        "SELECT * FROM public.job_runs WHERE org_id = %s AND id = %s",
        [str(org_id), str(job_id)],
    )
    return _decode(record[0]) if record else None


def get_job_by_key(*, org_id: UUID, job_type: str, key: str) -> dict[str, object] | None:
    record = rows(
        """
        SELECT * FROM public.job_runs
        WHERE org_id = %s AND type = %s AND idempotency_key = %s
        """,
        [str(org_id), job_type, key],
    )
    return _decode(record[0]) if record else None


def list_jobs(
    *,
    org_id: UUID,
    job_type: str | None = None,
    state: str | None = None,
    limit: int = 50,
) -> list[dict[str, object]]:
    clauses = ["org_id = %s"]
    parameters: list[object] = [str(org_id)]
    if job_type:
        clauses.append("type = %s")
        parameters.append(job_type)
    if state:
        clauses.append("state = %s")
        parameters.append(state)
    parameters.append(limit)
    return [
        _decode(record)
        for record in rows(
            f"""
            SELECT * FROM public.job_runs
            WHERE {' AND '.join(clauses)}
            ORDER BY created_at DESC
            LIMIT %s
            """,
            parameters,
        )
    ]


def claim_batch(*, worker_id: str, limit: int) -> list[dict[str, object]]:
    """Atomically claim queued rows; one worker wins each row."""
    if connection.vendor == "postgresql":
        record = rows(
            """
            UPDATE public.job_runs
            SET state = 'RUNNING',
                locked_by = %s,
                locked_at = NOW(),
                attempt = attempt + 1,
                started_at = COALESCE(started_at, NOW()),
                updated_at = NOW()
            WHERE id IN (
                SELECT id FROM public.job_runs
                WHERE state = 'QUEUED' AND run_after <= NOW()
                ORDER BY created_at
                FOR UPDATE SKIP LOCKED
                LIMIT %s
            )
            RETURNING *
            """,
            [worker_id, limit],
        )
        return [_decode(item) for item in record]
    # Development fallback (sqlite): single-process claim without SKIP LOCKED.
    record = rows(
        """
        SELECT id FROM public.job_runs
        WHERE state = 'QUEUED' AND run_after <= %s
        ORDER BY created_at
        LIMIT %s
        """,
        [datetime.now(timezone.utc).isoformat(), limit],
    )
    if not record:
        return []
    ids = [item["id"] for item in record]
    placeholders = ", ".join("%s" for _ in ids)
    claimed = rows(
        f"""
        UPDATE public.job_runs
        SET state = 'RUNNING',
            locked_by = %s,
            locked_at = %s,
            attempt = attempt + 1,
            started_at = COALESCE(started_at, %s),
            updated_at = %s
        WHERE id IN ({placeholders}) AND state = 'QUEUED'
        RETURNING *
        """,
        [
            worker_id,
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat(),
            *ids,
        ],
    )
    return [_decode(item) for item in claimed]


def release_stale(*, now: datetime | None = None) -> int:
    """Requeue RUNNING jobs whose worker disappeared (crash recovery)."""
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(
        seconds=STALE_LOCK_SECONDS
    )
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE public.job_runs
            SET state = 'QUEUED',
                locked_by = NULL,
                locked_at = NULL,
                updated_at = NOW()
            WHERE state = 'RUNNING' AND locked_at < %s
            """,
            [cutoff],
        )
        return cursor.rowcount


def report_progress(*, job_id: UUID, progress: float) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE public.job_runs
            SET progress = %s, updated_at = NOW()
            WHERE id = %s AND state = 'RUNNING'
            """,
            [progress, str(job_id)],
        )


def succeed(*, job_id: UUID, result: dict[str, object]) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE public.job_runs
            SET state = 'SUCCEEDED',
                progress = 100.00,
                result = %s::jsonb,
                error = NULL,
                locked_by = NULL,
                locked_at = NULL,
                completed_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
            """,
            [json_text(result), str(job_id)],
        )


def fail_or_retry(
    *, job_id: UUID, error: dict[str, object], attempt: int, max_attempts: int
) -> str:
    """Requeue with quadratic backoff, or mark FAILED after the last attempt."""
    terminal = attempt >= max_attempts
    state_update = (
        "state = 'FAILED', completed_at = NOW()"
        if terminal
        else "state = 'QUEUED'"
    )
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE public.job_runs
            SET {state_update},
                error = %s::jsonb,
                locked_by = NULL,
                locked_at = NULL,
                run_after = NOW() + (%s || ' seconds')::interval,
                updated_at = NOW()
            WHERE id = %s
            """,
            [json_text(error), str(15 * attempt * attempt), str(job_id)],
        )
    return "FAILED" if terminal else "QUEUED"
