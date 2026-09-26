"""Contract serializers for the customer-approval portal."""

from rest_framework import serializers


class ShareQuoteResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    expires_at = serializers.DateTimeField()
    path = serializers.CharField()


class PortalOrganizationSerializer(serializers.Serializer):
    name = serializers.CharField(allow_null=True, allow_blank=True)
    tax_id = serializers.CharField(allow_null=True, allow_blank=True)


class PortalPositionSerializer(serializers.Serializer):
    id = serializers.CharField(allow_blank=True)
    position_index = serializers.IntegerField(allow_null=True)
    quantity = serializers.IntegerField(allow_null=True)
    typology = serializers.CharField(allow_null=True, allow_blank=True)
    location_tag = serializers.CharField(allow_null=True, allow_blank=True)
    width_mm = serializers.CharField(allow_blank=True)
    height_mm = serializers.CharField(allow_blank=True)
    color_interior = serializers.CharField(allow_null=True, allow_blank=True)
    color_exterior = serializers.CharField(allow_null=True, allow_blank=True)
    price_net = serializers.CharField()
    parametric_tree = serializers.JSONField(allow_null=True)


class PortalPaymentSerializer(serializers.Serializer):
    status = serializers.CharField()
    collected = serializers.CharField()
    balance = serializers.CharField()


class PortalQuoteSerializer(serializers.Serializer):
    schema = serializers.CharField()
    organization = PortalOrganizationSerializer()
    project_code = serializers.CharField()
    project_name = serializers.CharField()
    client_name = serializers.CharField()
    project_status = serializers.CharField()
    revision_code = serializers.CharField()
    emitted_at = serializers.DateTimeField()
    currency = serializers.CharField()
    payment_terms = serializers.CharField(allow_null=True, allow_blank=True)
    total_price_net = serializers.CharField()
    total_price_tax = serializers.CharField()
    total_price_gross = serializers.CharField()
    positions = PortalPositionSerializer(many=True)
    payment = PortalPaymentSerializer(allow_null=True)
    valid_until = serializers.CharField(allow_null=True)
    validity_expired = serializers.BooleanField()
    superseded = serializers.BooleanField()
    expires_at = serializers.DateTimeField()
    approval_status = serializers.CharField()
    decided_by = serializers.CharField(allow_null=True)
    decided_at = serializers.DateTimeField(allow_null=True)
    decided_note = serializers.CharField(allow_null=True)
    quote_pdf_url = serializers.CharField(allow_null=True)


class ApprovalRecordSerializer(serializers.Serializer):
    id = serializers.CharField()
    status = serializers.CharField()
    revision_code = serializers.CharField()
    decided_by = serializers.CharField(allow_null=True)
    decided_at = serializers.DateTimeField(allow_null=True)
    expires_at = serializers.DateTimeField()
    created_at = serializers.DateTimeField()


class DecideRequestSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["APPROVED", "DECLINED"])
    decided_by = serializers.CharField(max_length=255)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate_decided_by(self, value):
        trimmed = value.strip()
        if not trimmed:
            raise serializers.ValidationError("required")
        return trimmed
