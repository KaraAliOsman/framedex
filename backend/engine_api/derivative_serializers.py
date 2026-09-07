"""Typed transports for derived inspection and cutting; calculate stays unchanged."""

from rest_framework import serializers

from engine_api.serializers import DecimalStringField, EngineCalculateRequestSerializer


class AnnotationSerializer(serializers.Serializer):
    bay_id = serializers.CharField()
    leaf_id = serializers.CharField(allow_null=True, required=False, default=None)
    bottom_drain_holes_mm = serializers.ListField(
        child=DecimalStringField(max_digits=14, decimal_places=4), allow_null=True, required=False)
    closing_points_perimeter_mm = serializers.ListField(
        child=DecimalStringField(max_digits=14, decimal_places=4), allow_null=True, required=False)
    continuous_width_mm = DecimalStringField(max_digits=14, decimal_places=4, allow_null=True, required=False)
    finish_class = serializers.ChoiceField(choices=["WHITE", "FOILED"], allow_null=True, required=False)
    has_coupler = serializers.BooleanField(allow_null=True, required=False)
    measured_d1_mm = DecimalStringField(max_digits=14, decimal_places=4, allow_null=True, required=False)
    measured_d2_mm = DecimalStringField(max_digits=14, decimal_places=4, allow_null=True, required=False)


class StructuralInputSerializer(serializers.Serializer):
    target_id = serializers.CharField()
    required_ix_cm4 = DecimalStringField(max_digits=12, decimal_places=4, allow_null=True, required=False)
    structural_basis = serializers.CharField(allow_null=True, allow_blank=True, required=False)


class EngineInspectRequestSerializer(EngineCalculateRequestSerializer):
    annotations = AnnotationSerializer(many=True, required=False, default=list)
    structural_inputs = StructuralInputSerializer(many=True, required=False, default=list)
    mode = serializers.ChoiceField(choices=["DESIGN", "WORKSHOP_QC"], required=False, default="DESIGN")


class EngineOptimizeRequestSerializer(EngineCalculateRequestSerializer):
    cutting_profile_code = serializers.CharField(required=False, allow_null=True, default=None)


class InspectorTargetSerializer(serializers.Serializer):
    bay_id = serializers.CharField()
    leaf_id = serializers.CharField(allow_null=True)


class DrainOperationSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=["ADD_BOTTOM_DRAIN_HOLE"])
    target = InspectorTargetSerializer()
    old_value = serializers.ListField(child=serializers.CharField())
    new_value = serializers.ListField(child=serializers.CharField())


class DiffPreconditionsSerializer(serializers.Serializer):
    opening_width_mm = serializers.CharField()
    bottom_drain_holes_mm = serializers.ListField(child=serializers.CharField())


class InspectorDiffSerializer(serializers.Serializer):
    diff_id = serializers.CharField()
    rule_id = serializers.ChoiceField(choices=["R07"])
    target = InspectorTargetSerializer()
    preconditions = DiffPreconditionsSerializer()
    operations = DrainOperationSerializer(many=True)


class InspectorFindingSerializer(serializers.Serializer):
    rule_id = serializers.ChoiceField(choices=[f"R{i:02d}" for i in range(1, 15)])
    severity = serializers.ChoiceField(choices=["YELLOW", "RED"])
    title = serializers.CharField()
    diagnosis = serializers.CharField()
    risk = serializers.CharField()
    recommendation = serializers.CharField()
    fixability = serializers.ChoiceField(choices=["AUTO_FIXABLE", "SUGGESTION_ONLY", "BLOCKED_MISSING_AUTHORITY"])
    bay_id = serializers.CharField(allow_null=True)
    leaf_id = serializers.CharField(allow_null=True)
    fix = InspectorDiffSerializer(allow_null=True)


class RuleEvaluationSerializer(serializers.Serializer):
    rule_id = serializers.ChoiceField(choices=[f"R{i:02d}" for i in range(1, 15)])
    status = serializers.ChoiceField(choices=["PASS", "FAIL", "NOT_APPLICABLE", "MISSING_INPUT"])
    bay_id = serializers.CharField(allow_null=True)
    leaf_id = serializers.CharField(allow_null=True)


class EngineInspectResponseSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["GREEN", "YELLOW", "RED"])
    production_allowed = serializers.BooleanField()
    evaluations = RuleEvaluationSerializer(many=True)
    findings = InspectorFindingSerializer(many=True)
    source_calculation_hash = serializers.CharField(allow_null=True)


class CutPlacementSerializer(serializers.Serializer):
    piece_id = serializers.CharField()
    source_kind = serializers.ChoiceField(choices=["PROFILE", "REINFORCEMENT"])
    workshop_sku = serializers.CharField()
    material = serializers.ChoiceField(choices=["PVC", "ALUMINIUM", "STEEL"])
    color = serializers.CharField()
    length_mm = serializers.CharField()
    source_position_id = serializers.CharField(allow_null=True)
    bay_id = serializers.CharField(allow_null=True)
    leaf_id = serializers.CharField(allow_null=True)
    role = serializers.CharField()
    unit_index = serializers.IntegerField()
    angle_left = serializers.CharField(allow_null=True)
    angle_right = serializers.CharField(allow_null=True)
    sequence = serializers.IntegerField()


class CutBarSerializer(serializers.Serializer):
    bar_index = serializers.IntegerField()
    commercial_sku = serializers.CharField()
    material = serializers.ChoiceField(choices=["PVC", "ALUMINIUM", "STEEL"])
    color = serializers.CharField()
    stock_length_mm = serializers.CharField()
    head_trim_mm = serializers.CharField()
    tail_trim_mm = serializers.CharField()
    kerf_mm = serializers.CharField()
    cuts = CutPlacementSerializer(many=True)
    kerf_total_mm = serializers.CharField()
    productive_length_mm = serializers.CharField()
    process_consumed_mm = serializers.CharField()
    remainder_mm = serializers.CharField()
    waste_mm = serializers.CharField()
    yield_pct = serializers.CharField()
    waste_pct = serializers.CharField()


class PurchaseLineSerializer(serializers.Serializer):
    commercial_sku = serializers.CharField()
    manufacturer = serializers.CharField()
    supplier = serializers.CharField(allow_null=True)
    stock_length_mm = serializers.CharField()
    material = serializers.ChoiceField(choices=["PVC", "ALUMINIUM", "STEEL"])
    color = serializers.CharField()
    unit = serializers.ChoiceField(choices=["BAR"])
    qty_bars = serializers.IntegerField()


class EngineOptimizeResponseSerializer(serializers.Serializer):
    source_calculation_hash = serializers.CharField()
    purchase_list = PurchaseLineSerializer(many=True)
    workshop_cut_plan = CutBarSerializer(many=True)
