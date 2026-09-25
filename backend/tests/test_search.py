"""§7 global search: deterministic grouped results, org-scoped, read-only."""

from __future__ import annotations

from uuid import uuid4

import pytest

from search import service


@pytest.fixture
def fake_rows(monkeypatch):
    calls: list[tuple[str, list]] = []
    responses: list[list[dict]] = []

    def _rows(sql, params=()):
        calls.append((sql, list(params)))
        return responses.pop(0) if responses else []

    monkeypatch.setattr(service, "rows", _rows)
    return calls, responses


def _seed(responses):
    pid, pos, aid = uuid4(), uuid4(), uuid4()
    responses.extend(
        [
            [{"id": pid, "code": "PRJ-1", "name": "Hotel Sur", "client_name": "Inmobiliaria"}],
            [{"id": uuid4(), "name": "Inmobiliaria Sur", "rut": "76.123.456-7"}],
            [
                {
                    "id": pos,
                    "project_id": pid,
                    "location_tag": "D101",
                    "typology": "FIXED",
                    "project_code": "PRJ-1",
                    "project_name": "Hotel Sur",
                }
            ],
            [{"id": aid, "code": "DEMO_60", "name": "Demo 60"}],
            [{"id": aid, "sku": "MRC-100", "name": "Marco", "system_code": "DEMO_60"}],
            [{"id": aid, "sku": "GL-44", "name": "4+4 incoloro", "kind": "GLASS"}],
            [
                {
                    "id": uuid4(),
                    "order_code": "OT-9",
                    "kind": "WORKSHOP_OT",
                    "status": "IN_PROGRESS",
                }
            ],
            [{"id": uuid4(), "invoice_code": "FAC-3", "project_id": pid, "project_code": "PRJ-1"}],
            [{"id": uuid4(), "note_code": "GD-2", "order_code": "OT-9"}],
            [{"id": aid, "sku": "SIL-1", "name": "Silicona", "category": "SUPPLY"}],
        ]
    )
    return pid, pos


def test_short_or_empty_query_returns_nothing(fake_rows):
    calls, _ = fake_rows
    assert service.search(uuid4(), " a ") == {"results": []}
    assert calls == []


def test_every_group_maps_row_to_result(fake_rows):
    calls, responses = fake_rows
    pid, pos = _seed(responses)
    out = service.search(uuid4(), "hotel")
    by_group = {}
    for item in out["results"]:
        by_group.setdefault(item["group"], []).append(item)
    assert by_group["projects"][0]["title"] == "PRJ-1 · Hotel Sur"
    assert by_group["projects"][0]["path"] == f"/projects/{pid}"
    assert by_group["clients"][0]["title"] == "Inmobiliaria Sur"
    assert by_group["positions"][0]["path"] == f"/projects/{pid}/positions/{pos}/edit"
    assert by_group["systems"][0]["title"] == "DEMO_60 · Demo 60"
    assert len(by_group["articles"]) == 2
    assert by_group["orders"][0]["path"] == "/production"
    assert by_group["documents"][0]["title"] == "FAC-3"
    assert by_group["documents"][1]["title"] == "GD-2"
    assert by_group["inventory"][0]["path"] == "/purchasing"


def test_queries_are_org_scoped_and_pattern_safe(fake_rows):
    calls, responses = fake_rows
    org = uuid4()
    _seed(responses)
    service.search(org, "%_;DROP--")
    for sql, params in calls:
        # org binding is a %s parameter in every query — bare "org_id=%s" for
        # tenant-only tables, the canonical visibility rule for catalog ones.
        assert "org_id=%s" in sql or "org_id = %s" in sql
        assert params[0] == str(org)
        assert "POSITION" in sql
        assert all(p == "%_;drop--" for p in params[1:]), params


def test_catalog_queries_use_canonical_visibility(fake_rows):
    """Systems/articles/infills must resolve through the same
    org-or-global-system rule the catalog service exposes — not a bare
    org_id filter that would hide global catalog rows."""
    calls, _ = fake_rows
    service.search(uuid4(), "ma")
    global_aware = [sql for sql, _ in calls if "is_global" in sql]
    assert len(global_aware) == 3
    for sql in global_aware:
        assert "org_id = %s OR" in sql
