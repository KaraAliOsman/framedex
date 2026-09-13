"""Explicit monetary strings and typed S09 input/output schemas."""

from decimal import Decimal
import json

from rest_framework import serializers

from dekopen_engine.commercial import PricingMode
from engine_api.serializers import EngineCalculateRequestSerializer

MODES = [mode.value for mode in PricingMode]


def money(**kwargs):
    return serializers.DecimalField(max_digits=14, decimal_places=4, min_value=Decimal('0'), **kwargs)


def fraction(**kwargs):
    return serializers.DecimalField(max_digits=6,decimal_places=4,min_value=Decimal('0'),max_value=Decimal('1'),**kwargs)


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data,dict) or set(data)-set(self.fields):
            raise serializers.ValidationError('Unknown input fields')
        return super().to_internal_value(data)


class CostListSerializer(StrictSerializer):
    supplier_name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False,allow_blank=True)
    currency = serializers.ChoiceField(choices=['CLP','USD'])
    valid_from = serializers.DateField()
    valid_to = serializers.DateField(required=False,allow_null=True)
    is_active = serializers.BooleanField(default=True)


class CostItemSerializer(StrictSerializer):
    cost_list_id = serializers.UUIDField()
    sku = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False,allow_blank=True,max_length=1000)
    item_type = serializers.CharField(max_length=50)
    unit = serializers.ChoiceField(choices=['BAR','M','M2','KIT','UNIT'])
    unit_cost = serializers.DecimalField(max_digits=14,decimal_places=4,min_value=Decimal('0'))


class RulesSerializer(StrictSerializer):
    pricing_mode = serializers.ChoiceField(choices=MODES)
    default_margin_pct = fraction()
    tax_rate_pct = fraction()
    waste_factor_pct = serializers.DecimalField(max_digits=6,decimal_places=4,
        min_value=Decimal('0.08'),max_value=Decimal('0.08'))
    labor_rate_per_m2 = serializers.DecimalField(max_digits=14,decimal_places=2,min_value=Decimal('0'))
    installation_rate_per_m2 = serializers.DecimalField(max_digits=14,decimal_places=2,min_value=Decimal('0'))


class ConfigurationSerializer(StrictSerializer):
    context_code = serializers.CharField(max_length=100)
    typology = serializers.CharField(max_length=50)
    pricing_mode = serializers.ChoiceField(choices=MODES)
    currency = serializers.ChoiceField(choices=['CLP','USD'])
    rate_per_m2 = money(required=False,allow_null=True)
    base_glass_sku = serializers.CharField(max_length=100,required=False,allow_null=True)
    catalog_price = money(required=False,allow_null=True)
    is_active = serializers.BooleanField(default=True)


class MatrixCellSerializer(StrictSerializer):
    configuration_id = serializers.UUIDField()
    width_mm = serializers.IntegerField(min_value=600,max_value=2400)
    height_mm = serializers.IntegerField(min_value=600,max_value=2400)
    price = money()


class FxSerializer(StrictSerializer):
    base_currency = serializers.ChoiceField(choices=['USD'])
    quote_currency = serializers.ChoiceField(choices=['CLP'])
    observed_rate = serializers.DecimalField(max_digits=20,decimal_places=8,min_value=Decimal('0.00000001'))
    observed_date = serializers.DateField()
    effective_date = serializers.DateField()
    source = serializers.CharField(max_length=300)


class AdminWriteSerializer(StrictSerializer):
    id = serializers.UUIDField(required=False)
    reason = serializers.CharField(max_length=1000)
    values = serializers.DictField()


class AdminResponseSerializer(serializers.Serializer):
    items = serializers.ListField(child=serializers.DictField())


class PriceRequestSerializer(StrictSerializer):
    project_id = serializers.UUIDField()
    pricing_mode = serializers.ChoiceField(choices=MODES)
    context_code = serializers.CharField(default='DEFAULT',max_length=100)
    currency = serializers.ChoiceField(choices=['CLP','USD'])
    effective_date = serializers.DateField()
    fx_snapshot_id = serializers.UUIDField(required=False,allow_null=True)
    discount_pct = fraction(default=Decimal('0'))
    target_margin = fraction(default=Decimal('0.35'))
    segment = serializers.ChoiceField(choices=['RETAIL','ARCHITECT','CONSTRUCTION'],default='RETAIL')
    confirmed = serializers.BooleanField(default=False)
    reason = serializers.CharField(max_length=1000)


class ApplySerializer(StrictSerializer):
    reason = serializers.CharField(max_length=1000)
    confirmed = serializers.BooleanField(default=False)
    reject = serializers.BooleanField(default=False)


class LineResponseSerializer(serializers.Serializer):
    position_index = serializers.IntegerField()
    line_net = serializers.CharField()


class PriceResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    project_id = serializers.UUIDField()
    discount_pct = serializers.CharField()
    state = serializers.ChoiceField(choices=['PREVIEW','PENDING','APPLIED','REJECTED'])
    currency = serializers.ChoiceField(choices=['CLP','USD'])
    lines = LineResponseSerializer(many=True)
    project_net = serializers.CharField()
    project_tax = serializers.CharField()
    project_gross = serializers.CharField()


class DraftPositionSerializer(EngineCalculateRequestSerializer):
    position_index = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)
    typology = serializers.CharField(max_length=50)


class DraftProjectSerializer(StrictSerializer):
    code = serializers.CharField(max_length=50)
    name = serializers.CharField(max_length=255)
    client_name = serializers.CharField(max_length=255)
    reason = serializers.CharField(max_length=1000)
    positions = DraftPositionSerializer(many=True,allow_empty=False)


class DraftResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()


class ImportRequestSerializer(StrictSerializer):
    file = serializers.FileField()
    mapping = serializers.CharField(help_text='JSON object mapping sku, description, unit and unit_cost to column names.')
    decimal_separator = serializers.ChoiceField(choices=['.',','],default='.')
    cost_list_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=1000)
    apply = serializers.BooleanField(default=False)

    def validate_mapping(self, value):
        try:
            mapping = json.loads(value)
        except (TypeError, ValueError) as error:
            raise serializers.ValidationError('Invalid mapping') from error
        if not isinstance(mapping, dict):
            raise serializers.ValidationError('Invalid mapping')
        return mapping


RESOURCE_SERIALIZERS = {
    'cost-lists':CostListSerializer,'cost-items':CostItemSerializer,'rules':RulesSerializer,
    'configurations':ConfigurationSerializer,'matrix-cells':MatrixCellSerializer,'fx':FxSerializer,
}
