from rest_framework import serializers
from decimal import Decimal


class AnalyticsPeriodSerializer(serializers.Serializer):
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)


class AnalyticsPreferenceSerializer(serializers.Serializer):
    period_days = serializers.IntegerField(min_value=1, max_value=366)


class AnalyticsDetailSerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField(allow_blank=True)
    href = serializers.CharField()
    value = serializers.CharField(allow_null=True)
    unit = serializers.CharField()
    currency = serializers.CharField(allow_null=True)
    reason = serializers.CharField(allow_null=True)


class AnalyticsMetricSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    group = serializers.CharField()
    value = serializers.CharField(allow_null=True)
    unit = serializers.CharField()
    currency = serializers.CharField(allow_null=True)
    reason = serializers.CharField(allow_null=True)
    formula = serializers.CharField()
    source = serializers.CharField()
    definition = serializers.CharField()
    missing = serializers.IntegerField()
    details = AnalyticsDetailSerializer(many=True)


class AnalyticsWorkspaceSerializer(serializers.Serializer):
    start = serializers.DateField()
    end = serializers.DateField()
    as_of = serializers.DateTimeField()
    metrics = AnalyticsMetricSerializer(many=True)
    works = serializers.ListField(child=serializers.DictField())
    source = serializers.CharField()
    empty = serializers.BooleanField()


def decimal_input():
    return serializers.DecimalField(
        max_digits=32,
        decimal_places=8,
        allow_null=True,
        min_value=Decimal(0),
        coerce_to_string=True,
    )


class MaterialActualSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    unit_cost = decimal_input()
    waste_quantity = decimal_input()


class LaborActualSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    hours = decimal_input()
    hourly_rate = decimal_input()


class BarActualSerializer(serializers.Serializer):
    complete = serializers.BooleanField(default=False)
    input_mm = decimal_input()
    productive_mm = decimal_input()
    waste_mm = decimal_input()
    reusable_mm = decimal_input()


class ActualReportRequestSerializer(serializers.Serializer):
    request_key = serializers.UUIDField()
    expected_revision = serializers.IntegerField(min_value=0)
    source_fingerprint = serializers.RegexField(r"^[0-9a-f]{64}$")
    currency = serializers.ChoiceField(choices=["CLP", "USD", "UF"])
    source = serializers.CharField(min_length=3, max_length=1000)
    reason = serializers.CharField(min_length=3, max_length=1000)
    materials = MaterialActualSerializer(many=True)
    labor = LaborActualSerializer(many=True)
    other_cost = decimal_input()
    reusable_credit = decimal_input()
    closed = serializers.BooleanField()
    bars = BarActualSerializer()
    confirmed = serializers.BooleanField(default=False)


class ActualReportResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    code = serializers.CharField()
    project_id = serializers.UUIDField()
    status = serializers.CharField()
    currency = serializers.CharField(allow_null=True)
    revision = serializers.IntegerField()
    source_fingerprint = serializers.CharField()
    source = serializers.CharField(allow_blank=True)
    reason = serializers.CharField(allow_blank=True)
    materials = serializers.ListField(child=serializers.DictField())
    labor = serializers.ListField(child=serializers.DictField())
    produced = serializers.ListField(child=serializers.DictField())
    other_cost = serializers.CharField(allow_null=True)
    reusable_credit = serializers.CharField(allow_null=True)
    closed = serializers.BooleanField()
    bars = serializers.DictField()
    result = serializers.DictField()
    previous_result = serializers.DictField(required=False)
