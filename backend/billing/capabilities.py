"""Single server authority for AI capabilities, limits and availability (v1 final 06).

The client only mirrors this resolution; every endpoint and the worker gate
again. Reading it never calls the provider, grants credits, reconciles
periods or creates a subscription: it is a pure read of persisted contracts.

Separate facts, never collapsed into one boolean:
- entitlement: the organization's plan grants the common AI core (or not);
- supported: the capability is technically implemented server-side;
- permitted: the actor's role may use it;
- availability + reason_code: provider, spendable balance, owner budget, ...
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from pricing.repository import rows

TERMS_VERSION = "plans-2026-09-prd03"          # frozen PRD-03 catalogue in the engine
QUOTA_POLICY_VERSION = "allowances-legacy-v1"   # 0/2000/6000/12000 per service window
CONSUMPTION_POLICY = "legacy_route_v1"          # fixed debit = route.credits_cost per exchange

MODEL_SELECTION = "MiMo 2.6 Pro"                # owner selection for every AI plan, no fallback

AI_ROLES = ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")
WRITE_ROLES = ("OWNER", "ESTIMATOR")

# Common core: identical for every AI plan. `route` is the gateway route that
# executes it; `roles` the domain permission to start it.
CORE = (
    {"id": "copilot.chat", "label": "Chat con fuentes", "route": "agent", "roles": AI_ROLES},
    {"id": "copilot.task", "label": "Trabajo delegado", "route": "agent", "roles": AI_ROLES},
    {"id": "ai.document_extract", "label": "Documento a posiciones y borrador", "route": "agent", "roles": WRITE_ROLES},
    {"id": "ai.catalog_draft", "label": "Candidatos de catálogo con evidencia", "route": "catalog_import", "roles": ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")},
    {"id": "ai.batch_transform", "label": "Cambios sobre ventanas", "route": "agent", "roles": WRITE_ROLES},
    {"id": "ai.plan_compare", "label": "Comparar revisiones y propagar diferencias", "route": "agent", "roles": WRITE_ROLES},
)
# Extras exist only with a real contract and support; none is declared yet.
EXTRAS: tuple[dict, ...] = ()

REASONS = {
    "ok": "Disponible.",
    "no_ai_entitlement": "El plan Manual completo no incluye IA. Todas las funciones manuales siguen disponibles.",
    "plan_inactive": "La suscripción no está activa. Las funciones manuales siguen disponibles.",
    "not_supported": "Esta capacidad todavía no está implementada.",
    "role_not_permitted": "Tu rol no puede iniciar esta tarea. El dueño o un estimador puede hacerlo.",
    "provider_missing": "El proveedor de IA no está configurado en el servidor. El dueño puede revisarlo en Empresa › Inteligencia artificial.",
    "insufficient_credits": "No quedan créditos gastables. Las funciones manuales siguen disponibles.",
    "budget_exhausted": "Se alcanzó el presupuesto mensual de IA que fijó el dueño.",
}


def entitled(organization: dict, now: datetime | None = None) -> bool:
    """The common AI core: any plan but the manual one, while active or in a
    live trial. One rule for the resolver, the gateway and the wallet."""
    now = now or datetime.now(timezone.utc)
    tier = organization["subscription_tier"]
    trial_ends = organization.get("trial_ends_at")
    trial_live = tier == "TRIAL" and trial_ends is not None and trial_ends > now
    return tier != "STARTER" and bool(organization["subscription_active"] or trial_live)


def _provider_configured(route: dict | None) -> bool:
    if route is None:
        return False
    provider = route["provider"]
    if provider == "MOCK":
        from ai_gateway.providers import _mock_enabled
        return _mock_enabled()
    return bool(os.environ.get(f"AI_GATEWAY_{provider}_API_KEY") and os.environ.get(f"AI_GATEWAY_{provider}_BASE_URL"))


def _service_window(org_id, now) -> dict | None:
    """Current allowance window from persisted billing periods (anniversaries)."""
    from billing.lifecycle import service_windows

    periods = rows(
        "SELECT * FROM public.billing_periods WHERE org_id=%s AND period_start<=%s AND period_end>%s "
        "ORDER BY period_start DESC LIMIT 1", [str(org_id), now, now])
    if not periods:
        return None
    windows = list(service_windows(periods[0]))
    for index, (left, right) in enumerate(windows):
        if left <= now < right:
            following = windows[index + 1][0] if index + 1 < len(windows) else None
            return {"start": left.isoformat(), "end": right.isoformat(),
                    "next_grant_at": following.isoformat() if following else None,
                    "cycle": periods[0]["billing_cycle"]}
    return None


def resolve(*, org_id, user_id, role: str) -> dict:
    """Pure read under the caller's verified membership (org/role from the token)."""
    from ai_gateway import usage
    from ai_gateway.service import _route
    from billing.wallet import financial_transaction

    now = datetime.now(timezone.utc)
    with financial_transaction(org_id):
        organization = rows(
            "SELECT subscription_tier, subscription_active, billing_cycle, trial_ends_at, credits_balance "
            "FROM public.tenancy_organizations WHERE id=%s", [str(org_id)])[0]
        lots = rows(
            "SELECT origin, remaining, expires_at FROM public.credit_lots WHERE org_id=%s AND remaining>0 "
            "AND (expires_at IS NULL OR expires_at>%s) ORDER BY expires_at NULLS LAST, created_at", [str(org_id), now])
        held = rows(
            "SELECT coalesce(sum(credits),0) AS held FROM public.credit_holds WHERE org_id=%s"
            " AND status IN ('ACTIVE','UNCERTAIN')", [str(org_id)])[0]["held"]
        settings = rows("SELECT monthly_budget_credits FROM public.ai_settings WHERE org_id=%s", [str(org_id)])
        window = _service_window(org_id, now)
        # Routes are read under billing_backend: member-facing `authenticated`
        # holds no grant over ai_routes / ai_capability_routes.
        routes: dict[str, dict | None] = {}
        for item in CORE:
            if item["route"] not in routes:
                routes[item["route"]] = _route(item["route"], org_id)
    tier = organization["subscription_tier"]
    trial_live = tier == "TRIAL" and organization["trial_ends_at"] is not None and organization["trial_ends_at"] > now
    is_entitled = entitled(organization, now)
    usable = sum(int(lot["remaining"]) for lot in lots)
    spendable = max(0, usable - int(held))

    budget_limit = settings[0]["monthly_budget_credits"] if settings else None
    budget_used = None
    if budget_limit is not None:
        budget_used = int(usage.summary(org_id)["capacity_credits"])

    capabilities = []
    for item in CORE:
        route = routes[item["route"]]
        supported = route is not None
        permitted = role in item["roles"]
        cost = int(route["credits_cost"]) if route else None
        if tier == "STARTER":
            reason = "no_ai_entitlement"
        elif not is_entitled:
            reason = "plan_inactive"
        elif not supported:
            reason = "not_supported"
        elif not permitted:
            reason = "role_not_permitted"
        elif not _provider_configured(route):
            reason = "provider_missing"
        elif cost is not None and spendable < cost:
            reason = "insufficient_credits"
        elif budget_limit is not None and budget_used is not None and cost is not None and budget_used + cost > budget_limit:
            reason = "budget_exhausted"
        else:
            reason = "ok"
        capabilities.append({
            "id": item["id"], "label": item["label"], "supported": supported, "permitted": permitted,
            "available": reason == "ok", "reason_code": reason, "reason": REASONS[reason],
            "credits_per_exchange": cost,
        })

    financial = role == "OWNER"
    from billing import quota_policy

    quota = quota_policy.resolve(tier)
    overall = "ok" if any(c["available"] for c in capabilities) else (
        capabilities[0]["reason_code"] if capabilities else "not_supported")
    return {
        "terms_version": TERMS_VERSION,
        "quota_policy_version": QUOTA_POLICY_VERSION,
        "consumption_policy_version": CONSUMPTION_POLICY,
        "plan": {"code": tier, "cycle": organization["billing_cycle"], "active": bool(organization["subscription_active"]),
                 "trial_ends_at": organization["trial_ends_at"].isoformat() if organization["trial_ends_at"] else None},
        "ai_entitlement": {"granted": is_entitled, "origin": "trial" if trial_live else ("plan" if is_entitled else "none")},
        "model_selection": MODEL_SELECTION if is_entitled else None,
        "capabilities": capabilities,
        "extras": list(EXTRAS),
        # The same core and model on every AI plan; plans differ by included
        # usage only (frozen legacy values, not proportional to price).
        "plans": [
            {"code": code, "ai": code != "STARTER", "included_credits": plan_quota.included_credits,
             "window_kind": plan_quota.window}
            for code, plan_quota in ((code, quota_policy.legacy(code))
                                     for code in ("STARTER", "TRIAL", "PRO", "BUSINESS", "BUSINESS_2X"))
        ],
        "limits": {
            "included_credits": quota.included_credits,
            "unit": quota.unit,
            "window_kind": quota.window,
            "policy_version": quota.policy_version,
            "unit_credits": quota.unit_credits,
            "multiplier": quota.multiplier,
            "source": quota.source,
            "window": window,
        },
        "balances": {
            "by_origin": [{"origin": lot["origin"], "remaining": int(lot["remaining"]),
                           "expires_at": lot["expires_at"].isoformat() if lot["expires_at"] else None} for lot in lots]
            if financial else [],
            "usable": usable if financial else None,
            "reserved": int(held) if financial else None,
            "spendable": spendable if financial else None,
        },
        "budget": {
            "monthly_limit": budget_limit if financial else None,
            "used": budget_used if financial else None,
            "window_start": usage.month_start(now).isoformat(),
            "timezone": "America/Santiago",
        },
        "ai_available": overall == "ok",
        "reason_code": overall,
        "reason": REASONS[overall],
        "role": role,
    }
