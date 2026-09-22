"""Read-only technical choices for the manual estimator, without cost information."""

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.views import APIView

from engine_api.repository import SystemParamsRepository
from pricing.repository import rows
from pricing.views import ERRORS, scope
from projects.views import READ_ROLES, SCHEMA, response


class ProfileChoiceSerializer(serializers.Serializer):
    sku = serializers.CharField()
    role = serializers.CharField()


class KitChoiceSerializer(serializers.Serializer):
    sku = serializers.CharField()
    name = serializers.CharField()
    opening_type = serializers.CharField()


class DesignOptionsSerializer(serializers.Serializer):
    profiles = ProfileChoiceSerializer(many=True)
    glazing_thicknesses = serializers.ListField(child=serializers.CharField())
    hardware_kits = KitChoiceSerializer(many=True)
    glass_skus = serializers.ListField(child=serializers.CharField())
    colors = serializers.ListField(child=serializers.CharField())
    coupler_skus = serializers.ListField(child=serializers.CharField())


class DesignOptionsView(APIView):
    @extend_schema(
        operation_id="project_design_options",
        responses={200: DesignOptionsSerializer, **ERRORS},
        **SCHEMA,
    )
    def get(self, request, system_id):
        with scope(request, READ_ROLES) as (_, _, org):
            repository = SystemParamsRepository()
            params = repository.load_visible(system_id, org)
            glass_rows = rows(
                "SELECT DISTINCT technical_sku FROM public.glass_purchase_mappings "
                "WHERE system_id=%s AND (org_id=%s OR org_id IS NULL) ORDER BY technical_sku",
                [system_id, org],
            )
            return response(
                {
                    "profiles": [
                        {"sku": item.sku, "role": item.role.value}
                        for item in params.effective_profile_articles.values()
                    ],
                    "glazing_thicknesses": [
                        str(value) for value in sorted(params.glazing_bead_rules)
                    ],
                    "hardware_kits": [
                        {"sku": item.sku, "name": item.name, "opening_type": item.opening_type}
                        for item in params.available_hardware_kits
                    ],
                    "glass_skus": [item["technical_sku"] for item in glass_rows],
                    "colors": ["WHITE"],
                    "coupler_skus": sorted(
                        repository.load_coupler_articles(system_id, org)
                    ),
                }
            )
