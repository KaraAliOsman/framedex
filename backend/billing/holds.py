"""Durable credit holds for AI admission (dirección final 06 · 5).

Spendable credits = organization balance − ACTIVE and UNCERTAIN holds. One
hold per (organization, operation_key): the fixed cost of the legacy policy
(`legacy_route_v1`: route.credits_cost per exchange) is retained before the
provider is called, then settled together with the debit, released when no
commercial debit applies (provider failure, replay won by a concurrent call,
domain rollback) or left UNCERTAIN when the outcome is unknown (timeout),
which blocks an automatic repeat of a possibly paid call until conciliation.

Admission runs in its own short transaction (`independent`) under a
per-organization advisory lock, never waiting on the organization row an
agent's long domain transaction may already hold. Holds are committed even
if the domain work later rolls back; `sweep` resolves holds orphaned by a
crash or a rollback (settled if their debit exists, released otherwise).
A hold never grants credits nor extends the life of a monthly lot.
"""

from __future__ import annotations

import json
from datetime import timedelta
from uuid import UUID

from django.db import connection

from authentication.errors import contract_error
from pricing.repository import rows

CONSUMPTION_POLICY = "legacy_route_v1"
STALE_AFTER = timedelta(minutes=20)
UNCERTAIN_CODES = frozenset({"ai_provider_timeout"})


def _lock(org_id) -> None:
    rows("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0)) AS locked", [f"credit_holds:{org_id}"])


def sweep(org_id) -> int:
    """Resolve ACTIVE holds older than STALE_AFTER whose exchange is no longer
    running: SETTLED when the debit for that operation exists, RELEASED when
    nothing was debited (crash or domain rollback). Idempotent."""
    stale = rows(
        "SELECT h.id, h.operation_key FROM public.credit_holds h WHERE h.org_id=%s AND h.status='ACTIVE'"
        " AND h.created_at < now() - %s * interval '1 second'"
        " AND NOT EXISTS (SELECT 1 FROM public.ai_provider_usage u WHERE u.org_id=h.org_id"
        "   AND u.operation_key=h.operation_key AND u.status='RUNNING')"
        " FOR UPDATE OF h SKIP LOCKED",
        [str(org_id), int(STALE_AFTER.total_seconds())],
    )
    for hold in stale:
        debit = rows(
            "SELECT l.id FROM public.ai_audit_logs a JOIN public.credit_ledger l"
            " ON l.org_id=a.org_id AND l.operation_key='ai:' || a.id::text"
            " WHERE a.org_id=%s AND a.operation_key=%s LIMIT 1",
            [str(org_id), hold["operation_key"]],
        )
        if debit:
            rows("UPDATE public.credit_holds SET status='SETTLED', ledger_id=%s, reason='sweep_settled',"
                 " resolved_at=now() WHERE id=%s RETURNING id", [str(debit[0]["id"]), str(hold["id"])])
        else:
            rows("UPDATE public.credit_holds SET status='RELEASED', reason='sweep_no_commit',"
                 " resolved_at=now() WHERE id=%s RETURNING id", [str(hold["id"])])
    return len(stale)


def held(org_id, exclude_key: str | None = None) -> int:
    found = rows(
        "SELECT coalesce(sum(credits),0) AS held FROM public.credit_holds WHERE org_id=%s"
        " AND status IN ('ACTIVE','UNCERTAIN')" + (" AND operation_key<>%s" if exclude_key else ""),
        [str(org_id), *([exclude_key] if exclude_key else [])],
    )
    return int(found[0]["held"])


def admit(*, org_id, user_id, operation_key: str, credits: int, capability: str,
          ai_job_id=None) -> dict:
    """Retain the fixed cost of one exchange before the provider is called."""
    from ai_gateway.usage import independent
    from billing.wallet import financial_transaction

    if type(credits) is not int or credits <= 0:
        raise ValueError("A hold requires positive integral credits")
    if connection.vendor != "postgresql":
        # Same rule as usage.begin: holds exist only on the real database.
        return {}

    def run() -> dict:
        with financial_transaction(org_id):
            _lock(org_id)
            sweep(org_id)
            existing = rows(
                "SELECT * FROM public.credit_holds WHERE org_id=%s AND operation_key=%s FOR UPDATE",
                [str(org_id), operation_key],
            )
            if existing and existing[0]["status"] in ("ACTIVE", "SETTLED"):
                # A retry of the same exchange reuses its hold; a settled one
                # is replayed by the audit before any provider call.
                return dict(existing[0])
            if existing and existing[0]["status"] == "UNCERTAIN":
                raise contract_error(
                    409, "ai_operation_uncertain",
                    "Esta solicitud quedó con resultado incierto en el proveedor. Se concilia antes de repetirla; "
                    "las funciones manuales siguen disponibles.",
                )
            balance = int(rows("SELECT credits_balance FROM public.tenancy_organizations WHERE id=%s",
                               [str(org_id)])[0]["credits_balance"])
            reserved = held(org_id, exclude_key=operation_key)
            if balance - reserved < credits:
                raise contract_error(409, "insufficient_credits",
                                     "No quedan créditos gastables para esta operación de IA.")
            # Expected lot origin (earliest expiry first), net of other holds —
            # informational: the debit consumes the lots at settlement.
            allocation: list[dict] = []
            skip, need = reserved, credits
            for lot in rows(
                "SELECT id, origin, remaining, expires_at FROM public.credit_lots WHERE org_id=%s AND remaining>0"
                " AND (expires_at IS NULL OR expires_at>now()) ORDER BY expires_at NULLS LAST, created_at, id",
                [str(org_id)],
            ):
                available = int(lot["remaining"])
                used_by_others = min(skip, available)
                skip -= used_by_others
                take = min(need, available - used_by_others)
                if take > 0:
                    allocation.append({"lot_id": str(lot["id"]), "origin": lot["origin"], "credits": take})
                    need -= take
                if need == 0:
                    break
            if existing:
                record = rows(
                    "UPDATE public.credit_holds SET status='ACTIVE', credits=%s, allocation=%s::jsonb, reason=NULL,"
                    " resolved_at=NULL, user_id=%s, ai_job_id=%s, created_at=now() WHERE id=%s RETURNING *",
                    [credits, json.dumps(allocation), str(user_id), str(ai_job_id) if ai_job_id else None,
                     str(existing[0]["id"])],
                )[0]
            else:
                record = rows(
                    "INSERT INTO public.credit_holds (org_id, user_id, operation_key, ai_job_id, capability,"
                    " consumption_policy, credits, status, allocation) VALUES (%s,%s,%s,%s,%s,%s,%s,'ACTIVE',%s::jsonb)"
                    " RETURNING *",
                    [str(org_id), str(user_id), operation_key, str(ai_job_id) if ai_job_id else None, capability,
                     CONSUMPTION_POLICY, credits, json.dumps(allocation)],
                )[0]
            return dict(record)

    return independent(run)


def settle(*, org_id, operation_key: str, ledger_id) -> None:
    """Inside the debit's transaction: the hold settles exactly with it."""
    if connection.vendor != "postgresql":
        # Same rule as usage.begin: holds exist only on the real database.
        return None
    rows(
        "UPDATE public.credit_holds SET status='SETTLED', ledger_id=%s, resolved_at=now(), reason=NULL"
        " WHERE org_id=%s AND operation_key=%s AND status='ACTIVE' RETURNING id",
        [str(ledger_id), str(org_id), operation_key],
    )


def finish_without_debit(*, org_id, operation_key: str, reason: str) -> None:
    """Provider failure, lost replay race or an output refused after the call:
    no commercial debit under legacy_route_v1. A timeout stays UNCERTAIN.
    Committed on its own so the outer rollback cannot resurrect the hold."""
    from ai_gateway.usage import independent
    from billing.wallet import financial_transaction

    if connection.vendor != "postgresql":
        # Same rule as usage.begin: holds exist only on the real database.
        return None
    status = "UNCERTAIN" if reason in UNCERTAIN_CODES else "RELEASED"

    def run() -> None:
        with financial_transaction(org_id):
            rows(
                "UPDATE public.credit_holds SET status=%s, reason=%s, resolved_at=CASE WHEN %s='RELEASED' THEN now() END"
                " WHERE org_id=%s AND operation_key=%s AND status='ACTIVE' RETURNING id",
                [status, reason[:120], status, str(org_id), operation_key],
            )

    independent(run)


def release_job(*, org_id, ai_job_id) -> None:
    """A rolled-back agent round: its debits were undone with the domain
    work, so every still-ACTIVE hold of that job is released."""
    if connection.vendor != "postgresql":
        # Same rule as usage.begin: holds exist only on the real database.
        return None
    from ai_gateway.usage import independent
    from billing.wallet import financial_transaction

    def run() -> None:
        with financial_transaction(org_id):
            rows(
                "UPDATE public.credit_holds SET status='RELEASED', reason='domain_rollback', resolved_at=now()"
                " WHERE org_id=%s AND ai_job_id=%s AND status='ACTIVE' RETURNING id",
                [str(org_id), str(UUID(str(ai_job_id)))],
            )

    independent(run)


def conciliate(*, org_id, operation_key: str, outcome: str, actor_id) -> dict | None:
    """Operator/OWNER conciliation of an UNCERTAIN hold with provider evidence:
    `settled` (the exchange was paid and debited elsewhere) or `released`."""
    from billing.wallet import financial_transaction

    if outcome not in ("settled", "released"):
        raise ValueError("outcome must be settled or released")
    with financial_transaction(org_id):
        found = rows(
            "UPDATE public.credit_holds SET status=%s, reason=%s, resolved_at=now()"
            " WHERE org_id=%s AND operation_key=%s AND status='UNCERTAIN' RETURNING *",
            ["SETTLED" if outcome == "settled" else "RELEASED", f"conciliated_by:{actor_id}"[:120],
             str(org_id), operation_key],
        )
    return dict(found[0]) if found else None


__all__ = ["CONSUMPTION_POLICY", "admit", "conciliate", "finish_without_debit", "held", "release_job",
           "settle", "sweep"]
