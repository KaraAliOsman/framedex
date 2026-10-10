"""Official interchange and one review surface for structured and AI sources."""

import json
from pathlib import Path

from django.db import DatabaseError
from django.http import FileResponse, HttpResponse
from io import BytesIO
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from authentication.errors import contract_error
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from documents.views import ERRORS, documentary_scope, validate
from ingest import catalog_review, catalog_sources
from ingest.catalog_service import _get
from ingest.catalog_template import SCHEMAS, export_csv, public_schema
from ingest.serializers import (
    CatalogImportConfirmResponseSerializer, CatalogImportDetailResponseSerializer,
    CatalogPublishRequestSerializer, CatalogReviewRequestSerializer, CatalogReviewResponseSerializer,
    CatalogTemplateSchemaSerializer, CatalogUndoRequestSerializer,
)
from ingest.views import _CATALOG_WRITERS, _READERS, _payload
from pricing.views import DecimalJSONParser
from pricing.repository import rows

HEADERS = [ACTIVE_ORGANIZATION_HEADER]
SCHEMA = {"parameters": HEADERS, "tags": ["catalogs"]}
FORMAT_PARAMETERS = [*HEADERS,
    OpenApiParameter("format", OpenApiTypes.STR, enum=["xlsx", "csv"], required=False),
    OpenApiParameter("sheet", OpenApiTypes.STR, enum=list(SCHEMAS), required=False)]


def _sheet(request):
    value = request.query_params.get("sheet", "Sistemas")
    if value not in SCHEMAS:
        raise contract_error(422, "catalog_template_sheet_invalid", "Elige una hoja de la plantilla vigente.")
    return value


class CatalogTemplateSchemaView(APIView):
    @extend_schema(operation_id="catalog_template_schema", responses={200: CatalogTemplateSchemaSerializer, **ERRORS}, **SCHEMA)
    def get(self, request):
        with documentary_scope(request, _READERS):
            return Response(public_schema())


class CatalogTemplateView(APIView):
    @extend_schema(operation_id="catalog_template_download", parameters=FORMAT_PARAMETERS,
        responses={200: OpenApiTypes.BINARY, **ERRORS}, tags=["catalogs"])
    def get(self, request):
        with documentary_scope(request, _READERS):
            format_ = request.query_params.get("format", "xlsx")
            if format_ == "xlsx":
                return FileResponse((Path(__file__).parent / "templates/catalogo-v1.xlsx").open("rb"),
                    as_attachment=True, filename="catalogo-dekopen-v1.xlsx",
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            if format_ != "csv":
                raise contract_error(422, "catalog_template_format_invalid", "Elige XLSX o CSV.")
            output = HttpResponse(export_csv(_sheet(request), []), content_type="text/csv; charset=utf-8")
            output["Content-Disposition"] = 'attachment; filename="catalogo-dekopen-v1.csv"'
            return output


class CatalogImportExportView(APIView):
    @extend_schema(operation_id="catalog_import_export", parameters=[*HEADERS, FORMAT_PARAMETERS[-1]],
        responses={200: OpenApiTypes.BINARY, **ERRORS}, tags=["catalogs"])
    def get(self, request, import_id):
        with documentary_scope(request, _READERS) as (_, _, org_id):
            row = _get(org_id, import_id)
            candidates = row["candidates"]
            if row["status"] == "CONFIRMED":
                found = rows("SELECT candidates FROM public.catalog_import_publications WHERE import_id=%s AND org_id=%s AND action='PUBLISH' ORDER BY created_at DESC LIMIT 1", [import_id, org_id])
                if found:
                    candidates = found[0]["candidates"]
            if isinstance(candidates, str):
                candidates = json.loads(candidates)
            output = HttpResponse(export_csv(_sheet(request), candidates), content_type="text/csv; charset=utf-8")
            output["Content-Disposition"] = 'attachment; filename="catalogo-revisado.csv"'
            return output


class CatalogImportReviewView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(operation_id="catalog_import_review", request=CatalogReviewRequestSerializer,
        responses={200: CatalogReviewResponseSerializer, **ERRORS}, **SCHEMA)
    def post(self, request, import_id):
        with documentary_scope(request, _CATALOG_WRITERS) as (token, _, org_id):
            data = validate(CatalogReviewRequestSerializer, request.data)
            result = catalog_review.preview(org_id=org_id, import_id=import_id, items=data["items"])
            catalog_sources.record_review(org_id=org_id, import_id=import_id,
                actor_id=token.user_id, items=data["items"], review_token=result["review_token"], errors=result["errors"])
            return _payload(result)


class CatalogImportEventSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    action = serializers.CharField()
    actor_id = serializers.UUIDField()
    actor = serializers.CharField()
    created_at = serializers.DateTimeField()
    details = serializers.DictField()


class CatalogImportTimelineSerializer(serializers.Serializer):
    items = CatalogImportEventSerializer(many=True)


class CatalogImportTimelineView(APIView):
    @extend_schema(operation_id="catalog_import_timeline", responses={200: CatalogImportTimelineSerializer, **ERRORS}, **SCHEMA)
    def get(self, request, import_id):
        with documentary_scope(request, _READERS) as (_, _, org_id):
            return _payload(catalog_sources.timeline(org_id, import_id))


class CatalogImportSourceView(APIView):
    @extend_schema(operation_id="catalog_import_source", responses={200: OpenApiTypes.BINARY, **ERRORS}, **SCHEMA)
    def get(self, request, import_id):
        # Original files can contain costs even when extraction did not find
        # any. Only the commercial catalog reviewers may open those bytes.
        with documentary_scope(request, _CATALOG_WRITERS) as (_, _, org_id):
            row, content = catalog_sources.original_source(org_id, import_id)
            mime = {"PDF": "application/pdf", "TEXT": "text/plain; charset=utf-8",
                    "CSV": "text/csv; charset=utf-8", "XLSX": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}.get(row["kind"])
            if row["kind"] == "IMAGE":
                suffix = row["file_name"].rsplit(".", 1)[-1].lower()
                mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}[suffix]
            response = FileResponse(BytesIO(content), filename=row["file_name"], content_type=mime)
            response["Cache-Control"] = "private, no-store"
            response["X-Content-Type-Options"] = "nosniff"
            return response


class CatalogImportPublishView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(operation_id="catalog_import_publish", request=CatalogPublishRequestSerializer,
        responses={200: CatalogImportConfirmResponseSerializer, **ERRORS}, **SCHEMA)
    def post(self, request, import_id):
        try:
            with documentary_scope(request, _CATALOG_WRITERS) as (token, _, org_id):
                data = validate(CatalogPublishRequestSerializer, request.data)
                return _payload(catalog_review.publish(org_id=org_id, actor_id=token.user_id,
                    import_id=import_id, items=data["items"], review_token=data["review_token"]))
        except DatabaseError as error:
            if "catalog_authority_referenced" in str(error):
                raise contract_error(409, "catalog_publish_locked", "Este catálogo ya se usa en un producto guardado. Publica la corrección con un código nuevo.") from error
            raise contract_error(422, "catalog_publish_constraint", "La publicación no cumple una compatibilidad del catálogo. Revisa las filas y sus referencias.") from error


class CatalogImportUndoView(APIView):
    @extend_schema(operation_id="catalog_import_undo", request=CatalogUndoRequestSerializer,
        responses={200: CatalogImportDetailResponseSerializer, **ERRORS}, **SCHEMA)
    def post(self, request, import_id):
        try:
            with documentary_scope(request, _CATALOG_WRITERS) as (token, _, org_id):
                validate(CatalogUndoRequestSerializer, request.data)
                return _payload(catalog_review.undo_publication(org_id=org_id, actor_id=token.user_id, import_id=import_id))
        except DatabaseError as error:
            raise contract_error(409, "catalog_undo_locked", "El catálogo ya se usa en otro registro. Conserva esta autoridad y publica una nueva versión para corregirla.") from error
