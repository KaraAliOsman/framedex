"""Reviewed thermal reports and explicit human envelope declarations."""

from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import serializers
from rest_framework.views import APIView
from decimal import Decimal
from dekopen_engine.models import BayOpeningType

from pricing.serializers import StrictSerializer
from pricing.views import DecimalJSONParser, ERRORS, scope, validate
from projects import thermal
from projects.views import SCHEMA, READ_ROLES, WRITE_ROLES, response


class ThermalPositionSerializer(StrictSerializer):
    position_id = serializers.UUIDField()
    orientation = serializers.ChoiceField(choices=("N", "E", "S", "W", "OGT"), allow_null=True, required=False)
    surface = serializers.ChoiceField(choices=("WALL", "ROOF"), allow_null=True, required=False)


class ThermalInputSerializer(StrictSerializer):
    zone = serializers.ChoiceField(choices=tuple("ABCDEFGHI"), allow_null=True, required=False)
    zone_source = serializers.CharField(allow_blank=True, max_length=1000, default="")
    use = serializers.ChoiceField(choices=("RESIDENTIAL", "EDUCATION", "HEALTH", "HOTEL"), allow_null=True, required=False)
    walls_m2 = serializers.DictField(child=serializers.DecimalField(max_digits=18, decimal_places=6, min_value=Decimal(0)), required=False)
    exposed_wall_area_m2 = serializers.DecimalField(max_digits=18, decimal_places=6, min_value=Decimal(0), allow_null=True, required=False)
    envelope_complete = serializers.BooleanField(default=False)
    wall_source = serializers.CharField(allow_blank=True, max_length=1000, default="")
    positions = ThermalPositionSerializer(many=True, required=False)
    include_doc01 = serializers.BooleanField(default=False)
    regulatory_scope_confirmed = serializers.BooleanField(default=False)
    regulatory_calculation_source = serializers.CharField(allow_blank=True, max_length=2000, default="")
    regulatory_method_confirmed = serializers.BooleanField(default=False)


class ThermalWriteSerializer(StrictSerializer):
    inputs = ThermalInputSerializer()
    expected_updated_at = serializers.DateTimeField(allow_null=True)


class ThermalReportSerializer(serializers.Serializer):
    inputs = ThermalInputSerializer()
    updated_at = serializers.DateTimeField(allow_null=True)
    sealed = serializers.BooleanField()
    assessment = serializers.JSONField()


class ThermalAuthoritySerializer(StrictSerializer):
    kind = serializers.ChoiceField(choices=("FRAME", "GLASS", "SPACER", "PERFORMANCE"))
    profile_skus = serializers.ListField(child=serializers.CharField(max_length=200), required=False)
    glass_sku = serializers.CharField(max_length=200, allow_null=True, required=False)
    source_position_id = serializers.UUIDField(allow_null=True, required=False)
    spacer_code = serializers.CharField(max_length=200, allow_null=True, required=False)
    uf = serializers.DecimalField(max_digits=12, decimal_places=6, allow_null=True, required=False)
    ug = serializers.DecimalField(max_digits=12, decimal_places=6, allow_null=True, required=False)
    solar_factor = serializers.DecimalField(max_digits=12, decimal_places=6, allow_null=True, required=False)
    psi_g = serializers.DecimalField(max_digits=12, decimal_places=6, allow_null=True, required=False)
    air_class = serializers.IntegerField(min_value=0, max_value=4, allow_null=True, required=False)
    air_pressure_pa = serializers.DecimalField(max_digits=12, decimal_places=6, allow_null=True, required=False)
    water_class = serializers.CharField(max_length=50, allow_null=True, required=False)
    wind_class = serializers.CharField(max_length=50, allow_null=True, required=False)
    min_width_mm = serializers.DecimalField(max_digits=12, decimal_places=2)
    max_width_mm = serializers.DecimalField(max_digits=12, decimal_places=2)
    min_height_mm = serializers.DecimalField(max_digits=12, decimal_places=2)
    max_height_mm = serializers.DecimalField(max_digits=12, decimal_places=2)
    opening_types = serializers.ListField(child=serializers.CharField(max_length=80), min_length=1)
    source_document = serializers.CharField(max_length=500)
    source_url = serializers.URLField(max_length=2000)
    source_page = serializers.CharField(max_length=200)
    laboratory = serializers.CharField(max_length=300)
    laboratory_registration = serializers.CharField(allow_blank=True, max_length=1000, default="")
    report_date = serializers.DateField()
    valid_until = serializers.DateField()
    standard = serializers.CharField(max_length=200)
    applicability = serializers.CharField(max_length=2000)
    synthetic = serializers.BooleanField(default=False)

    def validate_source_url(self, value):
        if not value.startswith(("https://", "http://")):
            raise serializers.ValidationError("Usa una URL HTTP o HTTPS del documento original.")
        return value

    def validate_opening_types(self, values):
        if not set(values) <= {opening.value for opening in BayOpeningType}:
            raise serializers.ValidationError("Elige aperturas declaradas por el motor.")
        return values


class ThermalReviewSerializer(StrictSerializer):
    state = serializers.ChoiceField(choices=("REVIEWED", "REJECTED", "REVOKED"))
    confirmed = serializers.BooleanField()


class ThermalCatalogResponseSerializer(serializers.Serializer):
    is_demo = serializers.BooleanField()
    catalog_fingerprint = serializers.CharField()
    profiles = serializers.ListField(child=serializers.JSONField())
    glasses = serializers.ListField(child=serializers.JSONField())
    specimens = serializers.ListField(child=serializers.JSONField())
    items = serializers.ListField(child=serializers.JSONField())


class ThermalAlternativeSerializer(serializers.Serializer):
    candidate = serializers.JSONField(allow_null=True)
    evaluated = serializers.IntegerField()
    reason = serializers.CharField(allow_null=True)
    scope = serializers.CharField(required=False)


class ProjectThermalView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(operation_id="project_thermal_report", responses={200: ThermalReportSerializer, **ERRORS}, **SCHEMA)
    def get(self, request, project_id):
        with scope(request, READ_ROLES) as (_, _, org):
            return response(thermal.project_report(org, project_id))

    @extend_schema(operation_id="project_thermal_save", request=ThermalWriteSerializer,
                   responses={200: ThermalReportSerializer, **ERRORS}, **SCHEMA)
    def put(self, request, project_id):
        data = validate(ThermalWriteSerializer, request.data)
        with scope(request, WRITE_ROLES) as (token, _, org):
            return response(thermal.save_inputs(org, project_id, token.user_id, data["inputs"], data["expected_updated_at"]))


class ThermalCatalogView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(operation_id="catalog_thermal_reports", responses={200: ThermalCatalogResponseSerializer, **ERRORS}, **SCHEMA)
    def get(self, request, system_id):
        with scope(request, READ_ROLES) as (_, _, org):
            return response(thermal.catalog_reports(org, system_id))

    @extend_schema(operation_id="catalog_thermal_declare", request=ThermalAuthoritySerializer,
                   responses={201: OpenApiTypes.OBJECT, **ERRORS}, **SCHEMA)
    def post(self, request, system_id):
        data = validate(ThermalAuthoritySerializer, request.data)
        with scope(request, ("OWNER", "WORKSHOP_MANAGER")) as (token, _, org):
            return response(thermal.declare_report(org, system_id, token.user_id, data), status=201)


class ThermalReviewView(APIView):
    @extend_schema(operation_id="catalog_thermal_review", request=ThermalReviewSerializer,
                   responses={200: OpenApiTypes.OBJECT, **ERRORS}, **SCHEMA)
    def post(self, request, system_id, report_id):
        data = validate(ThermalReviewSerializer, request.data)
        from authentication.errors import contract_error
        if not data["confirmed"]:
            raise contract_error(400, "thermal_review_confirmation", "Confirma la revisión humana del informe y su alcance.")
        with scope(request, ("OWNER", "WORKSHOP_MANAGER")) as (token, _, org):
            return response(thermal.review_report(org, system_id, report_id, token.user_id, data["state"]))


class ThermalAlternativesView(APIView):
    @extend_schema(operation_id="thermal_compliant_alternative", responses={200: ThermalAlternativeSerializer, **ERRORS}, **SCHEMA)
    def get(self, request, project_id, position_id):
        with scope(request, WRITE_ROLES) as (_, _, org):
            return response(thermal.alternatives(org, project_id, position_id))
