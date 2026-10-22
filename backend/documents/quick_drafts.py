"""Quick drafts — any document from a name and one window.

The person asks for a quotation, cut sheet, plan or materials list before
walking every step. The document is composed by the same authority the
issued revision uses (engine price, documentary composition, renderers),
inside one transaction that is always rolled back: a missing price is
calculated with the company's current rules, missing preparation takes the
same advisory defaults the preparation form proposes, and nothing of it is
stored. The PDF says «Borrador» on every page; it is never an issued
document, never consumes a commercial number and never authorizes the shop.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from django.db import transaction

# kind → (document type, layout, download name)
QUICK_DOCUMENTS = {
    "QUOTE": ("DOC-01", None, "cotizacion-borrador"),
    "CUT": ("DOC-05", None, "hoja-de-corte-borrador"),
    "PLAN": ("DOC-03", "PLANO", "plano-borrador"),
    "MATERIALS": ("DOC-05", "OBRA", "materiales-borrador"),
}

PENDING_TERMS = "Por definir"


class _Discard(Exception):
    def __init__(self, content: bytes):
        super().__init__("quick draft rendered")
        self.content = content


def _key(bay_id, leaf_id) -> str:
    return f"{bay_id}|{leaf_id or ''}"


def _with_suggestions(position: dict) -> dict:
    """The preparation form's advisory defaults: stored values win per field,
    suggestions fill the rest (mirror of mergePreparationSuggestions)."""
    pending = {_key(item["bay_id"], item.get("leaf_id")): item
               for item in position.get("workshop_suggestions") or []}
    annotations = []
    for row in position.get("workshop_annotations") or []:
        suggestion = pending.pop(_key(row["bay_id"], row.get("leaf_id")), None)
        if suggestion:
            row = {**row, **{field: suggestion.get(field) for field in (
                "bottom_drain_holes_mm", "closing_points_perimeter_mm", "continuous_width_mm",
                "finish_class", "has_coupler") if row.get(field) is None}}
        annotations.append(row)
    stored_polishing = {_key(row["bay_id"], row.get("leaf_id")) for row in position.get("glass_polishing") or []}
    return {
        **position,
        "workshop_annotations": annotations + list(pending.values()),
        "glass_polishing": [*(position.get("glass_polishing") or []), *(
            item for item in position.get("polishing_suggestions") or []
            if _key(item["bay_id"], item.get("leaf_id")) not in stored_polishing)],
    }


def _first_option(position: dict, field: str, options: str) -> object:
    if position.get(field):
        return position[field]
    choices = position.get(options) or []
    return choices[0]["id"] if choices else None


def _prepare_inputs(*, org_id: UUID, actor_id: UUID, project_id: UUID) -> bool:
    """Ensure documentary inputs exist inside the discarded transaction.
    Returns True when commercial terms were not declared by a person."""
    from documents.repository import DocumentaryError, documentary_backend
    from documents.serializers import DocumentaryInputsSerializer
    from documents.service import prepare_documentary_inputs, save_documentary_inputs

    with documentary_backend():
        prepared = prepare_documentary_inputs(org_id=org_id, project_id=project_id)
    pending_terms = not str(prepared.get("payment_terms") or "").strip()
    positions = []
    for raw in prepared["positions"]:
        position = _with_suggestions(raw)
        positions.append({
            "position_id": position["position_id"],
            "calculation_hash": position["calculation_hash"],
            "location_tag": position.get("location_tag") or f"V{len(positions) + 1}",
            "manufacturing_placement_policy_id": _first_option(
                position, "manufacturing_placement_policy_id", "placement_options"),
            "handle_requirement_policy_id": _first_option(
                position, "handle_requirement_policy_id", "handle_options"),
            "reinforcement_cut_policy_id": _first_option(
                position, "reinforcement_cut_policy_id", "reinforcement_options"),
            "workshop_annotations": position.get("workshop_annotations") or [],
            "structural_inputs": position.get("structural_inputs") or [],
            "glass_polishing": position.get("glass_polishing") or [],
            "handle_intents": position.get("handle_intents") or [],
            # Undeclared accessories do not change cuts or profiles; the draft
            # lists none rather than inventing screws or sealant.
            "accessory_schedule": position.get("accessory_schedule")
            or {"coverage": "NONE_REQUIRED", "items": []},
            "legacy_handle_migration_confirmed": bool(position.get("legacy_handle_migration_confirmed")),
        })
    payload = json.loads(json.dumps({
        "payment_terms": prepared.get("payment_terms") or PENDING_TERMS,
        "quotation_valid_until": prepared.get("quotation_valid_until")
        or datetime.now(ZoneInfo("America/Santiago")).date(),
        "commercial_terms": prepared.get("commercial_terms") or {},
        "alternative_version_ids": prepared.get("alternative_version_ids") or [],
        "positions": positions,
    }, default=str))
    serializer = DocumentaryInputsSerializer(data=payload)
    if not serializer.is_valid():
        raise DocumentaryError(
            "quick_draft_preparation_incomplete",
            detail="A una ventana le falta un dato técnico para el borrador. Ábrela en el editor y revísala.",
        )
    save_documentary_inputs(org_id=org_id, actor_id=actor_id, project_id=project_id,
                            data=serializer.validated_data)
    return pending_terms


def _ensure_price(*, org_id: UUID, tenant, token, project: dict) -> str:
    """The applied price, or one calculated now with the company's rules."""
    from dekopen_engine.commercial import PricingError
    from documents.repository import DocumentaryError
    from pricing.service import pricing_public_detail

    if project.get("current_pricing_operation_id"):
        return str(project["current_pricing_operation_id"])
    from pricing.working import apply_for_issue
    try:
        return str(apply_for_issue(org_id, tenant, token.user_id, UUID(str(project['id'])),
            confirmed=True, email=token.email))
    except PricingError as error:
        raise DocumentaryError(error.code, detail=pricing_public_detail(error.code)) from error



def _compose(*, request, project_id: UUID, kind: str) -> bytes:
    from documents.renderers import render_pdf_document
    from documents.repository import DocumentaryError, decoded
    from documents.service import compose_revision
    from documents.views import documentary_scope
    from dekopen_engine.documentary_canonical import documentary_canonical_json_v1
    from projects import service as projects_service

    document_type, layout, _ = QUICK_DOCUMENTS[kind]
    with documentary_scope(request, ("OWNER", "ESTIMATOR")) as (token, tenant, org_id):
        project = projects_service.project_public(org_id, projects_service.project_row(org_id, project_id))
        if project.get("status") != "DRAFT":
            raise DocumentaryError(
                "revision_not_available",
                detail="Esta obra ya tiene una versión emitida; sus documentos están en Documentos.",
            )
        operation_id = _ensure_price(org_id=org_id, tenant=tenant, token=token, project=project)
        pending_terms = _prepare_inputs(org_id=org_id, actor_id=token.user_id, project_id=project_id)
        prepared = compose_revision(
            org_id=org_id, actor_id=token.user_id, project_id=project_id,
            pricing_operation_id=UUID(operation_id), sealed_at=datetime.now(timezone.utc),
            allow_incomplete_workshop=True,
        )
        snapshot = decoded(documentary_canonical_json_v1(prepared.snapshot).decode())
        snapshot["draft"] = True
        if pending_terms:
            snapshot["project"]["payment_terms"] = PENDING_TERMS
            snapshot["project"]["quotation_valid_until"] = None
        content, _ = render_pdf_document(document_type, snapshot, pdf_identifier="draft", layout=layout)
        return content


def render(request, project_id: UUID, kind: str) -> tuple[bytes, str]:
    """Render one quick draft; every write it needed is rolled back."""
    try:
        with transaction.atomic():
            raise _Discard(_compose(request=request, project_id=project_id, kind=kind))
    except _Discard as rendered:
        return rendered.content, QUICK_DOCUMENTS[kind][2]


__all__ = ["QUICK_DOCUMENTS", "render"]
