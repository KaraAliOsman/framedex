"""Typed HTTP edge; field authority is checked again inside every transaction."""

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from documents.views import documentary_scope, validate, ERRORS
from pricing.serializers import StrictSerializer
from production import field
from production.views import public_production_errors

SCHEMA = {"parameters": [ACTIVE_ORGANIZATION_HEADER], "tags": ["field"]}


class FieldUnitChoiceSerializer(StrictSerializer):
    position_id = serializers.UUIDField()
    unit_index = serializers.IntegerField(min_value=1, max_value=10000)
    order_id = serializers.UUIDField(required=False, allow_null=True)


class FieldScheduleSerializer(StrictSerializer):
    operation_key = serializers.UUIDField()
    project_id = serializers.UUIDField()
    project_version_id = serializers.UUIDField(required=False, allow_null=True)
    kind = serializers.ChoiceField(choices=("DELIVERY", "MEASUREMENT", "INSTALLATION", "SERVICE"))
    assigned_to = serializers.UUIDField()
    planned_on = serializers.DateField()
    team = serializers.CharField(max_length=120)
    vehicle = serializers.CharField(required=False, allow_blank=True, max_length=120)
    address = serializers.CharField(required=False, max_length=1000)
    units = FieldUnitChoiceSerializer(many=True, allow_empty=False)

    def validate_units(self, value):
        if len(value) > 100:
            raise serializers.ValidationError("Agenda hasta cien unidades por visita.")
        return value


class FieldChecksSerializer(StrictSerializer):
    installed = serializers.BooleanField()
    levelled = serializers.BooleanField()
    sealed = serializers.BooleanField()
    adjusted = serializers.BooleanField()
    clean = serializers.BooleanField()


class FieldCommandSerializer(StrictSerializer):
    operation_key = serializers.UUIDField()
    kind = serializers.ChoiceField(
        choices=(
            "LOAD",
            "DEPART",
            "DELIVER",
            "CHECK",
            "MEASURE",
            "INCIDENT",
            "RECEIVE",
            "DIAGNOSE",
            "RESOLVE",
            "CLOSE",
            "CANCEL",
        )
    )
    position_id = serializers.UUIDField(required=False)
    unit_index = serializers.IntegerField(required=False, min_value=1, max_value=10000)
    scan = serializers.CharField(required=False, max_length=3000, allow_blank=True)
    note = serializers.CharField(required=False, max_length=2000, allow_blank=True)
    photo_b64 = serializers.CharField(required=False, max_length=2_000_000)
    signature_b64 = serializers.CharField(required=False, max_length=270_000)
    checks = FieldChecksSerializer(required=False)
    measurements = serializers.ListField(
        child=serializers.JSONField(), required=False, max_length=20
    )
    incident_kind = serializers.ChoiceField(
        choices=("DAMAGE", "MEASURE", "MISSING", "ADJUSTMENT", "WARRANTY", "SERVICE"),
        required=False,
    )
    incident_id = serializers.UUIDField(required=False)
    confirmed = serializers.BooleanField(required=False, default=False)
    receiver_name = serializers.CharField(required=False, max_length=255)
    receiver_rut = serializers.CharField(required=False, max_length=30)
    resolution_kind = serializers.ChoiceField(
        choices=("REMAKE", "PURCHASE", "SERVICE"), required=False
    )
    requirement_id = serializers.UUIDField(required=False)
    quantity = serializers.IntegerField(required=False, min_value=1, max_value=10000)
    planned_on = serializers.DateField(required=False)
    assigned_to = serializers.UUIDField(required=False)
    team = serializers.CharField(required=False, max_length=120)


class FieldVisitSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    code = serializers.CharField()
    project_id = serializers.UUIDField()
    project_version_id = serializers.UUIDField(allow_null=True)
    assigned_to = serializers.UUIDField()
    kind = serializers.CharField()
    planned_on = serializers.DateField()
    team = serializers.CharField()
    vehicle = serializers.CharField(allow_null=True)
    status = serializers.CharField()
    context = serializers.JSONField()
    events = serializers.ListField(child=serializers.JSONField())
    assets = serializers.ListField(child=serializers.JSONField())


class FieldWorkspaceSerializer(serializers.Serializer):
    role = serializers.CharField()
    visits = FieldVisitSerializer(many=True)
    incidents = serializers.ListField(child=serializers.JSONField())
    projects = serializers.ListField(child=serializers.JSONField())
    assignees = serializers.ListField(child=serializers.JSONField())


class FieldReceiptSerializer(serializers.Serializer):
    applied = serializers.BooleanField()
    visit = FieldVisitSerializer()
    operation_key = serializers.UUIDField(required=False)
    event_id = serializers.UUIDField(required=False)
    result = serializers.JSONField(required=False)


class FieldReviewSerializer(StrictSerializer):
    measurement_event_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=1000)
    confirmed = serializers.BooleanField(default=False)
    proposal_token = serializers.CharField(max_length=64, required=False)


class FieldReviewResponseSerializer(serializers.Serializer):
    design = serializers.JSONField()
    measurements = serializers.ListField(child=serializers.JSONField())
    price_change = serializers.JSONField()
    applied = serializers.BooleanField()
    revision_code = serializers.CharField()
    project_id = serializers.UUIDField(allow_null=True)
    project_code = serializers.CharField(allow_null=True)
    proposal_token = serializers.CharField()
    scope = serializers.CharField(required=False)


class FieldAssetAccessSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    signed_url = serializers.URLField()
    file_sha256 = serializers.CharField()
    expires_in = serializers.IntegerField()


class FieldWorkspaceView(APIView):
    @extend_schema(
        operation_id="fieldWorkspace", responses={200: FieldWorkspaceSerializer, **ERRORS}, **SCHEMA
    )
    def get(self, request):
        with (
            public_production_errors(),
            documentary_scope(request, field.READERS) as (token, _, org),
        ):
            return Response(field.workspace(org, token.user_id))


class FieldScheduleView(APIView):
    @extend_schema(
        operation_id="fieldSchedule",
        request=FieldScheduleSerializer,
        responses={201: FieldReceiptSerializer, **ERRORS},
        **SCHEMA,
    )
    def post(self, request):
        data = validate(FieldScheduleSerializer, request.data)
        with (
            public_production_errors(),
            documentary_scope(request, field.READERS[:-1]) as (token, _, org),
        ):
            return Response(field.schedule(org, token.user_id, data), status=201)


class FieldCommandView(APIView):
    @extend_schema(
        operation_id="fieldCommand",
        request=FieldCommandSerializer,
        responses={200: FieldReceiptSerializer, **ERRORS},
        **SCHEMA,
    )
    def post(self, request, visit_id):
        data = validate(FieldCommandSerializer, request.data)
        with (
            field.asset_transaction(),
            public_production_errors(),
            documentary_scope(request, field.READERS) as (token, _, org),
        ):
            return Response(field.command(org, token.user_id, visit_id, data))


class FieldReviewView(APIView):
    @extend_schema(
        operation_id="fieldReview",
        request=FieldReviewSerializer,
        responses={200: FieldReviewResponseSerializer, **ERRORS},
        **SCHEMA,
    )
    def post(self, request, visit_id):
        data = validate(FieldReviewSerializer, request.data)
        with (
            public_production_errors(),
            documentary_scope(request, ("OWNER", "ESTIMATOR")) as (token, tenant, org),
        ):
            return Response(field.review_measurement(org, token.user_id, visit_id, data, tenant))


class FieldAssetAccessView(APIView):
    @extend_schema(
        operation_id="fieldAssetAccess",
        responses={200: FieldAssetAccessSerializer, **ERRORS},
        **SCHEMA,
    )
    def get(self, request, asset_id):
        with (
            public_production_errors(),
            documentary_scope(request, field.READERS) as (token, _, org),
        ):
            return Response(field.asset_access(org, token.user_id, asset_id))
