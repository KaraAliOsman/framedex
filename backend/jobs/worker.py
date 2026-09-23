"""Worker loop: claim queued rows, run the registered handler, record the
terminal state. Crash recovery happens through release_stale() requeueing
RUNNING rows whose lock went stale."""

from __future__ import annotations

import logging
import socket
import time
from uuid import UUID

from jobs import registry, repository

logger = logging.getLogger(__name__)


def worker_id_default() -> str:
    return f"{socket.gethostname()}"


def run_once(*, worker_id: str, batch: int = 8) -> int:
    """One claim+execute pass. Returns the number of jobs processed."""
    released = repository.release_stale()
    if released:
        logger.warning("job worker %s requeued %s stale job(s)", worker_id, released)
    claimed = repository.claim_batch(worker_id=worker_id, limit=batch)
    for job in claimed:
        _execute(job)
    return len(claimed)


def run_forever(*, worker_id: str, batch: int = 8, poll_seconds: float = 2.0) -> None:
    logger.info("job worker %s polling every %.1fs", worker_id, poll_seconds)
    while True:
        try:
            processed = run_once(worker_id=worker_id, batch=batch)
        except Exception:
            logger.exception("job worker %s claim pass failed", worker_id)
            time.sleep(poll_seconds)
            continue
        if processed == 0:
            time.sleep(poll_seconds)


def _execute(job: dict[str, object]) -> None:
    job_type = str(job["type"])
    spec = registry.spec_for(job_type)
    job_id = job["id"]
    if spec is None:
        repository.fail_or_retry(
            job_id=job_id,
            error={"code": "job_type_unregistered", "detail": job_type},
            attempt=int(job["attempt"]),
            max_attempts=int(job["max_attempts"]),
        )
        return

    def report(progress: float) -> None:
        repository.report_progress(job_id=job_id, progress=max(0.0, min(progress, 99.0)))

    context = registry.JobContext(
        job_id=job_id if isinstance(job_id, UUID) else UUID(str(job_id)),
        org_id=UUID(str(job["org_id"])),
        created_by=UUID(str(job["created_by"])) if job.get("created_by") else None,
        attempt=int(job["attempt"]),
        payload=job["payload"] if isinstance(job["payload"], dict) else {},
    )
    try:
        result = spec.run(context.payload, context, report)
    except Exception as error:  # noqa: BLE001 — any handler error becomes job error
        logger.exception("job %s (%s) failed on attempt %s", job_id, job_type, job["attempt"])
        outcome = repository.fail_or_retry(
            job_id=job_id,
            error={
                "code": "job_handler_error",
                "detail": f"{type(error).__name__}: {error}"[:500],
            },
            attempt=int(job["attempt"]),
            max_attempts=int(job["max_attempts"]),
        )
        logger.warning("job %s marked %s", job_id, outcome)
        return
    repository.succeed(job_id=job_id, result=result)
    logger.info("job %s (%s) succeeded", job_id, job_type)
