"""P16 · What the organization's plan includes: seats, roles and features.

The database holds the terms (``private.plan_terms``) and enforces seats and
roles where access is granted; this module only reads them for the edge and
the interface. AI entitlement stays in ``billing.capabilities``.
"""

from __future__ import annotations

import json

from authentication.errors import contract_error
from pricing.repository import rows

FEATURES = ("client_3d", "purchasing", "cnc", "roles", "subagents", "stations", "field")

FEATURE_REASONS = {
    "purchasing": "Los pedidos de compra a proveedores están en el plan Pro. Las necesidades de "
    "material siguen a la vista.",
    "subagents": "El trabajo en paralelo del asistente está en el plan Empresa.",
}


def organization_plan(org_id) -> dict:
    """Terms and seats in use, under the caller's verified membership."""
    from billing.capabilities import entitled
    from billing.wallet import financial_transaction

    plan = rows("SELECT private.organization_plan(%s) AS plan", [str(org_id)])[0]["plan"]
    plan = json.loads(plan) if isinstance(plan, str) else plan
    with financial_transaction(org_id):
        organization = rows(
            "SELECT subscription_tier, subscription_active, trial_ends_at FROM public.tenancy_organizations WHERE id=%s",
            [str(org_id)],
        )
    seats = plan.get("seats")
    active = int(plan["active_members"])
    pending = int(plan["pending_invitations"])
    return {
        "code": plan["code"],
        "seats": seats,
        "active_members": active,
        "pending_invitations": pending,
        "seats_left": None if seats is None else max(0, int(seats) - active - pending),
        "roles": list(plan["roles"]),
        "features": [item for item in FEATURES if item in plan["features"]],
        "ai": bool(organization and entitled(organization[0])),
        # One person who does everything: no roles, no team screens.
        "solo": active <= 1 and pending == 0,
    }


def allows(org_id, feature: str) -> bool:
    return bool(rows("SELECT private.plan_allows(%s,%s) AS allowed", [str(org_id), feature])[0]["allowed"])


def require(org_id, feature: str) -> None:
    if not allows(org_id, feature):
        raise contract_error(403, "plan_feature_required", FEATURE_REASONS.get(feature, "Tu plan no incluye esta función."))
