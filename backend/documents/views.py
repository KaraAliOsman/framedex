"""Authenticated tenant boundary for documentary inputs, freeze, and artifacts."""

from __future__ import annotations

from contextlib import contextmanager
import json
import logging
from uuid import UUID

from django.db import connection, DatabaseError, transaction
from drf_spectacular.utils import OpenApiResponse, extend_schema
from psycopg.pq import TransactionStatus
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
    DocumentaryPreparationResponseSerializer,
    FreezeRequestSerializer,
    FreezeResponseSerializer,
    SignedAccessResponseSerializer,
)
from documents.service import freeze_revision_a, prepare_documentary_inputs, save_documentary_inputs

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
        if error.code in (
            "project_not_found",
            "project_version_not_found",
            "pricing_operation_not_found",
            "order_not_found",
            "artifact_not_found",
            "purchase_requirement_not_found",
            "supplier_eligibility_not_found",
            "purchase_projection_not_found",
        ):
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
            error.public_detail
            or "La evidencia documental no pudo guardarse; revisa el proyecto, sus autoridades y su estado.",
            error_extra=error.extra or None,
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
        ValueError,
    ) as error:
        logger.warning(
            "Documentary authority required (%s: %s)",
            type(error).__name__,
            error,
        )
        raise contract_error(
            422,
            "documentary_authority_required",
            "Falta o no coincide una autoridad técnica necesaria para congelar la revisión.",
            error_extra={"reason": str(error)},
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


def _freeze_connection_ready() -> None:
    if connection.vendor != "postgresql":
        raise DatabaseError("Documentary freeze requires PostgreSQL")
    connection.ensure_connection()
    raw_connection = connection.connection
    if (
        raw_connection is None
        or raw_connection.closed
        or connection.in_atomic_block
        or not connection.get_autocommit()
        or raw_connection.info.transaction_status != TransactionStatus.IDLE
    ):
        raise DatabaseError("Documentary freeze requires an idle outermost connection")


def _freeze_attempt(token, claims, organization_header, project_id, data):
    # One outermost transaction at REPEATABLE READ: the isolation statement is
    # the first SQL of the transaction, so claims, tenant resolution, RBAC/MFA,
    # authority locks, documentary reads, canonicalization, and the evidence
    # writes all share a single consistent snapshot.
    _freeze_connection_ready()
    with transaction.atomic(durable=True):
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            cursor.execute(
                "SELECT set_config('request.jwt.claims',%s,true)",
                [json.dumps(claims, separators=(",", ":"), sort_keys=True)],
            )
            cursor.execute("SET LOCAL ROLE authenticated")
        tenant = resolve_tenant_context(
            MembershipRepository().list_active_for_user(token.user_id),
            organization_header,
        )
        enforce_owner_mfa(tenant, token.aal)
        if tenant.active_organization.role not in ("OWNER", "ESTIMATOR"):
            raise contract_error(
                403,
                "documentary_permission_denied",
                "Tu rol no permite realizar esta operación documental.",
            )
        output = freeze_revision_a(
            org_id=tenant.active_organization.organization_id,
            actor_id=token.user_id,
            project_id=project_id,
            pricing_operation_id=data["pricing_operation_id"],
            confirmed=data["confirmed"],
            allow_incomplete_workshop=True,
        )
    return output


def _database_sqlstate(error):
    return getattr(error.__cause__, "sqlstate", None)


def _freeze_with_retry(token, claims, organization_header, project_id, data):
    # Only a serialization failure or deadlock justifies a fresh attempt; each
    # retry runs the complete attempt inside a new transaction/snapshot.
    for attempt in range(3):
        try:
            return _freeze_attempt(
                token, claims, organization_header, project_id, data
            )
        except DatabaseError as error:
            if _database_sqlstate(error) not in ("40001", "40P01") or attempt == 2:
                raise
    raise AssertionError("unreachable freeze retry state")


class DocumentaryInputsView(APIView):
    @extend_schema(
        operation_id="documentary_prepare_inputs",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        responses={200: DocumentaryPreparationResponseSerializer, **ERRORS},
        tags=["documents"],
    )
    def get(self, request, project_id: UUID):
        with documentary_scope(request, ("OWNER", "ESTIMATOR")) as (_, _, org_id):
            with documentary_backend():
                output = prepare_documentary_inputs(org_id=org_id, project_id=project_id)
        return Response(output)

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
        token = verified_request_token(request)
        with public_documentary_errors():
            output = _freeze_with_retry(
                token,
                dict(token.claims),
                request.headers.get("X-Organization-ID"),
                project_id,
                data,
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
            output, created = generate_artifact(
                org_id=org_id,
                actor_id=token.user_id,
                role=tenant.active_organization.role,
                project_version_id=data["project_version_id"],
                order_id=data.get("order_id"),
                document_type=data["document_type"],
                file_format=data["format"],
            )
        return Response(output, status=201 if created else 200)


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
