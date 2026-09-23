"""Unit tests for the production service + views."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime
import json
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


_POSITION_ID = str(uuid4())
_SNAPSHOT = {
    "positions": [{"id": _POSITION_ID, "system_id": str(uuid4())}],
    "bom": [
        {
            "position_id": _POSITION_ID,
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
        "production.service.transaction.atomic", side_effect=_atomic
    ), patch("production.service.documentary_backend", side_effect=_atomic):
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
    ), patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
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
    ), patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
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
        "production.service.transaction.atomic", side_effect=_atomic
    ), patch("production.service.documentary_backend", side_effect=_atomic):
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
        "production.service.transaction.atomic", side_effect=_atomic
    ), patch("production.service.documentary_backend", side_effect=_atomic):
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
        "production.service.transaction.atomic", side_effect=_atomic
    ), patch("production.service.documentary_backend", side_effect=_atomic):
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
    ), patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
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
    with patch("production.service.one", return_value=row), patch(
        "production.service.transaction.atomic", side_effect=_atomic
    ), patch("production.service.documentary_backend", side_effect=_atomic):
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


def test_optimize_work_order_builds_bar_plan_and_event() -> None:
    from decimal import Decimal

    from dekopen_engine.cutting import (
        CutBar, CutMaterial, CutOptimizationResult, CuttingProfile,
        PurchaseLine, StockRule,
    )

    order_id = uuid4()
    payload = {
        "position_id": str(uuid4()),
        "system_id": str(uuid4()),
        "quantity": 2,
        "materials": {
            "profile_cuts": [
                {
                    "qty": 2, "sku": "MARCO", "role": "FRAME",
                    "material": "PVC", "length_mm": "900.00",
                    "angle_left": "45.0", "angle_right": "45.0",
                }
            ],
            "reinforcements": [], "glasses": [], "panels": [], "hardware_items": [],
        },
    }
    seen = {}

    def fake_one(query, params=(), code=None):
        if "FOR UPDATE" in query:
            return {
                "id": order_id, "order_code": "OT-P-REV-A-01",
                "status": "RELEASED", "payload_json": payload,
            }
        if "snapshot_json" in query:
            return {"snapshot_json": {"positions": [], "manufacturing": []}}
        raise AssertionError(query)

    def fake_rows(query, params=()):
        if "inventory_items" in query:
            return []
        seen.setdefault("writes", []).append(query)
        return []

    stock = StockRule(
        stock_authority_id="S1", workshop_sku="MARCO",
        commercial_sku="P-MARCO-60", manufacturer_name="DEMO",
        supplier_name=None, purchase_unit="BAR",
        material=CutMaterial.PVC, color="BLANCO",
        stock_length_mm=Decimal("6000"),
    )
    authorities = SimpleNamespace(
        stocks=[stock], reinforcement_skus={}, inertias={},
    )
    profile = CuttingProfile(
        id="CP1", code="SAW01", kerf_mm=Decimal("5"),
        head_trim_mm=Decimal("10"), tail_trim_mm=Decimal("10"),
    )
    cut_result = CutOptimizationResult(
        workshop_cut_plan=[CutBar(
            bar_index=1, commercial_sku="P-MARCO-60",
            material=CutMaterial.PVC, color="BLANCO",
            stock_length_mm=Decimal("6000"),
            head_trim_mm=Decimal("10"), tail_trim_mm=Decimal("10"),
            kerf_mm=Decimal("5"), cuts=[],
            kerf_total_mm=Decimal("0"),
            productive_length_mm=Decimal("0"),
            process_consumed_mm=Decimal("0"),
            remainder_mm=Decimal("3000"),
            waste_mm=Decimal("0"),
            yield_pct=Decimal("50"), waste_pct=Decimal("50"),
        )],
        purchase_list=[PurchaseLine(
            commercial_sku="P-MARCO-60", manufacturer="DEMO",
            supplier=None, stock_length_mm=Decimal("6000"),
            material=CutMaterial.PVC, color="BLANCO",
            unit="BAR", qty_bars=1,
        )],
    )

    with patch("production.service.one", side_effect=fake_one), patch(
        "production.service.rows", side_effect=fake_rows
    ), patch("production.service.transaction.atomic", return_value=_atomic()), patch(
        "production.service.documentary_backend", return_value=_atomic()
    ), patch(
        "production.service.CuttingRepository"
    ) as repo, patch(
        "production.service.optimize_cut", return_value=cut_result
    ) as cut:
        repo.return_value.for_result.return_value = authorities
        repo.return_value.cutting_profile.return_value = profile
        output = service.optimize_work_order(
            org_id=uuid4(), order_id=order_id, actor_id=uuid4(), color="BLANCO",
        )
    assert output["optimization"]["color"] == "BLANCO"
    assert output["optimization"]["units"] == 2
    pieces_arg = cut.call_args[0][0]
    assert len(pieces_arg) == 4  # qty 2 per unit x 2 units
    assert len({p.unit_index for p in pieces_arg}) == 4  # unique per-unit identity
    writes = seen["writes"]
    assert any("payload_json" in q for q in writes)
    assert any("WO_OPTIMIZED" in q for q in writes)


def test_pick_sheet_rule_prefers_smallest_fitting() -> None:
    from decimal import Decimal

    rules = _sheet_rules_fake(
        [("BIG", "3000", "2000"), ("MID", "2000", "1500"), ("SML", "1200", "900")]
    )
    picked = service._pick_sheet_rule(rules, Decimal("1100"), Decimal("800"))
    assert picked is not None and picked.workshop_sku == "SML"
    rotated = service._pick_sheet_rule(rules, Decimal("800"), Decimal("1300"))
    assert rotated is not None and rotated.workshop_sku == "MID"
    too_big = service._pick_sheet_rule(rules, Decimal("4000"), Decimal("500"))
    assert too_big is not None and too_big.workshop_sku == "BIG"  # largest fallback
    assert service._pick_sheet_rule([], Decimal("10"), Decimal("10")) is None


def _sheet_rules_fake(rows_spec):
    from decimal import Decimal

    from dekopen_engine.nesting import SheetRule

    return [
        SheetRule(
            workshop_sku=sku, purchasing_sku=sku,
            sheet_width_mm=Decimal(w), sheet_height_mm=Decimal(h),
        )
        for sku, w, h in sorted(rows_spec, key=lambda r: Decimal(r[1]) * Decimal(r[2]))
    ]


def test_release_seals_system_from_snapshot_positions() -> None:
    seen = {}

    def fake_one(query, params=(), code=None):
        if "project_versions" in query:
            return _version_row(_SNAPSHOT)
        raise AssertionError(query)

    def fake_rows(query, params=()):
        if "INSERT INTO public.orders" in query:
            seen["payload"] = params[3]
            return [{"id": uuid4()}]
        return []

    with patch("production.service.one", side_effect=fake_one), patch(
        "production.service.rows", side_effect=fake_rows
    ), patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ), patch(
        "production.service._ensure_work_centers", return_value={}
    ):
        service.release_production(
            org_id=uuid4(), version_id=uuid4(), actor_id=uuid4()
        )
    assert json.loads(seen["payload"])["system_id"] == _SNAPSHOT["positions"][0]["system_id"]


def test_optimize_rejects_completed_order() -> None:
    order_id = uuid4()

    def fake_one(query, params=(), code=None):
        if "FOR UPDATE" in query:
            return {
                "id": order_id, "order_code": "OT", "status": "COMPLETED",
                "payload_json": {},
            }
        raise AssertionError(query)

    with patch("production.service.one", side_effect=fake_one), patch(
        "production.service.transaction.atomic", return_value=_atomic()
    ), patch("production.service.documentary_backend", return_value=_atomic()):
        with pytest.raises(DocumentaryError) as error:
            service.optimize_work_order(
                org_id=uuid4(), order_id=order_id, actor_id=uuid4(), color="BLANCO",
            )
    assert error.value.code == "work_order_completed"


def test_optimize_requires_color() -> None:
    with pytest.raises(DocumentaryError) as error:
        service.optimize_work_order(
            org_id=uuid4(), order_id=uuid4(), actor_id=uuid4(), color="  ",
        )
    assert error.value.code == "optimize_color_required"


def test_optimize_post_forwards_scope(monkeypatch) -> None:
    client, token, org_id = _client_with_scope(monkeypatch, "WORKSHOP_MANAGER")
    seen = {}

    def fake_optimize(**kwargs):
        seen.update(kwargs)
        return {"order_id": str(kwargs["order_id"]), "order_code": "OT", "optimization": {}}

    monkeypatch.setattr(service, "optimize_work_order", fake_optimize)
    order_id = uuid4()
    response = client.post(
        f"/api/v1/production/orders/{order_id}/optimize/",
        {"color": "BLANCO"}, format="json",
    )
    assert response.status_code == 200
    assert seen["actor_id"] == token.user_id
    assert seen["color"] == "BLANCO"


def test_optimize_post_rejects_blank_color(monkeypatch) -> None:
    client, _, _ = _client_with_scope(monkeypatch, "WORKSHOP_MANAGER")
    response = client.post(
        f"/api/v1/production/orders/{uuid4()}/optimize/",
        {"color": " "}, format="json",
    )
    assert response.status_code == 400






def test_qc_fail_blocks_step_and_holds_order(monkeypatch) -> None:
    org_id, step_id, order_id = uuid4(), uuid4(), uuid4()

    def fake_one(sql_text: str, params: list, code: str = "not_found") -> dict:
        lowered = " ".join(sql_text.lower().split())
        if "from public.production_steps" in lowered and "for update" in lowered:
            return {
                "id": str(step_id),
                "org_id": str(org_id),
                "order_id": str(order_id),
                "sequence": 5,
                "code": "QC",
                "label": "Control de calidad",
                "status": "IN_PROGRESS",
                "work_center_id": None,
                "work_center_code": "QC",
                "started_at": "2026-09-23T00:00:00+00:00",
                "finished_at": None,
                "actor_id": None,
                "note": None,
            }
        if "from public.orders" in lowered and "for update" in lowered:
            return {
                "id": str(order_id),
                "status": "RELEASED",
                "order_type": "WORKSHOP_OT",
                "payload_json": {},
            }
        if "order_id from public.production_steps" in lowered:
            return {"order_id": str(order_id)}
        if "from public.production_steps" in lowered:
            return {
                "id": str(step_id),
                "sequence": 5,
                "code": "QC",
                "label": "Control de calidad",
                "status": "BLOCKED",
                "work_center_id": None,
                "work_center_code": "QC",
                "started_at": "2026-09-23T00:00:00+00:00",
                "finished_at": None,
                "actor_id": None,
                "note": "rotura en esmerilado",
            }
        raise AssertionError(f"unexpected one(): {lowered}")

    writes: list[tuple[str, object]] = []

    def fake_rows(sql_text: str, params: object = ()) -> list[dict]:
        lowered = " ".join(sql_text.lower().split())
        writes.append((lowered, params))
        return [{"id": str(step_id)}] if "returning" in lowered else []

    monkeypatch.setattr("production.service.one", fake_one)
    monkeypatch.setattr("production.service.rows", fake_rows)
    monkeypatch.setattr("production.service._refresh_order_status", lambda **kw: "HOLD")
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ):
        result = service.transition_step(
            org_id=org_id,
            step_id=step_id,
            action="COMPLETE",
            actor_id=uuid4(),
            note="rotura en esmerilado",
            qc_result="FAIL",
        )
    step_update = next(
        p2 for s2, p2 in writes if "update public.production_steps" in s2
    )
    assert step_update["status"] == "BLOCKED"
    event_insert = next(
        p2 for s2, p2 in writes if "insert into public.production_step_events" in s2
    )
    assert event_insert[3] == "QC_FAILED"
    assert result["order_status"] == "HOLD"
    assert result["step"]["status"] == "BLOCKED"


def test_qc_result_rejected_on_non_qc_step(monkeypatch) -> None:
    org_id, step_id, order_id = uuid4(), uuid4(), uuid4()

    def fake_one(sql_text: str, params: list, code: str = "not_found") -> dict:
        lowered = " ".join(sql_text.lower().split())
        if "order_id from public.production_steps" in lowered:
            return {"order_id": str(order_id)}
        if "from public.orders" in lowered:
            return {"id": str(order_id), "status": "RELEASED"}
        if "from public.production_steps" in lowered:
            return {
                "id": str(step_id),
                "org_id": str(org_id),
                "order_id": str(order_id),
                "sequence": 2,
                "code": "ASSEMBLE",
                "label": "Ensamble",
                "status": "IN_PROGRESS",
                "work_center_id": None,
                "work_center_code": "ASSEMBLY",
                "started_at": None,
                "finished_at": None,
                "actor_id": None,
                "note": None,
            }
        raise AssertionError(f"unexpected one(): {lowered}")

    monkeypatch.setattr("production.service.one", fake_one)
    monkeypatch.setattr("production.service.rows", lambda *_a, **_k: [])
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ), pytest.raises(DocumentaryError, match="step_transition_invalid"):
        service.transition_step(
            org_id=org_id,
            step_id=step_id,
            action="COMPLETE",
            actor_id=uuid4(),
            note=None,
            qc_result="FAIL",
        )


def test_create_remake_clones_order_and_steps(monkeypatch) -> None:
    org_id, order_id, version_id, remake_id = uuid4(), uuid4(), uuid4(), uuid4()
    writes: list[tuple[str, list]] = []
    detail_calls: list[str] = []

    def fake_one(sql_text: str, params: list, code: str = "not_found") -> dict:
        lowered = " ".join(sql_text.lower().split())
        if "for update" in lowered:
            return {
                "id": str(order_id),
                "order_code": "OT-P-AAA-01",
                "status": "HOLD",
                "project_id": str(uuid4()),
                "project_version_id": str(version_id),
                "payload_json": {
                    "position_id": str(_POSITION_ID),
                    "quantity": 1,
                    "materials": {"profile_cuts": [{"a": 1}]},
                    "optimization": {"stale": True},
                },
            }
        if "count(*)" in lowered:
            return {"n": 1}
        if "insert into public.orders" in lowered:
            writes.append((lowered, list(params)))
            return {"id": str(remake_id), "order_code": "OT-P-AAA-01-RM-02"}
        raise AssertionError(f"unexpected one(): {lowered}")

    def fake_rows(sql_text: str, params: object = ()) -> list[dict]:
        lowered = " ".join(sql_text.lower().split())
        writes.append((lowered, list(params)))
        return [{"id": str(remake_id)}]

    monkeypatch.setattr("production.service.one", fake_one)
    monkeypatch.setattr("production.service.rows", fake_rows)
    monkeypatch.setattr(
        "production.service.get_work_order",
        lambda **kw: detail_calls.append(str(kw["order_id"])) or {"id": str(kw["order_id"])},
    )
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ):
        result = service.create_remake(
            org_id=org_id, order_id=order_id, actor_id=uuid4(), note="rehacer por QC"
        )
    order_insert = next(p2 for s2, p2 in writes if "insert into public.orders" in s2)
    payload = json.loads(order_insert[3])
    assert "optimization" not in payload
    assert payload["remake_of"] == str(order_id)
    assert order_insert[2] == "OT-P-AAA-01-RM-02"
    steps_copy = next(
        s2 for s2, _ in writes if "insert into public.production_steps" in s2 and "select" in s2
    )
    assert "from public.production_steps" in steps_copy
    assert any("wo_remade" in s2 for s2, _ in writes)
    assert detail_calls and result["id"] == str(remake_id)


def test_create_remake_requires_hold(monkeypatch) -> None:
    org_id, order_id = uuid4(), uuid4()
    monkeypatch.setattr(
        "production.service.one",
        lambda *_a, **_k: {
            "id": str(order_id),
            "order_code": "OT-P-AAA-01",
            "status": "RELEASED",
            "payload_json": {},
        },
    )
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ), pytest.raises(DocumentaryError, match="remake_requires_hold"):
        service.create_remake(org_id=org_id, order_id=order_id, actor_id=uuid4())


def test_export_cnc_files_writes_deterministic_csv(monkeypatch) -> None:
    org_id, order_id = uuid4(), uuid4()
    optimization = {
        "bars": {
            "workshop_cut_plan": [
                {
                    "bar_index": 1,
                    "commercial_sku": "MARCO-60",
                    "stock_length_mm": "6500",
                    "cuts": [
                        {"piece_id": "M-02", "length_mm": "1200", "sequence": 1,
                         "angle_left": "45.0", "angle_right": "45.0",
                         "unit_index": 1, "bay_id": "b1", "leaf_id": None,
                         "source_position_id": str(_POSITION_ID)},
                        {"piece_id": "M-01", "length_mm": "1500", "sequence": 2,
                         "angle_left": "90.0", "angle_right": "45.0",
                         "unit_index": 1, "bay_id": "b1", "leaf_id": None,
                         "source_position_id": str(_POSITION_ID)},
                    ],
                }
            ]
        },
        "sheets": [
            {
                "sheet_index": 2,
                "purchasing_sku": "GLASS-4",
                "sheet_width_mm": "3210",
                "sheet_height_mm": "2250",
                "placements": [
                    {"piece_id": "V-01", "x_mm": "100", "y_mm": "50",
                     "width_mm": "800", "height_mm": "600", "rotated": False,
                     "unit_index": 1, "bay_id": "b1", "leaf_id": "l1"}
                ],
            },
            {
                "sheet_index": 1,
                "purchasing_sku": "GLASS-4",
                "sheet_width_mm": "3210",
                "sheet_height_mm": "2250",
                "placements": [],
            },
        ],
    }
    writes: list[tuple[str, list]] = []

    def fake_one(sql_text: str, params: list, code: str = "not_found") -> dict:
        lowered = " ".join(sql_text.lower().split())
        if "for update" in lowered:
            return {
                "id": str(order_id),
                "order_code": "OT-P-AAA-01",
                "status": "IN_PROGRESS",
                "payload_json": {"optimization": optimization},
            }
        raise AssertionError(f"unexpected one(): {lowered}")

    monkeypatch.setattr("production.service.one", fake_one)
    monkeypatch.setattr(
        "production.service.rows",
        lambda sql_text, params=(): writes.append(
            (" ".join(sql_text.lower().split()), list(params))
        ) or [{"id": str(order_id)}],
    )
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ):
        out = service.export_cnc_files(org_id=org_id, order_id=order_id, actor_id=uuid4())
    update = next(p2 for s2, p2 in writes if "update public.orders" in s2)
    stored = json.loads(update[0])["cnc_export"]
    assert sorted(out["files"]) == ["bars.csv", "sheets.csv"]
    bars_csv = stored["files"]["bars.csv"]
    lines = bars_csv.strip().split("\n")
    assert lines[0].startswith("bar_index,")
    assert "M-02" in lines[1] and "M-01" in lines[2]  # stored cut sequence
    assert lines[1].split(",")[3] == "1"  # sequence_in_bar column
    assert "45.0" in lines[1] and "90.0" in lines[2]  # saw angles exported
    assert stored["schema"] == "work_order_cnc_export_v2"
    assert stored["optimization_fingerprint"]
    sheets_csv = stored["files"]["sheets.csv"]
    assert "GLASS-4" in sheets_csv and "V-01" in sheets_csv
    assert any("wo_cnc_exported" in s2 for s2, _ in writes)


def test_export_cnc_requires_optimization(monkeypatch) -> None:
    monkeypatch.setattr(
        "production.service.one",
        lambda *_a, **_k: {
            "id": "o",
            "order_code": "OT",
            "status": "RELEASED",
            "payload_json": {},
        },
    )
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ), pytest.raises(DocumentaryError, match="cnc_requires_optimization"):
        service.export_cnc_files(org_id=uuid4(), order_id=uuid4(), actor_id=uuid4())


def test_export_dxf_files_writes_deterministic_geometry(monkeypatch) -> None:
    org_id, order_id = uuid4(), uuid4()
    optimization = {
        "bars": {
            "workshop_cut_plan": [
                {
                    "bar_index": 1,
                    "commercial_sku": "MARCO-60",
                    "stock_length_mm": "6500",
                    "head_trim_mm": "15",
                    "tail_trim_mm": "20",
                    "kerf_mm": "4",
                    "cuts": [
                        {"piece_id": "M-02", "length_mm": "1200", "sequence": 1,
                         "unit_index": 1,
                         "angle_left": "45.0", "angle_right": "45.0"},
                        {"piece_id": "M-01", "length_mm": "1500", "sequence": 2,
                         "unit_index": 2,
                         "angle_left": "90.0", "angle_right": "45.0"},
                    ],
                }
            ]
        },
        "sheets": [
            {
                "sheet_index": 1,
                "purchasing_sku": "GLASS-4",
                "sheet_width_mm": "3210",
                "sheet_height_mm": "2250",
                "placements": [
                    {"piece_id": "V-01", "x_mm": "100", "y_mm": "50",
                     "width_mm": "800", "height_mm": "600", "unit_index": 2,
                     "rotated": False}
                ],
            },
        ],
    }
    writes: list[tuple[str, list]] = []

    def fake_one(sql_text: str, params: list, code: str = "not_found") -> dict:
        lowered = " ".join(sql_text.lower().split())
        if "for update" in lowered:
            return {
                "id": str(order_id),
                "order_code": "OT-P-AAA-01",
                "status": "IN_PROGRESS",
                "payload_json": {"optimization": optimization},
            }
        raise AssertionError(f"unexpected one(): {lowered}")

    monkeypatch.setattr("production.service.one", fake_one)
    monkeypatch.setattr(
        "production.service.rows",
        lambda sql_text, params=(): writes.append(
            (" ".join(sql_text.lower().split()), list(params))
        ) or [{"id": str(order_id)}],
    )
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ):
        out = service.export_dxf_files(org_id=org_id, order_id=order_id, actor_id=uuid4())
    update = next(p2 for s2, p2 in writes if "update public.orders" in s2)
    stored = json.loads(update[0])["dxf_export"]
    assert sorted(out["files"]) == ["bars.dxf", "sheet_1.dxf"]
    sheet = stored["files"]["sheet_1.dxf"]
    assert sheet.startswith("0\nSECTION\n2\nHEADER") and sheet.endswith("0\nEOF\n")
    assert "AC1015" in sheet and "V-01·U2 800x600" in sheet
    bars = stored["files"]["bars.dxf"]
    assert "M-02·U1 1200 45.0/45.0" in bars and "MARCO-60" in bars
    # Saw consumption matches optimize_cut: head trim once (mark at 15),
    # then each piece length + one kerf → piece ends at 1215 and 2719.
    for mark_x in ("10\n15\n20", "10\n1215\n20", "10\n2719\n20"):
        assert f"8\nMARK\n{mark_x}" in bars
    assert "10\n1200\n20" not in bars
    assert stored["schema"] == "work_order_dxf_export_v1"
    assert stored["optimization_fingerprint"]
    assert any("wo_dxf_exported" in s2 for s2, _ in writes)


def test_export_dxf_requires_optimization(monkeypatch) -> None:
    monkeypatch.setattr(
        "production.service.one",
        lambda *_a, **_k: {
            "id": "o",
            "order_code": "OT",
            "status": "RELEASED",
            "payload_json": {},
        },
    )
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ), pytest.raises(DocumentaryError, match="dxf_requires_optimization"):
        service.export_dxf_files(org_id=uuid4(), order_id=uuid4(), actor_id=uuid4())


def test_packing_manifest_builds_units_and_records(monkeypatch) -> None:
    org_id, order_id, actor_id = uuid4(), uuid4(), uuid4()
    events: list[list] = []
    payload = {
        "position_id": str(_POSITION_ID),
        "quantity": 2,
        "materials": {
            "profile_cuts": [{"a": 1, "qty": 3}, {"b": 2, "qty": 2}],
            "glasses": [{"g": 1}],
        },
    }

    def fake_one(sql_text: str, params: list, code: str = "not_found") -> dict:
        lowered = " ".join(sql_text.lower().split())
        if "for update" in lowered:
            return {
                "id": str(order_id),
                "order_code": "OT-1",
                "status": "IN_PROGRESS",
                "payload_json": payload,
            }
        raise AssertionError(f"unexpected one(): {lowered}")

    def fake_rows(sql_text: str, params: list) -> list:
        lowered = " ".join(sql_text.lower().split())
        if "insert into public.production_step_events" in lowered:
            events.append((lowered, list(params)))
        return [{"id": "ok"}]

    monkeypatch.setattr("production.service.one", fake_one)
    monkeypatch.setattr("production.service.rows", fake_rows)
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ):
        output = service.generate_packing_manifest(
            org_id=org_id, order_id=order_id, actor_id=actor_id
        )
    units = output["packing"]["units"]
    assert [u["unit_index"] for u in units] == [1, 2]
    assert units[0]["label_code"] == "OT-1-U01"
    # grouped rows count their qty, not one per row
    assert units[0]["profiles"] == 5 and units[0]["glasses"] == 1
    assert units[0]["panels"] == 0 and units[0]["hardware"] == 0
    assert "'wo_packed'" in events[0][0]


def test_dispatch_requires_completed_and_is_idempotent(monkeypatch) -> None:
    org_id, order_id = uuid4(), uuid4()
    updates: list[list] = []
    statuses = iter(["IN_PROGRESS"])

    def fake_one(sql_text: str, params: list, code: str = "not_found") -> dict:
        return {
            "id": str(order_id),
            "order_code": "OT-1",
            "status": next(statuses, "IN_PROGRESS"),
            "payload_json": {},
        }

    monkeypatch.setattr("production.service.one", fake_one)
    monkeypatch.setattr("production.service.rows", lambda *_a, **_k: [{"id": "ok"}])
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ), pytest.raises(DocumentaryError, match="dispatch_requires_completed"):
        service.dispatch_work_order(org_id=org_id, order_id=order_id, actor_id=uuid4())

    # Completed path updates status and emits the event; replay returns detail.
    captured_status: dict[str, dict] = {"row": {"status": "COMPLETED"}}
    project_id = uuid4()
    note_calls: list[dict] = []

    def fake_one_completed(sql_text: str, params: list, code: str = "not_found") -> dict:
        return {
            "id": str(order_id),
            "order_code": "OT-1",
            "status": captured_status["row"]["status"],
            "payload_json": {},
            "project_id": str(project_id),
        }

    def fake_rows_dispatch(sql_text: str, params: list) -> list:
        lowered = " ".join(sql_text.lower().split())
        if "update public.orders set status" in lowered:
            captured_status["row"]["status"] = "DISPATCHED"
        if "insert into public.production_step_events" in lowered:
            updates.append((lowered, list(params)))
        return [{"id": "ok"}]

    def fake_issue(**kwargs):
        note_calls.append(kwargs)
        return {"note_code": "GD-0001"}

    monkeypatch.setattr("production.service.one", fake_one_completed)
    monkeypatch.setattr("production.service.rows", fake_rows_dispatch)
    monkeypatch.setattr("production.service.issue_dispatch_note", fake_issue)
    monkeypatch.setattr(
        "production.service.project_row", lambda *a, **k: {"code": "P-1"}
    )
    monkeypatch.setattr(
        "production.service.get_work_order",
        lambda **kw: {"order": {"status": captured_status["row"]["status"]}},
    )
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ):
        service.dispatch_work_order(
            org_id=org_id, order_id=order_id, actor_id=uuid4(), note="Camión 12"
        )
        assert captured_status["row"]["status"] == "DISPATCHED"
        out2 = service.dispatch_work_order(org_id=org_id, order_id=order_id, actor_id=uuid4())
    assert "'wo_dispatched'" in updates[0][0]
    assert len(note_calls) == 1
    assert str(note_calls[0]["order"]["project_id"]) == str(project_id)
    event_payload = json.loads(updates[0][1][3])
    assert event_payload["dispatch_note"] == "GD-0001"
    assert out2["order"]["status"] == "DISPATCHED"


def test_remake_code_embeds_id_fragment_for_long_sources(monkeypatch) -> None:
    org_id, order_id = uuid4(), uuid4()
    source_code = "OT-" + "A" * 47  # exactly 50 chars
    captured: list[list] = []

    def fake_one(sql_text: str, params: list, code: str = "not_found") -> dict:
        lowered = " ".join(sql_text.lower().split())
        if "for update" in lowered:
            return {
                "id": str(order_id),
                "order_code": source_code,
                "status": "HOLD",
                "project_id": str(uuid4()),
                "project_version_id": str(uuid4()),
                "payload_json": {"position_id": str(_POSITION_ID)},
            }
        if "count(*)" in lowered:
            return {"n": 0}
        if "insert into public.orders" in lowered:
            captured.append(list(params))
            return {"id": str(uuid4()), "order_code": params[2]}
        raise AssertionError(f"unexpected one(): {lowered}")

    monkeypatch.setattr("production.service.one", fake_one)
    monkeypatch.setattr("production.service.rows", lambda *_a, **_k: [])
    monkeypatch.setattr("production.service.get_work_order", lambda **kw: {"id": "x"})
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ):
        service.create_remake(org_id=org_id, order_id=order_id, actor_id=uuid4())
    code = captured[0][2]
    assert len(code) <= 50
    assert code.endswith("-RM-01")
    marker = str(order_id).replace("-", "").upper()
    assert marker in code
    # distinct sources keep distinct codes even with identical prefixes
    other_id = uuid4()
    other_marker = str(other_id).replace("-", "").upper()
    assert code != f"{source_code[:50-len('-RM-01')-33]}-{other_marker}-RM-01"


def test_reinforcement_angles_flow_into_bars_csv() -> None:
    # The sealed manufacturing facts are the only authority for steel end
    # angles: PVC mitred 45/45 -> square-cut steel 90/90.
    snapshot = {
        "manufacturing": [
            {
                "position_id": "pos-1",
                "members": [
                    {
                        "member_id": "m1",
                        "identity": {"role": "FRAME"},
                        "bay_id": "b1",
                        "leaf_id": None,
                        "workshop_sku": "MARCO-60",
                    }
                ],
                "reinforcements": [
                    {
                        "parent_member_id": "m1",
                        "workshop_sku": "ACERO-35",
                        "cut_length_mm": "880.00",
                        "angle_left": "90.0",
                        "angle_right": "90.0",
                    }
                ],
            }
        ]
    }
    angle_map = service._reinforcement_angle_map(snapshot, "pos-1")
    assert angle_map == {("ACERO-35", "880.00", "FRAME", "b1", None): ("90.0", "90.0")}

    # Conflicting facts on the same key mark it ambiguous (None).
    snapshot["manufacturing"][0]["reinforcements"].append(
        {
            "parent_member_id": "m1",
            "workshop_sku": "ACERO-35",
            "cut_length_mm": "880.00",
            "angle_left": "45.0",
            "angle_right": "45.0",
        }
    )
    assert service._reinforcement_angle_map(snapshot, "pos-1")[
        ("ACERO-35", "880.00", "FRAME", "b1", None)
    ] is None


def test_bars_csv_rejects_reinforcement_without_angles() -> None:
    optimization = {
        "bars": {
            "workshop_cut_plan": [
                {
                    "bar_index": 1,
                    "commercial_sku": "ACERO-35",
                    "stock_length_mm": "6500",
                    "cuts": [
                        {
                            "piece_id": "R-01",
                            "source_kind": "REINFORCEMENT",
                            "length_mm": "880",
                            "sequence": 1,
                        }
                    ],
                }
            ]
        }
    }
    with pytest.raises(DocumentaryError, match="cnc_incomplete_cut_angles"):
        service._cnc_bars_csv(optimization)



def test_packing_labels_keep_suffix_on_long_order_code(monkeypatch) -> None:
    org_id, order_id = uuid4(), uuid4()
    long_code = "OT-" + "B" * 47
    monkeypatch.setattr(
        "production.service.one",
        lambda *_a, **_k: {
            "id": str(order_id),
            "order_code": long_code,
            "status": "IN_PROGRESS",
            "payload_json": {"quantity": 2, "materials": {}},
        },
    )
    monkeypatch.setattr("production.service.rows", lambda *_a, **_k: [{"id": "ok"}])
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ):
        output = service.generate_packing_manifest(
            org_id=org_id, order_id=order_id, actor_id=uuid4()
        )
    labels = [u["label_code"] for u in output["packing"]["units"]]
    assert labels[0].endswith("-U01") and labels[1].endswith("-U02")
    assert len(set(labels)) == 2 and all(len(label) <= 50 for label in labels)


def test_remake_drops_source_packing(monkeypatch) -> None:
    org_id, order_id = uuid4(), uuid4()
    captured: list[list] = []

    def fake_one(sql_text: str, params: list, code: str = "not_found") -> dict:
        lowered = " ".join(sql_text.lower().split())
        if "for update" in lowered:
            return {
                "id": str(order_id),
                "order_code": "OT-1",
                "status": "HOLD",
                "project_id": str(uuid4()),
                "project_version_id": str(uuid4()),
                "payload_json": {
                    "position_id": str(_POSITION_ID),
                    "packing": {"units": [{"label_code": "OT-1-U01"}]},
                },
            }
        if "count(*)" in lowered:
            return {"n": 0}
        if "insert into public.orders" in lowered:
            captured.append(list(params))
            return {"id": str(uuid4()), "order_code": params[2]}
        raise AssertionError(f"unexpected one(): {lowered}")

    monkeypatch.setattr("production.service.one", fake_one)
    monkeypatch.setattr("production.service.rows", lambda *_a, **_k: [{"id": "ok"}])
    monkeypatch.setattr("production.service.get_work_order", lambda **kw: {"id": "x"})
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ):
        service.create_remake(org_id=org_id, order_id=order_id, actor_id=uuid4())
    assert "packing" not in json.loads(captured[0][3])



def test_packing_labels_render_qr_per_unit(monkeypatch) -> None:
    org_id, order_id = uuid4(), uuid4()
    order = {
        "id": order_id,
        "order_code": "OT-LBL-1",
        "status": "COMPLETED",
        "payload_json": json.dumps(
            {
                "packing": {
                    "units": [
                        {
                            "unit_index": 1,
                            "label_code": "OT-LBL-1-U01",
                            "profiles": 6,
                            "reinforcements": 4,
                            "glasses": 2,
                            "panels": 0,
                            "hardware": 8,
                        }
                    ]
                }
            }
        ),
    }
    monkeypatch.setattr(service, "one", lambda *a, **k: order)
    monkeypatch.setattr(service, "documentary_backend", _atomic)
    monkeypatch.setattr(service.transaction, "atomic", _atomic)
    out = service.packing_labels(org_id=org_id, order_id=order_id)

    assert len(out["labels"]) == 1
    label = out["labels"][0]
    assert label["pieces"] == 20
    assert label["qr_payload"] == "DEKOPEN|OT-LBL-1|OT-LBL-1-U01|20"
    assert label["qr_svg"].startswith("<svg") and "path" in label["qr_svg"]


def test_packing_labels_require_manifest(monkeypatch) -> None:
    order = {
        "id": uuid4(),
        "order_code": "OT-LBL-2",
        "status": "IN_PROGRESS",
        "payload_json": json.dumps({}),
    }
    monkeypatch.setattr(service, "one", lambda *a, **k: order)
    monkeypatch.setattr(service, "documentary_backend", _atomic)
    monkeypatch.setattr(service.transaction, "atomic", _atomic)
    with pytest.raises(DocumentaryError, match="packing_required"):
        service.packing_labels(org_id=uuid4(), order_id=uuid4())


def test_installation_requires_dispatched_and_is_idempotent(monkeypatch) -> None:
    org_id, order_id = uuid4(), uuid4()
    statuses = iter(["IN_PROGRESS", "DISPATCHED", "INSTALLED"])
    captured: dict[str, str] = {}
    events: list[tuple[str, list]] = []

    def fake_one(sql_text: str, params: list, code: str = "not_found") -> dict:
        return {
            "id": str(order_id),
            "order_code": "OT-1",
            "status": captured.get("status") or next(statuses),
            "payload_json": {},
        }

    def fake_rows(sql_text: str, params: list) -> list:
        lowered = " ".join(sql_text.lower().split())
        if "from public.deliveries" in lowered:
            return []
        if "update public.orders set status" in lowered:
            captured["status"] = "INSTALLED"
        if "insert into public.production_step_events" in lowered:
            events.append((lowered, list(params)))
        return [{"id": "ok"}]

    monkeypatch.setattr("production.service.one", fake_one)
    monkeypatch.setattr("production.service.rows", fake_rows)
    monkeypatch.setattr(
        "production.service.get_work_order",
        lambda **kw: {"order": {"status": captured.get("status", "?")}},
    )
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ):
        with pytest.raises(DocumentaryError, match="installation_requires_dispatched"):
            service.confirm_installation(
                org_id=org_id, order_id=order_id, actor_id=uuid4()
            )
        service.confirm_installation(
            org_id=org_id, order_id=order_id, actor_id=uuid4(), note="Obra Norte"
        )
        # replay on INSTALLED returns the order without writing again
        out = service.confirm_installation(
            org_id=org_id, order_id=order_id, actor_id=uuid4()
        )
    assert "'wo_installed'" in events[0][0]
    assert len(events) == 1
    assert out["order"]["status"] == "INSTALLED"



def test_dispatched_order_rejects_mutation_actions(monkeypatch) -> None:
    org_id, order_id = uuid4(), uuid4()
    order = {
        "id": str(order_id),
        "order_code": "OT-1",
        "status": "DISPATCHED",
        "payload_json": {"optimization": {"bars": {"workshop_cut_plan": []}}},
    }
    monkeypatch.setattr("production.service.one", lambda *_a, **_k: order)
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ):
        with pytest.raises(DocumentaryError, match="work_order_dispatched"):
            service.export_cnc_files(
                org_id=org_id, order_id=order_id, actor_id=uuid4()
            )
        with pytest.raises(DocumentaryError, match="work_order_dispatched"):
            service.optimize_work_order(
                org_id=org_id, order_id=order_id, actor_id=uuid4(), color="BLANCO"
            )


def test_delivery_schedule_upserts_and_records_event(monkeypatch) -> None:
    org_id, order_id = uuid4(), uuid4()
    events: list[tuple[str, list]] = []
    delivery_row = {
        "id": uuid4(), "org_id": org_id, "order_id": order_id,
        "order_code": "OT-1", "scheduled_date": "2026-09-25",
        "time_window": "PM", "address": "Av. Norte 100",
        "contact_name": None, "contact_phone": None,
        "installer_name": "Cuadrilla 2", "notes": None,
        "status": "SCHEDULED", "scheduled_by": uuid4(),
        "created_at": __import__("datetime").datetime(2026, 9, 23),
        "updated_at": __import__("datetime").datetime(2026, 9, 23),
    }

    def fake_one(sql_text: str, params: list, code: str = "not_found") -> dict:
        lowered = " ".join(sql_text.lower().split())
        if "insert into public.deliveries" in lowered:
            return dict(delivery_row)
        return {"id": str(order_id), "order_code": "OT-1", "status": "COMPLETED"}

    def fake_rows(sql_text: str, params: list) -> list:
        lowered = " ".join(sql_text.lower().split())
        if "left join public.deliveries d" in lowered:
            return [dict(delivery_row)]
        if "from public.deliveries" in lowered:
            return []
        if "insert into public.production_step_events" in lowered:
            events.append((lowered, list(params)))
        return [{"id": "ok"}]

    monkeypatch.setattr("production.service.one", fake_one)
    monkeypatch.setattr("production.service.rows", fake_rows)
    monkeypatch.setattr("production.confirmations.rows", lambda *_a, **_k: [])
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ):
        out = service.schedule_delivery(
            org_id=org_id, order_id=order_id, actor_id=uuid4(),
            scheduled_date="2026-09-25", time_window="pm",
            address="  Av. Norte 100 ", installer_name="Cuadrilla 2",
        )
    delivery = out["delivery"]
    assert delivery["status"] == "SCHEDULED"
    assert delivery["time_window"] == "PM"
    assert "wo_delivery_scheduled" in events[0][0]


def test_delivery_schedule_replay_adds_no_duplicate_event(monkeypatch) -> None:
    org_id, order_id = uuid4(), uuid4()
    events: list[tuple[str, list]] = []
    stored = {
        "id": uuid4(), "org_id": org_id, "order_id": order_id,
        "order_code": "OT-1", "scheduled_date": date(2026, 9, 25),
        "time_window": "PM", "address": "Av. Norte 100",
        "contact_name": None, "contact_phone": None,
        "installer_name": "Cuadrilla 2", "notes": None,
        "status": "SCHEDULED", "scheduled_by": uuid4(),
        "created_at": datetime(2026, 9, 23), "updated_at": datetime(2026, 9, 23),
    }

    def fake_rows(sql_text: str, params: list) -> list:
        lowered = " ".join(sql_text.lower().split())
        if "left join public.deliveries d" in lowered or "from public.deliveries" in lowered:
            return [dict(stored)]
        if "insert into public.production_step_events" in lowered:
            events.append((lowered, list(params)))
        return [{"id": "ok"}]

    monkeypatch.setattr(
        "production.service.one",
        lambda *_a, **_k: {"id": str(order_id), "order_code": "OT-1", "status": "DISPATCHED"},
    )
    monkeypatch.setattr("production.service.rows", fake_rows)
    monkeypatch.setattr("production.confirmations.rows", lambda *_a, **_k: [])
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ):
        out = service.schedule_delivery(
            org_id=org_id, order_id=order_id, actor_id=uuid4(),
            scheduled_date="2026-09-25", time_window="PM",
            address="Av. Norte 100", installer_name="Cuadrilla 2",
        )
    assert events == []
    assert out["delivery"]["status"] == "SCHEDULED"


def test_installation_requires_delivered_delivery(monkeypatch) -> None:
    org_id, order_id = uuid4(), uuid4()
    monkeypatch.setattr(
        "production.service.one",
        lambda *_a, **_k: {
            "id": str(order_id), "order_code": "OT-1",
            "status": "DISPATCHED", "payload_json": {},
        },
    )
    monkeypatch.setattr(
        "production.service.rows",
        lambda *_a, **_k: [{"status": "ON_ROUTE"}],
    )
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ):
        with pytest.raises(DocumentaryError, match="installation_requires_delivered"):
            service.confirm_installation(org_id=org_id, order_id=order_id, actor_id=uuid4())


def test_delivery_transition_rejected_after_installation(monkeypatch) -> None:
    org_id, order_id = uuid4(), uuid4()
    monkeypatch.setattr(
        "production.service.one",
        lambda *_a, **_k: {"id": str(order_id), "order_code": "OT-1", "status": "INSTALLED"},
    )
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ):
        with pytest.raises(DocumentaryError, match="order_already_installed"):
            service.transition_delivery(
                org_id=org_id, order_id=order_id, actor_id=uuid4(), to_status="DELIVERED"
            )


def test_get_delivery_rejects_unknown_order(monkeypatch) -> None:
    monkeypatch.setattr("production.service.rows", lambda *_a, **_k: [])
    with patch("production.service.documentary_backend", side_effect=_atomic):
        with pytest.raises(DocumentaryError, match="work_order_not_found"):
            service.get_delivery(org_id=uuid4(), order_id=uuid4())


def test_delivery_schedule_guards_order_state_and_inputs(monkeypatch) -> None:
    org_id, order_id = uuid4(), uuid4()
    monkeypatch.setattr(
        "production.service.one",
        lambda *_a, **_k: {"id": str(order_id), "order_code": "OT-1", "status": "RELEASED"},
    )
    monkeypatch.setattr("production.service.rows", lambda *_a, **_k: [])
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ):
        with pytest.raises(DocumentaryError, match="delivery_requires_completed"):
            service.schedule_delivery(
                org_id=org_id, order_id=order_id, actor_id=uuid4(),
                scheduled_date="2026-09-25", time_window="AM", address="X 1",
            )
        with pytest.raises(DocumentaryError, match="delivery_window_invalid"):
            service.schedule_delivery(
                org_id=org_id, order_id=order_id, actor_id=uuid4(),
                scheduled_date="2026-09-25", time_window="NOCHE", address="X 1",
            )
        with pytest.raises(DocumentaryError, match="delivery_address_required"):
            service.schedule_delivery(
                org_id=org_id, order_id=order_id, actor_id=uuid4(),
                scheduled_date="2026-09-25", time_window="AM", address="  ",
            )
        with pytest.raises(DocumentaryError, match="delivery_date_invalid"):
            service.schedule_delivery(
                org_id=org_id, order_id=order_id, actor_id=uuid4(),
                scheduled_date="ayer", time_window="AM", address="X 1",
            )


def test_delivery_transition_requires_dispatched_order(monkeypatch) -> None:
    """ON_ROUTE needs the order DISPATCHED; DELIVERED needs ON_ROUTE first."""
    org_id, order_id = uuid4(), uuid4()
    order = {"id": str(order_id), "order_code": "OT-1", "status": "COMPLETED"}
    delivery = {"id": uuid4(), "status": "SCHEDULED"}

    monkeypatch.setattr(
        "production.service.one",
        lambda sql_text, params, code="nf": order if "orders" in sql_text else dict(delivery),
    )
    monkeypatch.setattr("production.service.rows", lambda *_a, **_k: [])
    monkeypatch.setattr(
        "production.service.get_delivery", lambda **kw: {"delivery": {"status": delivery["status"]}}
    )
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ):
        with pytest.raises(DocumentaryError, match="delivery_requires_dispatched"):
            service.transition_delivery(
                org_id=org_id, order_id=order_id, actor_id=uuid4(), to_status="ON_ROUTE"
            )
        with pytest.raises(DocumentaryError, match="delivery_transition_invalid"):
            service.transition_delivery(
                org_id=org_id, order_id=order_id, actor_id=uuid4(), to_status="DELIVERED"
            )
        with pytest.raises(DocumentaryError, match="delivery_transition_invalid"):
            service.transition_delivery(
                org_id=org_id, order_id=order_id, actor_id=uuid4(), to_status="SCHEDULED"
            )


def test_delivery_transition_delivers_and_replays(monkeypatch) -> None:
    org_id, order_id = uuid4(), uuid4()
    order = {"id": str(order_id), "order_code": "OT-1", "status": "DISPATCHED"}
    delivery = {"id": uuid4(), "status": "ON_ROUTE"}
    events: list[tuple[str, list]] = []

    def fake_rows(sql_text: str, params: list) -> list:
        lowered = " ".join(sql_text.lower().split())
        if "update public.deliveries set status" in lowered:
            delivery["status"] = params[0]
        if "insert into public.production_step_events" in lowered:
            events.append((lowered, list(params)))
        return [{"id": "ok"}]

    monkeypatch.setattr(
        "production.service.one",
        lambda sql_text, params, code="nf": order if "orders" in sql_text else dict(delivery),
    )
    monkeypatch.setattr("production.service.rows", fake_rows)
    monkeypatch.setattr(
        "production.service.get_delivery", lambda **kw: {"delivery": {"status": delivery["status"]}}
    )
    with patch("production.service.transaction.atomic", side_effect=_atomic), patch(
        "production.service.documentary_backend", side_effect=_atomic
    ):
        out = service.transition_delivery(
            org_id=org_id, order_id=order_id, actor_id=uuid4(), to_status="DELIVERED"
        )
        replay = service.transition_delivery(
            org_id=org_id, order_id=order_id, actor_id=uuid4(), to_status="DELIVERED"
        )
    assert out["delivery"]["status"] == "DELIVERED"
    assert replay["delivery"]["status"] == "DELIVERED"
    assert len(events) == 1 and events[0][1][2] == "WO_DELIVERY_DELIVERED"
