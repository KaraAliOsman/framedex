"""Additional physical loss enters the ordinary sealed OC/send/receive chain."""

from decimal import Decimal

from documents.repository import one
from purchasing.service import confirm_order_type_batch
from production.field import reject


def replacement_order(org, actor, version_id, case, data):
    if not data.get("requirement_id") or not data.get("quantity"):
        reject("Elige el requerimiento sellado y la cantidad física faltante.")
    requirement = one(
        "SELECT order_type::text FROM public.purchase_requirement_lines WHERE org_id=%s AND project_version_id=%s AND id=%s",
        [org, version_id, data["requirement_id"]],
        "purchase_requirement_not_found",
    )
    outputs, _ = confirm_order_type_batch(
        org_id=org,
        actor_id=actor,
        version_id=version_id,
        order_type=requirement["order_type"],
        confirmed=True,
        quantities={str(data["requirement_id"]): Decimal(data["quantity"])},
        field_replacement=case,
    )
    if len(outputs) != 1:
        reject("La compra adicional debe tener un proveedor elegible.")
    return {"purchase_order_id": outputs[0]["id"], "purchase_code": outputs[0]["order_code"]}
