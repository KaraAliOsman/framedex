"""Versioned included-credit policies (dirección final 06 · 4).

`allowances-legacy-v1` is the only active policy: the frozen PRD-03 values
(STARTER 0, PRO 2000, BUSINESS 6000, BUSINESS_2X 12000 per service window;
trial 500 in total). They are not proportional to their prices and are not
announced as such.

`proportional-v1` is prepared, not active: Q = m × U with an integer unit U
and integer multipliers m read from persisted, audited commercial terms.
There are no approved values yet — nothing here maps PRO/BUSINESS to 1/2/3
units, changes PLAN_ALLOWANCES, offers or subscribers, or derives a quota by
dividing an amount paid. Activation needs approved economics, versioned
terms, grandfathering and a human launch.
"""

from __future__ import annotations

from dataclasses import dataclass

from dekopen_engine.billing import PLAN_ALLOWANCES

ACTIVE_POLICY = "allowances-legacy-v1"
TRIAL_TOTAL_CREDITS = 500


@dataclass(frozen=True)
class Quota:
    policy_version: str
    included_credits: int
    unit: str
    window: str
    unit_credits: int | None = None
    multiplier: int | None = None
    source: str = ""


def legacy(tier: str) -> Quota:
    if tier == "TRIAL":
        return Quota(ACTIVE_POLICY, TRIAL_TOTAL_CREDITS, "credit", "trial_total",
                     source="PRD-03 · trial 7 días / 500 créditos totales")
    return Quota(ACTIVE_POLICY, int(PLAN_ALLOWANCES.get(tier, 0)), "credit", "service_window",
                 source="engine/billing.py PLAN_ALLOWANCES (PRD-03 congelado)")


def proportional(unit_credits: int, multiplier: int, *, terms_version: str) -> Quota:
    """Q = m × U from approved terms. Integers only; never inferred from price."""
    if type(unit_credits) is not int or type(multiplier) is not int or unit_credits <= 0 or multiplier < 0:
        raise ValueError("proportional quota requires positive integer unit and non-negative integer multiplier")
    return Quota("proportional-v1", unit_credits * multiplier, "credit", "service_window",
                 unit_credits=unit_credits, multiplier=multiplier, source=f"terms:{terms_version}")


def resolve(tier: str) -> Quota:
    """The effective policy today. A proportional policy becomes effective
    only when persisted commercial terms for it exist (none are approved)."""
    return legacy(tier)


__all__ = ["ACTIVE_POLICY", "Quota", "legacy", "proportional", "resolve"]
