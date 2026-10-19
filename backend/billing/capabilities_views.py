from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.views import APIView

from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from billing import capabilities as resolver
from pricing.views import ERRORS, scope
from projects.views import response

MEMBER_ROLES = ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER", "OPERATOR", "INSTALLER")


class CapabilitySerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    supported = serializers.BooleanField()
    permitted = serializers.BooleanField()
    available = serializers.BooleanField()
    reason_code = serializers.ChoiceField(choices=list(resolver.REASONS))
    reason = serializers.CharField()
    credits_per_exchange = serializers.IntegerField(allow_null=True)


class CapabilityPlanSerializer(serializers.Serializer):
    code = serializers.CharField()
    cycle = serializers.CharField(allow_null=True)
    active = serializers.BooleanField()
    trial_ends_at = serializers.CharField(allow_null=True)


class AiEntitlementSerializer(serializers.Serializer):
    granted = serializers.BooleanField()
    origin = serializers.ChoiceField(choices=["plan", "trial", "none"])


class ServiceWindowSerializer(serializers.Serializer):
    start = serializers.CharField()
    end = serializers.CharField()
    next_grant_at = serializers.CharField(allow_null=True)
    cycle = serializers.CharField()


class CapabilityLimitsSerializer(serializers.Serializer):
    included_credits = serializers.IntegerField()
    unit = serializers.CharField()
    window_kind = serializers.CharField()
    policy_version = serializers.CharField()
    # Q = m × U only under an approved proportional policy (none active).
    unit_credits = serializers.IntegerField(allow_null=True)
    multiplier = serializers.IntegerField(allow_null=True)
    source = serializers.CharField()
    window = ServiceWindowSerializer(allow_null=True)


class PlanQuotaSerializer(serializers.Serializer):
    code = serializers.CharField()
    ai = serializers.BooleanField()
    included_credits = serializers.IntegerField()
    window_kind = serializers.CharField()


class BalanceOriginSerializer(serializers.Serializer):
    origin = serializers.CharField(allow_null=True)
    remaining = serializers.IntegerField()
    expires_at = serializers.CharField(allow_null=True)


class CapabilityBalancesSerializer(serializers.Serializer):
    by_origin = BalanceOriginSerializer(many=True)
    usable = serializers.IntegerField(allow_null=True)
    reserved = serializers.IntegerField(allow_null=True)
    spendable = serializers.IntegerField(allow_null=True)


class CapabilityBudgetSerializer(serializers.Serializer):
    monthly_limit = serializers.IntegerField(allow_null=True)
    used = serializers.IntegerField(allow_null=True)
    window_start = serializers.CharField()
    timezone = serializers.CharField()


class CapabilitiesResponseSerializer(serializers.Serializer):
    terms_version = serializers.CharField()
    quota_policy_version = serializers.CharField()
    consumption_policy_version = serializers.CharField()
    plan = CapabilityPlanSerializer()
    ai_entitlement = AiEntitlementSerializer()
    model_selection = serializers.CharField(allow_null=True)
    capabilities = CapabilitySerializer(many=True)
    extras = serializers.ListField(child=serializers.DictField())
    plans = PlanQuotaSerializer(many=True)
    limits = CapabilityLimitsSerializer()
    balances = CapabilityBalancesSerializer()
    budget = CapabilityBudgetSerializer()
    ai_available = serializers.BooleanField()
    reason_code = serializers.ChoiceField(choices=list(resolver.REASONS))
    reason = serializers.CharField()
    role = serializers.CharField()


class CapabilitiesView(APIView):
    """Pure read of the organization's AI rights, support, permission and
    availability for the active member. Never calls the provider."""

    @extend_schema(operation_id="capabilities_retrieve", tags=["billing"],
                   parameters=[ACTIVE_ORGANIZATION_HEADER],
                   responses={200: CapabilitiesResponseSerializer, **ERRORS})
    def get(self, request):
        with scope(request, MEMBER_ROLES) as (token, tenant, org):
            return response(resolver.resolve(
                org_id=org, user_id=token.user_id, role=tenant.active_organization.role))
