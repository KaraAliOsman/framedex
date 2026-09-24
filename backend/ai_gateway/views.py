"""AI gateway HTTP edge — the only entry point for provider calls (PRD-13)."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_gateway import service
from ai_gateway.agent import act
from ai_gateway.assist import ask
from ai_gateway.context import _ContextError
from ai_gateway.providers import ProviderError
from ai_gateway.serializers import (
    AiAgentRequestSerializer,
    AiAgentResponseSerializer,
    AiAskRequestSerializer,
    AiAskResponseSerializer,
    AiInvokeRequestSerializer,
    AiInvokeResponseSerializer,
)
from ai_gateway.context import REQUIRED_REFS as AGENT_REQUIRED_REFS
from authentication.errors import contract_error
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from documents.views import ERRORS, documentary_scope, validate

_CALLERS = ("OWNER", "ESTIMATOR")
_AGENT_CALLERS = ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")


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
                        operation_key=str(data["operation_key"]),
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


class AiAskView(APIView):
    """Contextual "Preguntar a DEKOPEN" — the question and surface come from
    the client; every fact in the context is queried server-side under the
    caller's RLS. The provider answers inside that projection only."""

    @extend_schema(
        operation_id="ai_ask",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=AiAskRequestSerializer,
        responses={200: AiAskResponseSerializer, **ERRORS},
        tags=["ai"],
    )
    def post(self, request):
        data = validate(AiAskRequestSerializer, request.data)
        with documentary_scope(request, _CALLERS) as (token, _, org_id):
            try:
                return Response(
                    ask(
                        org_id=org_id,
                        user_id=token.user_id,
                        surface=str(data["surface"]),
                        refs=dict(data.get("refs") or {}),
                        question=str(data["question"]),
                        operation_key=str(data["operation_key"]),
                    )
                )
            except ProviderError as error:
                raise contract_error(
                    503,
                    error.code,
                    "El proveedor de IA no está disponible en este momento.",
                ) from None


class AiAgentView(APIView):
    """The agent surface: a goal becomes a bounded observe → plan → propose
    loop. Queries run server-side inside typed projections; every emitted
    step is validated before it reaches the client, and nothing consequential
    executes without the human clicking on the real surface."""

    @extend_schema(
        operation_id="ai_agent",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=AiAgentRequestSerializer,
        responses={200: AiAgentResponseSerializer, **ERRORS},
        tags=["ai"],
    )
    def post(self, request):
        data = validate(AiAgentRequestSerializer, request.data)
        # The agent only reads projections and proposes steps — the workshop
        # manager's surface needs it as much as the estimator's.
        with documentary_scope(request, _AGENT_CALLERS) as (token, _, org_id):
            surface = str(data["surface"])
            refs = dict(data.get("refs") or {})
            missing_refs = [
                name
                for name in AGENT_REQUIRED_REFS.get(surface, ())
                if name not in refs
            ]
            if missing_refs:
                raise contract_error(
                    400,
                    "ai_context_ref_required",
                    f"Esta superficie requiere la referencia '{missing_refs[0]}'.",
                )
            try:
                return Response(
                    act(
                        org_id=org_id,
                        user_id=token.user_id,
                        surface=surface,
                        refs=refs,
                        goal=str(data["goal"]),
                        product=data.get("product"),
                        history=list(data.get("history") or []),
                        operation_key=str(data["operation_key"]),
                    )
                )
            except _ContextError as error:
                if error.code == "ai_context_ref_invalid":
                    raise contract_error(
                        400,
                        "ai_context_ref_invalid",
                        "La referencia de contexto no es válida.",
                    ) from None
                raise contract_error(
                    404,
                    "ai_context_not_found",
                    "El contexto solicitado no existe o no está disponible.",
                ) from None
            except ProviderError as error:
                raise contract_error(
                    503,
                    error.code,
                    "El proveedor de IA no está disponible en este momento.",
                ) from None
