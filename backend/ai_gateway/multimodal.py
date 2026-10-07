"""Bounded PDF text/image parts; OCR proposals never become source authority."""

import base64
from contextlib import closing
from io import BytesIO

from ai_gateway.providers import ProviderError

MAX_SCAN_PAGES = 20
MAX_PIXELS = 8_000_000
MAX_IMAGE_BYTES = 12 * 1024 * 1024
MAX_TEXT_CHARS = 100_000


def pdf_page_parts(content):
    import pypdfium2 as pdfium
    parts, total, text_chars = [], 0, 0
    try:
        with pdfium.PdfDocument(content) as document:
            if len(document) > MAX_SCAN_PAGES:
                raise ProviderError("ai_source_page_limit")
            for index in range(len(document)):
                with closing(document[index]) as page:
                    with closing(page.get_textpage()) as text:
                        text_chars += text.count_chars()
                        if text_chars > MAX_TEXT_CHARS:
                            raise ProviderError("ai_source_page_limit")
                        literal = text.get_text_range().strip()
                        if literal:
                            parts.append({"ref": f"página {index + 1}", "text": literal})
                            continue
                    width, height = page.get_size()
                    if width <= 0 or height <= 0 or width * height * 4 > MAX_PIXELS:
                        raise ProviderError("ai_source_page_limit")
                    with closing(page.render(scale=2)) as bitmap:
                        output = BytesIO()
                        bitmap.to_pil().save(output, format="PNG", optimize=True)
                        raw = output.getvalue()
                    total += len(raw)
                    if total > MAX_IMAGE_BYTES:
                        raise ProviderError("ai_source_page_limit")
                    parts.append({"mime": "image/png", "data": base64.b64encode(raw).decode("ascii"), "ref": f"página {index + 1}"})
    except ProviderError:
        raise
    except Exception:
        raise ProviderError("ai_source_unreadable") from None
    return parts
