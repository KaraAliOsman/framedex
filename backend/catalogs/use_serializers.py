"""Public dependency-specific catalog permissions."""

from rest_framework import serializers

LEVELS = ("DRAWABLE", "QUOTABLE", "MANUFACTURABLE", "MACHINE_READY")


class CatalogPendingSerializer(serializers.Serializer):
    field = serializers.CharField()
    rule = serializers.CharField()
    origin = serializers.ChoiceField(choices=["MANUAL", "WORKSHOP", "SUGGESTED"], allow_null=True)
    action = serializers.CharField()
    required_for = serializers.ListField(child=serializers.ChoiceField(choices=LEVELS))
    resource = serializers.CharField()
    row_id = serializers.UUIDField(allow_null=True)


class CatalogUseCapabilitySerializer(serializers.Serializer):
    level = serializers.ChoiceField(choices=LEVELS)
    ok = serializers.BooleanField()
    pending = CatalogPendingSerializer(many=True)


class CatalogUseSerializer(serializers.Serializer):
    level = serializers.ChoiceField(choices=LEVELS, allow_null=True)
    levels = CatalogUseCapabilitySerializer(many=True)
    pending = CatalogPendingSerializer(many=True)
    suggested_count = serializers.IntegerField(min_value=0)
    verified = serializers.BooleanField()
    is_example = serializers.BooleanField()
    scope = serializers.CharField()
