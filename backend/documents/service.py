"""Atomic APPLIED-pricing freeze into one immutable documentary REV-A."""

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
from dekopen_engine.geometry import compute_geometry
from dekopen_engine.inspection_models import (
    InspectionMode,
    InspectorInput,
    RuleEvaluationStatus,
)
from dekopen_engine.inspector import inspect
from dekopen_engine.manufacturing import project_manufacturing_facts_v1
from dekopen_engine.purchasing import (
    HardwareSelectionV1,
    PositionPurchaseInputV1,
    project_purchase_requirements_v1,
)
from dekopen_engine.snapshot import calculation_response
from engine_api.adapter import normalized_root_from_api
from engine_api.cutting_repository import CuttingRepository
from engine_api.inspection_repository import InspectorRepository
from engine_api.repository import SystemParamsRepository
from pricing.repository import commercial_backend

from documents.repository import (
    DocumentaryError,
    PurchaseAuthorities,
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


def _position_rows(project_id: UUID, org_id: UUID) -> list[dict[str, object]]:
    return rows(
        "SELECT position.*,input.id AS documentary_input_id,"
        "input.manufacturing_placement_policy_id,input.handle_requirement_policy_id,"
        "input.reinforcement_cut_policy_id,input.workshop_annotations::text,"
        "input.structural_inputs::text,input.glass_polishing::text,"
        "input.handle_intents::text,input.accessory_schedule::text,"
        "input.legacy_handle_migration_confirmed "
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
    pricing_operation_id: UUID, confirmed: bool
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
        existing = rows(
            "SELECT id,pricing_operation_id,revision_code,bom_hash,snapshot_sha256,"
            "production_allowed,documentary_complete,emitted_at "
            "FROM public.project_versions WHERE project_id=%s AND org_id=%s",
            [project_id, org_id],
        )
        if existing:
            if len(existing) != 1 or str(existing[0]["pricing_operation_id"]) != str(
                pricing_operation_id
            ):
                raise DocumentaryError("initial_revision_already_sealed")
            return {
                **{key: (str(value) if isinstance(value, UUID) else value)
                   for key, value in existing[0].items()},
                "pricing_operation_id": str(pricing_operation_id),
                "created": False,
            }
        if project["status"] != "DRAFT" or project["current_revision"] != "REV-A":
            raise DocumentaryError("initial_revision_not_available")
        operation = one(
            "SELECT id,org_id,project_id,requested_by,request::text,input_snapshot::text,"
            "result::text,source_revision,state,approved_by,approved_at,reason,created_at "
            "FROM public.pricing_operations WHERE id=%s AND org_id=%s AND project_id=%s",
            [pricing_operation_id, org_id, project_id],
            "pricing_operation_not_found",
        )
        if operation["state"] != "APPLIED":
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
        stock_repository = CuttingRepository()
        for position in positions:
            position_id = str(position["id"])
            tree = _json_object(position["parametric_tree"], "invalid_parametric_tree")
            color = (
                "WHITE"
                if position["color_interior"] == "WHITE" and position["color_exterior"] == "WHITE"
                else "FOILED"
            )
            system_id = UUID(str(position["system_id"]))
            params = SystemParamsRepository().load_visible(system_id, org_id)
            root = normalized_root_from_api(
                parametric_tree=tree,
                nominal_width_mm=D(str(position["width_mm"])),
                nominal_height_mm=D(str(position["height_mm"])),
                color=color,
                params=params,
            )
            computation = compute_geometry(root, params, diagnostic=True)
            if computation.result is None or computation.manufacturing_trace is None:
                raise DocumentaryError("documentary_geometry_incomplete")
            result = computation.result
            current_bom = result.model_dump(mode="json")
            if position_id not in priced_bom or not _same_documentary_value(
                current_bom, priced_bom[position_id]
            ) or not _same_documentary_value(current_bom, decoded(position["bom_snapshot"])):
                raise DocumentaryError("applied_pricing_technical_binding_drift")

            annotations = workshop_annotations(position["workshop_annotations"])
            structural = structural_inputs(position["structural_inputs"])
            targets = {(opening.bay_id, None) for opening in computation.openings} | {
                (leaf.bay_id, leaf.leaf_id) for leaf in computation.leaves
            }
            if any((item.bay_id, item.leaf_id) not in targets for item in annotations):
                raise DocumentaryError("workshop_annotation_target_invalid")
            spans = {span.target_id for span in computation.spans}
            if any(item.target_id not in spans for item in structural):
                raise DocumentaryError("structural_input_target_invalid")
            if color != "WHITE" or any(item.finish_class not in (None, "WHITE") for item in annotations):
                raise DocumentaryError("unsupported_documentary_color")

            inspector_authorities = InspectorRepository().load(system_id, org_id)
            cutting = stock_repository.for_result(result, system_id, org_id, color)
            inertias: dict[str, Decimal | None] = {}
            for span in computation.spans:
                _, inertia = stock_repository.reinforcement_stock(
                    system_id, org_id, span.parent_profile_sku, None, color
                )
                inertias[span.target_id] = inertia
            calculation_request = {
                "system_id": str(system_id),
                "parametric_tree": tree,
                "nominal_width_mm": D(str(position["width_mm"])),
                "nominal_height_mm": D(str(position["height_mm"])),
                "color": color,
            }
            source_hash = calculation_response(calculation_request, result)["calculation_hash"]
            inspection = inspect(InspectorInput(
                computation=computation,
                chamber_clearance_mm=inspector_authorities.chamber_clearance_mm,
                annotations=annotations,
                structural_inputs=structural,
                reinforcement_ix_by_target=inertias,
                mode=InspectionMode.DESIGN,
                source_calculation_hash=str(source_hash),
            ), inspector_authorities.config)
            if not inspection.production_allowed or inspection.status == "RED":
                raise DocumentaryError("inspector_red_blocks_documentary_freeze")
            position_complete = not any(
                evaluation.status is RuleEvaluationStatus.MISSING_INPUT
                for evaluation in inspection.evaluations
            )
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
            units = [project_manufacturing_facts_v1(
                trace=computation.manufacturing_trace,
                position_id=position_id,
                position_index=int(position["position_index"]),
                repetition_index=repetition,
                placement_policy=policies.placement,
                handle_policy=policies.handles,
                reinforcement_policy=policies.reinforcement,
                handle_intents=intents,
                resolved_reinforcement_skus=cutting.reinforcement_skus,
                legacy_handle_height_present=_tree_has_legacy_handle(tree),
                legacy_handle_migration_confirmed=bool(
                    position["legacy_handle_migration_confirmed"]
                ),
            ) for repetition in range(1, quantity + 1)]
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
            accessories = accessory_schedule(
                position["accessory_schedule"], str(position["documentary_input_id"])
            )
            location_tag = str(position["location_tag"] or "")
            purchase_position = PositionPurchaseInputV1(
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
            )
            purchase_positions.append(purchase_position)
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
                "accessory_schedule": accessories.model_dump(mode="python"),
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
            manufacturing.extend(unit.model_dump(mode="python") for unit in units)
            inspector_evidence.append({
                "position_id": position_id,
                "mode": "DESIGN",
                "result": inspection.model_dump(mode="python"),
                "config": inspector_authorities.config.model_dump(mode="python"),
                "chamber_clearance_mm": inspector_authorities.chamber_clearance_mm,
                "documentary_complete": position_complete,
            })

        if purchase_authorities is None:
            raise DocumentaryError("purchase_authorities_required")
        purchase = project_purchase_requirements_v1(
            positions=purchase_positions,
            stock_bindings=purchase_authorities.stock_bindings,
            glass_mappings=purchase_authorities.glass_mappings,
            hardware_mappings=purchase_authorities.hardware_mappings,
            panel_authorities=purchase_authorities.panel_authorities,
        )
        revision = "REV-A"
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
            "purchase_requirements": purchase.model_dump(mode="python"),
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
            "production_allowed": True,
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
            "VALUES(%s,%s,%s,%s::jsonb,NULL,%s,%s,'SHOT09_V1',%s,%s,%s,%s,TRUE,%s) "
            "RETURNING id,revision_code,bom_hash,snapshot_sha256,production_allowed,"
            "documentary_complete,emitted_at",
            [project_id, org_id, revision,
             documentary_canonical_json_v1(snapshot).decode("utf-8"), actor_id, sealed_at,
             pricing_operation_id, DOCUMENTARY_CANONICAL_VERSION, bom_hash,
             snapshot_sha256, documentary_complete],
        )
        version_id = UUID(str(version["id"]))
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
        return {
            "id": str(version_id),
            "pricing_operation_id": str(pricing_operation_id),
            "created": True,
            "revision_code": revision,
            "bom_hash": bom_hash,
            "snapshot_sha256": snapshot_sha256,
            "production_allowed": True,
            "documentary_complete": documentary_complete,
            "emitted_at": sealed_at,
            "purchase_projection_hash": purchase.projection_hash,
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
            "SELECT id FROM public.project_positions WHERE project_id=%s AND org_id=%s "
            "ORDER BY position_index FOR UPDATE",
            [project_id, org_id],
        )
        expected = {str(item["id"]) for item in positions}
        supplied = {str(item["position_id"]) for item in supplied_values}
        if supplied != expected or len(supplied_values) != len(supplied):
            raise DocumentaryError("documentary_position_coverage_required")
    with documentary_backend():
        if rows(
            "SELECT id FROM public.project_versions WHERE project_id=%s AND org_id=%s",
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
                "legacy_handle_migration_confirmed,created_by) "
                "VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,%s,%s) "
                "ON CONFLICT(position_id,org_id) DO UPDATE SET "
                "manufacturing_placement_policy_id=EXCLUDED.manufacturing_placement_policy_id,"
                "handle_requirement_policy_id=EXCLUDED.handle_requirement_policy_id,"
                "reinforcement_cut_policy_id=EXCLUDED.reinforcement_cut_policy_id,"
                "workshop_annotations=EXCLUDED.workshop_annotations,"
                "structural_inputs=EXCLUDED.structural_inputs,"
                "glass_polishing=EXCLUDED.glass_polishing,"
                "handle_intents=EXCLUDED.handle_intents,"
                "accessory_schedule=EXCLUDED.accessory_schedule,"
                "legacy_handle_migration_confirmed=EXCLUDED.legacy_handle_migration_confirmed,"
                "updated_at=now() RETURNING id",
                [position_id, project_id, org_id,
                 item["manufacturing_placement_policy_id"],
                 item["handle_requirement_policy_id"],
                 item["reinforcement_cut_policy_id"], json_text(item["workshop_annotations"]),
                 json_text(item["structural_inputs"]), json_text(item["glass_polishing"]),
                 json_text(item["handle_intents"]), json_text(item["accessory_schedule"]),
                 item["legacy_handle_migration_confirmed"], actor_id],
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
    if version["authority_version"] != "SHOT09_V1":
        raise DocumentaryError("legacy_version_not_eligible")
    snapshot = _json_object(version["snapshot_json"], "invalid_frozen_revision_snapshot")
    if snapshot_sha256_v1(snapshot) != str(version["snapshot_sha256"]):
        raise DocumentaryError("frozen_revision_hash_mismatch")
    return version, snapshot
