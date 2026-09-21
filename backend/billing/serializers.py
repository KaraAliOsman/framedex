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


class CreditLotSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    grant_id = serializers.UUIDField()
    origin = serializers.ChoiceField(choices=['trial', 'monthly', 'pack', 'legacy'])
    remaining = serializers.IntegerField(min_value=0)
    expires_at = serializers.DateTimeField(allow_null=True)


class WalletSerializer(serializers.Serializer):
    plan = serializers.CharField()
    balance = serializers.IntegerField(min_value=0)
    trial_ends_at = serializers.DateTimeField(allow_null=True)
    billing_cycle = serializers.CharField()
    ai_available = serializers.BooleanField()
    ledger = LedgerSerializer(many=True)
    lots = CreditLotSerializer(many=True)


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


class OfferSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    product_code = serializers.CharField()
    kind = serializers.CharField()
    plan_tier = serializers.CharField(allow_null=True)
    billing_cycle = serializers.CharField(allow_null=True)
    credits = serializers.IntegerField()
    amount = serializers.CharField()
    fx_source = serializers.CharField()
    fx_observed_on = serializers.DateField()


class CheckoutInputSerializer(serializers.Serializer):
    operation_key = serializers.UUIDField()
    offer_id = serializers.UUIDField()


class CheckoutResultSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    operation_key = serializers.UUIDField()
    state = serializers.CharField()
    redirect_url = serializers.URLField(allow_null=True)


class CheckoutRecordSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    operation_key = serializers.UUIDField()
    offer_id = serializers.UUIDField()
    product_code = serializers.CharField()
    created_at = serializers.DateTimeField()


class ChangeResultSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    state = serializers.CharField()
    kind = serializers.CharField()
    effective_at = serializers.DateTimeField(allow_null=True)
    amount = serializers.CharField(allow_null=True)
    currency = serializers.CharField()
    product_code = serializers.CharField(allow_null=True)


class CommerceSerializer(serializers.Serializer):
    offers = OfferSerializer(many=True)
    checkouts = CheckoutRecordSerializer(many=True)
    registration_state = serializers.CharField(allow_null=True)
    pending_change = ChangeResultSerializer(allow_null=True)
    scheduled_changes = ChangeResultSerializer(many=True)
    reconciliation_required = serializers.BooleanField()


class ChangeInputSerializer(serializers.Serializer):
    operation_key = serializers.UUIDField()
    offer_id = serializers.UUIDField(required=False)
    cancel = serializers.BooleanField(default=False)


class ConfirmChangeSerializer(serializers.Serializer):
    operation_id = serializers.UUIDField()
