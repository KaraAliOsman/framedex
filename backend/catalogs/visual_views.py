from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.views import verified_request_token
from catalogs import visuals
from catalogs.views import ERRORS, HEADERS, READ_ROLES, WRITE_ROLES, _validated, catalog_scope
from pricing.serializers import StrictSerializer


class VisualQuerySerializer(StrictSerializer):
    system_id = serializers.UUIDField()


class VisualUploadSerializer(VisualQuerySerializer):
    kind = serializers.ChoiceField(choices=["PROFILE", "TEXTURE"])
    target_key = serializers.CharField(max_length=100)
    file = serializers.FileField(required=False)
    cleared = serializers.BooleanField(default=False)

    def validate(self, attrs):
        if attrs.get("cleared") and attrs.get("file"):
            raise serializers.ValidationError({"file": "Elige una foto o usa la ilustración, una acción a la vez."})
        return attrs


class CatalogVisualSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    system_id = serializers.UUIDField()
    kind = serializers.CharField()
    target_key = serializers.CharField()
    target_code = serializers.CharField(allow_null=True)
    file_name = serializers.CharField(allow_blank=True)
    content_sha256 = serializers.CharField(allow_null=True)
    image_url = serializers.CharField(allow_null=True)
    width_px = serializers.IntegerField(allow_null=True)
    height_px = serializers.IntegerField(allow_null=True)
    cleared = serializers.BooleanField()
    created_at = serializers.DateTimeField()


class CatalogVisualCollectionView(APIView):
    parser_classes = [MultiPartParser]

    @extend_schema(operation_id="catalog_visuals_list", parameters=[*HEADERS, VisualQuerySerializer], responses={200: CatalogVisualSerializer(many=True), **ERRORS}, tags=["catalogs"])
    def get(self, request):
        params = _validated(VisualQuerySerializer, request.query_params)
        with catalog_scope(request, roles=READ_ROLES) as org_id:
            result = visuals.latest(org_id, params["system_id"])
        return Response(CatalogVisualSerializer(result, many=True).data)

    @extend_schema(operation_id="catalog_visuals_create", parameters=HEADERS, request={"multipart/form-data": VisualUploadSerializer}, responses={201: CatalogVisualSerializer, **ERRORS}, tags=["catalogs"])
    def post(self, request):
        params = _validated(VisualUploadSerializer, request.data)
        with catalog_scope(request, roles=WRITE_ROLES) as org_id:
            result = visuals.save(org_id=org_id, actor_id=verified_request_token(request).user_id,
                system_id=params["system_id"], kind=params["kind"], target_key=params["target_key"],
                upload=params.get("file"), cleared=params["cleared"])
        return Response(CatalogVisualSerializer(result).data, status=201)
