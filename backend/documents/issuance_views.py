"""Guided quotation boundary: private preview and a single confirmed issuance."""

import json
from uuid import UUID

from django.db import connection, DatabaseError, transaction
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.errors import contract_error
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from authentication.tenancy import MembershipRepository, enforce_owner_mfa, resolve_tenant_context
from authentication.views import verified_request_token
from documents import issuance, quick_drafts
from documents.serializers import FreezeResponseSerializer
from documents.quote_serializers import QuotationLayoutSerializer
from documents.views import (
    ERRORS,
    _database_sqlstate,
    _freeze_connection_ready,
    documentary_scope,
    public_documentary_errors,
    validate,
)
from notifications.serializers import MailRecordSerializer
from pricing.serializers import StrictSerializer
from pricing.views import public_pricing_errors


class QuotationPreviewRequestSerializer(StrictSerializer):
    pricing_operation_id = serializers.UUIDField(required=False, allow_null=True, default=None)


class QuotationCustomerRequestSerializer(StrictSerializer):
    expected_updated_at = serializers.DateTimeField()
    client_name = serializers.CharField(max_length=255)
    client_rut = serializers.CharField(max_length=50)
    client_email = serializers.EmailField()
    delivery_address = serializers.CharField(max_length=2000)


class QuotationCustomerSerializer(serializers.Serializer):
    updated_at = serializers.DateTimeField()


class QuotationPreviewSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    revision_code = serializers.CharField()
    snapshot_sha256 = serializers.CharField()
    bom_hash = serializers.CharField()
    file_sha256 = serializers.CharField()
    byte_size = serializers.IntegerField()
    document_date = serializers.DateTimeField()
    expires_at = serializers.DateTimeField()
    recipient = serializers.EmailField()
    client_name = serializers.CharField()
    currency = serializers.CharField()
    total_price_gross = serializers.CharField()
    production_allowed = serializers.BooleanField()
    documentary_complete = serializers.BooleanField()
    valid_until = serializers.DateField()
    pdf_url = serializers.URLField()


class QuotationIssueRequestSerializer(StrictSerializer):
    preview_id = serializers.UUIDField()
    expected_snapshot_sha256 = serializers.RegexField(r"^[0-9a-f]{64}$")
    expected_document_sha256 = serializers.RegexField(r"^[0-9a-f]{64}$")
    expected_recipient = serializers.EmailField()
    confirmed = serializers.BooleanField()


class QuotationIssueSerializer(FreezeResponseSerializer):
    artifact_id = serializers.UUIDField()
    approval_id = serializers.UUIDField()
    path = serializers.CharField()
    file_sha256 = serializers.CharField()
    mail = MailRecordSerializer()


@public_pricing_errors()
def guided_with_retry(*, request, project_id, data, issuing):
    token = verified_request_token(request)
    for attempt in range(3):
        try:
            _freeze_connection_ready()
            with issuance.provisional_uploads(), transaction.atomic(durable=True):
                with connection.cursor() as cursor:
                    cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
                    cursor.execute(
                        "SELECT set_config('request.jwt.claims',%s,true), "
                        "set_config('request.jwt.claim.sub',%s,true)",
                        [json.dumps(dict(token.claims), separators=(",", ":"), sort_keys=True),
                         str(token.claims.get('sub') or '')],
                    )
                    cursor.execute("SET LOCAL ROLE authenticated")
                tenant = resolve_tenant_context(
                    MembershipRepository().list_active_for_user(token.user_id),
                    request.headers.get("X-Organization-ID"),
                )
                enforce_owner_mfa(tenant, token.aal)
                role = tenant.active_organization.role
                if role not in ("OWNER", "ESTIMATOR"):
                    raise contract_error(
                        403,
                        "documentary_permission_denied",
                        "Solo un estimador o propietario puede emitir. Solicita acceso al propietario.",
                    )
                args = dict(
                    org_id=tenant.active_organization.organization_id,
                    actor_id=token.user_id,
                    project_id=project_id,
                )
                if issuing:
                    return issuance.issue_preview(**args, role=role, data=data)
                return issuance.prepare_preview(
                    **args, pricing_operation_id=data.get("pricing_operation_id")
                )
        except DatabaseError as error:
            if _database_sqlstate(error) not in ("40001", "40P01") or attempt == 2:
                raise
    raise AssertionError("unreachable guided quotation retry state")


class QuotationPreviewView(APIView):
    @extend_schema(
        operation_id="quotation_prepare_preview",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=QuotationPreviewRequestSerializer,
        responses={201: QuotationPreviewSerializer, **ERRORS},
        tags=["documents"],
    )
    def post(self, request, project_id: UUID):
        data = validate(QuotationPreviewRequestSerializer, request.data)
        with public_documentary_errors():
            result = guided_with_retry(
                request=request, project_id=project_id, data=data, issuing=False
            )
        return Response(result, status=201)


class QuotationPreviewAccessView(APIView):
    @extend_schema(
        operation_id="quotation_preview_access",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        responses={200: QuotationPreviewSerializer, **ERRORS},
        tags=["documents"],
    )
    def get(self, request, project_id: UUID, preview_id: UUID):
        with documentary_scope(request, ("OWNER", "ESTIMATOR")) as (token, _, org_id):
            return Response(
                issuance.preview_access(
                    org_id=org_id,
                    actor_id=token.user_id,
                    project_id=project_id,
                    preview_id=preview_id,
                )
            )


class QuotationIssueView(APIView):
    @extend_schema(
        operation_id="quotation_issue",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=QuotationIssueRequestSerializer,
        responses={200: QuotationIssueSerializer, 201: QuotationIssueSerializer, **ERRORS},
        tags=["documents"],
    )
    def post(self, request, project_id: UUID):
        data = validate(QuotationIssueRequestSerializer, request.data)
        with public_documentary_errors():
            result = guided_with_retry(
                request=request, project_id=project_id, data=data, issuing=True
            )
        return Response(result, status=201 if result["created"] else 200)


class QuotationCustomerView(APIView):
    @extend_schema(
        operation_id="quotation_save_customer",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=QuotationCustomerRequestSerializer,
        responses={200: QuotationCustomerSerializer, **ERRORS},
        tags=["documents"],
    )
    def patch(self, request, project_id: UUID):
        data = validate(QuotationCustomerRequestSerializer, request.data)
        with documentary_scope(request, ("OWNER", "ESTIMATOR")) as (_, _, org_id):
            return Response(issuance.save_customer(org_id=org_id, project_id=project_id, data=data))


class QuotationLayoutResponseSerializer(serializers.Serializer):
    layout = QuotationLayoutSerializer()
    prepared = serializers.BooleanField()


class QuotationLayoutView(APIView):
    """This work's quotation composition (template, blocks, texts)."""

    @extend_schema(
        operation_id="quotation_layout_get",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        responses={200: QuotationLayoutResponseSerializer, **ERRORS},
        tags=["documents"],
    )
    def get(self, request, project_id: UUID):
        with documentary_scope(request, ("OWNER", "ESTIMATOR")) as (_, _, org_id):
            return Response(issuance.get_layout(org_id=org_id, project_id=project_id))

    @extend_schema(
        operation_id="quotation_layout_save",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=QuotationLayoutSerializer,
        responses={200: QuotationLayoutResponseSerializer, **ERRORS},
        tags=["documents"],
    )
    def put(self, request, project_id: UUID):
        data = validate(QuotationLayoutSerializer, request.data)
        with documentary_scope(request, ("OWNER", "ESTIMATOR")) as (_, _, org_id):
            return Response(issuance.save_layout(org_id=org_id, project_id=project_id, layout=data))


class QuotationDraftPreviewView(APIView):
    """The real document early: «Borrador», no number consumed, not stored.
    An optional unsaved layout lets the editor show a change before saving."""

    @extend_schema(
        operation_id="quotation_draft_preview",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=QuotationLayoutSerializer,
        responses={200: {"type": "string", "format": "binary"}, **ERRORS},
        tags=["documents"],
    )
    def post(self, request, project_id: UUID):
        data = validate(QuotationLayoutSerializer, request.data or {})
        with documentary_scope(request, ("OWNER", "ESTIMATOR")) as (token, _, org_id):
            content = issuance.draft_preview(
                org_id=org_id, actor_id=token.user_id, project_id=project_id, layout=data or None
            )
        response = HttpResponse(content, content_type="application/pdf")
        response["Cache-Control"] = "private, no-store"
        response["Content-Disposition"] = 'inline; filename="cotizacion-borrador.pdf"'
        return response


class QuickDraftRequestSerializer(StrictSerializer):
    document = serializers.ChoiceField(choices=sorted(quick_drafts.QUICK_DOCUMENTS))


class QuickDraftView(APIView):
    """Any document from a name and one window: quotation, cut sheet, plan or
    materials, rendered by the issuing authority and stamped «Borrador».
    Nothing is stored — a missing price or preparation is composed inside a
    rolled-back transaction."""

    @extend_schema(
        operation_id="documents_quick_draft",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=QuickDraftRequestSerializer,
        responses={200: {"type": "string", "format": "binary"}, **ERRORS},
        tags=["documents"],
    )
    def post(self, request, project_id: UUID):
        data = validate(QuickDraftRequestSerializer, request.data)
        content, name = quick_drafts.render(request, project_id, data["document"])
        response = HttpResponse(content, content_type="application/pdf")
        response["Cache-Control"] = "private, no-store"
        response["Content-Disposition"] = f'inline; filename="{name}.pdf"'
        return response


class QuotationNumberingSerializer(StrictSerializer):
    prefix = serializers.CharField(max_length=20, allow_blank=True)
    next_number = serializers.IntegerField(min_value=1, max_value=999999999)


class QuotationNumberingResponseSerializer(serializers.Serializer):
    prefix = serializers.CharField(allow_blank=True)
    next_number = serializers.IntegerField()
    highest_assigned = serializers.IntegerField(allow_null=True)
    example = serializers.CharField(allow_null=True)


class QuotationNumberingView(APIView):
    """Company quotation numbering: N.º 1 by default, editable prefix/next."""

    @extend_schema(
        operation_id="quotation_numbering_get",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        responses={200: QuotationNumberingResponseSerializer, **ERRORS},
        tags=["documents"],
    )
    def get(self, request):
        from documents import numbering

        with documentary_scope(request, ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")) as (_, _, org_id):
            return Response(numbering.settings(org_id))

    @extend_schema(
        operation_id="quotation_numbering_save",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=QuotationNumberingSerializer,
        responses={200: QuotationNumberingResponseSerializer, **ERRORS},
        tags=["documents"],
    )
    def put(self, request):
        from documents import numbering

        data = validate(QuotationNumberingSerializer, request.data)
        with documentary_scope(request, ("OWNER",)) as (_, _, org_id):
            return Response(numbering.save_settings(org_id, data))
