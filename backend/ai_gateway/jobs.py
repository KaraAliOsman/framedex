"""§07-B/G — durable AI jobs: every agent run persists as a job row carrying
its goal, plan, transcript (user turns + model rounds), typed projections
consulted, artifacts emitted, warnings and final result. The row is the UI's
truth — a settled job resumes with follow-up instructions, and artifacts stay
inspectable after the chat scrolls away.

States: RUNNING while a round executes; SUCCEEDED on a grounded reply;
WAITING_FOR_USER when the reply asks for missing input; WAITING_FOR_APPROVAL
when it proposes consequential actions; FAILED_RETRYABLE on a transient
provider/validity failure; FAILED on exhaustion; CANCELED by the user.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from decimal import Decimal
from typing import Any
from uuid import UUID

from django.db import DatabaseError, connection

from pricing.repository import rows


@contextmanager
def _ai_backend():
    """Job writes execute under the dedicated backend role: member-facing
    `authenticated` lost INSERT/UPDATE on ai_jobs so PostgREST cannot rewrite
    job state, transcripts, artifacts or results — the API is the only write
    path and it runs inside the same org/user RLS policies under this role.
    Mirrors commercial_backend: claims and policies stay unchanged.
    SQLite has no roles — the context is a no-op there."""
    if connection.vendor != "postgresql":
        yield
        return
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL ROLE ai_backend")
    try:
        yield
    except DatabaseError:
        raise
    except BaseException:
        if not connection.needs_rollback:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL ROLE authenticated")
        raise
    else:
        if not connection.needs_rollback:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL ROLE authenticated")

MAX_GOAL = 2000
MAX_ARTIFACT_TITLE = 120
MAX_ARTIFACT_BYTES = 32768
MAX_CLAIM = 240
MAX_CLAIMS = 8
MAX_REFERENCE = 120
MAX_REFERENCES = 12
MAX_ARTIFACTS_PER_RUN = 6
# The job-level artifact list accumulates across rounds — a follow-up turn
# must not erase drafts an earlier round produced. Bounded so a long-lived
# job can't grow the row without limit; oldest drafts age out first.
MAX_ARTIFACTS_TOTAL = 48

TERMINAL_STATES = frozenset({"SUCCEEDED", "FAILED", "CANCELED"})
OPEN_STATES = frozenset(
    {"QUEUED", "PLANNING", "RUNNING", "WAITING_FOR_USER",
     "WAITING_FOR_APPROVAL", "FAILED_RETRYABLE"}
)

# §07-G — artifact kinds are inspectable drafts. None of them mutate
# anything: a draft travels to the surface that owns the mutation, where a
# human confirms. Kinds mirror what the agent can actually produce today.
ARTIFACT_KINDS = frozenset(
    {
        "product_draft",
        "project_draft",
        "quote_draft",
        "catalog_candidates",
        "catalog_review",
        "purchase_plan",
        "production_plan",
        "message",
        "comparison",
        "document_preview",
    }
)


def _dump(value: Any) -> str:
    return json.dumps(value, default=str)


def create_job(*, org_id: UUID, user_id: UUID, surface: str,
               refs: dict, goal: str) -> dict:
    with _ai_backend():
        record = rows(
            "INSERT INTO public.ai_jobs"
            " (org_id, user_id, surface, refs, goal, state)"
            " VALUES (%s, %s, %s, %s::jsonb, %s, 'RUNNING')"
            " RETURNING id, org_id, user_id, surface, refs, goal, state, plan,"
            " transcript, artifacts, warnings, result, error_code,"
            " created_at, updated_at, completed_at",
            [str(org_id), str(user_id), surface, _dump(refs or {}),
             goal[:MAX_GOAL]],
        )[0]
    return _decode(record)


def get_job(*, org_id: UUID, user_id: UUID, job_id: UUID) -> dict | None:
    found = rows(
        "SELECT id, org_id, user_id, surface, refs, goal, state, plan,"
        " transcript, artifacts, warnings, result, error_code,"
        " created_at, updated_at, completed_at"
        " FROM public.ai_jobs WHERE id = %s AND org_id = %s AND user_id = %s",
        [str(job_id), str(org_id), str(user_id)],
    )
    return _decode(found[0]) if found else None


def list_jobs(
    *,
    org_id: UUID,
    user_id: UUID,
    limit: int = 30,
    before: str | None = None,
    before_id: str | None = None,
) -> list[dict]:
    params: list[object] = [str(org_id), str(user_id)]
    if before_id:
        try:
            UUID(str(before_id))
        except ValueError:
            before_id = None
    cursor = ""
    if before and before_id:
        # Composite keyset: ties on created_at paginate by id so rows sharing
        # the page-edge timestamp can't fall between pages.
        cursor = " AND (created_at < %s OR (created_at = %s AND id < %s::uuid))"
        params += [before, before, before_id]
    elif before:
        cursor = " AND created_at < %s"
        params.append(before)
    params.append(limit)
    return [
        _decode(row)
        for row in rows(
            "SELECT id, org_id, user_id, surface, refs, goal, state, plan,"
            " artifacts, warnings, result, error_code,"
            " created_at, updated_at, completed_at"
            " FROM public.ai_jobs WHERE org_id = %s AND user_id = %s"
            + cursor
            + " ORDER BY created_at DESC, id DESC LIMIT %s",
            params,
        )
    ]


def finish_job(*, job_id: UUID, state: str, transcript: list, plan: list,
               artifacts: list, warnings: list, result: dict | None,
               error_code: str | None = None) -> dict:
    with _ai_backend():
        record = rows(
        "UPDATE public.ai_jobs SET state = %s, transcript = %s::jsonb,"
        # The plan column mirrors the latest round that produced one — a
        # question-only follow-up keeps the last real plan visible instead
        # of blanking the rail.
        " plan = CASE WHEN %s::jsonb <> '[]'::jsonb THEN %s::jsonb ELSE plan END,"
        " artifacts = %s::jsonb, warnings = %s::jsonb, result = %s::jsonb,"
        " error_code = %s, updated_at = NOW(),"
        " completed_at = CASE WHEN %s IN ('SUCCEEDED','FAILED','CANCELED')"
        " THEN NOW() ELSE completed_at END"
        " WHERE id = %s AND state = 'RUNNING' RETURNING id",
        [
            state, _dump(transcript), _dump(plan), _dump(plan),
            _dump(artifacts), _dump(warnings),
            _dump(result) if result is not None else None, error_code,
            state, str(job_id),
        ],
        )
    if not record:
        raise ValueError("ai_job_terminal")
    return {"id": str(record[0]["id"])}


def resume_job(*, job_id: UUID, transcript: list) -> dict:
    """Claim a settled job for a new round. The UPDATE itself is the lock:
    only WAITING_*/FAILED_RETRYABLE/SUCCEEDED states move to RUNNING, so a
    follow-up racing a live round or a closed job gets a conflict instead of
    silently writing its stale transcript over the other round's work."""
    with _ai_backend():
        record = rows(
            "UPDATE public.ai_jobs SET state = 'RUNNING',"
            " transcript = %s::jsonb, result = NULL, error_code = NULL,"
            " completed_at = NULL, updated_at = NOW()"
            " WHERE id = %s AND state IN"
            " ('WAITING_FOR_USER','WAITING_FOR_APPROVAL','FAILED_RETRYABLE','SUCCEEDED')"
            " RETURNING id",
            [_dump(transcript), str(job_id)],
        )
    if record:
        return {"id": str(record[0]["id"])}
    state = rows(
        "SELECT state FROM public.ai_jobs WHERE id = %s", [str(job_id)]
    )
    if state and state[0]["state"] in TERMINAL_STATES:
        raise ValueError("ai_job_terminal")
    raise ValueError("ai_job_running")


def _failure_turns(goal: str, error_code: str) -> list[dict]:
    return [
        {"role": "user", "text": goal[:MAX_GOAL]},
        {"role": "error", "code": error_code[:120]},
    ]


def create_failed_job(*, org_id: UUID, user_id: UUID, surface: str,
                      refs: dict, goal: str, error_code: str) -> dict:
    """§07-B — a failed first round outlives the rolled-back request: after
    the scope unwinds, the caller re-enters its RLS context and records the
    job here, so the workspace shows a resumable FAILED_RETRYABLE row
    instead of nothing at all."""
    with _ai_backend():
        record = rows(
            "INSERT INTO public.ai_jobs"
            " (org_id, user_id, surface, refs, goal, state, transcript, error_code)"
            " VALUES (%s, %s, %s, %s::jsonb, %s, 'FAILED_RETRYABLE',"
            " %s::jsonb, %s) RETURNING id",
            [
                str(org_id), str(user_id), surface, _dump(refs or {}),
                goal[:MAX_GOAL], _dump(_failure_turns(goal, error_code)),
                error_code[:120],
            ],
        )
    return {"id": str(record[0]["id"])}


def record_failure(*, job_id: UUID, transcript_before: list, goal: str,
                   error_code: str) -> dict | None:
    """A failed follow-up lands on the existing job after its round rolled
    back: the user turn stays in the transcript and the row goes
    FAILED_RETRYABLE. The WHERE clause binds the write to the generation
    this round actually claimed — post-rollback the row still carries the
    transcript we resumed, so an exact match means the record can never
    overwrite a different round's claim or committed result (their
    transcript has moved on)."""
    with _ai_backend():
        found = rows(
        "UPDATE public.ai_jobs SET state = 'FAILED_RETRYABLE',"
        " transcript = transcript || %s::jsonb, result = NULL, error_code = %s,"
        " updated_at = NOW()"
        " WHERE id = %s AND state NOT IN ('CANCELED','RUNNING')"
        " AND transcript = %s::jsonb"
        " RETURNING id",
        [_dump(_failure_turns(goal, error_code)), error_code[:120],
         str(job_id), _dump(transcript_before)],
    )
    return {"id": str(found[0]["id"])} if found else None


def cancel_job(*, job_id: UUID) -> bool:
    with _ai_backend():
        return bool(
            rows(
                "UPDATE public.ai_jobs SET state = 'CANCELED',"
                " updated_at = NOW(), completed_at = NOW() WHERE id = %s"
                " AND state NOT IN ('SUCCEEDED','FAILED','CANCELED')"
                " RETURNING id",
                [str(job_id)],
            )
        )


# ----------------------------------------------------------------- contract


def _references(raw: Any, allowed: frozenset[str]) -> list[str]:
    """§07-F references point at entity ids the context actually showed."""
    out: list[str] = []
    for item in raw if isinstance(raw, list) else []:
        token = str(item).strip()[:MAX_REFERENCE]
        if token and token in allowed and token not in out:
            out.append(token)
        if len(out) >= MAX_REFERENCES:
            break
    return out


def claims_and_references(
    raw_claims: Any, allowed: frozenset[str]
) -> tuple[list[dict], list[str], int]:
    """A claim is answer text backed by references — entity ids/values that
    literally appear in the projections served to the model. Claims citing
    nothing, or citing ids the context never showed, are dropped and counted
    so the caller can surface honesty instead of a silent invention."""
    claims: list[dict] = []
    references: list[str] = []
    dropped = 0
    for item in raw_claims if isinstance(raw_claims, list) else []:
        if len(claims) >= MAX_CLAIMS or not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()[:MAX_CLAIM]
        if not text:
            continue
        refs = _references(item.get("evidence"), allowed)
        if not refs:
            dropped += 1
            continue
        claims.append({"text": text, "evidence": refs})
        references.extend(ref for ref in refs if ref not in references)
    return claims, references[:MAX_REFERENCES], dropped


def artifacts(raw: Any, allowed: frozenset[str]) -> list[dict]:
    """Validate artifact steps — kind from the allowlist, a title, a bounded
    JSON payload, and references to ids the context exposed. Anything else
    is dropped: an artifact is a draft proposal, never a mutation."""
    out: list[dict] = []
    for item in raw if isinstance(raw, list) else []:
        if len(out) >= MAX_ARTIFACTS_PER_RUN:
            break
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        title = str(item.get("title") or "").strip()[:MAX_ARTIFACT_TITLE]
        payload = item.get("payload")
        if (
            kind not in ARTIFACT_KINDS
            or not title
            or not isinstance(payload, dict)
            or len(_dump(payload)) > MAX_ARTIFACT_BYTES
        ):
            continue
        out.append(
            {
                "kind": kind,
                "title": title,
                "payload": payload,
                "references": _references(item.get("references"), allowed),
            }
        )
    return out


def _decode(record: dict[str, object]) -> dict[str, object]:
    out = dict(record)
    for name in ("refs", "plan", "transcript", "artifacts", "warnings", "result"):
        value = out.get(name)
        if isinstance(value, str):
            out[name] = json.loads(value, parse_float=Decimal, parse_int=Decimal)
    for name in ("id", "org_id", "user_id"):
        if out.get(name) is not None:
            out[name] = str(out[name])
    return out
