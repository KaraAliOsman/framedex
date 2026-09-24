"""Catalog ingestion service: upload → extract → review → confirm.

Same trust boundary as document ingestion: candidates are review data only.
Nothing becomes a profile_articles row — let alone catalog authority — without
the estimator's explicit confirm, and the target system must belong to the
organization (articles on a shared/global system would leak to every tenant).
"""

from __future__ import annotations

import json
from uuid import UUID, uuid4

from django.db import DatabaseError, transaction

from authentication.errors import contract_error
from documents.repository import documentary_backend
from documents.storage import SupabaseDocumentStorage
from ingest.catalog_parser import ROLES, parse_catalog_lines
from ingest.extract import extract, kind_for
from jobs import service as jobs_service
from pricing.repository import rows

MAX_UPLOAD_BYTES = 15_000_000
MAX_CANDIDATES = 200
JOB_TYPE = "ingest.catalog.extract"

# Missing manufacturing data stays UNKNOWN (NULL) — a supplier document that
# does not state a stock length, welding loss or weight must never gain a
# fabricated value here; downstream consumers refuse or flag instead.


def _numeric_or_none(value: object) -> str | None:
    return None if value is None else str(value)


class CatalogImportError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, str):
        return json.loads(value) if value else []
    return list(value)


def _public(row: dict) -> dict:
    def _stamp(value):
        return value.isoformat() if hasattr(value, "isoformat") else value

    return {
        "id": str(row["id"]),
        "file_name": row["file_name"],
        "kind": row["kind"],
        "status": row["status"],
        "system_id": str(row["system_id"]) if row["system_id"] else None,
        "candidates": _as_list(row["candidates"]),
        "warnings": _as_list(row["warnings"]),
        "result": _as_list(row["result"]),
        "error_code": row["error_code"],
        "created_at": _stamp(row["created_at"]),
        "updated_at": _stamp(row["updated_at"]),
    }


def _get(org_id: UUID, import_id: UUID) -> dict:
    found = rows(
        "SELECT * FROM public.catalog_imports WHERE org_id=%s AND id=%s",
        [str(org_id), str(import_id)],
    )
    if not found:
        raise CatalogImportError("catalog_import_not_found")
    return found[0]


def create_catalog_import(
    *,
    org_id: UUID,
    actor_id: UUID,
    file_name: str,
    content: bytes,
    content_type: str,
) -> dict:
    kind = kind_for(file_name)
    if kind is None:
        raise contract_error(
            422,
            "catalog_import_kind_unsupported",
            "Formato no soportado. Sube un PDF, XLSX o imagen (png, jpg, webp).",
        )
    if not content or len(content) > MAX_UPLOAD_BYTES:
        raise contract_error(
            422, "catalog_import_file_invalid", "El archivo está vacío o supera 15 MB."
        )
    if len(file_name) > 200 or len(file_name) == 0:
        raise contract_error(
            422,
            "catalog_import_file_invalid",
            "El nombre del archivo es demasiado largo o está vacío.",
        )
    import_id = uuid4()
    storage_path = f"catalog-imports/{org_id}/{import_id}/{file_name}"
    storage = SupabaseDocumentStorage()
    storage.upload_immutable(storage_path, content, content_type or "application/octet-stream")
    try:
        with transaction.atomic():
            with documentary_backend():
                row = rows(
                    "INSERT INTO public.catalog_imports("
                    "id, org_id, file_name, kind, storage_path, created_by)"
                    " VALUES (%s,%s,%s,%s,%s,%s) RETURNING *",
                    [str(import_id), str(org_id), file_name, kind, storage_path, str(actor_id)],
                )[0]
            # job_runs is a service-owned table — service_role only, inside the
            # atomic so row and job commit together.
            with jobs_service.job_backend():
                job, _ = jobs_service.enqueue(
                    org_id=org_id,
                    job_type=JOB_TYPE,
                    payload={"import_id": str(import_id)},
                    idempotency_key=f"catalog-extract:{import_id}",
                    created_by=actor_id,
                )
    except Exception:
        # The row or the enqueue failed — the immutable upload would orphan.
        try:
            storage.delete_object(storage_path)
        except Exception:
            pass
        raise
    return {"import": _public(row), "job": job}


def list_catalog_imports(*, org_id: UUID) -> dict:
    found = rows(
        "SELECT * FROM public.catalog_imports WHERE org_id=%s ORDER BY created_at DESC, id DESC",
        [str(org_id)],
    )
    return {"imports": [_public(row) for row in found]}


def get_catalog_import(*, org_id: UUID, import_id: UUID) -> dict:
    return {"import": _public(_get(org_id, import_id))}


def extract_catalog_import(*, org_id: UUID, import_id: UUID, actor_id: UUID) -> dict:
    """The worker body: bytes → article candidates. Deterministic first; a
    text-less source goes through the catalog_compile capability — debited
    under the org wallet, audited, idempotent on the import id."""
    found = rows(
        "SELECT * FROM public.catalog_imports WHERE id=%s AND org_id=%s",
        [str(import_id), str(org_id)],
    )
    if not found:
        raise CatalogImportError("catalog_import_not_found")
    row = found[0]
    # Claim in its own transaction so the provider call below can commit its
    # audit+debit independently of candidate writes — a retry never re-bills.
    with transaction.atomic():
        with documentary_backend():
            claimed = rows(
                "UPDATE public.catalog_imports SET status='EXTRACTING', updated_at=now() "
                "WHERE id=%s AND status='UPLOADED' RETURNING *",
                [str(import_id)],
            )
    if not claimed:
        current = rows(
            "SELECT * FROM public.catalog_imports WHERE id=%s",
            [str(import_id)],
        )[0]
        if current["status"] in ("REVIEW_READY", "CONFIRMED"):
            return {
                "import": _public(current),
                "candidate_count": len(_as_list(current["candidates"])),
            }
        if current["status"] != "EXTRACTING":
            raise CatalogImportError("catalog_import_status_invalid")
    content = SupabaseDocumentStorage().download(row["storage_path"])
    warnings: list[str] = []
    audit_id = None
    try:
        text, sheet_rows = extract(row["kind"], content)
    except Exception:
        text, sheet_rows = "", None
        warnings.append("catalog.source_parse_failed")
    lines: list[str] = []
    if sheet_rows is not None:
        for sheet_row in sheet_rows:
            joined = " ".join(
                str(cell) for cell in sheet_row if cell is not None and str(cell).strip()
            )
            if joined:
                lines.append(joined)
    elif text.strip():
        lines = [line for line in text.splitlines() if line.strip()]
    candidates = parse_catalog_lines(lines)
    if not candidates:
        from ai_gateway.service import ProviderError, invoke

        try:
            vision = invoke(
                org_id=org_id,
                user_id=actor_id,
                capability="catalog_compile",
                operation_key=f"catalog:{import_id}:compile",
                input_payload={
                    # Stable identity only — the provider adapter mints a fresh
                    # signed URL at wire time, so the audited input hash
                    # survives a job retry and replays the paid compile.
                    "file_name": row["file_name"],
                    "kind": row["kind"],
                    "storage_path": row["storage_path"],
                    "target": "profile_articles",
                },
            )
            audit_id = vision["audit_id"]
            vision_candidates = parse_catalog_lines(str(vision["output"]).splitlines())
            if vision_candidates:
                candidates = vision_candidates
            else:
                warnings.append("catalog.compile_no_candidates")
        except ProviderError as error:
            warnings.append(f"catalog.compile_failed:{error.code}")
        except Exception as error:
            code = getattr(error, "contract_code", "ai_gateway_error")
            warnings.append(f"catalog.compile_failed:{code}")
    if not candidates:
        warnings.append("catalog.no_candidates")
    if len(candidates) > MAX_CANDIDATES:
        candidates = candidates[:MAX_CANDIDATES]
        warnings.append("catalog.candidates_capped")
    with transaction.atomic():
        with documentary_backend():
            updated = rows(
                "UPDATE public.catalog_imports SET status='REVIEW_READY', "
                "candidates=%s::jsonb, warnings=%s::jsonb, audit_id=%s, updated_at=now() "
                "WHERE id=%s AND status='EXTRACTING' RETURNING *",
                [
                    json.dumps(candidates, default=str),
                    json.dumps(warnings),
                    audit_id,
                    str(import_id),
                ],
            )
    if not updated:
        current = rows(
            "SELECT * FROM public.catalog_imports WHERE id=%s",
            [str(import_id)],
        )[0]
        if current["status"] in ("REVIEW_READY", "CONFIRMED"):
            return {
                "import": _public(current),
                "candidate_count": len(_as_list(current["candidates"])),
            }
        raise CatalogImportError("catalog_import_status_invalid")
    return {"import": _public(updated[0]), "candidate_count": len(candidates)}


def mark_catalog_import_failed(*, org_id: UUID, import_id: UUID, code: str) -> None:
    with transaction.atomic():
        with documentary_backend():
            # Only an in-flight import may fail — a stale retry must never
            # overwrite a REVIEW_READY or CONFIRMED outcome.
            rows(
                "UPDATE public.catalog_imports SET status='FAILED', "
                "error_code=%s, updated_at=now() WHERE id=%s AND org_id=%s "
                "AND status IN ('UPLOADED','EXTRACTING')",
                [code[:80], str(import_id), str(org_id)],
            )


def confirm_catalog_import(
    *, org_id: UUID, import_id: UUID, system_id: UUID, items: list[dict]
) -> dict:
    """Human confirm — the only path from candidate to catalog authority.

    One transaction: the import row is locked FOR UPDATE, each article inserts
    under its own savepoint, and per-key outcomes accumulate in ``result`` —
    so a retry replays committed state, a partial failure stays retryable,
    and CONFIRMED only seals once every submitted key has an outcome."""
    with transaction.atomic():
        with documentary_backend():
            found = rows(
                "SELECT * FROM public.catalog_imports WHERE id=%s AND org_id=%s FOR UPDATE",
                [str(import_id), str(org_id)],
            )
        if not found:
            raise CatalogImportError("catalog_import_not_found")
        row = found[0]
        if row["status"] == "CONFIRMED":
            return {
                "import": _public(row),
                "created": _as_list(row["result"]),
                "errors": [],
            }
        if row["status"] not in ("REVIEW_READY", "FAILED"):
            raise contract_error(
                409,
                "catalog_import_not_review_ready",
                "La importación aún está procesándose. Espera a que termine.",
            )
        # A retried confirm continues the same target: earlier keys already
        # became articles in the stored system, so switching systems now would
        # split one import across two catalogs.
        if row["system_id"] and str(row["system_id"]) != str(system_id):
            raise contract_error(
                409,
                "catalog_system_changed",
                "La importación ya tiene artículos en otro sistema; "
                "confirma sobre el mismo sistema.",
            )
        # Articles on a global/shared system would be visible to every tenant
        # (the select policy opens global systems to all members) — the target
        # must be a system the organization owns.
        system = rows(
            "SELECT id, material FROM public.profile_systems WHERE id=%s AND org_id=%s",
            [str(system_id), str(org_id)],
        )
        if not system:
            raise contract_error(
                422,
                "catalog_system_not_tenant",
                "El sistema destino debe pertenecer a tu organización.",
            )
        material = system[0]["material"]
        candidate_keys = {candidate.get("key") for candidate in _as_list(row["candidates"])}
        created = _as_list(row["result"])
        done = {str(entry.get("key")) for entry in created}
        errors: list[dict] = []
        for item in items:
            key = str(item["key"])
            if key in done:
                continue
            if key not in candidate_keys:
                errors.append({"key": key, "code": "catalog_item_unknown"})
                continue
            sku = str(item["sku"]).strip().upper()
            role = str(item["role"]).upper()
            name = str(item.get("name") or "").strip() or sku
            if role not in ROLES:
                errors.append({"key": key, "code": "catalog_role_invalid"})
                continue
            try:
                # The tenant's own claims write the article — same RLS path
                # catalog CRUD uses; the per-item savepoint keeps a rejected
                # row (singleton role, constraint) from aborting the batch.
                with transaction.atomic():
                    inserted = rows(
                        "INSERT INTO public.profile_articles("
                        "system_id, org_id, sku, name, role, material, face_width_mm,"
                        " commercial_length_mm, welding_loss_mm, reinforcement_sku,"
                        " weight_kg_m, steel_weight_kg_m)"
                        " VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                        " ON CONFLICT (system_id, sku) DO NOTHING"
                        " RETURNING id",
                        [
                            str(system_id),
                            str(org_id),
                            sku,
                            name,
                            role,
                            material,
                            str(item["face_width_mm"]),
                            _numeric_or_none(item.get("commercial_length_mm")),
                            _numeric_or_none(item.get("welding_loss_mm")),
                            (str(item["reinforcement_sku"]).strip() or None)
                            if item.get("reinforcement_sku")
                            else None,
                            _numeric_or_none(item.get("weight_kg_m")),
                            _numeric_or_none(item.get("steel_weight_kg_m")),
                        ],
                    )
            except DatabaseError as error:
                code = (
                    "catalog_singleton_role_conflict"
                    if "catalog_singleton_role_conflict" in str(error)
                    else "catalog_insert_failed"
                )
                errors.append({"key": key, "code": code})
                continue
            if not inserted:
                errors.append({"key": key, "code": "catalog_sku_conflict"})
                continue
            created.append({"key": key, "article_id": str(inserted[0]["id"])})
            done.add(key)
        if errors:
            # Retryable: persist what was created so the next confirm only
            # attempts the still-unresolved keys.
            with documentary_backend():
                updated = rows(
                    "UPDATE public.catalog_imports SET result=%s::jsonb, "
                    "system_id=%s, updated_at=now() WHERE id=%s RETURNING *",
                    [json.dumps(created), str(system_id), str(import_id)],
                )[0]
            return {
                "import": _public(updated),
                "created": created,
                "errors": errors,
            }
        with documentary_backend():
            updated = rows(
                "UPDATE public.catalog_imports SET status='CONFIRMED', "
                "result=%s::jsonb, system_id=%s, updated_at=now() "
                "WHERE id=%s RETURNING *",
                [json.dumps(created), str(system_id), str(import_id)],
            )[0]
    return {"import": _public(updated), "created": created, "errors": []}
