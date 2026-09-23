"""Cobranza ledger for a project's commercial deal.

Payments are recorded by the sales side against the deal amount (the latest
sealed revision's gross total, else the live project totals). Recording is
idempotent on (org_id, operation_key) and a mistake is voided, never deleted —
the ledger keeps the full history.
"""

import json
from decimal import Decimal
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from authentication.errors import contract_error
from documents.repository import documentary_backend
from pricing.repository import rows
from projects.service import project_row


def _payment_public(row):
    return {
        "id": str(row["id"]),
        "kind": row["kind"],
        "amount": str(row["amount"]),
        "method": row["method"],
        "reference": row["reference"],
        "note": row["note"],
        "recorded_by": str(row["recorded_by"]) if row["recorded_by"] else None,
        "recorded_at": row["recorded_at"].isoformat()
        if hasattr(row["recorded_at"], "isoformat")
        else row["recorded_at"],
        "voided_at": row["voided_at"].isoformat()
        if row["voided_at"] and hasattr(row["voided_at"], "isoformat")
        else row["voided_at"],
        "void_reason": row["void_reason"],
        "created_at": row["created_at"].isoformat()
        if hasattr(row["created_at"], "isoformat")
        else row["created_at"],
    }


def _deal_total(org_id: UUID, project_id: UUID, project: dict) -> Decimal | None:
    """The deal amount: latest sealed revision's gross total, else live totals."""
    with documentary_backend():
        versions = rows(
            "SELECT snapshot_json::text AS snapshot_json FROM public.project_versions "
            "WHERE org_id=%s AND project_id=%s ORDER BY emitted_at DESC,id DESC LIMIT 1",
            [str(org_id), str(project_id)],
        )
    if versions:
        snapshot = versions[0]["snapshot_json"]
        if isinstance(snapshot, str):
            snapshot = json.loads(snapshot)
        sealed_project = snapshot.get("project") if isinstance(snapshot, dict) else None
        gross = (sealed_project or {}).get("total_price_gross")
        if gross is not None:
            return Decimal(str(gross))
    gross = project.get("total_price_gross")
    return Decimal(str(gross)) if gross is not None else None


def _summary(org_id: UUID, project_id: UUID, project: dict) -> dict:
    with documentary_backend():
        payments = rows(
            "SELECT * FROM public.project_payments "
            "WHERE org_id=%s AND project_id=%s ORDER BY recorded_at,id",
            [str(org_id), str(project_id)],
        )
    collected = sum(
        (Decimal(str(p["amount"])) for p in payments if p["voided_at"] is None),
        Decimal("0"),
    )
    total = _deal_total(org_id, project_id, project)
    balance = (total - collected) if total is not None else None
    if total is None:
        status = "NO_DEAL"
    elif collected <= 0:
        status = "PENDING"
    elif balance > 0:
        status = "PARTIAL"
    else:
        status = "PAID"
    return {
        "payments": [_payment_public(p) for p in payments],
        "collected": str(collected),
        "quote_total_gross": str(total) if total is not None else None,
        "balance": str(balance) if balance is not None else None,
        "status": status,
    }


def list_payments(*, org_id: UUID, project_id: UUID) -> dict:
    project = project_row(org_id, project_id)
    return _summary(org_id, project_id, project)


def record_payment(*, org_id: UUID, project_id: UUID, actor_id: UUID, data: dict) -> dict:
    project = project_row(org_id, project_id)
    with transaction.atomic(), documentary_backend():
        existing = rows(
            "SELECT * FROM public.project_payments WHERE org_id=%s AND operation_key=%s",
            [str(org_id), data["operation_key"]],
        )
        if existing:
            payment = existing[0]
            if str(payment["project_id"]) != str(project_id):
                raise contract_error(
                    409, "payment_operation_conflict", "La operación ya fue registrada en otro proyecto."
                )
        else:
            payment = rows(
                "INSERT INTO public.project_payments"
                "(org_id,project_id,operation_key,kind,amount,method,reference,note,"
                " recorded_by,recorded_at) "
                "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *",
                [
                    str(org_id),
                    str(project_id),
                    data["operation_key"],
                    data["kind"],
                    data["amount"],
                    data["method"],
                    data.get("reference") or None,
                    data.get("note") or None,
                    str(actor_id),
                    data.get("recorded_at") or timezone.now(),
                ],
            )[0]
    return {"payment": _payment_public(payment), **_summary(org_id, project_id, project)}


def void_payment(*, org_id: UUID, project_id: UUID, payment_id: UUID, actor_id: UUID, data: dict) -> dict:
    project = project_row(org_id, project_id)
    with transaction.atomic(), documentary_backend():
        found = rows(
            "UPDATE public.project_payments SET voided_at=%s, voided_by=%s, void_reason=%s "
            "WHERE org_id=%s AND project_id=%s AND id=%s AND voided_at IS NULL "
            "RETURNING *",
            [
                timezone.now(),
                str(actor_id),
                data.get("reason") or None,
                str(org_id),
                str(project_id),
                str(payment_id),
            ],
        )
        if not found:
            found = rows(
                "SELECT * FROM public.project_payments "
                "WHERE org_id=%s AND project_id=%s AND id=%s",
                [str(org_id), str(project_id), str(payment_id)],
            )
            if not found:
                raise contract_error(404, "payment_not_found", "El pago no está disponible.")
    return _summary(org_id, project_id, project)
