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
    dispatch_note_code = serializers.CharField(allow_null=True, required=False)


class StepTransitionRequestSerializer(StrictSerializer):
    action = serializers.ChoiceField(choices=("START", "COMPLETE", "BLOCK", "UNBLOCK", "NOTE"))
    note = serializers.CharField(required=False, allow_null=True, max_length=500)
    qc_result = serializers.ChoiceField(choices=("PASS", "FAIL"), required=False, allow_null=True)

    def validate(self, data):
        data = super().validate(data)
        if data["action"] == "NOTE" and not (data.get("note") or "").strip():
            raise serializers.ValidationError({"note": "Note text is required for NOTE"})
        if data.get("qc_result") and data["action"] != "COMPLETE":
            raise serializers.ValidationError(
                {"qc_result": "QC outcome only applies to COMPLETE"}
            )
        return data


class CncExportSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    order_code = serializers.CharField()
    exported_at = serializers.CharField()
    files = serializers.DictField(child=serializers.CharField())


class PackingManifestSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    order_code = serializers.CharField()
    packing = serializers.DictField()


class DispatchRequestSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, max_length=500)


class InstallationRequestSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, max_length=500)


class DispatchNoteSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    note_code = serializers.CharField()
    work_order_id = serializers.UUIDField()
    created_at = serializers.DateTimeField()


class DispatchNoteAccessSerializer(DispatchNoteSerializer):
    signed_url = serializers.CharField()
    expires_in = serializers.IntegerField()


class RemakeRequestSerializer(StrictSerializer):
    note = serializers.CharField(required=False, allow_null=True, max_length=500)


class StepTransitionSerializer(serializers.Serializer):
    step = ProductionStepSerializer()
    order_status = serializers.CharField()


class PackingLabelSerializer(serializers.Serializer):
    unit_index = serializers.IntegerField()
    label_code = serializers.CharField()
    pieces = serializers.IntegerField()
    profiles = serializers.IntegerField()
    reinforcements = serializers.IntegerField()
    glasses = serializers.IntegerField()
    panels = serializers.IntegerField()
    hardware = serializers.IntegerField()
    qr_payload = serializers.CharField()
    qr_svg = serializers.CharField()


class PackingLabelsSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    order_code = serializers.CharField()
    status = serializers.CharField()
    labels = PackingLabelSerializer(many=True)


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


class WorkOrderOptimizeRequestSerializer(StrictSerializer):
    color = serializers.CharField(max_length=50)
    cutting_profile_code = serializers.CharField(required=False, allow_null=True, max_length=50)

    def validate(self, data):
        data = super().validate(data)
        if not (data.get("color") or "").strip():
            raise serializers.ValidationError({"color": "Color is required"})
        return data


class WorkOrderOptimizeSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    order_code = serializers.CharField()
    optimization = serializers.DictField()


class DeliverySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    order_id = serializers.UUIDField()
    order_code = serializers.CharField()
    scheduled_date = serializers.CharField()
    time_window = serializers.CharField()
    address = serializers.CharField()
    contact_name = serializers.CharField(allow_null=True)
    contact_phone = serializers.CharField(allow_null=True)
    installer_name = serializers.CharField(allow_null=True)
    notes = serializers.CharField(allow_null=True)
    status = serializers.ChoiceField(
        choices=("SCHEDULED", "ON_ROUTE", "DELIVERED", "FAILED")
    )
    scheduled_by = serializers.UUIDField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class DeliveryResponseSerializer(serializers.Serializer):
    delivery = DeliverySerializer(allow_null=True)


class DeliveryScheduleRequestSerializer(StrictSerializer):
    scheduled_date = serializers.CharField(max_length=10)
    time_window = serializers.ChoiceField(
        choices=("AM", "PM", "JORNADA"), required=False, default="AM"
    )
    address = serializers.CharField(max_length=300)
    contact_name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    contact_phone = serializers.CharField(required=False, allow_blank=True, max_length=50)
    installer_name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)


class DeliveryTransitionRequestSerializer(StrictSerializer):
    status = serializers.ChoiceField(choices=("ON_ROUTE", "DELIVERED", "FAILED"))
