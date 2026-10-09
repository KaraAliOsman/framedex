"""One explicit, retry-safe supervisory decision: reject and remake."""

from uuid import UUID

from django.db import transaction

from documents.repository import DocumentaryError, documentary_backend, one, rows
from production import service


def reject_and_remake(
    *, org_id: UUID, order_id: UUID, actor_id: UUID, actor_role: str,
    confirmed: bool, operation_key: UUID, note: str, item_code: str,
) -> dict:
    if actor_role not in {"OWNER", "WORKSHOP_MANAGER"}:
        raise DocumentaryError("qc_requires_supervisor")
    if not confirmed or not note.strip():
        raise DocumentaryError("qc_confirmation_required")
    with transaction.atomic(), documentary_backend():
        one(
            "SELECT id FROM public.orders WHERE id = %s AND org_id = %s "
            "AND order_type = 'WORKSHOP_OT' FOR UPDATE",
            [str(order_id), str(org_id)], "work_order_not_found",
        )
        existing = rows(
            "SELECT id FROM public.orders WHERE org_id = %s "
            "AND payload_json->>'remake_of' = %s AND payload_json->>'qc_operation_key' = %s",
            [str(org_id), str(order_id), str(operation_key)],
        )
        if existing:
            return service.get_work_order(org_id=org_id, order_id=existing[0]["id"])
        step = one(
            "SELECT id, code FROM public.production_steps "
            "WHERE order_id = %s AND org_id = %s AND status <> 'DONE' "
            "ORDER BY sequence LIMIT 1",
            [str(order_id), str(org_id)], "production_step_not_found",
        )
        if step["code"] != "QC":
            raise DocumentaryError("step_sequence_blocked")
        service.transition_step(
            org_id=org_id, step_id=step["id"], actor_id=actor_id, actor_role=actor_role,
            action="QC_CHECK", note=note, block_on_fail=True,
            qc_check={"check": note, "expected": "", "actual": "", "result": "FAIL", "item_code": item_code},
        )
        return service.create_remake(
            org_id=org_id, order_id=order_id, actor_id=actor_id,
            note=note, operation_key=operation_key,
        )
