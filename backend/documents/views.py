"""Authenticated tenant boundary for documentary inputs, freeze, and artifacts."""

from __future__ import annotations

from contextlib import contextmanager
import logging
from uuid import UUID

from django.db import DatabaseError
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.errors import contract_error
from authentication.rls import authenticated_rls_context
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER, ErrorResponseSerializer
from authentication.tenancy import MembershipRepository, enforce_owner_mfa, resolve_tenant_context
from authentication.views import verified_request_token
from dekopen_engine.cutting import InvalidCutContract
from dekopen_engine.inspection_models import InspectorConfigurationError
from dekopen_engine.manufacturing import ManufacturingAuthorityError
from dekopen_engine.purchasing import PurchaseAuthorityError
from engine_api.adapter import InvalidEngineRequest, UnsupportedEngineContract
from engine_api.repository import SystemNotFound, UnsupportedCatalogContract

from documents.artifacts import generate_artifact, signed_artifact_access
from documents.repository import DocumentaryError, documentary_backend
from documents.serializers import (
    ArtifactRequestSerializer,
    ArtifactResponseSerializer,
    DocumentaryInputsResponseSerializer,
    DocumentaryInputsSerializer,
    FreezeRequestSerializer,
    FreezeResponseSerializer,
    SignedAccessResponseSerializer,
)
from documents.service import freeze_revision_a, save_documentary_inputs

logger = logging.getLogger(__name__)
ERRORS = {
    code: OpenApiResponse(ErrorResponseSerializer)
    for code in (400, 401, 403, 404, 409, 422, 503)
}


def validate(serializer_type, data):
    serializer = serializer_type(data=data)
    if not serializer.is_valid():
        raise contract_error(400, "validation_error", "Revisa los campos documentales ingresados.")
    return serializer.validated_data


@contextmanager
def public_documentary_errors():
    try:
        yield
    except DocumentaryError as error:
        if error.code in ("project_not_found", "project_version_not_found", "pricing_operation_not_found"):
            status_code = 404
        elif error.code == "document_access_denied":
            status_code = 403
        elif error.code == "documentary_freeze_confirmation_required":
            status_code = 409
        else:
            status_code = 422
        raise contract_error(
            status_code,
            error.code,
            "La evidencia documental no pudo guardarse; revisa el proyecto, sus autoridades y su estado.",
        ) from error
    except InvalidEngineRequest as error:
        raise contract_error(400, "validation_error", "Revisa los datos técnicos del proyecto.") from error
    except (
        InvalidCutContract,
        InspectorConfigurationError,
        ManufacturingAuthorityError,
        PurchaseAuthorityError,
        UnsupportedEngineContract,
        UnsupportedCatalogContract,
        SystemNotFound,
    ) as error:
        raise contract_error(
            422,
            "documentary_authority_required",
            "Falta o no coincide una autoridad técnica necesaria para congelar la revisión.",
        ) from error
    except DatabaseError as error:
        cause = error.__cause__
        logger.warning(
            "Documentary transaction rejected (%s, SQLSTATE=%s, constraint=%s)",
            type(error).__name__,
            getattr(cause, "sqlstate", None),
            getattr(getattr(cause, "diag", None), "constraint_name", None),
        )
        raise contract_error(
            409,
            "documentary_transaction_rejected",
            "La operación documental entró en conflicto; recarga el proyecto y vuelve a intentarlo.",
        ) from error


@contextmanager
def documentary_scope(request, allowed: tuple[str, ...]):
    token = verified_request_token(request)
    with public_documentary_errors():
        with authenticated_rls_context(token.claims):
            tenant = resolve_tenant_context(
                MembershipRepository().list_active_for_user(token.user_id),
                request.headers.get("X-Organization-ID"),
            )
            enforce_owner_mfa(tenant, token.aal)
            if tenant.active_organization.role not in allowed:
                raise contract_error(
                    403,
                    "documentary_permission_denied",
                    "Tu rol no permite realizar esta operación documental.",
                )
            yield token, tenant, tenant.active_organization.organization_id


class DocumentaryInputsView(APIView):
    @extend_schema(
        operation_id="documentary_save_inputs",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=DocumentaryInputsSerializer,
        responses={200: DocumentaryInputsResponseSerializer, **ERRORS},
        tags=["documents"],
    )
    def put(self, request, project_id: UUID):
        data = validate(DocumentaryInputsSerializer, request.data)
        with documentary_scope(request, ("OWNER", "ESTIMATOR")) as (token, _, org_id):
            with documentary_backend():
                output = save_documentary_inputs(
                    org_id=org_id,
                    actor_id=token.user_id,
                    project_id=project_id,
                    data=data,
                )
        return Response(output)


class FreezeRevisionView(APIView):
    @extend_schema(
        operation_id="documentary_freeze_revision_a",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=FreezeRequestSerializer,
        responses={200: FreezeResponseSerializer, 201: FreezeResponseSerializer, **ERRORS},
        tags=["documents"],
    )
    def post(self, request, project_id: UUID):
        data = validate(FreezeRequestSerializer, request.data)
        with documentary_scope(request, ("OWNER", "ESTIMATOR")) as (token, _, org_id):
            output = freeze_revision_a(
                org_id=org_id,
                actor_id=token.user_id,
                project_id=project_id,
                pricing_operation_id=data["pricing_operation_id"],
                confirmed=data["confirmed"],
            )
        return Response(output, status=201 if output["created"] else 200)


class ArtifactGenerateView(APIView):
    @extend_schema(
        operation_id="documentary_generate_artifact",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=ArtifactRequestSerializer,
        responses={200: ArtifactResponseSerializer, 201: ArtifactResponseSerializer, **ERRORS},
        tags=["documents"],
    )
    def post(self, request):
        data = validate(ArtifactRequestSerializer, request.data)
        with documentary_scope(
            request, ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")
        ) as (token, tenant, org_id):
            output = generate_artifact(
                org_id=org_id,
                actor_id=token.user_id,
                role=tenant.active_organization.role,
                project_version_id=data["project_version_id"],
                order_id=data.get("order_id"),
                document_type=data["document_type"],
                file_format=data["format"],
            )
        return Response(output, status=201)


class ArtifactAccessView(APIView):
    @extend_schema(
        operation_id="documentary_artifact_access",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=None,
        responses={200: SignedAccessResponseSerializer, **ERRORS},
        tags=["documents"],
    )
    def post(self, request, artifact_id: UUID):
        with documentary_scope(
            request, ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")
        ) as (_, tenant, org_id):
            _, output = signed_artifact_access(
                org_id=org_id,
                artifact_id=artifact_id,
                role=tenant.active_organization.role,
            )
        return Response(output)
