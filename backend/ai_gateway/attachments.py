"""Dirección final 05 · 3.1 — files attached from the copilot composer.

Common to every AI plan: PDF (text or scanned), PNG/JPEG/WebP, XLSX/CSV,
DOCX and TXT/Markdown. The server matrix below is the only authority on what
is accepted; a format is announced only with a real adapter.

Upload stores the private object, its SHA-256 and the extracted text parts
with their origin (página N, Hoja!A1:F1, fila N, párrafo N, tabla N · fila M,
línea N). Uploading, listing or reopening never calls the model or debits.
At run time `wire_parts` re-validates ownership and sends text parts plus the
visual pages (scans, drawings, images) inside the existing reservation —
there is no per-file charge. Coverage is declared: a truncated file is never
presented as a complete reading. Macros and active content are never run
(openpyxl reads values; DOCX is parsed as XML).
"""

from __future__ import annotations

import base64
import hashlib
import io
import zipfile
from typing import Any
from uuid import UUID, uuid4
from xml.etree import ElementTree

from ai_gateway.jobs import _ai_backend
from pricing.repository import rows

MAX_FILE_BYTES = 40 * 1024 * 1024
MAX_PER_TURN = 6
MAX_TEXT_CHARS_PER_FILE = 200_000
MAX_WIRE_TEXT_CHARS = 120_000
MAX_WIRE_IMAGES = 12
MAX_WIRE_IMAGE_BYTES = 12 * 1024 * 1024
MAX_PDF_PAGES = 600

MATRIX: list[dict[str, Any]] = [
    {"kind": "PDF", "label": "PDF con texto o escaneado", "extensions": [".pdf"],
     "reading": "Texto por página; las páginas escaneadas o con dibujo se leen como imagen.",
     "max_bytes": MAX_FILE_BYTES},
    {"kind": "IMAGE", "label": "Imagen PNG, JPEG o WebP", "extensions": [".png", ".jpg", ".jpeg", ".webp"],
     "reading": "Lectura visual. Una imagen sin cotas no produce medidas fabricables.",
     "max_bytes": MAX_FILE_BYTES},
    {"kind": "XLSX", "label": "Planilla XLSX", "extensions": [".xlsx", ".xlsm"],
     "reading": "Valores por hoja y celda. Las macros no se ejecutan.", "max_bytes": MAX_FILE_BYTES},
    {"kind": "CSV", "label": "CSV", "extensions": [".csv"], "reading": "Filas numeradas.",
     "max_bytes": MAX_FILE_BYTES},
    {"kind": "DOCX", "label": "Documento DOCX", "extensions": [".docx"],
     "reading": "Párrafos y tablas numerados.", "max_bytes": MAX_FILE_BYTES},
    {"kind": "TEXT", "label": "Texto o Markdown", "extensions": [".txt", ".md", ".markdown"],
     "reading": "Líneas numeradas.", "max_bytes": MAX_FILE_BYTES},
]
_BY_EXTENSION = {ext: item["kind"] for item in MATRIX for ext in item["extensions"]}
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class AttachmentError(Exception):
    def __init__(self, code: str, detail: str, status: int = 422):
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.status = status


def kind_of(file_name: str) -> str | None:
    lowered = file_name.lower()
    for extension, kind in _BY_EXTENSION.items():
        if lowered.endswith(extension):
            return kind
    return None


def _media_type(kind: str, file_name: str) -> str:
    lowered = file_name.lower()
    if kind == "IMAGE":
        return "image/png" if lowered.endswith(".png") else "image/webp" if lowered.endswith(".webp") else "image/jpeg"
    return {
        "PDF": "application/pdf",
        "XLSX": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "CSV": "text/csv",
        "DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "TEXT": "text/markdown" if lowered.endswith((".md", ".markdown")) else "text/plain",
    }[kind]


def _sniff(kind: str, content: bytes) -> bool:
    from ingest.extract import sniffed_kind

    if kind == "DOCX":
        if not content.startswith(b"PK\x03\x04"):
            return False
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                return "word/document.xml" in archive.namelist()
        except zipfile.BadZipFile:
            return False
    return sniffed_kind(kind, content)


def _docx_parts(content: bytes) -> list[dict]:
    """Paragraphs and table rows in document order; fields/macros ignored."""
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        info = archive.getinfo("word/document.xml")
        if info.file_size > 50 * 1024 * 1024:
            raise ValueError("docx_too_large")
        root = ElementTree.fromstring(archive.read(info))
    body = root.find(f"{_W}body")
    parts: list[dict] = []
    paragraph_number = 0
    table_number = 0
    for element in list(body) if body is not None else []:
        if element.tag == f"{_W}p":
            paragraph_number += 1
            text = "".join(node.text or "" for node in element.iter(f"{_W}t")).strip()
            if text:
                parts.append({"ref": f"párrafo {paragraph_number}", "text": text})
        elif element.tag == f"{_W}tbl":
            table_number += 1
            for row_number, row in enumerate(element.iter(f"{_W}tr"), start=1):
                cells = [
                    "".join(node.text or "" for node in cell.iter(f"{_W}t")).strip()
                    for cell in row.iter(f"{_W}tc")
                ]
                if any(cells):
                    parts.append({"ref": f"tabla {table_number} · fila {row_number}", "text": " | ".join(cells)})
    return parts


def _pdf_extract(content: bytes) -> dict:
    from ingest.catalog_pages import inventory

    import pypdfium2 as pdfium
    from contextlib import closing

    pages = inventory(content)
    parts: list[dict] = []
    with pdfium.PdfDocument(content) as document:
        for page in pages:
            with closing(document[page["page"] - 1]) as handle:
                with closing(handle.get_textpage()) as text:
                    literal = text.get_text_range().strip()
            if literal:
                parts.append({"ref": f"página {page['page']}", "text": literal})
    visual = [f"página {page['page']}" for page in pages if page["mode"] in ("scan", "mixed")]
    return {"parts": parts, "visual": visual, "unit": "página", "total": len(pages)}


def extract(kind: str, content: bytes) -> dict:
    """{parts, visual, coverage} — the origin of every value travels with it."""
    from ingest.extract import extract_tagged

    if kind == "PDF":
        found = _pdf_extract(content)
    elif kind == "IMAGE":
        found = {"parts": [], "visual": ["imagen"], "unit": "imagen", "total": 1}
    elif kind == "DOCX":
        parts = _docx_parts(content)
        found = {"parts": parts, "visual": [], "unit": "elemento", "total": len(parts)}
    else:
        tagged = extract_tagged(kind, content) or []
        parts = [{"ref": ref, "text": line} for line, ref in tagged]
        unit = {"XLSX": "fila", "CSV": "fila", "TEXT": "línea"}[kind]
        found = {"parts": parts, "visual": [], "unit": unit, "total": len(parts)}
    kept: list[dict] = []
    used = 0
    for part in found["parts"]:
        size = len(part["text"])
        if used + size > MAX_TEXT_CHARS_PER_FILE:
            break
        kept.append(part)
        used += size
    unprocessed = [part["ref"] for part in found["parts"][len(kept):]]
    return {
        "parts": kept,
        "visual": found["visual"],
        "coverage": {
            "unit": found["unit"],
            "total": found["total"],
            "processed": found["total"] - len(unprocessed) if kind != "PDF" else found["total"],
            "unprocessed": unprocessed[:200],
            "unprocessed_count": len(unprocessed),
        },
    }


def _extract(row: dict) -> dict:
    """The extract column as a dict (the repository returns jsonb as text)."""
    import json

    value = row.get("extract")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            value = {}
    return value if isinstance(value, dict) else {}


def _public(row: dict) -> dict:
    data = _extract(row)
    coverage = data.get("coverage") or {}
    return {
        "id": str(row["id"]),
        "file_name": row["file_name"],
        "media_type": row["media_type"],
        "kind": row["kind"],
        "byte_size": int(row["byte_size"]),
        "file_sha256": row["file_sha256"],
        "status": row["status"],
        "thread_id": str(row["thread_id"]) if row.get("thread_id") else None,
        "coverage": {
            "unit": str(coverage.get("unit") or ""),
            "total": int(coverage.get("total") or 0),
            "processed": int(coverage.get("processed") or 0),
            "unprocessed_count": int(coverage.get("unprocessed_count") or 0),
            "visual_count": len(data.get("visual") or []),
        },
        "preview": [
            {"ref": part["ref"], "text": part["text"][:240]} for part in (data.get("parts") or [])[:6]
        ],
        "created_at": row["created_at"],
    }


_COLUMNS = (
    "id, org_id, user_id, thread_id, file_name, media_type, kind, byte_size, file_sha256,"
    " storage_path, status, extract, created_at"
)


def upload(*, org_id: UUID, user_id: UUID, file_name: str, content: bytes,
           thread_id: UUID | None = None) -> dict:
    from documents.storage import SupabaseDocumentStorage
    from ingest.extract import safe_file_name

    if not (1 <= len(file_name) <= 200) or not safe_file_name(file_name):
        raise AttachmentError("ai_attachment_name_invalid", "El nombre del archivo no es válido.")
    kind = kind_of(file_name)
    if kind is None:
        raise AttachmentError(
            "ai_attachment_unsupported",
            "Formato no admitido. Usa PDF, PNG, JPEG, WebP, XLSX, CSV, DOCX, TXT o Markdown.",
        )
    if not content:
        raise AttachmentError("ai_attachment_empty", "El archivo está vacío.")
    if len(content) > MAX_FILE_BYTES:
        raise AttachmentError("ai_attachment_too_large", "El archivo supera 40 MB.", status=413)
    if not _sniff(kind, content):
        raise AttachmentError("ai_attachment_mismatch", "El contenido del archivo no coincide con su extensión.")
    if thread_id is not None:
        from ai_gateway import threads

        threads.require(org_id=org_id, user_id=user_id, thread_id=thread_id)
    status = "READY"
    try:
        extracted = extract(kind, content)
        if extracted["coverage"]["unprocessed_count"]:
            status = "PARTIAL"
    except Exception:  # noqa: BLE001 — an unreadable file is kept as evidence, never sent
        extracted = {"parts": [], "visual": [], "coverage": {"unit": "", "total": 0, "processed": 0,
                                                          "unprocessed": [], "unprocessed_count": 0}}
        status = "UNREADABLE"
    digest = hashlib.sha256(content).hexdigest()
    attachment_id = uuid4()
    storage_path = f"ai-attachments/{org_id}/{user_id}/{attachment_id}/{file_name}"
    storage = SupabaseDocumentStorage()
    storage.upload_immutable(storage_path, content, _media_type(kind, file_name))
    try:
        import json

        with _ai_backend():
            row = rows(
                f"INSERT INTO public.ai_attachments (id, org_id, user_id, thread_id, file_name, media_type,"
                f" kind, byte_size, file_sha256, storage_path, status, extract)"
                f" VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb) RETURNING {_COLUMNS}",
                [str(attachment_id), str(org_id), str(user_id), str(thread_id) if thread_id else None,
                 file_name, _media_type(kind, file_name), kind, len(content), digest, storage_path,
                 status, json.dumps(extracted, ensure_ascii=False)],
            )[0]
    except Exception:
        # A row that failed must not leave an orphaned private object.
        try:
            storage.delete_object(storage_path)
        except Exception:  # noqa: BLE001
            pass
        raise
    return _public(row)


def _owned(org_id: UUID, user_id: UUID, ids: list[UUID]) -> list[dict]:
    if not ids:
        return []
    found = rows(
        f"SELECT {_COLUMNS} FROM public.ai_attachments WHERE org_id=%s AND user_id=%s AND id = ANY(%s::uuid[])",
        [str(org_id), str(user_id), [str(item) for item in ids]],
    )
    by_id = {str(row["id"]): row for row in found}
    missing = [str(item) for item in ids if str(item) not in by_id]
    if missing:
        # Another person's or tenant's file is indistinguishable from a missing one.
        raise AttachmentError("ai_attachment_not_found", "Un adjunto no existe o no te pertenece.", status=404)
    return [by_id[str(item)] for item in ids]


def get(*, org_id: UUID, user_id: UUID, attachment_id: UUID) -> dict:
    return _public(_owned(org_id, user_id, [attachment_id])[0])


def detail(*, org_id: UUID, user_id: UUID, attachment_id: UUID) -> dict:
    row = _owned(org_id, user_id, [attachment_id])[0]
    data = _extract(row)
    return {**_public(row), "parts": (data.get("parts") or [])[:400], "visual": data.get("visual") or [],
            "unprocessed": (data.get("coverage") or {}).get("unprocessed") or []}


def content(*, org_id: UUID, user_id: UUID, attachment_id: UUID) -> tuple[bytes, str, str]:
    """Bytes for the citation viewer — reopening works after a signed URL
    would have expired because the API streams the private object."""
    from documents.storage import SupabaseDocumentStorage

    row = _owned(org_id, user_id, [attachment_id])[0]
    if not str(row["storage_path"]).startswith(f"ai-attachments/{org_id}/"):
        raise AttachmentError("ai_attachment_not_found", "El adjunto no existe.", status=404)
    raw = SupabaseDocumentStorage().download_bounded(row["storage_path"], MAX_FILE_BYTES)
    if raw is None:
        raise AttachmentError("ai_attachment_unavailable", "No se pudo leer el archivo.", status=503)
    return raw, row["media_type"], row["file_name"]


def list_for_thread(*, org_id: UUID, user_id: UUID, thread_id: UUID) -> list[dict]:
    found = rows(
        f"SELECT {_COLUMNS} FROM public.ai_attachments WHERE org_id=%s AND user_id=%s AND thread_id=%s"
        " ORDER BY created_at",
        [str(org_id), str(user_id), str(thread_id)],
    )
    return [_public(row) for row in found]


def bind_thread(*, org_id: UUID, user_id: UUID, ids: list[UUID], thread_id: UUID) -> None:
    if not ids:
        return
    with _ai_backend():
        rows(
            "UPDATE public.ai_attachments SET thread_id=%s WHERE org_id=%s AND user_id=%s"
            " AND id = ANY(%s::uuid[]) AND thread_id IS NULL RETURNING id",
            [str(thread_id), str(org_id), str(user_id), [str(item) for item in ids]],
        )


def seal(*, org_id: UUID, user_id: UUID, ids: list[UUID]) -> list[dict]:
    """The sealed reference a turn carries: id, name, hash, kind, coverage."""
    if len(ids) > MAX_PER_TURN:
        raise AttachmentError("ai_attachment_limit", f"Adjunta hasta {MAX_PER_TURN} archivos por mensaje.")
    sealed = []
    for row in _owned(org_id, user_id, ids):
        if row["status"] == "UNREADABLE":
            raise AttachmentError("ai_attachment_unreadable", f"No se pudo leer «{row['file_name']}»; quítalo para continuar.")
        public = _public(row)
        sealed.append({key: public[key] for key in ("id", "file_name", "kind", "file_sha256", "status", "coverage")})
    return sealed


def wire_parts(*, org_id: UUID, user_id: UUID, sealed: list[dict]) -> tuple[list[dict], list[dict]]:
    """(provider parts, manifest). Re-validates ownership and hash at read
    time; declares what was not sent so a partial read never looks complete."""
    from documents.storage import SupabaseDocumentStorage

    if not sealed:
        return [], []
    found = _owned(org_id, user_id, [UUID(str(item["id"])) for item in sealed])
    storage = SupabaseDocumentStorage()
    parts: list[dict] = []
    manifest: list[dict] = []
    text_budget = MAX_WIRE_TEXT_CHARS
    image_budget = MAX_WIRE_IMAGES
    byte_budget = MAX_WIRE_IMAGE_BYTES
    for row, seal_entry in zip(found, sealed):
        if row["file_sha256"] != seal_entry.get("file_sha256"):
            raise AttachmentError("ai_attachment_changed", "Un adjunto cambió desde que se envió el mensaje.", status=409)
        data = _extract(row)
        label = row["file_name"]
        sent: list[str] = []
        skipped: list[str] = list((data.get("coverage") or {}).get("unprocessed") or [])
        for part in data.get("parts") or []:
            if len(part["text"]) > text_budget:
                skipped.append(part["ref"])
                continue
            text_budget -= len(part["text"])
            parts.append({"ref": f"{label} · {part['ref']}", "text": part["text"]})
            sent.append(part["ref"])
        visual = list(data.get("visual") or [])
        if visual:
            raw = storage.download_bounded(row["storage_path"], MAX_FILE_BYTES)
            if raw is None:
                skipped += visual
            elif row["kind"] == "IMAGE":
                if image_budget > 0 and len(raw) <= byte_budget:
                    image_budget -= 1
                    byte_budget -= len(raw)
                    parts.append({"ref": f"{label} · imagen", "mime": row["media_type"],
                                  "data": base64.b64encode(raw).decode("ascii")})
                    sent.append("imagen")
                else:
                    skipped.append("imagen")
            else:
                from ingest.catalog_pages import page_png

                for ref in visual:
                    number = int(ref.rsplit(" ", 1)[-1])
                    if image_budget <= 0:
                        skipped.append(ref)
                        continue
                    png = page_png(raw, number)
                    if len(png) > byte_budget:
                        skipped.append(ref)
                        continue
                    image_budget -= 1
                    byte_budget -= len(png)
                    parts.append({"ref": f"{label} · {ref}", "mime": "image/png",
                                  "data": base64.b64encode(png).decode("ascii")})
                    sent.append(ref + " (imagen)")
        manifest.append({
            "id": str(row["id"]), "file_name": label, "kind": row["kind"], "file_sha256": row["file_sha256"],
            "sent": sent[:400], "not_processed": skipped[:200], "complete": not skipped,
        })
    return parts, manifest


def text_evidence(*, org_id: UUID, user_id: UUID, sealed: list[dict]) -> list[str]:
    """Literal text of the sealed attachments — the numbers the run may cite."""
    if not sealed:
        return []
    found = _owned(org_id, user_id, [UUID(str(item["id"])) for item in sealed])
    return [part["text"] for row in found for part in _extract(row).get("parts") or []]


def matrix() -> dict:
    return {"formats": MATRIX, "max_per_turn": MAX_PER_TURN, "max_file_bytes": MAX_FILE_BYTES}


__all__ = [
    "AttachmentError", "MATRIX", "bind_thread", "content", "detail", "extract", "get", "kind_of",
    "list_for_thread", "matrix", "seal", "text_evidence", "upload", "wire_parts",
]
