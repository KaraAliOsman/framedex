"""Dirección final 05 · 5 — typed postconditions and the run receipt.

A run is not SUCCEEDED because the provider returned text. After the round
the saved objects are re-read and checked against what the step promised:
positions created/changed/removed with the expected quantity, the project
created, the document composition saved. Solo proponer succeeds with a
complete proposal and never says «Aplicado». Partial work shows Parcial with
the checkpoint to continue; consequential actions stay pending for the
human click the domain requires.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

_GATED = ("ops", "batch_ops", "project_ops", "document_layout", "quote_draft")


def _project_positions(org_id: UUID, project_id: str) -> dict[str, dict] | None:
    from projects.project_ops import snapshot

    try:
        state = snapshot(org_id, UUID(project_id))
    except Exception:  # noqa: BLE001 — a vanished/forbidden project fails the check
        return None
    return {str(position["id"]): position for position in state.get("positions") or []}


def _project_ops_check(org_id: UUID, step: dict) -> tuple[bool, str]:
    simulation = step.get("simulation") or {}
    project_id = str(simulation.get("project_id") or step.get("applied", {}).get("project_id") or "")
    if not project_id:
        return False, "Sin obra de destino."
    saved = _project_positions(org_id, project_id)
    if saved is None:
        return False, "La obra no está disponible."
    problems: list[str] = []
    # New windows get their identity when applied (the service re-simulates),
    # so additions are verified by what was asked — location and quantity —
    # among the saved windows; changes and removals keep their identity.
    from collections import Counter

    expected_adds = Counter(
        (str((change.get("after") or {}).get("location_tag") or ""), int((change.get("after") or {}).get("quantity") or 0))
        for change in simulation.get("diff") or [] if change.get("kind") == "add"
    )
    known = {str((change.get("before") or {}).get("id") or "") for change in simulation.get("diff") or []}
    available = Counter(
        (str(position.get("location_tag") or ""), int(position.get("quantity") or 0))
        for identity, position in saved.items() if identity not in known
    )
    for (location, quantity), count in expected_adds.items():
        if available[(location, quantity)] < count:
            problems.append(f"falta guardar «{location or 'sin ubicación'}» × {quantity}")
    for change in simulation.get("diff") or []:
        kind = change.get("kind")
        after = change.get("after") or {}
        before = change.get("before") or {}
        identity = str((after or before).get("id") or "")
        if kind == "add":
            continue
        if kind == "remove":
            if identity in saved:
                problems.append(f"posición {before.get('position_index')} sigue presente")
            continue
        current = saved.get(identity)
        if current is None:
            problems.append(f"posición {after.get('position_index')} no quedó guardada")
            continue
        if int(current.get("quantity") or 0) != int(after.get("quantity") or 0):
            problems.append(f"posición {after.get('position_index')}: cantidad distinta a la propuesta")
    if problems:
        return False, "; ".join(problems[:4])
    return True, f"{len(simulation.get('diff') or [])} cambio(s) verificados en la obra."


def _object(kind: str, identity: str, label: str, status: str, *, url: str | None = None,
            cause: str | None = None, operation_id: str | None = None) -> dict:
    return {"kind": kind, "id": identity, "label": label[:160], "url": url, "status": status,
            "cause": cause, "operation_id": operation_id}


def build_receipt(*, org_id: UUID, result: dict, interaction_mode: str, autonomy: str,
                  attachments: list[dict] | None = None, outcomes: list[dict] | None = None,
                  turn_index: int | None = None) -> dict:
    steps: list[dict] = list(result.get("steps") or [])
    objects: list[dict] = []
    checks: list[dict] = []
    resolved = {
        (int(item.get("turn_index", -1)), int(item.get("step_index", -1))): item.get("action")
        for item in (outcomes or []) if isinstance(item, dict)
    }
    created = result.get("created_project")
    empty_destination = False
    if created:
        saved_positions = _project_positions(org_id, str(created["project_id"]))
        exists = saved_positions is not None
        objects.append(_object("project", str(created["project_id"]), f"Obra {created.get('code') or ''} {created.get('name') or ''}".strip(),
                               "applied" if exists else "blocked", url=f"/projects/{created['project_id']}",
                               cause=None if exists else "La obra creada no se pudo releer."))
        checks.append({"name": "project_saved", "label": "Obra guardada", "passed": exists,
                       "detail": "" if exists else "La obra no está disponible."})
        # A quotation work opened for an encargo is not a result by itself:
        # without saved windows the task is partial, never complete.
        planned = any(step.get("kind") == "project_ops" for step in steps)
        if exists and not saved_positions and not planned:
            empty_destination = True
            checks.append({"name": "project_has_windows", "label": "Ventanas guardadas en la obra", "passed": False,
                           "detail": "La obra quedó creada sin ventanas."})
    applied_any = False
    pending_any = False
    blocked_any = False
    for index, step in enumerate(steps):
        kind = step.get("kind")
        label = str(step.get("label") or kind or "Paso")
        decision = resolved.get((turn_index, index)) if turn_index is not None else None
        project_id = str((step.get("simulation") or {}).get("project_id") or step.get("project_id") or "")
        url = f"/projects/{project_id}" if project_id else (step.get("path") or None)
        if kind == "prepare":
            # Consequential actions (emit, send, buy, release, pay): prepared,
            # and waiting for the person's click on the real surface.
            pending_any = True
            objects.append(_object("action", f"step-{index}", label, "pending", url=step.get("path"),
                                   cause="Requiere tu clic en la pantalla correspondiente."))
            continue
        if kind not in _GATED:
            continue
        if kind == "quote_draft":
            url = f"/projects/{project_id}?section=quote" if project_id else None
            if step.get("applied") or decision == "applied":
                applied_any = True
                checks.append({"name": f"step_{index}", "label": "Borrador PDF accesible", "passed": True,
                               "detail": "Precio aplicado con las reglas vigentes; borrador sin número comercial."})
                objects.append(_object("quote_draft", f"step-{index}", label, "applied", url=url,
                                       operation_id=(step.get("applied") or {}).get("pricing_operation_id")))
            elif step.get("apply_error"):
                blocked_any = True
                checks.append({"name": f"step_{index}", "label": "Borrador PDF accesible", "passed": False,
                               "detail": str(step["apply_error"])})
                objects.append(_object("quote_draft", f"step-{index}", label, "blocked", url=url,
                                       cause=str(step["apply_error"])))
            else:
                pending_any = True
                objects.append(_object("quote_draft", f"step-{index}", label,
                                       "proposed" if autonomy in ("propose", "approve") or interaction_mode == "chat" else "pending",
                                       url=url))
            continue
        if step.get("applied") or decision == "applied":
            applied = step.get("applied") or {}
            if kind == "project_ops" and step.get("applied"):
                passed, detail = _project_ops_check(org_id, step)
                checks.append({"name": f"step_{index}", "label": label, "passed": passed, "detail": detail})
                if not passed:
                    blocked_any = True
                    objects.append(_object("project_change", f"step-{index}", label, "blocked", url=url, cause=detail,
                                           operation_id=applied.get("operation_id")))
                    continue
            applied_any = True
            objects.append(_object("project_change" if kind != "document_layout" else "document_layout",
                                   f"step-{index}", label, "applied", url=url,
                                   operation_id=applied.get("operation_id")))
        elif decision == "undone":
            objects.append(_object("project_change", f"step-{index}", label, "undone", url=url))
        elif step.get("apply_error") or decision in ("declined", "apply_failed"):
            blocked_any = True
            objects.append(_object("project_change", f"step-{index}", label, "blocked", url=url,
                                   cause=str(step.get("apply_error") or ("Rechazado por ti." if decision == "declined" else "No se pudo aplicar."))))
        else:
            pending_any = True
            objects.append(_object("project_change", f"step-{index}", label,
                                   "proposed" if autonomy in ("propose", "approve") or interaction_mode == "chat" else "pending",
                                   url=url))
    attachment_notes = [item for item in (attachments or []) if not item.get("complete", True)]
    for item in attachments or []:
        checks.append({
            "name": f"attachment_{item.get('id')}",
            "label": f"Lectura de {item.get('file_name')}",
            "passed": bool(item.get("complete", True)),
            "detail": "" if item.get("complete", True) else
            "No procesado: " + ", ".join(str(ref) for ref in (item.get("not_processed") or [])[:8]),
        })
    questions = list(result.get("questions") or [])
    if result.get("clarify"):
        questions.append(str((result.get("clarify") or {}).get("question") or "Falta una precisión."))
    if questions:
        checks.append({"name": "questions", "label": "Datos faltantes", "passed": False,
                       "detail": "; ".join(str(item) for item in questions[:4])[:400]})
    gated = [item for item in objects if item["kind"] != "action"]
    if not gated and not created and not questions and not attachment_notes and not pending_any:
        outcome = "answer"
        summary = "Respuesta con fuentes; sin cambios en tus datos."
    elif blocked_any and not applied_any and not pending_any and not questions and not attachment_notes:
        outcome = "blocked"
        summary = "No se pudo completar: revisa la causa de cada paso."
    elif interaction_mode == "chat" or autonomy == "propose":
        outcome = "partial" if questions or attachment_notes else "proposal"
        summary = "Propuesta lista para revisar; nada se aplicó." if outcome == "proposal" else \
            "Propuesta parcial: faltan datos o partes del archivo por leer."
    elif autonomy == "approve" and pending_any and not applied_any:
        outcome = "partial" if questions or attachment_notes else "proposal"
        summary = "Conjunto preparado; se aplica con tu aprobación." if outcome == "proposal" else \
            "Conjunto parcial: faltan datos para completar el encargo."
    elif empty_destination or blocked_any or questions or attachment_notes or any(item["status"] == "proposed" for item in gated):
        outcome = "partial"
        summary = "Parcial: lo independiente quedó hecho; revisa lo pendiente."
    else:
        outcome = "complete"
        summary = "Cambios aplicados y verificados."
    checkpoint = None
    if outcome == "partial":
        missing = [item["label"] for item in objects if item["status"] in ("pending", "blocked", "proposed")]
        checkpoint = ("Continúa con: " + "; ".join(missing[:4])) if missing else (
            "La obra está creada; pide «continúa» para agregar las ventanas." if empty_destination else
            "Responde lo que falta para continuar." if questions else "Revisa las partes no leídas del archivo.")
    return {
        "outcome": outcome,
        "summary": summary,
        "autonomy": autonomy,
        "interaction_mode": interaction_mode,
        "objects": objects[:60],
        "checks": checks[:40],
        "attachments": list(attachments or [])[:6],
        "credits": int(result["credits_debited"]) if isinstance(result.get("credits_debited"), int) else None,
        "checkpoint": checkpoint,
    }


def refresh_receipt(*, org_id: UUID, job: dict) -> dict | None:
    """Recompute after the person approves/declines/undoes a step."""
    transcript: list[Any] = list(job.get("transcript") or [])
    for turn_index in range(len(transcript) - 1, -1, -1):
        turn = transcript[turn_index]
        if isinstance(turn, dict) and turn.get("role") == "agent":
            previous = job.get("receipt") or {}
            return build_receipt(
                org_id=org_id,
                result={**turn, "credits_debited": (job.get("result") or {}).get("credits_debited"),
                        "created_project": (job.get("result") or {}).get("created_project")},
                interaction_mode=str(previous.get("interaction_mode") or job.get("interaction_mode") or "work"),
                autonomy=str(previous.get("autonomy") or job.get("autonomy") or "propose"),
                attachments=list(previous.get("attachments") or []),
                outcomes=list(job.get("outcomes") or []),
                turn_index=turn_index,
            )
    return None


__all__ = ["build_receipt", "refresh_receipt"]
