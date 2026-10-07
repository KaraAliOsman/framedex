from io import BytesIO
import base64

import httpx
import json
from types import SimpleNamespace
import pytest
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

from ai_gateway import multimodal
from ai_gateway.providers import ProviderError, OpenAICompatibleProvider
from backend.tests.test_ai_provider_operations import provider, reply


def pdf(pages):
    output = BytesIO()
    document = PdfWriter()
    for text in pages:
        page = document.add_blank_page(width=320, height=240)
        if text:
            font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
            page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})})
            stream = DecodedStreamObject()
            stream.set_data(f"BT /F1 12 Tf 20 160 Td ({text}) Tj ET".encode("ascii"))
            page[NameObject("/Contents")] = document._add_object(stream)
    document.write(output)
    return output.getvalue()


def test_mixed_pdf_preserves_literal_pages_and_renders_only_scans():
    parts = multimodal.pdf_page_parts(pdf(["MARCO A: 60 mm", None, "JUNQUILLO B", None]))
    assert [part["ref"] for part in parts] == [f"página {index}" for index in range(1, 5)]
    assert [part["text"] for part in parts if "text" in part] == ["MARCO A: 60 mm", "JUNQUILLO B"]
    images = [part for part in parts if "data" in part]
    assert [image["ref"] for image in images] == ["página 2", "página 4"]
    assert all(image["mime"] == "image/png" and base64.b64decode(image["data"]).startswith(b"\x89PNG") for image in images)
    assert multimodal.pdf_page_parts(pdf(["Literal catalog"])) == [{"ref": "página 1", "text": "Literal catalog"}]


@pytest.mark.parametrize("content", [b"invalid file", b"%PDF-1.7\ninvalid"])
def test_bad_pdf_reports_only_sanitized_cause(content):
    with pytest.raises(ProviderError) as error:
        multimodal.pdf_page_parts(content)
    assert error.value.code == "ai_source_unreadable"


def test_pdf_page_pixel_and_total_byte_limits(monkeypatch):
    with pytest.raises(ProviderError) as error:
        multimodal.pdf_page_parts(pdf([None] * 21))
    assert error.value.code == "ai_source_page_limit"
    monkeypatch.setattr(multimodal, "MAX_PIXELS", 100)
    with pytest.raises(ProviderError, match="ai_source_page_limit"):
        multimodal.pdf_page_parts(pdf([None]))
    monkeypatch.setattr(multimodal, "MAX_PIXELS", 8_000_000)
    monkeypatch.setattr(multimodal, "MAX_IMAGE_BYTES", 20)
    with pytest.raises(ProviderError, match="ai_source_page_limit"):
        multimodal.pdf_page_parts(pdf([None]))


def test_pdf_literal_text_is_bounded_without_silent_truncation(monkeypatch):
    monkeypatch.setattr(multimodal, "MAX_TEXT_CHARS", 10)
    with pytest.raises(ProviderError, match="ai_source_page_limit"):
        multimodal.pdf_page_parts(pdf(["Catalog table", "Dimensions"]))


@pytest.mark.parametrize("pages", [["Technical table A: 7135"], ["Technical table A: 7135", None]])
def test_vision_transport_receives_text_layer_pdf_and_mixed_pages(monkeypatch, pages):
    subject, bodies = provider(monkeypatch), []
    content = pdf(pages)
    monkeypatch.setattr("documents.storage.SupabaseDocumentStorage", lambda: SimpleNamespace(
        signed_url=lambda *_: "https://storage.example/private.pdf?token=synthetic", download_bounded=lambda *_: content))
    def handler(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json=reply())
    assert isinstance(subject, OpenAICompatibleProvider)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        subject.invoke(route={"provider_model": "vision-model"}, capability="vision_ocr",
            input_payload={"kind": "PDF", "source": {"kind": "document_import", "id": "synthetic-source"}},
            document_path="tenant/private.pdf", operation_key="pdf-fallback", client=client)
    parts = bodies[0]["messages"][-1]["content"]
    assert any(part.get("text") == "Technical table A: 7135" for part in parts)
    assert len([part for part in parts if part["type"] == "image_url"]) == len(pages) - 1
    assert "storage.example" not in json.dumps(bodies) and "synthetic-source" in json.dumps(bodies)
