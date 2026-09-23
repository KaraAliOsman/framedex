"""Unit tests for the production service + views."""

from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest
from rest_framework.test import APIClient

from documents.repository import DocumentaryError
from production import service, views as production_views


@contextmanager
def _atomic():
    yield


def _tenant(role: str, org_id):
    return SimpleNamespace(
        active_organization=SimpleNamespace(organization_id=org_id, role=role)
    )


def _client_with_scope(monkeypatch, role: str):
    org_id = uuid4()
    token = SimpleNamespace(user_id=uuid4(), claims={}, aal="aal1")

    @contextmanager
    def fake_scope(request, allowed):
        assert role in allowed
        yield token, _tenant(role, org_id), org_id

    monkeypatch.setattr(production_views, "documentary_scope", fake_scope)
    client = APIClient()
    client.force_authenticate(user=SimpleNamespace(is_authenticated=True), token=object())
    return client, token, org_id


def _version_row(snapshot: dict) -> dict:
    return {
        "id": uuid4(),
        "project_id": uuid4(),
        "revision_code": "REV-A",
        "snapshot_json": snapshot,
        "production_allowed": True,
    }


_SNAPSHOT = {
    "bom": [
        {
            "position_id": str(uuid4()),
            "quantity": 1,
            "engine_result": {
                "profile_cuts": [{"sku": "MARCO", "length_mm": "900"}],
                "reinforcements": [],
                "glasses": [{"width_mm": "800", "height_mm": "600"}],
                "panels": [],
                "hardware_items": [],
            },
        }
    ]
}


def test_routing_skips_cut_and_glaze_without_materials() -> None:
    routing = service._routing({"glasses": [], "panels": [], "profile_cuts": [], "reinforcements": []})
    assert routing == ["ASSEMBLE", "QC", "PACK"]
    routing = service._routing({"profile_cuts": [{"sku": "x"}], "glasses": [{"a": 1}], "panels": []})
    assert routing == ["CUT", "ASSEMBLE", "GLAZE", "QC", "PACK"]


def test_release_rejects_not_allowed_version() -> None:
    version = _version_row({"bom": []})
    version["production_allowed"] = False
    with patch("production.service.one", return_value=version), patch(
        "production.service.transaction.atomic", return_value=_atomic()
    ), patch("production.service.documentary_backend", return_value=_atomic()):
        with pytest.raises(DocumentaryError) as error:
            service.release_production(org_id=uuid4(), version_id=uuid4(), actor_id=uuid4())
    assert error.value.code == "version_not_releasable"


def test_release_creates_work_order_with_steps() -> None:
    version = _version_row(_SNAPSHOT)
    order_id = uuid4()
    inserted_rows = []

    def fake_one(query, params=(), code=None):
        if "project_versions" in query:
            return version
        raise AssertionError(query)

    def fake_rows(query, params=()):
        if "INSERT INTO public.orders" in query:
            return [{"id": order_id}]
        if "FROM public.orders" in query and "GROUP BY" in query:
            return [
                {
                    "id": order_id,
                    "order_code": "OT-REV-A-01",
                    "order_type": "WORKSHOP_OT",
                    "status": "RELEASED",
                    "payload_json": service._work_order_payload(_SNAPSHOT["bom"][0]),
                    "project_version_id": version["id"],
                    "created_at": "2026-09-23T00:00:00Z",
                    "steps_total": 5,
                    "steps_done": 0,
                }
            ]
        inserted_rows.append(query)
        return []

    with patch("production.service.one", side_effect=fake_one), patch(
        "production.service.rows", side_effect=fake_rows
    ), patch("production.service.transaction.atomic", return_value=_atomic()), patch(
        "production.service.documentary_backend", return_value=_atomic()
    ):
        output = service.release_production(
            org_id=uuid4(), version_id=version["id"], actor_id=uuid4()
        )
    assert output["released"] == 1 and output["created"] == 1
    step_inserts = [q for q in inserted_rows if "production_steps" in q]
    assert len(step_inserts) == 5  # CUT ASSEMBLE GLAZE QC PACK
    event_inserts = [q for q in inserted_rows if "production_step_events" in q]
    assert len(event_inserts) == 1


def test_release_replay_returns_existing() -> None:
    version = _version_row(_SNAPSHOT)
    existing_id = uuid4()

    def fake_one(query, params=(), code=None):
        if "project_versions" in query:
            return version
        if "SELECT id FROM public.orders" in query:
            return {"id": existing_id}
        raise AssertionError(query)

    def fake_rows(query, params=()):
        if "INSERT INTO public.orders" in query:
            return []  # conflict → no row
        if "GROUP BY" in query:
            return [
                {
                    "id": existing_id,
                    "order_code": "OT-REV-A-01",
                    "order_type": "WORKSHOP_OT",
                    "status": "RELEASED",
                    "payload_json": {"position_id": _SNAPSHOT["bom"][0]["position_id"]},
                    "project_version_id": version["id"],
                    "created_at": "2026-09-23T00:00:00Z",
                    "steps_total": 5,
                    "steps_done": 2,
                }
            ]
        return []

    with patch("production.service.one", side_effect=fake_one), patch(
        "production.service.rows", side_effect=fake_rows
    ), patch("production.service.transaction.atomic", return_value=_atomic()), patch(
        "production.service.documentary_backend", return_value=_atomic()
    ):
        output = service.release_production(
            org_id=uuid4(), version_id=version["id"], actor_id=uuid4()
        )
    assert output["released"] == 1 and output["created"] == 0


def _transition_fakes(step: dict, order_status: str):
    def fake_one(query, params=(), code=None):
        if "SELECT order_id FROM public.production_steps" in query:
            return {"order_id": step["order_id"]}
        if "FROM public.orders" in query:
            return {"id": step["order_id"], "status": order_status}
        if "FOR UPDATE OF s" in query:
            return step
        raise AssertionError(query)

    return fake_one


def _step_row(**overrides) -> dict:
    base = {
        "id": uuid4(),
        "order_id": uuid4(),
        "status": "READY",
        "sequence": 1,
        "code": "CUT",
        "label": "x",
        "work_center_id": None,
        "started_at": None,
        "finished_at": None,
        "actor_id": None,
        "note": None,
    }
    base.update(overrides)
    return base


def test_transition_step_rejects_invalid_state() -> None:
    step = _step_row(status="DONE")
    fake_one = _transition_fakes(step, "IN_PROGRESS")

    with patch("production.service.one", side_effect=fake_one), patch(
        "production.service.transaction.atomic", return_value=_atomic()
    ):
        with pytest.raises(DocumentaryError) as error:
            service.transition_step(
                org_id=uuid4(), step_id=step["id"], action="START",
                actor_id=uuid4(), note=None,
            )
    assert error.value.code == "step_transition_invalid"


def test_transition_step_completed_order_blocked() -> None:
    step = _step_row()
    fake_one = _transition_fakes(step, "COMPLETED")

    with patch("production.service.one", side_effect=fake_one), patch(
        "production.service.transaction.atomic", return_value=_atomic()
    ):
        with pytest.raises(DocumentaryError) as error:
            service.transition_step(
                org_id=uuid4(), step_id=step["id"], action="START",
                actor_id=uuid4(), note=None,
            )
    assert error.value.code == "work_order_completed"


def test_start_from_blocked_step_is_rejected() -> None:
    step = _step_row(status="BLOCKED")
    fake_one = _transition_fakes(step, "IN_PROGRESS")

    with patch("production.service.one", side_effect=fake_one), patch(
        "production.service.transaction.atomic", return_value=_atomic()
    ):
        with pytest.raises(DocumentaryError) as error:
            service.transition_step(
                org_id=uuid4(), step_id=step["id"], action="START",
                actor_id=uuid4(), note=None,
            )
    assert error.value.code == "step_transition_invalid"


def test_note_action_requires_text() -> None:
    with pytest.raises(DocumentaryError) as error:
        service.transition_step(
            org_id=uuid4(), step_id=uuid4(), action="NOTE",
            actor_id=uuid4(), note="   ",
        )
    assert error.value.code == "step_note_required"


def test_hold_event_only_appended_once() -> None:
    captured = []

    def fake_one(query, params=(), code=None):
        if "SELECT status::text" in query:
            return {"status": "HOLD"}
        if "production_steps" in query:
            return {"total": 2, "done": 0, "blocked": 1, "in_progress": 0}
        if "UPDATE public.orders" in query:
            return {"status": "HOLD"}
        raise AssertionError(query)

    def fake_rows(query, params=()):
        captured.append(query)
        return []

    with patch("production.service.one", side_effect=fake_one), patch(
        "production.service.rows", side_effect=fake_rows
    ):
        status = service._refresh_order_status(
            org_id=uuid4(), order_id=uuid4(), actor_id=uuid4()
        )
    assert status == "HOLD"
    assert not any("WO_HOLD" in query for query in captured)


def test_hold_event_appended_on_transition_into_hold() -> None:
    captured = []

    def fake_one(query, params=(), code=None):
        if "SELECT status::text" in query:
            return {"status": "IN_PROGRESS"}
        if "production_steps" in query:
            return {"total": 2, "done": 0, "blocked": 1, "in_progress": 0}
        if "UPDATE public.orders" in query:
            return {"status": "HOLD"}
        raise AssertionError(query)

    def fake_rows(query, params=()):
        captured.append(query)
        return []

    with patch("production.service.one", side_effect=fake_one), patch(
        "production.service.rows", side_effect=fake_rows
    ):
        service._refresh_order_status(
            org_id=uuid4(), order_id=uuid4(), actor_id=uuid4()
        )
    assert any("WO_HOLD" in query for query in captured)


def test_order_code_scopes_to_project() -> None:
    snapshot = {
        "project": {"code": "PRO-77"},
        "bom": _SNAPSHOT["bom"],
    }
    version = _version_row(snapshot)
    seen = {}

    def fake_one(query, params=(), code=None):
        if "project_versions" in query:
            return version
        raise AssertionError(query)

    def fake_rows(query, params=()):
        if "INSERT INTO public.orders" in query:
            seen["order_code"] = params[2]
            return [{"id": uuid4()}]
        if "GROUP BY" in query:
            return []
        return []

    with patch("production.service.one", side_effect=fake_one), patch(
        "production.service.rows", side_effect=fake_rows
    ), patch("production.service.transaction.atomic", return_value=_atomic()), patch(
        "production.service.documentary_backend", return_value=_atomic()
    ), patch(
        "production.service._ensure_work_centers", return_value={}
    ):
        service.release_production(
            org_id=uuid4(), version_id=version["id"], actor_id=uuid4()
        )
    assert seen["order_code"] == "OT-PRO-77-REV-A-01"


def test_work_center_upsert_reports_created() -> None:
    row = {
        "id": uuid4(), "code": "X", "name": "x", "kind": "CUT",
        "display_order": 0, "active": True, "created": False,
    }
    with patch("production.service.one", return_value=row):
        center, created = service.create_work_center(
            org_id=uuid4(), code="X", name="x", kind="CUT", display_order=0
        )
    assert created is False
    assert center["code"] == "X"


def test_release_post_forwards_scope(monkeypatch) -> None:
    client, token, org_id = _client_with_scope(monkeypatch, "WORKSHOP_MANAGER")
    seen = {}

    def fake_release(**kwargs):
        seen.update(kwargs)
        return {"version_id": kwargs["version_id"], "released": 1, "created": 1, "orders": []}

    monkeypatch.setattr(service, "release_production", fake_release)
    version_id = uuid4()
    response = client.post(f"/api/v1/production/versions/{version_id}/release/")
    assert response.status_code == 201
    assert seen["actor_id"] == token.user_id
    assert seen["org_id"] == org_id


def test_release_denies_estimator(monkeypatch) -> None:
    org_id = uuid4()
    token = SimpleNamespace(user_id=uuid4(), claims={}, aal="aal1")

    @contextmanager
    def fake_scope(request, allowed):
        from authentication.errors import contract_error

        if "ESTIMATOR" in allowed and len(allowed) > 1:
            yield token, _tenant("ESTIMATOR", org_id), org_id
        else:
            raise contract_error(403, "documentary_permission_denied", "denied")
            yield

    monkeypatch.setattr(production_views, "documentary_scope", fake_scope)
    client = APIClient()
    client.force_authenticate(user=SimpleNamespace(is_authenticated=True), token=object())
    response = client.post(f"/api/v1/production/versions/{uuid4()}/release/")
    assert response.status_code == 403


def test_orders_list_allows_installer(monkeypatch) -> None:
    client, _, _ = _client_with_scope(monkeypatch, "INSTALLER")
    monkeypatch.setattr(
        service, "list_production_orders", lambda *, org_id: {"orders": []}
    )
    response = client.get("/api/v1/production/orders/")
    assert response.status_code == 200


def test_step_transition_forwards_action(monkeypatch) -> None:
    client, token, _ = _client_with_scope(monkeypatch, "INSTALLER")
    seen = {}

    def fake_transition(**kwargs):
        seen.update(kwargs)
        return {"step": {}, "order_status": "IN_PROGRESS"}

    monkeypatch.setattr(service, "transition_step", fake_transition)
    response = client.post(
        f"/api/v1/production/steps/{uuid4()}/transition/",
        {"action": "START", "note": "voy"},
        format="json",
    )
    assert response.status_code == 200
    assert seen["action"] == "START"
    assert seen["actor_id"] == token.user_id
