"""HTTP adapter for the engine's shared operation registry and simulations."""

from copy import deepcopy
from datetime import datetime
from decimal import Decimal
import json
from uuid import UUID
from zoneinfo import ZoneInfo

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.views import APIView
from engine_api.serializers import ProductIssueSerializer

from authentication.errors import ContractAPIException, contract_error
from authentication.tenancy import MembershipRepository, resolve_tenant_context
from catalogs.glass import load_products
from dekopen_engine.commercial import PricingError, PricingMode, indicative_line_net
from dekopen_engine.catalog_rules import CatalogRuleError
from dekopen_engine.openings import OpeningCapabilityError
from dekopen_engine.weight import MissingFabricationAuthority
from dekopen_engine.design_operations import (
    BY_NAME, REGISTRY, VERSION, OperationError, apply_operations,
    as_product, validate_operation, fingerprint,
)
from dekopen_engine.extra_models import ExtraLine
from dekopen_engine.finishes import finish_selling_delta
from dekopen_engine.product import elevation_envelope
from dekopen_engine.snapshot import evaluation_response
from engine_api.adapter import InvalidEngineRequest, UnsupportedEngineContract, evaluate_assembly_from_api, parse_product_model
from engine_api.repository import SystemParamsRepository
from pricing.repository import PricingRepository, commercial_backend, json_text, rows
from pricing.serializers import StrictSerializer
from pricing.service import configured_unit_price, position_cost, pricing_public_detail
from pricing.views import DecimalJSONParser, ERRORS, scope, validate
from projects import design_assist, service
from projects.operation_serializers import DesignOperationSerializer
from projects.views import SCHEMA, READ_ROLES, response


class OperationSpecSerializer(serializers.Serializer):
    name = serializers.ChoiceField(choices=list(BY_NAME))
    description = serializers.CharField()
    scope = serializers.ChoiceField(choices=["design", "position", "project", "prepare"])
    preconditions = serializers.ListField(child=serializers.CharField())
    handler = serializers.CharField()
    schema = serializers.JSONField()
    examples = serializers.ListField(child=serializers.JSONField())


class OperationsRegistrySerializer(serializers.Serializer):
    version = serializers.CharField()
    operations = OperationSpecSerializer(many=True)


class SimulateOpsSerializer(StrictSerializer):
    system_id = serializers.UUIDField()
    color = serializers.CharField(max_length=50)
    product = serializers.JSONField()
    ops = DesignOperationSerializer(many=True, max_length=50)
    quantity = serializers.IntegerField(min_value=1, max_value=2147483647, default=1)


class SimulationSerializer(serializers.Serializer):
    registry_version = serializers.CharField()
    product = serializers.JSONField()
    system_id = serializers.UUIDField()
    color = serializers.CharField()
    ops = DesignOperationSerializer(many=True)
    valid = serializers.BooleanField()
    status = serializers.CharField()
    issues = ProductIssueSerializer(many=True)
    engine = serializers.JSONField()
    price = serializers.JSONField()
    before = serializers.JSONField()
    diff = serializers.ListField(child=serializers.JSONField())


def catalog_for(org_id, system_id):
    catalog = design_assist._catalog(UUID(str(system_id)), org_id)
    products = load_products(system_id, org_id)
    return {**catalog, "glass_specs": catalog["glass_recipes"],
            "coupler_skus": set(SystemParamsRepository().load_coupler_articles(UUID(str(system_id)), org_id)),
            "glass_products": {row["technical_sku"]: row["resolved_product"].model_dump(mode="json")
                               for row in products if row.get("resolved_product") is not None}}


def product_from_position(position):
    tree = position["parametric_tree"]
    if isinstance(tree, str):
        tree = json.loads(tree)
    if tree.get("version") == "product-v2":
        return deepcopy(tree)
    return {"version": "product-v2", "assembly": {"couplings": [], "modules": [{
        "id": "single", "width_mm": str(position["width_mm"]), "height_mm": str(position["height_mm"]), "tree": deepcopy(tree)}]}}


def design_from_product(product, system_id, color):
    model = parse_product_model(product)
    width, height = elevation_envelope(model.assembly)
    single = (len(model.assembly.modules) == 1 and not model.assembly.couplings
              and model.assembly.modules[0].contour is None
              and model.assembly.modules[0].frameless is None)
    return {"system_id": UUID(str(system_id)), "color": color,
            "nominal_width_mm": width, "nominal_height_mm": height,
            "parametric_tree": product["assembly"]["modules"][0]["tree"] if single else product}


def calculate_product(org_id, product, system_id, color, catalog=None):
    repo = SystemParamsRepository()
    params = catalog["params"] if catalog else repo.load_visible(UUID(str(system_id)), org_id)
    model = parse_product_model(product)
    width, height = elevation_envelope(model.assembly)
    evaluation = evaluate_assembly_from_api(product=model, color=color, params=params,
        coupler_articles=repo.load_coupler_articles(UUID(str(system_id)), org_id))
    return evaluation_response({"system_id": str(system_id), "product": product, "color": color,
        "nominal_width_mm": width, "nominal_height_mm": height}, evaluation)


def sale_price(org_id, product, system_id, color, quantity=1):
    """Read-only indicative selling price; no buying costs leave this adapter."""
    with commercial_backend():
        organizations = rows("SELECT currency FROM public.tenancy_organizations WHERE id=%s", [org_id])
        if not organizations:
            raise contract_error(404, "organization_not_found",
                                 "La organización ya no está disponible. Selecciona una organización para continuar.")
        org = organizations[0]
        rules = rows("SELECT * FROM public.pricing_rules WHERE org_id=%s", [org_id])
        currency = org["currency"]
        if not rules:
            return {"net": None, "currency": currency, "reason": "Completa las reglas de precio en Ajustes."}
        rules = rules[0]
        repo = PricingRepository(org_id, datetime.now(ZoneInfo("America/Santiago")).date(), currency, None)
        def quote(value, count):
            design = design_from_product(value, system_id, color)
            mode = PricingMode(rules["pricing_mode"])
            if mode is PricingMode.TARGET_GROSS_MARGIN_PROJECT:
                return {"net": None, "currency": currency, "reason": "El margen objetivo requiere calcular el proyecto completo."}
            calculated = {**rules, **{field: repo.convert(rules[field], currency) for field in ("labor_rate_per_m2", "installation_rate_per_m2")}}
            position = {"system_id": design["system_id"], "width_mm": design["nominal_width_mm"],
                        "height_mm": design["nominal_height_mm"], "parametric_tree": design["parametric_tree"],
                        "color_interior": color, "color_exterior": color, "typology": service._typology(design["parametric_tree"])}
            cost, area, result, formation = position_cost(repo, position, calculated)
            extras = [ExtraLine.model_validate_json(json_text(item)) for item in formation.get("extra_lines", [])]
            net = configured_unit_price(repo, mode, position, cost=cost, area=area, result=result,
                                       margin=rules["default_margin_pct"], context_code="DEFAULT", extras=extras)
            return {"net": str(indicative_line_net(net, count, currency)), "unit_net": str(net), "currency": currency, "reason": None,
                    "source": "Motor comercial; modo y tarifa predeterminados de Ajustes; precio neto indicativo sin descuento."}

        try:
            price = quote(product, quantity)
            modules = product.get("assembly", {}).get("modules", [])
            if price.get("net") is not None and len(modules) > 1:
                from dekopen_engine.commercial import assembly_sale_adjustment
                component_prices = []
                for module in modules:
                    single = {"version":"product-v2", "assembly":{"modules":[module], "couplings":[]}}
                    try:
                        component = quote(single, 1)
                    except (PricingError, ContractAPIException, InvalidEngineRequest, UnsupportedEngineContract,
                            CatalogRuleError, OpeningCapabilityError, MissingFabricationAuthority) as error:
                        component = {"net": None, "reason": pricing_public_detail(error.code)
                                     if isinstance(error, PricingError) else "Completa la tarifa y autoridad de este módulo."}
                    component_prices.append({"module_id":module["id"], "net":component.get("net"), "reason":component.get("reason")})
                common = assembly_sale_adjustment(Decimal(price["unit_net"]), [Decimal(item["net"]) for item in component_prices], currency) if all(item["net"] is not None for item in component_prices) else None
                price.update({"modules":component_prices, "assembly_adjustment_net":str(common) if common is not None else None,
                    "breakdown_source":"Cada módulo se cotiza con sus propias medidas, apertura y vidrio. Acoples y ajustes = precio unitario del conjunto − suma de módulos; incluye las uniones de la BOM, costos comunes y diferencias de tarifa. No es una distribución proporcional."})
            return price
        except (PricingError, ContractAPIException) as error:
            detail = pricing_public_detail(error.code) if isinstance(error, PricingError) else error.public_detail
            return {"net": None, "currency": currency, "reason": detail}
        except (InvalidEngineRequest, UnsupportedEngineContract, CatalogRuleError, OpeningCapabilityError, MissingFabricationAuthority):
            return {"net": None, "currency": currency,
                    "reason": "Sin dato: completa el vidrio y la autoridad de fabricación del diseño en el editor."}


def _diff(before, after, path=""):
    if before == after:
        return []
    if isinstance(before, dict) and isinstance(after, dict):
        return [change for key in dict.fromkeys([*before, *after])
                for change in _diff(before.get(key), after.get(key), f"{path}.{key}" if path else key)]
    if isinstance(before, list) and isinstance(after, list) and len(before) == len(after):
        return [change for index, (left, right) in enumerate(zip(before, after, strict=True))
                for change in _diff(left, right, f"{path}[{index}]")]
    return [{"field": path, "before": before, "after": after}]


def simulate_ops(org_id, product, ops, system_id, color, quantity=1):
    previous_system, previous_color = system_id, color
    catalog = catalog_for(org_id, system_id)
    before = as_product(product)
    if not ops:
        # A read-only editor quote evaluates accepted intent without inventing
        # a mutation. Actual editing still requires the engine's operation gate.
        output = {"product": before, "ops": [], "registry_version": VERSION}
    elif any(BY_NAME.get(op.get("op"), {}).get("scope") == "position" for op in ops):
        current = deepcopy(before)
        normalized = []
        for raw in ops:
            op = validate_operation(raw)
            if BY_NAME[op["op"]]["scope"] == "position":
                attributes = resolve_attributes(org_id, system_id, color, op)
                system_id, color = attributes["system_id"], attributes["color"]
                catalog = catalog_for(org_id, system_id)
                normalized.append({**op, "base_sig": fingerprint(current), "result": deepcopy(current),
                                   "context_effect": attributes, "description": BY_NAME[op["op"]]["description"]})
            else:
                edit = apply_operations(current, [op], params=catalog["params"], catalog=catalog, finish=color)
                current = edit["product"]
                normalized.extend(edit["ops"])
        output = {"product": current, "ops": normalized, "registry_version": VERSION}
    else:
        output = apply_operations(before, ops, params=catalog["params"], catalog=catalog, finish=color)
    engine = calculate_product(org_id, output["product"], system_id, color, catalog)
    same_design = before == output["product"] and previous_system == system_id and previous_color == color
    try:
        previous_engine = engine if same_design else calculate_product(org_id, before, previous_system, previous_color)
    except (ValueError, InvalidEngineRequest, UnsupportedEngineContract, CatalogRuleError, OpeningCapabilityError, MissingFabricationAuthority):
        previous_engine = None
    issues = engine.get("issues", [])
    valid = engine.get("status") in {"VALID", "MANUFACTURING_INCOMPLETE"} and not any(issue.get("severity") == "error" for issue in issues)
    previous = sale_price(org_id, before, previous_system, previous_color, quantity)
    price = (previous if same_design else sale_price(org_id, output["product"], system_id, color, quantity)) if valid else {"net": None, "currency": previous["currency"], "reason": "Corrige la geometría antes de preciar."}
    delta = str(finish_selling_delta(Decimal(previous["net"]), Decimal(price["net"]))) if price.get("net") is not None and previous.get("net") is not None else None
    return {**output, "system_id": str(system_id), "color": color, "valid": valid, "status": engine["status"], "issues": issues, "engine": engine,
            "before": {"product": before, "system_id": str(previous_system), "color": previous_color, "price": previous, "engine": previous_engine}, "price": {**price, "delta_net": delta},
            "diff": _diff(before, output["product"]) + _diff(
                {"system_id": str(previous_system), "color": previous_color},
                {"system_id": str(system_id), "color": color}, "attributes")}


def resolve_attributes(org_id, system_id, color, op):
    if op["op"] == "set_system":
        catalog_for(org_id, op["system_id"])
        return {"system_id": op["system_id"], "color": color}
    catalog = catalog_for(org_id, system_id)
    authority = catalog["params"].finish_authority
    if authority is None:
        if op["interior"] != op["exterior"] or op["interior"] not in catalog["params"].finishes:
            raise OperationError("finish_not_available", "Las caras no están declaradas por esta serie.")
        return {"system_id": str(system_id), "color": op["interior"]}
    chosen = next((combination for combination in authority.combinations
                   if combination.interior == op["interior"] and combination.exterior == op["exterior"]), None)
    if chosen is None:
        raise OperationError("finish_not_available", "La combinación no está en la carta de esta serie.")
    return {"system_id": str(system_id), "color": chosen.code}


def actor_for(org_id, user_id):
    return resolve_tenant_context(MembershipRepository().list_active_for_user(user_id), str(org_id))


class OperationsRegistryView(APIView):
    @extend_schema(operation_id="design_operations_registry", responses={200: OperationsRegistrySerializer, **ERRORS}, **SCHEMA)
    def get(self, request):
        with scope(request, READ_ROLES):
            return response({"version": VERSION, "operations": REGISTRY})


class SimulateOpsView(APIView):
    parser_classes = [DecimalJSONParser]
    @extend_schema(operation_id="design_operations_simulate", request=SimulateOpsSerializer,
                   responses={200: SimulationSerializer, **ERRORS}, **SCHEMA)
    def post(self, request):
        data = validate(SimulateOpsSerializer, request.data)
        try:
            with scope(request, READ_ROLES) as (_, _, org):
                return response(simulate_ops(org, data["product"], data["ops"], data["system_id"], data["color"], data["quantity"]))
        except OperationError as error:
            raise contract_error(422, error.code, str(error)) from error
        except (ValueError, InvalidEngineRequest, UnsupportedEngineContract) as error:
            raise contract_error(422, "design_operation_invalid",
                "No se puede simular el cambio: el diseño no cumple el contrato. Revisa el marco y su catálogo.") from error
