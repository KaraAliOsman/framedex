"""«Deshacer todo» for one assistant job (P08).

Every reversible change the job saved — its window operations, newest first
— is undone through the same project service the manual review uses, and a
draft work the job itself created is removed once it is empty again. A
change made afterwards by a person stops the chain: nothing older is undone
over it, and the response says what was kept and why.
"""

from __future__ import annotations

from uuid import UUID

from django.db import transaction

from ai_gateway import jobs
from pricing.repository import rows


def _applied(job: dict) -> list[dict]:
    """Applied window operations still standing, newest first."""
    outcomes = [item for item in job.get("outcomes") or [] if isinstance(item, dict)]
    undone = {(item.get("turn_index"), item.get("step_index"))
              for item in outcomes if item.get("action") == "undone"}
    transcript = job.get("transcript") or []
    found = []
    for item in outcomes:
        key = (item.get("turn_index"), item.get("step_index"))
        if item.get("action") != "applied" or not item.get("operation_id") or key in undone:
            continue
        turn = transcript[key[0]] if isinstance(key[0], int) and 0 <= key[0] < len(transcript) else {}
        steps = turn.get("steps") or [] if isinstance(turn, dict) else []
        step = steps[key[1]] if isinstance(key[1], int) and 0 <= key[1] < len(steps) else {}
        project_id = (step.get("applied") or {}).get("project_id") or (step.get("simulation") or {}).get("project_id")
        if project_id:
            found.append({"turn_index": key[0], "step_index": key[1],
                          "operation_id": str(item["operation_id"]), "project_id": str(project_id)})
    return list(reversed(found))


def _created_project(job: dict) -> str | None:
    created = (job.get("result") or {}).get("created_project") or {}
    return str(created["project_id"]) if created.get("project_id") else None


def _remove_empty_draft(org_id: UUID, project_id: str) -> str | None:
    """Delete the work the job created when nothing of it remains; any
    dependent record (a price, a document, a person's later edit) keeps it."""
    counted = rows(
        "SELECT p.status, (SELECT count(*) FROM public.project_positions q"
        " WHERE q.project_id = p.id AND q.org_id = p.org_id) AS positions"
        " FROM public.projects p WHERE p.id = %s AND p.org_id = %s",
        [project_id, org_id],
    )
    if not counted:
        return "removed"
    if counted[0]["status"] != "DRAFT" or int(counted[0]["positions"]):
        return "kept"
    try:
        with transaction.atomic():
            rows("DELETE FROM public.projects WHERE id = %s AND org_id = %s AND status = 'DRAFT' RETURNING id",
                 [project_id, org_id])
    except Exception:  # noqa: BLE001 — dependent records keep the empty draft
        return "kept"
    return "removed"


def undo_all(*, org_id: UUID, user_id: UUID, job_id: UUID) -> dict:
    from projects.project_ops import undo_project_operations

    job = jobs.get_job(org_id=org_id, user_id=user_id, job_id=job_id)
    if job is None:
        raise LookupError("ai_job_not_found")
    undone: list[dict] = []
    kept: list[dict] = []
    for item in _applied(job):
        try:
            with transaction.atomic():
                undo_project_operations(org_id, user_id, UUID(item["project_id"]), UUID(item["operation_id"]))
        except Exception as error:  # noqa: BLE001 — a later human edit stops the chain
            kept.append({**item, "reason": str(getattr(error, "public_detail", None)
                                               or "La obra cambió después; revísala antes de deshacer.")[:240]})
            break
        undone.append(item)
    if undone:
        jobs.record_assistant_outcomes(job_id=job_id, entries=[
            {"turn_index": item["turn_index"], "step_index": item["step_index"], "action": "undone",
             "ops": ["undo_all"], "recorded_by": "human", "operation_id": item["operation_id"]}
            for item in undone
        ])
    project = _created_project(job)
    project_state = None
    if project and not kept:
        project_state = _remove_empty_draft(org_id, project)
    return {"job_id": str(job_id), "undone": len(undone), "kept": kept,
            "created_project": project, "project_state": project_state}


__all__ = ["undo_all"]
