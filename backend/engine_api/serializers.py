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
    material = serializers.ChoiceField(choices=["PVC", "ALUMINIUM"])
    length_mm = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    angle_left = serializers.DecimalField(max_digits=5, decimal_places=1, coerce_to_string=True)
    angle_right = serializers.DecimalField(max_digits=5, decimal_places=1, coerce_to_string=True)
    qty = serializers.IntegerField()
    bay_id = serializers.CharField(allow_null=True)
    leaf_id = serializers.CharField(allow_null=True)


class ReinforcementSerializer(serializers.Serializer):
    parent_profile_sku = serializers.CharField()
    reinforcement_sku = serializers.CharField(allow_null=True)
    role = serializers.CharField()
    length_mm = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    qty = serializers.IntegerField()
    bay_id = serializers.CharField(allow_null=True)
    leaf_id = serializers.CharField(allow_null=True)


class GlassPieceSerializer(serializers.Serializer):
    bay_id = serializers.CharField()
    leaf_id = serializers.CharField(allow_null=True)
    width_mm = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    height_mm = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    area_m2 = serializers.DecimalField(max_digits=12, decimal_places=4, coerce_to_string=True)
    weight_kg = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    thickness_net_mm = serializers.DecimalField(
        max_digits=12, decimal_places=2, coerce_to_string=True
    )


class PanelPieceSerializer(serializers.Serializer):
    sku = serializers.CharField()
    name = serializers.CharField()
    bay_id = serializers.CharField()
    leaf_id = serializers.CharField(allow_null=True)
    width_mm = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    height_mm = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    area_m2 = serializers.DecimalField(max_digits=12, decimal_places=4, coerce_to_string=True)
    weight_kg = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)


class HardwareComponentSerializer(serializers.Serializer):
    sku = serializers.CharField()
    name = serializers.CharField()
    qty = serializers.CharField(help_text="Exact Decimal quantity serialized as a string")
    unit = serializers.CharField()


class HardwareItemSerializer(serializers.Serializer):
    kit_sku = serializers.CharField()
    name = serializers.CharField()
    qty = serializers.IntegerField()
    unit = serializers.ChoiceField(choices=["kit"])
    bay_id = serializers.CharField()
    leaf_id = serializers.CharField(allow_null=True)
    contents = HardwareComponentSerializer(many=True)


class LeafWeightSerializer(serializers.Serializer):
    bay_id = serializers.CharField()
    leaf_id = serializers.CharField(allow_null=True)
    pvc_weight_kg = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    steel_weight_kg = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    infill_weight_kg = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    hardware_weight_kg = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    total_weight_kg = serializers.DecimalField(max_digits=12, decimal_places=2, coerce_to_string=True)
    used_fallback = serializers.BooleanField()


class EngineCalculateResponseSerializer(serializers.Serializer):
    profile_cuts = ProfileCutSerializer(many=True)
    reinforcements = ReinforcementSerializer(many=True)
    glasses = GlassPieceSerializer(many=True)
    panels = PanelPieceSerializer(many=True)
    hardware_items = HardwareItemSerializer(many=True)
    leaf_weights = LeafWeightSerializer(many=True)
    calculation_hash = serializers.RegexField(regex=r"^sha256:[0-9a-f]{64}$")


class ProfileSystemSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    code = serializers.CharField()
    name = serializers.CharField()
    is_demo = serializers.BooleanField()


class EngineSystemsResponseSerializer(serializers.Serializer):
    systems = ProfileSystemSummarySerializer(many=True)
