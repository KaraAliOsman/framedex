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
from projects import sii
from projects.receipts import _receipt_public, issue_receipt
from projects.service import project_row


def _payment_public(row, receipt=None):
    return {
        "id": str(row["id"]),
        "receipt_id": str(receipt["id"]) if receipt else None,
        "receipt_code": receipt["receipt_code"] if receipt else None,
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


def _deal(org_id: UUID, project_id: UUID, project: dict) -> dict | None:
    """The commercial deal: latest sealed revision's gross total and currency,
    else live totals when an applied pricing authority proves the project was
    priced. Zero-valued live totals without that authority are not a deal."""
    with documentary_backend():
        versions = rows(
            "SELECT revision_code,snapshot_json::text AS snapshot_json "
            "FROM public.project_versions "
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
            return {
                "total": Decimal(str(gross)),
                "currency": (sealed_project or {}).get("currency") or "CLP",
                "sealed_revision": versions[0]["revision_code"],
            }
    with documentary_backend():
        applied = rows(
            "SELECT currency FROM private.applied_pricing_currency(%s,%s)",
            [str(org_id), str(project_id)],
        )
        if not applied:
            return None
        org = rows(
            "SELECT currency FROM public.tenancy_organizations WHERE id=%s", [str(org_id)]
        )
    return {
        "total": Decimal(str(project["total_price_gross"])),
        "currency": applied[0]["currency"] or (org[0]["currency"] if org else "CLP"),
        "sealed_revision": None,
    }


def _summary(org_id: UUID, project_id: UUID, project: dict) -> dict:
    with documentary_backend():
        payments = rows(
            "SELECT * FROM public.project_payments "
            "WHERE org_id=%s AND project_id=%s ORDER BY recorded_at,id",
            [str(org_id), str(project_id)],
        )
        receipts = {
            str(receipt["payment_id"]): receipt
            for receipt in rows(
                "SELECT id,payment_id,receipt_code FROM public.payment_receipts "
                "WHERE org_id=%s AND project_id=%s",
                [str(org_id), str(project_id)],
            )
        }
        credit_notes = {
            str(note["invoice_id"]): {
                "id": str(note["id"]),
                "credit_code": note["credit_code"],
                "invoice_id": str(note["invoice_id"]),
                "created_at": note["created_at"].isoformat()
                if hasattr(note["created_at"], "isoformat")
                else note["created_at"],
            }
            for note in rows(
                "SELECT id,invoice_id,credit_code,created_at "
                "FROM public.project_credit_notes "
                "WHERE org_id=%s AND project_id=%s",
                [str(org_id), str(project_id)],
            )
        }
        dtes = sii.dtes_by_invoice(org_id=org_id, project_id=project_id)
        credit_dtes = sii.dtes_by_credit_note(org_id=org_id, project_id=project_id)
        invoices = [
            {
                "id": str(invoice["id"]),
                "invoice_code": invoice["invoice_code"],
                "project_id": str(project_id),
                "revision_code": (
                    invoice["payload_json"]
                    if isinstance(invoice["payload_json"], dict)
                    else json.loads(invoice["payload_json"])
                ).get("revision_code"),
                "credit_note": {
                    **credit_notes[str(invoice["id"])],
                    "invoice_code": invoice["invoice_code"],
                    "project_id": str(project_id),
                    "dte": credit_dtes.get(credit_notes[str(invoice["id"])]["id"]),
                }
                if str(invoice["id"]) in credit_notes
                else None,
                "dte": dtes.get(str(invoice["id"])),
                "created_at": invoice["created_at"].isoformat()
                if hasattr(invoice["created_at"], "isoformat")
                else invoice["created_at"],
            }
            for invoice in rows(
                "SELECT id,invoice_code,payload_json::text AS payload_json,created_at "
                "FROM public.project_invoices "
                "WHERE org_id=%s AND project_id=%s ORDER BY created_at,id",
                [str(org_id), str(project_id)],
            )
        ]
    collected = sum(
        (Decimal(str(p["amount"])) for p in payments if p["voided_at"] is None),
        Decimal("0"),
    )
    deal = _deal(org_id, project_id, project)
    total = deal["total"] if deal else None
    balance = (total - collected) if total is not None else None
    if deal is None:
        status = "NO_DEAL"
    elif collected <= 0:
        status = "PENDING"
    elif balance > 0:
        status = "PARTIAL"
    else:
        status = "PAID"
    return {
        "payments": [
            _payment_public(p, receipts.get(str(p["id"]))) for p in payments
        ],
        "invoices": invoices,
        "collected": str(collected),
        "quote_total_gross": str(total) if total is not None else None,
        "balance": str(balance) if balance is not None else None,
        "currency": deal["currency"] if deal else "CLP",
        "status": status,
        "sealed_revision": deal["sealed_revision"] if deal else None,
    }


def list_payments(*, org_id: UUID, project_id: UUID) -> dict:
    project = project_row(org_id, project_id)
    return _summary(org_id, project_id, project)


def resolve_or_insert_payment(
    *,
    org_id: UUID,
    project_id: UUID,
    project: dict,
    actor_id: UUID,
    data: dict,
) -> tuple[dict, dict | None]:
    """The shared cobranza ledger primitive: replay the
    ``(org_id, operation_key)`` row with a cross-project guard, else validate
    the deal, currency and recorded_at and insert. Cross-domain flows that
    must settle a payment inside their own transaction (e.g. the POD cobro)
    call this instead of re-implementing the rules.

    Returns ``(payment_row, deal)``; ``deal`` is ``None`` on replay since the
    recorded row is returned even when the deal later reset.
    """
    existing = rows(
        "SELECT * FROM public.project_payments WHERE org_id=%s AND operation_key=%s",
        [str(org_id), data["operation_key"]],
    )
    if existing:
        payment = existing[0]
        if str(payment["project_id"]) != str(project_id):
            raise contract_error(
                409,
                "payment_operation_conflict",
                "La operación ya fue registrada en otro proyecto.",
            )
        return payment, None
    deal = _deal(org_id, project_id, project)
    if deal is None:
        raise contract_error(
            422,
            "payment_requires_deal",
            "Registra cobros solo sobre un proyecto cotizado.",
        )
    if deal["currency"] == "CLP" and data["amount"] != data[
        "amount"
    ].to_integral_value():
        raise contract_error(
            422,
            "payment_fractional_currency",
            "Los montos en CLP no llevan decimales.",
        )
    recorded_at = data.get("recorded_at")
    if recorded_at is not None and recorded_at > timezone.now():
        raise contract_error(
            422,
            "payment_recorded_in_future",
            "La fecha del cobro no puede ser futura.",
        )
    payment = rows(
        "INSERT INTO public.project_payments"
        "(org_id,project_id,operation_key,kind,amount,method,reference,note,"
        " recorded_by,recorded_at) "
        "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
        "ON CONFLICT (org_id, operation_key) DO NOTHING RETURNING *",
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
    )
    if not payment:
        # Lost race — the unique key converges on one row.
        payment = rows(
            "SELECT * FROM public.project_payments WHERE org_id=%s AND operation_key=%s",
            [str(org_id), data["operation_key"]],
        )
    payment = payment[0]
    if str(payment["project_id"]) != str(project_id):
        raise contract_error(
            409,
            "payment_operation_conflict",
            "La operación ya fue registrada en otro proyecto.",
        )
    return payment, deal


def record_payment(*, org_id: UUID, project_id: UUID, actor_id: UUID, data: dict) -> dict:
    with transaction.atomic():
        # Same lock order as pricing reset: the project row is the concurrency
        # point so a retired deal can never slip between the check and the insert.
        project = project_row(org_id, project_id, lock=True)
        with documentary_backend():
            payment, deal = resolve_or_insert_payment(
                org_id=org_id,
                project_id=project_id,
                project=project,
                actor_id=actor_id,
                data=data,
            )
            if deal is None:
                # Replay returns the recorded row even if the deal later reset.
                receipt = rows(
                    "SELECT * FROM public.payment_receipts WHERE payment_id=%s AND org_id=%s",
                    [str(payment["id"]), str(org_id)],
                )
                receipt_row = receipt[0] if receipt else None
                return {
                    "payment": _payment_public(payment, receipt_row),
                    "receipt": _receipt_public(receipt_row) if receipt_row else None,
                    **_summary(org_id, project_id, project),
                }
            receipt = issue_receipt(
                org_id=org_id,
                project=project,
                payment=payment,
                actor_id=actor_id,
                deal=deal,
            )
    return {
        "payment": _payment_public(payment, receipt),
        "receipt": receipt,
        **_summary(org_id, project_id, project),
    }


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
