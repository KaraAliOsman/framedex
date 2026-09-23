"""HTTP surface for production: work-order release and floor transitions."""

from __future__ import annotations

from contextlib import contextmanager
import logging
from uuid import UUID

from django.db import DatabaseError
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.errors import contract_error
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from documents.repository import DocumentaryError
from documents.views import ERRORS, documentary_scope, validate
from production import service
from production.serializers import (
    ProductionOrderDetailSerializer,
    ProductionOrderListSerializer,
    ProductionReleaseSerializer,
    StepTransitionRequestSerializer,
    StepTransitionSerializer,
    WorkCenterListSerializer,
    WorkCenterRequestSerializer,
    WorkCenterSerializer,
    WorkOrderOptimizeRequestSerializer,
    WorkOrderOptimizeSerializer,
)

logger = logging.getLogger(__name__)

_READERS = ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER", "INSTALLER")
_STEP_ACTORS = ("OWNER", "WORKSHOP_MANAGER", "INSTALLER")
_WRITERS = ("OWNER", "WORKSHOP_MANAGER")


@contextmanager
def public_production_errors():
    try:
        yield
    except DocumentaryError as error:
        status_code = 404 if error.code in ("version_not_found", "work_order_not_found", "production_step_not_found") else 422
        raise contract_error(
            status_code,
            error.code,
            "La operación de producción fue rechazada; revisa la orden y el paso.",
        ) from error
    except serializers.ValidationError as error:
        raise contract_error(
            422, "production_payload_invalid", "Revisa los parámetros de producción."
        ) from error
    except DatabaseError as error:
        logger.warning("Production transaction rejected (%s)", type(error).__name__)
        raise contract_error(
            409,
            "production_transaction_rejected",
            "La operación de producción entró en conflicto; reintenta.",
        ) from error


class ProductionReleaseView(APIView):
    @extend_schema(
        operation_id="production_release",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=None,
        responses={200: ProductionReleaseSerializer, 201: ProductionReleaseSerializer, **ERRORS},
        tags=["production"],
    )
    def post(self, request, version_id: UUID):
        with public_production_errors():
            with documentary_scope(request, _WRITERS) as (token, _, org_id):
                output = service.release_production(
                    org_id=org_id, version_id=version_id, actor_id=token.user_id
                )
        return Response(output, status=201 if output["created"] else 200)


class ProductionOrderListView(APIView):
    @extend_schema(
        operation_id="production_orders",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=None,
        responses={200: ProductionOrderListSerializer, **ERRORS},
        tags=["production"],
    )
    def get(self, request):
        with public_production_errors():
            with documentary_scope(request, _READERS) as (_, _, org_id):
                output = service.list_production_orders(org_id=org_id)
        return Response(output)


class ProductionOrderDetailView(APIView):
    @extend_schema(
        operation_id="production_order_detail",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=None,
        responses={200: ProductionOrderDetailSerializer, **ERRORS},
        tags=["production"],
    )
    def get(self, request, order_id: UUID):
        with public_production_errors():
            with documentary_scope(request, _READERS) as (_, _, org_id):
                output = service.get_work_order(org_id=org_id, order_id=order_id)
        return Response(output)


class ProductionStepTransitionView(APIView):
    @extend_schema(
        operation_id="production_step_transition",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=StepTransitionRequestSerializer,
        responses={200: StepTransitionSerializer, **ERRORS},
        tags=["production"],
    )
    def post(self, request, step_id: UUID):
        data = validate(StepTransitionRequestSerializer, request.data)
        with public_production_errors():
            with documentary_scope(request, _STEP_ACTORS) as (token, _, org_id):
                output = service.transition_step(
                    org_id=org_id,
                    step_id=step_id,
                    action=data["action"],
                    actor_id=token.user_id,
                    note=data.get("note"),
                )
        return Response(output)


class WorkCenterListView(APIView):
    @extend_schema(
        operation_id="production_work_centers",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=None,
        responses={200: WorkCenterListSerializer, **ERRORS},
        tags=["production"],
    )
    def get(self, request):
        with public_production_errors():
            with documentary_scope(request, _READERS) as (_, _, org_id):
                output = service.list_work_centers(org_id=org_id)
        return Response(output)

    @extend_schema(
        operation_id="production_work_centers_create",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=WorkCenterRequestSerializer,
        responses={200: WorkCenterSerializer, 201: WorkCenterSerializer, **ERRORS},
        tags=["production"],
    )
    def post(self, request):
        data = validate(WorkCenterRequestSerializer, request.data)
        with public_production_errors():
            with documentary_scope(request, _WRITERS) as (_, _, org_id):
                output, created = service.create_work_center(
                    org_id=org_id,
                    code=data["code"],
                    name=data["name"],
                    kind=data["kind"],
                    display_order=data.get("display_order", 0),
                )
        return Response(output, status=201 if created else 200)


class ProductionOrderOptimizeView(APIView):
    @extend_schema(
        operation_id="production_order_optimize",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=WorkOrderOptimizeRequestSerializer,
        responses={200: WorkOrderOptimizeSerializer, **ERRORS},
        tags=["production"],
    )
    def post(self, request, order_id: UUID):
        data = validate(WorkOrderOptimizeRequestSerializer, request.data)
        with public_production_errors():
            with documentary_scope(request, _WRITERS) as (token, _, org_id):
                output = service.optimize_work_order(
                    org_id=org_id,
                    order_id=order_id,
                    actor_id=token.user_id,
                    color=data["color"],
                    cutting_profile_code=data.get("cutting_profile_code"),
                )
        return Response(output)
