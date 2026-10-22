"""A catalog trial remains distinct from publishing manufacturer facts."""

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.views import verified_request_token
from catalogs import reference_windows
from catalogs.reference_serializers import (
    ReferenceWindowListSerializer, ReferenceWindowSerializer, SetupProgressInputSerializer,
    SetupProgressSerializer, TrialInputSerializer, TrialProposalInputSerializer,
    TrialProposalsSerializer, TrialResponseSerializer, TrialVerificationSerializer,
)
from catalogs.views import CatalogJSONParser, ERRORS, HEADERS, READ_ROLES, _validated, catalog_scope

SCHEMA = {"tags": ["catalogs"], "parameters": HEADERS}


class SeriesTrialView(APIView):
    parser_classes = [CatalogJSONParser]

    @extend_schema(operation_id="catalog_series_trial", request=TrialInputSerializer,
        responses={200: TrialResponseSerializer, **ERRORS, 422: ERRORS[400]}, **SCHEMA)
    def post(self, request, system_id):
        with catalog_scope(request, roles=READ_ROLES) as org_id:
            result = reference_windows.trial(org_id, system_id, _validated(TrialInputSerializer, request.data))
            return Response(TrialResponseSerializer(result).data)


class SeriesTrialProposalsView(APIView):
    parser_classes = [CatalogJSONParser]

    @extend_schema(operation_id="catalog_series_trial_proposals", request=TrialProposalInputSerializer,
        responses={200: TrialProposalsSerializer, **ERRORS, 422: ERRORS[400]}, **SCHEMA)
    def post(self, request, system_id):
        with catalog_scope(request) as org_id:
            result = reference_windows.proposals(org_id, system_id, _validated(TrialProposalInputSerializer, request.data))
            return Response(TrialProposalsSerializer(result).data)


class SeriesTrialVerifyView(APIView):
    parser_classes = [CatalogJSONParser]

    @extend_schema(operation_id="catalog_series_trial_verify", request=TrialVerificationSerializer,
        responses={201: ReferenceWindowSerializer, **ERRORS, 422: ERRORS[400]}, **SCHEMA)
    def post(self, request, system_id):
        with catalog_scope(request) as org_id:
            result = reference_windows.verify(org_id, system_id, verified_request_token(request).user_id,
                _validated(TrialVerificationSerializer, request.data))
            return Response(ReferenceWindowSerializer(result).data, status=201)


class SeriesReferencesView(APIView):
    @extend_schema(operation_id="catalog_series_references", responses={200: ReferenceWindowListSerializer, **ERRORS}, **SCHEMA)
    def get(self, request, system_id):
        with catalog_scope(request, roles=READ_ROLES) as org_id:
            result = {"items": reference_windows.references(org_id, system_id)}
            return Response(ReferenceWindowListSerializer(result).data)


class SeriesSetupProgressView(APIView):
    parser_classes = [CatalogJSONParser]

    @extend_schema(operation_id="catalog_series_setup_progress", responses={200: SetupProgressSerializer, **ERRORS}, **SCHEMA)
    def get(self, request, system_id):
        with catalog_scope(request, roles=READ_ROLES) as org_id:
            return Response(SetupProgressSerializer(reference_windows.progress(org_id, system_id)).data)

    @extend_schema(operation_id="catalog_series_save_setup_progress", request=SetupProgressInputSerializer,
        responses={200: SetupProgressSerializer, **ERRORS}, **SCHEMA)
    def put(self, request, system_id):
        with catalog_scope(request) as org_id:
            result = reference_windows.progress(org_id, system_id, _validated(SetupProgressInputSerializer, request.data))
            return Response(SetupProgressSerializer(result).data)
