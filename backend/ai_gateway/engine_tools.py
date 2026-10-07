"""Allowlisted read-only function calls. No tool here writes domain state."""

from copy import deepcopy
from decimal import Decimal
import json
from uuid import UUID

from authentication.errors import ContractAPIException
from dekopen_engine.design_operations import OperationError, as_product
from dekopen_engine.catalog_rules import CatalogRuleError
from dekopen_engine.weight import MissingFabricationAuthority
from projects import ops_registry, service
from projects.finishes import position_finish_code
from engine_api.repository import SystemParamsRepository, SystemNotFound, UnsupportedCatalogContract

TOOLS = [
    {"name": name, "description": description, "parameters": {"type": "object", "additionalProperties": False,
     "properties": {**({"system_id": {"type": "string"}, "kind": {"type": "string", "enum": ["all", "opening", "glass", "finish", "system"]}} if name == "list_catalog_options" else {}),
                    **({"ops": {"type": "array", "items": {"type": "object"}, "maxItems": 50}} if name in {"simulate_ops", "explain_price_delta"} else {}),
                    **({"position_id": {"type": "string"}} if name not in {"price_project", "list_catalog_options"} else {}),
                    **({"project_id": {"type": "string"}} if name in {"price_project", "get_blockers"} else {})}}}
    for name, description in [
        ("calculate_position", "Calcula con el motor medidas, pesos de hojas y validez del diseño actual."),
        ("validate_position", "Devuelve la validez y todas las causas del motor."),
        ("price_position", "Devuelve exclusivamente venta neta indicativa calculada; nunca costos de compra."),
        ("price_project", "Lee precios aplicados vigentes del proyecto; si faltan, explica la autoridad ausente."),
        ("explain_price_delta", "Simula operaciones y compara venta antes/después con la misma configuración."),
        ("list_catalog_options", "Lista opciones reales de serie, apertura, receta y caras de acabado."),
        ("get_blockers", "Lista exacta de impedimentos del motor o de preparación documental."),
        ("simulate_ops", "Aplica operaciones en una copia atómica; devuelve diseño, validez, diff y delta de venta."),
    ]
]
TOOLS.append({"name": "preview_project_operations", "description": "Simula creación, copia, eliminación, cantidad, ubicación y filtros en el proyecto; no escribe.",
              "parameters": {"type": "object", "additionalProperties": False, "properties": {
                  "project_id": {"type": "string"}, "ops": {"type": "array", "items": {"type": "object"}, "maxItems": 50}}}})
BY_NAME = {item["name"]: item for item in TOOLS}


class EngineTools:
    def __init__(self, *, org_id, user_id, refs, product, observed_refs, goal):
        self.org_id, self.user_id, self.refs = org_id, user_id, refs
        self.product, self.observed_refs, self.goal = product, observed_refs, goal
        self.cache = {}
        self.calls = []

    def _reference(self, arguments, name):
        value = arguments.get(name) or self.refs.get(name)
        if value is None or str(value) not in self.observed_refs:
            raise OperationError("unobserved_ref", "Consulta primero la entidad del proyecto.")
        return UUID(str(value))

    def position(self, arguments):
        identity = self._reference(arguments, "position_id")
        position = service.position_row(self.org_id, identity)
        product = as_product(self.product) if self.product and str(identity) == str(self.refs.get("position_id")) else ops_registry.product_from_position(position)
        if self.product and isinstance(self.product.get("design_context"), dict) and str(identity) == str(self.refs.get("position_id")):
            context = self.product["design_context"]
            if set(context) == {"system_id", "color"} and all(isinstance(value, str) for value in context.values()):
                SystemParamsRepository().load_visible(UUID(context["system_id"]), self.org_id)
                position = {**position, "system_id": UUID(context["system_id"]), "color_interior": context["color"], "color_exterior": context["color"], "bom_snapshot": None}
        return position, product

    def catalog(self, arguments):
        system_id = arguments.get("system_id")
        if system_id is None:
            position, _ = self.position(arguments)
            system_id = position["system_id"]
        elif str(system_id) not in self.observed_refs:
            raise OperationError("unobserved_ref", "Consulta primero la serie del catálogo.")
        catalog = ops_registry.catalog_for(self.org_id, system_id)
        params = catalog["params"]
        return {"system_id": str(system_id), "system_code": params.system_code,
                "openings": catalog["openings"], "opening_choices": catalog["opening_choices"],
                "glass": [{"sku": sku, "composition": catalog["glass_specs"].get(sku),
                           "product": catalog["glass_products"].get(sku)} for sku in sorted(catalog["glass_skus"])],
                "finishes": list(params.finishes),
                "clarify_options": [{"label": f"{catalog['glass_specs'].get(sku) or sku} · {sku}", "value": sku}
                                    for sku in sorted(catalog["glass_skus"])],
                "finish_authority": params.finish_authority.model_dump(mode="json") if params.finish_authority else None}

    def call(self, name, arguments):
        if name not in BY_NAME or not isinstance(arguments, dict):
            raise OperationError("tool_unknown", "La herramienta no existe.")
        allowed = set(BY_NAME[name]["parameters"]["properties"])
        if set(arguments) - allowed:
            raise OperationError("tool_arguments_invalid", "Revisa los parámetros de la herramienta.")
        key = json.dumps({"name": name, "arguments": arguments}, sort_keys=True, default=str)
        if key in self.cache:
            return deepcopy(self.cache[key]), False
        try:
            output = self._execute(name, arguments)
        except (OperationError, ContractAPIException, CatalogRuleError, MissingFabricationAuthority, SystemNotFound, UnsupportedCatalogContract, ValueError) as error:
            output = {"error": getattr(error, "code", None) or getattr(error, "contract_code", None) or "technical_authority_required",
                      "detail": getattr(error, "public_detail", None) or str(error)}
        self.cache[key] = deepcopy(output)
        self.calls.append({"name": name, "arguments": arguments, "status": "error" if "error" in output else "ok"})
        return output, True

    def _execute(self, name, arguments):
        if name == "preview_project_operations":
            from projects.project_ops import preview_project_operations
            identity = self._reference(arguments, "project_id")
            return preview_project_operations(self.org_id, self.user_id, identity, arguments.get("ops"))
        if name == "list_catalog_options":
            if arguments.get("kind") == "system":
                return {"systems": [system.public_dict() for system in SystemParamsRepository().list_visible(self.org_id)]}
            return self.catalog(arguments)
        if name == "price_project":
            identity = self._reference(arguments, "project_id")
            project = service.project_public(self.org_id, service.project_row(self.org_id, identity), detail=True)
            if not project["pricing_current"]:
                return {"project_id": str(identity), "prices": None, "reason": "Sin dato: calcula y aplica los precios del proyecto antes de comparar posiciones."}
            return {"project_id": str(identity), "currency": project["currency"],
                    "totals": {key: project[key] for key in ("total_price_net", "total_price_tax", "total_price_gross")},
                    "prices": [{"position_id": str(position["id"]), "index": position["position_index"],
                                "location": position["location_tag"], "price_net": position["price_net"],
                                "quantity": position["quantity"]} for position in project["positions"]]}
        if name == "get_blockers" and arguments.get("project_id"):
            from documents.service import prepare_documentary_inputs
            from documents.repository import documentary_backend
            identity = self._reference(arguments, "project_id")
            with documentary_backend():
                preparation = prepare_documentary_inputs(org_id=self.org_id, project_id=identity)
            return {"project_id": str(identity), "blockers": preparation.get("missing", []), "preparation": preparation}
        position, product = self.position(arguments)
        system_id, color = position["system_id"], position_finish_code(position)
        if name in {"simulate_ops", "explain_price_delta"}:
            ops = arguments.get("ops")
            if not isinstance(ops, list):
                raise OperationError("ops_required", "Declara las operaciones a simular.")
            # Input numbers must be stated or already present in actual intent.
            # Derived effects become new authority only after the engine runs.
            from projects.design_assist import _declared_values
            allowed = _declared_values(self.goal)
            def collect(value):
                if isinstance(value, dict):
                    for field, child in value.items():
                        if field.endswith("_mm") or field in {"tracks", "track", "count", "angle_deg"}:
                            try:
                                allowed.add(Decimal(str(child)))
                            except ArithmeticError:
                                pass
                        elif isinstance(child, (dict, list)):
                            collect(child)
                elif isinstance(value, list):
                    for child in value:
                        collect(child)
            collect(product)
            def check(value):
                if isinstance(value, dict):
                    for field, child in value.items():
                        if (field.endswith("_mm") or field in {"mm", "count", "angle_deg"}) and child is not None:
                            if Decimal(str(child)) not in allowed:
                                raise OperationError("measure_ungrounded", "La medida no está declarada ni respaldada por el diseño.")
                        elif isinstance(child, (dict, list)):
                            check(child)
                elif isinstance(value, list):
                    for child in value:
                        check(child)
            check(ops)
            return ops_registry.simulate_ops(self.org_id, product, ops, system_id, color)
        if name == "price_position":
            return ops_registry.sale_price(self.org_id, product, system_id, color)
        engine = ops_registry.calculate_product(self.org_id, product, system_id, color)
        if name == "get_blockers":
            return {"position_id": str(position["id"]), "blockers": engine["issues"], "status": engine["status"]}
        return {"position_id": str(position["id"]), "status": engine["status"], "issues": engine["issues"],
                "modules": [{"module_id": module.get("module_id", module.get("id")),
                             "leaf_weights": (module.get("result") or {}).get("leaf_weights", []),
                             "opening_leaves": (module.get("result") or {}).get("opening_leaves", [])}
                            for module in engine.get("modules", [])], "engine": engine}
