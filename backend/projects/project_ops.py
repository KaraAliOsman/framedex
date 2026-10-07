"""Shared project edits: pure preview, explicit atomic apply, guarded undo."""

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from uuid import UUID, uuid4

from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.views import APIView

from authentication.errors import contract_error
from dekopen_engine.design_operations import BY_NAME, OperationError, validate_operation
from pricing.repository import commercial_backend, encode, json_text, rows
from pricing.serializers import StrictSerializer
from pricing.views import DecimalJSONParser, ERRORS, scope, validate
from projects import service
from projects.ops_registry import DesignOperationSerializer, catalog_for, design_from_product, product_from_position, simulate_ops, resolve_attributes
from projects.serializers import PositionWriteSerializer, PositionUpdateSerializer
from projects.views import SCHEMA, WRITE_ROLES, response

MAX_PROJECT_EDITS = 100


def _plain(value):
    def encode_value(item):
        return item.isoformat() if isinstance(item, datetime) else encode(item)
    return json.loads(json.dumps(value, default=encode_value, allow_nan=False))


def signature(value):
    return hashlib.sha256(json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def snapshot(org_id, project_id):
    project = service.project_row(org_id, project_id, lock=True)
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM public.project_positions WHERE project_id=%s AND org_id=%s ORDER BY position_index FOR UPDATE", [project_id, org_id])
    positions = service.positions(org_id, project_id)
    return _plain({"project_id": str(project_id), "revision": project["current_revision"],
                   "updated_at": project["updated_at"], "positions": positions})


def _position(after, identity):
    found = next((position for position in after if str(position["id"]) == str(identity)), None)
    if found is None:
        raise OperationError("position_not_found", "La posición no existe en este proyecto.")
    return found


def _product(position):
    design = position["design"]
    return product_from_position({"parametric_tree": design["parametric_tree"],
        "width_mm": design["nominal_width_mm"], "height_mm": design["nominal_height_mm"]})


def _design_edit(org_id, position, ops):
    # Wildcards expand against the actual graph before entering the engine.
    product = _product(position)
    expanded = []
    for op in ops:
        if op.get("module") == "*":
            expanded.extend({**op, "module": module["id"]} for module in product["assembly"]["modules"])
        else:
            expanded.append(op)
    design = position["design"]
    result = simulate_ops(org_id, product, expanded, design["system_id"], design["color"])
    if not result["valid"]:
        raise OperationError("simulation_invalid", "El motor rechaza la geometría propuesta.")
    position["design"] = _plain(design_from_product(result["product"], result["system_id"], result["color"]))
    return result


def _new_position(org_id, op, next_index):
    catalog = catalog_for(org_id, op["system_id"])
    if op["template"] not in catalog["openings"]:
        raise OperationError("opening_incompatible", "El sistema seleccionado no admite esa apertura. Elige una serie compatible del catálogo.")
    params = catalog["params"]
    # A catalog-backed default is explicit in the preview, never technical guesswork.
    skus = sorted(catalog["glass_skus"])
    finish = next(iter(params.finishes), None)
    if not skus or finish is None:
        raise OperationError("catalog_default_missing", "La serie no declara vidrio o acabado inicial. Completa el catálogo.")
    identity = str(uuid4())
    product = {"version": "product-v2", "assembly": {"couplings": [], "modules": [{"id": "single",
        "width_mm": op["dims"]["width_mm"], "height_mm": op["dims"]["height_mm"],
        "tree": {"id": "bay", "type": "BAY", "opening_type": op["template"]}}]}}
    result = simulate_ops(org_id, product, [{"op": "set_glass", "module": "single", "sku": skus[0]}], op["system_id"], finish)
    if not result["valid"]:
        raise OperationError("simulation_invalid", "El motor rechaza la plantilla para esa serie y medidas.")
    return {"id": identity, "position_index": next_index, "location_tag": op["location"], "quantity": op.get("quantity", 1),
            "design": _plain(design_from_product(result["product"], op["system_id"], finish)),
            "opening_type": op["template"], "width_mm": op["dims"]["width_mm"], "height_mm": op["dims"]["height_mm"],
            "defaults": {"glass_sku": skus[0], "finish": finish, "source": "Opciones reales del catálogo, declaradas en la vista previa."}}


def preview_project_operations(org_id, user_id, project_id, raw_ops):
    service.editable(org_id, project_id)
    if not isinstance(raw_ops, list) or not 1 <= len(raw_ops) <= 50:
        raise OperationError("limite_operaciones", "Propón entre una y cincuenta operaciones.")
    ops = [validate_operation(op) for op in raw_ops]
    before = snapshot(org_id, project_id)
    after = deepcopy(before["positions"])
    simulations = []
    for op in ops:
        name = op["op"]
        if name == "add_position":
            after.append(_new_position(org_id, op, max((p["position_index"] for p in after), default=0) + 1))
        elif name == "duplicate_position":
            source = _position(after, op["position_id"])
            for _ in range(op["count"]):
                duplicate = deepcopy(source)
                duplicate.update(id=str(uuid4()), position_index=max((p["position_index"] for p in after), default=0) + 1,
                                 location_tag=op["location"], source_position_id=source["id"])
                after.append(duplicate)
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
                design_ops = []
                for child in op["ops"]:
                    if BY_NAME[child["op"]]["scope"] == "position":
                        _attribute(org_id, position, child)
                    else:
                        design_ops.append(child)
                if design_ops:
                    simulations.append({"position_id": position["id"], **_design_edit(org_id, position, design_ops)})
        else:
            raise OperationError("operation_scope_invalid", "Usa operaciones de posición o filtros dentro del proyecto.")
        if len(after) > MAX_PROJECT_EDITS:
            raise OperationError("batch_too_large", "Divide el trabajo en lotes de hasta cien posiciones.")
    # Every changed design goes through the canonical save gate before a preview exists.
    original = {p["id"]: p for p in before["positions"]}
    for position in after:
        if position["id"] not in original or position["design"] != original[position["id"]]["design"]:
            service.calculate_design(org_id, validate(PositionWriteSerializer, {key: position[key] for key in ("location_tag", "quantity", "design")})["design"])
    diff = []
    for position in before["positions"]:
        changed = next((p for p in after if p["id"] == position["id"]), None)
        if changed is None or any(changed[key] != position[key] for key in ("location_tag", "quantity", "design")):
            diff.append({"kind": "remove" if changed is None else "change", "index": position["position_index"], "before": position, "after": changed})
    for position in after:
        if position["id"] not in original:
            diff.append({"kind": "add", "index": position["position_index"], "before": None, "after": position})
    return {"project_id": str(project_id), "before_sig": signature(before), "ops": ops, "valid": True,
            "positions": after, "diff": diff, "simulations": simulations}


def _attribute(org_id, position, op):
    design = position["design"]
    resolved = resolve_attributes(org_id, design["system_id"], design["color"], op)
    design.update(system_id=resolved["system_id"], color=resolved["color"])


def _save(org_id, project_id, before, after):
    existing = {p["id"]: p for p in before["positions"]}
    wanted = {p["id"]: p for p in after}
    for identity, position in existing.items():
        if identity not in wanted:
            service.delete_position(org_id, UUID(identity), datetime.fromisoformat(position["updated_at"]))
    for position in after:
        source = existing.get(position["id"])
        if source and all(position[key] == source[key] for key in ("location_tag", "quantity", "design")):
            continue
        data = {key: position[key] for key in ("location_tag", "quantity", "design")}
        if source:
            data["expected_updated_at"] = source["updated_at"]
            data = validate(PositionUpdateSerializer, data)
            service.save_position(org_id, project_id, data, position_id=UUID(position["id"]), apply_defaults=False)
        else:
            data = validate(PositionWriteSerializer, data)
            service.save_position(org_id, project_id, data, create_id=UUID(position["id"]), create_index=position["position_index"], apply_defaults=False)


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
    with commercial_backend():
        rows("UPDATE public.project_edit_operations SET state='UNDONE',undone_at=clock_timestamp() WHERE id=%s AND org_id=%s RETURNING id", [operation_id, org_id])
    return {"operation_id": str(operation_id), "state": "UNDONE", "project": service.project_public(org_id, service.project_row(org_id, project_id), detail=True)}


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
