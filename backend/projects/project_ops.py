"""Shared project edits: pure preview, explicit atomic apply, guarded undo."""

from copy import deepcopy
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from uuid import UUID, uuid4

from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.views import APIView

from authentication.errors import contract_error
from documents.repository import documentary_backend
from dekopen_engine.design_operations import OperationError, validate_operation
from dekopen_engine.commercial import indicative_line_net
from dekopen_engine.finishes import finish_selling_delta
from pricing.repository import commercial_backend, encode, json_text, rows
from pricing.serializers import StrictSerializer
from pricing.views import DecimalJSONParser, ERRORS, scope, validate
from projects import service
from projects.ops_registry import DesignOperationSerializer, calculate_product, catalog_for, design_from_product, product_from_position, sale_price, simulate_ops
from projects.serializers import PositionWriteSerializer, PositionUpdateSerializer
from projects.views import SCHEMA, WRITE_ROLES, response

MAX_PROJECT_EDITS = 100


def _plain(value):
    def encode_value(item):
        return item.isoformat() if isinstance(item, datetime) else encode(item)
    return json.loads(json.dumps(value, default=encode_value, allow_nan=False))


def signature(value):
    value = _plain(value)
    # Additive read projections and neutral defaults cannot stale a pre-P21
    # proposal/undo. A declared grouping or a changed order still participates.
    if isinstance(value, dict):
        for position in value.get("positions", []):
            for field in ("system_name", "system_demo", "commercial"):
                position.pop(field, None)
            if not position.get("placement"):
                position.pop("placement", None)
            if position.get("display_order") == position.get("position_index"):
                position.pop("display_order", None)
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def snapshot(org_id, project_id):
    project = service.project_row(org_id, project_id, lock=True)
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM public.project_positions WHERE project_id=%s AND org_id=%s ORDER BY position_index FOR UPDATE", [project_id, org_id])
    positions = service.positions(org_id, project_id)
    with documentary_backend():
        preparation = rows("SELECT to_jsonb(input) AS payload FROM public.position_documentary_inputs input "
            "WHERE project_id=%s AND org_id=%s ORDER BY position_id FOR UPDATE", [project_id, org_id])
        documentary_inputs = [json.loads(item["payload"]) if isinstance(item["payload"], str)
                              else item["payload"] for item in preparation]
    return _plain({"project_id": str(project_id), "revision": project["current_revision"],
                   "updated_at": project["updated_at"], "positions": positions,
                   "documentary_inputs": documentary_inputs})


def _position(after, identity):
    found = next((position for position in after if str(position["id"]) == str(identity)), None)
    if found is None:
        raise OperationError("position_not_found", "La posición no existe en este proyecto.")
    return found


def _targets(after, identities):
    if len(set(identities)) != len(identities):
        raise OperationError("batch_duplicate_targets", "Una posición aparece más de una vez. Revisa la selección.")
    return [_position(after, identity) for identity in identities]


def _copy_position(after, source, location=None):
    duplicate = deepcopy(source)
    duplicate.update(id=str(uuid4()), position_index=max((p["position_index"] for p in after), default=0) + 1,
        display_order=max((p.get("display_order", p["position_index"]) for p in after), default=0) + 1,
        location_tag=source["location_tag"] if location is None else location, source_position_id=source["id"])
    # A copied geometry is not a survey of the new physical opening.
    duplicate["measurements"] = None
    duplicate["commercial"] = None
    after.append(duplicate)


def _edit_values(position):
    return (position["location_tag"], position["quantity"], position["design"],
            position.get("placement", {}), position.get("display_order", position["position_index"]))


def _product(position):
    design = position["design"]
    return product_from_position({"parametric_tree": design["parametric_tree"],
        "width_mm": design["nominal_width_mm"], "height_mm": design["nominal_height_mm"]})


def _design_edit(org_id, position, ops, cache=None):
    cache_key = signature({"design": position["design"], "ops": ops})
    if cache is not None and cache_key in cache:
        position["design"], result = deepcopy(cache[cache_key])
        return result
    # Wildcards expand against the actual graph before entering the engine.
    from dekopen_engine.design_operations import as_product, handled_leaf_keys, walk
    from dekopen_engine.geometry import compute_geometry
    from dekopen_engine.models import ParametricNode
    product = as_product(_product(position))
    expanded = []
    for op in ops:
        modules = product["assembly"]["modules"] if op.get("module") == "*" else [None]
        for module in modules:
            concrete = {**op, "module": module["id"]} if module else op
            if concrete["op"] == "set_handle_height" and concrete.get("bay") == "*":
                targets = [module] if module else [item for item in product["assembly"]["modules"] if item["id"] == concrete.get("module")]
                params = catalog_for(org_id, position["design"]["system_id"])["params"]
                for target in targets:
                    root = {**target["tree"], "width_mm": target["width_mm"], "height_mm": target["height_mm"]}
                    computation = compute_geometry(ParametricNode.model_validate_json(json.dumps(root)), params,
                        finish=position["design"]["color"], diagnostic=True, diagnose_catalog_limits=True)
                    leaf_bays = {bay for bay, _ in handled_leaf_keys(computation)}
                    expanded.extend({**concrete, "module": target["id"], "bay": node["id"], "all_handles": True}
                                    for node in walk(target["tree"]) if node["type"] == "BAY" and node["id"] in leaf_bays)
            else:
                expanded.append(concrete)
    if not expanded:
        return None
    design = position["design"]
    result = simulate_ops(org_id, product, expanded, design["system_id"], design["color"])
    if not result["valid"]:
        diagnoses = [issue.get("message") for issue in result["issues"] if issue.get("message")]
        raise OperationError("simulation_invalid", "El motor rechaza la geometría propuesta. " + " ".join(diagnoses))
    position["design"] = _plain(design_from_product(result["product"], result["system_id"], result["color"]))
    if cache is not None:
        cache[cache_key] = deepcopy((position["design"], result))
    return result


def _new_position(org_id, op, next_index):
    catalog = catalog_for(org_id, op["system_id"])
    choice = next((item for item in catalog["opening_choices"] if item["label"] == op["template"]), None)
    if choice is None and op["template"] not in catalog["openings"]:
        raise OperationError("opening_incompatible", "El sistema seleccionado no admite esa apertura. Elige una serie compatible del catálogo.")
    if op["glass_sku"] not in catalog["glass_skus"] or op["color"] not in catalog["params"].finishes:
        raise OperationError("catalog_selection_invalid", "Elige vidrio y acabado disponibles para esta serie.")
    finish = op["color"]
    identity = str(uuid4())
    product = {"version": "product-v2", "assembly": {"couplings": [], "modules": [{"id": "single",
        "width_mm": op["dims"]["width_mm"], "height_mm": op["dims"]["height_mm"],
        "tree": {"id": "bay", "type": "BAY", "opening_type": "FIXED"}}]}}
    opening = {key: value for key, value in choice.items() if key in {
        "opening", "opening_use", "opening_recipe_code", "hinged_layout", "sliding_layout"}} if choice else {"opening": op["template"]}
    result = simulate_ops(org_id, product, [{"op": "set_opening", "module": "single", **opening},
        {"op": "set_glass", "module": "single", "sku": op["glass_sku"]}], op["system_id"], finish)
    if not result["valid"]:
        raise OperationError("simulation_invalid", "El motor rechaza la plantilla para esa serie y medidas.")
    return {"id": identity, "position_index": next_index, "location_tag": op["location"], "quantity": op.get("quantity", 1),
            "design": _plain(design_from_product(result["product"], op["system_id"], finish)),
            "opening_type": op["template"], "width_mm": op["dims"]["width_mm"], "height_mm": op["dims"]["height_mm"]}


def _new_design_position(org_id, op, next_index):
    catalog = catalog_for(org_id, op["system_id"])
    if op["glass_sku"] not in catalog["glass_skus"] or op["color"] not in catalog["params"].finishes:
        raise OperationError("catalog_selection_invalid", "Elige vidrio y acabado disponibles para esta serie.")
    try:
        design = design_from_product(op["product"], op["system_id"], op["color"])
    except (TypeError, ValueError, KeyError) as error:
        raise OperationError("product_invalid", "La receta no contiene un diseño completo. Vuelve a elegirla en la biblioteca.") from error
    position = {"id": str(uuid4()), "position_index": next_index, "display_order": next_index,
                "location_tag": op["location"], "quantity": op["quantity"], "placement": {}, "design": _plain(design)}
    _design_edit(org_id, position, [{"op": "set_glass", "module": "*", "sku": op["glass_sku"]}])
    return position


def _position_view(org_id, position, cache):
    if position is None:
        return None
    design = position["design"]
    key = signature(design)
    if key not in cache:
        product = _product(position)
        engine = calculate_product(org_id, product, design["system_id"], design["color"])
        cache[key] = {"product": product, "system_id": str(design["system_id"]),
                      "color": design["color"], "engine": engine,
                      "price": sale_price(org_id, product, design["system_id"], design["color"])}
    view = deepcopy(cache[key])
    price = view["price"]
    unit_net = price.get("unit_net", price.get("net"))
    view["quantity"] = position["quantity"]
    view["price"] = {**price, "unit_net": unit_net,
        "net": str(indicative_line_net(Decimal(unit_net), position["quantity"], price["currency"]))
        if unit_net is not None else None}
    if connection.vendor == "postgresql" and "thermal" not in cache[key]:
        from projects.thermal import position_metric
        cache[key]["thermal"] = position_metric(org_id, {
            "id": position["id"], "position_index": position["position_index"],
            "location_tag": position["location_tag"], "quantity": position["quantity"],
            "system_id": design["system_id"], "width_mm": Decimal(design["nominal_width_mm"]),
            "height_mm": Decimal(design["nominal_height_mm"]), "color_interior": design["color"],
            "parametric_tree": design["parametric_tree"],
        })["thermal"]
    if "thermal" in cache[key]:
        view["thermal"] = deepcopy(cache[key]["thermal"])
    return view


def _change_simulation(org_id, change, cache):
    before = _position_view(org_id, change["before"], cache)
    after = _position_view(org_id, change["after"], cache)
    view = after or before
    currency = view["price"]["currency"]
    absent = {"product": None, "quantity": 0, "price": {
        "net": str(indicative_line_net(Decimal("0"), 0, currency)), "currency": currency,
        "source": "Sin posición en este lado de la propuesta."}}
    left, right = before or absent, after or absent
    price = right["price"]
    delta = str(finish_selling_delta(Decimal(left["price"]["net"]), Decimal(price["net"]))) if (
        price.get("net") is not None and left["price"].get("net") is not None) else None
    engine = view["engine"]
    from dekopen_engine.thermal import thermal_delta
    left_metric, right_metric = left.get("thermal"), right.get("thermal")
    uw_delta = thermal_delta(left_metric.get("uw") if left_metric else None,
                             right_metric.get("uw") if right_metric else None)
    return {**right, "position_id": (change["after"] or change["before"])["id"],
            "thermal_delta": {"before": left_metric, "after": right_metric, "delta_uw": uw_delta},
            "system_id": view["system_id"], "color": view["color"],
            "before": left, "price": {**price, "delta_net": delta,
                "reason": price.get("reason") or left["price"].get("reason")},
            "status": engine["status"], "engine": engine,
            "valid": engine["status"] in {"VALID", "MANUFACTURING_INCOMPLETE"}
                and not any(issue.get("severity") == "error" for issue in engine.get("issues", [])),
            "diff": [change]}


def preview_project_operations(org_id, user_id, project_id, raw_ops):
    service.editable(org_id, project_id)
    if not isinstance(raw_ops, list) or not 1 <= len(raw_ops) <= 50:
        raise OperationError("limite_operaciones", "Propón entre una y cincuenta operaciones.")
    ops = [validate_operation(op) for op in raw_ops]
    before = snapshot(org_id, project_id)
    after = deepcopy(before["positions"])
    design_cache = {}
    for op in ops:
        name = op["op"]
        if name == "add_position":
            after.append(_new_position(org_id, op, max((p["position_index"] for p in after), default=0) + 1))
        elif name == "add_design_position":
            after.append(_new_design_position(org_id, op, max((p["position_index"] for p in after), default=0) + 1))
        elif name == "duplicate_position":
            source = _position(after, op["position_id"])
            for _ in range(op["count"]):
                _copy_position(after, source, op["location"])
        elif name in {"duplicate_positions", "remove_positions", "set_positions", "reorder_positions"}:
            targets = _targets(after, op["position_ids"])
            if name == "duplicate_positions":
                for source in targets:
                    _copy_position(after, source)
            elif name == "remove_positions":
                for target in targets:
                    after.remove(target)
            elif name == "reorder_positions":
                if len(targets) != len(after):
                    raise OperationError("reorder_incomplete", "Incluye cada posición del proyecto una sola vez para reordenar.")
                after = targets
                for index, target in enumerate(after, start=1):
                    target["display_order"] = index
            else:
                if not any(field in op for field in ("quantity", "location", "placement")):
                    raise OperationError("batch_change_missing", "Elige cantidad, ubicación, piso, recinto o eje para preparar el cambio.")
                for target in targets:
                    if "quantity" in op:
                        target["quantity"] = op["quantity"]
                    if "location" in op:
                        target["location_tag"] = op["location"]
                    if "placement" in op:
                        target["placement"] = {**target.get("placement", {}), **op["placement"]}
        elif name == "remove_position":
            after.remove(_position(after, op["position_id"]))
        elif name in {"set_quantity", "set_location"}:
            position = _position(after, op["position_id"])
            position["quantity" if name == "set_quantity" else "location_tag"] = op["quantity" if name == "set_quantity" else "location"]
        elif name == "apply_to_positions":
            filter_ = op["filter"]
            wanted = [position for position in after
                      if (not filter_.get("position_ids") or position["id"] in filter_["position_ids"])
                      and (not filter_.get("location_contains") or filter_["location_contains"].casefold() in str(position["location_tag"]).casefold())
                      and (not filter_.get("typology") or filter_["typology"].upper() == str(position.get("typology")).upper())]
            if not wanted:
                raise OperationError("batch_no_targets", "Ninguna posición coincide con el filtro.")
            for position in wanted:
                try:
                    _design_edit(org_id, position, op["ops"], design_cache)
                except OperationError as error:
                    raise OperationError(error.code, f"Posición {position['position_index']} · {position['location_tag'] or 'Sin ubicación'}: {error}") from error
        else:
            raise OperationError("operation_scope_invalid", "Usa operaciones de posición o filtros dentro del proyecto.")
        if len(after) > MAX_PROJECT_EDITS:
            raise OperationError("batch_too_large", "Divide el trabajo en lotes de hasta cien posiciones.")
    # Every changed design goes through the canonical save gate before a preview exists.
    original = {p["id"]: p for p in before["positions"]}
    validated_designs = set()
    for position in after:
        if position["id"] not in original or position["design"] != original[position["id"]]["design"]:
            data = validate(PositionWriteSerializer, {key: position[key] for key in ("location_tag", "quantity", "design")})
            key = signature(position["design"])
            if key not in validated_designs:
                service.calculate_design(org_id, data["design"])
                validated_designs.add(key)
    diff = []
    for position in before["positions"]:
        changed = next((p for p in after if p["id"] == position["id"]), None)
        if changed is None or _edit_values(changed) != _edit_values(position):
            diff.append({"kind": "remove" if changed is None else "change", "index": position["position_index"], "before": position, "after": changed})
    for position in after:
        if position["id"] not in original:
            diff.append({"kind": "add", "index": position["position_index"], "before": None, "after": position})
    cache = {}
    simulations = [_change_simulation(org_id, change, cache) for change in diff]
    return {"project_id": str(project_id), "before_sig": signature(before), "ops": ops, "valid": True,
            "positions": after, "diff": diff, "simulations": simulations}


def _save(org_id, project_id, before, after):
    existing = {p["id"]: p for p in before["positions"]}
    wanted = {p["id"]: p for p in after}
    calculation_cache = {}
    for identity, position in existing.items():
        if identity not in wanted:
            service.delete_position(org_id, UUID(identity), datetime.fromisoformat(position["updated_at"]), refresh_price=False)
    for position in after:
        source = existing.get(position["id"])
        if source and _edit_values(position) == _edit_values(source):
            continue
        if source and position["design"] == source["design"]:
            service.save_position_metadata(org_id, project_id, {**position, "updated_at": source["updated_at"]}, refresh_price=False)
            continue
        data = {key: position[key] for key in ("location_tag", "quantity", "design")}
        data["placement"] = position.get("placement", {})
        if source:
            data["expected_updated_at"] = source["updated_at"]
            data = validate(PositionUpdateSerializer, data)
            saved = service.save_position(org_id, project_id, data, position_id=UUID(position["id"]), apply_defaults=False, calculation_cache=calculation_cache, refresh_price=False)
        else:
            data = validate(PositionWriteSerializer, data)
            saved = service.save_position(org_id, project_id, data, create_id=UUID(position["id"]), create_index=position["position_index"], apply_defaults=False, calculation_cache=calculation_cache, refresh_price=False)
        if saved["display_order"] != position.get("display_order", position["position_index"]):
            service.save_position_metadata(org_id, project_id, {**position, "updated_at": saved["updated_at"]}, refresh_price=False)


def apply_project_operations(org_id, user_id, project_id, data):
    # The project row serializes apply, undo and canonical position saves.
    current = snapshot(org_id, project_id)
    with commercial_backend():
        replay = rows("SELECT id,state,request FROM public.project_edit_operations WHERE org_id=%s AND project_id=%s AND operation_key=%s", [org_id, project_id, data["operation_key"]])
    if replay:
        stored_request = replay[0]["request"]
        if isinstance(stored_request, str):
            stored_request = json.loads(stored_request)
        if stored_request != data["ops"]:
            raise contract_error(409, "operation_key_conflict", "Ese intento ya corresponde a otra propuesta.")
        return {"operation_id": str(replay[0]["id"]), "state": replay[0]["state"], "project": service.project_public(org_id, service.project_row(org_id, project_id), detail=True)}
    if signature(current) != data["before_sig"]:
        raise contract_error(409, "proposal_stale", "El proyecto cambió. Vuelve a simular la propuesta.")
    preview = preview_project_operations(org_id, user_id, project_id, data["ops"])
    _save(org_id, project_id, current, preview["positions"])
    after = snapshot(org_id, project_id)
    with commercial_backend():
        identity = rows("INSERT INTO public.project_edit_operations(org_id,project_id,actor_id,operation_key,state,request,before_state,after_state) VALUES(%s,%s,%s,%s,'APPLIED',%s::jsonb,%s::jsonb,%s::jsonb) RETURNING id",
                        [org_id, project_id, user_id, data["operation_key"], json_text(data["ops"]), json_text(current), json_text(after)])[0]["id"]
    return {"operation_id": str(identity), "state": "APPLIED", "project": service.project_public(org_id, service.project_row(org_id, project_id), detail=True)}


def _restore_documentary_inputs(org_id, project_id, restored):
    """Recover draft preparation cascaded by a reversible position removal."""
    wanted = {position["id"] for position in restored["positions"]}
    with documentary_backend():
        existing = {str(item["position_id"]) for item in rows(
            "SELECT position_id FROM public.position_documentary_inputs WHERE project_id=%s AND org_id=%s",
            [project_id, org_id])}
        for item in restored.get("documentary_inputs", []):
            if (item["org_id"] != str(org_id) or item["project_id"] != str(project_id)
                    or item["position_id"] not in wanted):
                raise contract_error(409, "undo_documentary_scope_invalid", "La preparación documental no corresponde al proyecto que se restaura.")
            if item["position_id"] not in existing:
                # The immutable operation captured this row server-side; callers
                # cannot provide it. RLS, policy-scope and sealing guards still run.
                rows("INSERT INTO public.position_documentary_inputs SELECT "
                    "(jsonb_populate_record(NULL::public.position_documentary_inputs,%s::jsonb)).* RETURNING id",
                    [json_text(item)])


def undo_project_operations(org_id, user_id, project_id, operation_id):
    service.editable(org_id, project_id)
    current = snapshot(org_id, project_id)
    with commercial_backend():
        found = rows("SELECT * FROM public.project_edit_operations WHERE id=%s AND project_id=%s AND org_id=%s FOR UPDATE", [operation_id, project_id, org_id])
    if not found:
        raise contract_error(404, "operation_not_found", "La operación no está disponible.")
    operation = found[0]
    for field in ("before_state", "after_state"):
        if isinstance(operation[field], str):
            operation[field] = json.loads(operation[field])
    if operation["state"] == "UNDONE":
        return {"operation_id": str(operation_id), "state": "UNDONE", "project": service.project_public(org_id, service.project_row(org_id, project_id), detail=True)}
    if signature(current) != signature(operation["after_state"]):
        raise contract_error(409, "undo_stale", "Hay cambios posteriores. Revisa el proyecto antes de deshacer.")
    _save(org_id, project_id, current, operation["before_state"]["positions"])
    _restore_documentary_inputs(org_id, project_id, operation["before_state"])
    with commercial_backend():
        rows("UPDATE public.project_edit_operations SET state='UNDONE',undone_at=clock_timestamp() WHERE id=%s AND org_id=%s RETURNING id", [operation_id, org_id])
    return {"operation_id": str(operation_id), "state": "UNDONE", "project": service.project_public(org_id, service.project_row(org_id, project_id), detail=True)}


def project_operation_state(org_id, project_id, operation_key):
    service.project_row(org_id, project_id)
    with commercial_backend():
        found = rows("SELECT id,state FROM public.project_edit_operations WHERE org_id=%s AND project_id=%s AND operation_key=%s", [org_id, project_id, operation_key])
    return {"operation_id": str(found[0]["id"]) if found else None,
            "state": found[0]["state"] if found else "PROPOSED"}


class ProjectOpsPreviewSerializer(StrictSerializer):
    ops = DesignOperationSerializer(many=True, max_length=50)


class ProjectOpsApplySerializer(ProjectOpsPreviewSerializer):
    before_sig = serializers.RegexField(r"^[0-9a-f]{64}$")
    operation_key = serializers.CharField(min_length=8, max_length=120)


class ProjectOpsPreviewResponseSerializer(serializers.Serializer):
    project_id = serializers.UUIDField()
    before_sig = serializers.CharField()
    valid = serializers.BooleanField()
    ops = DesignOperationSerializer(many=True)
    positions = serializers.ListField(child=serializers.JSONField())
    diff = serializers.ListField(child=serializers.JSONField())
    simulations = serializers.ListField(child=serializers.JSONField())


class ProjectOpsResultSerializer(serializers.Serializer):
    operation_id = serializers.UUIDField()
    state = serializers.ChoiceField(choices=["APPLIED", "UNDONE"])
    project = serializers.JSONField()


class ProjectOpsStateQuerySerializer(StrictSerializer):
    operation_key = serializers.CharField(min_length=8, max_length=120)


class ProjectOpsStateSerializer(serializers.Serializer):
    operation_id = serializers.UUIDField(allow_null=True)
    state = serializers.ChoiceField(choices=["PROPOSED", "APPLIED", "UNDONE"])


class ProjectOpsStateView(APIView):
    @extend_schema(operation_id="project_operations_state",
                   responses={200: ProjectOpsStateSerializer, **ERRORS},
                   **{**SCHEMA, "parameters": [*SCHEMA["parameters"], ProjectOpsStateQuerySerializer]})
    def get(self, request, project_id):
        data = validate(ProjectOpsStateQuerySerializer, request.query_params)
        with scope(request, WRITE_ROLES) as (_, _, org):
            return response(project_operation_state(org, project_id, data["operation_key"]))


class ProjectOpsPreviewView(APIView):
    parser_classes = [DecimalJSONParser]
    @extend_schema(operation_id="project_operations_preview", request=ProjectOpsPreviewSerializer,
                   responses={200: ProjectOpsPreviewResponseSerializer, **ERRORS}, **SCHEMA)
    def post(self, request, project_id):
        data = validate(ProjectOpsPreviewSerializer, request.data)
        try:
            with scope(request, WRITE_ROLES) as (token, _, org):
                return response(preview_project_operations(org, token.user_id, project_id, data["ops"]))
        except OperationError as error:
            raise contract_error(422, error.code, str(error)) from error


class ProjectOpsApplyView(APIView):
    parser_classes = [DecimalJSONParser]
    @extend_schema(operation_id="project_operations_apply", request=ProjectOpsApplySerializer,
                   responses={200: ProjectOpsResultSerializer, **ERRORS}, **SCHEMA)
    def post(self, request, project_id):
        data = validate(ProjectOpsApplySerializer, request.data)
        try:
            with scope(request, WRITE_ROLES) as (token, _, org):
                return response(apply_project_operations(org, token.user_id, project_id, data))
        except OperationError as error:
            raise contract_error(422, error.code, str(error)) from error


class ProjectOpsUndoView(APIView):
    @extend_schema(operation_id="project_operations_undo", request=None,
                   responses={200: ProjectOpsResultSerializer, **ERRORS}, **SCHEMA)
    def post(self, request, project_id, operation_id):
        with scope(request, WRITE_ROLES) as (token, _, org):
            return response(undo_project_operations(org, token.user_id, project_id, operation_id))
