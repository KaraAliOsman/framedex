"""Tenant-bound template and series-sheet endpoints."""

from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.views import verified_request_token
from catalogs import series
from catalogs.family_templates import family_templates
from catalogs.series_serializers import (
    CellAddressSerializer, CellHistorySerializer, FamilyTemplateListSerializer,
    SeriesBatchConfirmSerializer, SeriesBatchEditSerializer, SeriesCreateSerializer,
    SeriesSheetSerializer,
)
from catalogs.views import (
    CatalogJSONParser, ERRORS, HEADERS, READ_ROLES, _validated, catalog_scope,
)
from authentication.tenancy import MembershipRepository, resolve_tenant_context


def _owner(request):
    tenant = resolve_tenant_context(
        MembershipRepository().list_active_for_user(verified_request_token(request).user_id),
        request.headers.get("X-Organization-ID"))
    return tenant.active_organization.role == "OWNER"


class FamilyTemplatesView(APIView):
    @extend_schema(operation_id="catalog_family_templates", tags=["catalogs"], parameters=HEADERS,
        responses={200: FamilyTemplateListSerializer, **ERRORS})
    def get(self, request):
        with catalog_scope(request, roles=READ_ROLES):
            return Response(FamilyTemplateListSerializer({"items": family_templates()}).data)


class SeriesCreateView(APIView):
    parser_classes = [CatalogJSONParser]

    @extend_schema(operation_id="catalog_series_create", tags=["catalogs"], parameters=HEADERS,
        request=SeriesCreateSerializer, responses={201: SeriesSheetSerializer, **ERRORS})
    def post(self, request):
        with catalog_scope(request) as org_id:
            sheet = series.create_from_template(org_id, verified_request_token(request).user_id,
                _validated(SeriesCreateSerializer, request.data), can_view_prices=_owner(request))
            return Response(SeriesSheetSerializer(sheet).data, status=201)


class SeriesSheetView(APIView):
    @extend_schema(operation_id="catalog_series_sheet", tags=["catalogs"], parameters=HEADERS,
        responses={200: SeriesSheetSerializer, **ERRORS})
    def get(self, request, system_id):
        with catalog_scope(request, roles=READ_ROLES) as org_id:
            sheet = series.series_sheet(org_id, system_id, can_view_prices=_owner(request))
            return Response(SeriesSheetSerializer(sheet).data)


class SeriesCellsView(APIView):
    parser_classes = [CatalogJSONParser]

    @extend_schema(operation_id="catalog_series_edit_cells", tags=["catalogs"], parameters=HEADERS,
        request=SeriesBatchEditSerializer, responses={200: SeriesSheetSerializer, **ERRORS})
    def patch(self, request, system_id):
        with catalog_scope(request) as org_id:
            sheet = series.edit_cells(org_id, system_id, verified_request_token(request).user_id,
                _validated(SeriesBatchEditSerializer, request.data), can_view_prices=_owner(request))
            return Response(SeriesSheetSerializer(sheet).data)


class SeriesConfirmView(APIView):
    parser_classes = [CatalogJSONParser]

    @extend_schema(operation_id="catalog_series_confirm_cells", tags=["catalogs"], parameters=HEADERS,
        request=SeriesBatchConfirmSerializer, responses={200: SeriesSheetSerializer, **ERRORS})
    def post(self, request, system_id):
        with catalog_scope(request) as org_id:
            sheet = series.confirm_cells(org_id, system_id, verified_request_token(request).user_id,
                _validated(SeriesBatchConfirmSerializer, request.data), can_view_prices=_owner(request))
            return Response(SeriesSheetSerializer(sheet).data)


class SeriesHistoryView(APIView):
    @extend_schema(operation_id="catalog_series_cell_history", tags=["catalogs"], parameters=[*HEADERS,
        OpenApiParameter("resource", OpenApiTypes.STR, required=True),
        OpenApiParameter("row_id", OpenApiTypes.UUID, required=True),
        OpenApiParameter("field", OpenApiTypes.STR, required=True)],
        responses={200: CellHistorySerializer, **ERRORS})
    def get(self, request, system_id):
        with catalog_scope(request, roles=READ_ROLES) as org_id:
            result = series.history(org_id, system_id, _validated(CellAddressSerializer, request.query_params.dict()))
            return Response(CellHistorySerializer(result).data)
