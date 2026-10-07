"""Shared editing contract. Pure, atomic transformations; no provider or I/O.

The browser consumes the effects calculated here. An effect binds to the
complete previous graph, so applying a stale or partial proposal is refused.
Catalog identifiers and physical choices are authority, never defaults.
"""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
from typing import Any, cast

from .geometry import compute_geometry, validate_sliding_layout
from .catalog_rules import CatalogRuleError, FAMILY_OPENINGS, validate_family
from .models import BayOpeningType, OpeningMovement, LeafRole, ParametricNode, ProfileRole, SystemParams, HardwareSelection
from .glass_composition import GlassProcessing
from .openings import OpeningCapabilityError, normalize_opening_tree, node_opening, node_use, resolve_capability
from .product import FramelessSpec
from .extra_models import ExtraSelection, ExtraContext

VERSION = "design-ops-v1"
MAX_OPERATIONS = 50
MAX_MODULES = 12
MM = {"type": "string", "pattern": r"^-?\d+(?:\.\d{1,2})?$", "description": "Milímetros decimales exactos; sin separador de miles."}
REF = {"type": "string", "minLength": 1, "maxLength": 160}
TEXT = {"type": "string", "minLength": 1, "maxLength": 100}
COUNT = {"type": "integer", "minimum": 1, "maximum": 100}


def model_schema(model: Any) -> dict[str, Any]:
    """Inline finite domain schemas so HTTP and model tools share their types."""
    schema = model.model_json_schema()
    definitions = schema.pop("$defs", {})
    def expand(value: Any) -> Any:
        if isinstance(value, list):
            return [expand(item) for item in value]
        if not isinstance(value, dict):
            return value
        if "$ref" in value:
            return expand(deepcopy(definitions[value["$ref"].split("/")[-1]]))
        if "const" in value:
            value = {**value, "enum": [value["const"]]}
            value.pop("const")
        # Decimal is transported as a string, never a JSON float.
        if "anyOf" in value and {item.get("type") for item in value["anyOf"] if item.get("type") != "null"} == {"number", "string"}:
            exact = {"type": "string", "pattern": r"^-?\d+(?:\.\d+)?$"}
            return optional(exact) if any(item.get("type") == "null" for item in value["anyOf"]) else exact
        return {key: expand(child) for key, child in value.items() if key != "title"}
    return cast(dict[str, Any], expand(schema))


def optional(schema: dict[str, Any]) -> dict[str, Any]:
    return {"oneOf": [schema, {"type": "null"}]}


BAY_PATCH = {"type": "object", "additionalProperties": False, "minProperties": 1, "properties": {
    "hardware_set_sku": optional(REF), "hardware_selection": optional(model_schema(HardwareSelection)),
    "glass_processing": optional(model_schema(GlassProcessing)),
    "sill_height_mm": optional(MM),
    "is_sidelight": {"type": "boolean"}, "door_handedness": {"type": ["string", "null"], "enum": ["LEFT", "RIGHT", None]},
}}


def choice(*values: str) -> dict[str, Any]:
    return {"type": "string", "enum": list(values)}


def spec(name: str, label: str, properties: dict[str, Any], required: list[str], example: dict[str, Any],
         *, scope: str = "design", precondition: str = "Diseño editable y serie visible; el motor valida la geometría.") -> dict[str, Any]:
    return {"name": name, "description": label, "scope": scope, "preconditions": [precondition],
            "handler": "apply_operations" if scope == "design" else "preview_project_operations",
            "schema": {"type": "object", "additionalProperties": False,
                       "properties": {"op": {"type": "string", "enum": [name]}, **properties},
                       "required": ["op", *required]}, "examples": [{"op": name, **example}]}


TARGET = {"module": REF, "bay": REF}
DIVIDER = {"module": REF, "divider": REF}
REGISTRY = [
    spec("split_bay", "Divide un paño dentro del mismo marco; V crea montante y H travesaño.",
         {**TARGET, "axis": choice("V", "H"), "offset_mm": MM, "from": choice("START", "END", "CENTER")},
         ["bay", "axis", "from"], {"bay": "b1", "axis": "H", "offset_mm": "400", "from": "START"}),
    spec("move_divider", "Mueve el eje de un montante o travesaño.",
         {**DIVIDER, "offset_mm": MM, "from": choice("START", "END", "CENTER")},
         ["divider", "offset_mm"], {"divider": "d1", "offset_mm": "400"}),
    spec("remove_divider", "Retira una división conservando el paño indicado; rechaza estructura anidada.",
         {**DIVIDER, "keep_bay": REF}, ["divider"], {"divider": "d1"}),
    spec("set_bay_size", "Ajusta un paño moviendo su división inmediata; requiere eje compatible.",
         {**TARGET, "axis": choice("V", "H"), "size_mm": MM}, ["bay", "axis", "size_mm"],
         {"bay": "b1", "axis": "V", "size_mm": "600"}),
    spec("equalize_bays", "Reparte el marco en paños con ejes iguales; count cambia la cantidad en un solo marco.",
         {"module": REF, "axis": choice("V", "H"), "count": {**COUNT, "maximum": 12}}, ["module", "axis"],
         {"module": "m1", "axis": "V", "count": 3}),
    spec("set_opening", "Cambia la apertura de un paño o todos los paños del módulo según el catálogo.",
         {**TARGET, "opening": {"oneOf": [choice(*(v.value for v in BayOpeningType)), {"type": "object"}]},
          "opening_use": choice("WINDOW", "DOOR"), "hinged_layout": {"type": ["object", "null"]},
          "sliding_layout": {"type": ["object", "null"]}}, ["module", "opening"],
         {"module": "m1", "bay": "b2", "opening": "TILT_TURN_LEFT"}),
    spec("flip_handing", "Invierte bisagras y cierre conservando movimiento y dirección.", TARGET, ["bay"], {"bay": "b1"}),
    spec("set_handle_height", "Declara la altura local de manilla; FLOOR exige antepecho explícito.",
         {**TARGET, "height_mm": MM, "reference": choice("LEAF_TOP", "LEAF_BOTTOM", "FLOOR"), "sill_height_mm": MM},
         ["bay", "height_mm", "reference"], {"bay": "b1", "height_mm": "400", "reference": "LEAF_TOP"}),
    spec("set_sliding_layout", "Define corredera: X móvil, O fijo; cada móvil declara carril.",
         {**TARGET, "panels": {"type": "string", "pattern": "^[XO]{2,4}$"}, "tracks": {"type": "integer", "minimum": 2, "maximum": 4},
          "panel_tracks": {"type": "array", "items": {"type": ["integer", "null"]}},
          "travel_mm": MM}, ["bay", "panels", "tracks"], {"bay": "b1", "panels": "XX", "tracks": 2}),
    spec("set_travel", "Prepara el recorrido declarado de corredera; exige soporte explícito del modelo.",
         {**TARGET, "travel_mm": MM}, ["bay", "travel_mm"], {"bay": "b1", "travel_mm": "600"},
         precondition="La serie y el contrato de corredera declaran recorrido editable; en caso contrario devuelve un bloqueo."),
    spec("set_glass", "Asigna SKU real o composición que coincida exactamente con una receta del catálogo.",
         {**TARGET, "sku": REF, "composition": TEXT}, ["module"], {"module": "m1", "sku": "VIDRIO-BASE"}),
    spec("set_glass_thickness", "Elige un espesor declarado por la serie.", {"module": REF, "mm": MM},
         ["module", "mm"], {"module": "m1", "mm": "4"}),
    spec("set_panel", "Asigna o retira un panel disponible.", {**TARGET, "sku": {"type": ["string", "null"]}},
         ["module", "sku"], {"module": "m1", "sku": None}),
    spec("set_finish", "Selecciona caras interior/exterior de la carta de acabados real.",
         {"interior": TEXT, "exterior": TEXT}, ["interior", "exterior"], {"interior": "WHITE", "exterior": "WHITE"}, scope="position"),
    spec("set_system", "Cambia la serie y vuelve a validar todas sus compatibilidades.", {"system_id": REF},
         ["system_id"], {"system_id": "id-visible"}, scope="position"),
    spec("set_module_width", "Fija el ancho nominal de un módulo.", {"module": REF, "width_mm": MM},
         ["module", "width_mm"], {"module": "m1", "width_mm": "1800"}),
    spec("resize", "Suma un incremento a las dimensiones actuales; el motor calcula el nuevo valor exacto.",
         {"module": REF, "delta_width_mm": MM, "delta_height_mm": MM}, ["module"],
         {"module": "m1", "delta_width_mm": "200"}),
    spec("set_total_width", "Reparte proporcionalmente el ancho total entre módulos.", {"width_mm": MM}, ["width_mm"], {"width_mm": "2400"}),
    spec("set_height", "Fija el alto nominal de los módulos.", {"height_mm": MM}, ["height_mm"], {"height_mm": "1350"}),
    spec("equalize_widths", "Iguala anchos nominales conservando exactamente el total.", {}, [], {}),
    spec("equalize_angles", "Iguala ángulos según la primera unión declarada.", {}, [], {}),
    spec("set_coupling_angle", "Fija el ángulo de una unión existente.", {"coupling": REF, "angle_deg": MM}, ["coupling", "angle_deg"], {"coupling": "c1", "angle_deg": "15"}),
    spec("set_coupling_kind", "Cambia el tipo de unión compatible con sus bordes.", {"coupling": REF, "kind": choice("INLINE", "STACKED", "TEE", "CORNER")}, ["coupling", "kind"], {"coupling": "c1", "kind": "INLINE"}),
    spec("set_module_count", "Cambia la cantidad de marcos independientes acoplados; no equivale a dividir paños.", {"count": {**COUNT, "maximum": 12}}, ["count"], {"count": 2}),
    spec("add_unit", "Agrega un marco unido en un extremo libre.", {"side": choice("left", "right")}, ["side"], {"side": "right"}),
    spec("remove_unit", "Quita un marco; conserva las conexiones restantes compatibles.", {"module": REF}, ["module"], {"module": "m2"}),
    spec("duplicate_module", "Duplica un marco sobre un borde libre.", {"module": REF}, ["module"], {"module": "m1"}),
    spec("add_stacked_unit", "Agrega un fijo superior conectado al borde libre del marco.", {"module": REF}, ["module"], {"module": "m1"}),
    spec("insert_module", "Inserta un marco dentro de una unión recta existente.", {"coupling": REF}, ["coupling"], {"coupling": "c1"}),
    spec("remove_coupling", "Desconecta una unión conservando sus marcos.", {"coupling": REF}, ["coupling"], {"coupling": "c1"}),
    spec("set_bay_spec", "Declara herraje, tratamiento y clasificación de un paño; el motor comprueba la autoridad.",
         {**TARGET, "patch": BAY_PATCH}, ["module", "bay", "patch"], {"module": "m1", "bay": "b1", "patch": {"hardware_set_sku": None}}),
    spec("clear_glass_thickness", "Retira el espesor declarado y deja su ausencia explícita.",
         {"module": REF}, ["module"], {"module": "m1"}),
    spec("set_module_tree", "Aplica una especificación declarada o copiada conservando la identidad del marco; el motor la valida completa.",
         {"module": REF, "tree": {"type": "object"}}, ["module", "tree"], {"module": "m1", "tree": {"id": "b1", "type": "BAY", "opening_type": "FIXED"}}),
    spec("set_extras", "Declara accesorios y medidas del vano sobre el marco; las cantidades salen del motor.",
         {"module": REF, "extras": {"type": "array", "maxItems": 30, "items": model_schema(ExtraSelection)}, "context": optional(model_schema(ExtraContext))},
         ["module", "extras"], {"module": "m1", "extras": []}),
    spec("set_frameless", "Declara soportes y herrajes del paño sin marco; la evaluación comprueba su catálogo.",
         {"module": REF, "spec": optional(model_schema(FramelessSpec))}, ["module", "spec"], {"module": "m1", "spec": {"supports": [], "fittings": []}}),
    spec("set_contour_vertex", "Fija un vértice del contorno; END mide la distancia desde el extremo del marco.",
         {"module": REF, "index": {"type": "integer", "minimum": 0, "maximum": 255}, "x_mm": MM, "y_mm": MM, "from": choice("START", "END")},
         ["module", "index", "x_mm", "y_mm"], {"module": "m1", "index": 0, "x_mm": "0", "y_mm": "0"}),
    spec("set_contour_bulge", "Declara la flecha de un arco del contorno.",
         {"module": REF, "index": {"type": "integer", "minimum": 0, "maximum": 255}, "rise_mm": MM},
         ["module", "index", "rise_mm"], {"module": "m1", "index": 0, "rise_mm": "200"}),
    spec("resize_seam", "Desplaza la unión entre dos marcos; conserva exactamente su ancho total.",
         {"left": REF, "right": REF, "delta_mm": MM}, ["left", "right", "delta_mm"], {"left": "m1", "right": "m2", "delta_mm": "100"}),
    spec("swap_modules", "Intercambia dos marcos en la disposición existente.",
         {"module": REF, "other": REF}, ["module", "other"], {"module": "m1", "other": "m2"}),
    spec("set_coupler_sku", "Declara el acople real de una unión, o retira su selección.",
         {"coupling": REF, "sku": optional(REF)}, ["coupling", "sku"], {"coupling": "c1", "sku": None}),
    spec("set_location", "Cambia la ubicación de una posición.", {"position_id": REF, "location": TEXT}, ["position_id", "location"], {"position_id": "id-visible", "location": "Cocina"}, scope="project"),
    spec("set_quantity", "Cambia la cantidad exacta de una posición.", {"position_id": REF, "quantity": {**COUNT, "maximum": 2147483647}}, ["position_id", "quantity"], {"position_id": "id-visible", "quantity": 4}, scope="project"),
    spec("add_position", "Crea una posición desde una plantilla real o apertura catalogada y dimensiones explícitas.",
         {"system_id": REF, "template": TEXT, "dims": {"type": "object", "additionalProperties": False, "properties": {"width_mm": MM, "height_mm": MM}, "required": ["width_mm", "height_mm"]}, "location": TEXT, "quantity": COUNT, "glass_sku": REF, "color": TEXT},
         ["system_id", "template", "dims", "location", "glass_sku", "color"], {"system_id": "id-visible", "template": "SLIDING_2L", "dims": {"width_mm": "1600", "height_mm": "1100"}, "location": "Cocina", "glass_sku": "VIDRIO-BASE", "color": "WHITE"}, scope="project"),
    spec("duplicate_position", "Crea copias exactas de una posición; count es el número de copias nuevas.", {"position_id": REF, "count": COUNT, "location": TEXT}, ["position_id", "count", "location"], {"position_id": "id-visible", "count": 4, "location": "Dormitorios"}, scope="project"),
    spec("remove_position", "Quita una posición de la revisión editable.", {"position_id": REF}, ["position_id"], {"position_id": "id-visible"}, scope="project"),
    spec("apply_to_positions", "Propone un cambio sobre posiciones filtradas por ubicación, tipología o ids.", {"filter": {"type": "object", "additionalProperties": False, "properties": {"location_contains": TEXT, "typology": TEXT, "position_ids": {"type": "array", "items": REF}}}, "ops": {"type": "array", "minItems": 1, "maxItems": 50, "items": {"type": "object"}}}, ["filter", "ops"], {"filter": {"location_contains": "segundo piso"}, "ops": [{"op": "set_glass", "module": "*", "sku": "VIDRIO-BASE"}]}, scope="project"),
    *[spec(name, description, {"project_id": REF}, ["project_id"], {"project_id": "id-visible"}, scope="prepare",
           precondition="Solo prepara la ruta; la acción consecuente exige un clic humano independiente.")
      for name, description in [("prepare_emit", "Prepara emisión de cotización."), ("prepare_release", "Prepara liberación de producción."),
                                ("prepare_purchase", "Prepara compra de faltantes."), ("prepare_payment_link", "Prepara enlace de pago.")]],
]
BY_NAME = {item["name"]: item for item in REGISTRY}
OPERATION_SCHEMA = {"oneOf": [item["schema"] for item in REGISTRY], "discriminator": {"propertyName": "op"}}


class OperationError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        super().__init__(detail)


def _validate(value: Any, schema: dict[str, Any], path: str) -> None:
    import re
    alternatives = schema.get("oneOf", schema.get("anyOf"))
    if alternatives is not None:
        for alternative in alternatives:
            try:
                _validate(value, alternative, path)
                return
            except OperationError:
                pass
        raise OperationError("operation_schema_invalid", f"Revisa {path}.")
    types = schema.get("type", [])
    types = [types] if isinstance(types, str) else types
    matches = {"null": value is None, "string": isinstance(value, str),
               "object": isinstance(value, dict), "array": isinstance(value, list),
               "integer": isinstance(value, int) and not isinstance(value, bool),
               "boolean": isinstance(value, bool)}
    if types and not any(matches.get(kind, False) for kind in types):
        raise OperationError("operation_schema_invalid", f"Revisa el tipo de {path}.")
    if "enum" in schema and value not in schema["enum"]:
        raise OperationError("operation_schema_invalid", f"Elige una opción declarada para {path}.")
    if isinstance(value, str) and (len(value) < schema.get("minLength", 0) or len(value) > schema.get("maxLength", 262144)
                                 or ("pattern" in schema and re.fullmatch(schema["pattern"], value) is None)):
        raise OperationError("operation_schema_invalid", f"Revisa {path}.")
    if isinstance(value, int) and not isinstance(value, bool) and not schema.get("minimum", value) <= value <= schema.get("maximum", value):
        raise OperationError("operation_schema_invalid", f"{path} está fuera del rango permitido.")
    if isinstance(value, dict):
        if len(value) < schema.get("minProperties", 0):
            raise OperationError("operation_schema_invalid", f"Declara los cambios de {path}.")
        fields = schema.get("properties", {})
        if set(schema.get("required", [])) - set(value) or (schema.get("additionalProperties") is False and set(value) - set(fields)):
            raise OperationError("operation_schema_invalid", f"Faltan parámetros o hay campos no admitidos en {path}.")
        for key, child in value.items():
            if key in fields:
                _validate(child, fields[key], f"{path}.{key}")
    if isinstance(value, list):
        if not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", 100):
            raise OperationError("operation_schema_invalid", f"Revisa la cantidad en {path}.")
        for child in value:
            _validate(child, schema.get("items", {}), path)


def validate_operation(op: Any) -> dict[str, Any]:
    if not isinstance(op, dict) or op.get("op") not in BY_NAME:
        raise OperationError("operacion_desconocida", "La operación no está en el registro.")
    _validate(op, BY_NAME[op["op"]]["schema"], op["op"])
    if op["op"] == "apply_to_positions":
        for child in op["ops"]:
            validate_operation(child)
            if BY_NAME[child["op"]]["scope"] not in {"design", "position"}:
                raise OperationError("batch_op_not_allowed", "El lote solo admite cambios del diseño y sus atributos.")
    return deepcopy(op)


def fingerprint(value: Any) -> str:
    # JS JSON.stringify / UTF-16 FNV-1a. Used only for concurrency, never as a seal.
    data = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-16-le", errors="surrogatepass")
    result = 0x811C9DC5
    for index in range(0, len(data), 2):
        result = ((result ^ int.from_bytes(data[index:index + 2], "little")) * 0x01000193) & 0xFFFFFFFF
    return f"{result:08x}"


def decimal(value: Any) -> Decimal:
    if isinstance(value, bool):
        raise OperationError("dimension_invalid", "La medida debe ser decimal.")
    try:
        result = Decimal(str(value))
    except (ValueError, InvalidOperation) as error:
        raise OperationError("dimension_invalid", "La medida debe ser decimal.") from error
    if not result.is_finite():
        raise OperationError("dimension_invalid", "La medida debe ser finita.")
    return result


def mm(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def walk(node: dict[str, Any]) -> list[dict[str, Any]]:
    return [node, *[found for child in node.get("children", []) for found in walk(child)]]


def as_product(value: dict[str, Any]) -> dict[str, Any]:
    product: dict[str, Any] = deepcopy(value if value.get("version") == "product-v2" else {"version": "product-v2", "assembly": {
        "modules": [{**module, "id": module.get("id") or module.get("ref") or f"m{index + 1}"}
                    for index, module in enumerate(value.get("modules", []))], "couplings": value.get("couplings", [])}})
    product.pop("design_context", None)
    modules = product.get("assembly", {}).get("modules", [])
    if not 1 <= len(modules) <= MAX_MODULES or any(not isinstance(module.get("tree"), dict) for module in modules):
        raise OperationError("product_invalid", "Envía el diseño completo con sus paños.")
    ids = [module["id"] for module in modules]
    if len(ids) != len(set(ids)):
        raise OperationError("product_invalid", "Los marcos deben tener identidad única.")
    for module in modules:
        nodes = walk(module["tree"])
        if len(nodes) > 255 or len({node.get("id") for node in nodes}) != len(nodes):
            raise OperationError("product_invalid", "Revisa la identidad y cantidad de paños.")
    return product


def _module(product: dict[str, Any], address: str | None) -> dict[str, Any]:
    modules = cast(list[dict[str, Any]], product["assembly"]["modules"])
    direct = next((module for module in modules if module["id"] == address), None)
    if direct is not None:
        return direct
    if address and address.startswith("m") and address[1:].isdigit() and 0 < int(address[1:]) <= len(modules):
        return modules[int(address[1:]) - 1]
    if address is None and len(modules) == 1:
        return modules[0]
    raise OperationError("modulo_invalido", "El marco indicado ya no existe.")


def _target(product: dict[str, Any], op: dict[str, Any], field: str = "bay") -> tuple[dict[str, Any], dict[str, Any]]:
    module = _module(product, op.get("module"))
    address = op[field]
    nodes = walk(module["tree"])
    found = next((node for node in nodes if node["id"] == address), None)
    kind = "BAY" if field == "bay" else None
    choices = [node for node in nodes if node["type"] == kind] if kind else [node for node in nodes if node["type"] in {"SPLIT_V", "SPLIT_H"}]
    prefix = "b" if kind else "d"
    if found is None and address.startswith(prefix) and address[1:].isdigit() and 0 < int(address[1:]) <= len(choices):
        found = choices[int(address[1:]) - 1]
    if found is None or found not in choices:
        raise OperationError("bay_unavailable" if kind else "division_unavailable", "El paño o división ya no existe.")
    return module, found


def _replace(tree: dict[str, Any], target: str, replacement: dict[str, Any]) -> dict[str, Any]:
    if tree["id"] == target:
        return replacement
    if tree.get("children"):
        tree["children"] = [_replace(child, target, replacement) for child in tree["children"]]
    return tree


def _parent(tree: dict[str, Any], target: str) -> dict[str, Any] | None:
    return next((node for node in walk(tree) if any(child["id"] == target for child in node.get("children", []))), None)


def _top(tree: dict[str, Any]) -> dict[str, Any]:
    return tree["children"][0] if tree["type"] == "ROOT" else tree


def _layout(module: dict[str, Any], params: SystemParams, finish: str) -> dict[str, tuple[Decimal, Decimal]]:
    root = deepcopy(module["tree"])
    root.update(width_mm=module["width_mm"], height_mm=module["height_mm"])
    return compute_geometry(ParametricNode.model_validate_json(json.dumps(root)), params, finish=finish,
                            diagnostic=True, diagnose_catalog_limits=True).node_dimensions


def _opening(node: dict[str, Any], value: Any, params: SystemParams, op: dict[str, Any]) -> None:
    node.update(opening_type=value if isinstance(value, str) else None, opening=value if isinstance(value, dict) else None,
                opening_use=op.get("opening_use", "WINDOW") if isinstance(value, dict) else None,
                hinged_layout=op.get("hinged_layout"), sliding_layout=op.get("sliding_layout"))
    parsed = ParametricNode.model_validate_json(json.dumps(node))
    physical = node_opening(parsed)
    if (isinstance(value, str) and params.opening_capabilities
            and physical.movement is not OpeningMovement.SLIDE
            and physical.leaf_role is LeafRole.SINGLE):
        # This is new authoring, not a migration of a saved tree. Resolve
        # aliases through the declared physical capability so its permitted
        # hardware classes also govern the saved design, exactly like the UI.
        use = node_use(parsed)
        node.update(opening_type=None, opening=physical.model_dump(mode="json"), opening_use=use.value)
        parsed = ParametricNode.model_validate_json(json.dumps(node))
    if isinstance(value, str) and (not params.uses_legacy_rules or node_opening(parsed).movement is OpeningMovement.SLIDE):
        # A new operation cannot borrow an old transport alias to bypass the
        # selected series' physical authority. Reading frozen legacy trees is
        # unchanged; this check applies only to a newly requested edit.
        try:
            resolve_capability(parsed.model_copy(update={"opening_type": None,
                "opening": node_opening(parsed), "opening_use": node_use(parsed)}), params)
        except OpeningCapabilityError as error:
            raise OperationError("opening_incompatible", str(error)) from error
    try:
        normalize_opening_tree(parsed, params)
        validate_family(parsed, params)
    except (OpeningCapabilityError, CatalogRuleError) as error:
        raise OperationError("opening_incompatible", str(error)) from error
    if parsed.sliding_layout is not None:
        validate_sliding_layout(parsed.sliding_layout, params)


def editable_legacy_openings(params: SystemParams) -> list[str]:
    """Choices for new edits; historical reading keeps its frozen authority."""
    candidates = FAMILY_OPENINGS[params.system_family] if params.system_family else set(BayOpeningType)
    accepted = []
    for kind in candidates:
        if kind.value.startswith("SLIDING"):
            node = ParametricNode.model_validate_json(json.dumps({"id": "choice", "type": "BAY", "opening_type": kind.value}))
            try:
                resolve_capability(node.model_copy(update={"opening_type": None,
                    "opening": node_opening(node), "opening_use": node_use(node)}), params)
            except OpeningCapabilityError:
                continue
        accepted.append(kind.value)
    return sorted(accepted)


def _new_id(product: dict[str, Any], prefix: str) -> str:
    ids = {node["id"] for module in product["assembly"]["modules"] for node in walk(module["tree"])}
    ids.update(module["id"] for module in product["assembly"]["modules"])
    ids.update(coupling["id"] for coupling in product["assembly"]["couplings"])
    index = 1
    while f"ops-{prefix}-{index}" in ids:
        index += 1
    return f"ops-{prefix}-{index}"


def _dimensions(product: dict[str, Any]) -> None:
    for module in product["assembly"]["modules"]:
        if not Decimal("150") <= decimal(module["width_mm"]) <= Decimal("6000") or not Decimal("200") <= decimal(module["height_mm"]) <= Decimal("4000"):
            raise OperationError("dimension_invalid", "Revisa el ancho y alto del marco.")


def _resize_module(module: dict[str, Any], *, width: Decimal | None = None, height: Decimal | None = None) -> None:
    new_width = width if width is not None else decimal(module["width_mm"])
    new_height = height if height is not None else decimal(module["height_mm"])
    contour = module.get("contour")
    if contour:
        vertices = contour["vertices"]
        xs, ys = [decimal(v["x_mm"]) for v in vertices], [decimal(v["y_mm"]) for v in vertices]
        old_width, old_height = max(xs) - min(xs), max(ys) - min(ys)
        if old_width <= 0 or old_height <= 0:
            raise OperationError("contour_invalid", "El contorno necesita ancho y alto positivos.")
        sx, sy = new_width / old_width, new_height / old_height
        scaled = [{"x_mm": mm((x - min(xs)) * sx), "y_mm": mm((y - min(ys)) * sy)} for x, y in zip(xs, ys, strict=True)]
        bulges: list[str | None] = []
        for index, rise in enumerate(contour["bulges"]):
            if rise is None:
                bulges.append(None)
                continue
            following = (index + 1) % len(vertices)
            dx, dy = xs[following] - xs[index], ys[following] - ys[index]
            length = (dx * dx + dy * dy).sqrt()
            if length == 0:
                raise OperationError("contour_invalid", "El contorno repite un vértice.")
            # Perpendicular sagitta after the affine resize. A stretched
            # normal also has a tangential component on diagonal chords;
            # only its projection onto the new chord normal is a rise.
            factor = sx * sy * length / ((dx * sx) ** 2 + (dy * sy) ** 2).sqrt()
            bulges.append(mm(decimal(rise) * factor))
        module["contour"] = {"vertices": scaled, "bulges": bulges}
    module.update(width_mm=mm(new_width), height_mm=mm(new_height))


def _apply(product: dict[str, Any], op: dict[str, Any], params: SystemParams, catalog: dict[str, Any], finish: str) -> None:
    name = op["op"]
    modules = cast(list[dict[str, Any]], product["assembly"]["modules"])
    couplings = product["assembly"]["couplings"]
    if name == "set_bay_spec":
        _, node = _target(product, op)
        node.update(deepcopy(op["patch"]))
        ParametricNode.model_validate_json(json.dumps(node))
    elif name == "set_module_tree":
        module = _module(product, op["module"])
        ParametricNode.model_validate_json(json.dumps(op["tree"]))
        module["tree"] = deepcopy(op["tree"])
    elif name == "clear_glass_thickness":
        module = _module(product, op["module"])
        for node in walk(module["tree"]):
            if node["type"] == "BAY":
                if node.get("glass_product"):
                    raise OperationError("glass_composition_required", "La composición declara su espesor; cambia la receta para modificarlo.")
                node["glass_thickness_mm"] = None
    elif name == "set_extras":
        module = _module(product, op["module"])
        module["tree"]["extras"] = deepcopy(op["extras"])
        if "context" in op:
            module["tree"]["extra_context"] = deepcopy(op["context"])
        ParametricNode.model_validate_json(json.dumps(module["tree"]))
    elif name == "set_frameless":
        module = _module(product, op["module"])
        if op["spec"] is None:
            module.pop("frameless", None)
        else:
            FramelessSpec.model_validate_json(json.dumps(op["spec"]))
            module["frameless"] = deepcopy(op["spec"])
    elif name in {"set_contour_vertex", "set_contour_bulge"}:
        module = _module(product, op["module"])
        contour = module.get("contour")
        if contour is None or op["index"] >= len(contour["vertices"]):
            raise OperationError("contour_invalid", "El vértice o arco ya no existe.")
        if name == "set_contour_vertex":
            x = decimal(op["x_mm"])
            contour["vertices"][op["index"]] = {"x_mm": mm(decimal(module["width_mm"]) - x if op.get("from") == "END" else x), "y_mm": op["y_mm"]}
        else:
            contour["bulges"][op["index"]] = op["rise_mm"]
    elif name == "resize_seam":
        left, right = _module(product, op["left"]), _module(product, op["right"])
        if left is right or not any(c.get("modules") in ([left["id"], right["id"]], [right["id"], left["id"]]) and c.get("kind", "INLINE") == "INLINE" for c in couplings):
            raise OperationError("union_invalida", "Selecciona dos marcos con una unión lateral.")
        delta = decimal(op["delta_mm"])
        _resize_module(left, width=decimal(left["width_mm"]) + delta)
        _resize_module(right, width=decimal(right["width_mm"]) - delta)
    elif name == "swap_modules":
        _materialize(product)
        first, other = _module(product, op["module"]), _module(product, op["other"])
        a, b = modules.index(first), modules.index(other)
        modules[a], modules[b] = modules[b], modules[a]
        for coupling in couplings:
            coupling["modules"] = [other["id"] if identity == first["id"] else first["id"] if identity == other["id"] else identity for identity in coupling["modules"]]
    elif name == "set_coupler_sku":
        coupling = next((item for item in couplings if item["id"] == op["coupling"]), None)
        if coupling is None or op["sku"] is not None and op["sku"] not in catalog.get("coupler_skus", set()):
            raise OperationError("union_invalida", "Elige un acople disponible para esa unión.")
        coupling["coupler_profile_sku"] = op["sku"]
    elif name in {"split_bay", "move_divider"}:
        module, node = _target(product, op, "bay" if name == "split_bay" else "divider")
        if module.get("contour") or module.get("frameless"):
            raise OperationError("geometry_unsupported", "La división necesita un marco rectangular.")
        axis = op.get("axis") or ("V" if node["type"] == "SPLIT_V" else "H")
        size = _layout(module, params, finish)[node["id"]][0 if axis == "V" else 1]
        offset = decimal(op.get("offset_mm", "0"))
        reference = op.get("from", "START")
        offset = size - offset if reference == "END" else size / 2 + offset if reference == "CENTER" else offset
        if not Decimal("0") < offset < size:
            raise OperationError("division_invalid", "La división debe quedar dentro del paño.")
        if name == "move_divider":
            node["split_offset_mm"] = mm(offset)
        else:
            if node.get("opening_use") == "DOOR" or str(node.get("opening_type", "")).startswith("DOOR"):
                raise OperationError("door_requires_top_bay", "La puerta necesita un paño completo.")
            role = ProfileRole.MULLION_V if axis == "V" else ProfileRole.MULLION_H
            article = params.effective_profile_articles.get(role)
            if article is None:
                raise OperationError("mullion_missing", "La serie no declara perfil para esa división.")
            second = deepcopy(node)
            second["id"] = _new_id(product, "bay")
            for child in (node, second):
                child.pop("width_mm", None)
                child.pop("height_mm", None)
                child.pop("sliding_layout", None)
            if axis == "V":
                _flip(second, require_mobile=False)
            replacement = {"id": _new_id(product, "divider"), "type": f"SPLIT_{axis}",
                           "split_offset_mm": mm(offset), "mullion_profile_sku": article.sku,
                           "children": [node, second]}
            module["tree"] = _replace(module["tree"], node["id"], replacement)
    elif name == "remove_divider":
        module, node = _target(product, op, "divider")
        children = node.get("children", [])
        if len(children) != 2 or any(child["type"] != "BAY" for child in children):
            raise OperationError("division_nested", "Retira primero las divisiones interiores.")
        keep = next((child for child in children if child["id"] == op.get("keep_bay")), children[0])
        module["tree"] = _replace(module["tree"], node["id"], keep)
    elif name == "set_bay_size":
        module, node = _target(product, op)
        parent = _parent(module["tree"], node["id"])
        if parent is None or parent["type"] != f"SPLIT_{op['axis']}":
            raise OperationError("division_unavailable", "Ese paño no tiene una división compatible con el eje.")
        role = ProfileRole.MULLION_V if op["axis"] == "V" else ProfileRole.MULLION_H
        half = params.effective_profile_articles[role].face_width_mm / 2
        size = decimal(op["size_mm"])
        if parent["children"][0]["id"] == node["id"]:
            frame = params.effective_profile_articles[ProfileRole.FRAME].face_width_mm if parent is _top(module["tree"]) else Decimal("0")
            parent["split_offset_mm"] = mm(size + frame + half)
        else:
            total = _layout(module, params, finish)[parent["id"]][0 if op["axis"] == "V" else 1]
            frame = params.effective_profile_articles[ProfileRole.FRAME].face_width_mm if parent is _top(module["tree"]) else Decimal("0")
            parent["split_offset_mm"] = mm(total - size - frame - half)
    elif name == "equalize_bays":
        module = _module(product, op["module"])
        axis = op["axis"]
        bays = [node for node in walk(module["tree"]) if node["type"] == "BAY"]
        count = op.get("count", len(bays))
        if not 1 <= count <= 12:
            raise OperationError("bay_count_invalid", "Elige entre uno y doce paños.")
        size = decimal(module["width_mm" if axis == "V" else "height_mm"])
        article = params.effective_profile_articles.get(ProfileRole.MULLION_V if axis == "V" else ProfileRole.MULLION_H)
        if count > 1 and article is None:
            raise OperationError("mullion_missing", "La serie no declara el perfil de división.")
        half = article.face_width_mm / 2 if article else Decimal("0")
        leaves = deepcopy(bays[:count])
        while len(leaves) < count:
            leaf = deepcopy(bays[0])
            leaf["id"] = _new_id(product, "bay")
            # Reserve each identity before minting the next.
            product["assembly"]["modules"].append({"id": leaf["id"], "tree": leaf})
            leaves.append(leaf)
        del modules[len(modules) - max(0, count - len(bays)):]
        for leaf in leaves:
            leaf.pop("width_mm", None)
            leaf.pop("height_mm", None)
        current = leaves[-1]
        # Global equally spaced centerlines, translated to each child's local
        # origin (right/bottom of the previous half-face), with exact Decimal.
        for index in range(count - 2, -1, -1):
            global_axis = (size * Decimal(index + 1) / count).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            previous_axis = (size * Decimal(index) / count).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            local = global_axis if index == 0 else global_axis - previous_axis - half
            current = {"id": f"{_new_id(product, 'divider')}-{index}", "type": f"SPLIT_{axis}",
                       "split_offset_mm": mm(local), "mullion_profile_sku": article.sku if article else None,
                       "children": [leaves[index], current]}
        module["tree"] = _replace(module["tree"], _top(module["tree"])["id"], current)
    elif name in {"set_opening", "set_glass", "set_panel", "set_glass_thickness"}:
        module = _module(product, op["module"])
        targets = [_target(product, op)[1]] if "bay" in op else [node for node in walk(module["tree"]) if node["type"] == "BAY"]
        for node in targets:
            if name == "set_opening":
                _opening(node, op["opening"], params, op)
            elif name == "set_glass":
                recipes = catalog.get("glass_specs", {})
                sku = op.get("sku")
                if sku is None:
                    sku = next((key for key, recipe in recipes.items() if recipe == op.get("composition")), None)
                if sku not in catalog.get("glass_skus", set()):
                    raise OperationError("vidrio_invalido", "La receta o SKU no está disponible en el catálogo.")
                node.update(glass_article_sku=sku, glass_spec=recipes.get(sku), panel_article_sku=None)
                product_value = catalog.get("glass_products", {}).get(sku)
                if product_value is not None:
                    from .glass_composition import GlassProduct, total_glass_thickness
                    parsed = GlassProduct.model_validate_json(json.dumps(product_value))
                    thickness = total_glass_thickness(parsed.composition)
                    node.update(glass_product=product_value, glass_thickness_mm=mm(thickness) if thickness is not None else None)
                else:
                    node["glass_product"] = None
            elif name == "set_panel":
                if op["sku"] is not None and op["sku"] not in catalog.get("panel_skus", set()):
                    raise OperationError("panel_invalido", "El panel no está en el catálogo.")
                node["panel_article_sku"] = op["sku"]
            else:
                if decimal(op["mm"]) not in catalog.get("thicknesses", set()):
                    raise OperationError("espesor_invalido", "El espesor no está declarado por la serie.")
                node["glass_thickness_mm"] = mm(decimal(op["mm"]))
    elif name == "flip_handing":
        _, node = _target(product, op)
        _flip(node)
    elif name == "set_handle_height":
        module, node = _target(product, op)
        reference = op["reference"]
        height = decimal(op["height_mm"])
        if reference == "FLOOR":
            if "sill_height_mm" not in op:
                raise OperationError("installation_height_required", "¿A qué altura del piso está el antepecho de la ventana?")
            node["sill_height_mm"] = op["sill_height_mm"]
        root = deepcopy(module["tree"])
        root.update(width_mm=module["width_mm"], height_mm=module["height_mm"])
        computation = compute_geometry(ParametricNode.model_validate_json(json.dumps(root)), params,
                                       finish=finish, diagnostic=True, diagnose_catalog_limits=True)
        technical_leaves = [item for item in computation.leaves if item.bay_id == node["id"]]
        if len(technical_leaves) != 1:
            raise OperationError("handle_leaf_required", "Elige una hoja móvil con manilla individual.")
        leaf_height = technical_leaves[0].finished_height_mm
        if reference == "FLOOR":
            trace = computation.manufacturing_trace
            physical_leaf = next((item for item in trace.leaves if item.bay_id == node["id"]), None) if trace else None
            if physical_leaf is None or physical_leaf.direct_rect is None:
                raise OperationError("handle_datum_missing", "El motor no declara el origen de esa hoja respecto del marco.")
            bottom_above_frame = decimal(module["height_mm"]) - physical_leaf.direct_rect.y_mm - physical_leaf.direct_rect.height_mm
            height -= decimal(op["sill_height_mm"]) + bottom_above_frame
        if height <= 0 or height >= leaf_height:
            raise OperationError("handle_height_invalid", "La manilla queda fuera de la hoja.")
        if reference == "LEAF_TOP":
            height = leaf_height - height
        node["handle_height_mm"] = mm(height)
    elif name == "set_sliding_layout":
        _, node = _target(product, op)
        tracks = op["tracks"]
        kinds = op["panels"]
        declared = op.get("panel_tracks")
        if declared is not None and len(declared) != len(kinds):
            raise OperationError("sliding_layout_invalid", "Declara un carril por panel.")
        panels = [{"slot": f"S{index + 1}", "kind": "MOVING" if kind == "X" else "FIXED",
                   "track": declared[index] if declared is not None else (index % tracks if kind == "X" else None)}
                  for index, kind in enumerate(kinds)]
        _opening(node, {"movement": "SLIDE", "hinge_side": "NONE", "direction": "INWARD",
                        "leaf_role": "SINGLE", "fixed_in_sash": False}, params,
                 {"sliding_layout": {"tracks": tracks, "panels": panels}})
        if "travel_mm" in op:
            raise OperationError("travel_not_supported", "El contrato actual no declara recorrido editable de corredera.")
    elif name == "set_travel":
        raise OperationError("travel_not_supported", "El contrato actual no declara recorrido editable de corredera.")
    elif name in {"set_module_width", "resize"}:
        module = _module(product, op["module"])
        if name == "set_module_width":
            _resize_module(module, width=decimal(op["width_mm"]))
        else:
            _resize_module(module, width=decimal(module["width_mm"]) + decimal(op.get("delta_width_mm", "0")),
                           height=decimal(module["height_mm"]) + decimal(op.get("delta_height_mm", "0")))
    elif name == "set_height":
        for module in modules:
            _resize_module(module, height=decimal(op["height_mm"]))
    elif name in {"set_total_width", "equalize_widths"}:
        total = sum((decimal(module["width_mm"]) for module in modules), Decimal("0"))
        target = decimal(op["width_mm"]) if name == "set_total_width" else total
        assigned = Decimal("0")
        for index, module in enumerate(modules):
            value = target - assigned if index == len(modules) - 1 else (target / len(modules) if name == "equalize_widths" else target * decimal(module["width_mm"]) / total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            _resize_module(module, width=value)
            assigned += value
    elif name in {"set_coupling_angle", "set_coupling_kind", "remove_coupling", "equalize_angles"}:
        if name == "equalize_angles":
            if couplings:
                for coupling in couplings:
                    coupling["angle_deg"] = couplings[0]["angle_deg"]
        else:
            coupling = next((item for index, item in enumerate(couplings) if item["id"] == op["coupling"] or f"c{index + 1}" == op["coupling"]), None)
            if coupling is None:
                raise OperationError("union_invalida", "La unión ya no existe.")
            if name == "remove_coupling":
                couplings.remove(coupling)
            elif name == "set_coupling_angle":
                if not Decimal("-90") < decimal(op["angle_deg"]) < Decimal("90"):
                    raise OperationError("angulo_invalido", "El ángulo debe quedar dentro de menos y más noventa grados.")
                coupling["angle_deg"] = op["angle_deg"]
            else:
                lateral = all(edge in {"left", "right"} for edge in coupling.get("edges", ["right", "left"]))
                if op["kind"] not in ({"INLINE"} if lateral else {"STACKED", "TEE", "CORNER"}):
                    raise OperationError("tipo_invalido", "La unión no corresponde a sus bordes.")
                coupling["kind"] = op["kind"]
    else:
        # Graph editing uses the existing domain graph contract; explicit
        # endpoint/edge validation is performed again by evaluate_product.
        _structure(product, op)
    _dimensions(product)


def _flip(node: dict[str, Any], *, require_mobile: bool = True) -> None:
    mirror = {"TURN_LEFT": "TURN_RIGHT", "TURN_RIGHT": "TURN_LEFT", "TILT_TURN_LEFT": "TILT_TURN_RIGHT", "TILT_TURN_RIGHT": "TILT_TURN_LEFT"}
    physical = node.get("opening")
    if isinstance(physical, dict) and physical.get("hinge_side") in {"LEFT", "RIGHT"}:
        if node.get("hinged_layout"):
            for leaf in node["hinged_layout"]["leaves"]:
                opening = leaf["opening"]
                opening["leaf_role"] = "PASSIVE" if opening["leaf_role"] == "ACTIVE" else "ACTIVE"
            node["hardware_selection"] = None
        physical["hinge_side"] = "RIGHT" if physical["hinge_side"] == "LEFT" else "LEFT"
    elif node.get("opening_type") in mirror:
        node["opening_type"] = mirror[node["opening_type"]]
    elif node.get("door_handedness") in {"LEFT", "RIGHT"}:
        node["door_handedness"] = "RIGHT" if node["door_handedness"] == "LEFT" else "LEFT"
    elif require_mobile:
        raise OperationError("handing_unavailable", "El paño no declara bisagras laterales que se puedan invertir.")


def _materialize(product: dict[str, Any]) -> None:
    """Resolve historical chain endpoints before changing the graph order."""
    modules = product["assembly"]["modules"]
    couplings = product["assembly"]["couplings"]
    for index, coupling in enumerate(couplings):
        if not coupling.get("modules") and index + 1 < len(modules):
            coupling.update(modules=[modules[index]["id"], modules[index + 1]["id"]], edges=["right", "left"], kind=coupling.get("kind", "INLINE"))


def _structure(product: dict[str, Any], op: dict[str, Any]) -> None:
    name = op["op"]
    assembly = product["assembly"]
    modules, couplings = assembly["modules"], assembly["couplings"]
    _materialize(product)
    if name == "remove_unit":
        target = _module(product, op["module"])
        if len(modules) == 1:
            raise OperationError("modulo_invalido", "Conserva al menos un marco.")
        incident = [c for c in couplings if target["id"] in c.get("modules", [])]
        if len(incident) > 2 or any(c.get("kind", "INLINE") != "INLINE" for c in incident):
            raise OperationError("modulo_con_uniones", "Desconecta las uniones especiales antes de quitar el marco.")
        if len(incident) == 2:
            endpoints = [(mid, edge) for c in incident for mid, edge in zip(c["modules"], c["edges"]) if mid != target["id"]]
            incident[0].update(modules=[v[0] for v in endpoints], edges=[v[1] for v in endpoints])
            couplings.remove(incident[1])
        elif incident:
            couplings.remove(incident[0])
        modules.remove(target)
        return
    if name == "set_module_count":
        count = op["count"]
        while len(modules) > count:
            _structure(product, {"op": "remove_unit", "module": modules[-1]["id"]})
        while len(modules) < count:
            _structure(product, {"op": "add_unit", "side": "right"})
        return
    if len(modules) >= MAX_MODULES:
        raise OperationError("limite_unidades", "El conjunto admite hasta doce marcos.")
    if name == "insert_module":
        seam = next((c for c in couplings if c["id"] == op["coupling"]), None)
        if seam is None or seam.get("kind", "INLINE") != "INLINE":
            raise OperationError("union_invalida", "Selecciona una unión recta.")
        left, right = seam["modules"]
        clone = deepcopy(_module(product, left))
        clone["id"] = _new_id(product, "module")
        modules.insert(next(index for index, module in enumerate(modules) if module["id"] == right), clone)
        seam["modules"] = [left, clone["id"]]
        new = {**deepcopy(seam), "id": _new_id(product, "coupling"), "modules": [clone["id"], right]}
        couplings.insert(couplings.index(seam) + 1, new)
        return
    if name not in {"add_unit", "duplicate_module", "add_stacked_unit"}:
        raise OperationError("operacion_desconocida", "La operación no modifica un diseño.")
    side = op.get("side", "right")
    target = _module(product, op.get("module")) if "module" in op else modules[-1] if side == "right" else modules[0]
    claimed = {edge for c in couplings for mid, edge in zip(c.get("modules", []), c.get("edges", [])) if mid == target["id"]}
    if name == "add_stacked_unit":
        side = "top"
    if name == "duplicate_module" and side in claimed:
        side = "left"
    if side in claimed or target.get("contour") or target.get("frameless"):
        raise OperationError("sin_borde_libre", "El marco necesita un borde libre y recto.")
    clone = deepcopy(target)
    clone["id"] = _new_id(product, "module")
    if side == "top":
        top = deepcopy(next(node for node in walk(clone["tree"]) if node["type"] == "BAY"))
        top.update(opening_type="FIXED", opening=None, sliding_layout=None, hinged_layout=None)
        clone["tree"] = top
    modules.insert(modules.index(target) + (0 if side == "left" else 1), clone)
    coupling = {"id": _new_id(product, "coupling"), "modules": [target["id"], clone["id"]],
                "edges": [side, {"right": "left", "left": "right", "top": "bottom"}[side]],
                "kind": "STACKED" if side == "top" else "INLINE", "angle_deg": "0", "coupler_profile_sku": couplings[-1].get("coupler_profile_sku") if couplings else None}
    couplings.append(coupling)


def apply_operations(product: dict[str, Any], ops: list[dict[str, Any]], *, params: SystemParams, catalog: dict[str, Any],
                     finish: str) -> dict[str, Any]:
    """No partial acceptance: every operation succeeds or the whole proposal fails."""
    if not isinstance(ops, list) or not 1 <= len(ops) <= MAX_OPERATIONS:
        raise OperationError("limite_operaciones", "Propón entre una y cincuenta operaciones.")
    current = as_product(product)
    normalized = []
    origin = {"module": [module["id"] for module in current["assembly"]["modules"]],
              "coupling": [coupling["id"] for coupling in current["assembly"]["couplings"]]}
    added: dict[str, list[str]] = {"module": [], "coupling": []}
    for raw in ops:
        op = validate_operation(raw)
        for field, prefix, collection in (("module", "m", "modules"), ("coupling", "c", "couplings")):
            address = op.get(field)
            if isinstance(address, str):
                live = {item["id"] for item in current["assembly"][collection]}
                if address in live:
                    continue
                if address.startswith(f"added_{prefix}") and address[len(prefix) + 6:].isdigit():
                    index = int(address[len(prefix) + 6:]) - 1
                    if 0 <= index < len(added[field]):
                        op[field] = added[field][index]
                elif address.startswith(prefix) and address[1:].isdigit():
                    index = int(address[1:]) - 1
                    if 0 <= index < len(origin[field]):
                        op[field] = origin[field][index]
        if BY_NAME[op["op"]]["scope"] != "design":
            raise OperationError("operation_scope_invalid", "Usa la vista previa de posiciones para ese cambio.")
        before = fingerprint(current)
        _apply(current, op, params, catalog, finish)
        for field, collection in (("module", "modules"), ("coupling", "couplings")):
            added[field].extend(item["id"] for item in current["assembly"][collection]
                                if item["id"] not in origin[field] and item["id"] not in added[field])
        normalized.append({**op, "base_sig": before, "result": deepcopy(current), "description": BY_NAME[op["op"]]["description"]})
    return {"product": current, "ops": normalized, "registry_version": VERSION}
