"""Dirección final 05 — private conversation threads for the global copilot.

A thread is the identity of a conversation per organization/person. It
groups the durable jobs (Trabajo) and the legacy ask turns (Chat) without a
second job engine: transcripts, artifacts, outcomes and receipts stay on the
job rows. The write destination is sealed on each job/turn, never on the
thread, so navigating the app never redirects a running task.

Reads run under the caller's RLS (org + user); writes under ai_backend. A
thread id grants nothing by itself — every query re-checks org and user.
Loading history, reopening a thread or restoring persisted state never calls
the model.
"""

from __future__ import annotations

import base64
import binascii
from datetime import datetime
from typing import Any
from uuid import UUID

from ai_gateway.jobs import _ai_backend
from pricing.repository import rows

MAX_TITLE = 120
PAGE = 20
MODES = ("chat", "work")
AUTONOMY = ("propose", "approve", "draft")

_COLUMNS = (
    "id, org_id, user_id, title, interaction_mode, autonomy, origin, legacy_key,"
    " archived_at, created_at, updated_at, last_activity_at"
)


class ThreadError(Exception):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


def title_from(text: str) -> str:
    """First line of the first request, trimmed — editable later."""
    words = " ".join(str(text or "").split())
    return (words[: MAX_TITLE - 1] + "…") if len(words) > MAX_TITLE else (words or "Conversación")


def _public(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "title": row["title"],
        "interaction_mode": row["interaction_mode"],
        "autonomy": row["autonomy"],
        "origin": row["origin"],
        "archived": row["archived_at"] is not None,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "last_activity_at": row["last_activity_at"],
    }


def _encode_cursor(moment: datetime, identifier: Any) -> str:
    raw = f"{moment.isoformat()}|{identifier}".encode()
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_cursor(cursor: str | None) -> tuple[str, str] | None:
    if not cursor:
        return None
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        moment, identifier = base64.urlsafe_b64decode(padded.encode()).decode().split("|", 1)
        datetime.fromisoformat(moment)
        UUID(identifier)
    except (ValueError, binascii.Error, UnicodeDecodeError):
        raise ThreadError("ai_thread_cursor_invalid", "El cursor del historial no es válido.") from None
    return moment, identifier


def create(*, org_id: UUID, user_id: UUID, title: str = "", interaction_mode: str = "chat",
           autonomy: str = "approve") -> dict:
    if interaction_mode not in MODES or autonomy not in AUTONOMY:
        raise ThreadError("ai_thread_invalid", "Modo o política no válidos.")
    with _ai_backend():
        row = rows(
            f"INSERT INTO public.ai_threads (org_id, user_id, title, interaction_mode, autonomy)"
            f" VALUES (%s, %s, %s, %s, %s) RETURNING {_COLUMNS}",
            [str(org_id), str(user_id), title_from(title), interaction_mode, autonomy],
        )[0]
    return _public(row)


def get(*, org_id: UUID, user_id: UUID, thread_id: UUID) -> dict | None:
    found = rows(
        f"SELECT {_COLUMNS} FROM public.ai_threads WHERE id=%s AND org_id=%s AND user_id=%s",
        [str(thread_id), str(org_id), str(user_id)],
    )
    return _public(found[0]) if found else None


def require(*, org_id: UUID, user_id: UUID, thread_id: UUID) -> dict:
    thread = get(org_id=org_id, user_id=user_id, thread_id=thread_id)
    if thread is None:
        # Another person's or another tenant's thread is indistinguishable
        # from a missing one.
        raise ThreadError("ai_thread_not_found", "La conversación no existe.")
    return thread


def update(*, org_id: UUID, user_id: UUID, thread_id: UUID, title: str | None = None,
           archived: bool | None = None, interaction_mode: str | None = None,
           autonomy: str | None = None) -> dict:
    require(org_id=org_id, user_id=user_id, thread_id=thread_id)
    sets: list[str] = []
    params: list[Any] = []
    if title is not None:
        clean = " ".join(title.split())[:MAX_TITLE]
        if not clean:
            raise ThreadError("ai_thread_invalid", "El título no puede quedar vacío.")
        sets.append("title=%s")
        params.append(clean)
    if archived is not None:
        sets.append("archived_at=" + ("now()" if archived else "NULL"))
    if interaction_mode is not None:
        if interaction_mode not in MODES:
            raise ThreadError("ai_thread_invalid", "Modo no válido.")
        sets.append("interaction_mode=%s")
        params.append(interaction_mode)
    if autonomy is not None:
        if autonomy not in AUTONOMY:
            raise ThreadError("ai_thread_invalid", "Política no válida.")
        # A preference change governs new tasks only; each job keeps the
        # policy sealed when it was sent.
        sets.append("autonomy=%s")
        params.append(autonomy)
    if not sets:
        return require(org_id=org_id, user_id=user_id, thread_id=thread_id)
    sets.append("updated_at=now()")
    with _ai_backend():
        row = rows(
            f"UPDATE public.ai_threads SET {', '.join(sets)} WHERE id=%s AND org_id=%s AND user_id=%s"
            f" RETURNING {_COLUMNS}",
            [*params, str(thread_id), str(org_id), str(user_id)],
        )[0]
    return _public(row)


def touch(*, org_id: UUID, user_id: UUID, thread_id: UUID) -> None:
    with _ai_backend():
        rows(
            "UPDATE public.ai_threads SET last_activity_at=now(), updated_at=now()"
            " WHERE id=%s AND org_id=%s AND user_id=%s RETURNING id",
            [str(thread_id), str(org_id), str(user_id)],
        )


def list_threads(*, org_id: UUID, user_id: UUID, query: str = "", archived: bool = False,
                 cursor: str | None = None, limit: int = PAGE) -> dict:
    limit = max(1, min(int(limit), 50))
    clauses = ["t.org_id=%s", "t.user_id=%s", "t.archived_at IS " + ("NOT NULL" if archived else "NULL")]
    params: list[Any] = [str(org_id), str(user_id)]
    term = " ".join(str(query or "").split())[:120]
    if term:
        # Title or any goal of its jobs — never another person's rows (RLS
        # and the explicit user filter both apply).
        clauses.append(
            "(t.title ILIKE %s OR EXISTS (SELECT 1 FROM public.ai_jobs j WHERE j.thread_id=t.id"
            " AND j.org_id=t.org_id AND j.user_id=t.user_id AND j.goal ILIKE %s))"
        )
        like = "%" + term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        params += [like, like]
    decoded = _decode_cursor(cursor)
    if decoded:
        clauses.append("(t.last_activity_at, t.id) < (%s::timestamptz, %s::uuid)")
        params += list(decoded)
    found = rows(
        f"SELECT {', '.join('t.' + c.strip() for c in _COLUMNS.split(','))} FROM public.ai_threads t"
        f" WHERE {' AND '.join(clauses)} ORDER BY t.last_activity_at DESC, t.id DESC LIMIT %s",
        [*params, limit + 1],
    )
    page = found[:limit]
    next_cursor = (
        _encode_cursor(page[-1]["last_activity_at"], page[-1]["id"]) if len(found) > limit else None
    )
    return {"items": [_public(row) for row in page], "next_cursor": next_cursor}


def _json(value: Any) -> Any:
    """jsonb columns arrive as text from the repository helper."""
    import json

    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return None
    return value


def _job_entry(row: dict) -> dict:
    return {
        "kind": "job",
        "id": str(row["id"]),
        "created_at": row["created_at"],
        "goal": row["goal"],
        "state": row["state"],
        "surface": row["surface"],
        "refs": _json(row["refs"]) or {},
        "interaction_mode": row["interaction_mode"] or "work",
        "autonomy": row["autonomy"] or "propose",
        "receipt": _json(row["receipt"]),
        "error_code": row["error_code"],
        "question": None,
        "answer": None,
    }


def _ask_entry(row: dict) -> dict:
    answer = _json(row["answer"])
    answer = answer if isinstance(answer, dict) else {}
    return {
        "kind": "ask",
        "id": str(row["id"]),
        "created_at": row["created_at"],
        "goal": None,
        "state": None,
        "surface": row["surface"],
        "refs": _json(row["refs"]) or {},
        "interaction_mode": "chat",
        "autonomy": "propose",
        "receipt": None,
        "error_code": None,
        "question": row["question"],
        "answer": str(answer.get("answer") or answer.get("text") or "")[:4000] or None,
    }


def timeline(*, org_id: UUID, user_id: UUID, thread_id: UUID, cursor: str | None = None,
             limit: int = PAGE) -> dict:
    """Newest first with a stable (created_at, id) cursor; errors and
    cancellations stay visible. Pure read — never consults the model."""
    require(org_id=org_id, user_id=user_id, thread_id=thread_id)
    limit = max(1, min(int(limit), 50))
    decoded = _decode_cursor(cursor)
    bound = " AND (created_at, id) < (%s::timestamptz, %s::uuid)" if decoded else ""
    extra = list(decoded) if decoded else []
    scope = [str(thread_id), str(org_id), str(user_id)]
    jobs_found = rows(
        "SELECT id, created_at, goal, state, surface, refs, interaction_mode, autonomy, receipt, error_code"
        " FROM public.ai_jobs WHERE thread_id=%s AND org_id=%s AND user_id=%s" + bound
        + " ORDER BY created_at DESC, id DESC LIMIT %s",
        [*scope, *extra, limit + 1],
    )
    asks_found = rows(
        "SELECT id, created_at, surface, refs, question, answer FROM public.ai_ask_turns"
        " WHERE thread_id=%s AND org_id=%s AND user_id=%s" + bound
        + " ORDER BY created_at DESC, id DESC LIMIT %s",
        [*scope, *extra, limit + 1],
    )
    merged = sorted(
        [_job_entry(row) for row in jobs_found] + [_ask_entry(row) for row in asks_found],
        key=lambda item: (item["created_at"], item["id"]),
        reverse=True,
    )
    page = merged[:limit]
    next_cursor = _encode_cursor(page[-1]["created_at"], page[-1]["id"]) if len(merged) > limit else None
    return {"items": page, "next_cursor": next_cursor}


def latest_open_job(*, org_id: UUID, user_id: UUID, thread_id: UUID) -> dict | None:
    found = rows(
        "SELECT id, state FROM public.ai_jobs WHERE thread_id=%s AND org_id=%s AND user_id=%s"
        " ORDER BY created_at DESC, id DESC LIMIT 1",
        [str(thread_id), str(org_id), str(user_id)],
    )
    return found[0] if found else None


def link_job(*, org_id: UUID, user_id: UUID, job_id: UUID, thread_id: UUID,
             interaction_mode: str, autonomy: str) -> None:
    """Seal the conversation, mode and effective policy on the job row."""
    from django.db import connection

    if connection.vendor != "postgresql":
        return
    with _ai_backend():
        rows(
            "UPDATE public.ai_jobs SET thread_id=%s, interaction_mode=%s, autonomy=%s"
            " WHERE id=%s AND org_id=%s AND user_id=%s RETURNING id",
            [str(thread_id), interaction_mode, autonomy, str(job_id), str(org_id), str(user_id)],
        )
    touch(org_id=org_id, user_id=user_id, thread_id=thread_id)


__all__ = [
    "AUTONOMY", "MODES", "ThreadError", "create", "get", "link_job", "list_threads",
    "require", "timeline", "title_from", "touch", "update", "latest_open_job",
]
