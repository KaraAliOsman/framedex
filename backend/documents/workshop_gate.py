"""Commercial issue can retain explicitly pending physical preparation."""

from decimal import Decimal
from uuid import UUID

from dekopen_engine.cutting import MissingStockAuthority, AmbiguousStockAuthority
from dekopen_engine.inspection_models import InspectorConfigurationError
from documents.repository import DocumentaryError, load_manufacturing_policies
from engine_api.inspection_repository import InspectorRepository


def pending(field, action, system_id):
    return {"field": field, "rule": "workshop_preparation", "origin": None, "action": action,
        "required_for": ["MANUFACTURABLE", "MACHINE_READY"], "resource": "systems", "row_id": str(system_id)}


def workshop_inputs(position, result, system_id, org_id, color, stocks):
    missing = []
    inspector = cutting = policies = None
    try:
        inspector = InspectorRepository().load(system_id, org_id)
    except InspectorConfigurationError:
        missing.append(pending("inspection", "Completa los parámetros de inspección antes de fabricar.", system_id))
    try:
        cutting = stocks.for_result(result, system_id, org_id, color)
    except (MissingStockAuthority, AmbiguousStockAuthority):
        missing.append(pending("stock", "Completa los largos y referencias de barra antes de fabricar.", system_id))
    fields = ("manufacturing_placement_policy_id", "handle_requirement_policy_id", "reinforcement_cut_policy_id")
    for field in fields:
        if position.get(field) is None:
            missing.append(pending(field, "Completa esta regla de taller antes de fabricar.", system_id))
    if all(position.get(field) is not None for field in fields):
        policies = load_manufacturing_policies(system_id=system_id, org_id=org_id,
            placement_id=UUID(str(position[fields[0]])), handle_id=UUID(str(position[fields[1]])),
            reinforcement_id=UUID(str(position[fields[2]])))
    return inspector, cutting, policies, missing


def quote_only_position(position, *, system_id, tree, result, bom, drawing_plan, system_facts,
                        calculation_hash, catalog_gate, process_facts, measurements):
    """Commercial facts and engine evidence, without manufactured placeholders."""
    return {"id": str(position["id"]), "position_index": int(position["position_index"]),
        "quantity": int(position["quantity"]), "typology": str(position["typology"]), "system_id": system_id,
        "width_mm": Decimal(str(position["width_mm"])), "height_mm": Decimal(str(position["height_mm"])),
        "color_interior": str(position["color_interior"]), "color_exterior": str(position["color_exterior"]),
        "location_tag": str(position["location_tag"] or ""), "system_name": str(position["system_name"]),
        "is_demo": bool(system_facts.get("is_demo", False)), "price_net": Decimal(str(position["price_net"])),
        "discount_pct": str(position["discount_pct"]), "parametric_tree": tree,
        **({"resolved_finish": result.finish.model_dump(mode="python")} if result.finish is not None else {}),
        **({"drawing_plan": drawing_plan} if drawing_plan else {}),
        **({"opening_leaves": bom["opening_leaves"]} if bom.get("opening_leaves") else {}),
        **({"commercial_hardware": [{"handle_name": item.resolution.handle_name,
            "handle_color": item.resolution.handle_color, "options": item.resolution.options,
            "synthetic": item.resolution.synthetic} for item in result.hardware_items if item.resolution is not None]}
            if any(item.resolution is not None for item in result.hardware_items) else {}),
        "calculation_hash": calculation_hash, "process_facts": process_facts,
        "catalog_authority_gate": catalog_gate, "measurements": measurements,
        "workshop_preparation": "PENDING"}


def require_workshop(missing):
    if missing:
        raise DocumentaryError("catalog_use_incomplete", detail="Completa la preparación de taller antes de fabricar.",
            extra={"required_level": "MANUFACTURABLE", "pending": missing})
