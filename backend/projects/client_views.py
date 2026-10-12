"""Typed client directory, audit and account endpoints."""

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.views import APIView

from authentication.errors import contract_error
from pricing.serializers import StrictSerializer
from pricing.views import DecimalJSONParser, ERRORS, scope, validate
from projects import clients, client_history
from projects.client_serializers import (
    ClientNoteWriteSerializer,
    ClientNoteSerializer,
    ClientMergePreviewRequestSerializer,
    ClientMergeRequestSerializer,
)
from projects.serializers import (
    ClientResponseSerializer,
    ClientDossierResponseSerializer,
    ClientMergePreviewSerializer,
)
from projects.views import SCHEMA, READ_ROLES, WRITE_ROLES, response


class ClientDirectoryRequestSerializer(StrictSerializer):
    q = serializers.CharField(max_length=255, required=False, allow_blank=True)
    with_active_projects = serializers.BooleanField(required=False, default=False)
    with_balance = serializers.BooleanField(required=False, default=False)
    include_merged = serializers.BooleanField(required=False, default=False)
    offset = serializers.IntegerField(min_value=0, required=False, default=0)
    limit = serializers.IntegerField(min_value=1, max_value=100, required=False, default=50)


class ClientDirectoryItemSerializer(ClientResponseSerializer):
    has_active_projects = serializers.BooleanField()


class ClientDirectorySerializer(serializers.Serializer):
    items = ClientDirectoryItemSerializer(many=True)
    total = serializers.IntegerField()
    next_offset = serializers.IntegerField(allow_null=True)


class ClientDirectoryView(APIView):
    @extend_schema(
        operation_id="client_directory",
        parameters=[ClientDirectoryRequestSerializer, *SCHEMA["parameters"]],
        responses={200: ClientDirectorySerializer, **ERRORS},
        tags=["projects"],
    )
    def get(self, request):
        data = validate(ClientDirectoryRequestSerializer, request.query_params.dict())
        with scope(request, READ_ROLES) as (_, tenant, org):
            commercial = tenant.active_organization.role in WRITE_ROLES
            if data.get("with_balance") and not commercial:
                raise contract_error(
                    403,
                    "client_financial_denied",
                    "El dueño o estimador consulta el saldo de clientes.",
                )
            return response(client_history.directory(org, data, commercial=commercial))


class ClientDossierView(APIView):
    @extend_schema(
        operation_id="client_dossier",
        responses={200: ClientDossierResponseSerializer, **ERRORS},
        **SCHEMA,
    )
    def get(self, request, client_id):
        with scope(request, WRITE_ROLES) as (_, _, org):
            return response(client_history.dossier(org, client_id))


class ClientNotesView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(
        operation_id="client_note_add",
        request=ClientNoteWriteSerializer,
        responses={201: ClientNoteSerializer, **ERRORS},
        **SCHEMA,
    )
    def post(self, request, client_id):
        data = validate(ClientNoteWriteSerializer, request.data)
        with scope(request, WRITE_ROLES) as (token, _, org):
            return response(clients.add_note(org, client_id, token.user_id, data), status=201)


class ClientMergePreviewView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(
        operation_id="client_merge_preview",
        request=ClientMergePreviewRequestSerializer,
        responses={200: ClientMergePreviewSerializer, **ERRORS},
        **SCHEMA,
    )
    def post(self, request, client_id):
        data = validate(ClientMergePreviewRequestSerializer, request.data)
        with scope(request, WRITE_ROLES) as (_, _, org):
            return response(clients.merge_preview(org, client_id, data["target_id"]))


class ClientMergeView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(
        operation_id="client_merge",
        request=ClientMergeRequestSerializer,
        responses={200: ClientResponseSerializer, **ERRORS},
        **SCHEMA,
    )
    def post(self, request, client_id):
        data = validate(ClientMergeRequestSerializer, request.data)
        with scope(request, WRITE_ROLES) as (_, _, org):
            return response(clients.merge_client(org, client_id, data))
