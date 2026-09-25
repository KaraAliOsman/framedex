"""Revision comparison: positions keyed by index, commercial fields diffed."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from documents import service
from documents.repository import DocumentaryError


@contextmanager
def _no_backend():
    yield


def _version(code: str, snapshot: dict[str, object]) -> dict[str, object]:
    return {
        "id": uuid4(),
        "revision_code": code,
        "snapshot_json": snapshot,
        "snapshot_sha256": None,
        "emitted_at": datetime(2026, 9, 20, tzinfo=timezone.utc),
    }


def _position(index: int, **overrides) -> dict[str, object]:
    position = {
        "id": str(uuid4()),
        "position_index": index,
        "location_tag": "DORMITORIO",
        "typology": "OPENING_WINDOW",
        "system_id": "WDS-76",
        "width_mm": "1200.00",
        "height_mm": "1500.00",
        "quantity": 1,
        "color_interior": "WHITE",
        "color_exterior": "WHITE",
        "price_net": "250000",
        "discount_pct": "0",
        "parametric_tree": {"id": "B1", "type": "BAY", "children": []},
        "calculation_hash": "a" * 64,
    }
    position.update(overrides)
    return position


def _snapshot(
    revision: str, positions: list[dict[str, object]], gross: str
) -> dict[str, object]:
    return {
        "revision": revision,
        "project": {
            "total_price_net": gross,
            "total_price_tax": "0",
            "total_price_gross": gross,
        },
        "positions": positions,
    }


def _patch_rows(monkeypatch: pytest.MonkeyPatch, versions: list[dict[str, object]]) -> None:
    monkeypatch.setattr(service, "documentary_backend", _no_backend)
    monkeypatch.setattr(
        service,
        "one",
        lambda *args, **kwargs: {"id": uuid4(), "code": "P-001", "name": "Casa"},
    )
    monkeypatch.setattr(service, "rows", lambda *args, **kwargs: versions)


def _compare(monkeypatch, base_positions, head_positions, base_gross="500000", head_gross="600000"):
    _patch_rows(
        monkeypatch,
        [
            _version("REV-A", _snapshot("REV-A", base_positions, base_gross)),
            _version("REV-B", _snapshot("REV-B", head_positions, head_gross)),
        ],
    )
    return service.compare_versions(
        org_id=uuid4(), project_id=uuid4(), base_code="REV-A", head_code="REV-B"
    )


def test_compare_reports_added_removed_changed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = _compare(
        monkeypatch,
        [_position(1), _position(2)],
        [_position(1, width_mm="1400.00"), _position(3, location_tag="LIVING")],
    )
    assert output["summary"] == {
        "added": 1,
        "removed": 1,
        "changed": 1,
        "unchanged": 0,
        "price_gross_delta": "100000",
    }
    changes = {entry["position_index"]: entry for entry in output["positions"]}
    assert changes[1]["change"] == "CHANGED"
    assert changes[2]["change"] == "REMOVED"
    assert changes[3]["change"] == "ADDED"
    # The width diff names the field and both values — the estimator reads
    # what changed, not a hash.
    assert {
        "field": "width_mm",
        "before": "1200.00",
        "after": "1400.00",
    } in changes[1]["changes"]
    # calculation_hash is an internal signal → surfaced only as a spec flag
    # when the technical tree actually changed, never raw.
    assert "calculation_hash" not in changes[1]["after"]
    assert {"field": "spec", "before": "", "after": ""} not in changes[1]["changes"]
    assert changes[3]["after"]["parametric_tree"]["type"] == "BAY"
    assert output["base"]["integrity"] is None
    assert output["head"]["total_price_gross"] == "600000"


def test_compare_unchanged_positions_stay_out_of_the_diff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = _compare(monkeypatch, [_position(1)], [_position(1)], "250000", "250000")
    assert output["positions"] == []
    assert output["summary"]["unchanged"] == 1
    assert output["summary"]["price_gross_delta"] == "0"


def test_compare_rejects_unknown_revision(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_rows(monkeypatch, [_version("REV-A", _snapshot("REV-A", [], "0"))])
    with pytest.raises(DocumentaryError) as missing:
        service.compare_versions(
            org_id=uuid4(), project_id=uuid4(), base_code="REV-A", head_code="REV-Z"
        )
    assert missing.value.code == "version_not_found"


def test_compare_flags_spec_drift_without_field_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = _compare(
        monkeypatch,
        [_position(1)],
        [_position(1, calculation_hash="b" * 64)],
        "250000",
        "250000",
    )
    assert output["positions"][0]["change"] == "CHANGED"
    assert output["positions"][0]["changes"] == [
        {"field": "spec", "before": "", "after": ""}
    ]
