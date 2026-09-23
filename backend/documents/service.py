"""Atomic APPLIED-pricing freeze into immutable documentary revisions."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import TypeVar
from uuid import NAMESPACE_URL, UUID, uuid5

from django.db import connection

from dekopen_engine.documentary_canonical import (
    DOCUMENTARY_CANONICAL_VERSION,
    bom_hash_v1,
    documentary_canonical_json_v1,
    snapshot_sha256_v1,
)
from dekopen_engine.geometry import GeometryComputation, compute_geometry
from dekopen_engine.inspection_models import (
    InspectionMode,
    InspectorInput,
    InspectorResult,
    RuleEvaluationStatus,
)
from dekopen_engine.inspector import inspect
from dekopen_engine.manufacturing import (
    HandleIntentV1,
    HandleRequirementPolicyV1,
    ManufacturingFactsV1,
    ManufacturingPlacementPolicyV1,
    project_coupling_facts_v1,
    project_manufacturing_facts_v1,
)
from dekopen_engine.manufacturing_trace import (
    GeometryManufacturingTraceV1,
    PlacementDomain,
    SemanticLeafTraceV1,
    TracePointV1,
)
from dekopen_engine.models import EngineResult, ProfileRole
from dekopen_engine.product import PlanGeometry
from dekopen_engine.purchasing import (
    HardwareSelectionV1,
    PositionPurchaseInputV1,
    project_purchase_requirements_v1,
)
from dekopen_engine.snapshot import calculation_response
from engine_api.adapter import (
    evaluate_assembly_from_api,
    normalized_root_from_api,
    parse_product_model,
)
from engine_api.cutting_repository import CuttingRepository
from engine_api.inspection_repository import InspectorRepository
from engine_api.repository import SystemParamsRepository
from pricing.repository import commercial_backend

from documents.repository import (
    DocumentaryError,
    PurchaseAuthorities,
    _handle_policy,
    _placement_policy,
    accessory_schedule,
    decoded,
    documentary_backend,
    glass_polishing,
    handle_intents,
    json_text,
    load_manufacturing_policies,
    load_purchase_authorities,
    one,
    rows,
    structural_inputs,
    workshop_annotations,
)

D = Decimal
T = TypeVar("T")


def _json_object(value: object, code: str) -> dict[str, object]:
    parsed = decoded(value)
    if not isinstance(parsed, dict) or not all(isinstance(key, str) for key in parsed):
        raise DocumentaryError(code)
    return parsed


def _json_array(value: object, code: str) -> list[object]:
    parsed = decoded(value)
    if not isinstance(parsed, list):
        raise DocumentaryError(code)
    return parsed


def _indexed_amounts(value: object, code: str) -> dict[int, Decimal]:
    if not isinstance(value, list):
        raise DocumentaryError(code)
    result: dict[int, Decimal] = {}
    try:
        for pair in value:
            if not isinstance(pair, list) or len(pair) != 2:
                raise DocumentaryError(code)
            index = int(pair[0])
            if index in result:
                raise DocumentaryError(code)
            result[index] = D(str(pair[1]))
    except (TypeError, ValueError) as error:
        if isinstance(error, DocumentaryError):
            raise
        raise DocumentaryError(code) from error
    return result


def _stored_money(value: Decimal) -> Decimal:
    return value.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def _pricing_state_matches(
    project: dict[str, object], positions: list[dict[str, object]],
    request: dict[str, object], snapshot: dict[str, object], result: dict[str, object],
) -> None:
    costs = _indexed_amounts(snapshot.get("cost_lines"), "invalid_applied_pricing_snapshot")
    prices = _indexed_amounts(result.get("lines"), "invalid_applied_pricing_result")
    indexes = {int(position["position_index"]) for position in positions}
    if set(costs) != indexes or set(prices) != indexes:
        raise DocumentaryError("applied_pricing_binding_mismatch")
    discount = D(str(request.get("discount_pct")))
    for position in positions:
        index = int(position["position_index"])
        if (
            D(str(position["cost_net"])) != _stored_money(costs[index])
            or D(str(position["price_net"])) != _stored_money(prices[index])
            or D(str(position["discount_pct"])) != discount
        ):
            raise DocumentaryError("applied_pricing_binding_mismatch")
    expected_cost = _stored_money(sum(costs.values(), D("0")))
    expected_net = _stored_money(D(str(result.get("project_net"))))
    expected_tax = _stored_money(D(str(result.get("project_tax"))))
    expected_gross = _stored_money(D(str(result.get("project_gross"))))
    if (
        D(str(project["total_cost_net"])) != expected_cost
        or D(str(project["total_price_net"])) != expected_net
        or D(str(project["total_price_tax"])) != expected_tax
        or D(str(project["total_price_gross"])) != expected_gross
    ):
        raise DocumentaryError("applied_pricing_binding_mismatch")


def _module_scoped(
    items: list[T], module_id: str | None, *id_fields: str
) -> list[T]:
    """Items whose ids are namespaced "<module_id>|<id>" belong to one module;
    feed each module's classic computation only its own, prefix stripped."""
    if module_id is None:
        return items
    prefix = f"{module_id}|"
    scoped: list[T] = []
    for item in items:
        anchor = getattr(item, id_fields[0], None)
        if not isinstance(anchor, str) or not anchor.startswith(prefix):
            continue
        updates = {}
        for field in id_fields:
            value = getattr(item, field, None)
            updates[field] = (
                value[len(prefix):]
                if isinstance(value, str) and value.startswith(prefix)
                else value
            )
        scoped.append(item.model_copy(update=updates))
    return scoped


def _missing_handle_intents(
    trace: GeometryManufacturingTraceV1,
    handle_policy: HandleRequirementPolicyV1,
    intents: list[HandleIntentV1],
) -> bool:
    available = {
        (item.bay_id, item.leaf_id, item.handle_domain_slot) for item in intents
    }
    for leaf in trace.leaves:
        for rule in handle_policy.slots:
            if rule.opening_type is not leaf.opening_type or (
                rule.leaf_slot is not None and rule.leaf_slot != leaf.leaf_slot
            ):
                continue
            if (
                leaf.bay_id,
                leaf.leaf_id,
                rule.handle_domain_slot,
            ) not in available:
                return True
    return False


def _leaf_rects(
    leaf: SemanticLeafTraceV1,
    placement_authorities: list[tuple[str, ManufacturingPlacementPolicyV1]],
) -> list[dict[str, object]]:
    """Resolved leaf rectangle per placement option. The entered intent
    height is measured from the selected vertical reference; transforming the
    leaf-top mounting bounds into the input's own units requires the leaf's
    position inside the outer rectangle — which only the placement policy
    resolves for sliding leaves."""
    rects: list[dict[str, object]] = []
    for policy_id, policy in placement_authorities:
        if leaf.placement_domain is PlacementDomain.DIRECT:
            rect = leaf.direct_rect
            if rect is None:
                continue
            y_mm, height_mm = rect.y_mm, rect.height_mm
        else:
            offset = policy.sliding_leaf_offsets.get(leaf.leaf_slot)
            if offset is None:
                continue
            y_mm = leaf.reference_rect.y_mm + offset.y_mm
            height_mm = leaf.finished_height_mm
        rects.append(
            {
                "placement_policy_id": policy_id,
                "leaf_top_from_outer_top_mm": str(y_mm),
                "leaf_height_mm": str(height_mm),
            }
        )
    return rects


def _handle_policy_requirements(
    trace_leaves: list[dict[str, object]],
    handle_policy: HandleRequirementPolicyV1,
    placement_authorities: list[tuple[str, ManufacturingPlacementPolicyV1]],
) -> list[dict[str, object]]:
    """Leaf-matched handle requirements of a policy for the preparation UI:
    the editor needs to know which (bay, leaf) pairs need an intent and the
    policy bounds that govern it before a position can freeze completely."""
    requirements: list[dict[str, object]] = []
    for item in trace_leaves:
        leaf = item["leaf"]
        for rule in handle_policy.slots:
            if rule.opening_type is not leaf.opening_type or (
                rule.leaf_slot is not None and rule.leaf_slot != leaf.leaf_slot
            ):
                continue
            requirements.append(
                {
                    "bay_id": item["bay_id"],
                    "leaf_id": item["leaf_id"],
                    "leaf_label": item["leaf_label"],
                    "opening_type": leaf.opening_type.value,
                    "handle_domain_slot": rule.handle_domain_slot,
                    "host_member_side": rule.host_member_side.value,
                    "outer_height_mm": str(item["nominal_height_mm"]),
                    "mounting_min_from_leaf_top_mm": str(
                        rule.mounting_min_from_leaf_top_mm
                    ),
                    "mounting_max_from_leaf_top_mm": str(
                        rule.mounting_max_from_leaf_top_mm
                    ),
                    "permitted_vertical_references": [
                        reference.value
                        for reference in rule.permitted_vertical_references
                    ],
                    "leaf_rects": _leaf_rects(leaf, placement_authorities),
                }
            )
    return requirements


def _tree_has_legacy_handle(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    if value.get("handle_height_mm") is not None:
        return True
    children = value.get("children", [])
    return isinstance(children, list) and any(_tree_has_legacy_handle(child) for child in children)


def _same_documentary_value(left: object, right: object) -> bool:
    return documentary_canonical_json_v1(left) == documentary_canonical_json_v1(right)


def _unique_by(items: list[T], attribute: str, code: str) -> list[T]:
    result: dict[str, T] = {}
    for item in items:
        identity = str(getattr(item, attribute))
        previous = result.get(identity)
        if previous is not None and previous != item:
            raise DocumentaryError(code)
        result[identity] = item
    return [result[key] for key in sorted(result)]


def _position_calculations(
    *,
    tree: dict[str, object],
    width_mm: Decimal,
    height_mm: Decimal,
    color: str,
    params: object,
    system_id: UUID,
    org_id: UUID,
) -> tuple[
    list[tuple[str | None, GeometryComputation, dict[str, object]]],
    EngineResult,
    PlanGeometry | None,
]:
    """Classic per-module geometry+trace for one persisted position.

    Returns (calculations, result, plan): classic positions compute once
    with a ``None`` module id; product-v2 assemblies evaluate for the BOM
    and each module recomputes on its own tree, the ``module.id`` becoming
    the ``"<module_id>|<id>"`` namespace used by the persisted BOM. ``plan``
    is the assembly plan geometry (coupling wedges included) or ``None``
    for classic positions.
    """
    calculations: list[tuple[str | None, GeometryComputation, dict[str, object]]] = []
    is_assembly = isinstance(tree, dict) and tree.get("version") == "product-v2"
    if is_assembly:
        product = parse_product_model(tree)
        evaluation = evaluate_assembly_from_api(
            product=product,
            color=color,
            params=params,
            coupler_articles=SystemParamsRepository().load_coupler_articles(
                system_id, org_id
            ),
        )
        if evaluation.status.value != "VALID" or evaluation.bom is None:
            raise DocumentaryError("documentary_geometry_incomplete")
        result = evaluation.bom
        module_specs = [
            (module.id, module.tree.model_dump(mode="json"), module.width_mm, module.height_mm)
            for module in product.assembly.modules
        ]
    else:
        result = None
        module_specs = [(None, tree, width_mm, height_mm)]
    for module_id, module_tree, module_width, module_height in module_specs:
        module_root = normalized_root_from_api(
            parametric_tree=module_tree,
            nominal_width_mm=module_width,
            nominal_height_mm=module_height,
            color=color,
            params=params,
        )
        computation = compute_geometry(module_root, params, diagnostic=True)
        if computation.result is None or computation.manufacturing_trace is None:
            raise DocumentaryError("documentary_geometry_incomplete")
        calculations.append((module_id, computation, module_tree))
        if not is_assembly:
            result = computation.result
    if result is None:
        raise DocumentaryError("documentary_geometry_incomplete")
    return calculations, result, evaluation.plan if is_assembly else None


def _valid_targets(
    calculations: list[tuple[str | None, GeometryComputation, dict[str, object]]],
) -> tuple[
    set[str],
    set[tuple[str, str | None]],
    set[str],
    set[tuple[str, str | None]],
]:
    """Valid bays, (bay, leaf) pairs, span ids and glass targets for a
    position, namespaced ``<module_id>|<id>`` exactly like the assembly BOM."""
    bays: set[str] = set()
    leaves: set[tuple[str, str | None]] = set()
    spans: set[str] = set()
    glass: set[tuple[str, str | None]] = set()
    for module_id, computation, _ in calculations:
        bays |= {
            f"{module_id}|{opening.bay_id}" if module_id else opening.bay_id
            for opening in computation.openings
        }
        leaves |= {
            (
                f"{module_id}|{leaf.bay_id}" if module_id else leaf.bay_id,
                f"{module_id}|{leaf.leaf_id}"
                if module_id and leaf.leaf_id is not None
                else leaf.leaf_id,
            )
            for leaf in computation.leaves
        }
        spans |= {
            f"{module_id}|{span.target_id}" if module_id else span.target_id
            for span in computation.spans
        }
        trace = computation.manufacturing_trace
        glass |= {
            (
                f"{module_id}|{infill.bay_id}" if module_id else infill.bay_id,
                f"{module_id}|{infill.leaf_id}"
                if module_id and infill.leaf_id is not None
                else infill.leaf_id,
            )
            for infill in (trace.infills if trace else [])
            if infill.kind == "GLASS"
        }
    return bays, leaves, spans, glass


def _workshop_targets(
    calculations: list[tuple[str | None, GeometryComputation, dict[str, object]]],
    trace_leaves: list[dict[str, object]],
) -> dict[str, object]:
    """Ordered annotation/purchase targets for the emission-prep editors —
    ids namespaced ``<module_id>|<id>`` exactly like the saved inputs."""
    leaf_labels = {
        (item["bay_id"], item["leaf_id"]): str(item["leaf_label"]) for item in trace_leaves
    }
    bays: list[dict[str, object]] = []
    leaves: list[dict[str, object]] = []
    spans: list[dict[str, object]] = []
    glass: list[dict[str, object]] = []
    for module_index, (module_id, computation, _) in enumerate(calculations, 1):
        prefix = f"{module_id}|" if module_id else ""
        unit = f"Unidad {module_index} · " if module_id else ""
        for index, opening in enumerate(computation.openings, 1):
            bays.append({
                "bay_id": f"{prefix}{opening.bay_id}",
                "label": f"{unit}Vano {index}",
                "width_mm": opening.width_mm,
            })
        for index, leaf in enumerate(computation.leaves, 1):
            leaf_id = (
                f"{prefix}{leaf.leaf_id}"
                if module_id and leaf.leaf_id is not None
                else leaf.leaf_id
            )
            leaves.append({
                "bay_id": f"{prefix}{leaf.bay_id}",
                "leaf_id": leaf_id,
                "leaf_label": leaf_labels.get(
                    (f"{prefix}{leaf.bay_id}", leaf_id), f"{unit}Hoja {index}"
                ),
            })
        for index, span in enumerate(computation.spans, 1):
            spans.append({
                "target_id": f"{prefix}{span.target_id}",
                "label": f"{unit}Travesaño {index}",
                "span_mm": span.span_mm,
            })
        trace = computation.manufacturing_trace
        glass_count = 0
        for infill in trace.infills if trace else []:
            if infill.kind != "GLASS":
                continue
            glass_count += 1
            bay_key = f"{prefix}{infill.bay_id}"
            leaf_key = (
                f"{prefix}{infill.leaf_id}"
                if module_id and infill.leaf_id is not None
                else infill.leaf_id
            )
            glass.append({
                "bay_id": bay_key,
                "leaf_id": leaf_key,
                "label": leaf_labels.get((bay_key, leaf_key), f"{unit}Vidrio {glass_count}"),
            })
    return {"bays": bays, "leaves": leaves, "spans": spans, "glass": glass}


def _position_rows(project_id: UUID, org_id: UUID) -> list[dict[str, object]]:
    return rows(
        "SELECT position.*,input.id AS documentary_input_id,"
        "input.manufacturing_placement_policy_id,input.handle_requirement_policy_id,"
        "input.reinforcement_cut_policy_id,input.workshop_annotations::text,"
        "input.structural_inputs::text,input.glass_polishing::text,"
        "input.handle_intents::text,input.accessory_schedule::text,"
        "input.legacy_handle_migration_confirmed,input.calculation_hash AS documentary_calculation_hash "
        "FROM public.project_positions position "
        "JOIN public.position_documentary_inputs input "
        "ON input.position_id=position.id AND input.project_id=position.project_id "
        "AND input.org_id=position.org_id "
        "WHERE position.project_id=%s AND position.org_id=%s "
        "ORDER BY position.position_index",
        [project_id, org_id],
    )


def _technical_bom(snapshot: dict[str, object]) -> dict[str, object]:
    values = snapshot.get("positions")
    if not isinstance(values, list):
        raise DocumentaryError("invalid_applied_pricing_snapshot")
    result: dict[str, object] = {}
    for value in values:
        if not isinstance(value, dict) or not isinstance(value.get("position_id"), str):
            raise DocumentaryError("invalid_applied_pricing_snapshot")
        position_id = value["position_id"]
        if position_id in result or "bom" not in value:
            raise DocumentaryError("invalid_applied_pricing_snapshot")
        result[position_id] = value["bom"]
    return result


def _collect_purchase_authorities(
    existing: PurchaseAuthorities | None, following: PurchaseAuthorities
) -> PurchaseAuthorities:
    prior = existing or PurchaseAuthorities([], [], [], [])
    return PurchaseAuthorities(
        _unique_by(prior.stock_bindings + following.stock_bindings, "binding_id",
                   "physical_stock_authority_conflict"),
        _unique_by(prior.glass_mappings + following.glass_mappings, "authority_id",
                   "glass_purchase_authority_conflict"),
        _unique_by(prior.hardware_mappings + following.hardware_mappings, "authority_id",
                   "hardware_purchase_authority_conflict"),
        _unique_by(prior.panel_authorities + following.panel_authorities, "authority_id",
                   "panel_purchase_authority_conflict"),
    )


def freeze_revision_a(
    *, org_id: UUID, actor_id: UUID, project_id: UUID,
    pricing_operation_id: UUID, confirmed: bool,
    allow_incomplete_workshop: bool = False,
) -> dict[str, object]:
    if not confirmed:
        raise DocumentaryError("documentary_freeze_confirmation_required")
    with commercial_backend():
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM public.projects WHERE id=%s AND org_id=%s FOR UPDATE",
                [project_id, org_id],
            )
            cursor.execute(
                "SELECT id FROM public.pricing_operations "
                "WHERE id=%s AND project_id=%s AND org_id=%s FOR UPDATE",
                [pricing_operation_id, project_id, org_id],
            )
            cursor.execute(
                "SELECT id FROM public.project_positions "
                "WHERE project_id=%s AND org_id=%s ORDER BY position_index FOR UPDATE",
                [project_id, org_id],
            )
    with documentary_backend():
        project = one(
            "SELECT * FROM public.projects WHERE org_id=%s AND id=%s",
            [org_id, project_id],
            "project_not_found",
        )
        revision = str(project["current_revision"])
        existing = rows(
            "SELECT id,pricing_operation_id,revision_code,bom_hash,snapshot_sha256,"
            "production_allowed,documentary_complete,emitted_at "
            "FROM public.project_versions WHERE project_id=%s AND org_id=%s "
            "AND revision_code=%s",
            [project_id, org_id, revision],
        )
        if existing:
            if len(existing) != 1 or str(existing[0]["pricing_operation_id"]) != str(
                pricing_operation_id
            ):
                raise DocumentaryError("revision_already_sealed")
            return {
                **{key: (str(value) if isinstance(value, UUID) else value)
                   for key, value in existing[0].items()},
                "pricing_operation_id": str(pricing_operation_id),
                "created": False,
            }
        if project["status"] != "DRAFT":
            raise DocumentaryError("revision_not_available")
        operation = one(
            "SELECT id,org_id,project_id,requested_by,request::text,input_snapshot::text,"
            "result::text,source_revision,revision_code,state,approved_by,approved_at,reason,created_at "
            "FROM public.pricing_operations WHERE id=%s AND org_id=%s AND project_id=%s",
            [pricing_operation_id, org_id, project_id],
            "pricing_operation_not_found",
        )
        if operation["state"] != "APPLIED" or str(
            operation["revision_code"] or "REV-A"
        ) != revision:
            raise DocumentaryError("applied_pricing_authority_required")
        if project["pricing_reset_at"] is not None and (
            operation["approved_at"] is None or operation["approved_at"] <= project["pricing_reset_at"]
        ):
            raise DocumentaryError("applied_pricing_authority_required")
        project_input = one(
            "SELECT * FROM public.project_documentary_inputs "
            "WHERE project_id=%s AND org_id=%s",
            [project_id, org_id],
            "project_documentary_inputs_required",
        )
        positions = _position_rows(project_id, org_id)
        if not positions:
            raise DocumentaryError("position_documentary_inputs_required")
        request = _json_object(operation["request"], "invalid_applied_pricing_request")
        pricing_snapshot = _json_object(
            operation["input_snapshot"], "invalid_applied_pricing_snapshot"
        )
        pricing_result = _json_object(operation["result"], "invalid_applied_pricing_result")
        _pricing_state_matches(project, positions, request, pricing_snapshot, pricing_result)
        priced_bom = _technical_bom(pricing_snapshot)

        position_inputs: list[dict[str, object]] = []
        bom: list[dict[str, object]] = []
        manufacturing: list[object] = []
        inspector_evidence: list[dict[str, object]] = []
        purchase_positions: list[PositionPurchaseInputV1] = []
        purchase_authorities: PurchaseAuthorities | None = None
        documentary_complete = True
        production_allowed = True
        stock_repository = CuttingRepository()
        for position in positions:
            position_id = str(position["id"])
            tree = _json_object(position["parametric_tree"], "invalid_parametric_tree")
            is_assembly = isinstance(tree, dict) and tree.get("version") == "product-v2"
            color = (
                "WHITE"
                if position["color_interior"] == "WHITE" and position["color_exterior"] == "WHITE"
                else "FOILED"
            )
            system_id = UUID(str(position["system_id"]))
            params = SystemParamsRepository().load_visible(system_id, org_id)
            calculations, result, plan = _position_calculations(
                tree=tree,
                width_mm=D(str(position["width_mm"])),
                height_mm=D(str(position["height_mm"])),
                color=color,
                params=params,
                system_id=system_id,
                org_id=org_id,
            )
            current_bom = result.model_dump(mode="json")
            stored_bom = _json_object(position["bom_snapshot"], "invalid_stored_bom")
            stored_bom.pop("calculation_hash", None)
            if position_id not in priced_bom or not _same_documentary_value(
                current_bom, priced_bom[position_id]
            ) or not _same_documentary_value(current_bom, stored_bom):
                raise DocumentaryError("applied_pricing_technical_binding_drift")

            annotations = workshop_annotations(position["workshop_annotations"])
            structural = structural_inputs(position["structural_inputs"])
            targets = {
                (f"{module_id}|{opening.bay_id}" if module_id else opening.bay_id, None)
                for module_id, computation, _ in calculations
                for opening in computation.openings
            } | {
                (
                    f"{module_id}|{leaf.bay_id}" if module_id else leaf.bay_id,
                    f"{module_id}|{leaf.leaf_id}" if module_id else leaf.leaf_id,
                )
                for module_id, computation, _ in calculations
                for leaf in computation.leaves
            }
            if any((item.bay_id, item.leaf_id) not in targets for item in annotations):
                raise DocumentaryError("workshop_annotation_target_invalid")
            spans = {
                f"{module_id}|{span.target_id}" if module_id else span.target_id
                for module_id, computation, _ in calculations
                for span in computation.spans
            }
            if any(item.target_id not in spans for item in structural):
                raise DocumentaryError("structural_input_target_invalid")
            if color != "WHITE" or any(item.finish_class not in (None, "WHITE") for item in annotations):
                raise DocumentaryError("unsupported_documentary_color")

            inspector_authorities = InspectorRepository().load(system_id, org_id)
            cutting = stock_repository.for_result(result, system_id, org_id, color)
            calculation_request = {
                "system_id": str(system_id),
                "parametric_tree": tree,
                "nominal_width_mm": D(str(position["width_mm"])),
                "nominal_height_mm": D(str(position["height_mm"])),
                "color": color,
            }
            source_hash = calculation_response(calculation_request, result)["calculation_hash"]
            if position["documentary_calculation_hash"] != source_hash:
                raise DocumentaryError("documentary_calculation_identity_stale")
            inspections: list[tuple[str | None, InspectorResult, bool, bool]] = []
            has_failures = False
            position_production_allowed = True
            position_complete = True
            for module_id, computation, _ in calculations:
                inertias: dict[str, Decimal | None] = {}
                for span in computation.spans:
                    _, inertia = stock_repository.reinforcement_stock(
                        system_id, org_id, span.parent_profile_sku, None, color
                    )
                    inertias[span.target_id] = inertia
                inspection = inspect(InspectorInput(
                    computation=computation,
                    chamber_clearance_mm=inspector_authorities.chamber_clearance_mm,
                    annotations=_module_scoped(annotations, module_id, "bay_id", "leaf_id"),
                    structural_inputs=_module_scoped(structural, module_id, "target_id"),
                    reinforcement_ix_by_target=inertias,
                    mode=InspectionMode.DESIGN,
                    source_calculation_hash=str(source_hash),
                ), inspector_authorities.config)
                module_allowed = inspection.production_allowed
                module_complete = not any(
                    evaluation.status is RuleEvaluationStatus.MISSING_INPUT
                    for evaluation in inspection.evaluations
                )
                inspections.append(
                    (module_id, inspection, module_complete, module_allowed)
                )
                has_failures = has_failures or any(
                    evaluation.status is RuleEvaluationStatus.FAIL
                    for evaluation in inspection.evaluations
                )
                position_production_allowed = (
                    position_production_allowed and module_allowed
                )
                position_complete = position_complete and module_complete
            is_red = not position_production_allowed or any(
                inspection.status == "RED" for _, inspection, _, _ in inspections
            )
            if has_failures or (is_red and not allow_incomplete_workshop):
                failures: list[dict[str, object]] = []
                for module_id, inspection, _, _ in inspections:
                    prefix = f"{module_id}|" if module_id else ""
                    failures.extend(
                        {
                            "rule_id": evaluation.rule_id.value,
                            "status": evaluation.status.value,
                            "position_id": position_id,
                            "bay_id": (
                                f"{prefix}{evaluation.bay_id}"
                                if evaluation.bay_id is not None
                                else None
                            ),
                            "leaf_id": (
                                f"{prefix}{evaluation.leaf_id}"
                                if evaluation.leaf_id is not None
                                else None
                            ),
                        }
                        for evaluation in inspection.evaluations
                        if evaluation.status
                        in (RuleEvaluationStatus.FAIL, RuleEvaluationStatus.MISSING_INPUT)
                    )
                raise DocumentaryError(
                    "inspector_red_blocks_documentary_freeze",
                    details={"failures": failures},
                )
            production_allowed = production_allowed and position_production_allowed
            documentary_complete = documentary_complete and position_complete

            policies = load_manufacturing_policies(
                system_id=system_id,
                org_id=org_id,
                placement_id=UUID(str(position["manufacturing_placement_policy_id"])),
                handle_id=UUID(str(position["handle_requirement_policy_id"])),
                reinforcement_id=UUID(str(position["reinforcement_cut_policy_id"])),
            )
            intents = handle_intents(position["handle_intents"])
            quantity = int(position["quantity"])
            unit_models: list[tuple[str | None, ManufacturingFactsV1]] = []
            skipped_module = False
            for module_id, computation, module_tree in calculations:
                scoped_intents = _module_scoped(
                    intents, module_id, "bay_id", "leaf_id"
                )
                if is_assembly and _missing_handle_intents(
                    computation.manufacturing_trace,
                    policies.handles,
                    scoped_intents,
                ):
                    # A module whose handle intents were never saved is not
                    # projected rather than blocking the commercial freeze;
                    # skipped_module marks the seal incomplete below.
                    skipped_module = True
                    continue
                for repetition in range(1, quantity + 1):
                    unit_models.append((
                        module_id,
                        project_manufacturing_facts_v1(
                            trace=computation.manufacturing_trace,
                            position_id=position_id,
                            position_index=int(position["position_index"]),
                            repetition_index=repetition,
                            placement_policy=policies.placement,
                            handle_policy=policies.handles,
                            reinforcement_policy=policies.reinforcement,
                            handle_intents=scoped_intents,
                            resolved_reinforcement_skus=cutting.reinforcement_skus,
                            legacy_handle_height_present=_tree_has_legacy_handle(module_tree),
                            legacy_handle_migration_confirmed=bool(
                                position["legacy_handle_migration_confirmed"]
                            ),
                            module_id=module_id,
                        ),
                    ))
            coupler_cuts = [
                cut for cut in result.profile_cuts if cut.role is ProfileRole.COUPLER
            ]
            coupler_reinforcements = [
                piece
                for piece in result.reinforcements
                if piece.role is ProfileRole.COUPLER
            ]
            if is_assembly and (coupler_cuts or coupler_reinforcements):
                if plan is None:
                    raise DocumentaryError("documentary_geometry_incomplete")
                coupling_wedges = {
                    wedge.coupling_id: [
                        TracePointV1(x_mm=point.x_mm, y_mm=point.y_mm)
                        for point in wedge.polygon
                    ]
                    for wedge in plan.couplings
                }
                for repetition in range(1, quantity + 1):
                    unit_models.append((
                        None,
                        project_coupling_facts_v1(
                            coupler_cuts=coupler_cuts,
                            coupler_reinforcements=coupler_reinforcements,
                            coupling_wedges=coupling_wedges,
                            position_id=position_id,
                            position_index=int(position["position_index"]),
                            repetition_index=repetition,
                            nominal_width_mm=D(str(position["width_mm"])),
                            nominal_height_mm=D(str(position["height_mm"])),
                            placement_policy=policies.placement,
                            handle_policy=policies.handles,
                            reinforcement_policy=policies.reinforcement,
                        ),
                    ))
            units = [unit for _, unit in unit_models]
            hardware = [HardwareSelectionV1(
                repetition_index=repetition,
                bay_id=item.bay_id,
                leaf_id=item.leaf_id,
                technical_kit_sku=item.kit_sku,
                name=item.name,
                quantity=item.qty,
                contents=item.contents,
            ) for repetition in range(1, quantity + 1) for item in result.hardware_items]
            polishing = glass_polishing(position["glass_polishing"])
            glass_targets = {
                (infill.bay_id, infill.leaf_id)
                for _, unit in unit_models
                for infill in unit.infills
                if infill.kind == "GLASS"
            }
            accessories = (
                accessory_schedule(position["accessory_schedule"], str(position["documentary_input_id"]))
                if position["accessory_schedule"] is not None else None
            )
            purchase_complete = (
                not skipped_module
                and {(item.bay_id, item.leaf_id) for item in polishing} == glass_targets
                and accessories is not None
            )
            # A skipped module means the sealed snapshot would omit its units:
            # incomplete, never faked. When every module projects, assemblies
            # carry purchase evidence under the same contract as classics.
            if not purchase_complete:
                if not allow_incomplete_workshop:
                    raise DocumentaryError("purchase_authority_incomplete")
                position_production_allowed = False
                position_complete = False
                production_allowed = False
                documentary_complete = False
            location_tag = str(position["location_tag"] or "")
            if purchase_complete:
                purchase_positions.append(PositionPurchaseInputV1(
                    position_id=position_id,
                    position_index=int(position["position_index"]),
                    system_id=str(system_id),
                    quantity=quantity,
                    color=color,
                    location_tag=location_tag,
                    manufacturing_units=units,
                    hardware=hardware,
                    glass_polishing=polishing,
                    accessory_schedule=accessories,
                ))
            # Unit members now cover every profile SKU the BOM carries:
            # assembly coupler cuts are minted as position-level sources too.
            profile_skus = {member.workshop_sku for unit in units for member in unit.members}
            reinforcement_skus = {
                item.workshop_sku for unit in units for item in unit.reinforcements
            }
            glass_skus = {
                infill.technical_sku for unit in units for infill in unit.infills
                if infill.kind == "GLASS"
            }
            panel_skus = {
                infill.technical_sku for unit in units for infill in unit.infills
                if infill.kind == "PANEL"
            }
            following = load_purchase_authorities(
                system_id=system_id,
                org_id=org_id,
                color=color,
                profile_skus=profile_skus,
                reinforcement_skus=reinforcement_skus,
                glass_skus=glass_skus,
                hardware_skus={item.technical_kit_sku for item in hardware},
                panel_skus=panel_skus,
            )
            purchase_authorities = _collect_purchase_authorities(
                purchase_authorities, following
            )
            position_inputs.append({
                "id": position_id,
                "position_index": int(position["position_index"]),
                "quantity": quantity,
                "typology": str(position["typology"]),
                "system_id": system_id,
                "width_mm": D(str(position["width_mm"])),
                "height_mm": D(str(position["height_mm"])),
                "color_interior": str(position["color_interior"]),
                "color_exterior": str(position["color_exterior"]),
                "location_tag": location_tag,
                "parametric_tree": tree,
                "workshop_annotations": [item.model_dump(mode="python") for item in annotations],
                "structural_inputs": [item.model_dump(mode="python") for item in structural],
                "glass_polishing": [item.model_dump(mode="python") for item in polishing],
                "handle_intents": [item.model_dump(mode="python") for item in intents],
                "accessory_schedule": accessories.model_dump(mode="python") if accessories else None,
                "calculation_hash": source_hash,
                "manufacturing_policies": {
                    "placement": policies.placement.model_dump(mode="python"),
                    "handles": policies.handles.model_dump(mode="python"),
                    "reinforcement": policies.reinforcement.model_dump(mode="python"),
                },
                "legacy_handle_migration_confirmed": bool(
                    position["legacy_handle_migration_confirmed"]
                ),
            })
            bom.append({
                "position_id": position_id,
                "quantity": quantity,
                "engine_result": current_bom,
                "calculation_hash": source_hash,
            })
            manufacturing.extend(
                {
                    **unit.model_dump(mode="python"),
                    **({"module_id": module_id} if module_id else {}),
                }
                for module_id, unit in unit_models
            )
            for module_id, inspection, module_complete, module_allowed in inspections:
                inspector_evidence.append({
                    "position_id": position_id,
                    **({"module_id": module_id} if module_id else {}),
                    "mode": "DESIGN",
                    "result": inspection.model_dump(mode="python"),
                    "config": inspector_authorities.config.model_dump(mode="python"),
                    "chamber_clearance_mm": inspector_authorities.chamber_clearance_mm,
                    "documentary_complete": module_complete,
                    "production_allowed": module_allowed,
                })

        if purchase_authorities is None:
            raise DocumentaryError("purchase_authorities_required")
        purchase = project_purchase_requirements_v1(
            positions=purchase_positions,
            stock_bindings=purchase_authorities.stock_bindings,
            glass_mappings=purchase_authorities.glass_mappings,
            hardware_mappings=purchase_authorities.hardware_mappings,
            panel_authorities=purchase_authorities.panel_authorities,
        ) if len(purchase_positions) == len(positions) else None
        bom_hash = bom_hash_v1(
            project_id=project_id, revision=revision, positions=position_inputs, bom=bom
        )
        sealed_at = datetime.now(timezone.utc)
        snapshot = {
            "schema_version": 1,
            "canonical_version": DOCUMENTARY_CANONICAL_VERSION,
            "project_id": project_id,
            "org_id": org_id,
            "revision": revision,
            "sealed_by": actor_id,
            "sealed_at": sealed_at,
            "project": {
                "code": str(project["code"]),
                "name": str(project["name"]),
                "client_name": str(project["client_name"]),
                "client_rut": project["client_rut"],
                "client_email": project["client_email"],
                "client_phone": project["client_phone"],
                "delivery_address": project["delivery_address"],
                "payment_terms": str(project_input["payment_terms"]),
                "quotation_valid_until": project_input["quotation_valid_until"],
                "notes_commercial": project["notes_commercial"],
                "currency": request.get("currency"),
                "total_price_net": D(str(project["total_price_net"])),
                "total_price_tax": D(str(project["total_price_tax"])),
                "total_price_gross": D(str(project["total_price_gross"])),
            },
            "positions": position_inputs,
            "bom": bom,
            "pricing": {
                "operation_id": operation["id"],
                "state": "APPLIED",
                "requested_by": operation["requested_by"],
                "approved_by": operation["approved_by"],
                "approved_at": operation["approved_at"],
                "request": request,
                "input_snapshot": pricing_snapshot,
                "result": pricing_result,
                "applied_total_cost_net": D(str(project["total_cost_net"])),
                "source_revision": operation["source_revision"],
            },
            "inspector": inspector_evidence,
            "manufacturing": manufacturing,
            "purchase_requirements": purchase.model_dump(mode="python") if purchase else None,
            "purchase_authorities": {
                "physical_stock_bindings": [
                    item.model_dump(mode="python")
                    for item in purchase_authorities.stock_bindings
                ],
                "glass": [item.model_dump(mode="python")
                          for item in purchase_authorities.glass_mappings],
                "hardware": [item.model_dump(mode="python")
                             for item in purchase_authorities.hardware_mappings],
                "panel": [item.model_dump(mode="python")
                          for item in purchase_authorities.panel_authorities],
            },
            "production_allowed": production_allowed,
            "documentary_complete": documentary_complete,
            "realized_waste": {"status": "NOT_RECORDED", "value": None},
            "bom_hash": bom_hash,
        }
        snapshot_sha256 = snapshot_sha256_v1(snapshot)
        version = one(
            "INSERT INTO public.project_versions("
            "project_id,org_id,revision_code,snapshot_json,pdf_storage_path,emitted_by,emitted_at,"
            "authority_version,pricing_operation_id,canonical_version,bom_hash,snapshot_sha256,"
            "production_allowed,documentary_complete) "
            "VALUES(%s,%s,%s,%s::jsonb,NULL,%s,%s,'SHOT10_V1',%s,%s,%s,%s,%s,%s) "
            "RETURNING id,revision_code,bom_hash,snapshot_sha256,production_allowed,"
            "documentary_complete,emitted_at",
            [project_id, org_id, revision,
             documentary_canonical_json_v1(snapshot).decode("utf-8"), actor_id, sealed_at,
             pricing_operation_id, DOCUMENTARY_CANONICAL_VERSION, bom_hash,
             snapshot_sha256, production_allowed, documentary_complete],
        )
        version_id = UUID(str(version["id"]))
        if purchase is not None:
            projection_snapshot = purchase.model_dump(mode="python")
            projection = one(
                "INSERT INTO public.purchase_projections("
                "project_id,project_version_id,org_id,bom_hash,snapshot_sha256,schema_version,"
                "projection_hash,snapshot_json,created_by,created_at) "
                "VALUES(%s,%s,%s,%s,%s,1,%s,%s::jsonb,%s,%s) RETURNING id",
                [project_id, version_id, org_id, bom_hash, snapshot_sha256,
                 purchase.projection_hash,
                 documentary_canonical_json_v1(projection_snapshot).decode("utf-8"),
                 actor_id, sealed_at],
            )
            projection_id = UUID(str(projection["id"]))
            for requirement in purchase.requirements:
                requirement_id = uuid5(
                    NAMESPACE_URL, f"https://dekopen.local/requirement/{version_id}/{requirement.requirement_key}"
                )
                common = {
                    "requirement_key", "order_type", "category", "authority_ids",
                    "technical_skus", "purchasing_sku", "physical_stock_identity",
                    "unit", "quantity", "source_trace",
                }
                payload = requirement.model_dump(mode="python")
                specification = {
                    key: value for key, value in payload.items()
                    if key not in common and value is not None
                }
                one(
                    "INSERT INTO public.purchase_requirement_lines("
                    "id,requirement_key,projection_id,project_id,project_version_id,org_id,"
                    "bom_hash,snapshot_sha256,order_type,category,technical_identity,purchasing_sku,"
                    "physical_stock_identity,unit,quantity,specification,source_trace) "
                    "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s::jsonb,%s::jsonb) "
                    "RETURNING id",
                    [requirement_id, requirement.requirement_key, projection_id, project_id,
                     version_id, org_id, bom_hash, snapshot_sha256,
                     requirement.order_type.value, requirement.category,
                     json_text({"authority_ids": requirement.authority_ids,
                                "technical_skus": requirement.technical_skus}),
                     requirement.purchasing_sku, requirement.physical_stock_identity,
                     requirement.unit, requirement.quantity, json_text(specification),
                     json_text(requirement.source_trace)],
                )
        with commercial_backend():
            one(
                "UPDATE public.projects SET status='QUOTED',updated_at=clock_timestamp() "
                "WHERE id=%s AND org_id=%s AND status='DRAFT' AND current_revision=%s RETURNING id",
                [project_id, org_id, revision],
                "revision_state_transition_failed",
            )
        return {
            "id": str(version_id),
            "pricing_operation_id": str(pricing_operation_id),
            "created": True,
            "revision_code": revision,
            "bom_hash": bom_hash,
            "snapshot_sha256": snapshot_sha256,
            "production_allowed": production_allowed,
            "documentary_complete": documentary_complete,
            "emitted_at": sealed_at,
            "purchase_projection_hash": purchase.projection_hash if purchase else None,
        }


def prepare_documentary_inputs(
    *, org_id: UUID, project_id: UUID
) -> dict[str, object]:
    project = one(
        "SELECT id,status,current_revision FROM public.projects WHERE id=%s AND org_id=%s",
        [project_id, org_id],
        "project_not_found",
    )
    positions = rows(
        "SELECT position.id,position.system_id,position.location_tag,position.width_mm,"
        "position.height_mm,position.color_interior,position.color_exterior,"
        "position.parametric_tree,system.name AS system_name "
        "FROM public.project_positions position JOIN public.profile_systems system "
        "ON system.id=position.system_id WHERE position.project_id=%s AND position.org_id=%s "
        "ORDER BY position.position_index",
        [project_id, org_id],
    )
    project_inputs = rows(
        "SELECT payment_terms,quotation_valid_until FROM public.project_documentary_inputs "
        "WHERE project_id=%s AND org_id=%s",
        [project_id, org_id],
    )
    position_inputs = {
        str(item["position_id"]): item
        for item in rows(
            "SELECT position_id,manufacturing_placement_policy_id,handle_requirement_policy_id,"
            "reinforcement_cut_policy_id,workshop_annotations::text,structural_inputs::text,"
            "glass_polishing::text,handle_intents::text,accessory_schedule::text,"
            "legacy_handle_migration_confirmed,calculation_hash FROM public.position_documentary_inputs "
            "WHERE project_id=%s AND org_id=%s",
            [project_id, org_id],
        )
    }
    systems = {item["system_id"] for item in positions}

    def policy_options(table):
        if not systems:
            return {}
        placeholders = ",".join(["%s"] * len(systems))
        values = rows(
            f"SELECT id,system_id,version,authority->>'policy_id' AS label FROM public.{table} "
            f"WHERE system_id IN ({placeholders}) AND (org_id IS NULL OR org_id=%s) "
            "ORDER BY system_id,version DESC,id",
            [*systems, org_id],
        )
        grouped = {}
        for value in values:
            grouped.setdefault(str(value["system_id"]), []).append(
                {
                    "id": value["id"],
                    "label": value["label"] or f"Versión {value['version']}",
                    "version": value["version"],
                }
            )
        return grouped

    placement = policy_options("manufacturing_placement_policies")
    handles = policy_options("handle_requirement_policies")
    reinforcement = policy_options("reinforcement_cut_policies")
    handle_authorities: dict[str, HandleRequirementPolicyV1] = {}
    placement_authorities: dict[str, ManufacturingPlacementPolicyV1] = {}
    if systems:
        placeholders = ",".join(["%s"] * len(systems))
        for value in rows(
            "SELECT id,authority::text FROM public.handle_requirement_policies "
            f"WHERE system_id IN ({placeholders}) AND (org_id IS NULL OR org_id=%s)",
            [*systems, org_id],
        ):
            handle_authorities[str(value["id"])] = _handle_policy(value["authority"])
        for value in rows(
            "SELECT id,authority::text FROM public.manufacturing_placement_policies "
            f"WHERE system_id IN ({placeholders}) AND (org_id IS NULL OR org_id=%s)",
            [*systems, org_id],
        ):
            placement_authorities[str(value["id"])] = _placement_policy(
                value["authority"]
            )

    def selected(existing, key, options):
        if existing and existing[key] is not None:
            return existing[key]
        return options[0]["id"] if len(options) == 1 else None

    prepared = []
    for position in positions:
        identity = str(position["id"])
        existing = position_inputs.get(identity)
        system_id = str(position["system_id"])
        system_id_uuid = UUID(system_id)
        placement_options = placement.get(system_id, [])
        handle_options = handles.get(system_id, [])
        reinforcement_options = reinforcement.get(system_id, [])

        tree = _json_object(position["parametric_tree"], "invalid_parametric_tree")
        color = (
            "WHITE"
            if position.get("color_interior") == "WHITE" and position.get("color_exterior") == "WHITE"
            else "FOILED"
        )
        params = SystemParamsRepository().load_visible(system_id_uuid, org_id)
        calculations, result, _plan = _position_calculations(
            tree=tree,
            width_mm=D(str(position["width_mm"])),
            height_mm=D(str(position["height_mm"])),
            color=color,
            params=params,
            system_id=system_id_uuid,
            org_id=org_id,
        )
        identity_hash = calculation_response({
            "system_id": system_id, "parametric_tree": tree,
            "nominal_width_mm": D(str(position["width_mm"])),
            "nominal_height_mm": D(str(position["height_mm"])), "color": color,
        }, result)["calculation_hash"]
        if existing and existing["calculation_hash"] != identity_hash:
            existing = None
        valid_bays, valid_leaves, valid_spans, valid_glass = _valid_targets(calculations)

        trace_leaves: list[dict[str, object]] = []
        leaf_counts: dict[str | None, int] = {}
        for module_index, (module_id, computation, _module_tree) in enumerate(
            calculations, 1
        ):
            trace = computation.manufacturing_trace
            if trace is None:
                continue
            for leaf in trace.leaves:
                leaf_counts[module_id] = leaf_counts.get(module_id, 0) + 1
                number = leaf_counts[module_id]
                trace_leaves.append(
                    {
                        "bay_id": (
                            f"{module_id}|{leaf.bay_id}"
                            if module_id
                            else leaf.bay_id
                        ),
                        "leaf_id": (
                            f"{module_id}|{leaf.leaf_id}"
                            if module_id and leaf.leaf_id is not None
                            else leaf.leaf_id
                        ),
                        "leaf_label": (
                            f"Unidad {module_index} · Hoja {number}"
                            if module_id
                            else f"Hoja {number}"
                        ),
                        "leaf": leaf,
                        "nominal_height_mm": trace.nominal_height_mm,
                    }
                )

        existing_workshop = (
            decoded(existing["workshop_annotations"])
            if existing and existing["workshop_annotations"] is not None
            else []
        )
        existing_glass = (
            decoded(existing["glass_polishing"])
            if existing and existing["glass_polishing"] is not None
            else []
        )
        existing_structural = (
            decoded(existing["structural_inputs"])
            if existing and existing["structural_inputs"] is not None
            else []
        )
        existing_intents = (
            decoded(existing["handle_intents"])
            if existing and existing["handle_intents"] is not None
            else []
        )

        workshop = [
            item for item in (existing_workshop or [])
            if isinstance(item, dict)
            and item.get("bay_id") in valid_bays
            and (item.get("leaf_id") is None or (item.get("bay_id"), item.get("leaf_id")) in valid_leaves)
        ]
        glass = [
            item for item in (existing_glass or [])
            if isinstance(item, dict)
            and (item.get("bay_id"), item.get("leaf_id")) in valid_glass
        ]
        structural = [
            item for item in (existing_structural or [])
            if isinstance(item, dict)
            and item.get("target_id") in valid_spans
        ]
        intents = [
            item for item in (existing_intents or [])
            if isinstance(item, dict)
            and (item.get("bay_id"), item.get("leaf_id")) in valid_leaves
        ]

        prepared.append(
            {
                "position_id": position["id"],
                "calculation_hash": identity_hash,
                "location_tag": position["location_tag"] or "",
                "system_name": position["system_name"],
                "placement_options": placement_options,
                "handle_options": handle_options,
                "reinforcement_options": reinforcement_options,
                "manufacturing_placement_policy_id": selected(
                    existing, "manufacturing_placement_policy_id", placement_options
                ),
                "handle_requirement_policy_id": selected(
                    existing, "handle_requirement_policy_id", handle_options
                ),
                "reinforcement_cut_policy_id": selected(
                    existing, "reinforcement_cut_policy_id", reinforcement_options
                ),
                "workshop_annotations": workshop,
                "structural_inputs": structural,
                "glass_polishing": glass,
                "handle_intents": intents,
                "handle_requirements": [
                    {
                        "policy_id": option["id"],
                        "requirements": _handle_policy_requirements(
                            trace_leaves,
                            handle_authorities[str(option["id"])],
                            [
                                (str(placement["id"]), placement_authorities[str(placement["id"])])
                                for placement in placement_options
                                if str(placement["id"]) in placement_authorities
                            ],
                        ),
                    }
                    for option in handle_options
                    if str(option["id"]) in handle_authorities
                ],
                "workshop_targets": _workshop_targets(calculations, trace_leaves),
                "accessory_schedule": decoded(existing["accessory_schedule"])
                if existing and existing["accessory_schedule"] is not None else None,
                "legacy_handle_migration_confirmed": bool(
                    existing and existing["legacy_handle_migration_confirmed"]
                ),
            }
        )
    values = project_inputs[0] if project_inputs else {}
    return {
        "project_id": project["id"],
        "revision_code": project["current_revision"],
        "payment_terms": values.get("payment_terms", ""),
        "quotation_valid_until": values.get("quotation_valid_until"),
        "positions": prepared,
    }


def save_documentary_inputs(
    *, org_id: UUID, actor_id: UUID, project_id: UUID, data: dict[str, object]
) -> dict[str, object]:
    supplied_values = data.get("positions")
    if not isinstance(supplied_values, list) or not all(
        isinstance(item, dict) for item in supplied_values
    ):
        raise DocumentaryError("invalid_documentary_inputs")
    with commercial_backend():
        project = one(
            "SELECT id,status FROM public.projects WHERE id=%s AND org_id=%s FOR UPDATE",
            [project_id, org_id],
            "project_not_found",
        )
        if project["status"] != "DRAFT":
            raise DocumentaryError("documentary_inputs_require_draft")
        positions = rows(
            "SELECT id,system_id,width_mm,height_mm,color_interior,color_exterior,parametric_tree "
            "FROM public.project_positions WHERE project_id=%s AND org_id=%s "
            "ORDER BY position_index FOR UPDATE",
            [project_id, org_id],
        )
        expected = {str(item["id"]) for item in positions}
        supplied = {str(item["position_id"]) for item in supplied_values}
        if supplied != expected or len(supplied_values) != len(supplied):
            raise DocumentaryError("documentary_position_coverage_required")
        positions_by_id = {str(item["id"]): item for item in positions}

    for item in supplied_values:
        pos = positions_by_id[str(item["position_id"])]
        system_id_uuid = UUID(str(pos["system_id"]))
        tree = _json_object(pos["parametric_tree"], "invalid_parametric_tree")
        color = (
            "WHITE"
            if pos.get("color_interior") == "WHITE" and pos.get("color_exterior") == "WHITE"
            else "FOILED"
        )
        params = SystemParamsRepository().load_visible(system_id_uuid, org_id)
        calculations, result, _plan = _position_calculations(
            tree=tree,
            width_mm=D(str(pos["width_mm"])),
            height_mm=D(str(pos["height_mm"])),
            color=color,
            params=params,
            system_id=system_id_uuid,
            org_id=org_id,
        )
        identity_hash = calculation_response({
            "system_id": str(system_id_uuid), "parametric_tree": tree,
            "nominal_width_mm": D(str(pos["width_mm"])),
            "nominal_height_mm": D(str(pos["height_mm"])), "color": color,
        }, result)["calculation_hash"]
        valid_bays, valid_leaves, valid_spans, valid_glass = _valid_targets(calculations)
        item_workshop = item.get("workshop_annotations") or []
        for w in item_workshop:
            if not isinstance(w, dict) or w.get("bay_id") not in valid_bays or (
                w.get("leaf_id") is not None and (w.get("bay_id"), w.get("leaf_id")) not in valid_leaves
            ):
                raise DocumentaryError("workshop_annotation_target_invalid")
        item_structural = item.get("structural_inputs") or []
        for s in item_structural:
            if not isinstance(s, dict) or s.get("target_id") not in valid_spans:
                raise DocumentaryError("structural_input_target_invalid")
        item_glass = item.get("glass_polishing") or []
        for g in item_glass:
            if not isinstance(g, dict) or (g.get("bay_id"), g.get("leaf_id")) not in valid_glass:
                raise DocumentaryError("glass_polishing_target_invalid")
        for h in item.get("handle_intents") or []:
            if not isinstance(h, dict) or (h.get("bay_id"), h.get("leaf_id")) not in valid_leaves:
                raise DocumentaryError("handle_intent_target_invalid")
        if item.get("calculation_hash") != identity_hash:
            raise DocumentaryError("documentary_calculation_identity_stale")

    with documentary_backend():
        if rows(
            "SELECT version.id FROM public.project_versions version "
            "JOIN public.projects project ON project.id=version.project_id "
            "AND project.org_id=version.org_id "
            "WHERE version.project_id=%s AND version.org_id=%s "
            "AND version.revision_code=project.current_revision",
            [project_id, org_id],
        ):
            raise DocumentaryError("sealed_documentary_inputs_immutable")
        for item in supplied_values:
            one(
                "UPDATE public.project_positions SET location_tag=%s,updated_at=now() "
                "WHERE id=%s AND project_id=%s AND org_id=%s RETURNING id",
                [item["location_tag"], UUID(str(item["position_id"])), project_id, org_id],
            )
        one(
            "INSERT INTO public.project_documentary_inputs("
            "project_id,org_id,payment_terms,quotation_valid_until,created_by) "
            "VALUES(%s,%s,%s,%s,%s) "
            "ON CONFLICT(project_id,org_id) DO UPDATE SET "
            "payment_terms=EXCLUDED.payment_terms,"
            "quotation_valid_until=EXCLUDED.quotation_valid_until,updated_at=now() RETURNING id",
            [project_id, org_id, data["payment_terms"], data["quotation_valid_until"], actor_id],
        )
        for item in supplied_values:
            position_id = UUID(str(item["position_id"]))
            one(
                "INSERT INTO public.position_documentary_inputs("
                "position_id,project_id,org_id,manufacturing_placement_policy_id,"
                "handle_requirement_policy_id,reinforcement_cut_policy_id,workshop_annotations,"
                "structural_inputs,glass_polishing,handle_intents,accessory_schedule,"
                "legacy_handle_migration_confirmed,created_by,calculation_hash) "
                "VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s,%s) "
                "ON CONFLICT(position_id,org_id) DO UPDATE SET "
                "manufacturing_placement_policy_id=EXCLUDED.manufacturing_placement_policy_id,"
                "handle_requirement_policy_id=EXCLUDED.handle_requirement_policy_id,"
                "reinforcement_cut_policy_id=EXCLUDED.reinforcement_cut_policy_id,"
                "workshop_annotations=EXCLUDED.workshop_annotations,"
                "structural_inputs=EXCLUDED.structural_inputs,"
                "glass_polishing=EXCLUDED.glass_polishing,"
                "handle_intents=EXCLUDED.handle_intents,"
                "accessory_schedule=EXCLUDED.accessory_schedule,"
                "calculation_hash=EXCLUDED.calculation_hash,"
                "legacy_handle_migration_confirmed=EXCLUDED.legacy_handle_migration_confirmed,"
                "updated_at=now() RETURNING id",
                [position_id, project_id, org_id,
                 item["manufacturing_placement_policy_id"],
                 item["handle_requirement_policy_id"],
                 item["reinforcement_cut_policy_id"], json_text(item["workshop_annotations"]),
                 json_text(item["structural_inputs"]), json_text(item["glass_polishing"]),
                 json_text(item["handle_intents"]),
                 json_text(item["accessory_schedule"]) if item["accessory_schedule"] is not None else None,
                 item["legacy_handle_migration_confirmed"], actor_id, item["calculation_hash"]],
            )
    return {"project_id": str(project_id), "positions_saved": len(supplied_values)}


def revision_snapshot(version_id: UUID, org_id: UUID) -> tuple[dict[str, object], dict[str, object]]:
    with documentary_backend():
        version = one(
            "SELECT id,project_id,org_id,revision_code,authority_version,snapshot_json::text,"
            "bom_hash,snapshot_sha256,production_allowed,documentary_complete,"
            "emitted_by,emitted_at "
            "FROM public.project_versions WHERE id=%s AND org_id=%s",
            [version_id, org_id],
            "project_version_not_found",
        )
    if version["authority_version"] not in ("SHOT09_V1", "SHOT10_V1"):
        raise DocumentaryError("legacy_version_not_eligible")
    snapshot = _json_object(version["snapshot_json"], "invalid_frozen_revision_snapshot")
    if snapshot_sha256_v1(snapshot) != str(version["snapshot_sha256"]):
        raise DocumentaryError("frozen_revision_hash_mismatch")
    return version, snapshot
