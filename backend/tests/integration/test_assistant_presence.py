"""Real tenant/context isolation and outcome locking on PostgreSQL."""
from uuid import UUID, uuid4

from django.db import connection, transaction

import pytest

from ai_gateway import jobs
from authentication.errors import ContractAPIException
from authentication.types import VerifiedSupabaseToken
from backend.tests.integration.test_shot08_pricing import (
    commercial_rows as commercial_rows, as_user,
)
from pricing.repository import rows

pytestmark = pytest.mark.rls_integration


@pytest.fixture(autouse=True)
def real_ai_backend(monkeypatch):
    # The unit suite's default stub must not remove roles or row locks here.
    monkeypatch.setattr(jobs, "connection", connection)
    monkeypatch.setattr(jobs, "transaction", transaction)


def test_exact_context_outlives_recent_page_and_is_private(commercial_rows):
    org, other, users = commercial_rows
    actor = users["ESTIMATOR"]
    refs = {"project_id": str(uuid4())}
    with as_user(actor):
        original = jobs.create_job(org_id=org, user_id=actor, surface="project", refs=refs, goal="Contexto exacto")
        with jobs._ai_backend():
            rows("UPDATE public.ai_jobs SET created_at=NOW()-interval '1 day' WHERE id=%s RETURNING id", [original["id"]])
        for _ in range(32):
            jobs.create_job(org_id=org, user_id=actor, surface="dashboard", refs={}, goal="Otro contexto")
        assert original["id"] not in {job["id"] for job in jobs.list_jobs(org_id=org, user_id=actor)}
        assert [job["id"] for job in jobs.list_jobs(org_id=org, user_id=actor, surface="project", refs=refs, limit=1)] == [original["id"]]
        assert jobs.list_jobs(org_id=other, user_id=actor, surface="project", refs=refs, limit=1) == []
        assert jobs.list_jobs(org_id=org, user_id=users["WORKSHOP_MANAGER"], surface="project", refs=refs, limit=1) == []
        assert jobs.list_jobs(org_id=org, user_id=actor, surface="project", refs={**refs,"position_id":str(uuid4())}, limit=1) == []


def test_failed_apply_remains_pending_and_undo_requires_applied(commercial_rows):
    org, _, users = commercial_rows
    actor = users["ESTIMATOR"]
    with as_user(actor):
        job = jobs.create_job(org_id=org, user_id=actor, surface="dashboard", refs={}, goal="Propuesta")
        jobs.finish_job(job_id=UUID(job["id"]), state="WAITING_FOR_APPROVAL", transcript=[{"role":"user","text":"Propuesta"},{"role":"agent","steps":[{"kind":"ops"}]}], plan=[], artifacts=[], warnings=[], result=None)
        arguments = {"org_id":org,"user_id":actor,"job_id":UUID(job["id"])}
        entry = {"turn_index":1,"step_index":0}
        assert jobs.record_outcome(**arguments, entry={**entry,"action":"undone"}) is None
        assert jobs.record_outcome(**arguments, entry={**entry,"action":"apply_failed"})["recorded"]
        assert jobs.get_job(**arguments)["state"] == "WAITING_FOR_APPROVAL"
        assert jobs.record_outcome(**arguments, entry={**entry,"action":"applied"})["recorded"]
        assert jobs.get_job(**arguments)["state"] == "SUCCEEDED"
        assert jobs.record_outcome(**arguments, entry={**entry,"action":"undone"})["recorded"]
        assert not jobs.record_outcome(**arguments, entry={**entry,"action":"undone"})["recorded"]
        assert not jobs.record_outcome(**arguments, entry={**entry,"action":"declined"})["recorded"]
        assert [outcome["action"] for outcome in jobs.get_job(**arguments)["outcomes"]] == ["apply_failed","applied","undone"]


def test_presence_role_gate_is_backend_authority(commercial_rows, monkeypatch):
    org, _, users = commercial_rows
    user = users["INSTALLER"]
    token = VerifiedSupabaseToken(access_token="fixture", user_id=user, claims={"sub":str(user),"role":"authenticated","aal":"aal2"}, aal="aal2", email="installer@fixture.local")
    monkeypatch.setattr("documents.views.verified_request_token", lambda _: token)
    from ai_gateway.views import AiPresenceView
    from rest_framework.test import APIRequestFactory
    from rest_framework.request import Request
    request = Request(APIRequestFactory().get("/ai/presence/", {"surface":"dashboard"}, HTTP_X_ORGANIZATION_ID=str(org)))
    with pytest.raises(ContractAPIException) as denied:
        AiPresenceView().get(request)
    assert denied.value.status_code == 403
