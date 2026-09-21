from rest_framework import serializers


class FlowConfirmationSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=512, trim_whitespace=False)


class FlowAcknowledgementSerializer(serializers.Serializer):
    received = serializers.BooleanField()


class LedgerSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    amount = serializers.IntegerField()
    balance_after = serializers.IntegerField(min_value=0)
    action_type = serializers.CharField()
    reference_id = serializers.UUIDField(allow_null=True)
    expires_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()


class WalletSerializer(serializers.Serializer):
    plan = serializers.CharField()
    balance = serializers.IntegerField(min_value=0)
    trial_ends_at = serializers.DateTimeField(allow_null=True)
    billing_cycle = serializers.CharField()
    ai_available = serializers.BooleanField()
    ledger = LedgerSerializer(many=True)


class SubscriptionSerializer(serializers.Serializer):
    plan_tier = serializers.CharField()
    billing_cycle = serializers.CharField()
    status = serializers.CharField()
    currency = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    current_period_end = serializers.DateTimeField(allow_null=True)


class PaymentSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    status = serializers.CharField()
    tax_doc_type = serializers.CharField(allow_null=True)
    tax_doc_folio = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()


class BillingSerializer(serializers.Serializer):
    plan = serializers.CharField()
    trial_ends_at = serializers.DateTimeField(allow_null=True)
    subscription = SubscriptionSerializer(allow_null=True)
    payments = PaymentSerializer(many=True)
