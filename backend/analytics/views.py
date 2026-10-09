"""Read-only operational analytics surface."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from documents.views import ERRORS, documentary_scope
from analytics import service, today
from analytics.serializers import (
    OperationalSummarySerializer, QuotationIndexQuerySerializer,
    QuotationIndexResponseSerializer, TodayResponseSerializer,
)

_READERS = ("OWNER", "ESTIMATOR", "WORKSHOP_MANAGER")


class OperationalSummaryView(APIView):
    @extend_schema(
        operation_id="analytics_operational_summary",
        parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=None,
        responses={200: OperationalSummarySerializer, **ERRORS},
        tags=["analytics"],
    )
    def get(self, request):
        with documentary_scope(request, _READERS) as (token, tenant, org_id):
            output = service.operational_summary(org_id=org_id)
            from pricing.repository import commercial_backend
            from pricing.workspace import project_price_attention
            with commercial_backend():
                output['prep'].update(project_price_attention(org_id,token.user_id,tenant.active_organization.role))
        # job_runs is a service-owned table: the member-facing RLS context has
        # no grant, so the count runs outside it as the connection owner with
        # the verified org filter — the same pattern as the jobs API.
        output["prep"]["jobs_failed"] = service.failed_jobs_count(org_id=org_id)
        return Response(output)


class TodayView(APIView):
    @extend_schema(
        operation_id="analytics_today", parameters=[ACTIVE_ORGANIZATION_HEADER],
        request=None, responses={200: TodayResponseSerializer, **ERRORS}, tags=["analytics"],
    )
    def get(self, request):
        with documentary_scope(request, (*_READERS, "OPERATOR", "INSTALLER")) as (token, tenant, org_id):
            output = today.daily_work(org_id, token.user_id, tenant.active_organization.role)
        return Response(output)


class QuotationsView(APIView):
    @extend_schema(
        operation_id="analytics_quotations",
        parameters=[ACTIVE_ORGANIZATION_HEADER, QuotationIndexQuerySerializer],
        request=None, responses={200: QuotationIndexResponseSerializer, **ERRORS}, tags=["analytics"],
    )
    def get(self, request):
        query = QuotationIndexQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        with documentary_scope(request, ("OWNER", "ESTIMATOR")) as (_, _, org_id):
            data = query.validated_data
            output = today.quotations(org_id, query=data["q"], attention=data["attention"],
                                      phase=data["phase"], currency=data["currency"],
                                      offset=data["offset"], limit=data["limit"])
        return Response(output)
