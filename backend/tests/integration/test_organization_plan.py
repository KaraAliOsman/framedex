"""P16 · The plan says how many people, which roles and which features."""

import pytest
from django.db import connection
from rest_framework.exceptions import APIException

from backend.tests.integration.test_shot09_documentary import (
    as_user,
    documentary_tenant as documentary_tenant,
)
from billing import plans

pytestmark = pytest.mark.rls_integration


def _tier(org, tier):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE public.tenancy_organizations SET subscription_tier=%s WHERE id=%s", [tier, org])


def test_a_taller_is_one_person_who_does_everything(documentary_tenant):
    org, other, users, outsider = documentary_tenant
    with as_user(outsider):
        trial = plans.organization_plan(other)
    assert trial["code"] == "TRIAL"
    assert (trial["seats"], trial["seats_left"], trial["solo"]) == (3, 2, True)
    assert trial["roles"] == ["OWNER", "ESTIMATOR", "WORKSHOP_MANAGER"]
    assert "client_3d" in trial["features"] and "subagents" not in trial["features"]

    _tier(other, "STARTER")
    with as_user(outsider):
        taller = plans.organization_plan(other)
    assert taller == {
        "code": "STARTER", "seats": 1, "active_members": 1, "pending_invitations": 0,
        "seats_left": 0, "roles": ["OWNER"], "features": [], "ai": False, "solo": True,
    }

    # Four people kept from a larger plan stay; the plan just has no seat left.
    with as_user(users["OWNER"]):
        team = plans.organization_plan(org)
    assert (team["active_members"], team["seats_left"], team["solo"]) == (4, 0, False)


def test_supplier_orders_start_at_pro(documentary_tenant):
    org, _, users, _ = documentary_tenant
    _tier(org, "STARTER")
    with as_user(users["OWNER"]), pytest.raises(APIException) as refused:
        plans.require(org, "purchasing")
    assert refused.value.status_code == 403
    _tier(org, "PRO")
    with as_user(users["OWNER"]):
        plans.require(org, "purchasing")
        assert not plans.allows(org, "subagents")
    _tier(org, "BUSINESS")
    with as_user(users["WORKSHOP_MANAGER"]):
        assert plans.allows(org, "subagents")
