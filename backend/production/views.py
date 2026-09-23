"""HTTP surface for production: work-order release and floor transitions."""

from __future__ import annotations

from contextlib import contextmanager
import logging
from uuid import UUID

from django.db import DatabaseError
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from pydantic import ValidationError as PydanticValidationError

from authentication.errors import contract_error
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from dekopen_engine.cutting import InvalidCutContract
from documents.repository import DocumentaryError
from documents.views import ERRORS, documentary_scope, validate
from engine_api.repository import SystemNotFound
from production import service
from production.confirmations import confirmation_access, confirm_delivery
from production.dispatch_notes import dispatch_note_access
from production.serializers import (
    DeliveryConfirmRequestSerializer,
    DeliveryConfirmResponseSerializer,
    DeliveryConfirmationAccessSerializer,
    DeliveryResponseSerializer,
    DeliveryScheduleRequestSerializer,
    DeliveryTransitionRequestSerializer,
    CncExportSerializer,
    DispatchNoteAccessSerializer,
    DispatchRequestSerializer,
    InstallationRequestSerializer,
    PackingLabelsSerializer,
    PackingManifestSerializer,
    ProductionOrderDetailSerializer,
    RemakeRequestSerializer,
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
        status_code = 404 if error.code in ("version_not_found", "work_order_not_found", "production_step_not_found", "delivery_not_found", "delivery_confirmation_not_found") else 422
        raise contract_error(
            status_code,
            error.code,
            "La operación de producción fue rechazada; revisa la orden y el paso.",
        ) from error
    except (InvalidCutContract, SystemNotFound, PydanticValidationError) as error:
        logger.warning(
            "Production authority resolution failed (%s: %s)",
            type(error).__name__,
            error,
        )
        raise contract_error(
            422,
            "documentary_authority_required",
            "Falta o no coincide una autoridad técnica necesaria para optimizar la orden.",
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
                    qc_result=data.get("qc_result"),
                )
        return Response(output)


class ProductionOrderRemakeView(APIView):
    @extend_schema(
        operation_id="production_order_remake",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=RemakeRequestSerializer,
        responses={201: ProductionOrderDetailSerializer, **ERRORS},
        tags=["production"],
    )
    def post(self, request, order_id: UUID):
        data = validate(RemakeRequestSerializer, request.data)
        with public_production_errors():
            with documentary_scope(request, _WRITERS) as (token, _, org_id):
                output = service.create_remake(
                    org_id=org_id,
                    order_id=order_id,
                    actor_id=token.user_id,
                    note=data.get("note"),
                )
        return Response(output, status=201)


class ProductionOrderCncExportView(APIView):
    @extend_schema(
        operation_id="production_order_cnc_export",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=None,
        responses={201: CncExportSerializer, **ERRORS},
        tags=["production"],
    )
    def post(self, request, order_id: UUID):
        with public_production_errors():
            with documentary_scope(request, _WRITERS) as (token, _, org_id):
                output = service.export_cnc_files(
                    org_id=org_id,
                    order_id=order_id,
                    actor_id=token.user_id,
                )
        return Response(output, status=201)


class ProductionOrderCncFileView(APIView):
    @extend_schema(
        operation_id="production_order_cnc_file",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=None,
        responses={200: None, **ERRORS},
        tags=["production"],
    )
    def get(self, request, order_id: UUID, filename: str):
        with public_production_errors():
            with documentary_scope(request, _READERS) as (_, _, org_id):
                found = service.cnc_file_content(
                    org_id=org_id, order_id=order_id, filename=filename
                )
        if found is None:
            raise contract_error(
                404,
                "cnc_file_not_found",
                "No hay un archivo CNC generado con ese nombre en la orden.",
            )
        download_name, content = found
        response = HttpResponse(content, content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{download_name}"'
        return response


class ProductionOrderInstallationView(APIView):
    @extend_schema(
        operation_id="production_order_install",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=InstallationRequestSerializer,
        responses={200: ProductionOrderDetailSerializer, **ERRORS},
        tags=["production"],
    )
    def post(self, request, order_id: UUID):
        data = validate(InstallationRequestSerializer, request.data)
        with public_production_errors():
            with documentary_scope(request, _STEP_ACTORS) as (token, _, org_id):
                output = service.confirm_installation(
                    org_id=org_id,
                    order_id=order_id,
                    actor_id=token.user_id,
                    note=data.get("note"),
                )
        return Response(output)


class ProductionOrderPackingView(APIView):
    @extend_schema(
        operation_id="production_order_packing",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=None,
        responses={201: PackingManifestSerializer, **ERRORS},
        tags=["production"],
    )
    def post(self, request, order_id: UUID):
        with public_production_errors():
            with documentary_scope(request, _WRITERS) as (token, _, org_id):
                output = service.generate_packing_manifest(
                    org_id=org_id,
                    order_id=order_id,
                    actor_id=token.user_id,
                )
        return Response(output, status=201)


class ProductionOrderLabelsView(APIView):
    @extend_schema(
        operation_id="production_order_labels",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=None,
        responses={200: PackingLabelsSerializer, **ERRORS},
        tags=["production"],
    )
    def get(self, request, order_id: UUID):
        with public_production_errors():
            with documentary_scope(request, _READERS) as (_, _, org_id):
                output = service.packing_labels(org_id=org_id, order_id=order_id)
        return Response(output)


class ProductionOrderDispatchView(APIView):
    @extend_schema(
        operation_id="production_order_dispatch",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=DispatchRequestSerializer,
        responses={200: ProductionOrderDetailSerializer, **ERRORS},
        tags=["production"],
    )
    def post(self, request, order_id: UUID):
        data = validate(DispatchRequestSerializer, request.data)
        with public_production_errors():
            with documentary_scope(request, _WRITERS) as (token, _, org_id):
                output = service.dispatch_work_order(
                    org_id=org_id,
                    order_id=order_id,
                    actor_id=token.user_id,
                    note=data.get("note"),
                )
        return Response(output)


class ProductionOrderDispatchNoteView(APIView):
    @extend_schema(
        operation_id="production_order_dispatch_note",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=None,
        responses={200: DispatchNoteAccessSerializer, **ERRORS},
        tags=["production"],
    )
    def get(self, request, order_id: UUID):
        with public_production_errors():
            with documentary_scope(request, _READERS) as (_, _, org_id):
                output = dispatch_note_access(org_id=org_id, order_id=order_id)
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


class ProductionOrderDeliveryView(APIView):
    @extend_schema(
        operation_id="production_order_delivery",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=None,
        responses={200: DeliveryResponseSerializer, **ERRORS},
        tags=["production"],
    )
    def get(self, request, order_id: UUID):
        with public_production_errors():
            with documentary_scope(request, _READERS) as (_, _, org_id):
                return Response(service.get_delivery(org_id=org_id, order_id=order_id))

    @extend_schema(
        operation_id="production_order_delivery_schedule",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=DeliveryScheduleRequestSerializer,
        responses={200: DeliveryResponseSerializer, **ERRORS},
        tags=["production"],
    )
    def put(self, request, order_id: UUID):
        data = validate(DeliveryScheduleRequestSerializer, request.data)
        with public_production_errors():
            with documentary_scope(request, _WRITERS) as (token, _, org_id):
                output = service.schedule_delivery(
                    org_id=org_id,
                    order_id=order_id,
                    actor_id=token.user_id,
                    scheduled_date=str(data["scheduled_date"]),
                    time_window=str(data["time_window"]),
                    address=str(data["address"]),
                    contact_name=data.get("contact_name"),
                    contact_phone=data.get("contact_phone"),
                    installer_name=data.get("installer_name"),
                    notes=data.get("notes"),
                )
        return Response(output)


class ProductionOrderDeliveryConfirmView(APIView):
    @extend_schema(
        operation_id="production_order_delivery_confirm",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=DeliveryConfirmRequestSerializer,
        responses={200: DeliveryConfirmResponseSerializer, 201: DeliveryConfirmResponseSerializer, **ERRORS},
        tags=["production"],
    )
    def post(self, request, order_id: UUID):
        data = validate(DeliveryConfirmRequestSerializer, request.data)
        with public_production_errors():
            with documentary_scope(request, _STEP_ACTORS) as (token, _, org_id):
                confirmation = confirm_delivery(
                    org_id=org_id,
                    order_id=order_id,
                    actor_id=token.user_id,
                    receiver_name=data["receiver_name"],
                    receiver_rut=data.get("receiver_rut"),
                    signature_b64=data["signature_png"],
                    payment=data.get("payment"),
                )
                output = {
                    "confirmation": confirmation,
                    "delivery": service.get_delivery(
                        org_id=org_id, order_id=order_id
                    )["delivery"],
                }
        return Response(output, status=201)


class ProductionOrderDeliveryConfirmationView(APIView):
    @extend_schema(
        operation_id="production_order_delivery_confirmation",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=None,
        responses={200: DeliveryConfirmationAccessSerializer, **ERRORS},
        tags=["production"],
    )
    def get(self, request, order_id: UUID):
        with public_production_errors():
            with documentary_scope(request, _READERS) as (_, _, org_id):
                output = confirmation_access(org_id=org_id, order_id=order_id)
        return Response(output)


class ProductionOrderDeliveryTransitionView(APIView):
    @extend_schema(
        operation_id="production_order_delivery_transition",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=DeliveryTransitionRequestSerializer,
        responses={200: DeliveryResponseSerializer, **ERRORS},
        tags=["production"],
    )
    def post(self, request, order_id: UUID):
        data = validate(DeliveryTransitionRequestSerializer, request.data)
        with public_production_errors():
            with documentary_scope(request, _STEP_ACTORS) as (token, _, org_id):
                output = service.transition_delivery(
                    org_id=org_id,
                    order_id=order_id,
                    actor_id=token.user_id,
                    to_status=str(data["status"]),
                )
        return Response(output)
