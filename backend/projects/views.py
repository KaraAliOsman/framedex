"""Manual project API using the existing verified JWT and RLS boundary."""

import json
from datetime import datetime

from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.parsers import FormParser
from rest_framework.permissions import AllowAny

from ai_gateway.providers import ProviderError
from authentication.errors import contract_error
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from billing.flow import FlowError
from billing.serializers import FlowAcknowledgementSerializer, FlowConfirmationSerializer
from pricing.repository import encode
from pricing.views import DecimalJSONParser, ERRORS, scope, validate
from projects import design_assist, payment_links, payments, service
from projects.serializers import (
    PaymentIntegrationSerializer,
    PaymentIntegrationStatusSerializer,
    PaymentLinkCreateSerializer,
    PaymentLinkResponseSerializer,
    PaymentLinksResponseSerializer,
    PaymentRecordResponseSerializer,
    PaymentRecordSerializer,
    PaymentsSummarySerializer,
    PaymentVoidSerializer,
    CloneProjectSerializer,
    DeletePositionSerializer,
    DesignAssistRequestSerializer,
    DesignAssistResponseSerializer,
    PositionResponseSerializer,
    PositionUpdateSerializer,
    PositionWriteSerializer,
    ProjectListResponseSerializer,
    ProjectResponseSerializer,
    ProjectUpdateSerializer,
    ProjectWriteSerializer,
    ResetPricingSerializer,
    SuccessorRequestSerializer,
)

READ_ROLES = ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")
WRITE_ROLES = ("OWNER", "ESTIMATOR")
SCHEMA = {"parameters": [ACTIVE_ORGANIZATION_HEADER], "tags": ["projects"]}


def response(value, *, status=200):
    def public_encode(item):
        return item.isoformat() if isinstance(item, datetime) else encode(item)

    return Response(
        json.loads(json.dumps(value, default=public_encode, allow_nan=False)), status=status
    )


class ProjectsView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(
        operation_id="projects_list",
        responses={200: ProjectListResponseSerializer, **ERRORS},
        **SCHEMA,
    )
    def get(self, request):
        with scope(request, READ_ROLES) as (_, _, org):
            return response({"items": service.list_projects(org)})

    @extend_schema(
        operation_id="projects_create",
        request=ProjectWriteSerializer,
        responses={201: ProjectResponseSerializer, **ERRORS},
        **SCHEMA,
    )
    def post(self, request):
        data = validate(ProjectWriteSerializer, request.data)
        with scope(request, WRITE_ROLES) as (token, _, org):
            return response(service.create_project(org, token.user_id, data), status=201)


class ProjectView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(
        operation_id="projects_retrieve",
        responses={200: ProjectResponseSerializer, **ERRORS},
        **SCHEMA,
    )
    def get(self, request, project_id):
        with scope(request, READ_ROLES) as (_, _, org):
            return response(
                service.project_public(org, service.project_row(org, project_id), detail=True)
            )

    @extend_schema(
        operation_id="projects_update",
        request=ProjectUpdateSerializer,
        responses={200: ProjectResponseSerializer, **ERRORS},
        **SCHEMA,
    )
    def patch(self, request, project_id):
        if not isinstance(request.data, dict) or "expected_updated_at" not in request.data:
            raise contract_error(400, "validation_error", "expected_updated_at es obligatorio.")
        data = validate(ProjectUpdateSerializer, request.data, partial=True)
        with scope(request, WRITE_ROLES) as (_, _, org):
            return response(service.update_project(org, project_id, data))


class ProjectPositionsView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(
        operation_id="positions_create",
        request=PositionWriteSerializer,
        responses={201: PositionResponseSerializer, **ERRORS},
        **SCHEMA,
    )
    def post(self, request, project_id):
        data = validate(PositionWriteSerializer, request.data)
        with scope(request, WRITE_ROLES) as (_, _, org):
            return response(service.save_position(org, project_id, data), status=201)


class ProjectCloneView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(
        operation_id="projects_clone",
        request=CloneProjectSerializer,
        responses={201: ProjectResponseSerializer, **ERRORS},
        **SCHEMA,
    )
    def post(self, request, project_id):
        data = validate(CloneProjectSerializer, request.data)
        with scope(request, WRITE_ROLES) as (token, _, org):
            return response(service.clone_project(org, token.user_id, project_id, data), status=201)


class ProjectSuccessorView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(
        operation_id="projects_start_successor",
        request=SuccessorRequestSerializer,
        responses={200: ProjectResponseSerializer, 201: ProjectResponseSerializer, **ERRORS},
        **SCHEMA,
    )
    def post(self, request, project_id):
        with scope(request, WRITE_ROLES) as (_, _, org):
            data = validate(SuccessorRequestSerializer, request.data)
            value = service.start_successor(
                org, project_id, data["expected_current_revision"]
            )
        created = value.pop("successor_created")
        return response(value, status=201 if created else 200)


class ProjectResetPricingView(APIView):
    @extend_schema(operation_id="projects_reset_pricing", request=ResetPricingSerializer,
                   responses={200: ProjectResponseSerializer, **ERRORS}, **SCHEMA)
    def post(self, request, project_id):
        data = validate(ResetPricingSerializer, request.data)
        with scope(request, WRITE_ROLES) as (_, _, org):
            return response(service.reset_draft_pricing(
                org, project_id, data["expected_operation_id"], data["reason"],
            ))


class PositionView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(
        operation_id="positions_retrieve",
        responses={200: PositionResponseSerializer, **ERRORS},
        **SCHEMA,
    )
    def get(self, request, position_id):
        with scope(request, READ_ROLES) as (_, _, org):
            return response(service.position_public(service.position_row(org, position_id)))

    @extend_schema(
        operation_id="positions_update",
        request=PositionUpdateSerializer,
        responses={200: PositionResponseSerializer, **ERRORS},
        **SCHEMA,
    )
    def put(self, request, position_id):
        data = validate(PositionUpdateSerializer, request.data)
        with scope(request, WRITE_ROLES) as (_, _, org):
            existing = service.position_row(org, position_id)
            return response(
                service.save_position(org, existing["project_id"], data, position_id=position_id)
            )

    @extend_schema(
        operation_id="positions_destroy",
        parameters=[
            ACTIVE_ORGANIZATION_HEADER,
            OpenApiParameter(
                "expected_updated_at",
                OpenApiTypes.DATETIME,
                OpenApiParameter.QUERY,
                required=True,
            ),
        ],
        tags=["projects"],
        responses={204: None, **ERRORS},
    )
    def delete(self, request, position_id):
        data = validate(DeletePositionSerializer, request.query_params)
        with scope(request, WRITE_ROLES) as (_, _, org):
            service.delete_position(org, position_id, data["expected_updated_at"])
        return Response(status=204)


class PositionDesignAssistView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(
        operation_id="positions_design_assist",
        request=DesignAssistRequestSerializer,
        responses={200: DesignAssistResponseSerializer, 502: ERRORS[503], **ERRORS},
        **SCHEMA,
    )
    def post(self, request, position_id):
        data = validate(DesignAssistRequestSerializer, request.data)
        with scope(request, WRITE_ROLES) as (token, _, org):
            try:
                return response(
                    design_assist.assist(
                        org_id=org,
                        user_id=token.user_id,
                        position=service.position_row(org, position_id),
                        product=data["product"],
                        prompt=str(data["prompt"]),
                        operation_key=str(data["operation_key"]),
                    )
                )
            except ProviderError as error:
                raise contract_error(
                    503,
                    error.code,
                    "El proveedor de IA no está disponible en este momento.",
                ) from None


class ProjectPaymentsView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(
        operation_id="project_payments_list",
        responses={200: PaymentsSummarySerializer, **ERRORS},
        **SCHEMA,
    )
    def get(self, request, project_id):
        with scope(request, READ_ROLES) as (_, _, org):
            return response(payments.list_payments(org_id=org, project_id=project_id))

    @extend_schema(
        operation_id="project_payments_record",
        request=PaymentRecordSerializer,
        responses={201: PaymentRecordResponseSerializer, **ERRORS},
        **SCHEMA,
    )
    def post(self, request, project_id):
        data = validate(PaymentRecordSerializer, request.data)
        with scope(request, WRITE_ROLES) as (token, _, org):
            return response(
                payments.record_payment(
                    org_id=org, project_id=project_id, actor_id=token.user_id, data=data
                ),
                status=201,
            )


class ProjectPaymentLinksView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(
        operation_id="project_payment_links_list",
        responses={200: PaymentLinksResponseSerializer, **ERRORS},
        **SCHEMA,
    )
    def get(self, request, project_id):
        with scope(request, READ_ROLES) as (_, _, org):
            return response(payment_links.list_links(org_id=org, project_id=project_id))

    @extend_schema(
        operation_id="project_payment_link_create",
        request=PaymentLinkCreateSerializer,
        responses={201: PaymentLinkResponseSerializer, **ERRORS},
        **SCHEMA,
    )
    def post(self, request, project_id):
        data = validate(PaymentLinkCreateSerializer, request.data)
        with scope(request, WRITE_ROLES) as (token, _, org):
            return response(
                payment_links.create_link(
                    org_id=org, project_id=project_id, actor_id=token.user_id, data=data
                ),
                status=201,
            )


class ProjectPaymentLinkRecoverView(APIView):
    @extend_schema(
        operation_id="project_payment_link_recover",
        request=None,
        responses={200: PaymentLinkResponseSerializer, **ERRORS},
        **SCHEMA,
    )
    def post(self, request, project_id, link_id):
        with scope(request, WRITE_ROLES) as (_, _, org):
            try:
                return response(
                    payment_links.recover_link(org_id=org, link_id=link_id)
                )
            except FlowError as error:
                raise contract_error(
                    503, error.code, "El link requiere verificación del proveedor."
                ) from None


class ProjectPaymentIntegrationView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(
        operation_id="project_payment_integration_status",
        responses={200: PaymentIntegrationStatusSerializer, **ERRORS},
        **SCHEMA,
    )
    def get(self, request):
        with scope(request, WRITE_ROLES) as (_, _, org):
            return response(payment_links.get_integration(org_id=org))

    @extend_schema(
        operation_id="project_payment_integration_save",
        request=PaymentIntegrationSerializer,
        responses={200: PaymentIntegrationStatusSerializer, **ERRORS},
        **SCHEMA,
    )
    def put(self, request):
        data = validate(PaymentIntegrationSerializer, request.data)
        with scope(request, WRITE_ROLES) as (_, _, org):
            return response(payment_links.save_integration(org_id=org, data=data))


class FlowPaymentConfirmView(APIView):
    """Flow urlConfirmation webhook — public, verified server-side."""

    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = [FormParser]

    @extend_schema(
        operation_id="project_payment_flow_confirm",
        tags=["projects"],
        request=FlowConfirmationSerializer,
        responses={200: FlowAcknowledgementSerializer, **ERRORS},
    )
    def post(self, request, link_id):
        data = FlowConfirmationSerializer(data=request.data)
        if not data.is_valid() or len(request.data.getlist("token")) != 1:
            raise contract_error(
                400, "invalid_flow_callback", "La confirmación requiere un token válido."
            )
        try:
            payment_links.confirm_link(link_id=link_id, token=data.validated_data["token"])
        except FlowError as error:
            raise contract_error(
                404 if error.code == "payment_link_not_found" else 503,
                error.code,
                "El cobro requiere confirmación del proveedor.",
            ) from None
        return response({"received": True})


class ProjectPaymentView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(
        operation_id="project_payment_void",
        request=PaymentVoidSerializer,
        responses={200: PaymentsSummarySerializer, **ERRORS},
        **SCHEMA,
    )
    def post(self, request, project_id, payment_id):
        data = validate(PaymentVoidSerializer, request.data)
        with scope(request, WRITE_ROLES) as (token, _, org):
            return response(
                payments.void_payment(
                    org_id=org,
                    project_id=project_id,
                    payment_id=payment_id,
                    actor_id=token.user_id,
                    data=data,
                )
            )
