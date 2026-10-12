"""Render only sealed authoritative metrics; never invent a certificate."""
from copy import deepcopy
import warnings
import json

from backend.tests.doc01_cases import proposal_case
from documents.quotation import thermal_annex, field_specs
from documents.renderers import render_pdf_document
from engine.tests.thermal_cases import geometry, reports, AS_OF
from dekopen_engine.thermal import calculate_uw
from dekopen_engine.glass_composition import GlassProduct, parse_glass_notation

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message=r"builtin type (SwigPyPacked|SwigPyObject|swigvarlink) has no __module__ attribute", category=DeprecationWarning)
    import fitz


def annex_case():
    geo, _ = geometry()
    metric = calculate_uw(geo, reports(), catalog_fingerprint="unit-test-geometry", as_of=AS_OF)
    return {"inputs":{"include_doc01":True},"assessment":{"scope":"Fixture matemático, no usar en obra", "positions":[
        {"position_index":1,"location_tag":"Caso aislado, sin certificado","thermal":metric},
        {"position_index":2,"location_tag":"INCOMPLETE-MARKER","thermal":{"state":"UNKNOWN","uw":None}},
    ]}}


def test_optional_annex_omits_unknown_values_and_escapes_source_text():
    report = annex_case()
    html = thermal_annex(report)
    assert "1,37 W/m²K" in html and "Factor solar g" in html and "0,55" in html
    assert "INCOMPLETE-MARKER" not in html and "Sin dato" not in html
    assert "Prueba matemática aislada; sin certificación" in html
    absent = deepcopy(report)
    absent["inputs"]["include_doc01"] = False
    assert thermal_annex(absent) == "" and thermal_annex(None) == ""
    report["assessment"]["positions"][0]["thermal"]["trace"]["frame_report"]["source_document"] = "<script>unsafe</script>"
    assert "<script>" not in thermal_annex(report) and "&lt;script&gt;" in thermal_annex(report)


def test_new_emissions_never_reuse_unreviewed_glass_properties():
    product = GlassProduct.model_validate_json(json.dumps({
        "name": "Vidrio sintético", "source": "Fixture", "synthetic": True,
        "composition": parse_glass_notation("4-16-4").model_dump(mode="json"),
        "properties": {"ug": {"value": "1.1", "source": "UNREVIEWED-MARKER"}},
    }))
    position = {"width_mm":"1000", "height_mm":"1000", "parametric_tree": {
        "id":"fixture", "type":"BAY", "opening_type":"FIXED",
        "glass_thickness_mm":"24", "glass_product":product.model_dump(mode="json"),
    }}
    assert "UNREVIEWED-MARKER" in field_specs(position)
    current = field_specs(position, authoritative_thermal=True)
    assert "DEMO" in current and "UNREVIEWED-MARKER" not in current


def test_sealed_annex_pdf_contains_sources_with_no_text_outside_body():
    snapshot = proposal_case(1)
    snapshot["thermal"] = annex_case()
    pdf, _ = render_pdf_document("DOC-01", snapshot, pdf_identifier="thermal-unit-fixture")
    with fitz.open(stream=pdf,filetype="pdf") as document:
        text = "\n".join(page.get_text() for page in document)
        assert "1,37" in text and "Anexo técnico" in text and "sin certificación" in text
        assert "INCOMPLETE-MARKER" not in text
        for page in document:
            for word in page.get_text("words"):
                if 35 < word[1] and word[3] < page.rect.height - 70:
                    assert 30 < word[0] < word[2] < page.rect.width - 30, word
