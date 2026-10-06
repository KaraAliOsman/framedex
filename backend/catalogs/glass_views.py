"""Glass compositor previews and explicit source-backed catalog publication."""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.errors import contract_error
from authentication.rls import catalog_backend
from authentication.views import verified_request_token
from catalogs import glass, service
from catalogs.views import CatalogJSONParser, ERRORS, HEADERS, READ_ROLES, WRITE_HEADERS, catalog_scope, _validated
from dekopen_engine.commercial import PricingError
from dekopen_engine.glass_composition import (
    GlassProduct, GlassProcessing, assess_glass, format_glass_notation,
    glass_mass_per_m2, glass_section, net_glass_thickness, price_glass, total_glass_thickness,
    candidate_leaf_mass,
    glass_rate_requirements,
)
from engine_api.repository import SystemParamsRepository
from pricing.repository import PricingRepository, commercial_backend, json_text, rows
from pricing.serializers import StrictSerializer


class GlassPreviewInputSerializer(StrictSerializer):
    system_id = serializers.UUIDField()
    product = serializers.JSONField()
    processing = serializers.JSONField(required=False)
    width_mm = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"), required=False)
    height_mm = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"), required=False)
    opening_type = serializers.CharField(required=False)
    opening_use = serializers.ChoiceField(choices=["WINDOW", "DOOR"], required=False, allow_null=True)
    is_sidelight = serializers.BooleanField(required=False, default=False)
    sill_height_mm = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"), required=False, allow_null=True)
    hardware_sku = serializers.CharField(required=False, allow_null=True)
    leaf_weight_kg = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"), required=False, allow_null=True)
    previous_infill_kg = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"), required=False, allow_null=True)
    technical_sku = serializers.CharField(required=False)


class GlassFindingSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    source = serializers.CharField(allow_null=True)
    blocking = serializers.BooleanField()
    synthetic = serializers.BooleanField()


class GlassSectionSerializer(serializers.Serializer):
    kind = serializers.CharField()
    x_mm = serializers.CharField()
    width_mm = serializers.CharField()
    label = serializers.CharField()


class GlassPreviewOutputSerializer(serializers.Serializer):
    product = serializers.JSONField()
    notation = serializers.CharField()
    total_thickness_mm = serializers.CharField(allow_null=True)
    net_thickness_mm = serializers.CharField()
    weight_kg_m2 = serializers.CharField(allow_null=True)
    section = GlassSectionSerializer(many=True)
    section_error = serializers.CharField(allow_null=True)
    findings = GlassFindingSerializer(many=True)
    price = serializers.JSONField(allow_null=True)
    price_error = serializers.CharField(allow_null=True)
    alternative_skus = serializers.ListField(child=serializers.CharField())
    dimensions_known = serializers.BooleanField()


class GlassRulesSerializer(StrictSerializer):
    items = serializers.ListField(child=serializers.JSONField(), max_length=200)


class GlassRulesOutputSerializer(GlassRulesSerializer):
    revision = serializers.CharField()
    configured = serializers.BooleanField()
    examples = serializers.ListField(child=serializers.JSONField())


class GlassVariantSerializer(StrictSerializer):
    system_id = serializers.UUIDField()
    technical_sku = serializers.CharField(max_length=100)
    purchasing_sku = serializers.CharField(max_length=100)
    manufacturer_name = serializers.CharField(max_length=255)
    version = serializers.IntegerField(min_value=1)
    product = serializers.JSONField()
    confirmed = serializers.BooleanField()


class GlassVariantOutputSerializer(serializers.Serializer):
    mapping_id = serializers.UUIDField()
    product = serializers.JSONField()
    spec = serializers.CharField()
    technical_sku = serializers.CharField()


def _product(value):
    try:
        return GlassProduct.model_validate_json(json_text(value))
    except (ValueError, TypeError) as error:
        raise contract_error(400, "glass_composition_invalid", "Revisa espesores, cámaras, PVB y fuentes de la composición.") from error


def _rates(repo, product, sku, processing):
    rates = {sku: repo.cost(sku, "M2")}
    for rate_sku, unit in glass_rate_requirements(product, processing):
        rates[rate_sku] = repo.cost(rate_sku, unit)
    return rates


class GlassPreviewView(APIView):
    parser_classes = [CatalogJSONParser]

    @extend_schema(operation_id="catalog_glass_preview", parameters=HEADERS, request=GlassPreviewInputSerializer,
        responses={200: GlassPreviewOutputSerializer, **ERRORS}, tags=["catalogs"])
    def post(self, request):
        data = _validated(GlassPreviewInputSerializer, request.data)
        with catalog_scope(request, roles=READ_ROLES) as org_id:
            product = _product(data["product"])
            try:
                processing = GlassProcessing.model_validate_json(json_text(data.get("processing") or {}))
            except ValueError as error:
                raise contract_error(400, "glass_processing_invalid", "Revisa cantos, perforaciones y palillaje.") from error
            params = SystemParamsRepository().load_visible(data["system_id"], org_id)
            rules = glass.load_safety_rules(org_id)
            dimensions_known = "width_mm" in data and "height_mm" in data
            findings = ()
            if dimensions_known:
                width, height = data["width_mm"], data["height_mm"]
                candidate_weight = candidate_leaf_mass(total_kg=data.get("leaf_weight_kg"),
                    previous_infill_kg=data.get("previous_infill_kg"), candidate=product,
                    area_m2=width * height / Decimal("1000000"))
                kit = next((kit for kit in params.available_hardware_kits if kit.sku == data.get("hardware_sku")), None)
                findings = assess_glass(product, width_mm=width, height_mm=height,
                    bead_thicknesses=tuple(params.glazing_bead_rules), rules=rules,
                    door=glass.is_door_glazing(data), sidelight=data["is_sidelight"],
                    sill_mm=data.get("sill_height_mm"), leaf_weight_kg=candidate_weight,
                    hardware_limit_kg=kit.max_leaf_weight_kg if kit else None)
            total = total_glass_thickness(product.composition)
            mass = glass_mass_per_m2(product)
            section_error = None
            try:
                section = glass_section(product.composition)
            except ValueError as error:
                section, section_error = [], str(error)
            price, price_error = None, None
            if dimensions_known and data.get("technical_sku"):
                with commercial_backend():
                    currency = rows("SELECT currency FROM public.tenancy_organizations WHERE id=%s", [org_id])[0]["currency"]
                    repo = PricingRepository(org_id, timezone.localdate(), currency)
                    try:
                        price = price_glass(product=product, sku=data["technical_sku"], width_mm=data["width_mm"], height_mm=data["height_mm"],
                            rates=_rates(repo, product, data["technical_sku"], processing), processing=processing).model_dump(mode="json")
                        owner = rows("SELECT private.pricing_role(%s,ARRAY['OWNER']) AS allowed", [org_id])[0]["allowed"]
                        if not owner:
                            price = {key: price[key] for key in ("area_m2", "billable_area_m2", "bars_length_m", "bars_crossings")}
                    except (ValueError, PricingError):
                        price_error = "Sin dato · falta una tarifa vigente para el producto o sus procesos. Completa la lista de costos."
            alternatives = []
            for item in glass.load_products(data["system_id"], org_id):
                candidate = item["resolved_product"]
                if not candidate or candidate == product:
                    continue
                if dimensions_known:
                    candidate_weight = candidate_leaf_mass(total_kg=data.get("leaf_weight_kg"),
                        previous_infill_kg=data.get("previous_infill_kg"), candidate=candidate,
                        area_m2=data["width_mm"] * data["height_mm"] / Decimal("1000000"))
                    checks = assess_glass(candidate, width_mm=data["width_mm"], height_mm=data["height_mm"],
                        bead_thicknesses=tuple(params.glazing_bead_rules), rules=rules,
                        door=glass.is_door_glazing(data), sidelight=data["is_sidelight"],
                        sill_mm=data.get("sill_height_mm"), leaf_weight_kg=candidate_weight,
                        hardware_limit_kg=kit.max_leaf_weight_kg if kit else None)
                    if any(check.blocking or check.code in {code for rule in rules for code in (rule.code, rule.code + "_height_unknown")} for check in checks):
                        continue
                elif total_glass_thickness(candidate.composition) not in params.glazing_bead_rules:
                    continue
                alternatives.append(item["technical_sku"])
        return Response(GlassPreviewOutputSerializer({
            "product": product.model_dump(mode="json"), "notation": format_glass_notation(product.composition),
            "total_thickness_mm": None if total is None else str(total), "net_thickness_mm": str(net_glass_thickness(product.composition)),
            "weight_kg_m2": None if mass is None else str(mass), "section": section, "section_error": section_error,
            "findings": [value.model_dump(mode="json") for value in findings], "price": price, "price_error": price_error,
            "alternative_skus": alternatives, "dimensions_known": dimensions_known,
        }).data)


class GlassRulesView(APIView):
    parser_classes = [CatalogJSONParser]

    @extend_schema(operation_id="catalog_glass_rules", parameters=HEADERS,
        responses={200: GlassRulesOutputSerializer, **ERRORS}, tags=["catalogs"])
    def get(self, request):
        with catalog_scope(request, roles=READ_ROLES) as org_id:
            result = glass.rules_snapshot(org_id)
        return Response(GlassRulesOutputSerializer(result).data)

    @extend_schema(operation_id="catalog_glass_rules_replace", parameters=WRITE_HEADERS, request=GlassRulesSerializer,
        responses={200: GlassRulesOutputSerializer, **ERRORS}, tags=["catalogs"])
    def put(self, request):
        data = _validated(GlassRulesSerializer, request.data)
        with catalog_scope(request) as org_id:
            result = glass.replace_safety_rules(org_id, verified_request_token(request).user_id, data["items"], request.headers.get("If-Match"))
        return Response(GlassRulesOutputSerializer(result).data)


class GlassVariantView(APIView):
    parser_classes = [CatalogJSONParser]

    @extend_schema(operation_id="catalog_glass_variant_publish", parameters=HEADERS, request=GlassVariantSerializer,
        responses={201: GlassVariantOutputSerializer, **ERRORS}, tags=["catalogs"])
    def post(self, request):
        data = _validated(GlassVariantSerializer, request.data)
        if not data["confirmed"]:
            raise contract_error(400, "glass_variant_confirmation", "Revisa la composición antes de publicarla.")
        product = _product(data["product"]).model_copy(update={"authority_id": None})
        from ingest.catalog_review import GLASS
        with catalog_scope(request) as org_id, transaction.atomic():
            SystemParamsRepository().load_visible(data["system_id"], org_id)
            spec = format_glass_notation(product.composition)
            if len(spec) > 200:
                raise contract_error(400, "glass_notation_length", "La notación supera 200 caracteres. Revisa los SKU de las capas.")
            row = service.create(GLASS, org_id, {key: data[key] for key in (
                "system_id", "technical_sku", "purchasing_sku", "manufacturer_name", "version")}
                | {"glass_spec": spec, "purchase_unit": "EA", "provenance": {"source": product.source}},
                actor_id=verified_request_token(request).user_id)
            with catalog_backend():
                rows("INSERT INTO public.catalog_glass_compositions(org_id,system_id,mapping_id,status,product,review_reason) "
                    "VALUES(%s,%s,%s,'PARSED',%s::jsonb,'') RETURNING id", [org_id, data["system_id"], row["id"], json_text(product.model_dump(mode="json"))])
        return Response(GlassVariantOutputSerializer({"mapping_id": row["id"], "technical_sku": data["technical_sku"],
            "product": product.model_copy(update={"authority_id": str(row["id"])}).model_dump(mode="json"), "spec": spec}).data, status=201)
