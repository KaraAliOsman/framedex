"""Quotation preparation from saved designs and the owner's pricing defaults.

This tool calculates a reviewable result. It never applies prices, issues a
revision or sends a document, and exposes only selling amounts to the model.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from authentication.errors import contract_error
from authentication.tenancy import MembershipRepository, resolve_tenant_context
from documents.repository import documentary_backend
from documents.service import prepare_documentary_inputs
from pricing.repository import commercial_backend, one
from pricing.serializers import PriceRequestSerializer
from pricing.service import preview
from projects import service


def _missing_summary(items):
    grouped = {}
    for item in items:
        key = (item["code"], item["detail"])
        if key not in grouped:
            grouped[key] = {"code": item["code"], "detail": item["detail"], "positions": []}
        if item.get("position_id"):
            grouped[key]["positions"].append(str(item["position_id"]))
    for item in grouped.values():
        if item["code"] == "pricing_not_applied":
            item["detail"] = "Revisa y aplica el precio preparado."
        if item["positions"]:
            item["detail"] += f" ({len(item['positions'])} posiciones)."
    return list(grouped.values())


def prepare(*, org_id, user_id, project_id):
    actor = resolve_tenant_context(MembershipRepository().list_active_for_user(user_id), str(org_id))
    if actor.active_organization.role not in {"OWNER", "ESTIMATOR"}:
        raise contract_error(403, "pricing_permission_denied", "El dueño o un estimador pueden preparar la cotización.")
    project = service.project_public(org_id, service.project_row(org_id, project_id), detail=True)
    request = None
    if project["pricing_current"]:
        currency = project["currency"]
        totals = {"net": project["total_price_net"], "tax": project["total_price_tax"], "gross": project["total_price_gross"]}
        lines = [{"index": position["position_index"], "location": position["location_tag"], "quantity": position["quantity"],
                  "net": position["price_net"]} for position in project["positions"]]
    else:
        with commercial_backend():
            rules = one("SELECT pricing_mode,default_margin_pct FROM public.pricing_rules WHERE org_id=%s", [org_id], "pricing_rules_not_found")
            organization = one("SELECT coalesce(quotation_currency,currency) AS currency FROM public.tenancy_organizations WHERE id=%s", [org_id])
            serializer = PriceRequestSerializer(data={"project_id": str(project_id), "pricing_mode": rules["pricing_mode"],
                "currency": organization["currency"], "effective_date": datetime.now(ZoneInfo("America/Santiago")).date().isoformat(),
                "target_margin": str(rules["default_margin_pct"]), "reason": "Cotización preparada con las preferencias de la empresa"})
            serializer.is_valid(raise_exception=True)
            request = dict(serializer.validated_data)
            calculated = preview(org_id, actor, {**request, "_actor_id": user_id}, simulate=True)
        currency = calculated["currency"]
        totals = {"net": calculated["project_net"], "tax": calculated["project_tax"], "gross": calculated["project_gross"]}
        positions = {position["position_index"]: position for position in project["positions"]}
        lines = [{"index": index, "location": positions[index]["location_tag"], "quantity": positions[index]["quantity"], "net": amount}
                 for index, amount in calculated["lines"]]
    with documentary_backend():
        documentary = prepare_documentary_inputs(org_id=org_id, project_id=project_id)
    return {"valid": True, "project_id": str(project_id), "project_code": project["code"], "project_name": project["name"],
            "currency": currency, "totals": totals, "lines": lines, "request": request,
            "basis": {"updated_at": project["updated_at"], "revision": project["current_revision"],
                      "positions": [{"id": str(position["id"]), "updated_at": position["updated_at"]}
                                    for position in project["positions"]]},
            "price_applied": bool(project["pricing_current"]), "missing": _missing_summary(documentary.get("missing", [])),
            "scope": "Cálculo con las preferencias de la empresa. Revisa el precio y la propuesta antes de emitir o enviar."}
