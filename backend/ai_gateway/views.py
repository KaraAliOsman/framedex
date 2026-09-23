"""AI gateway HTTP edge — the only entry point for provider calls (PRD-13)."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_gateway import service
from ai_gateway.providers import ProviderError
from ai_gateway.serializers import AiInvokeRequestSerializer, AiInvokeResponseSerializer
from authentication.errors import contract_error
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from documents.views import ERRORS, documentary_scope, validate

_CALLERS = ("OWNER", "ESTIMATOR")


class AiInvokeView(APIView):
    @extend_schema(
        operation_id="ai_invoke",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=AiInvokeRequestSerializer,
        responses={200: AiInvokeResponseSerializer, **ERRORS},
        tags=["ai"],
    )
    def post(self, request):
        data = validate(AiInvokeRequestSerializer, request.data)
        with documentary_scope(request, _CALLERS) as (token, _, org_id):
            try:
                return Response(
                    service.invoke(
                        org_id=org_id,
                        user_id=token.user_id,
                        capability=str(data["capability"]),
                        input_payload=dict(data["input_payload"]),
                        tool_name=str(data.get("tool_name") or "") or None,
                    )
                )
            except ProviderError as error:
                raise contract_error(
                    503,
                    error.code,
                    "El proveedor de IA no está disponible en este momento.",
                ) from None
