"""Durable job queue: registry, service validation, worker state machine."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from rest_framework import serializers
from rest_framework.test import APIClient

from jobs import registry, repository, service, worker
from jobs.serializers import JobEnqueueSerializer, JobRunSerializer
from jobs import views as job_views


class DemoPayloadSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)


@pytest.fixture(autouse=True)
def isolated_registry(monkeypatch: pytest.MonkeyPatch):
    registry.reset_registry()
    yield
    registry.reset_registry()


def register_demo(run=None):
    @registry.register(
        "demo.echo",
        roles=("OWNER", "ESTIMATOR"),
        payload_serializer=DemoPayloadSerializer,
    )
    def demo_run(payload, context, report):
        report(50)
        return {"echo": payload["amount"], "org": str(context.org_id)}

    return demo_run if run is None else run


def test_registry_rejects_unknown_types_and_duplicates() -> None:
    register_demo()
    assert registry.public_types() == ("demo.echo",)
    assert registry.spec_for("demo.echo") is not None
    assert registry.spec_for("demo.other") is None
    with pytest.raises(registry.JobRegistryError):
        register_demo()


def test_enqueue_validates_payload_against_spec(monkeypatch) -> None:
    register_demo()
    org_id, actor = uuid4(), uuid4()
    captured: dict[str, object] = {}

    def fake_insert(**kwargs):
        captured.update(kwargs)
        return {"id": uuid4(), "type": "demo.echo", "state": "QUEUED"}, True

    monkeypatch.setattr(repository, "insert_job", fake_insert)
    with pytest.raises(service.JobServiceError) as bad:
        service.enqueue(org_id=org_id, job_type="demo.echo", payload={"amount": 0})
    assert bad.value.code == "job_payload_invalid"

    with pytest.raises(service.JobServiceError) as unknown:
        service.enqueue(org_id=org_id, job_type="demo.missing", payload={})
    assert unknown.value.code == "job_type_unknown"

    job, created = service.enqueue(
        org_id=org_id,
        job_type="demo.echo",
        payload={"amount": 7},
        idempotency_key="k-1",
        created_by=actor,
    )
    assert created is True
    assert captured["idempotency_key"] == "k-1"
    assert captured["created_by"] == actor
    assert captured["payload"] == {"amount": 7}


def test_worker_executes_handler_and_reports_success(monkeypatch) -> None:
    register_demo()
    org_id, job_id, actor = uuid4(), uuid4(), uuid4()
    succeeded: dict[str, object] = {}
    progress_values: list[float] = []

    def record_progress(*, job_id, progress):
        progress_values.append(progress)

    monkeypatch.setattr(repository, "report_progress", record_progress)
    monkeypatch.setattr(
        repository, "succeed", lambda *, job_id, result: succeeded.update(result)
    )

    claimed = {
        "id": job_id,
        "org_id": org_id,
        "created_by": actor,
        "type": "demo.echo",
        "payload": {"amount": 42},
        "attempt": 1,
        "max_attempts": 3,
    }
    worker._execute(claimed)
    assert progress_values == [50]
    assert succeeded == {"echo": 42, "org": str(org_id)}


def test_worker_marks_failure_with_error_payload(monkeypatch) -> None:
    def boom(payload, context, report):
        raise RuntimeError("upstream offline")

    registry.register(
        "demo.boom", roles=("OWNER",), payload_serializer=DemoPayloadSerializer
    )(boom)
    outcomes: list[dict[str, object]] = []
    monkeypatch.setattr(repository, "report_progress", lambda **kwargs: None)
    monkeypatch.setattr(
        repository, "fail_or_retry", lambda **kwargs: outcomes.append(kwargs) or "QUEUED"
    )

    worker._execute(
        {
            "id": uuid4(),
            "org_id": uuid4(),
            "created_by": uuid4(),
            "type": "demo.boom",
            "payload": {"amount": 1},
            "attempt": 2,
            "max_attempts": 3,
        }
    )
    assert len(outcomes) == 1
    assert outcomes[0]["error"]["code"] == "job_handler_error"
    assert "upstream offline" in outcomes[0]["error"]["detail"]
    assert outcomes[0]["attempt"] == 2
    assert outcomes[0]["max_attempts"] == 3


def test_worker_fails_unregistered_type(monkeypatch) -> None:
    outcomes: list[dict[str, object]] = []
    monkeypatch.setattr(
        repository, "fail_or_retry", lambda **kwargs: outcomes.append(kwargs) or "FAILED"
    )
    worker._execute(
        {
            "id": uuid4(),
            "org_id": uuid4(),
            "created_by": None,
            "type": "demo.ghost",
            "payload": {},
            "attempt": 1,
            "max_attempts": 3,
        }
    )
    assert outcomes[0]["error"]["code"] == "job_type_unregistered"


def test_enqueue_serializer_rejects_unknown_fields() -> None:
    serializer = JobEnqueueSerializer(
        data={"type": "demo.echo", "payload": {}, "surprise": True}
    )
    assert not serializer.is_valid()
    serializer = JobEnqueueSerializer(
        data={"type": "demo.echo", "payload": {"amount": 3}}
    )
    assert serializer.is_valid()


def _tenant(role: str, org_id):
    return SimpleNamespace(
        active_organization=SimpleNamespace(organization_id=org_id, role=role)
    )


def _client_with_scope(monkeypatch, role: str):
    """Authenticated client whose job_scope is a canned tenant resolution."""
    from contextlib import contextmanager

    org_id = uuid4()
    token = SimpleNamespace(user_id=uuid4(), claims={}, aal="aal1")

    @contextmanager
    def fake_scope(request):
        yield token, _tenant(role, org_id), org_id

    monkeypatch.setattr(job_views, "job_scope", fake_scope)
    client = APIClient()
    client.force_authenticate(
        user=SimpleNamespace(is_authenticated=True), token=object()
    )
    return client, token, org_id


def test_enqueue_view_denies_role_outside_spec(monkeypatch) -> None:
    register_demo()
    client, _, _ = _client_with_scope(monkeypatch, "WORKSHOP_MANAGER")
    response = client.post(
        "/api/v1/jobs/",
        {"type": "demo.echo", "payload": {"amount": 1}},
        format="json",
    )
    assert response.status_code == 403
    assert response.data["error"]["code"] == "job_permission_denied"


def test_enqueue_view_rejects_unknown_type(monkeypatch) -> None:
    client, _, _ = _client_with_scope(monkeypatch, "OWNER")
    response = client.post(
        "/api/v1/jobs/", {"type": "demo.ghost", "payload": {}}, format="json"
    )
    assert response.status_code == 422
    assert response.data["error"]["code"] == "job_type_unknown"


def test_enqueue_view_creates_and_dedupes(monkeypatch) -> None:
    register_demo()
    client, token, org_id = _client_with_scope(monkeypatch, "ESTIMATOR")
    calls: list[dict[str, object]] = []

    def fake_enqueue(**kwargs):
        calls.append(kwargs)
        row = {
            "id": uuid4(),
            "type": "demo.echo",
            "state": "QUEUED",
            "progress": "0.00",
            "result": None,
            "error": None,
            "attempt": 0,
            "max_attempts": 3,
            "created_at": datetime.now(timezone.utc),
            "started_at": None,
            "completed_at": None,
        }
        return row, len(calls) == 1

    monkeypatch.setattr(service, "enqueue", fake_enqueue)
    body = {
        "type": "demo.echo",
        "payload": {"amount": 9},
        "idempotency_key": "abc",
    }
    first = client.post("/api/v1/jobs/", body, format="json")
    second = client.post("/api/v1/jobs/", body, format="json")
    assert first.status_code == 201
    assert second.status_code == 200
    assert calls[0]["created_by"] == token.user_id
    assert calls[0]["idempotency_key"] == "abc"
    JobRunSerializer(first.data)


def test_detail_view_404s_for_missing_job(monkeypatch) -> None:
    client, _, _ = _client_with_scope(monkeypatch, "OWNER")
    monkeypatch.setattr(service, "get", lambda *, org_id, job_id: None)
    response = client.get(f"/api/v1/jobs/{uuid4()}/")
    assert response.status_code == 404
    assert response.data["error"]["code"] == "job_not_found"


def test_list_view_passes_filters(monkeypatch) -> None:
    client, _, org_id = _client_with_scope(monkeypatch, "INSTALLER")
    seen: dict[str, object] = {}
    monkeypatch.setattr(
        service,
        "list_recent",
        lambda **kwargs: seen.update(kwargs) or [],
    )
    response = client.get("/api/v1/jobs/?state=FAILED&type=demo.echo&limit=5")
    assert response.status_code == 200
    assert seen == {
        "org_id": org_id,
        "job_type": "demo.echo",
        "state": "FAILED",
        "limit": 5,
    }
