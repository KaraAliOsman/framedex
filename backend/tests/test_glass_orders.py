"""HTTP downloads cannot collide with renderer negotiation or lose exact cuts."""
from contextlib import contextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest
from rest_framework.test import APIClient

from production import glass_orders


@pytest.fixture
def report():
    return {"authority": "Medidas del BOM sellado", "revisions": [], "labels": [], "rows": [{
        "order_code": "OT-P000001-A-01", "position_index": 1, "location": "=1+2",
        "piece_index": 1, "width_mm": "812.25", "height_mm": "1234.00",
        "integer_dimensions": False, "quantity": 2, "composition": "4 / 16 Ar / 4 Low-E (c3)",
        "article_sku": "VIDRIO", "processing": {"polished_edges": ["TOP"], "holes": 1},
        "instructions": [], "label_codes": ["P01-U01-V01", "P01-U02-V01"]}]}


@pytest.mark.parametrize("export_format,media", [("JSON", "application/json"),
    ("CSV", "text/csv; charset=utf-8"), ("PDF", "application/pdf")])
def test_export_parameter_reaches_real_route(monkeypatch, report, export_format, media):
    org, order = uuid4(), uuid4()

    @contextmanager
    def scope(request, readers):
        yield None, None, org

    monkeypatch.setattr(glass_orders, "documentary_scope", scope)
    def sealed(**kwargs):
        assert kwargs["org_id"] == org and kwargs["order_ids"] == [order]
        return report
    monkeypatch.setattr(glass_orders, "glass_order", sealed)
    monkeypatch.setattr(glass_orders, "glass_pdf", lambda value: b"%PDF-1.7\nsealed-test")
    client = APIClient()
    client.force_authenticate(user=SimpleNamespace(is_authenticated=True), token=object())
    response = client.get("/api/v1/production/glass-orders/", {"orders": str(order), "export_format": export_format})
    assert response.status_code == 200, response.content
    assert response["Content-Type"] == media
    if export_format == "JSON":
        assert response.data["rows"][0]["width_mm"] == "812.25"
    else:
        assert response["Content-Disposition"].endswith(f'pedido-vidrio.{export_format.lower()}"')


def test_csv_preserves_fractional_authority_and_neutralizes_formula(report):
    csv = glass_orders.glass_csv(report).decode("utf-8-sig")
    assert "812.25;1234;2" in csv
    assert "'=1+2" in csv
    assert "Pulido: superior; Perforaciones: 1" in csv
    assert glass_orders._display_size("1234.25") == "1\u2009234,25"


def test_pdf_font_fetcher_loads_only_bundled_fonts_including_windows_uris():
    from documents.renderers import _FONTS_DIR, _url_fetcher
    from documents.repository import DocumentaryError
    font = _url_fetcher((_FONTS_DIR / "IBMPlexSans-400.ttf").as_uri())
    if hasattr(font, "__enter__"):
        with font as fetched:
            assert fetched["mime_type"] in ("font/ttf", "application/x-font-ttf", "application/octet-stream")
    else:
        assert font
    with pytest.raises(DocumentaryError):
        _url_fetcher((_FONTS_DIR.parent / "renderers.py").as_uri())


def test_synthetic_glass_on_commercial_system_marks_the_document():
    from documents.renderers import _has_synthetic_glass
    value = {"is_demo": False, "positions": [{"is_demo": False, "parametric_tree": {
        "assembly": {"modules": [{"tree": {"glass_product": {"synthetic": True}}}]}}}]}
    assert _has_synthetic_glass(value)
    value["positions"][0]["parametric_tree"]["assembly"]["modules"][0]["tree"]["glass_product"]["synthetic"] = False
    assert not _has_synthetic_glass(value)


def test_supplier_pdf_repeats_demo_warning_on_every_page(report):
    from io import BytesIO
    from pypdf import PdfReader

    report["rows"] = [{**report["rows"][0], "position_index": index,
        "instructions": ["DEMO · catálogo sintético"]} for index in range(1, 25)]
    pages = PdfReader(BytesIO(glass_orders.glass_pdf(report))).pages
    assert len(pages) > 1
    assert all("DEMO · catálogo sintético" in page.extract_text() for page in pages)
