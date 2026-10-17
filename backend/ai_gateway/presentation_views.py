from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_gateway import presentation
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from documents.views import documentary_scope, validate, ERRORS
from pricing.serializers import StrictSerializer


class PresentationPreviewSerializer(StrictSerializer):
    patch = presentation.PresentationPatchSerializer()


class PresentationApplySerializer(PresentationPreviewSerializer):
    before_sig = serializers.RegexField(r"^[a-f0-9]{64}$")
    operation_key = serializers.CharField(min_length=8, max_length=200)


class PresentationPreviewResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    before_sig = serializers.CharField()
    patch = presentation.PresentationPatchSerializer()
    before = serializers.JSONField()
    after = serializers.JSONField()
    changes = serializers.ListField(child=serializers.DictField())
    scope = serializers.CharField()


class PresentationAppliedSerializer(serializers.Serializer):
    operation_id = serializers.UUIDField()
    applied = serializers.BooleanField()
    replayed = serializers.BooleanField()


class PresentationStateSerializer(serializers.Serializer):
    operation_id = serializers.UUIDField(allow_null=True)
    state = serializers.ChoiceField(choices=("PROPOSED", "APPLIED", "UNDONE"))


class PresentationStateView(APIView):
    @extend_schema(operation_id="ai_presentation_state", parameters=[ACTIVE_ORGANIZATION_HEADER,
                   OpenApiParameter("operation_key", str, required=True)],
                   responses={200: PresentationStateSerializer, **ERRORS}, tags=["ai"])
    def get(self, request):
        key = serializers.CharField(min_length=8, max_length=200).run_validation(request.query_params.get("operation_key"))
        with documentary_scope(request, ("OWNER",)) as (token, _, org_id):
            return Response(presentation.operation_state(org_id=org_id, user_id=token.user_id, operation_key=key))


class PresentationPreviewView(APIView):
    @extend_schema(operation_id="ai_presentation_preview", parameters=[ACTIVE_ORGANIZATION_HEADER], request=PresentationPreviewSerializer,
                   responses={200: PresentationPreviewResponseSerializer, **ERRORS}, tags=["ai"])
    def post(self, request):
        data = validate(PresentationPreviewSerializer, request.data)
        with documentary_scope(request, ("OWNER",)) as (token, _, org_id):
            return Response(presentation.preview(org_id=org_id, user_id=token.user_id, **data))


class PresentationApplyView(APIView):
    @extend_schema(operation_id="ai_presentation_apply", parameters=[ACTIVE_ORGANIZATION_HEADER], request=PresentationApplySerializer,
                   responses={200: PresentationAppliedSerializer, **ERRORS}, tags=["ai"])
    def post(self, request):
        data = validate(PresentationApplySerializer, request.data)
        with documentary_scope(request, ("OWNER",)) as (token, _, org_id):
            return Response(presentation.apply(org_id=org_id, user_id=token.user_id, **data))


class PresentationUndoView(APIView):
    @extend_schema(operation_id="ai_presentation_undo", parameters=[ACTIVE_ORGANIZATION_HEADER], request=None,
                   responses={200: PresentationAppliedSerializer, **ERRORS}, tags=["ai"])
    def post(self, request, operation_id):
        with documentary_scope(request, ("OWNER",)) as (token, _, org_id):
            return Response(presentation.undo(org_id=org_id, user_id=token.user_id, operation_id=operation_id))
