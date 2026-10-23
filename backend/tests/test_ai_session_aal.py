"""An owner's agent run keeps the second factor of the session that delegated
it: sealed at enqueue from the verified token, never from the client."""

import json
from uuid import uuid4

from ai_gateway import handlers
from ai_gateway.serializers import AiAgentRunSerializer
from jobs.registry import JobContext


def _context(payload):
    return JobContext(job_id=uuid4(), org_id=uuid4(), created_by=uuid4(), attempt=1, max_attempts=3,
                      payload=payload)


def test_worker_claims_follow_the_sealed_session_assurance():
    assert json.loads(handlers._claims(_context({"session_aal": "aal2"})))["aal"] == "aal2"
    assert json.loads(handlers._claims(_context({"session_aal": "aal1"})))["aal"] == "aal1"
    assert json.loads(handlers._claims(_context({})))["aal"] == "aal1"
    assert json.loads(handlers._claims(_context({"session_aal": "AAL2 "})))["aal"] == "aal1"


def test_run_payload_accepts_only_known_assurance_levels():
    base = {"ai_job_id": str(uuid4()), "mode": "new", "surface": "dashboard", "goal": "x",
            "operation_key": "operation-key-1"}
    serializer = AiAgentRunSerializer(data=base)
    assert serializer.is_valid()
    assert serializer.validated_data["session_aal"] == "aal1"
    assert not AiAgentRunSerializer(data={**base, "session_aal": "aal3"}).is_valid()


def test_generic_queue_reseals_assurance_from_the_token(monkeypatch):
    from contextlib import contextmanager
    from types import SimpleNamespace

    from rest_framework.test import APIClient

    from jobs import views

    captured = {}
    token = SimpleNamespace(user_id=uuid4(), claims={}, aal="aal1")
    tenant = SimpleNamespace(active_organization=SimpleNamespace(role="ESTIMATOR"))

    @contextmanager
    def fake_scope(request, allowed=None):
        yield token, tenant, uuid4()

    def fake_enqueue(**kwargs):
        captured.update(kwargs)
        return {"id": str(uuid4())}, True

    monkeypatch.setattr(views, "job_scope", fake_scope)
    monkeypatch.setattr(views.service, "enqueue", fake_enqueue)
    monkeypatch.setattr(views, "JobRunSerializer", lambda job: SimpleNamespace(data=job))
    client = APIClient()
    client.force_authenticate(user=SimpleNamespace(is_authenticated=True), token=object())
    response = client.post("/api/v1/jobs/", {
        "type": "ai.agent.run", "payload": {"ai_job_id": str(uuid4()), "session_aal": "aal2"},
    }, format="json")
    assert response.status_code in (200, 201), response.data
    # A client-declared aal2 never survives: the verified token's level wins.
    assert captured["payload"]["session_aal"] == "aal1"
