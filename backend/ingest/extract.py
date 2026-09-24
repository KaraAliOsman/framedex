"""Source readers: bytes → schedule text/rows for the deterministic parser.

PDF keeps a real text layer (pypdf); XLSX reads every sheet's rows. IMAGE and
scanned PDFs have no local text — those flow to the vision_ocr capability
through the AI gateway, debited under the org's wallet."""

from __future__ import annotations

from io import BytesIO


def pdf_text(content: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def xlsx_rows(content: bytes) -> list[list[object]]:
    from openpyxl import load_workbook

    workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
    rows: list[list[object]] = []
    for sheet in workbook.worksheets:
        for row in sheet.iter_rows(values_only=True):
            rows.append(list(row))
    workbook.close()
    return rows


def extract(kind: str, content: bytes) -> tuple[str, list[list[object]] | None]:
    """Return (text, rows|None) the schedule parser understands."""
    if kind == "PDF":
        return pdf_text(content), None
    if kind == "XLSX":
        sheet_rows = xlsx_rows(content)
        text = "\n".join(
            " ".join(str(cell) for cell in row if cell is not None and str(cell).strip())
            for row in sheet_rows
        )
        return text, sheet_rows
    return "", None


def kind_for(file_name: str) -> str | None:
    lowered = file_name.lower()
    if lowered.endswith(".pdf"):
        return "PDF"
    if lowered.endswith(".xlsx") or lowered.endswith(".xlsm"):
        return "XLSX"
    if lowered.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return "IMAGE"
    return None
