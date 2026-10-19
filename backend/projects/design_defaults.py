"""Usual design values inherited company → project → window.

They seed new windows only. A window keeps its own design (the exception),
existing positions are never rewritten when a usual value changes, and issued
revisions keep their frozen snapshot. Every value is checked against the
catalog the organization can read; nothing here manufactures a number.
"""

from __future__ import annotations

import json
from uuid import UUID

from authentication.errors import contract_error
from documents.repository import documentary_backend, one
from engine_api.repository import SystemParamsRepository
from pricing.repository import json_text, rows

KEYS = ("system_id", "color", "glass_article_sku")


def _decoded(value) -> dict:
    if isinstance(value, str):
        value = json.loads(value or "{}")
    return value if isinstance(value, dict) else {}


def clean_stored(value) -> dict:
    """Stored values as the API presents them (unknown keys dropped)."""
    decoded = _decoded(value)
    return {key: str(decoded[key]) for key in KEYS if decoded.get(key)}


def clean(org_id, value: dict | None) -> dict:
    """Keep known, non-empty values; reject a system outside the tenant view."""
    result: dict[str, str] = {}
    for key in KEYS:
        raw = (value or {}).get(key)
        if raw is None:
            continue
        text = str(raw).strip()
        if not text:
            continue
        if len(text) > 80:
            raise contract_error(400, "design_default_invalid", "Un valor habitual es demasiado largo.")
        result[key] = text
    if "system_id" in result:
        try:
            wanted = UUID(result["system_id"])
        except ValueError as error:
            raise contract_error(400, "design_default_invalid", "La serie elegida no es válida.") from error
        visible = {system.id for system in SystemParamsRepository().list_visible(UUID(str(org_id)))}
        if wanted not in visible:
            raise contract_error(
                400, "design_default_system_unavailable", "La serie elegida no está disponible en tus catálogos."
            )
        result["system_id"] = str(wanted)
    return result


def company_defaults(org_id) -> dict:
    row = one(
        "SELECT design_defaults, updated_at FROM public.tenancy_organizations WHERE id=%s",
        [str(org_id)],
        "organization_not_found",
    )
    return {"values": _decoded(row.get("design_defaults")), "updated_at": row.get("updated_at")}


def save_company_defaults(org_id, data: dict) -> dict:
    values = clean(org_id, data.get("values"))
    with documentary_backend():
        one(
            "UPDATE public.tenancy_organizations SET design_defaults=%s::jsonb, updated_at=clock_timestamp() "
            "WHERE id=%s RETURNING id",
            [json_text(values), str(org_id)],
            "organization_not_found",
        )
    return company_defaults(org_id)


def effective(org_id, project: dict | None, company: dict | None = None) -> dict:
    """Each usual value with its origin, for display and for new windows."""
    company_values = company if company is not None else company_defaults(org_id)["values"]
    project_values = _decoded((project or {}).get("design_defaults"))
    result = {}
    for key in KEYS:
        if project_values.get(key):
            result[key] = {"value": project_values[key], "source": "project"}
        elif company_values.get(key):
            result[key] = {"value": company_values[key], "source": "company"}
    return result


def project_defaults(org_id, project_id) -> dict:
    found = rows(
        "SELECT design_defaults FROM public.projects WHERE id=%s AND org_id=%s",
        [project_id, org_id],
    )
    return _decoded(found[0]["design_defaults"]) if found else {}
