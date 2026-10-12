"""HTTP surface for the customer approval portal."""

from __future__ import annotations

from contextlib import contextmanager
import logging
from uuid import UUID

from django.db import DatabaseError
from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.gzip import gzip_page
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.errors import contract_error
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from config.throttling import PortalRateThrottle
from documents.repository import DocumentaryError
from documents.views import ERRORS, documentary_scope, validate
from portal import service
from portal import link_controls
from pricing.serializers import StrictSerializer
from portal.serializers import (
    ApprovalRecordSerializer,
    DecideRequestSerializer,
    InternalApprovalResultSerializer,
    InternalApprovalSerializer,
    PortalQuoteSerializer,
    ShareQuoteResponseSerializer,
    PortalPayRequestSerializer, PortalPayResultSerializer, PortalPayReturnSerializer,
)

logger = logging.getLogger(__name__)

_WRITERS = ("OWNER", "ESTIMATOR")


@contextmanager
def public_portal_errors():
    try:
        yield
    except DocumentaryError as error:
        if error.code in (
            "project_not_found",
            "version_not_found",
            "quote_not_found",
            "approval_not_found",
        ):
            raise contract_error(404, error.code, "El enlace de cotización no existe.") from error
        if error.code == "quote_revoked":
            raise contract_error(
                410, error.code, "Este enlace fue revocado; solicite uno nuevo.", extra=error.extra
            ) from error
        if error.code == "approval_not_pending":
            raise contract_error(
                409, error.code, "Este enlace ya fue respondido y no puede revocarse."
            ) from error
        if error.code in ("quote_expired", "quote_validity_expired"):
            raise contract_error(
                410, error.code, "Esta cotización ya no está vigente; solicite un enlace nuevo.", extra=error.extra
            ) from error
        if error.code == "quote_approve_revision_mismatch":
            raise contract_error(
                409, error.code, "Esta cotización fue reemplazada por una revisión nueva."
            ) from error
        if error.code == "quote_link_stale":
            raise contract_error(
                409, error.code, "Esta cotización fue reemplazada por una revisión nueva."
            ) from error
        if error.code == "quote_link_control_stale":
            raise contract_error(409, error.code, error.public_detail) from error
        if error.code == "quote_already_decided":
            raise contract_error(
                409, error.code, "Esta cotización ya fue respondida."
            ) from error
        raise contract_error(
            409 if error.code in ('quote_consent_stale','quote_option_committed') else 422,
            error.code, error.public_detail or "La acción sobre la cotización fue rechazada.", extra=error.extra
        ) from error
    except serializers.ValidationError as error:
        raise contract_error(
            400, "portal_payload_invalid", "Revise la decisión ingresada."
        ) from error
    except DatabaseError as error:
        logger.warning("Portal transaction rejected (%s)", type(error).__name__)
        raise contract_error(
            409, "portal_transaction_rejected", "La operación fue rechazada por la base."
        ) from error


class ProjectQuoteLinkView(APIView):
    @extend_schema(
        operation_id="project_quote_link_create",
        description="Mint a customer-approval link for the latest sealed version.",
        request=None,
        responses={200: ShareQuoteResponseSerializer, **ERRORS},
    )
    def post(self, request, project_id: UUID):
        with public_portal_errors(), documentary_scope(request, _WRITERS) as (
            token,
            tenant,
            org_id,
        ):
            output = service.share_quote(
                org_id=org_id,
                project_id=project_id,
                actor_id=token.user_id,
                role=tenant.active_organization.role,
            )
            output["path"] = f"/cotizacion/{output['token']}"
            return Response(output)

    @extend_schema(
        operation_id="project_quote_links_list",
        description="Every approval link minted for the project, newest first.",
        request=None,
        responses={200: ApprovalRecordSerializer(many=True), **ERRORS},
    )
    def get(self, request, project_id: UUID):
        with public_portal_errors(), documentary_scope(
            request, ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")
        ) as (_, tenant, org_id):
            output = service.list_approvals(org_id=org_id, project_id=project_id)
            if tenant.active_organization.role == 'WORKSHOP_MANAGER':
                for record in output:
                    record.update(evidence=None, decided_by=None, decided_note=None)
            return Response(
                ApprovalRecordSerializer(
                    output,
                    many=True,
                ).data
            )


class ProjectQuoteLinkRevokeView(APIView):
    @extend_schema(
        operation_id="project_quote_link_revoke",
        description="Revoke a PENDING customer-approval link — the token dies immediately.",
        request=None,
        responses={200: ApprovalRecordSerializer(many=True), **ERRORS},
    )
    def post(self, request, project_id: UUID, approval_id: UUID):
        with public_portal_errors(), documentary_scope(request, _WRITERS) as (
            token,
            _,
            org_id,
        ):
            service.revoke_link(
                org_id=org_id,
                project_id=project_id,
                approval_id=approval_id,
                actor_id=token.user_id,
            )
            return Response(
                ApprovalRecordSerializer(
                    service.list_approvals(org_id=org_id, project_id=project_id),
                    many=True,
                ).data
            )


class LinkDeadlineSerializer(StrictSerializer):
    expected_expires_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField()
    confirmed = serializers.BooleanField()


class LinkRegenerateSerializer(StrictSerializer):
    confirmed = serializers.BooleanField()


class ProjectQuoteLinkDeadlineView(APIView):
    @extend_schema(operation_id="project_quote_link_deadline", request=LinkDeadlineSerializer,
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        responses={200: ApprovalRecordSerializer(many=True), **ERRORS})
    def put(self, request, project_id: UUID, approval_id: UUID):
        data = validate(LinkDeadlineSerializer, request.data)
        with public_portal_errors(), documentary_scope(request, _WRITERS) as (token, _, org_id):
            return Response(link_controls.change_deadline(org_id=org_id, project_id=project_id,
                approval_id=approval_id, actor_id=token.user_id, data=data))


class ProjectQuoteLinkRegenerateView(APIView):
    @extend_schema(operation_id="project_quote_link_regenerate", request=LinkRegenerateSerializer,
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        responses={200: ShareQuoteResponseSerializer, **ERRORS})
    def post(self, request, project_id: UUID, approval_id: UUID):
        data = validate(LinkRegenerateSerializer, request.data)
        with public_portal_errors(), documentary_scope(request, _WRITERS) as (token, tenant, org_id):
            return Response(link_controls.regenerate(org_id=org_id, project_id=project_id,
                approval_id=approval_id, actor_id=token.user_id, role=tenant.active_organization.role,
                confirmed=data["confirmed"]))


class ProjectQuoteApproveView(APIView):
    @extend_schema(
        operation_id="project_quote_approve_internal",
        description=(
            "Staff records that the customer approved the quote off-channel — "
            "same audit trail and project transition as a portal decision."
        ),
        request=InternalApprovalSerializer,
        responses={200: InternalApprovalResultSerializer, **ERRORS},
    )
    def post(self, request, project_id: UUID):
        with public_portal_errors(), documentary_scope(request, _WRITERS) as (
            token,
            _,
            org_id,
        ):
            payload = validate(InternalApprovalSerializer, request.data or {})
            return Response(
                service.approve_internal(
                    org_id=org_id,
                    project_id=project_id,
                    actor_id=token.user_id,
                    actor_label=token.email or str(token.user_id),
                    note=payload.get("note"),
                )
            )


@method_decorator(never_cache, name="dispatch")
@method_decorator(gzip_page, name='dispatch')
class PortalQuoteView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [PortalRateThrottle]

    @extend_schema(
        operation_id="portal_quote_retrieve",
        description="Public quote summary behind a share token.",
        responses={200: PortalQuoteSerializer, **ERRORS},
    )
    def get(self, request, token: str):
        with public_portal_errors():
            return Response(service.portal_quote(token))


@method_decorator(never_cache, name="dispatch")
class PortalQuoteDecisionView(APIView):
    authentication_classes = []
    throttle_classes = [PortalRateThrottle]
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="portal_quote_decide",
        description="Customer approves or declines the shared quote.",
        request=DecideRequestSerializer,
        responses={200: PortalQuoteSerializer, **ERRORS},
    )
    def post(self, request, token: str):
        with public_portal_errors():
            data = validate(DecideRequestSerializer, request.data)
            output = service.decide_quote(
                token=token,
                **data,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:1024],
            )
            return Response(output)


@method_decorator(never_cache, name='dispatch')
class PortalQuotePaymentView(APIView):
    authentication_classes = []
    throttle_classes = [PortalRateThrottle]
    permission_classes = [AllowAny]

    @extend_schema(operation_id='portal_quote_pay', request=PortalPayRequestSerializer,
                   responses={200: PortalPayResultSerializer, **ERRORS})
    def post(self, request, token: str):
        from portal.payments import create
        with public_portal_errors():
            data = validate(PortalPayRequestSerializer, request.data)
            return Response(create(token=token, **data))


@method_decorator(never_cache, name='dispatch')
class PortalPaymentReturnView(APIView):
    authentication_classes = []
    throttle_classes = [PortalRateThrottle]
    permission_classes = [AllowAny]

    @extend_schema(operation_id='portal_payment_return', parameters=[
        OpenApiParameter('access', str, required=True), OpenApiParameter('redirect', bool)],
        responses={200: PortalPayReturnSerializer, 302: None, **ERRORS})
    def get(self, request, context_id: UUID):
        from portal.payments import result
        with public_portal_errors():
            output = result(context_id=context_id, access=request.query_params.get('access', ''))
            if request.query_params.get('redirect') == 'true':
                return self._redirect(output)
            return Response(output)

    @extend_schema(operation_id='portal_payment_provider_return', request=None,
        parameters=[OpenApiParameter('access', str, required=True)], responses={302: None, **ERRORS})
    def post(self, request, context_id: UUID):
        from portal.payments import result
        with public_portal_errors():
            return self._redirect(result(context_id=context_id, access=request.query_params.get('access', '')))

    @staticmethod
    def _redirect(output):
        origin = (settings.DEKOPEN_PUBLIC_APP_URL or settings.BILLING_FRONTEND_ORIGIN).rstrip('/')
        return HttpResponseRedirect(origin + output['portal_path'])
