"""Catalog ingestion: article parser, service contract, confirm lifecycle."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from rest_framework.exceptions import APIException

from django.db import DatabaseError

from ingest import catalog_service
from ingest.catalog_parser import parse_article_line, parse_catalog_lines
from ingest.serializers import CatalogImportConfirmSerializer


def test_parse_article_line_full_match():
    candidate = parse_article_line(
        "MRC-100 Marco oscilobatiente 78 mm 1.45 kg/m refuerzo AC-55", "r0"
    )
    assert candidate is not None
    assert candidate["sku"] == "MRC-100"
    assert candidate["role"] == "FRAME"
    assert candidate["face_width_mm"] == Decimal("78")
    assert candidate["confidence"] == "HIGH"
    assert candidate["weight_kg_m"] == Decimal("1.45")
    assert candidate["reinforcement_sku"] == "AC-55"


def test_parse_article_line_sash_and_mullion_roles():
    assert parse_article_line("HJA-20 hoja ventana 65mm", "r0")["role"] == "SASH"
    assert parse_article_line("MON-30 montante vertical 40mm", "r0")["role"] == "MULLION_V"
    assert parse_article_line("TRV-40 travesaño horizontal 40mm", "r0")["role"] == "MULLION_H"
    assert parse_article_line("CVD-50 contravidrio 25mm", "r0")["role"] == "GLAZING_BEAD"


def test_parse_article_line_missing_fields_flags_review():
    candidate = parse_article_line("XYZ-9", "r0")
    assert candidate is not None
    assert candidate["confidence"] == "REVIEW_REQUIRED"
    assert "catalog_name_missing" in candidate["warnings"]
    assert "catalog_role_unknown" in candidate["warnings"]
    assert "catalog_face_width_missing" in candidate["warnings"]


def test_parse_article_line_rejects_unusable_sku():
    assert parse_article_line("catalogo general perfiles", "r0") is None
    assert parse_article_line("", "r0") is None


def test_parse_article_line_face_width_bounds():
    assert parse_article_line("ABC-1 marco 400 mm", "r0")[
        "confidence"
    ] == "REVIEW_REQUIRED"
    candidate = parse_article_line("ABC-1 marco 45 mm", "r0")
    assert candidate["face_width_mm"] == Decimal("45")


def test_parse_catalog_lines_dedupes_sku():
    lines = ["MRC-1 marco 50mm", "MRC-1 marco 50mm", "HJA-2 hoja 60mm"]
    candidates = parse_catalog_lines(lines)
    assert [c["sku"] for c in candidates] == ["MRC-1", "HJA-2"]
    assert [c["key"] for c in candidates] == ["c0", "c2"]


def _backend():
    class _Backend:
        def __enter__(self):
            return None

        def __exit__(self, *a):
            return None

    return _Backend()


class _NullAtomic:
    def atomic(self):
        return _backend()

    def __call__(self, *args, **kwargs):
        return _backend()


@pytest.fixture(autouse=True)
def _no_db(monkeypatch):
    monkeypatch.setattr(catalog_service, "transaction", _NullAtomic())


def _import_row(**overrides):
    row = {
        "id": uuid4(),
        "org_id": uuid4(),
        "system_id": None,
        "file_name": "aluprof.pdf",
        "kind": "PDF",
        "storage_path": "catalog-imports/o/i/aluprof.pdf",
        "status": "REVIEW_READY",
        "candidates": [
            {
                "key": "c0",
                "sku": "MRC-100",
                "name": "Marco oscilobatiente",
                "role": "FRAME",
                "face_width_mm": "78",
                "commercial_length_mm": "6000",
                "welding_loss_mm": "6",
                "reinforcement_sku": "AC-55",
                "weight_kg_m": "1.45",
                "steel_weight_kg_m": "1.7",
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
        "key": "c0",
        "sku": "MRC-100",
        "name": "Marco oscilobatiente",
        "role": "FRAME",
        "face_width_mm": "78",
        "commercial_length_mm": "6000",
        "welding_loss_mm": "6",
        "reinforcement_sku": "AC-55",
        "weight_kg_m": "1.45",
        "steel_weight_kg_m": "1.7",
    }
    item.update(overrides)
    return item


def _confirm_patches(monkeypatch, row, system_found=True, insert_return=True):
    article_id = uuid4()
    updates = []
    inserts = []

    def _rows(sql, params=None):
        if "FROM public.catalog_imports" in sql:
            return [row]
        if "FROM public.profile_systems" in sql:
            return (
                [{"id": params[0], "material": "ALUMINIUM"}]
                if system_found
                else []
            )
        if "INSERT INTO public.profile_articles" in sql:
            inserts.append(params)
            return [{"id": article_id}] if insert_return else []
        if "UPDATE public.catalog_imports" in sql:
            updates.append(params)
            return [row]
        return []

    monkeypatch.setattr(catalog_service, "rows", _rows)
    monkeypatch.setattr(catalog_service, "documentary_backend", _backend)
    return updates, inserts, article_id


def test_confirm_inserts_articles_and_seals(monkeypatch):
    row = _import_row()
    system_id = uuid4()
    updates, inserts, article_id = _confirm_patches(monkeypatch, row)
    out = catalog_service.confirm_catalog_import(
        org_id=row["org_id"],
        import_id=row["id"],
        system_id=system_id,
        items=[_item()],
    )
    assert out["created"] == [{"key": "c0", "article_id": str(article_id)}]
    assert out["errors"] == []
    # Org-scoped insert: org_id written on the article row.
    assert inserts[0][1] == str(row["org_id"])
    # Decimal string passed as text — engine purity preserved.
    assert inserts[0][6] == "78"
    # The article inherits the owned system's material, never the PVC default.
    assert inserts[0][5] == "ALUMINIUM"
    # CONFIRMED is inline in the seal SQL; params carry result, system, import.
    assert updates[0][1] == str(system_id)


def test_confirm_rejects_shared_system(monkeypatch):
    row = _import_row()
    _confirm_patches(monkeypatch, row, system_found=False)
    with pytest.raises(APIException) as failure:
        catalog_service.confirm_catalog_import(
            org_id=row["org_id"],
            import_id=row["id"],
            system_id=uuid4(),
            items=[_item()],
        )
    assert failure.value.contract_code == "catalog_system_not_tenant"


def test_confirm_sku_conflict_surfaces_per_key(monkeypatch):
    row = _import_row()
    _confirm_patches(monkeypatch, row, insert_return=False)
    out = catalog_service.confirm_catalog_import(
        org_id=row["org_id"],
        import_id=row["id"],
        system_id=uuid4(),
        items=[_item()],
    )
    assert out["errors"] == [{"key": "c0", "code": "catalog_sku_conflict"}]
    assert out["created"] == []


def test_confirm_rejects_unknown_key(monkeypatch):
    row = _import_row()
    _confirm_patches(monkeypatch, row)
    out = catalog_service.confirm_catalog_import(
        org_id=row["org_id"],
        import_id=row["id"],
        system_id=uuid4(),
        items=[_item(key="nope")],
    )
    assert out["errors"] == [{"key": "nope", "code": "catalog_item_unknown"}]


def test_confirm_replays_confirmed_import(monkeypatch):
    result = [{"key": "c0", "article_id": str(uuid4())}]
    row = _import_row(status="CONFIRMED", result=result)
    monkeypatch.setattr(catalog_service, "rows", lambda sql, params=None: [row])
    monkeypatch.setattr(catalog_service, "documentary_backend", _backend)
    out = catalog_service.confirm_catalog_import(
        org_id=row["org_id"],
        import_id=row["id"],
        system_id=uuid4(),
        items=[_item()],
    )
    assert out["created"] == result
    assert out["errors"] == []


def test_confirm_defaults_apply_to_null_fields(monkeypatch):
    row = _import_row()
    _, inserts, _ = _confirm_patches(monkeypatch, row)
    item = _item(
        commercial_length_mm=None, welding_loss_mm=None,
        weight_kg_m=None, steel_weight_kg_m=None, reinforcement_sku=None,
    )
    catalog_service.confirm_catalog_import(
        org_id=row["org_id"],
        import_id=row["id"],
        system_id=uuid4(),
        items=[item],
    )
    assert inserts[0][7] == str(Decimal("6000"))
    assert inserts[0][8] == str(Decimal("6"))
    assert inserts[0][10] == str(Decimal("1.2"))
    assert inserts[0][11] == str(Decimal("1.7"))


def test_parse_article_line_threshold_role():
    assert parse_article_line("UMB-10 umbral 30mm", "r0")["role"] == "THRESHOLD"
    assert parse_article_line("THR-30 threshold 45mm", "r1")["role"] == "THRESHOLD"


def test_confirm_serializer_rejects_duplicate_keys():
    serializer = CatalogImportConfirmSerializer(
        data={
            "system_id": str(uuid4()),
            "items": [_item(), _item()],
        }
    )
    assert not serializer.is_valid()


def _failing_insert(monkeypatch, row, error):
    updates = []

    def _rows(sql, params=None):
        if "FROM public.catalog_imports" in sql:
            return [row]
        if "FROM public.profile_systems" in sql:
            return [{"id": params[0], "material": "PVC"}]
        if "INSERT INTO public.profile_articles" in sql:
            raise error
        if "UPDATE public.catalog_imports" in sql:
            updates.append(params)
            return [row]
        return []

    monkeypatch.setattr(catalog_service, "rows", _rows)
    monkeypatch.setattr(catalog_service, "documentary_backend", _backend)
    return updates


def test_confirm_singleton_role_conflict_is_per_key(monkeypatch):
    row = _import_row()
    updates = _failing_insert(
        monkeypatch,
        row,
        DatabaseError("catalog_singleton_role_conflict: FRAME already exists"),
    )
    out = catalog_service.confirm_catalog_import(
        org_id=row["org_id"],
        import_id=row["id"],
        system_id=uuid4(),
        items=[_item()],
    )
    assert out["errors"] == [
        {"key": "c0", "code": "catalog_singleton_role_conflict"}
    ]
    assert out["created"] == []
    # Retryable: the import stays REVIEW_READY — no FAILED seal.
    assert updates[0][0].startswith("[")


def test_confirm_insert_failure_is_per_key(monkeypatch):
    row = _import_row()
    _failing_insert(monkeypatch, row, DatabaseError("constraint exploded"))
    out = catalog_service.confirm_catalog_import(
        org_id=row["org_id"],
        import_id=row["id"],
        system_id=uuid4(),
        items=[_item()],
    )
    assert out["errors"] == [{"key": "c0", "code": "catalog_insert_failed"}]


def test_confirm_failed_import_is_reconfirmable(monkeypatch):
    row = _import_row(status="FAILED")
    updates, inserts, article_id = _confirm_patches(monkeypatch, row)
    out = catalog_service.confirm_catalog_import(
        org_id=row["org_id"],
        import_id=row["id"],
        system_id=uuid4(),
        items=[_item()],
    )
    assert out["created"] == [{"key": "c0", "article_id": str(article_id)}]
    assert updates[0][1] != "FAILED"


def test_mark_failed_only_updates_inflight(monkeypatch):
    statements = []

    def _rows(sql, params=None):
        statements.append((sql, params))
        return []

    monkeypatch.setattr(catalog_service, "rows", _rows)
    monkeypatch.setattr(catalog_service, "documentary_backend", _backend)
    catalog_service.mark_catalog_import_failed(
        org_id=uuid4(), import_id=uuid4(), code="x" * 200
    )
    sql, params = statements[0]
    assert "UPLOADED" in sql and "EXTRACTING" in sql
    assert len(params[0]) == 80


def test_parse_article_line_name_strips_measurements():
    candidate = parse_article_line("ABC-1 Marco 78 mm", "r0")
    assert candidate["name"] == "Marco"
    candidate = parse_article_line(
        "MRC-100 Marco oscilobatiente 78 mm 1.45 kg/m refuerzo AC-55", "r1"
    )
    assert candidate["name"] == "Marco oscilobatiente"
    candidate = parse_article_line("MON-2 Montante 1.10 kg/m", "r2")
    assert candidate["name"] == "Montante"


def test_confirm_retry_rejects_other_system(monkeypatch):
    system_a = uuid4()
    row = _import_row(
        system_id=system_a,
        result=[{"key": "c0", "article_id": str(uuid4())}],
    )
    monkeypatch.setattr(
        catalog_service, "rows", lambda sql, params=None: [row]
    )
    monkeypatch.setattr(catalog_service, "documentary_backend", _backend)
    with pytest.raises(APIException) as failure:
        catalog_service.confirm_catalog_import(
            org_id=row["org_id"],
            import_id=row["id"],
            system_id=uuid4(),
            items=[_item(key="c1")],
        )
    assert failure.value.contract_code == "catalog_system_changed"
