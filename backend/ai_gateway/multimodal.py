"""Bounded PDF text/image parts; OCR proposals never become source authority."""

import base64
from contextlib import closing
from io import BytesIO

from ai_gateway.providers import ProviderError

MAX_SCAN_PAGES = 20
MAX_PIXELS = 8_000_000
MAX_IMAGE_BYTES = 12 * 1024 * 1024
MAX_TEXT_CHARS = 100_000


def pdf_page_parts(content, *, page_range=None):
    import pypdfium2 as pdfium
    parts, total, text_chars = [], 0, 0
    try:
        with pdfium.PdfDocument(content) as document:
            start, end = 1, len(document)
            if page_range is not None:
                if (not isinstance(page_range, list) or len(page_range) != 2
                        or any(type(value) is not int for value in page_range)):
                    raise ProviderError("ai_source_page_limit")
                start, end = page_range
            if start < 1 or end > len(document) or end < start or end - start + 1 > MAX_SCAN_PAGES:
                raise ProviderError("ai_source_page_limit")
            for index in range(start - 1, end):
                with closing(document[index]) as page:
                    with closing(page.get_textpage()) as text:
                        text_chars += text.count_chars()
                        if text_chars > MAX_TEXT_CHARS:
                            raise ProviderError("ai_source_page_limit")
                        literal = text.get_text_range().strip()
                        if literal:
                            parts.append({"ref": f"página {index + 1}", "text": literal})
                    # Mixed pages need their diagrams too. Text is evidence;
                    # the image preserves sections, arrows and table layout.
                    width, height = page.get_size()
                    if width <= 0 or height <= 0:
                        raise ProviderError("ai_source_page_limit")
                    scale = min(2, (MAX_PIXELS / (width * height)) ** 0.5)
                    with closing(page.render(scale=scale)) as bitmap:
                        output = BytesIO()
                        bitmap.to_pil().convert("RGB").save(output, format="JPEG", quality=88, optimize=True)
                        raw = output.getvalue()
                    total += len(raw)
                    if total > MAX_IMAGE_BYTES:
                        raise ProviderError("ai_source_page_limit")
                    parts.append({"mime": "image/jpeg", "data": base64.b64encode(raw).decode("ascii"), "ref": f"página {index + 1}"})
    except ProviderError:
        raise
    except Exception:
        raise ProviderError("ai_source_unreadable") from None
    return parts
