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
from decimal import Decimal
from typing import Any
from uuid import UUID


from pricing.repository import rows

MAX_GOAL = 2000
MAX_ARTIFACT_TITLE = 120
MAX_ARTIFACT_BYTES = 32768
MAX_CLAIM = 240
MAX_CLAIMS = 8
MAX_REFERENCE = 120
MAX_REFERENCES = 12
MAX_ARTIFACTS_PER_RUN = 6

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
        "quote_draft",
        "catalog_candidates",
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
    record = rows(
        "INSERT INTO public.ai_jobs (org_id, user_id, surface, refs, goal, state)"
        " VALUES (%s, %s, %s, %s::jsonb, %s, 'RUNNING')"
        " RETURNING id, org_id, user_id, surface, refs, goal, state, plan,"
        " transcript, artifacts, warnings, result, error_code,"
        " created_at, updated_at, completed_at",
        [str(org_id), str(user_id), surface, _dump(refs or {}), goal[:MAX_GOAL]],
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


def list_jobs(*, org_id: UUID, user_id: UUID, limit: int = 30) -> list[dict]:
    return [
        _decode(row)
        for row in rows(
            "SELECT id, org_id, user_id, surface, refs, goal, state,"
            " artifacts, warnings, result, error_code,"
            " created_at, updated_at, completed_at"
            " FROM public.ai_jobs WHERE org_id = %s AND user_id = %s"
            " ORDER BY created_at DESC LIMIT %s",
            [str(org_id), str(user_id), limit],
        )
    ]


def finish_job(*, job_id: UUID, state: str, transcript: list,
               artifacts: list, warnings: list, result: dict | None,
               error_code: str | None = None) -> dict:
    record = rows(
        "UPDATE public.ai_jobs SET state = %s, transcript = %s::jsonb,"
        " artifacts = %s::jsonb, warnings = %s::jsonb, result = %s::jsonb,"
        " error_code = %s, updated_at = NOW(),"
        " completed_at = CASE WHEN %s IN ('SUCCEEDED','FAILED','CANCELED')"
        " THEN NOW() ELSE completed_at END"
        " WHERE id = %s AND state NOT IN ('SUCCEEDED','FAILED','CANCELED')"
        " RETURNING id",
        [
            state, _dump(transcript), _dump(artifacts), _dump(warnings),
            _dump(result) if result is not None else None, error_code,
            state, str(job_id),
        ],
    )
    if not record:
        raise ValueError("ai_job_terminal")
    return {"id": str(record[0]["id"])}


def resume_job(*, job_id: UUID, transcript: list) -> dict:
    """A follow-up message reopens a settled/open job: transcript already
    carries the new user turn; state goes back to RUNNING."""
    record = rows(
        "UPDATE public.ai_jobs SET state = 'RUNNING', transcript = %s::jsonb,"
        " result = NULL, error_code = NULL, completed_at = NULL, updated_at = NOW()"
        " WHERE id = %s AND state NOT IN ('CANCELED')"
        " RETURNING id",
        [_dump(transcript), str(job_id)],
    )
    if not record:
        raise ValueError("ai_job_terminal")
    return {"id": str(record[0]["id"])}


def cancel_job(*, job_id: UUID) -> bool:
    return bool(
        rows(
            "UPDATE public.ai_jobs SET state = 'CANCELED', updated_at = NOW(),"
            " completed_at = NOW() WHERE id = %s"
            " AND state NOT IN ('SUCCEEDED','FAILED','CANCELED') RETURNING id",
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
