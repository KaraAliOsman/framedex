"""Manual project API using the existing verified JWT and RLS boundary."""

import json
from datetime import datetime

from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from pricing.repository import encode
from pricing.views import DecimalJSONParser, ERRORS, scope, validate
from projects import service
from projects.serializers import (
    CloneProjectSerializer,
    DeletePositionSerializer,
    PositionResponseSerializer,
    PositionUpdateSerializer,
    PositionWriteSerializer,
    ProjectListResponseSerializer,
    ProjectResponseSerializer,
    ProjectUpdateSerializer,
    ProjectWriteSerializer,
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
        data = validate(ProjectUpdateSerializer, request.data)
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
            return response(service.clone_draft(org, token.user_id, project_id, data), status=201)


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
