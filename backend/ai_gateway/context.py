"""Typed context projections for the contextual assistant (M3 §3).

Every surface maps to a bounded, curated view of the organization's data —
never a client-supplied context blob and never a table dump. All queries run
under the caller's RLS (the endpoint wraps the whole pipeline in
authenticated_rls_context), so a projection can only see what the caller's
role already sees, and it can never reach another tenant's rows.
"""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from authentication.errors import ContractAPIException
from pricing.repository import rows

MAX_LIST = 20
MAX_FIELD = 120

# Surface → required ref names. A surface that names a ref without a matching
# tenant-scoped row raises the same 404 the feature's own endpoint would.
REQUIRED_REFS: dict[str, tuple[str, ...]] = {
    "dashboard": (),
    "projects": (),
    "project": ("project_id",),
    "position": ("position_id",),
    "quotation": ("project_id",),
    "catalog": (),
    "production": (),
    "work_order": ("work_order_id",),
    "clients": (),
    "purchasing": (),
    "settings": (),
}


class _ContextError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _jsonb(value: Any) -> Any:
    """Raw cursors return jsonb columns as text — decode before the shape
    checks or a real dict/list payload silently collapses to None."""
    if isinstance(value, str):
        try:
            return json.loads(value, parse_float=Decimal)
        except json.JSONDecodeError:
            return None
    return value


def _cut(value: Any, limit: int = MAX_FIELD) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text[:limit] if text else None


def _positive(value: Any) -> bool:
    try:
        return Decimal(str(value)) > 0
    except (InvalidOperation, ValueError):
        return False


def _ref(refs: dict[str, Any], name: str) -> UUID:
    raw = refs.get(name)
    try:
        return UUID(str(raw))
    except (TypeError, ValueError):
        raise _ContextError("ai_context_ref_invalid") from None


def _organization(org_id: UUID) -> dict:
    result = rows(
        "SELECT name, subscription_tier, credits_balance, currency "
        "FROM public.tenancy_organizations WHERE id=%s",
        [org_id],
    )
    if not result:
        raise _ContextError("ai_context_not_found")
    org = result[0]
    return {
        "name": _cut(org["name"]),
        "plan": _cut(org.get("subscription_tier")),
        "credits_balance": _cut(org.get("credits_balance")),
        "currency": _cut(org.get("currency")),
    }


def _dashboard(org_id: UUID) -> dict:
    counts = rows(
        "SELECT "
        "(SELECT count(*) FROM public.projects WHERE org_id=%(o)s) AS projects, "
        "(SELECT count(*) FROM public.project_positions WHERE org_id=%(o)s) AS positions, "
        "(SELECT count(*) FROM public.orders WHERE org_id=%(o)s "
        " AND order_type='WORKSHOP_OT' AND status NOT IN ('COMPLETED','INSTALLED'))"
        " AS work_orders_open, "
        "(SELECT count(*) FROM public.clients WHERE org_id=%(o)s AND is_active)"
        " AS clients, "
        "(SELECT count(*) FROM public.profile_systems WHERE org_id=%(o)s OR "
        " (org_id IS NULL AND is_global)) AS profile_systems",
        {"o": org_id},
    )
    recent = rows(
        "SELECT code, name, client_name, status "
        "FROM public.projects WHERE org_id=%s ORDER BY updated_at DESC LIMIT 5",
        [org_id],
    )
    return {
        "counts": {key: int(value) for key, value in (counts[0] if counts else {}).items()},
        "recent_projects": [
            {
                "code": _cut(p["code"]),
                "name": _cut(p["name"]),
                "client": _cut(p["client_name"]),
                "status": _cut(p["status"]),
            }
            for p in recent
        ],
    }


def _projects(org_id: UUID) -> dict:
    result = rows(
        "SELECT p.code, p.name, p.client_name, p.status, "
        "(SELECT count(*) FROM public.project_positions pp "
        " WHERE pp.project_id=p.id AND pp.org_id=%s) AS positions "
        "FROM public.projects p WHERE p.org_id=%s "
        "ORDER BY p.updated_at DESC LIMIT %s",
        [org_id, org_id, MAX_LIST],
    )
    return {
        "projects": [
            {
                "code": _cut(p["code"]),
                "name": _cut(p["name"]),
                "client": _cut(p["client_name"]),
                "status": _cut(p["status"]),
                "positions": int(p["positions"]),
            }
            for p in result
        ],
        "truncated": len(result) == MAX_LIST,
    }


def _project_row(org_id: UUID, project_id: UUID) -> dict:
    result = rows(
        "SELECT id, code, name, client_name, status, current_revision, "
        "total_price_net, total_price_tax, total_price_gross "
        "FROM public.projects WHERE id=%s AND org_id=%s",
        [project_id, org_id],
    )
    if not result:
        raise _ContextError("ai_context_not_found")
    return result[0]


def _payments(org_id: UUID, project_id: UUID) -> dict:
    result = rows(
        "SELECT count(*) AS count, COALESCE(SUM(amount),0) AS collected "
        "FROM public.project_payments "
        "WHERE org_id=%s AND project_id=%s AND voided_at IS NULL",
        [org_id, project_id],
    )
    return {
        "payments_count": int(result[0]["count"]),
        "payments_collected": _cut(result[0]["collected"]),
    }


def _project(org_id: UUID, refs: dict) -> dict:
    project = _project_row(org_id, _ref(refs, "project_id"))
    positions = rows(
        "SELECT position_index, location_tag, typology, width_mm, height_mm "
        "FROM public.project_positions WHERE org_id=%s AND project_id=%s "
        "ORDER BY position_index LIMIT %s",
        [org_id, project["id"], MAX_LIST],
    )
    versions = rows(
        "SELECT revision_code, documentary_complete, production_allowed "
        "FROM public.project_versions WHERE org_id=%s AND project_id=%s "
        "ORDER BY emitted_at DESC LIMIT 1",
        [org_id, project["id"]],
    )
    context: dict[str, Any] = {
        "id": str(project["id"]),
        "code": _cut(project["code"]),
        "name": _cut(project["name"]),
        "client": _cut(project["client_name"]),
        "status": _cut(project["status"]),
        "current_revision": _cut(project["current_revision"]),
        "totals": {
            "net": _cut(project["total_price_net"]),
            "tax": _cut(project["total_price_tax"]),
            "gross": _cut(project["total_price_gross"]),
        },
        "payments": _payments(org_id, project["id"]),
        "positions": [
            {
                "index": int(p["position_index"]),
                "location": _cut(p["location_tag"]),
                "typology": _cut(p["typology"]),
                "width_mm": _cut(p["width_mm"]),
                "height_mm": _cut(p["height_mm"]),
            }
            for p in positions
        ],
    }
    if versions:
        context["latest_version"] = {
            "revision": _cut(versions[0]["revision_code"]),
            "documentary_complete": bool(versions[0]["documentary_complete"]),
            "production_allowed": bool(versions[0]["production_allowed"]),
        }
    return context


def _position(org_id: UUID, refs: dict) -> dict:
    result = rows(
        "SELECT p.id, p.project_id, p.position_index, p.location_tag, p.typology, "
        "p.width_mm, p.height_mm, p.parametric_tree, "
        "s.code AS system_code, s.name AS system_name, s.material, "
        "pr.code AS project_code, pr.name AS project_name "
        "FROM public.project_positions p "
        "LEFT JOIN public.profile_systems s ON s.id = p.system_id "
        "JOIN public.projects pr ON pr.id = p.project_id AND pr.org_id = p.org_id "
        "WHERE p.id=%s AND p.org_id=%s",
        [_ref(refs, "position_id"), org_id],
    )
    if not result:
        raise _ContextError("ai_context_not_found")
    position = result[0]
    tree = _jsonb(position.get("parametric_tree"))
    assembly = tree.get("assembly") if isinstance(tree, dict) else None
    modules = assembly.get("modules") if isinstance(assembly, dict) else None
    couplings = assembly.get("couplings") if isinstance(assembly, dict) else None
    if modules is None and isinstance(tree, dict) and tree:
        # Single-module positions persist the module's own tree without an
        # assembly envelope — surface one module carrying the position's dims.
        modules = [
            {
                "single": True,
                "width_mm": position["width_mm"],
                "height_mm": position["height_mm"],
            }
        ]
    return {
        "id": str(position["id"]),
        "project": {
            "id": str(position["project_id"]),
            "code": _cut(position["project_code"]),
            "name": _cut(position["project_name"]),
        },
        "index": int(position["position_index"]),
        "location": _cut(position["location_tag"]),
        "typology": _cut(position["typology"]),
        "system": {
            "code": _cut(position["system_code"]),
            "name": _cut(position["system_name"]),
            "material": _cut(position["material"]),
        },
        "width_mm": _cut(position["width_mm"]),
        "height_mm": _cut(position["height_mm"]),
        "modules": (
            [
                {
                    "id": _cut(m.get("id"), 40),
                    "width_mm": _cut(m.get("width_mm")),
                    "height_mm": _cut(m.get("height_mm")),
                    **({"single": True} if m.get("single") else {}),
                }
                for m in modules[:MAX_LIST]
                if isinstance(m, dict)
            ]
            if isinstance(modules, list)
            else None
        ),
        "couplings": len(couplings) if isinstance(couplings, list) else None,
    }


def _quotation(org_id: UUID, refs: dict) -> dict:
    project = _project_row(org_id, _ref(refs, "project_id"))
    versions = rows(
        "SELECT revision_code, documentary_complete, production_allowed, "
        "bom_hash IS NOT NULL AS frozen "
        "FROM public.project_versions WHERE org_id=%s AND project_id=%s "
        "ORDER BY emitted_at DESC LIMIT 3",
        [org_id, project["id"]],
    )
    # Document counts deliberately don't query document_artifacts: the sealed
    # evidence table is revoked from `authenticated` and served only through
    # documentary_backend — a caller-scoped projection must not proxy it.
    return {
        "project": {
            "id": str(project["id"]),
            "code": _cut(project["code"]),
            "name": _cut(project["name"]),
        },
        "current_revision": _cut(project["current_revision"]),
        "totals": {
            "net": _cut(project["total_price_net"]),
            "tax": _cut(project["total_price_tax"]),
            "gross": _cut(project["total_price_gross"]),
        },
        "payments": _payments(org_id, project["id"]),
        "versions": [
            {
                "revision": _cut(v["revision_code"]),
                "documentary_complete": bool(v["documentary_complete"]),
                "production_allowed": bool(v["production_allowed"]),
                "frozen": bool(v["frozen"]),
            }
            for v in versions
        ],
    }


def _catalog(org_id: UUID, refs: dict) -> dict:
    """§06-H catalog assistant context. Without a system ref: every visible
    system plus the review-queue signals a triage answer needs. With
    system_id: the workspace aggregate projected down — readiness ladder
    with exact blockers (explain), provenance/review state (evidence),
    compact entity rosters (relationships, dedupe) and revisions."""
    raw = refs.get("system_id")
    if raw:
        return _catalog_system(org_id, _ref(refs, "system_id"))
    systems = rows(
        "SELECT id, code, name, material::text AS material, is_global, "
        "is_active AS active, is_global AS read_only, data_provenance::text AS provenance, "
        "review_pending "
        "FROM public.profile_systems "
        "WHERE org_id=%s OR (org_id IS NULL AND is_global) "
        "ORDER BY code LIMIT %s",
        [org_id, MAX_LIST],
    )
    return {
        "systems": [
            {
                "id": str(s["id"]),
                "code": _cut(s["code"]),
                "name": _cut(s["name"]),
                "material": _cut(s["material"]),
                "is_global": bool(s["is_global"]),
                "read_only": bool(s["read_only"]),
                "provenance": _cut(s["provenance"]),
                "review_pending": bool(s["review_pending"]),
                "active": bool(s["active"]),
            }
            for s in systems
        ],
        "truncated": len(systems) == MAX_LIST,
    }


def _catalog_system(org_id: UUID, system_id: UUID) -> dict:
    from catalogs.readiness import catalog_readiness
    from catalogs.service import system_workspace

    try:
        workspace = system_workspace(org_id, system_id)
    except ContractAPIException as error:
        if getattr(error, "status_code", None) == 404:
            raise _ContextError("ai_context_not_found") from None
        raise
    system = workspace["system"]

    def entities(rows_: list[dict], fields: tuple[str, ...]) -> list[dict]:
        return [
            {name: _cut(row.get(name)) if not isinstance(row.get(name), bool) else row.get(name) for name in fields}
            for row in rows_[:MAX_LIST]
        ]

    review_queue = [
        {"kind": kind, "id": str(row.get("id")), "label": _cut(row.get("sku") or row.get("code") or row.get("name"))}
        for kind, rows_ in (
            ("system", [system]),
            ("article", workspace["articles"]),
            ("bead", workspace["beads"]),
            ("kit", workspace["kits"]),
        )
        for row in rows_
        if row.get("review_pending") or row.get("data_provenance") == "LEGACY_UNVERIFIED"
    ][:MAX_LIST]

    try:
        readiness = catalog_readiness(system_id, org_id)
    except Exception:
        readiness = None

    return {
        "system": {
            "id": str(system["id"]),
            "code": _cut(system.get("code")),
            "name": _cut(system.get("name")),
            "material": _cut(system.get("material")),
            "manufacturer": _cut(system.get("manufacturer")),
            "family": _cut(system.get("family")),
            "read_only": bool(system.get("read_only")),
            "provenance": _cut(system.get("data_provenance")),
            "review_pending": bool(system.get("review_pending")),
            "revision": _cut(system.get("revision")),
        },
        "readiness": readiness,
        "counts": {
            "articles": len(workspace["articles"]),
            "beads": len(workspace["beads"]),
            "kits": len(workspace["kits"]),
            "reinforcements": len(workspace["reinforcements"]),
            "purchase_mappings": len(workspace["purchase_mappings"]),
            "sections_declared": sum(
                1 for a in workspace["articles"] if a.get("section")
            ),
            "sections_dxf": sum(
                1
                for a in workspace["articles"]
                if isinstance(a.get("section"), dict)
                and a["section"].get("source") == "DXF_REFERENCE"
            ),
        },
        "articles": entities(
            workspace["articles"],
            ("id", "sku", "name", "role", "review_pending",
             "revision", "section_revision", "section_revised_by"),
        ),
        "beads": entities(workspace["beads"], ("id", "sku", "name")),
        "kits": entities(workspace["kits"], ("id", "code", "label", "review_pending")),
        "purchase_mappings": entities(
            workspace["purchase_mappings"],
            ("id", "profile_article_id", "commercial_sku", "manufacturer_name", "supplier_name"),
        ),
        "reinforcements": entities(
            workspace["reinforcements"], ("id", "sku", "commercial_sku", "name")
        ),
        "process_profile": (
            {
                "code": _cut(workspace["process_profile"].get("code")),
                "label": _cut(workspace["process_profile"].get("label")),
                "version": _cut(workspace["process_profile"].get("version")),
            }
            if workspace.get("process_profile")
            else None
        ),
        "review_queue": review_queue,
        "truncated": any(
            len(workspace[key]) > MAX_LIST
            for key in ("articles", "beads", "kits", "purchase_mappings", "reinforcements")
        ),
    }


def _production(org_id: UUID) -> dict:
    orders = rows(
        "SELECT o.id, o.order_code, o.status::text AS status, "
        "COUNT(s.id) AS steps_total, "
        "COUNT(s.id) FILTER (WHERE s.status='DONE') AS steps_done "
        "FROM public.orders o "
        "LEFT JOIN public.production_steps s ON s.order_id=o.id "
        "WHERE o.org_id=%s AND o.order_type='WORKSHOP_OT' "
        "GROUP BY o.id ORDER BY o.created_at DESC LIMIT %s",
        [org_id, MAX_LIST],
    )
    return {
        "work_orders": [
            {
                "id": str(o["id"]),
                "code": _cut(o["order_code"]),
                "status": _cut(o["status"]),
                "steps_done": int(o["steps_done"]),
                "steps_total": int(o["steps_total"]),
            }
            for o in orders
        ],
        "truncated": len(orders) == MAX_LIST,
    }


def _work_order(org_id: UUID, refs: dict) -> dict:
    order_id = _ref(refs, "work_order_id")
    order = rows(
        "SELECT o.order_code, o.status::text AS status, "
        "o.payload_json->'optimization'->'stock_reservations' AS reservations "
        "FROM public.orders o "
        "WHERE o.id=%s AND o.org_id=%s AND o.order_type='WORKSHOP_OT'",
        [order_id, org_id],
    )
    if not order:
        raise _ContextError("ai_context_not_found")
    steps = rows(
        "SELECT sequence, code, label, status FROM public.production_steps "
        "WHERE org_id=%s AND order_id=%s ORDER BY sequence LIMIT %s",
        [org_id, order_id, MAX_LIST * 2],
    )
    reservations = _jsonb(order[0].get("reservations"))
    shortages = (
        sum(1 for entry in reservations if isinstance(entry, dict) and _positive(entry.get("short")))
        if isinstance(reservations, list)
        else 0
    )
    return {
        "id": str(order_id),
        "order_code": _cut(order[0]["order_code"]),
        "status": _cut(order[0]["status"]),
        "shortages": shortages,
        "steps": [
            {
                "sequence": int(s["sequence"]),
                "code": _cut(s["code"]),
                "label": _cut(s["label"]),
                "status": _cut(s["status"]),
            }
            for s in steps
        ],
    }


def _clients(org_id: UUID) -> dict:
    result = rows(
        "SELECT name, rut FROM public.clients "
        "WHERE org_id=%s AND is_active ORDER BY name LIMIT %s",
        [org_id, MAX_LIST],
    )
    return {
        "clients": [{"name": _cut(c["name"]), "rut": _cut(c["rut"])} for c in result],
        "truncated": len(result) == MAX_LIST,
    }


def _purchasing(org_id: UUID) -> dict:
    orders = rows(
        "SELECT order_code, order_type::text AS order_type, status::text AS status, "
        "supplier_name FROM public.orders "
        "WHERE org_id=%s AND order_type::text LIKE 'SUPPLIER%%' "
        "ORDER BY created_at DESC LIMIT %s",
        [org_id, MAX_LIST],
    )
    return {
        "supplier_orders": [
            {
                "code": _cut(o["order_code"]),
                "type": _cut(o["order_type"]),
                "status": _cut(o["status"]),
                "supplier": _cut(o["supplier_name"]),
            }
            for o in orders
        ],
        "truncated": len(orders) == MAX_LIST,
    }


def _settings(org_id: UUID) -> dict:
    # The organization block already carries what the settings surface can
    # answer about; no extra projection needed.
    return {}


_BUILDERS = {
    "dashboard": _dashboard,
    "projects": _projects,
    "project": _project,
    "position": _position,
    "quotation": _quotation,
    "catalog": _catalog,
    "production": _production,
    "work_order": _work_order,
    "clients": _clients,
    "purchasing": _purchasing,
    "settings": _settings,
}

_REF_BUILDERS = {"project", "position", "quotation", "work_order", "catalog"}


def build_context(org_id: UUID, surface: str, refs: dict | None) -> dict:
    """Surface → bounded typed projection. The client supplies only the
    surface name and identity refs; every value the model sees is queried
    server-side under the caller's RLS context."""
    builder = _BUILDERS.get(surface)
    if builder is None:
        raise _ContextError("ai_surface_unknown")
    refs = dict(refs or {})
    if surface in _REF_BUILDERS:
        context = builder(org_id, refs)
    else:
        context = builder(org_id)
    context["surface"] = surface
    context["organization"] = _organization(org_id)
    context["context_version"] = 1
    return context


__all__ = ["REQUIRED_REFS", "build_context", "_ContextError"]
