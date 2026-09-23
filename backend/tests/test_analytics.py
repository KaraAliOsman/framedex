"""Analytics aggregates: org-scoped reads of the live operational tables."""

from contextlib import contextmanager
from unittest.mock import patch
from uuid import uuid4

from analytics import service


@contextmanager
def _atomic():
    yield


class _FakeTs:
    def isoformat(self) -> str:
        return "2026-09-23T00:00:00+00:00"


def test_operational_summary_aggregates_live_tables(monkeypatch) -> None:
    org_id = uuid4()
    seen_params: list[list] = []

    def fake_rows(sql_text: str, params: list) -> list[dict]:
        lowered = " ".join(sql_text.lower().split())
        seen_params.append(list(params))
        if "order_type = 'workshop_ot'" in lowered:
            return [{"status": "INSTALLED", "n": 2}]
        if "order_type <> 'workshop_ot'" in lowered:
            return [{"status": "FULFILLED", "n": 1}]
        if "document_artifacts" in lowered:
            return [{"document_type": "DOC-03", "n": 4}]
        if "limit 10" in lowered:
            return [
                {
                    "event": "WO_INSTALLED",
                    "order_code": "OT-1",
                    "created_at": _FakeTs(),
                }
            ]
        return []

    def fake_one(sql_text: str, params: list, code: str = "not_found") -> dict:
        lowered = " ".join(sql_text.lower().split())
        seen_params.append(list(params))
        if "extract(epoch" in lowered:
            return {"release_to_dispatch_hours": 4.26}
        if "wo_dispatched" in lowered:
            return {"dispatched_30d": 3, "installed_30d": 2, "completed_30d": 2}
        if "inventory_items" in lowered:
            return {"n": 7}
        if "offcut_inventory" in lowered:
            return {"n": 2}
        if "projects" in lowered:
            return {"projects": 5, "positions": 9, "sealed_versions": 3}
        raise AssertionError(f"unexpected one(): {lowered}")

    monkeypatch.setattr("analytics.service.rows", fake_rows)
    monkeypatch.setattr("analytics.service.one", fake_one)
    with patch("analytics.service.transaction.atomic", side_effect=_atomic), patch(
        "analytics.service.documentary_backend", side_effect=_atomic
    ):
        out = service.operational_summary(org_id=org_id)

    assert out["work_orders"] == {"INSTALLED": 2}
    assert out["supplier_orders"] == {"FULFILLED": 1}
    assert out["throughput_30d"]["dispatched_30d"] == 3
    assert out["avg_release_to_dispatch_hours"] == 4.3
    assert out["inventory"] == {"items": 7, "offcuts": 2}
    assert out["documents"] == {"DOC-03": 4}
    assert out["projects"]["sealed_versions"] == 3
    assert out["recent_events"][0]["event"] == "WO_INSTALLED"
    # every aggregate ran org-scoped
    assert seen_params and all(p == [str(org_id)] or p == [str(org_id)] * 3 for p in seen_params)
