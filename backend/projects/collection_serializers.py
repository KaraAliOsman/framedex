from rest_framework import serializers

from pricing.serializers import StrictSerializer


class CollectionSettingsRequestSerializer(StrictSerializer):
    simulation_enabled = serializers.BooleanField()
    payment_link_days = serializers.IntegerField(min_value=1, max_value=90)
    sii_active = serializers.BooleanField()
    sii_certified = serializers.BooleanField()


class CollectionIntegrationSerializer(CollectionSettingsRequestSerializer):
    flow_connected = serializers.BooleanField()
    sii_connected = serializers.BooleanField()
    flow_environment = serializers.CharField(allow_null=True)
    flow_instructions = serializers.CharField()
    sii_instructions = serializers.CharField()


class CollectionMilestoneSerializer(serializers.Serializer):
    label = serializers.CharField()
    share = serializers.CharField()
    amount = serializers.CharField()
    collected = serializers.CharField()
    remaining = serializers.CharField()
    due_on = serializers.DateField(allow_null=True)
    due_source = serializers.ChoiceField(choices=("DECLARED", "UNKNOWN", "APPROVAL", "APPROVAL_PENDING", "DELIVERY", "DELIVERY_PENDING"))
    status = serializers.ChoiceField(choices=("PENDING", "DUE", "OVERDUE", "PAID"))


class FlowSimulationRequestSerializer(StrictSerializer):
    token = serializers.CharField(min_length=20, max_length=100)
    outcome = serializers.ChoiceField(choices=("PAID", "FAILED"))


class FlowSimulationSerializer(serializers.Serializer):
    amount = serializers.CharField()
    status = serializers.ChoiceField(choices=("PENDING", "PAID", "FAILED", "EXPIRED", "CANCELLED"))
    environment = serializers.ChoiceField(choices=("simulated",))
    expires_at = serializers.DateTimeField(allow_null=True)
    deal_revision = serializers.CharField(allow_null=True)


class FiscalSimulationRequestSerializer(StrictSerializer):
    operation_key = serializers.CharField(min_length=8, max_length=80)
    invoice_id = serializers.UUIDField()
    credit_note_id = serializers.UUIDField(required=False, allow_null=True)
    scenario = serializers.ChoiceField(choices=("ACCEPTED", "WARNINGS", "REJECTED"))


class FiscalSimulationSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    invoice_id = serializers.UUIDField()
    credit_note_id = serializers.UUIDField(allow_null=True)
    folio = serializers.CharField()
    dte_type = serializers.IntegerField()
    status = serializers.ChoiceField(choices=("ACCEPTED", "WARNINGS", "REJECTED"))
    detail = serializers.CharField()
    simulated = serializers.BooleanField()
    actor_label = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()


class FiscalSimulationsSerializer(serializers.Serializer):
    items = FiscalSimulationSerializer(many=True)


class InternalDocumentRequestSerializer(StrictSerializer):
    document_kind = serializers.ChoiceField(choices=("FACTURA", "BOLETA"), required=False, default="FACTURA")


class CollectionReminderSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    recipient = serializers.EmailField()
    reference = serializers.CharField()
    body = serializers.CharField()
    prepared_by_ai = serializers.BooleanField()
    sent = serializers.BooleanField()


class CollectionReminderSendSerializer(StrictSerializer):
    reminder_id = serializers.UUIDField()
    confirmed = serializers.BooleanField()
