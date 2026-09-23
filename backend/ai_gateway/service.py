"""AI gateway invoke: one transaction binding entitlement, provider call,
immutable audit and wallet debit (PRD-13 pre/post-invocation hooks).

The org row lock (reconcile → FOR UPDATE) serializes AI spend per tenant; the
balance check runs BEFORE any provider HTTP so a broke wallet cancels the call
before the request exists. Tenants only ever see public_name — provider and
model stay sealed in the audit row."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import UUID

from authentication.errors import contract_error
from ai_gateway.providers import ProviderError, provider_for
from billing import wallet
from documents.repository import rows

RETENTION_DAYS = 90


def _route(capability: str) -> dict | None:
    found = rows(
        "SELECT * FROM public.ai_routes WHERE capability=%s AND enabled",
        [capability],
    )
    return found[0] if found else None


def _audit(
    *,
    org_id: UUID,
    user_id: UUID,
    route: dict,
    tool_name: str,
    input_payload: dict,
    result: dict,
) -> dict:
    state_hash = hashlib.sha256(
        json.dumps(input_payload, sort_keys=True, default=str).encode()
    ).hexdigest()
    return rows(
        "INSERT INTO public.ai_audit_logs("
        "org_id, user_id, tool_name, model_used, prompt_version, retention_until,"
        " input_payload, output_payload, points_debited,"
        " tokens_prompt, tokens_completion, latency_ms, state_hash_before)"
        " VALUES(%s,%s,%s,%s,%s, now() + interval '%s days',%s,%s,%s,%s,%s,%s,%s)"
        " RETURNING *",
        [
            str(org_id),
            str(user_id),
            tool_name,
            str(route["provider_model"]),
            str(route["prompt_version"]),
            RETENTION_DAYS,
            json.dumps(input_payload, default=str),
            json.dumps({"output": result["output"]}, default=str),
            int(route["credits_cost"]),
            int(result["tokens_prompt"]),
            int(result["tokens_completion"]),
            int(result["latency_ms"]),
            state_hash,
        ],
    )[0]


def invoke(
    *,
    org_id: UUID,
    user_id: UUID,
    capability: str,
    input_payload: dict,
    tool_name: str | None = None,
) -> dict[str, Any]:
    with wallet.financial_transaction(org_id):
        organization = wallet.reconcile(org_id)
        if (
            organization["subscription_tier"] == "STARTER"
            or not organization["subscription_active"]
        ):
            raise contract_error(
                409,
                "ai_entitlement_required",
                "Tu plan conserva todas las funciones manuales.",
            )
        route = _route(capability)
        if route is None:
            raise contract_error(
                404,
                "ai_capability_unknown",
                "La capacidad de IA solicitada no está disponible.",
            )
        credits = int(route["credits_cost"])
        # Pre-invocation hook: balance is checked while the org row is locked,
        # before any provider request exists — never debit after the fact.
        if int(organization["credits_balance"]) < credits:
            raise contract_error(
                409,
                "insufficient_credits",
                "No quedan créditos suficientes para esta operación de IA.",
            )
        result = provider_for(route).invoke(
            route=route,
            capability=capability,
            input_payload=input_payload,
        )
        audit = _audit(
            org_id=org_id,
            user_id=user_id,
            route=route,
            tool_name=tool_name or capability,
            input_payload=input_payload,
            result=result,
        )
        wallet.debit(org_id, credits, audit["id"])
        return {
            "audit_id": str(audit["id"]),
            "capability": capability,
            "model": route["public_name"],
            "output": result["output"],
            "tokens_prompt": int(result["tokens_prompt"]),
            "tokens_completion": int(result["tokens_completion"]),
            "latency_ms": int(result["latency_ms"]),
            "credits_debited": credits,
        }


__all__ = ["ProviderError", "invoke"]
