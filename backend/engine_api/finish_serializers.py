"""Face color authority is explicit in the generated API contract."""

from rest_framework import serializers


class FinishColorSerializer(serializers.Serializer):
    code = serializers.CharField()
    manufacturer_code = serializers.CharField()
    name = serializers.CharField()
    kind = serializers.CharField()
    linear_rgb = serializers.ListField(child=serializers.CharField(), min_length=3, max_length=3)
    gloss = serializers.CharField(allow_null=True)
    texture_path = serializers.CharField(allow_null=True)
    approximate = serializers.BooleanField()
    source = serializers.CharField()
    synthetic = serializers.BooleanField()


class FinishSurchargeSerializer(serializers.Serializer):
    kind = serializers.CharField()
    amount = serializers.CharField()
    currency = serializers.CharField()
    source = serializers.CharField()


class FinishCombinationSerializer(serializers.Serializer):
    code = serializers.CharField()
    interior = serializers.CharField()
    exterior = serializers.CharField()
    base = serializers.CharField(allow_null=True)
    reinforcement_required = serializers.BooleanField()
    reinforcement_stock_code = serializers.CharField()
    glass_clearance_mm = serializers.CharField()
    max_position_width_mm = serializers.CharField(allow_null=True)
    max_position_height_mm = serializers.CharField(allow_null=True)
    max_leaf_width_mm = serializers.CharField(allow_null=True)
    max_leaf_height_mm = serializers.CharField(allow_null=True)
    extra_lead_days = serializers.IntegerField(allow_null=True)
    surcharge = FinishSurchargeSerializer()
    allowed_handle_colors = serializers.ListField(child=serializers.CharField())
    source = serializers.CharField()
    synthetic = serializers.BooleanField()


class FinishAuthoritySerializer(serializers.Serializer):
    schema_version = serializers.IntegerField()
    material = serializers.CharField()
    colors = FinishColorSerializer(many=True)
    handle_colors = FinishColorSerializer(many=True, required=False)
    combinations = FinishCombinationSerializer(many=True)
    source = serializers.CharField()


class ResolvedFinishSerializer(serializers.Serializer):
    combination = FinishCombinationSerializer()
    interior = FinishColorSerializer()
    exterior = FinishColorSerializer()
    base = FinishColorSerializer(allow_null=True)
    profile_skus = serializers.DictField(child=serializers.CharField())
    handle_colors = FinishColorSerializer(many=True, required=False)
