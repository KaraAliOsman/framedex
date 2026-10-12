"""Costs require OWNER/WORKSHOP_MANAGER in both HTTP and database policies."""

import csv
import json
from decimal import Decimal, InvalidOperation
from io import StringIO

from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from documents.repository import documentary_backend, json_text
from documents.views import ERRORS, documentary_scope
from analytics import metrics, reports
from analytics.decision_serializers import (
    ActualReportRequestSerializer,
    ActualReportResponseSerializer,
    AnalyticsPeriodSerializer,
    AnalyticsPreferenceSerializer,
    AnalyticsWorkspaceSerializer,
)

READERS = ("OWNER", "WORKSHOP_MANAGER")
CSV_UNITS = {"fraction": "proporción", "money": "dinero", "count": "unidades", "hours": "horas"}


class AnalyticsWorkspaceView(APIView):
    @extend_schema(
        operation_id="analytics_decision_workspace",
        parameters=[ACTIVE_ORGANIZATION_HEADER, AnalyticsPeriodSerializer],
        responses={200: AnalyticsWorkspaceSerializer, **ERRORS},
        tags=["analytics"],
    )
    def get(self, request):
        query = AnalyticsPeriodSerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        with documentary_scope(request, READERS) as (_, _, org), documentary_backend():
            output = metrics.workspace(org, **query.validated_data)
        return Response(output)


def csv_cell(value):
    text = "" if value is None else str(value)
    try:
        if Decimal(text).is_finite():
            return text
    except InvalidOperation:
        pass
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else text


class AnalyticsCsvView(APIView):
    @extend_schema(
        operation_id="analytics_decision_csv",
        parameters=[ACTIVE_ORGANIZATION_HEADER, AnalyticsPeriodSerializer],
        responses={
            200: OpenApiResponse(
                OpenApiTypes.BINARY,
                description="Detalle CSV UTF-8; valores exactos y definición por cifra.",
            ),
            **ERRORS,
        },
        tags=["analytics"],
    )
    def get(self, request):
        query = AnalyticsPeriodSerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        with documentary_scope(request, READERS) as (_, _, org), documentary_backend():
            output = metrics.workspace(org, **query.validated_data)
        buffer = StringIO(newline="")
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "desde",
                "hasta",
                "metrica",
                "valor",
                "unidad",
                "moneda",
                "causa",
                "formula",
                "fuente",
                "obra_ot_movimiento",
                "detalle",
                "destino",
                "valor_fuente",
            ]
        )
        for metric in output["metrics"]:
            for detail in metric["details"] or [{}]:
                writer.writerow(
                    [
                        csv_cell(v)
                        for v in [
                            output["start"],
                            output["end"],
                            metric["label"],
                            metric["value"],
                            CSV_UNITS[metric["unit"]],
                            metric["currency"],
                            metric["reason"],
                            metric["formula"],
                            metric["source"],
                            detail.get("code"),
                            detail.get("label"),
                            detail.get("href"),
                            detail.get("value"),
                        ]
                    ]
                )
        response = HttpResponse(
            "\ufeff" + buffer.getvalue(), content_type="text/csv; charset=utf-8"
        )
        response["Content-Disposition"] = (
            f'attachment; filename="analitica-{output["start"]}-{output["end"]}.csv"'
        )
        return response


class AnalyticsPreferencesView(APIView):
    @extend_schema(
        operation_id="analytics_preferences",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        responses={200: AnalyticsPreferenceSerializer, **ERRORS},
        tags=["analytics"],
    )
    def get(self, request):
        with documentary_scope(request, READERS) as (_, _, org), documentary_backend():
            output = reports.preferences(org)
        return Response(output)

    @extend_schema(
        operation_id="analytics_preferences_save",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=AnalyticsPreferenceSerializer,
        responses={200: AnalyticsPreferenceSerializer, **ERRORS},
        tags=["analytics"],
    )
    def put(self, request):
        serializer = AnalyticsPreferenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with documentary_scope(request, ("OWNER",)) as (token, _, org), documentary_backend():
            output = reports.update_preferences(
                org, token.user_id, serializer.validated_data["period_days"]
            )
        return Response(output)


class ActualReportView(APIView):
    @extend_schema(
        operation_id="analytics_actual_report",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        responses={200: ActualReportResponseSerializer, **ERRORS},
        tags=["analytics"],
    )
    def get(self, request, order_id):
        with documentary_scope(request, READERS) as (_, _, org), documentary_backend():
            output = reports.order_read(org, order_id)
        return Response(output)

    @extend_schema(
        operation_id="analytics_actual_report_save",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=ActualReportRequestSerializer,
        responses={201: ActualReportResponseSerializer, **ERRORS},
        tags=["analytics"],
    )
    def post(self, request, order_id):
        serializer = ActualReportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with documentary_scope(request, READERS) as (token, _, org), documentary_backend():
            output = reports.save_report(org, token.user_id, order_id, serializer.validated_data)
        return Response(json.loads(json_text(output)), status=201)


class ActualReportPreviewView(APIView):
    @extend_schema(
        operation_id="analytics_actual_report_preview",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=ActualReportRequestSerializer,
        responses={200: ActualReportResponseSerializer, **ERRORS},
        tags=["analytics"],
    )
    def post(self, request, order_id):
        serializer = ActualReportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with documentary_scope(request, READERS) as (token, _, org), documentary_backend():
            output = reports.save_report(
                org, token.user_id, order_id, serializer.validated_data, preview=True
            )
        return Response(json.loads(json_text(output)))
