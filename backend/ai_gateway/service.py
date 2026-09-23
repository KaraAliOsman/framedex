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
MAX_OUTPUT_CHARS = 256_000


def _route(capability: str) -> dict | None:
    found = rows(
        "SELECT * FROM public.ai_routes WHERE capability=%s AND enabled",
        [capability],
    )
    return found[0] if found else None


def _input_hash(input_payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(input_payload, sort_keys=True, default=str).encode()
    ).hexdigest()


def _response(*, audit: dict, capability: str, route: dict, result: dict) -> dict:
    """The white-label invoke envelope — replayed verbatim on idempotent retries."""
    return {
        "audit_id": str(audit["id"]),
        "capability": capability,
        "model": route["public_name"],
        "output": result["output"],
        "tokens_prompt": int(result["tokens_prompt"]),
        "tokens_completion": int(result["tokens_completion"]),
        "latency_ms": int(result["latency_ms"]),
        "credits_debited": int(route["credits_cost"]),
    }


def _replay(
    *,
    org_id: UUID,
    operation_key: str,
    capability: str,
    tool_name: str | None,
    input_hash: str,
) -> dict | None:
    """The stored response of a completed operation, or None when no audit won
    this key. The org row lock (reconcile FOR UPDATE) makes the winner's commit
    visible here before any provider work is spent."""
    found = rows(
        "SELECT id, tool_name, state_hash_before, output_payload "
        "FROM public.ai_audit_logs WHERE org_id=%s AND operation_key=%s",
        [str(org_id), operation_key],
    )
    if not found:
        return None
    audit = found[0]
    envelope = audit["output_payload"] or {}
    if (
        envelope.get("capability") != capability
        or audit["state_hash_before"] != input_hash
        or (audit["tool_name"] or capability) != (tool_name or capability)
    ):
        raise contract_error(
            409,
            "ai_operation_conflict",
            "La clave de operación ya fue usada con una solicitud distinta.",
        )
    return {"audit_id": str(audit["id"]), **envelope}


def _audit(
    *,
    org_id: UUID,
    user_id: UUID,
    route: dict,
    tool_name: str,
    operation_key: str,
    input_payload: dict,
    result: dict,
    response: dict,
) -> dict | None:
    inserted = rows(
        "INSERT INTO public.ai_audit_logs("
        "org_id, user_id, tool_name, model_used, prompt_version, retention_until,"
        " input_payload, output_payload, points_debited,"
        " tokens_prompt, tokens_completion, latency_ms, state_hash_before,"
        " operation_key, route_id)"
        " VALUES(%s,%s,%s,%s,%s, now() + %s * interval '1 day',%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        " ON CONFLICT (org_id, operation_key) WHERE operation_key IS NOT NULL DO NOTHING"
        " RETURNING *",
        [
            str(org_id),
            str(user_id),
            tool_name,
            # Audit rows are tenant-readable — model_used stores the white-label
            # name. Provider provenance lives behind route_id, an opaque FK only
            # the backend role can join to the sealed provider/model internals.
            str(route["public_name"]),
            str(route["prompt_version"]),
            RETENTION_DAYS,
            json.dumps(input_payload, default=str),
            json.dumps(response, default=str),
            int(route["credits_cost"]),
            int(result["tokens_prompt"]),
            int(result["tokens_completion"]),
            int(result["latency_ms"]),
            _input_hash(input_payload),
            operation_key,
            str(route["id"]),
        ],
    )
    if inserted:
        # Seal the exact provider/model/prompt at invocation time — route_id
        # alone would re-attribute history after a route edit. Provenance is
        # backend-only (billing_backend), the same role writing here.
        rows(
            "INSERT INTO public.ai_audit_provenance("
            "audit_id, provider, provider_model, prompt_version)"
            " VALUES(%s,%s,%s,%s) RETURNING audit_id",
            [
                str(inserted[0]["id"]),
                str(route["provider"]),
                # The model the request actually ran on (provider-reported or
                # its configured override) — never the route's label when the
                # transport selected another model behind it.
                str(result.get("model") or route["provider_model"]),
                str(route["prompt_version"]),
            ],
        )
    return inserted[0] if inserted else None


def invoke(
    *,
    org_id: UUID,
    user_id: UUID,
    capability: str,
    operation_key: str,
    input_payload: dict,
    tool_name: str | None = None,
    provider_options: dict | None = None,
) -> dict[str, Any]:
    # provider_options is server-side transport config (system prompt, output
    # mode). It is deliberately NOT part of input_payload: that hash covers the
    # client's request semantics so a prompt-version change can never break
    # replay, and the generic invoke endpoint can never smuggle in control keys.
    input_hash = _input_hash(input_payload)
    with wallet.financial_transaction(org_id):
        organization = wallet.reconcile(org_id)
        # Idempotency: a retry of a completed operation replays its stored
        # response — no second provider call, no second debit.
        replay = _replay(
            org_id=org_id,
            operation_key=operation_key,
            capability=capability,
            tool_name=tool_name,
            input_hash=input_hash,
        )
        if replay is not None:
            return replay
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
            provider_options=provider_options,
            # The wire key is org-namespaced: a real provider dedupes on the
            # header globally, so the raw org-scoped key alone would collide
            # across tenants sharing a capability-level key prefix.
            operation_key=f"{org_id}:{operation_key}",
        )
        if len(str(result["output"])) > MAX_OUTPUT_CHARS:
            raise ProviderError("ai_provider_output_too_large")
        audit = _audit(
            org_id=org_id,
            user_id=user_id,
            route=route,
            tool_name=tool_name or capability,
            operation_key=operation_key,
            input_payload=input_payload,
            result=result,
            response={
                "capability": capability,
                "model": route["public_name"],
                "output": result["output"],
                "tokens_prompt": int(result["tokens_prompt"]),
                "tokens_completion": int(result["tokens_completion"]),
                "latency_ms": int(result["latency_ms"]),
                "credits_debited": credits,
            },
        )
        if audit is None:
            # Defense in depth: the org lock already serializes invokes, so this
            # only fires if the row appeared without holding the lock.
            return _replay(
                org_id=org_id,
                operation_key=operation_key,
                capability=capability,
                tool_name=tool_name,
                input_hash=input_hash,
            )
        wallet.debit(org_id, credits, audit["id"])
        return _response(audit=audit, capability=capability, route=route, result=result)


__all__ = ["ProviderError", "invoke"]
