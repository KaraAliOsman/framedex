"""Whole PDF sections and complementary evidence do not invent authority."""

from io import BytesIO
from uuid import uuid4

from pypdf import PdfWriter

from ingest.catalog_ai import compile_catalog, merge_sections
from ingest.catalog_template import candidate


def test_whole_pdf_is_read_in_stable_bounded_sections(monkeypatch):
    writer = PdfWriter()
    for _ in range(9):
        writer.add_blank_page(width=100, height=100)
    content = BytesIO()
    writer.write(content)
    calls, progress = [], []
    def invoke(**kwargs):
        calls.append(kwargs)
        return {"audit_id": "audit", "output": '{"records":[]}'}
    monkeypatch.setattr("ai_gateway.service.invoke", invoke)
    identity = uuid4()
    result = compile_catalog(org_id=uuid4(), actor_id=uuid4(), import_id=identity,
        kind="PDF", file_name="Catalogo.pdf", content=content.getvalue(),
        tagged=[(f"Texto {index}", f"página {index}") for index in range(1, 10)],
        on_progress=lambda *values: progress.append(values))
    assert result == ([], "audit")
    assert [call["input_payload"]["page_range"] for call in calls] == [[1, 4], [5, 8], [9, 9]]
    assert [len(call["input_payload"]["source_lines"]) for call in calls] == [4, 4, 1]
    assert [call["operation_key"] for call in calls] == [f"catalog:{identity}:typed-v2:section:{index}" for index in range(3)]
    assert progress == [(1, 3, 0, [1, 4]), (2, 3, 0, [5, 8]), (3, 3, 0, [9, 9])]


def test_merge_combines_complementary_fields_and_keeps_conflicting_rows():
    def row(key, values):
        return candidate("Perfiles", {"system_code": "S60", "sku": "M01", **values}, key=key, row=1, method="AI")
    merged = merge_sections([row("one", {"name": "Marco"}), row("two", {"face_width_mm": "60.00"}), row("three", {"face_width_mm": "65.00"})])
    assert len(merged) == 2
    assert merged[0]["values"]["name"] == "Marco"
    assert str(merged[0]["values"]["face_width_mm"]) == "60.00"
    assert str(merged[1]["values"]["face_width_mm"]) == "65.00"


def test_different_declared_revisions_are_not_merged():
    entries = [candidate("Sistemas", {"system_code": "S60", "version": version}, key=str(version), row=1, method="AI") for version in (1, 2)]
    assert len(merge_sections(entries)) == 2
