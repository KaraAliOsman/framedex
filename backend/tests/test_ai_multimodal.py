from io import BytesIO
import base64

import pytest
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

from ai_gateway import multimodal
from ai_gateway.providers import ProviderError


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


def test_only_pages_without_literal_text_become_png_parts():
    images = multimodal.scanned_pdf_images(pdf(["MARCO A: 60 mm", None, "JUNQUILLO B", None]))
    assert [image["ref"] for image in images] == ["página 2", "página 4"]
    assert all(image["mime"] == "image/png" and base64.b64decode(image["data"]).startswith(b"\x89PNG") for image in images)
    assert multimodal.scanned_pdf_images(pdf(["Literal catalog"])) == []


@pytest.mark.parametrize("content", [b"invalid file", b"%PDF-1.7\ninvalid"])
def test_bad_pdf_reports_only_sanitized_cause(content):
    with pytest.raises(ProviderError) as error:
        multimodal.scanned_pdf_images(content)
    assert error.value.code == "ai_source_unreadable"


def test_pdf_page_pixel_and_total_byte_limits(monkeypatch):
    with pytest.raises(ProviderError) as error:
        multimodal.scanned_pdf_images(pdf([None] * 21))
    assert error.value.code == "ai_source_page_limit"
    monkeypatch.setattr(multimodal, "MAX_PIXELS", 100)
    with pytest.raises(ProviderError, match="ai_source_page_limit"):
        multimodal.scanned_pdf_images(pdf([None]))
    monkeypatch.setattr(multimodal, "MAX_PIXELS", 8_000_000)
    monkeypatch.setattr(multimodal, "MAX_IMAGE_BYTES", 20)
    with pytest.raises(ProviderError, match="ai_source_page_limit"):
        multimodal.scanned_pdf_images(pdf([None]))
