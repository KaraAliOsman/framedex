"""OpenAPI-visible request and response shapes for engine calculation."""

from rest_framework import serializers


class DecimalStringField(serializers.DecimalField):
    def to_internal_value(self, data: object) -> object:
        if not isinstance(data, str):
            self.fail("invalid")
        return super().to_internal_value(data)


class EngineCalculateRequestSerializer(serializers.Serializer):
    system_id = serializers.UUIDField()
    nominal_width_mm = DecimalStringField(max_digits=10, decimal_places=2)
    nominal_height_mm = DecimalStringField(max_digits=10, decimal_places=2)
    color = serializers.CharField(max_length=50)
    parametric_tree = serializers.JSONField()


class ProfileCutSerializer(serializers.Serializer):
    sku = serializers.CharField()
    role = serializers.CharField()
    length_mm = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    angle_left = serializers.DecimalField(max_digits=5, decimal_places=1, coerce_to_string=True)
    angle_right = serializers.DecimalField(max_digits=5, decimal_places=1, coerce_to_string=True)
    qty = serializers.IntegerField()
    bay_id = serializers.CharField(allow_null=True)


class ReinforcementSerializer(serializers.Serializer):
    parent_profile_sku = serializers.CharField()
    reinforcement_sku = serializers.CharField(allow_null=True)
    role = serializers.CharField()
    length_mm = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    qty = serializers.IntegerField()
    bay_id = serializers.CharField(allow_null=True)


class GlassPieceSerializer(serializers.Serializer):
    bay_id = serializers.CharField()
    width_mm = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    height_mm = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    area_m2 = serializers.DecimalField(max_digits=12, decimal_places=4, coerce_to_string=True)
    weight_kg = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    thickness_net_mm = serializers.DecimalField(
        max_digits=12, decimal_places=2, coerce_to_string=True
    )


class EngineCalculateResponseSerializer(serializers.Serializer):
    profile_cuts = ProfileCutSerializer(many=True)
    reinforcements = ReinforcementSerializer(many=True)
    glasses = GlassPieceSerializer(many=True)
    hardware_items = serializers.ListField(child=serializers.DictField())
