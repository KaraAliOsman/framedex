"""Subagents: one task split into a few parallel tasks (P14).

The assistant may divide what the person asked into up to four independent
tasks when they ask for it or when the work is naturally parallel (one per
work, per supplier, per document). Each subtask is an ordinary assistant job:
same person, same workshop, the second factor of the session that delegated
it, the same autonomy and every domain guard of a single task. A subtask
never delegates again, and consequential actions keep their human click.
"""

from __future__ import annotations

from uuid import UUID

MAX_TASKS = 4
MAX_TASK_GOAL = 600


def tasks_from(item: dict) -> list[dict] | None:
    """The validated subtasks of a delegate step, or None when unusable."""
    raw = item.get("tasks")
    if not isinstance(raw, list) or not 2 <= len(raw) <= MAX_TASKS:
        return None
    tasks: list[dict] = []
    for entry in raw:
        if not isinstance(entry, dict):
            return None
        goal = str(entry.get("goal") or "").strip()
        if not goal or len(goal) > MAX_TASK_GOAL:
            return None
        label = str(entry.get("label") or goal).strip()[:80]
        tasks.append({"goal": goal, "label": label})
    if len({task["goal"] for task in tasks}) != len(tasks):
        return None
    return tasks


def spawn(*, org_id: UUID, user_id: UUID, parent_job_id: UUID, step: dict, key: str,
          session_aal: str, autonomy: str, surface: str, refs: dict) -> dict:
    """Enqueue every subtask as its own job; replaying the same step reuses them."""
    from ai_gateway import jobs
    from jobs import service as job_service

    children = []
    for index, task in enumerate(step["tasks"]):
        operation_key = f"{key}:sub:{index}"
        job = jobs.enqueue_job(org_id=org_id, user_id=user_id, surface=surface, refs=refs,
                               goal=task["goal"], operation_key=operation_key)
        with job_service.job_backend():
            job_service.enqueue(
                org_id=org_id,
                job_type="ai.agent.run",
                payload={
                    "session_aal": session_aal if session_aal in ("aal1", "aal2") else "aal1",
                    "ai_job_id": job["id"],
                    "mode": "new",
                    "surface": surface,
                    "refs": refs,
                    "goal": task["goal"],
                    "history": [],
                    "operation_key": operation_key,
                    "autonomy": autonomy,
                    "interaction_mode": "work",
                    "parent_ai_job_id": str(parent_job_id),
                },
                idempotency_key=f"ai:{operation_key}",
                created_by=user_id,
            )
        children.append({"job_id": str(job["id"]), "label": task["label"], "goal": task["goal"]})
    return {"children": children}
