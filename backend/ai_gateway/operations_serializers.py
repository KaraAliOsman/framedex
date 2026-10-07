from rest_framework import serializers
from decimal import Decimal

from ai_gateway.configuration import PROVIDERS
from ai_gateway.usage import CAPABILITIES
from pricing.serializers import StrictSerializer


class AiRouteSettingsSerializer(StrictSerializer):
    capability = serializers.ChoiceField(choices=CAPABILITIES)
    provider = serializers.ChoiceField(choices=PROVIDERS)
    provider_model = serializers.RegexField(r"^[A-Za-z0-9._/:+\-]{1,120}$")
    timeout_s = serializers.IntegerField(min_value=1, max_value=180)
    retries = serializers.IntegerField(min_value=0, max_value=2)
    tools_mode = serializers.ChoiceField(choices=("AUTO", "NATIVE", "JSON"))
    input_usd_per_million = serializers.DecimalField(max_digits=18, decimal_places=8, min_value=Decimal(0), max_value=Decimal(1000000), allow_null=True)
    output_usd_per_million = serializers.DecimalField(max_digits=18, decimal_places=8, min_value=Decimal(0), max_value=Decimal(1000000), allow_null=True)

    def validate(self, data):
        if (data["input_usd_per_million"] is None) != (data["output_usd_per_million"] is None):
            raise serializers.ValidationError("Declara ambas tarifas o deja ambas sin dato.")
        return data


class AiSettingsSaveSerializer(StrictSerializer):
    expected_revision = serializers.IntegerField(min_value=1)
    monthly_budget_credits = serializers.IntegerField(min_value=0, max_value=2147483647, allow_null=True)
    routes = AiRouteSettingsSerializer(many=True, min_length=4, max_length=4)

    def validate_routes(self, value):
        if {route["capability"] for route in value} != set(CAPABILITIES):
            raise serializers.ValidationError("Configura las cuatro capacidades una sola vez.")
        return value


class AiRouteStatusSerializer(AiRouteSettingsSerializer):
    credits_cost = serializers.IntegerField()
    credential_configured = serializers.BooleanField()
    test_mode = serializers.BooleanField()
    state = serializers.ChoiceField(choices=("UNTESTED", "CONNECTED", "ERROR", "MISSING_CREDENTIAL"))
    last_cause = serializers.CharField(allow_null=True)
    checked_at = serializers.CharField(allow_null=True)


class AiUsageTotalsSerializer(serializers.Serializer):
    calls = serializers.IntegerField()
    tokens_prompt = serializers.IntegerField(allow_null=True)
    tokens_completion = serializers.IntegerField(allow_null=True)
    capacity_credits = serializers.IntegerField()
    estimated_cost_usd = serializers.CharField(allow_null=True)


class AiUserUsageSerializer(AiUsageTotalsSerializer):
    user_id = serializers.UUIDField()
    user_label = serializers.CharField(required=False, allow_null=True)


class AiMonthlyUsageSerializer(AiUsageTotalsSerializer):
    credits_debited = serializers.IntegerField()
    monthly_budget_credits = serializers.IntegerField(allow_null=True)
    budget_blocked = serializers.BooleanField()
    budget_notice_at = serializers.CharField(allow_null=True)
    month_start = serializers.CharField()
    users = AiUserUsageSerializer(many=True)


class AiSettingsSerializer(serializers.Serializer):
    revision = serializers.IntegerField()
    routes = AiRouteStatusSerializer(many=True)
    mock_available = serializers.BooleanField()
    usage = AiMonthlyUsageSerializer()


class AiModeSerializer(serializers.Serializer):
    test_mode = serializers.BooleanField()


class AiConnectionTestSerializer(StrictSerializer):
    operation_key = serializers.CharField(min_length=8, max_length=120)


class AiConnectionResultSerializer(serializers.Serializer):
    passed = serializers.BooleanField()
    case_id = serializers.CharField()
    test_mode = serializers.BooleanField()
    tokens_prompt = serializers.IntegerField()
    tokens_completion = serializers.IntegerField()
    credits_debited = serializers.IntegerField()
    latency_ms = serializers.IntegerField()


class AiUsageQuerySerializer(StrictSerializer):
    capability = serializers.CharField(max_length=100, required=False)
    state = serializers.ChoiceField(choices=("QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELED"), required=False)
    limit = serializers.IntegerField(min_value=1, max_value=100, default=50)
    offset = serializers.IntegerField(min_value=0, max_value=100000, default=0)


class AiUsageWorkSerializer(AiUsageTotalsSerializer):
    id = serializers.UUIDField()
    job_id = serializers.UUIDField(allow_null=True)
    ai_job_id = serializers.UUIDField(allow_null=True)
    capability = serializers.CharField()
    user_id = serializers.UUIDField()
    user_label = serializers.CharField(allow_null=True)
    status = serializers.CharField()
    job_state = serializers.CharField(allow_null=True)
    test_mode = serializers.BooleanField()
    latency_ms = serializers.IntegerField(allow_null=True)
    retries = serializers.IntegerField()
    fallback = serializers.BooleanField()
    tools = serializers.ListField(child=serializers.CharField())
    trace = serializers.ListField(child=serializers.DictField(child=serializers.CharField()))
    last_cause = serializers.CharField(allow_null=True)
    created_at = serializers.CharField()
