"""Read-only class explanation and priced next-class proposals, from the engine."""

from datetime import datetime
from zoneinfo import ZoneInfo

from django.db import DatabaseError
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.errors import contract_error
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from dekopen_engine.geometry import compute_geometry
from dekopen_engine.hardware import NoCompatibleHardwareKit, AmbiguousHardwareKit, resolve_hardware_evaluations
from dekopen_engine.hardware_classes import hardware_sale_price, hardware_price_delta, hardware_total_sale_price
from dekopen_engine.hardware_proposals import split_hardware_bay
from dekopen_engine.models import HardwareItem
from engine_api.adapter import parse_parametric_node, InvalidEngineRequest
from engine_api.repository import SystemParamsRepository, SystemNotFound, UnsupportedCatalogContract
from pricing.repository import PricingRepository, commercial_backend, rows
from pricing.serializers import StrictSerializer
from engine_api.serializers import DecimalStringField
from pricing.views import ERRORS, scope, validate
from dekopen_engine.commercial import PricingError


class HardwarePreviewRequestSerializer(StrictSerializer):
    system_id = serializers.UUIDField()
    width_mm = DecimalStringField(max_digits=10, decimal_places=2)
    height_mm = DecimalStringField(max_digits=10, decimal_places=2)
    color = serializers.CharField(max_length=50)
    bay_id = serializers.CharField(max_length=200)
    parametric_tree = serializers.JSONField()


class HardwareCandidateSerializer(serializers.Serializer):
    sku = serializers.CharField()
    name = serializers.CharField()
    compatible = serializers.BooleanField()
    selected = serializers.BooleanField()
    violations = serializers.ListField(child=serializers.CharField())
    resolution = serializers.JSONField(allow_null=True)
    contents = serializers.ListField(child=serializers.JSONField())
    price_net = serializers.CharField(allow_null=True)
    price_reason = serializers.CharField(allow_null=True)
    delta_net = serializers.CharField(allow_null=True)
    class_authority = serializers.JSONField(allow_null=True)


class HardwareLeafPreviewSerializer(serializers.Serializer):
    leaf_id = serializers.CharField(allow_null=True)
    editable = serializers.BooleanField()
    width_mm = serializers.CharField()
    height_mm = serializers.CharField()
    candidates = HardwareCandidateSerializer(many=True)
    recommendation_sku = serializers.CharField(allow_null=True)
    message = serializers.CharField(allow_null=True)


class HardwarePreviewSerializer(serializers.Serializer):
    leaves = HardwareLeafPreviewSerializer(many=True)
    pricing_basis = serializers.CharField()
    is_demo = serializers.BooleanField()
    division = serializers.JSONField(allow_null=True)


def preview_hardware(org_id, data):
    params = SystemParamsRepository().load_visible(data["system_id"], org_id)
    from dekopen_engine.finishes import prepare_finish
    params = prepare_finish(params, data["color"])
    original = parse_parametric_node(data["parametric_tree"])
    target = None
    def automatic(node):
        nonlocal target
        if node.id == data["bay_id"]:
            target = node
        return node.model_copy(update={"hardware_set_sku": None if node.id == data["bay_id"] else node.hardware_set_sku,
            "children": [automatic(child) for child in node.children]})
    root = automatic(original).model_copy(update={"width_mm": data["width_mm"], "height_mm": data["height_mm"]})
    if target is None:
        raise contract_error(400, "hardware_bay_missing", "El vano ya no existe. Selecciona una hoja del diseño actual.")
    computation = compute_geometry(root, params, diagnostic=True, diagnose_catalog_limits=True, finish=data["color"])
    leaves = [leaf for leaf in computation.leaves if leaf.bay_id == data["bay_id"]]
    result = []
    division = None
    for leaf in leaves:
        catalog_failures = [str(error) for error in computation.catalog_violations
            if error.params.get("bay") == leaf.bay_id]
        editable = leaf.opening is None or leaf.opening.leaf_role.value != "PASSIVE"
        selected_sku = target.hardware_set_sku if editable else None
        if selected_sku is None and leaf.selected_kit is not None:
            selected_sku = leaf.selected_kit.sku
        matched = [candidate for candidate in leaf.candidates if candidate.opening_match and candidate.rail_match]
        candidates = []
        prices = {}
        for candidate in matched:
            expansion = candidate.expansion
            price, reason = None, None
            contents = expansion.contents if expansion is not None else candidate.kit.contents
            item = HardwareItem(kit_sku=candidate.kit.sku, name=candidate.kit.name,
                bay_id=leaf.bay_id, leaf_id=leaf.leaf_id, contents=contents,
                **({"resolution": expansion.resolution} if expansion is not None else {}))
            if candidate.kit.class_authority is not None and expansion is None:
                reason = "Sin dato: la selección no permite expandir los componentes."
            else:
                try:
                    with commercial_backend():
                        rules = rows("SELECT default_margin_pct,waste_factor_pct FROM public.pricing_rules WHERE org_id=%s", [org_id])
                        if not rules:
                            raise PricingError("pricing_rules_not_found")
                        repo = PricingRepository(org_id, datetime.now(ZoneInfo("America/Santiago")).date(), "CLP", None)
                        rates = ({(component.sku, component.price_unit): repo.cost(component.sku, component.price_unit) for component in contents}
                            if expansion is not None else {(candidate.kit.sku, "KIT"): repo.cost(candidate.kit.sku, "KIT")})
                        price = hardware_sale_price(item, rates, waste_pct=rules[0]["waste_factor_pct"], margin_pct=rules[0]["default_margin_pct"])
                        prices[candidate.kit.sku] = price
                except PricingError:
                    reason = "Sin dato: completa la lista de costos, su vigencia y las reglas de precio."
            failures = [*catalog_failures, *[message for _, message in candidate.violations]]
            if not candidate.width_match or not candidate.height_match:
                failures.append(f"Hoja {leaf.finished_width_mm} × {leaf.finished_height_mm} mm; rango {candidate.kit.min_leaf_width_mm}–{candidate.kit.max_leaf_width_mm} × {candidate.kit.min_leaf_height_mm}–{candidate.kit.max_leaf_height_mm} mm. Ajusta la medida o divide la bahía.")
            mass = candidate.exact_total_weight.total_weight_kg
            if candidate.weight_match is False:
                failures.append(f"Hoja {mass} kg; {candidate.kit.name} admite hasta {candidate.kit.max_leaf_weight_kg} kg. Usa la siguiente clase compatible o reduce el ancho.")
            if candidate.weight_match is None:
                labels = {"missing_profile_mass": "perfiles", "missing_steel_mass": "refuerzos",
                    "missing_hardware_component_mass": "componentes de herraje", "missing_hardware_mass": "herrajes",
                    "missing_infill_mass": "vidrio o panel", "missing_screw_mass": "tornillos"}
                missing = sorted({labels.get(reason.split(":")[0], "un componente de la hoja")
                    for reason in candidate.exact_total_weight.weight_unknown_reasons})
                failures.append("Sin dato: falta masa de " + ", ".join(missing) + ". Completa las fuentes del catálogo.")
            candidates.append({"sku": candidate.kit.sku, "name": candidate.kit.name,
                "compatible": candidate.compatible and not catalog_failures, "selected": candidate.kit.sku == selected_sku,
                "violations": failures, "resolution": None if expansion is None else expansion.resolution.model_dump(mode="json"),
                "contents": [component.model_dump(mode="json") for component in contents],
                "price_net": None if price is None else str(price), "price_reason": reason, "delta_net": None,
                "class_authority": None if candidate.kit.class_authority is None else candidate.kit.class_authority.model_dump(mode="json")})
        reference = prices.get(selected_sku)
        if reference is not None:
            for candidate_row in candidates:
                if candidate_row["sku"] in prices:
                    candidate_row["delta_net"] = str(hardware_price_delta(reference, prices[candidate_row["sku"]]))
        selected = next((candidate for candidate in candidates if candidate["selected"]), None)
        recommended, message = None, None
        if (selected is not None and not selected["compatible"]) or (selected is None and selected_sku is not None):
            message = " ".join(selected["violations"]) if selected else "La clase guardada no está disponible para esta apertura. Revisa la siguiente clase del catálogo antes de aplicar."
            try:
                if catalog_failures:
                    raise NoCompatibleHardwareKit("El límite del sistema exige revisar la geometría.")
                next_kit, _ = resolve_hardware_evaluations(leaf.candidates, opening=leaf.opening_type,
                    leaf_width_mm=leaf.finished_width_mm, leaf_height_mm=leaf.finished_height_mm)
                recommended = next_kit.sku
            except (NoCompatibleHardwareKit, AmbiguousHardwareKit):
                pass
        if selected is None and not any(candidate["compatible"] for candidate in candidates):
            message = " ".join(candidates[0]["violations"]) if candidates else "Sin dato: no hay una clase declarada para esta apertura. Completa el catálogo."
        if editable and message and recommended is None and division is None:
            alternative = split_hardware_bay(root,params,bay_id=data["bay_id"],dimensions=computation.node_dimensions)
            if alternative is not None:
                tree, bom = alternative
                items = [item for item in bom.hardware_items if item.bay_id.startswith(data["bay_id"]+":division:")]
                split_price, split_reason = None, None
                try:
                    with commercial_backend():
                        rule = rows("SELECT default_margin_pct,waste_factor_pct FROM public.pricing_rules WHERE org_id=%s",[org_id])
                        if not rule:
                            raise PricingError("pricing_rules_not_found")
                        repo = PricingRepository(org_id,datetime.now(ZoneInfo("America/Santiago")).date(),"CLP",None)
                        rates = {(component.sku,component.price_unit):repo.cost(component.sku,component.price_unit)
                            for item in items for component in item.contents}
                        split_price = hardware_total_sale_price(items,rates,waste_pct=rule[0]["waste_factor_pct"],margin_pct=rule[0]["default_margin_pct"])
                except PricingError:
                    split_reason = "Sin dato: completa los costos de los componentes y las reglas de precio."
                division = {"tree": tree.model_dump(mode="json"), "price_net": None if split_price is None else str(split_price),
                    "delta_net": None if split_price is None or reference is None else str(hardware_price_delta(reference,split_price)),
                    "price_reason": split_reason,
                    "description": "Una hoja → dos hojas con montante. El motor acepta su apertura, clase y componentes; cotiza la posición para comparar el precio completo."}
        result.append({"leaf_id": leaf.leaf_id,
            "editable": editable,
            "width_mm": str(leaf.finished_width_mm),
            "height_mm": str(leaf.finished_height_mm), "candidates": candidates,
            "recommendation_sku": recommended, "message": message})
    return {"leaves": result, "division": division, "is_demo": any(kit.class_authority is not None and kit.class_authority.synthetic for kit in params.available_hardware_kits),
        "pricing_basis": "Precio neto de herrajes por hoja, con merma y margen vigentes de la organización. El precio completo se confirma al cotizar."}


class HardwarePreviewView(APIView):
    @extend_schema(operation_id="hardware_preview", parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=HardwarePreviewRequestSerializer, responses={200: HardwarePreviewSerializer, **ERRORS}, tags=["projects"])
    def post(self, request):
        data = validate(HardwarePreviewRequestSerializer, request.data)
        try:
            with scope(request, allowed=("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")) as (_, _, org_id):
                result = preview_hardware(org_id, data)
        except (InvalidEngineRequest, ValueError, SystemNotFound, UnsupportedCatalogContract) as error:
            raise contract_error(422, "hardware_authority_required", "Sin dato: revisa las medidas, el vidrio y las fuentes del catálogo antes de resolver herrajes.") from error
        except DatabaseError as error:
            raise contract_error(409, "hardware_preview_unavailable", "No se pudo leer la autoridad. Vuelve a cargar el catálogo.") from error
        return Response(result)
