"""Exact workshop policy transport; costs never arrive from the browser."""

from decimal import Decimal

from rest_framework import serializers

from dekopen_engine.commercial import PricingError
from pricing.serializers import StrictSerializer, fraction, money
from pricing.simple_policy import engine_policy


class SimplePolicyValuesSerializer(StrictSerializer):
    currency = serializers.ChoiceField(choices=['CLP', 'USD'])
    labor_rate = money()
    labor_basis = serializers.ChoiceField(choices=['M2', 'WINDOW'])
    installation_rate = money()
    installation_basis = serializers.ChoiceField(choices=['M2', 'WINDOW'])
    margin = serializers.DecimalField(max_digits=6, decimal_places=4,
        min_value=Decimal('0'), max_value=Decimal('.9999'))
    rounding_step = money()
    waste = fraction()
    tax_rate = fraction()
    use_advanced = serializers.BooleanField()

    def validate(self, attrs):
        try:
            engine_policy(attrs)
        except PricingError as error:
            raise serializers.ValidationError('Revisa las unidades, el margen y el redondeo de la moneda.') from error
        return attrs


class SimplePolicyResponseSerializer(SimplePolicyValuesSerializer):
    revision = serializers.IntegerField(min_value=0)
    updated_at = serializers.DateTimeField(allow_null=True)
    saved = serializers.BooleanField()
    suggested_fields = serializers.ListField(child=serializers.CharField())


class SimplePolicyWriteSerializer(StrictSerializer):
    values = SimplePolicyValuesSerializer()
    expected_revision = serializers.IntegerField(min_value=0)
    reason = serializers.CharField(max_length=1000, allow_blank=False)


class SimplePolicyExampleRequestSerializer(StrictSerializer):
    values = SimplePolicyValuesSerializer()
    position_id = serializers.UUIDField(required=False)


class PlainAmountField(serializers.CharField):
    """Exact engine decimals in the UI's plain-decimal contract, including 0E-80."""

    def to_representation(self, value):
        return format(Decimal(str(value)), 'f')


class SimplePriceBreakdownSerializer(serializers.Serializer):
    materials = PlainAmountField()
    waste = PlainAmountField()
    labor = PlainAmountField()
    installation = PlainAmountField()
    direct_cost = PlainAmountField()
    exact_unit_price = PlainAmountField()
    unit_net = PlainAmountField()
    rounding = PlainAmountField()
    profit = PlainAmountField()
    extras_cost = PlainAmountField()
    extras_net = PlainAmountField()


class SimplePolicyExampleResponseSerializer(serializers.Serializer):
    position_id = serializers.UUIDField(allow_null=True)
    position_index = serializers.IntegerField(allow_null=True)
    currency = serializers.ChoiceField(choices=['CLP', 'USD'])
    breakdown = SimplePriceBreakdownSerializer(allow_null=True)
    project_net = PlainAmountField(allow_null=True)
    project_tax = PlainAmountField(allow_null=True)
    project_gross = PlainAmountField(allow_null=True)
    assumptions = serializers.JSONField()
    detail = serializers.CharField()


class WorkingPriceErrorSerializer(serializers.Serializer):
    code = serializers.CharField()
    detail = serializers.CharField()


class WorkingPriceLineSerializer(serializers.Serializer):
    position_index = serializers.IntegerField()
    quantity = serializers.IntegerField()
    unit_price = PlainAmountField()
    discount_pct = PlainAmountField()
    line_net = PlainAmountField()
    breakdown = SimplePriceBreakdownSerializer(required=False, allow_null=True)
    catalog_use = serializers.JSONField(required=False, allow_null=True)


class WorkingPriceSerializer(serializers.Serializer):
    use_advanced = serializers.BooleanField()
    policy = SimplePolicyResponseSerializer(required=False)
    state = serializers.ChoiceField(choices=['READY', 'BLOCKED', 'PENDING'])
    currency = serializers.ChoiceField(choices=['CLP', 'USD'])
    policy_revision = serializers.IntegerField()
    computed_at = serializers.DateTimeField()
    error = WorkingPriceErrorSerializer(allow_null=True)
    project_net = PlainAmountField(allow_null=True)
    project_tax = PlainAmountField(allow_null=True)
    project_gross = PlainAmountField(allow_null=True)
    lines = WorkingPriceLineSerializer(many=True)
