"""Document ingestion service: upload → extract → review → confirm.

The mandate's trust boundary: candidates are review data only. Nothing becomes
a position — let alone a BOM — without the estimator's explicit confirm, and
every confirmed item carries the system's real authority (system_id + glass)
chosen by the human, not inferred by the parser."""

from __future__ import annotations

import json
from uuid import UUID, uuid4


from authentication.errors import contract_error
from documents.repository import documentary_backend
from documents.storage import SupabaseDocumentStorage
from ingest.extract import extract, kind_for
from ingest.parser import candidates_from_rows, candidates_from_text
from jobs import service as jobs_service
from pricing.repository import rows
from projects import service as projects_service

MAX_UPLOAD_BYTES = 15_000_000
JOB_TYPE = "ingest.document.extract"


class ImportError_(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _public(row: dict) -> dict:
    def _stamp(value):
        return value.isoformat() if hasattr(value, "isoformat") else value

    return {
        "id": str(row["id"]),
        "file_name": row["file_name"],
        "kind": row["kind"],
        "status": row["status"],
        "candidates": row["candidates"] or [],
        "warnings": row["warnings"] or [],
        "result": row["result"] or [],
        "error_code": row["error_code"],
        "created_at": _stamp(row["created_at"]),
        "updated_at": _stamp(row["updated_at"]),
    }


def _get(org_id: UUID, project_id: UUID, import_id: UUID, *, backend: bool = False) -> dict:
    def _fetch():
        return rows(
            "SELECT * FROM public.document_imports "
            "WHERE org_id=%s AND project_id=%s AND id=%s",
            [str(org_id), str(project_id), str(import_id)],
        )

    found = _fetch() if not backend else _fetch_under_backend(_fetch)
    if not found:
        raise ImportError_("import_not_found")
    return found[0]


def _fetch_under_backend(fetch):
    with documentary_backend():
        return fetch()


def create_import(
    *, org_id: UUID, project_id: UUID, actor_id: UUID, file_name: str,
    content: bytes, content_type: str,
) -> dict:
    projects_service.project_row(org_id, project_id)
    kind = kind_for(file_name)
    if kind is None:
        raise contract_error(
            422,
            "import_kind_unsupported",
            "Formato no soportado. Sube un PDF, XLSX o imagen (png, jpg, webp).",
        )
    if not content or len(content) > MAX_UPLOAD_BYTES:
        raise contract_error(
            422, "import_file_invalid", "El archivo está vacío o supera 15 MB."
        )
    import_id = uuid4()
    storage_path = f"imports/{org_id}/{project_id}/{import_id}/{file_name}"
    SupabaseDocumentStorage().upload_immutable(
        storage_path, content, content_type or "application/octet-stream"
    )
    with documentary_backend():
        row = rows(
            "INSERT INTO public.document_imports("
            "id, org_id, project_id, file_name, kind, storage_path, created_by)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING *",
            [str(import_id), str(org_id), str(project_id), file_name, kind,
             storage_path, str(actor_id)],
        )[0]
        job, _ = jobs_service.enqueue(
            org_id=org_id,
            job_type=JOB_TYPE,
            payload={"import_id": str(import_id)},
            idempotency_key=f"import-extract:{import_id}",
            created_by=actor_id,
        )
    return {"import": _public(row), "job": job}


def list_imports(*, org_id: UUID, project_id: UUID) -> dict:
    projects_service.project_row(org_id, project_id)
    found = rows(
        "SELECT * FROM public.document_imports "
        "WHERE org_id=%s AND project_id=%s ORDER BY created_at DESC, id DESC",
        [str(org_id), str(project_id)],
    )
    return {"imports": [_public(row) for row in found]}


def get_import(*, org_id: UUID, project_id: UUID, import_id: UUID) -> dict:
    return {"import": _public(_get(org_id, project_id, import_id))}


def extract_for_import(*, org_id: UUID, import_id: UUID, actor_id: UUID) -> dict:
    """The worker body: bytes → text → candidates. Deterministic first (PDF
    text layer, XLSX rows); a text-less source goes through the vision_ocr
    capability — debited under the org wallet, audited, idempotent on the
    import id so a job retry never double-charges."""
    found = rows(
        "SELECT * FROM public.document_imports WHERE id=%s AND org_id=%s",
        [str(import_id), str(org_id)],
    )
    if not found:
        raise ImportError_("import_not_found")
    row = found[0]
    with documentary_backend():
        rows(
            "UPDATE public.document_imports SET status='EXTRACTING', updated_at=now() "
            "WHERE id=%s AND status='UPLOADED'",
            [str(import_id)],
        )
    content = SupabaseDocumentStorage().download(row["storage_path"])
    warnings: list[str] = []
    audit_id = None
    try:
        text, sheet_rows = extract(row["kind"], content)
    except Exception:
        text, sheet_rows = "", None
        warnings.append("import.source_parse_failed")
    if sheet_rows is not None:
        candidates = candidates_from_rows(sheet_rows)
    elif text.strip():
        candidates = candidates_from_text(text)
    else:
        candidates = []
    if not candidates:
        # No deterministic extraction — the vision capability reads the
        # document. The operation key makes a retried job replay its stored
        # response instead of double-charging the wallet.
        from ai_gateway.service import ProviderError, invoke

        try:
            vision = invoke(
                org_id=org_id,
                user_id=actor_id,
                capability="vision_ocr",
                operation_key=f"import:{import_id}:vision",
                input_payload={
                    "file_name": row["file_name"],
                    "kind": row["kind"],
                    "storage_path": row["storage_path"],
                },
            )
            audit_id = vision["audit_id"]
            vision_candidates = candidates_from_text(str(vision["output"]))
            if vision_candidates:
                candidates = vision_candidates
            else:
                warnings.append("import.vision_no_candidates")
        except ProviderError as error:
            warnings.append(f"import.vision_failed:{error.code}")
        except Exception as error:
            code = getattr(error, "contract_code", "ai_gateway_error")
            warnings.append(f"import.vision_failed:{code}")
    if not candidates:
        warnings.append("import.no_candidates")
    with documentary_backend():
        updated = rows(
            "UPDATE public.document_imports SET status='REVIEW_READY', "
            "candidates=%s::jsonb, warnings=%s::jsonb, audit_id=%s, updated_at=now() "
            "WHERE id=%s RETURNING *",
            [
                json.dumps(candidates),
                json.dumps(warnings),
                audit_id,
                str(import_id),
            ],
        )[0]
    return {"import": _public(updated), "candidate_count": len(candidates)}


def confirm_import(
    *, org_id: UUID, project_id: UUID, import_id: UUID, items: list[dict]
) -> dict:
    """Human confirm — the only path from candidate to position. Each item is
    an explicit estimator decision (opening + system + glass); per-item errors
    are collected, never silently dropped. Replay returns the stored result."""
    row = _get(org_id, project_id, import_id)
    if row["status"] == "CONFIRMED":
        return {"import": _public(row), "created": row["result"], "errors": []}
    if row["status"] not in ("REVIEW_READY", "FAILED"):
        raise contract_error(
            409,
            "import_not_review_ready",
            "La importación aún está procesándose. Espera a que termine.",
        )
    candidate_keys = {candidate.get("key") for candidate in row["candidates"] or []}
    created: list[dict] = []
    errors: list[dict] = []
    for item in items:
        key = str(item["key"])
        if candidate_keys and key not in candidate_keys:
            errors.append({"key": key, "code": "import_item_unknown"})
            continue
        design = {
            "system_id": str(item["system_id"]),
            "nominal_width_mm": item["width_mm"],
            "nominal_height_mm": item["height_mm"],
            "color": item["color"],
            "parametric_tree": {
                "id": "imported",
                "type": "BAY",
                "opening_type": item["opening_type"],
                "glass_thickness_mm": item["glass_thickness_mm"],
                "glass_spec": item["glass_spec"],
            },
        }
        try:
            position = projects_service.save_position(
                org_id,
                project_id,
                {
                    "location_tag": item["label"],
                    "quantity": item["quantity"],
                    "design": design,
                },
            )
            created.append({"key": key, "position_id": str(position["id"])})
        except Exception as error:
            errors.append({"key": key, "code": getattr(error, "contract_code", "save_failed")})
    if not created and errors:
        return {"import": _public(row), "created": [], "errors": errors}
    with documentary_backend():
        updated = rows(
            "UPDATE public.document_imports SET status='CONFIRMED', result=%s::jsonb, "
            "updated_at=now() WHERE id=%s AND status<>'CONFIRMED' RETURNING *",
            [json.dumps(created), str(import_id)],
        )
        if updated:
            row = updated[0]
        else:
            row = _get(org_id, project_id, import_id, backend=True)
    return {"import": _public(row), "created": created, "errors": errors}
