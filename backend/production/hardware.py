"""Read-only consolidated picking for every position of a sealed revision."""

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from documents.views import ERRORS, documentary_scope
from production.serializers import HardwarePickingRowSerializer
from production.service import version_hardware_picking
from production.views import _READERS, public_production_errors


class VersionHardwarePickingSerializer(serializers.Serializer):
    rows = HardwarePickingRowSerializer(many=True)


class VersionHardwarePickingView(APIView):
    @extend_schema(operation_id="production_version_hardware_picking", parameters=[ACTIVE_ORGANIZATION_HEADER],
        responses={200: VersionHardwarePickingSerializer, **ERRORS}, tags=["production"])
    def get(self, request, version_id):
        with public_production_errors(), documentary_scope(request, _READERS) as (_, _, org_id):
            result = version_hardware_picking(org_id=org_id, version_id=version_id)
        return Response(result)
