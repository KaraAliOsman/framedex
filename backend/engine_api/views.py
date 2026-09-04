"""Tenant-bound HTTP endpoint delegating all mathematics to /engine."""

from __future__ import annotations

from typing import cast

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.errors import contract_error
from authentication.rls import authenticated_rls_context
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER, ErrorResponseSerializer
from authentication.tenancy import (
    MembershipRepository,
    enforce_owner_mfa,
    resolve_tenant_context,
)
from authentication.views import verified_request_token
from engine_api.adapter import (
    InvalidEngineRequest,
    UnsupportedEngineContract,
    calculate_from_api,
)
from engine_api.repository import (
    SystemNotFound,
    SystemParamsRepository,
    UnsupportedCatalogContract,
)
from engine_api.serializers import (
    EngineCalculateRequestSerializer,
    EngineCalculateResponseSerializer,
)


class EngineCalculateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="engine_calculate",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=EngineCalculateRequestSerializer,
        responses={
            200: EngineCalculateResponseSerializer,
            400: OpenApiResponse(ErrorResponseSerializer),
            401: OpenApiResponse(ErrorResponseSerializer),
            403: OpenApiResponse(ErrorResponseSerializer),
            404: OpenApiResponse(ErrorResponseSerializer),
            409: OpenApiResponse(ErrorResponseSerializer),
            422: OpenApiResponse(ErrorResponseSerializer),
        },
        tags=["engine"],
    )
    def post(self, request: Request) -> Response:
        request_serializer = EngineCalculateRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise contract_error(
                status.HTTP_400_BAD_REQUEST,
                "validation_error",
                "Request validation failed",
            )
        data = request_serializer.validated_data
        token = verified_request_token(request)

        try:
            with authenticated_rls_context(token.claims):
                memberships = MembershipRepository().list_active_for_user(token.user_id)
                tenant = resolve_tenant_context(
                    memberships,
                    request.headers.get("X-Organization-ID"),
                )
                enforce_owner_mfa(tenant, token.aal)
                params = SystemParamsRepository().load_visible(
                    data["system_id"], tenant.active_organization.organization_id
                )
                result = calculate_from_api(
                    parametric_tree=data["parametric_tree"],
                    nominal_width_mm=data["nominal_width_mm"],
                    nominal_height_mm=data["nominal_height_mm"],
                    color=data["color"],
                    params=params,
                )
        except SystemNotFound as error:
            raise contract_error(
                status.HTTP_404_NOT_FOUND,
                "system_not_found",
                "Profile system does not exist or is not visible",
            ) from error
        except (UnsupportedEngineContract, UnsupportedCatalogContract) as error:
            raise contract_error(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "unsupported_engine_contract",
                "Engine contract is not supported in SHOT-04",
            ) from error
        except InvalidEngineRequest as error:
            raise contract_error(
                status.HTTP_400_BAD_REQUEST,
                "validation_error",
                "Request validation failed",
            ) from error

        response_payload = cast(dict[str, object], result.model_dump(mode="json"))
        return Response(response_payload, status=status.HTTP_200_OK)
