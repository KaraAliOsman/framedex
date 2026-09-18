"""Typed project metadata and engine-owned position inputs."""

from decimal import Decimal

from rest_framework import serializers

from engine_api.serializers import (
    EngineCalculateRequestSerializer,
    EngineCalculateResponseSerializer,
    DecimalStringField,
)
from pricing.serializers import StrictSerializer


class ProjectWriteSerializer(StrictSerializer):
    name = serializers.CharField(max_length=255)
    client_name = serializers.CharField(max_length=255)
    client_rut = serializers.CharField(max_length=50, required=False, allow_blank=True)
    client_email = serializers.EmailField(required=False, allow_blank=True)
    client_phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    delivery_address = serializers.CharField(required=False, allow_blank=True)
    notes_commercial = serializers.CharField(required=False, allow_blank=True)
    notes_internal = serializers.CharField(required=False, allow_blank=True)


class ProjectUpdateSerializer(ProjectWriteSerializer):
    expected_updated_at = serializers.DateTimeField()


class PositionDesignSerializer(EngineCalculateRequestSerializer, StrictSerializer):
    nominal_width_mm = DecimalStringField(max_digits=10, decimal_places=2, min_value=Decimal("250"))
    nominal_height_mm = DecimalStringField(
        max_digits=10, decimal_places=2, min_value=Decimal("250")
    )
    color = serializers.ChoiceField(choices=["WHITE"])


class PositionWriteSerializer(StrictSerializer):
    location_tag = serializers.CharField(max_length=100, allow_blank=True)
    quantity = serializers.IntegerField(min_value=1, max_value=2147483647)
    design = PositionDesignSerializer()


class PositionUpdateSerializer(PositionWriteSerializer):
    expected_updated_at = serializers.DateTimeField()


class PositionResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    project_id = serializers.UUIDField()
    position_index = serializers.IntegerField()
    location_tag = serializers.CharField(allow_null=True)
    quantity = serializers.IntegerField()
    typology = serializers.CharField()
    design = EngineCalculateRequestSerializer()
    bom = EngineCalculateResponseSerializer()
    updated_at = serializers.DateTimeField()


class ProjectResponseSerializer(ProjectWriteSerializer):
    id = serializers.UUIDField()
    code = serializers.CharField()
    status = serializers.ChoiceField(
        choices=[
            "DRAFT",
            "QUOTED",
            "APPROVED",
            "IN_PRODUCTION",
            "COMPLETED",
            "CANCELLED",
        ]
    )
    current_revision = serializers.CharField()
    total_price_net = serializers.CharField()
    total_price_tax = serializers.CharField()
    total_price_gross = serializers.CharField()
    pricing_current = serializers.BooleanField()
    position_count = serializers.IntegerField()
    updated_at = serializers.DateTimeField()
    positions = PositionResponseSerializer(many=True, required=False)


class ProjectListResponseSerializer(serializers.Serializer):
    items = ProjectResponseSerializer(many=True)


class CloneProjectSerializer(StrictSerializer):
    name = serializers.CharField(max_length=255, required=False)
    expected_updated_at = serializers.DateTimeField()


class DeletePositionSerializer(StrictSerializer):
    expected_updated_at = serializers.DateTimeField()
