from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_gateway import configuration, usage
from ai_gateway.operations_serializers import (
    AiSettingsSerializer, AiSettingsSaveSerializer, AiConnectionTestSerializer,
    AiConnectionResultSerializer, AiUsageQuerySerializer, AiUsageWorkSerializer, AiModeSerializer,
)
from ai_gateway.providers import ProviderError
from authentication.errors import contract_error
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from documents.views import documentary_scope, validate, ERRORS


class AiSettingsView(APIView):
    @extend_schema(operation_id="ai_settings_get", parameters=[ACTIVE_ORGANIZATION_HEADER], responses={200: AiSettingsSerializer, **ERRORS}, tags=["ai"])
    def get(self, request):
        with documentary_scope(request, ("OWNER",)) as (_, _, org_id):
            return Response(AiSettingsSerializer(configuration.get(org_id)).data)

    @extend_schema(operation_id="ai_settings_save", parameters=[ACTIVE_ORGANIZATION_HEADER], request=AiSettingsSaveSerializer, responses={200: AiSettingsSerializer, **ERRORS}, tags=["ai"])
    def put(self, request):
        data = validate(AiSettingsSaveSerializer, request.data)
        with documentary_scope(request, ("OWNER",)) as (token, _, org_id):
            return Response(AiSettingsSerializer(configuration.save(org_id, token.user_id, data)).data)


class AiModeView(APIView):
    @extend_schema(operation_id="ai_mode_get", parameters=[ACTIVE_ORGANIZATION_HEADER], responses={200: AiModeSerializer, **ERRORS}, tags=["ai"])
    def get(self, request):
        from ai_gateway.service import _route
        from ai_gateway.providers import _mock_enabled
        from billing.wallet import financial_transaction
        with documentary_scope(request, ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")) as (_, _, org_id):
            with financial_transaction(org_id):
                routes = [_route(capability, org_id) for capability in usage.CAPABILITIES]
            return Response({"test_mode": _mock_enabled() and any(route and route["provider"] == "MOCK" for route in routes)})


class AiConnectionView(APIView):
    @extend_schema(operation_id="ai_connection_test", parameters=[ACTIVE_ORGANIZATION_HEADER], request=AiConnectionTestSerializer, responses={200: AiConnectionResultSerializer, **ERRORS}, tags=["ai"])
    def post(self, request):
        data = validate(AiConnectionTestSerializer, request.data)
        with documentary_scope(request, ("OWNER",)) as (token, _, org_id):
            try:
                result = configuration.probe(org_id, token.user_id, data)
            except ProviderError as error:
                raise contract_error(503, error.code, configuration.cause(error.code)) from None
            return Response(AiConnectionResultSerializer(result).data)


class AiUsageView(APIView):
    @extend_schema(operation_id="ai_usage_list", parameters=[ACTIVE_ORGANIZATION_HEADER,
                   OpenApiParameter("capability", OpenApiTypes.STR, OpenApiParameter.QUERY),
                   OpenApiParameter("state", OpenApiTypes.STR, OpenApiParameter.QUERY),
                   OpenApiParameter("limit", OpenApiTypes.INT, OpenApiParameter.QUERY),
                   OpenApiParameter("offset", OpenApiTypes.INT, OpenApiParameter.QUERY)],
                   responses={200: AiUsageWorkSerializer(many=True), **ERRORS}, tags=["ai"])
    def get(self, request):
        data = validate(AiUsageQuerySerializer, request.query_params)
        with documentary_scope(request, ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")) as (token, tenant, org_id):
            actor = None if tenant.active_organization.role == "OWNER" else token.user_id
            result = usage.list_work(org_id, actor, **data)
            return Response(AiUsageWorkSerializer(result, many=True).data)
