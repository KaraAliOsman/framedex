"""Human read projections. Every referenced entity is resolved in this tenant."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from pricing.repository import rows
from jobs import registry


def _id(value: object) -> str | None:
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError):
        return None


def context_identity(*, org_id: UUID, refs: dict, surface: str = "") -> dict:
    """Identifiers supplied by a job never authorize a read or a link."""
    order_id = _id(refs.get("order_id") or refs.get("work_order_id"))
    if order_id:
        found = rows(
            "SELECT id,order_type, CASE WHEN order_type='WORKSHOP_OT' THEN order_code "
            "ELSE private.entity_code(org_id,'OC',id,order_code) END AS code "
            "FROM public.orders WHERE org_id=%s AND id=%s",
            [str(org_id), order_id],
        )
        if found:
            destination = "production" if found[0]["order_type"] == "WORKSHOP_OT" else "purchasing"
            return {"context_label": str(found[0]["code"]), "context_url": f"/{destination}?order={order_id}"}
        return {"context_label": "Orden no disponible", "context_url": None}
    position_id = _id(refs.get("position_id"))
    project_id = _id(refs.get("project_id"))
    version_id = _id(refs.get("project_version_id") or refs.get("version_id"))
    if position_id:
        found = rows(
            "SELECT p.id AS project_id,p.code,pos.position_index,pos.location_tag "
            "FROM public.project_positions pos JOIN public.projects p "
            "ON p.id=pos.project_id AND p.org_id=pos.org_id "
            "WHERE pos.org_id=%s AND pos.id=%s "
            "AND (%s::uuid IS NULL OR pos.project_id=%s::uuid)",
            [str(org_id), position_id, project_id, project_id],
        )
        if found:
            item = found[0]
            label = f"Pos. {int(item['position_index']):02d}"
            if item.get("location_tag"):
                label += f" {item['location_tag']}"
            return {"context_label": f"{label} · {item['code']}", "context_url": f"/projects/{item['project_id']}/positions/{position_id}/edit"}
        return {"context_label": "Posición no disponible", "context_url": None}
    if version_id and not project_id:
        found = rows("SELECT project_id FROM public.project_versions WHERE org_id=%s AND id=%s", [str(org_id), version_id])
        if found:
            project_id = str(found[0]["project_id"])
    if project_id:
        found = rows("SELECT code,name FROM public.projects WHERE org_id=%s AND id=%s", [str(org_id), project_id])
        if found:
            return {"context_label": f"{found[0]['code']} · {found[0]['name']}", "context_url": f"/projects/{project_id}"}
        return {"context_label": "Proyecto no disponible", "context_url": None}
    if version_id:
        return {"context_label": "Revisión no disponible", "context_url": None}
    client_id = _id(refs.get("client_id"))
    if client_id:
        found = rows("SELECT name FROM public.clients WHERE org_id=%s AND id=%s", [str(org_id), client_id])
        return {"context_label": str(found[0]["name"]) if found else "Cliente no disponible", "context_url": f"/clients/{client_id}" if found else None}
    labels = {"position": "Posición nueva", "project": "Proyecto", "quotation": "Precios", "production": "Producción", "work_order": "Orden de trabajo", "purchasing": "Compras", "catalog": "Catálogo", "clients": "Clientes", "client": "Cliente", "settings": "Ajustes", "dashboard": "Inicio", "assistant": "Asistente", "jobs": "Trabajos"}
    return {"context_label": labels.get(surface, "Trabajo de organización"), "context_url": None}


def duration_ms(job: dict) -> int | None:
    start = job.get("started_at")
    end = job.get("completed_at") or datetime.now(timezone.utc)
    if isinstance(start, str):
        start = datetime.fromisoformat(start.replace("Z", "+00:00"))
    if isinstance(end, str):
        end = datetime.fromisoformat(end.replace("Z", "+00:00"))
    if not isinstance(start, datetime) or not isinstance(end, datetime):
        return None
    delta = end - start
    return max(0, delta.days * 86_400_000 + delta.seconds * 1000 + delta.microseconds // 1000)


def retry_allowed(job: dict, *, role: str, actor_id: UUID) -> bool:
    if job.get("state") not in {"FAILED", "CANCELED"}:
        return False
    spec = registry.spec_for(str(job.get("type")))
    if spec is None or role not in spec.roles:
        return False
    payload = job.get("payload") or {}
    serializer = spec.payload_serializer(data=payload)
    if not serializer.is_valid():
        return False
    if spec.authorize and not spec.authorize(dict(serializer.validated_data), role):
        return False
    if job.get("type") == "ai.agent.run":
        return False  # AI retries use the owner-bound /ai/jobs/<id>/retry/ endpoint.
    return True


def present_job(job: dict, *, org_id: UUID, role: str, actor_id: UUID) -> dict:
    payload = job.get("payload") or {}
    refs = job.get("context_refs") or payload
    result = {**job, **context_identity(org_id=org_id, refs=refs, surface=str(job.get("surface") or ""))}
    actor = _id(job.get("created_by"))
    label = None
    if actor:
        found = rows(
            "SELECT u.email FROM auth.users u JOIN public.tenancy_memberships m "
            "ON m.user_id=u.id WHERE m.org_id=%s AND u.id=%s LIMIT 1",
            [str(org_id), actor],
        )
        if found:
            label = found[0].get("email")
    result.update(actor_label=label or ("Sistema" if not actor else "Usuario no disponible"), duration_ms=duration_ms(job), can_retry=retry_allowed(job, role=role, actor_id=actor_id))
    result["result_label"] = {"QUEUED": "Esperando turno", "RUNNING": "En ejecución", "FAILED": "Falló", "CANCELED": "Cancelado", "SUCCEEDED": "Trabajo terminado"}.get(str(job.get("state")), "Estado no disponible")
    if job.get("type") == "ai.agent.run" and job.get("state") == "SUCCEEDED":
        result["result_label"] = "Respuesta preparada · revisa el trabajo de IA"
    return result
