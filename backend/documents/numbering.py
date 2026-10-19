"""Commercial quotation numbering per company: N.º 1, 2, 3… by default.

A work receives its number once, atomically, when its first issuable preview
is prepared — that preview is the PDF that gets issued. Revisions keep the
number; repeating the preparation reuses it. Changing the prefix or the next
number only affects new assignments, never issued documents, and can never
collide with a number already given.
"""

from __future__ import annotations

from uuid import UUID

from authentication.errors import contract_error
from documents.repository import documentary_backend, one, rows

DEFAULT_PREFIX = "N.º "


def label(prefix: str | None, number: int | None) -> str | None:
    if not number:
        return None
    return f"{prefix if prefix is not None else DEFAULT_PREFIX}{number}"


def assign_commercial_number(org_id: UUID, project_id: UUID) -> int:
    """Idempotent: the work's existing number, or the next free one."""
    with documentary_backend():
        project = one(
            "SELECT commercial_number FROM public.projects WHERE id=%s AND org_id=%s FOR UPDATE",
            [str(project_id), str(org_id)],
            "project_not_found",
        )
        if project["commercial_number"]:
            return int(project["commercial_number"])
        # The organization row serializes concurrent assignments.
        org = one(
            "SELECT quotation_next_number FROM public.tenancy_organizations WHERE id=%s FOR UPDATE",
            [str(org_id)],
            "organization_not_found",
        )
        number = int(org["quotation_next_number"])
        taken = rows(
            "SELECT commercial_number FROM public.projects WHERE org_id=%s AND commercial_number >= %s "
            "ORDER BY commercial_number",
            [str(org_id), number],
        )
        for row in taken:
            if int(row["commercial_number"]) == number:
                number += 1
            elif int(row["commercial_number"]) > number:
                break
        one(
            "UPDATE public.projects SET commercial_number=%s WHERE id=%s AND org_id=%s RETURNING id",
            [number, str(project_id), str(org_id)],
            "project_not_found",
        )
        one(
            "UPDATE public.tenancy_organizations SET quotation_next_number=%s WHERE id=%s RETURNING id",
            [number + 1, str(org_id)],
            "organization_not_found",
        )
    return number


def settings(org_id: UUID) -> dict:
    org = one(
        "SELECT quotation_number_prefix, quotation_next_number FROM public.tenancy_organizations WHERE id=%s",
        [str(org_id)],
        "organization_not_found",
    )
    highest = rows(
        "SELECT max(commercial_number) AS highest FROM public.projects WHERE org_id=%s",
        [str(org_id)],
    )[0]["highest"]
    return {
        "prefix": org["quotation_number_prefix"],
        "next_number": int(org["quotation_next_number"]),
        "highest_assigned": int(highest) if highest else None,
        "example": label(org["quotation_number_prefix"], int(org["quotation_next_number"])),
    }


def save_settings(org_id: UUID, data: dict) -> dict:
    prefix = str(data.get("prefix", DEFAULT_PREFIX))
    if len(prefix) > 20 or any(char in prefix for char in "<>{}"):
        raise contract_error(400, "quotation_prefix_invalid", "El prefijo admite hasta 20 caracteres sin símbolos de código.")
    next_number = int(data["next_number"])
    current = settings(org_id)
    if current["highest_assigned"] and next_number <= current["highest_assigned"]:
        raise contract_error(
            409,
            "quotation_number_taken",
            f"El N.º {current['highest_assigned']} ya fue usado. El próximo número debe ser mayor.",
        )
    if next_number < 1:
        raise contract_error(400, "quotation_number_invalid", "El número debe ser mayor que cero.")
    with documentary_backend():
        one(
            "UPDATE public.tenancy_organizations SET quotation_number_prefix=%s, quotation_next_number=%s "
            "WHERE id=%s RETURNING id",
            [prefix, next_number, str(org_id)],
            "organization_not_found",
        )
    return settings(org_id)
