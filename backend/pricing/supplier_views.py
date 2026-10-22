"""Only the owner can inspect or apply a supplier's purchase costs."""

from drf_spectacular.utils import extend_schema
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from pricing import supplier_prices
from pricing.supplier_serializers import (SupplierFileSerializer, SupplierReviewSerializer,
    SupplierInspectionSerializer, SupplierPreviewSerializer)
from pricing.views import ERRORS, scope, validate
from pricing.xlsx_import import MAX_BYTES

SCHEMA = {"tags": ["pricing"], "parameters": [ACTIVE_ORGANIZATION_HEADER]}


class SupplierInspectView(APIView):
    parser_classes = [MultiPartParser]

    @extend_schema(operation_id="pricing_supplier_inspect", request=SupplierFileSerializer,
        responses={200: SupplierInspectionSerializer, **ERRORS}, **SCHEMA)
    def post(self, request):
        with scope(request):
            upload = validate(SupplierFileSerializer, request.data)["file"]
            result = supplier_prices.inspect(upload.read(MAX_BYTES + 1), upload.name)
            return Response(SupplierInspectionSerializer(result).data)


class SupplierReviewView(APIView):
    parser_classes = [MultiPartParser]

    @extend_schema(operation_id="pricing_supplier_review", request=SupplierReviewSerializer,
        responses={200: SupplierPreviewSerializer, **ERRORS}, **SCHEMA)
    def post(self, request):
        with scope(request) as (_, _, org_id):
            data = validate(SupplierReviewSerializer, request.data)
            upload = data["file"]
            result = supplier_prices.review(org_id, upload.read(MAX_BYTES + 1), upload.name, data)
            return Response(SupplierPreviewSerializer(result).data)
