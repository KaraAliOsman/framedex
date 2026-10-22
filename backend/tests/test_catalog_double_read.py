"""Independent reads preserve discrepancies, literal evidence and exact decimals."""

from copy import deepcopy
from decimal import Decimal
from uuid import uuid4
import json

import pytest

from ingest import catalog_ai, catalog_review
from ingest.catalog_double_read import compare_reads
from ingest.catalog_template import SCHEMAS, normalize

TAGGED = [("Sistema S60. SKU MARCO. Ancho de cara 60,00 mm. Otra tabla: ancho de cara 61,00 mm.", "página 1")]


def response(value="60.00", *, sku="MARCO", confidence="HIGH"):
    literal = value.replace(".", ",")
    quote = "Ancho de cara 60,00 mm" if Decimal(value) == Decimal("60") else "ancho de cara 61,00 mm"
    return {"records": [{"sheet": "Perfiles", "values": {"system_code": "S60", "sku": sku, "face_width_mm": value},
        "evidence": {"system_code": {"ref": "página 1", "quote": "Sistema S60", "literal": "S60", "confidence": "HIGH"},
            "sku": {"ref": "página 1", "quote": f"SKU {sku}", "literal": sku, "confidence": "HIGH"},
            "face_width_mm": {"ref": "página 1", "quote": quote, "literal": literal, "confidence": confidence}}}]}


def read(payload):
    return catalog_ai.parse_response(json.dumps(payload), tagged=TAGGED, file_name="ficha.pdf")


def compare(a=None, b=None):
    return compare_reads(read(a or response()), read(b or response()), file_name="ficha.pdf", audit_ids=[uuid4(), uuid4()])


def test_equal_cells_are_exact_proposals_with_two_audits_and_citations():
    row = compare()[0]
    assert row["values"]["face_width_mm"] == "60.00"
    field = row["fields"]["face_width_mm"]
    assert field["comparison"] == "AGREED" and field["confidence"] == "HIGH"
    assert len({item["audit_id"] for item in field["readings"]}) == 2
    assert all(item["quote"] and item["ref"] == "página 1" for item in field["readings"])
    column = next(column for column in SCHEMAS["Perfiles"] if column.key == "face_width_mm")
    assert Decimal(normalize(row["values"]["face_width_mm"], column)) == Decimal("60.00")
    assert "origin" not in row  # Extraction never publishes MANUAL facts.


def test_only_different_or_unsupported_cells_need_review():
    row = compare(b=response("61.00"))[0]
    assert row["values"]["face_width_mm"] is None
    assert row["double_read"]["review_fields"] == ["face_width_mm"]
    assert row["fields"]["system_code"]["comparison"] == "AGREED"
    assert row["fields"]["weight_kg_m"]["comparison"] == "MISSING"
    assert [item["value"] for item in row["fields"]["face_width_mm"]["readings"]] == ["60.00", "61.00"]
    unsupported = compare(b=response(confidence="LOW"))[0]
    assert unsupported["values"]["face_width_mm"] is None
    assert unsupported["fields"]["face_width_mm"]["comparison"] == "REVIEW"


def test_decimal_scale_does_not_create_a_false_discrepancy():
    left, right = read(response()), read(response())
    right[0]["values"]["face_width_mm"] = "60.0"
    rows = compare_reads(left, right, file_name="ficha.pdf", audit_ids=["first", "second"])
    assert rows[0]["fields"]["face_width_mm"]["comparison"] == "AGREED"


def test_reordered_records_align_by_identity_and_duplicates_never_silently_merge():
    a = read(response())
    other = deepcopy(a[0])
    other["values"]["sku"] = "OTRO"
    first = [*a, other]
    rows = compare_reads(first, list(reversed(deepcopy(first))), file_name="ficha.pdf", audit_ids=["1", "2"])
    assert len(rows) == 2 and all(row["double_read"]["identity_unique"] for row in rows)
    rows = compare_reads(a + deepcopy(a), a, file_name="ficha.pdf", audit_ids=["1", "2"])
    assert len(rows) == 3 and not any(row["double_read"]["identity_unique"] for row in rows)
    assert all(row["values"]["face_width_mm"] is None for row in rows)


def test_missing_row_and_distinct_text_codes_remain_separate():
    first = read(response())
    second = deepcopy(first)
    first[0]["values"]["sku"] = "001"
    second[0]["values"]["sku"] = "1"
    rows = compare_reads(first, second, file_name="ficha.pdf", audit_ids=["1", "2"])
    assert len(rows) == 2 and all(row["double_read"]["review_fields"] for row in rows)


def test_rows_without_a_supported_identity_cannot_be_agreed():
    first = read(response())
    first[0]["values"]["sku"] = None
    rows = compare_reads(first, deepcopy(first), file_name="ficha.pdf", audit_ids=["1", "2"])
    assert len(rows) == 2 and not any(row["double_read"]["identity_unique"] for row in rows)
    assert all(row["values"]["face_width_mm"] is None for row in rows)


@pytest.mark.parametrize("pages", [False, True])
def test_provider_calls_are_independent_and_retries_keep_distinct_stable_keys(monkeypatch, pages):
    calls = []
    audit_ids = [uuid4(), uuid4()]
    def invoke(**kwargs):
        calls.append(kwargs)
        return {"output": json.dumps(response()), "audit_id": audit_ids[(len(calls) - 1) % 2]}
    monkeypatch.setattr("ai_gateway.service.invoke", invoke)
    args = {"org_id": uuid4(), "actor_id": uuid4(), "import_id": uuid4(), "file_name": "ficha.pdf", "tagged": TAGGED}
    run = catalog_ai.compile_catalog_pages if pages else catalog_ai.compile_catalog
    extra = {"chunk": {"first": 1, "last": 2, "visual_pages": [2]}} if pages else {"kind": "TEXT"}
    rows, anchor = run(**args, **extra)
    assert anchor == audit_ids[0] and rows[0]["values"]["face_width_mm"] == "60.00"
    assert len(calls) == 2
    assert calls[0]["operation_key"] != calls[1]["operation_key"]
    assert calls[0]["provider_options"]["system"] != calls[1]["provider_options"]["system"]
    assert all("records" not in call["input_payload"] and "output" not in call["input_payload"] for call in calls)
    run(**args, **extra)
    assert [call["operation_key"] for call in calls[:2]] == [call["operation_key"] for call in calls[2:]]


def test_second_read_failure_does_not_return_single_read_proposals(monkeypatch):
    calls = []
    def invoke(**kwargs):
        calls.append(kwargs)
        if len(calls) == 2:
            raise ValueError("provider unavailable")
        return {"output": json.dumps(response()), "audit_id": uuid4()}
    monkeypatch.setattr("ai_gateway.service.invoke", invoke)
    with pytest.raises(ValueError, match="provider unavailable"):
        catalog_ai.compile_catalog(org_id=uuid4(), actor_id=uuid4(), import_id=uuid4(), kind="TEXT", file_name="ficha.pdf", tagged=TAGGED)


def test_review_can_choose_a_supported_read_but_arbitrary_correction_stays_workshop():
    original = compare(b=response("61.00"))[0]
    saved = {"candidates": [original]}
    for value, method in (("61.00", "AI"), ("62.00", "HUMAN_CORRECTION")):
        selected = catalog_review._entries(saved, [{"key": original["key"], "values": {**original["values"], "face_width_mm": value}}])[0]
        assert selected["fields"]["face_width_mm"]["method"] == method
        if method == "AI":
            assert selected["fields"]["face_width_mm"]["literal"] == "61,00"
            assert selected["fields"]["face_width_mm"]["comparison"] == "HUMAN_RESOLVED"


@pytest.mark.parametrize("bad", [0.1, float("nan"), float("inf"), Decimal("NaN")])
def test_native_inexact_or_nonfinite_numbers_are_rejected_before_candidate_creation(bad):
    payload = response()
    payload["records"][0]["values"]["section"] = {"depth_mm": bad}
    with pytest.raises(ValueError, match="inexacto o no finito"):
        catalog_ai.parse_response(payload, tagged=TAGGED, file_name="ficha.pdf")
