"""OpenAPI-visible contracts for the production API."""

from __future__ import annotations

from rest_framework import serializers


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - set(self.fields):
            raise serializers.ValidationError("Unknown input fields")
        return super().to_internal_value(data)


class ProductionStepSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    sequence = serializers.IntegerField()
    code = serializers.CharField()
    label = serializers.CharField()
    status = serializers.ChoiceField(
        choices=("PENDING", "READY", "IN_PROGRESS", "DONE", "BLOCKED")
    )
    work_center_id = serializers.UUIDField(allow_null=True)
    work_center_code = serializers.CharField(allow_null=True)
    started_at = serializers.DateTimeField(allow_null=True)
    finished_at = serializers.DateTimeField(allow_null=True)
    actor_id = serializers.UUIDField(allow_null=True)
    note = serializers.CharField(allow_null=True)


class ProductionOrderSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    order_code = serializers.CharField()
    order_type = serializers.CharField()
    status = serializers.CharField()
    position_id = serializers.CharField(allow_null=True)
    quantity = serializers.IntegerField(allow_null=True)
    steps_done = serializers.IntegerField()
    steps_total = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    project_version_id = serializers.UUIDField(allow_null=True, required=False)
    payload = serializers.DictField(required=False)


class ProductionReleaseSerializer(serializers.Serializer):
    version_id = serializers.UUIDField()
    released = serializers.IntegerField()
    created = serializers.IntegerField()
    orders = ProductionOrderSerializer(many=True)


class ProductionOrderListSerializer(serializers.Serializer):
    orders = ProductionOrderSerializer(many=True)


class ProductionStepEventSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    step_id = serializers.UUIDField(allow_null=True)
    event = serializers.CharField()
    actor_id = serializers.UUIDField(allow_null=True)
    payload = serializers.DictField()
    created_at = serializers.DateTimeField()


class ProductionOrderDetailSerializer(ProductionOrderSerializer):
    steps = ProductionStepSerializer(many=True)
    events = ProductionStepEventSerializer(many=True)


class StepTransitionRequestSerializer(StrictSerializer):
    action = serializers.ChoiceField(choices=("START", "COMPLETE", "BLOCK", "UNBLOCK", "NOTE"))
    note = serializers.CharField(required=False, allow_null=True, max_length=500)


class StepTransitionSerializer(serializers.Serializer):
    step = ProductionStepSerializer()
    order_status = serializers.CharField()


class WorkCenterSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    code = serializers.CharField()
    name = serializers.CharField()
    kind = serializers.CharField()
    display_order = serializers.IntegerField()
    active = serializers.BooleanField()


class WorkCenterListSerializer(serializers.Serializer):
    centers = WorkCenterSerializer(many=True)


class WorkCenterRequestSerializer(StrictSerializer):
    code = serializers.CharField(max_length=50)
    name = serializers.CharField(max_length=200)
    kind = serializers.ChoiceField(choices=("CUT", "ASSEMBLY", "GLAZING", "QC", "PACK"))
    display_order = serializers.IntegerField(required=False, default=0)
