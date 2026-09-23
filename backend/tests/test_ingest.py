"""Document ingestion: parser, service contract, and extraction job paths."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from rest_framework.exceptions import APIException

from ingest import service
from ingest.extract import kind_for
from ingest.parser import (
    candidates_from_text,
    normalize_opening,
    parse_line,
)


def test_parse_line_finds_label_dimensions_and_opening():
    candidate = parse_line("V-01 oscilobatiente 1200x1000 2")
    assert candidate is not None
    assert candidate["label"] == "V-01"
    assert candidate["width_mm"] == "1200"
    assert candidate["height_mm"] == "1000"
    assert candidate["quantity"] == 2
    assert candidate["opening_type"] == "TILT_TURN_LEFT"
    assert candidate["confidence"] == "HIGH"
    assert candidate["warnings"] == []


def test_parse_line_requires_dimensions():
    assert parse_line("ventana sin medidas") is None
    assert parse_line("fijo 0x1000") is None


def test_parse_line_missing_hint_flags_review():
    candidate = parse_line("1500x1200")
    assert candidate is not None
    assert candidate["confidence"] == "REVIEW_REQUIRED"
    assert "import.candidate_no_label" in candidate["warnings"]
    assert "import.candidate_no_opening" in candidate["warnings"]


def test_parse_line_label_digits_do_not_inflate_quantity():
    candidate = parse_line("V-10 fijo 1200x1000")
    assert candidate is not None
    assert candidate["label"] == "V-10"
    assert candidate["quantity"] == 1
    candidate = parse_line("V-10 fijo 1200x1000 3 unidades")
    assert candidate["quantity"] == 3


def test_candidates_from_text_keys_rows():
    candidates = candidates_from_text("A-1 fijo 1000x1000\nA-2 corredera 1500x1200")
    assert [c["key"] for c in candidates] == ["r0", "r1"]
    assert candidates[1]["opening_type"] == "SLIDING_2L"


def test_normalize_opening_whitelists():
    assert normalize_opening("FIXED") == "FIXED"
    assert normalize_opening("banana") is None
    assert normalize_opening(None) is None


def test_kind_for_extensions():
    assert kind_for("plano.PDF") == "PDF"
    assert kind_for("lista.xlsx") == "XLSX"
    assert kind_for("foto.webp") == "IMAGE"
    assert kind_for("nota.txt") is None


def _import_row(**overrides):
    row = {
        "id": uuid4(),
        "org_id": uuid4(),
        "project_id": uuid4(),
        "file_name": "lista.pdf",
        "kind": "PDF",
        "storage_path": "imports/o/p/i/lista.pdf",
        "status": "REVIEW_READY",
        "candidates": [
            {
                "key": "r0",
                "label": "V-01",
                "width_mm": "1200",
                "height_mm": "1000",
                "quantity": 1,
                "opening_type": "TILT_TURN_LEFT",
                "confidence": "HIGH",
                "warnings": [],
            }
        ],
        "warnings": [],
        "result": [],
        "error_code": None,
        "audit_id": None,
        "created_by": uuid4(),
        "created_at": "2026-09-23T00:00:00Z",
        "updated_at": "2026-09-23T00:00:00Z",
    }
    row.update(overrides)
    return row


def _item(**overrides):
    item = {
        "key": "r0",
        "label": "V-01",
        "width_mm": "1200.00",
        "height_mm": "1000.00",
        "quantity": 1,
        "opening_type": "TILT_TURN_LEFT",
        "system_id": str(uuid4()),
        "color": "WHITE",
        "glass_thickness_mm": "20.00",
        "glass_spec": "4-12-4",
    }
    item.update(overrides)
    return item


def test_confirm_creates_positions_and_stores_result(monkeypatch):
    row = _import_row()
    saved = []
    updates = []

    monkeypatch.setattr(service.projects_service, "project_row", lambda *a, **k: {"id": "p"})
    monkeypatch.setattr(service, "rows", lambda sql, params=None: [])
    monkeypatch.setattr(
        service.projects_service,
        "save_position",
        lambda org, proj, data: saved.append(data) or {"id": uuid4()},
    )

    monkeypatch.setattr(service, "documentary_backend", _backend)
    monkeypatch.setattr(
        service,
        "rows",
        lambda sql, params=None: (
            updates.append(sql) or [row | {"status": "CONFIRMED", "result": []}]
            if "UPDATE public.document_imports" in sql
            else [row]
            if "FROM public.document_imports" in sql
            else []
        ),
    )
    out = service.confirm_import(
        org_id=row["org_id"],
        project_id=row["project_id"],
        import_id=row["id"],
        items=[_item()],
    )
    assert len(out["created"]) == 1
    assert saved[0]["design"]["parametric_tree"]["opening_type"] == "TILT_TURN_LEFT"
    # The engine's Decimal-purity contract: JSON ints must become Decimal here.
    assert saved[0]["design"]["nominal_width_mm"] == Decimal("1200.00")
    assert any("SET status='CONFIRMED'" in sql for sql in updates)


def test_confirm_replays_confirmed_import(monkeypatch):
    result = [{"key": "r0", "position_id": str(uuid4())}]
    row = _import_row(status="CONFIRMED", result=result)
    monkeypatch.setattr(service, "rows", lambda sql, params=None: [row])
    monkeypatch.setattr(service, "documentary_backend", _backend)
    out = service.confirm_import(
        org_id=row["org_id"],
        project_id=row["project_id"],
        import_id=row["id"],
        items=[_item()],
    )
    assert out["created"] == result
    assert out["errors"] == []


def test_confirm_refuses_in_flight_import(monkeypatch):
    row = _import_row(status="EXTRACTING")
    monkeypatch.setattr(service, "rows", lambda sql, params=None: [row])
    monkeypatch.setattr(service, "documentary_backend", _backend)
    with pytest.raises(APIException) as failure:
        service.confirm_import(
            org_id=row["org_id"],
            project_id=row["project_id"],
            import_id=row["id"],
            items=[_item()],
        )
    assert failure.value.contract_code == "import_not_review_ready"


def test_confirm_collects_item_errors_without_blocking(monkeypatch):
    row = _import_row()
    monkeypatch.setattr(service.projects_service, "project_row", lambda *a, **k: {"id": "p"})

    def _rows(sql, params=None):
        if "UPDATE public.document_imports" in sql:
            return [row | {"result": params[0]}]
        if "FROM public.document_imports" in sql:
            return [row]
        return []

    monkeypatch.setattr(service, "rows", _rows)
    monkeypatch.setattr(service, "documentary_backend", _backend)
    monkeypatch.setattr(
        service.projects_service,
        "save_position",
        lambda *a: (_ for _ in ()).throw(Exception("boom")),
    )
    out = service.confirm_import(
        org_id=row["org_id"],
        project_id=row["project_id"],
        import_id=row["id"],
        items=[_item(key="r0"), _item(key="ghost")],
    )
    assert out["created"] == []
    assert {e["key"] for e in out["errors"]} == {"r0", "ghost"}
    assert out["errors"][1]["code"] == "import_item_unknown"


def test_confirm_partial_failure_stays_retryable_then_seals(monkeypatch):
    row = _import_row(
        candidates=[
            {"key": "r0", "label": "V-01", "width_mm": "1200", "height_mm": "1000",
             "quantity": 1, "opening_type": "FIXED", "confidence": "HIGH", "warnings": []},
            {"key": "r1", "label": "V-02", "width_mm": "800", "height_mm": "600",
             "quantity": 1, "opening_type": "FIXED", "confidence": "HIGH", "warnings": []},
        ]
    )
    stored = {"result": []}

    def _rows(sql, params=None):
        if "UPDATE public.document_imports" in sql:
            stored["result"] = params[0]
            if "SET status='CONFIRMED'" in sql:
                return [row | {"status": "CONFIRMED", "result": params[0]}]
            return [row | {"result": params[0]}]
        if "FROM public.document_imports" in sql:
            return [row | {"result": stored["result"]}]
        return []

    monkeypatch.setattr(service, "rows", _rows)
    monkeypatch.setattr(service, "documentary_backend", _backend)
    calls = []

    def _save(org, proj, data):
        calls.append(data["location_tag"])
        if data["location_tag"] == "V-01" and calls.count("V-01") == 1:
            raise Exception("catalog rejected")
        return {"id": uuid4()}

    monkeypatch.setattr(service.projects_service, "save_position", _save)

    first = service.confirm_import(
        org_id=row["org_id"], project_id=row["project_id"],
        import_id=row["id"], items=[_item(key="r0", label="V-01"), _item(key="r1", label="V-02")],
    )
    assert first["import"]["status"] == "REVIEW_READY"
    assert [e["key"] for e in first["errors"]] == ["r0"]
    assert [c["key"] for c in first["created"]] == ["r1"]

    second = service.confirm_import(
        org_id=row["org_id"], project_id=row["project_id"],
        import_id=row["id"], items=[_item(key="r0", label="V-01")],
    )
    assert second["import"]["status"] == "CONFIRMED"
    assert second["errors"] == []
    assert {c["key"] for c in second["created"]} == {"r0", "r1"}
    assert calls == ["V-01", "V-02", "V-01"]


def _backend():
    class _Backend:
        def __enter__(self):
            return None

        def __exit__(self, *a):
            return None

    return _Backend()


@pytest.fixture(autouse=True)
def _no_db(monkeypatch):
    """Service transactions are exercised at SQL level in pgTAP — unit tests
    mock rows/documentary_backend and would hit the no-DB guard on atomic()."""
    monkeypatch.setattr(service, "transaction", _NullAtomic())


class _NullAtomic:
    def atomic(self):
        return _backend()

    def __call__(self, *args, **kwargs):
        return _backend()


class _FakeConnection:
    def cursor(self):
        class _Cursor:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return None

            def execute(self, *a):
                return None

        return _Cursor()


def test_terminal_failure_marks_import_failed(monkeypatch):
    import ingest.handlers as handlers

    calls = []
    monkeypatch.setattr(handlers, "transaction", _NullAtomic())
    monkeypatch.setattr(handlers, "connection", _FakeConnection())
    monkeypatch.setattr(
        "ingest.service.extract_for_import",
        lambda **kw: (_ for _ in ()).throw(RuntimeError("storage down")),
    )
    monkeypatch.setattr(
        "ingest.service.mark_import_failed", lambda **kw: calls.append(kw)
    )

    ctx = type(
        "Ctx",
        (),
        {
            "created_by": uuid4(),
            "org_id": uuid4(),
            "attempt": 3,
            "max_attempts": 3,
            "job_id": uuid4(),
        },
    )()
    with pytest.raises(RuntimeError):
        handlers.extract_document_job(
            {"import_id": str(uuid4())}, ctx, lambda progress: None
        )
    assert calls[0]["code"] == "import_extract_failed"
    assert str(calls[0]["import_id"]) == calls[0]["import_id"]


def test_non_terminal_failure_leaves_import_pending(monkeypatch):
    import ingest.handlers as handlers

    calls = []
    monkeypatch.setattr(handlers, "transaction", _NullAtomic())
    monkeypatch.setattr(handlers, "connection", _FakeConnection())
    monkeypatch.setattr(
        "ingest.service.extract_for_import",
        lambda **kw: (_ for _ in ()).throw(RuntimeError("storage down")),
    )
    monkeypatch.setattr(
        "ingest.service.mark_import_failed", lambda **kw: calls.append(kw)
    )

    ctx = type(
        "Ctx",
        (),
        {
            "created_by": uuid4(),
            "org_id": uuid4(),
            "attempt": 1,
            "max_attempts": 3,
            "job_id": uuid4(),
        },
    )()
    with pytest.raises(RuntimeError):
        handlers.extract_document_job(
            {"import_id": str(uuid4())}, ctx, lambda progress: None
        )
    assert calls == []


def test_extract_deterministic_path_never_calls_provider(monkeypatch):
    row = _import_row(kind="PDF")
    updates = []

    class _Storage:
        def download(self, path):
            return b"%PDF fake bytes"

    monkeypatch.setattr(service, "SupabaseDocumentStorage", lambda: _Storage())
    monkeypatch.setattr(
        service, "extract", lambda kind, content: ("V-01 fijo 1200x1000", None)
    )

    class _Backend:
        def __enter__(self):
            return None

        def __exit__(self, *a):
            return None

    monkeypatch.setattr(service, "documentary_backend", lambda: _Backend())
    monkeypatch.setattr(
        service,
        "rows",
        lambda sql, params=None: (
            updates.append((sql, params)) or [row | {"status": "REVIEW_READY"}]
            if "UPDATE public.document_imports" in sql and "RETURNING" in sql
            else [row]
            if "FROM public.document_imports" in sql
            else []
        ),
    )

    def _boom(**kwargs):
        raise AssertionError("provider must not be called")

    monkeypatch.setattr("ai_gateway.service.invoke", _boom)
    out = service.extract_for_import(
        org_id=row["org_id"], import_id=row["id"], actor_id=uuid4()
    )
    assert out["candidate_count"] == 1
    stored = [p for sql, p in updates if "candidates" in sql][0]
    assert "V-01" in stored[0]


def test_extract_vision_fallback_when_no_text(monkeypatch):
    row = _import_row(kind="IMAGE", storage_path="imports/o/p/i/foto.png")
    seen = []

    class _Storage:
        def download(self, path):
            return b"\x89PNG"

    monkeypatch.setattr(service, "SupabaseDocumentStorage", lambda: _Storage())
    monkeypatch.setattr(service, "extract", lambda kind, content: ("", None))

    class _Backend:
        def __enter__(self):
            return None

        def __exit__(self, *a):
            return None

    monkeypatch.setattr(service, "documentary_backend", lambda: _Backend())
    monkeypatch.setattr(
        service,
        "rows",
        lambda sql, params=None: (
            [row | {"status": "REVIEW_READY"}]
            if "UPDATE public.document_imports" in sql and "RETURNING" in sql
            else [row]
            if "FROM public.document_imports" in sql
            else []
        ),
    )
    monkeypatch.setattr(
        "ai_gateway.service.invoke",
        lambda **kwargs: seen.append(kwargs)
        or {"audit_id": str(uuid4()), "output": "A-1 fijo 800x600"},
    )
    out = service.extract_for_import(
        org_id=row["org_id"], import_id=row["id"], actor_id=uuid4()
    )
    assert seen[0]["capability"] == "vision_ocr"
    assert seen[0]["operation_key"] == f"import:{row['id']}:vision"
    assert out["candidate_count"] == 1
