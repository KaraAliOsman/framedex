"""Context-bound presence and safe read projections."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

from ai_gateway import jobs, views
from ai_gateway.serializers import AiPresenceQuerySerializer
from jobs import presentation, repository, service
import pytest


def test_presence_binds_tenant_user_and_exact_stable_context(monkeypatch):
    org, actor, project = uuid4(), uuid4(), uuid4()
    calls = []
    @contextmanager
    def scope(*_):
        yield SimpleNamespace(user_id=actor), None, org
    monkeypatch.setattr(views, "documentary_scope", scope)
    monkeypatch.setattr(jobs, "list_jobs", lambda **kwargs: calls.append(kwargs) or [{"id": "context-job"}])
    monkeypatch.setattr(presentation, "context_identity", lambda **_: {"context_label": "P-000012 · Obra", "context_url": "/projects/p"})
    request = APIRequestFactory().get("/ai/presence/", {"surface": "project", "refs": '{"project_id":"'+str(project)+'","selection":"m1"}'})
    response = views.AiPresenceView().get(Request(request))
    assert response.status_code == 200
    assert response.data["job"]["id"] == "context-job"
    assert calls == [{"org_id": org, "user_id": actor, "surface": "project", "refs": {"project_id": str(project)}, "limit": 1}]


@pytest.mark.parametrize("value", ['[]', '{"project_id": {}}', 'null', 'not-json', '{"x":'+('"'+('a'*500)+'"')+'}'])
def test_presence_rejects_nested_or_unbounded_identifiers(value):
    serializer = AiPresenceQuerySerializer(data={"surface": "project", "refs": value})
    assert not serializer.is_valid()


def test_context_lookup_never_links_to_another_tenant(monkeypatch):
    org, project, position = uuid4(), uuid4(), uuid4()
    queries = []
    monkeypatch.setattr(presentation, "rows", lambda query, params: queries.append((query, params)) or [])
    assert presentation.context_identity(org_id=org, refs={"project_id": str(project), "position_id": str(position)}) == {"context_label": "Posición no disponible", "context_url": None}
    assert queries[0][1] == [str(org), str(position), str(project), str(project)]
    assert "pos.org_id=%s" in queries[0][0]


def test_duration_is_elapsed_work_and_not_queued_wait():
    start = datetime(2026, 10, 9, tzinfo=timezone.utc)
    assert presentation.duration_ms({"created_at": start}) is None
    assert presentation.duration_ms({"started_at": start, "completed_at": start+timedelta(milliseconds=1321)}) == 1321


def test_generic_retry_cannot_resume_an_ai_conversation(monkeypatch):
    from ai_gateway.serializers import AiAgentRunSerializer
    from jobs import registry
    monkeypatch.setattr(repository, "get_job", lambda **_: {"id": str(uuid4()), "state": "FAILED", "type": "ai.agent.run"})
    monkeypatch.setattr(registry, "spec_for", lambda _: SimpleNamespace(roles=("ESTIMATOR",), payload_serializer=AiAgentRunSerializer))
    with pytest.raises(service.JobServiceError, match="job_permission_denied"):
        service.retry(org_id=uuid4(), job_id=uuid4(), actor_id=uuid4(), role="ESTIMATOR")


def test_explicit_provider_proposes_intents_without_numeric_effects():
    from ai_gateway.providers import _agent_output
    result = _agent_output({"goal": "divide la hoja en dos oscilobatientes", "surface": "position", "context": {}, "observations": [{"surface":"calculate_position"}], "product": {"assembly": {"modules": [{"id": "single"}]}}})
    ops = result["steps"][0]["ops"]
    assert ops == [{"op":"split_bay","module":"single","bay":"b1","axis":"V","from":"CENTER"}, {"op":"set_opening","module":"single","opening":"TILT_TURN_LEFT"}]
    assert all("result" not in op and "price" not in op for op in ops)
