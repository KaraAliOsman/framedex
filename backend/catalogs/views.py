"""Explicit, typed catalog endpoints with one technical-management permission."""

from contextlib import contextmanager
from decimal import Decimal
import json

from django.db import DatabaseError
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.errors import contract_error
from authentication.rls import authenticated_rls_context
from authentication.serializers import (
    ACTIVE_ORGANIZATION_HEADER,
    ErrorResponseSerializer,
)
from authentication.tenancy import (
    MembershipRepository,
    enforce_owner_mfa,
    resolve_tenant_context,
)
from authentication.views import verified_request_token
from catalogs import service
from catalogs.serializers import (
    ArticleListSerializer,
    ArticleResponseSerializer,
    BeadListSerializer,
    BeadResponseSerializer,
    CatalogFilterSerializer,
    KitListSerializer,
    KitResponseSerializer,
    SystemListSerializer,
    SystemResponseSerializer,
)


def _reject_constant(value):
    raise ValueError("Nonfinite JSON number")


class CatalogJSONParser(JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        try:
            return json.load(
                stream,
                parse_float=Decimal,
                parse_constant=_reject_constant,
            )
        except (ValueError, UnicodeDecodeError) as error:
            raise contract_error(
                400,
                "invalid_json",
                "catalogs.errors.invalid_json",
            ) from error


def _validated(serializer_type, data, *, partial=False):
    serializer = serializer_type(data=data, partial=partial)
    if not serializer.is_valid():
        raise contract_error(
            400,
            "catalog_validation_error",
            "catalogs.errors.validation",
            error_extra={"fields": serializer.errors},
        )
    return serializer.validated_data


READ_ROLES = ("OWNER", "WORKSHOP_MANAGER", "ESTIMATOR")
WRITE_ROLES = ("OWNER", "WORKSHOP_MANAGER")


def _reraise_catalog_error(error):
    sqlstate = getattr(error.__cause__, "sqlstate", None)
    if sqlstate == "23514" and "catalog_authority_referenced" in str(error):
        raise contract_error(409, "catalog_authority_referenced", "catalogs.errors.referenced") from error
    if sqlstate == "42501":
        status, code = 403, "catalog_permission_denied"
    elif sqlstate and (sqlstate.startswith("23") or sqlstate in ("P0001", "40001", "40P01")):
        status, code = 409, "catalog_constraint_conflict"
    else:
        status, code = 503, "catalog_unavailable"
    raise contract_error(status, code, f"catalogs.errors.{code}") from error


@contextmanager
def catalog_scope(request, *, roles=WRITE_ROLES):
    token = verified_request_token(request)
    try:
        with authenticated_rls_context(token.claims):
            tenant = resolve_tenant_context(
                MembershipRepository().list_active_for_user(token.user_id),
                request.headers.get("X-Organization-ID"),
            )
            enforce_owner_mfa(tenant, token.aal)
            if tenant.active_organization.role not in roles:
                raise contract_error(
                    403,
                    "catalog_permission_denied",
                    "catalogs.errors.permission",
                )
            yield tenant.active_organization.organization_id
    except DatabaseError as error:
        _reraise_catalog_error(error)


ERRORS = {code: OpenApiResponse(ErrorResponseSerializer) for code in (400, 401, 403, 404, 409, 503)}
HEADERS = [ACTIVE_ORGANIZATION_HEADER]
WRITE_HEADERS = [*HEADERS, OpenApiParameter(
    "If-Match", OpenApiTypes.STR, OpenApiParameter.HEADER, required=True,
    description="Quoted revision from the most recently read catalog entity.",
)]


class CatalogCollectionView(APIView):
    parser_classes = [CatalogJSONParser]
    resource = None
    response_serializer = None
    list_serializer = None

    def get(self, request):
        with catalog_scope(request, roles=READ_ROLES) as org_id:
            filters = _validated(CatalogFilterSerializer, request.query_params.dict())
            if self.resource is service.SYSTEMS and filters:
                raise contract_error(
                    400,
                    "catalog_validation_error",
                    "catalogs.errors.validation",
                )
            rows = service.list_rows(
                self.resource,
                org_id,
                filters.get("system_id"),
            )
            output = self.list_serializer({"items": rows}).data
        return Response(output)

    def post(self, request):
        with catalog_scope(request) as org_id:
            data = _validated(self.resource.serializer, request.data)
            row = service.create(self.resource, org_id, data)
            output = self.response_serializer(row).data
        return Response(output, status=201)


class CatalogDetailView(APIView):
    parser_classes = [CatalogJSONParser]
    resource = None
    response_serializer = None

    def get(self, request, row_id):
        with catalog_scope(request, roles=READ_ROLES) as org_id:
            row = service.retrieve(self.resource, org_id, row_id)
            output = self.response_serializer(row).data
        return Response(output)

    def patch(self, request, row_id):
        with catalog_scope(request) as org_id:
            data = _validated(
                self.resource.serializer,
                request.data,
                partial=True,
            )
            row = service.update(self.resource, org_id, row_id, data, request.headers.get("If-Match"))
            output = self.response_serializer(row).data
        return Response(output)

    def delete(self, request, row_id):
        with catalog_scope(request) as org_id:
            service.delete(self.resource, org_id, row_id, request.headers.get("If-Match"))
        return Response(status=204)


class CatalogReviewView(APIView):
    """POST {resource}/{id}/review/ — a human vouches for the row's technical
    values; flips LEGACY_UNVERIFIED provenance to MANUAL."""

    resource = None
    response_serializer = None

    def post(self, request, row_id):
        token = verified_request_token(request)
        try:
            with authenticated_rls_context(token.claims):
                tenant = resolve_tenant_context(
                    MembershipRepository().list_active_for_user(token.user_id),
                    request.headers.get("X-Organization-ID"),
                )
                enforce_owner_mfa(tenant, token.aal)
                if tenant.active_organization.role not in WRITE_ROLES:
                    raise contract_error(
                        403,
                        "catalog_permission_denied",
                        "catalogs.errors.permission",
                    )
                row = service.review(
                    self.resource,
                    tenant.active_organization.organization_id,
                    row_id,
                    token.user_id,
                )
                output = self.response_serializer(row).data
        except DatabaseError as error:
            _reraise_catalog_error(error)
        return Response(output)


def _endpoint_classes(name, resource, response_serializer, list_serializer):
    attributes = {
        "__module__": __name__,
        "resource": resource,
        "response_serializer": response_serializer,
        "list_serializer": list_serializer,
    }
    collection = type(
        f"{name}CollectionView",
        (CatalogCollectionView,),
        attributes,
    )
    detail = type(f"{name}DetailView", (CatalogDetailView,), attributes)
    filters = (
        []
        if resource is service.SYSTEMS
        else [
            OpenApiParameter("system_id", OpenApiTypes.UUID, OpenApiParameter.QUERY),
        ]
    )
    collection = extend_schema_view(
        get=extend_schema(
            operation_id=f"catalog_{name.lower()}_list",
            parameters=[*HEADERS, *filters],
            responses={200: list_serializer, **ERRORS},
            tags=["catalogs"],
        ),
        post=extend_schema(
            operation_id=f"catalog_{name.lower()}_create",
            parameters=HEADERS,
            request=resource.serializer,
            responses={201: response_serializer, **ERRORS},
            tags=["catalogs"],
        ),
    )(collection)
    detail = extend_schema_view(
        get=extend_schema(
            operation_id=f"catalog_{name.lower()}_retrieve",
            parameters=HEADERS,
            responses={200: response_serializer, **ERRORS},
            tags=["catalogs"],
        ),
        patch=extend_schema(
            operation_id=f"catalog_{name.lower()}_update",
            parameters=WRITE_HEADERS,
            request=resource.serializer,
            responses={200: response_serializer, **ERRORS},
            tags=["catalogs"],
        ),
        delete=extend_schema(
            operation_id=f"catalog_{name.lower()}_delete",
            parameters=WRITE_HEADERS,
            responses={204: OpenApiResponse(description="Deleted"), **ERRORS},
            tags=["catalogs"],
        ),
    )(detail)
    return collection, detail


def _review_view(name, resource, response_serializer):
    return extend_schema_view(
        post=extend_schema(
            operation_id=f"catalog_{name.lower()}_review",
            parameters=HEADERS,
            request=None,
            responses={200: response_serializer, **ERRORS},
            tags=["catalogs"],
            description=(
                "Mark the row technically reviewed; LEGACY_UNVERIFIED "
                "provenance becomes MANUAL."
            ),
        )
    )(
        type(
            f"{name}ReviewView",
            (CatalogReviewView,),
            {
                "__module__": __name__,
                "resource": resource,
                "response_serializer": response_serializer,
            },
        )
    )


SystemCollectionView, SystemDetailView = _endpoint_classes(
    "System",
    service.SYSTEMS,
    SystemResponseSerializer,
    SystemListSerializer,
)
SystemReviewView = _review_view("System", service.SYSTEMS, SystemResponseSerializer)
ArticleCollectionView, ArticleDetailView = _endpoint_classes(
    "Article",
    service.ARTICLES,
    ArticleResponseSerializer,
    ArticleListSerializer,
)
ArticleReviewView = _review_view("Article", service.ARTICLES, ArticleResponseSerializer)
BeadCollectionView, BeadDetailView = _endpoint_classes(
    "Bead",
    service.BEADS,
    BeadResponseSerializer,
    BeadListSerializer,
)
KitCollectionView, KitDetailView = _endpoint_classes(
    "Kit",
    service.KITS,
    KitResponseSerializer,
    KitListSerializer,
)
KitReviewView = _review_view("Kit", service.KITS, KitResponseSerializer)
