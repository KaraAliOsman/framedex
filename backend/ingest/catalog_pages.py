"""Page inventory and internal partition for long or mixed catalog PDFs.

A long catalog is processed in bounded batches of consecutive pages instead
of asking the person to split the document. A page that carries text but
also a large drawing or a scanned table is «mixed»: it travels as text AND as
an image so the drawing is not lost because a footer has text. Nothing here
interprets values; it only decides how each page is read.
"""

from __future__ import annotations

from contextlib import closing
from io import BytesIO

# Partition bounds: small enough for one provider call to keep page context,
# large enough to keep tables that continue across pages together.
CHUNK_PAGES = 8
CHUNK_CHARS = 40_000
MAX_CHUNK_IMAGES = 6
# A page is read visually when its text is scarce or images cover a real
# part of it.
MIN_TEXT_CHARS = 160
MIXED_IMAGE_COVERAGE = 0.18
# Technical sections are usually vector drawings, not images: a page with
# many path objects carries a drawing whose dimensions need the picture.
DRAWING_PATHS = 120
MAX_PAGES = 600


def text_quality(literal: str) -> float:
    """Share of the text layer that reads as language (letters, digits,
    spaces, usual punctuation). A broken font encoding yields symbol soup
    that must be read visually instead."""
    if not literal:
        return 0.0
    usual = sum(1 for char in literal if char.isalnum() or char.isspace() or char in ".,;:-()/°%×x²³")
    vowels = sum(1 for char in literal.lower() if char in "aeiouáéíóú")
    letters = sum(1 for char in literal if char.isalpha())
    ratio = usual / len(literal)
    # Real Spanish/technical text keeps a vowel share among letters.
    if letters > 40 and vowels / letters < 0.18:
        ratio = min(ratio, 0.4)
    return ratio


def inventory(content: bytes) -> list[dict]:
    """[{page, chars, image_coverage, mode}] with mode text | scan | mixed."""
    import pypdfium2 as pdfium
    import pypdfium2.raw as raw

    pages: list[dict] = []
    with pdfium.PdfDocument(content) as document:
        if len(document) > MAX_PAGES:
            raise ValueError("catalog_pages_over_limit")
        for index in range(len(document)):
            with closing(document[index]) as page:
                width, height = page.get_size()
                area = max(width * height, 1.0)
                with closing(page.get_textpage()) as text:
                    chars = text.count_chars()
                    quality = text_quality(text.get_text_range()) if chars else 0.0
                covered = 0.0
                paths = 0
                for item in page.get_objects(
                    filter=[raw.FPDF_PAGEOBJ_IMAGE, raw.FPDF_PAGEOBJ_PATH], max_depth=3
                ):
                    if item.type == raw.FPDF_PAGEOBJ_PATH:
                        paths += 1
                        continue
                    left, bottom, right, top = item.get_bounds()
                    covered += max(right - left, 0) * max(top - bottom, 0)
                coverage = min(covered / area, 1.0)
                garbled = chars >= MIN_TEXT_CHARS and quality < 0.75
                drawing = paths >= DRAWING_PATHS
                mode = (
                    # Little text: what matters is on the picture (scan or
                    # vector drawing). An empty page stays text (nothing to see).
                    "scan"
                    if chars < MIN_TEXT_CHARS and (coverage > 0.05 or drawing or chars == 0 and paths > 0)
                    else "mixed"
                    if coverage >= MIXED_IMAGE_COVERAGE or garbled or drawing
                    else "text"
                )
                pages.append({
                    "page": index + 1,
                    "chars": int(chars),
                    "image_coverage": round(coverage, 3),
                    "text_quality": round(quality, 2),
                    "vector_paths": paths,
                    "mode": mode,
                })
    return pages


def partition(pages: list[dict]) -> list[dict]:
    """Consecutive page batches bounded by pages, text and images."""
    chunks: list[dict] = []
    current: list[dict] = []

    def close() -> None:
        if current:
            chunks.append({
                "index": len(chunks),
                "first": current[0]["page"],
                "last": current[-1]["page"],
                "chars": sum(item["chars"] for item in current),
                "visual_pages": [item["page"] for item in current if item["mode"] != "text"],
                "state": "PENDING",
            })

    for page in pages:
        visual = sum(1 for item in current if item["mode"] != "text") + (page["mode"] != "text")
        if current and (
            len(current) >= CHUNK_PAGES
            or sum(item["chars"] for item in current) + page["chars"] > CHUNK_CHARS
            or visual > MAX_CHUNK_IMAGES
        ):
            close()
            current = []
        current.append(page)
    close()
    return chunks


def page_parts(content: bytes, first: int, last: int, visual_pages: set[int]) -> list[dict]:
    """Provider parts for one batch: text for every page with text, plus a
    rendered image for scanned and mixed pages."""
    import base64

    import pypdfium2 as pdfium

    parts: list[dict] = []
    with pdfium.PdfDocument(content) as document:
        for number in range(first, min(last, len(document)) + 1):
            with closing(document[number - 1]) as page:
                with closing(page.get_textpage()) as text:
                    literal = text.get_text_range().strip()
                if literal:
                    parts.append({"ref": f"página {number}", "text": literal})
                if number in visual_pages:
                    parts.append({
                        "ref": f"página {number}",
                        "mime": "image/png",
                        "data": base64.b64encode(render_page(page)).decode("ascii"),
                    })
    return parts


def render_page(page, scale: float = 2.0) -> bytes:
    width, height = page.get_size()
    # Large-format pages are rendered at a bounded size.
    scale = min(scale, 2200 / max(width, height, 1))
    with closing(page.render(scale=scale)) as bitmap:
        output = BytesIO()
        bitmap.to_pil().convert("RGB").save(output, format="PNG", optimize=True)
        return output.getvalue()


def page_png(content: bytes, number: int) -> bytes:
    import pypdfium2 as pdfium

    with pdfium.PdfDocument(content) as document:
        if number < 1 or number > len(document):
            raise ValueError("catalog_page_out_of_range")
        with closing(document[number - 1]) as page:
            return render_page(page)
