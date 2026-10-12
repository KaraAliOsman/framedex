"""Typed customer dossier commands and read projections."""

from rest_framework import serializers
from pricing.serializers import StrictSerializer


class ClientContactWriteSerializer(StrictSerializer):
    id = serializers.UUIDField(required=False)
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    contact_role = serializers.CharField(max_length=80, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=64, required=False, allow_blank=True)
    is_primary = serializers.BooleanField(required=False, default=False)

    def validate(self, value):
        if not value.get("email", "").strip() and not value.get("phone", "").strip():
            raise serializers.ValidationError("Indica el correo o teléfono del contacto.")
        return value


class ClientAddressWriteSerializer(StrictSerializer):
    id = serializers.UUIDField(required=False)
    label = serializers.CharField(max_length=80)
    address = serializers.CharField(max_length=500)
    comuna = serializers.CharField(max_length=80, required=False, allow_blank=True)


class ClientContactSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    contact_role = serializers.CharField()
    email = serializers.CharField()
    phone = serializers.CharField()
    is_primary = serializers.BooleanField()
    is_active = serializers.BooleanField()
    origin_id = serializers.UUIDField(allow_null=True)
    updated_at = serializers.DateTimeField()


class ClientAddressSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    label = serializers.CharField()
    address = serializers.CharField()
    comuna = serializers.CharField()
    is_active = serializers.BooleanField()
    origin_id = serializers.UUIDField(allow_null=True)
    updated_at = serializers.DateTimeField()


class ClientNoteWriteSerializer(StrictSerializer):
    operation_key = serializers.UUIDField()
    body = serializers.CharField(max_length=4000)


class ClientNoteSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    body = serializers.CharField()
    author_label = serializers.CharField()
    created_at = serializers.DateTimeField()
    is_legacy = serializers.BooleanField()
    source_updated_at = serializers.DateTimeField(allow_null=True)


class ClientMergePreviewRequestSerializer(StrictSerializer):
    target_id = serializers.UUIDField()


class ClientMergeRequestSerializer(ClientMergePreviewRequestSerializer):
    expected_source_updated_at = serializers.DateTimeField()
    expected_target_updated_at = serializers.DateTimeField()
    reason = serializers.CharField(max_length=2000)
    confirmed = serializers.BooleanField()

    def validate_confirmed(self, value):
        if not value:
            raise serializers.ValidationError("Revisa la fusión antes de confirmarla.")
        return value


class ClientMergeFieldSerializer(serializers.Serializer):
    field = serializers.CharField()
    before = serializers.CharField(allow_null=True)
    after = serializers.CharField(allow_null=True)


class ClientMergeRecordSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    source_name = serializers.CharField()
    target_name = serializers.CharField()
    reason = serializers.CharField()
    actor_label = serializers.CharField()
    created_at = serializers.DateTimeField()


class ClientProjectHistorySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    code = serializers.CharField()
    name = serializers.CharField()
    status = serializers.CharField()
    updated_at = serializers.DateTimeField()
    currency = serializers.CharField(allow_null=True)
    revision_code = serializers.CharField(allow_null=True)
    total = serializers.CharField(allow_null=True)
    collected = serializers.CharField(allow_null=True)
    balance = serializers.CharField(allow_null=True)
    money_cause = serializers.CharField(allow_null=True)
    simulated = serializers.BooleanField()


class ClientQuoteHistorySerializer(serializers.Serializer):
    project_id = serializers.UUIDField()
    project_code = serializers.CharField()
    project_name = serializers.CharField()
    version_id = serializers.UUIDField()
    revision_code = serializers.CharField()
    emitted_at = serializers.DateTimeField()
    currency = serializers.CharField(allow_null=True)
    total = serializers.CharField(allow_null=True)
    agreement_status = serializers.CharField(allow_null=True)
    selected = serializers.BooleanField()


class ClientDocumentSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    kind = serializers.ChoiceField(choices=("QUOTE", "INVOICE", "RECEIPT", "CREDIT_NOTE"))
    project_id = serializers.UUIDField()
    project_code = serializers.CharField()
    label = serializers.CharField()
    revision_code = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()


class ClientBalanceSerializer(serializers.Serializer):
    currency = serializers.CharField()
    total = serializers.CharField()
    collected = serializers.CharField()
    balance = serializers.CharField()
    simulated_collected = serializers.CharField()
    projects = serializers.IntegerField()


class ClientPaymentHistorySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    project_id = serializers.UUIDField()
    project_code = serializers.CharField()
    receipt_code = serializers.CharField(allow_null=True)
    amount = serializers.CharField()
    currency = serializers.CharField(allow_null=True)
    kind = serializers.CharField()
    method = serializers.CharField()
    recorded_at = serializers.DateTimeField()
    voided_at = serializers.DateTimeField(allow_null=True)
    simulated = serializers.BooleanField()


# Compose dossier, directory and merge preview responses with the existing
# ClientResponseSerializer after its contact/address extensions are installed.
