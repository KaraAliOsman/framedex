"""Contract serializers for the customer-approval portal."""

from rest_framework import serializers


class ShareQuoteResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    expires_at = serializers.DateTimeField()
    path = serializers.CharField()


class PortalQuoteSerializer(serializers.Serializer):
    schema = serializers.CharField()
    project_code = serializers.CharField()
    project_name = serializers.CharField()
    client_name = serializers.CharField()
    project_status = serializers.CharField()
    revision_code = serializers.CharField()
    emitted_at = serializers.DateTimeField()
    total_price_net = serializers.CharField()
    total_price_tax = serializers.CharField()
    total_price_gross = serializers.CharField()
    valid_until = serializers.CharField(allow_null=True)
    superseded = serializers.BooleanField()
    expires_at = serializers.DateTimeField()
    approval_status = serializers.CharField()
    decided_by = serializers.CharField(allow_null=True)
    decided_at = serializers.DateTimeField(allow_null=True)
    decided_note = serializers.CharField(allow_null=True)
    quote_pdf_url = serializers.CharField(allow_null=True)


class DecideRequestSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["APPROVED", "DECLINED"])
    decided_by = serializers.CharField(max_length=255)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500)
