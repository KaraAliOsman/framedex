"""Role projection at the HTTP boundary; sealed commercial evidence stays exact."""

from copy import deepcopy

COST_ROLES = {"OWNER", "WORKSHOP_MANAGER"}
COST_REASON = "Los costos de compra son confidenciales. El dueño o jefe de taller puede consultarlos."

# Estimators receive an allowlist of selling evidence. An internal authority
# may contain arbitrary nested rates, so recursively deleting known cost keys
# would let a new rate field escape. Never expose it through this projection.
SELLING_FIELDS = {
    "id", "state", "project_id", "project_code", "project_name", "client_name",
    "revision_code", "discount_pct", "pricing_mode", "segment", "currency",
    "lines", "line_detail", "services", "document_extra_prices", "extras", "extras_net",
    "project_net", "project_tax", "project_gross", "reason", "requested_by",
    "requested_by_email", "approved_by", "approved_at", "created_at",
}
SERVICE_FIELDS = {
    "code", "name", "scope", "kind", "quantity", "unit", "source", "synthetic",
    "width_mm", "height_mm", "bay_id", "leaf_id", "sku", "installation", "zone",
    "currency", "selling_rate", "total_price", "unit_price", "amount", "rounding",
}
LINE_FIELDS = {"position_index", "quantity", "unit_price", "discount_pct", "base_net", "sublines"}


def price_visibility(value, role):
    if role in COST_ROLES:
        return {**value, "costs_visible": True, "costs_reason": None}
    public = deepcopy({key: item for key, item in value.items() if key in SELLING_FIELDS})
    public["services"] = [
        {key: item for key, item in service.items() if key in SERVICE_FIELDS}
        for service in public.get("services") or []
    ]
    public["line_detail"] = [
        {**{key: item for key, item in entry.items() if key in LINE_FIELDS and key != "sublines"},
         **({"sublines": [{key: item for key, item in line.items() if key in SERVICE_FIELDS | {"net"}}
                          for line in entry["sublines"]]} if "sublines" in entry else {})}
        for entry in public.get("line_detail") or []
    ]
    public.update({
        "costs_visible": False, "costs_reason": COST_REASON, "total_cost": None,
        "cost_lines": [], "positions_breakdown": [], "authorities": [],
        "rules": {key: item for key, item in (value.get("rules") or {}).items()
                  if key in {"default_margin_pct", "tax_rate_pct"}},
    })
    return public


def batch_visibility(value, role):
    if role in COST_ROLES:
        return {**value, "costs_visible": True, "costs_reason": None}
    return {
        "currency": value["currency"], "costs_visible": False, "costs_reason": COST_REASON,
        "items": [
            {**{key: item for key, item in entry.items() if key in {
                "position_id", "index", "ok", "error_code", "error", "quantity"}},
             **{key: None for key in ("unit_cost_before", "unit_cost_after",
                                     "line_cost_before", "line_cost_after")}}
            for entry in value["items"]
        ],
    }
