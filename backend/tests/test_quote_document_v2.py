"""Read the actual PDF: currency, text bounds, density and frozen declarations."""
from copy import deepcopy
from decimal import Decimal
import re
import warnings

import pytest
from PIL import Image
import zxingcpp

# MuPDF's generated SWIG types warn during module initialization on Python
# 3.12; treating that third-party warning as an exception can crash its loader.
# Keep the repository's warnings-as-errors policy for the PDF work itself.
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message=r"builtin type (SwigPyPacked|SwigPyObject|swigvarlink) has no __module__ attribute", category=DeprecationWarning)
    import fitz

from backend.tests.doc01_cases import proposal_case
from documents.preferences import document_preferences
from documents.quote_serializers import CommercialTermsSerializer
from documents.renderers import _doc01, _money, render_pdf_document


@pytest.mark.parametrize("count,currency,long_names", [
    (1, "CLP", False), (12, "CLP", False), (24, "CLP", False),
    (100, "CLP", False), (12, "USD", False), (100, "CLP", True),
])
def test_pdf_pages_have_content_exact_totals_and_no_text_collisions(count, currency, long_names):
    snapshot = proposal_case(count, currency, long_names=long_names)
    content, _ = render_pdf_document("DOC-01", snapshot, pdf_identifier="quote-layout-test",
        portal_url="https://example.test/cotizacion/revision-bound-token")
    with fitz.open(stream=content, filetype="pdf") as document:
        detected_tables = 0
        assert len(document) <= 45
        text = "\n".join(page.get_text() for page in document)
        expected = _money(snapshot["pricing"]["result"]["project_gross"], currency)
        assert expected in text
        assert snapshot["project"]["total_price_gross"] == str(snapshot["pricing"]["result"]["project_gross"])
        assert "US$" in text if currency == "USD" else "US$" not in text
        assert "IVA 19,0 %" in text
        assert "DEMO" in text and "Sin dato" not in text
        if long_names:
            assert len(snapshot["project"]["client_name"]) == 120
            assert all(len(item["location_tag"]) == 120 for item in snapshot["positions"])
            assert " ".join(snapshot["project"]["client_name"].split()) in " ".join(text.split())
        for page_index, page in enumerate(document):
            words = [word for word in page.get_text("words") if 35 < word[1] and word[3] < page.rect.height - 70]
            assert len(words) > 10, (page_index, page.get_text())
            body_text = " ".join(word[4] for word in words)
            assert any(marker in body_text for marker in ("Cotización", "Resumen", "Posición", "Aceptación", "$")), (page_index, body_text)
            assert not re.search(r"\b[0-9a-fA-F]{10,}\b", body_text)
            assert "costo" not in body_text.casefold() and "margen" not in body_text.casefold()
            # Test monetary columns and wrapped names in actual table words.
            tables = page.find_tables(vertical_strategy="text", horizontal_strategy="lines").tables
            detected_tables += len(tables)
            for table in tables:
                table_words = [word for word in words if fitz.Rect(table.bbox).contains(fitz.Rect(word[:4]))]
                for index, first in enumerate(table_words):
                    assert 33 < first[0] < first[2] < page.rect.width - 33, first
                    for second in table_words[index + 1:]:
                        overlap = fitz.Rect(first[:4]) & fitz.Rect(second[:4])
                        assert overlap.width <= 0.2 or overlap.height <= 0.2, (page_index, first, second)
            assert f"Página {page_index + 1} / {len(document)}" in " ".join(page.get_text().split())
            assert "COT-P-000123-REV-B" in page.get_text()
        assert detected_tables > 0


@pytest.mark.parametrize("paper,width,height", [("LETTER", 612, 792), ("A4", 595.28, 841.89), ("OFICIO", 612.28, 935.43)])
def test_declared_paper_is_used_and_plex_is_embedded(paper, width, height):
    pdf, _ = render_pdf_document("DOC-01", proposal_case(1, paper=paper), pdf_identifier="paper-test")
    with fitz.open(stream=pdf, filetype="pdf") as document:
        assert document[0].rect.width == pytest.approx(width, abs=0.1)
        assert document[0].rect.height == pytest.approx(height, abs=0.1)
        fonts = [font for page in document for font in page.get_fonts()]
        assert any("Plex-Sans" in font[3] for font in fonts)
        assert any("Plex-Mono" in font[3] for font in fonts)
        assert all(document.extract_font(font[0])[3] for font in fonts)


def test_historical_payment_text_never_invents_a_schedule_or_discount():
    snapshot = proposal_case(1)
    snapshot["project"].pop("commercial_terms")
    snapshot["pricing"]["result"].pop("line_detail")
    html = _doc01(snapshot)
    assert "Calendario de pagos" not in html
    assert "Neto antes de descuento" not in html
    assert "Anticipo al aprobar" in html
    snapshot["organization"]["document_preferences"] = document_preferences({})
    assert _doc01(snapshot) == html


def test_tax_label_uses_sealed_rules_not_a_guessed_ratio():
    snapshot = proposal_case(1)
    snapshot["pricing"]["request"] = {}
    snapshot["pricing"]["input_snapshot"] = {"rules": {"tax_rate_pct": "0.19"}}
    assert "IVA 19,0 %" in _doc01(snapshot)
    snapshot["pricing"]["input_snapshot"] = {}
    assert "IVA" not in _doc01(snapshot) and "Impuesto" in _doc01(snapshot)


def test_terms_require_exact_fraction_sum_and_escape_legal_text():
    good = {"payment_schedule": [{"label": "Al aprobar", "share": "0.4"}, {"label": "Entrega", "share": "0.6"}]}
    assert CommercialTermsSerializer(data=good).is_valid()
    bad = deepcopy(good)
    bad["payment_schedule"][1]["share"] = "0.600001"
    assert not CommercialTermsSerializer(data=bad).is_valid()
    assert not CommercialTermsSerializer(data={"payment_schedule": [{"label": "Uno", "share": "0"}]}).is_valid()
    snapshot = proposal_case(1)
    snapshot["project"]["commercial_terms"]["warranty"] = "<script>Garantía</script>"
    assert "&lt;script&gt;" in _doc01(snapshot)


def test_plan_and_fields_use_declared_geometry_only():
    snapshot = proposal_case(1)
    from backend.tests.integration.test_product_v2_documentary import _bow_tree
    from dekopen_engine.product import _plan_geometry
    from engine_api.adapter import parse_product_model
    tree = _bow_tree()
    plan, _ = _plan_geometry(parse_product_model(tree).assembly, Decimal("60"))
    snapshot["positions"][0].update(parametric_tree=tree, drawing_plan=plan.model_dump(mode="json"))
    html = _doc01(snapshot)
    assert 'data-drawing="sealed-plan"' in html
    assert "Campo 3.1" in html
    pdf, _ = render_pdf_document("DOC-01", snapshot, pdf_identifier="module-identification")
    with fitz.open(stream=pdf, filetype="pdf") as document:
        # Names remain readable in the specification even when many dimension
        # lanes reduce the assembly's drawing to a small reference image.
        labels = [span for page in document for block in page.get_text("dict")["blocks"]
                  if "lines" in block for line in block["lines"] for span in line["spans"]
                  if "Módulo" in span["text"] and span["size"] >= 8.25]
        assert all(any(f"Módulo {index}" in span["text"] for span in labels) for index in (1, 2, 3))
    snapshot["positions"][0].pop("drawing_plan")
    assert 'data-drawing="sealed-plan"' not in _doc01(snapshot)


def test_supplier_glass_composition_and_ug_survive_pdf_without_inference():
    from dekopen_engine.glass_composition import GlassProduct, GlassProperties, SupplierValue, parse_glass_notation
    snapshot = proposal_case(1)
    glass = GlassProduct(name="Termopanel de prueba", composition=parse_glass_notation("4/16 argón/4 Low-E"),
        source="Ficha declarada de prueba", properties=GlassProperties(ug=SupplierValue(value=Decimal("1.10"), source="Ficha térmica de prueba")))
    snapshot["positions"][0]["parametric_tree"]["glass_product"] = glass.model_dump(mode="json")
    pdf, _ = render_pdf_document("DOC-01", snapshot, pdf_identifier="glass-authority")
    with fitz.open(stream=pdf, filetype="pdf") as document:
        text = " ".join(" ".join(page.get_text().split()) for page in document)
        assert "1,10 W/m²K" in text and "Ficha térmica de prueba" in text
        assert "16 Ar" in text and "Low-E" in text
    snapshot["positions"][0]["parametric_tree"]["glass_product"]["properties"] = {}
    assert ">Ug" not in _doc01(snapshot)


def test_qr_decodes_from_printed_pixels_and_matches_the_clickable_revision_link():
    target = "https://example.test/cotizacion/revision-bound-document-token"
    pdf, _ = render_pdf_document("DOC-01", proposal_case(12), pdf_identifier="printed-qr", portal_url=target)
    with fitz.open(stream=pdf, filetype="pdf") as document:
        acceptance = document[-1]
        pixels = acceptance.get_pixmap(dpi=150, alpha=False)
        decoded = zxingcpp.read_barcodes(Image.frombytes("RGB", (pixels.width, pixels.height), pixels.samples))
        assert [code.text for code in decoded] == [target]
        assert any(link.get("uri") == target for link in acceptance.get_links())


def test_doc01_reads_exact_sealed_measures_with_nonzero_coupling_gap():
    from backend.tests.doc01_cases import proposal_case
    from documents.renderers import _doc01, render_pdf_document
    from dekopen_engine.product import evaluate_product
    from dekopen_engine.assembly_measures import developed_layout
    from engine.tests.assembly_cases import bow_model, joint_article
    from engine.tests.catalog import demo_60_params
    article = joint_article(width='24')
    product = bow_model()
    evaluation = evaluate_product(product, demo_60_params(), coupler_articles={article.sku: article})
    position = proposal_case(1)
    position['positions'][0].update(parametric_tree=product.model_dump(mode='json'),
        width_mm='2448.00', height_mm='1200.00',
        drawing_plan={**evaluation.plan.model_dump(mode='json'),
                      'assembly_measures': evaluation.measures.model_dump(mode='json')})
    before = product.model_dump(mode='json')
    html = _doc01(position)
    assert 'data-drawing="sealed-plan"' in html
    pdf, _ = render_pdf_document('DOC-01', position, pdf_identifier='sealed-coupling-measures')
    with fitz.open(stream=pdf, filetype='pdf') as document:
        text = ' '.join(' '.join(page.get_text().split()) for page in document)
        assert 'Ancho desarrollado' in text and 'Frente / cuerda' in text and 'Proyección' in text
        assert '2 448' in text
    assert product.model_dump(mode='json') == before
    assert developed_layout(product.assembly, evaluation.measures).members[1].x_mm == Decimal('624')
