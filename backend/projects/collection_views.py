from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from pricing.views import DecimalJSONParser, ERRORS, scope, validate
from projects import collection_settings, fiscal_adapter, simulated_flow, collection_reminders
from notifications.serializers import MailRecordSerializer
from projects.collection_serializers import (
    CollectionIntegrationSerializer, CollectionSettingsRequestSerializer,
    FiscalSimulationRequestSerializer, FiscalSimulationSerializer, FiscalSimulationsSerializer,
    FlowSimulationRequestSerializer, FlowSimulationSerializer,
    CollectionReminderSerializer, CollectionReminderSendSerializer,
)
from projects.views import READ_ROLES, SCHEMA, WRITE_ROLES, response


class CollectionSettingsView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(operation_id="collection_integrations", responses={200: CollectionIntegrationSerializer, **ERRORS}, **SCHEMA)
    def get(self, request):
        with scope(request, READ_ROLES) as (_, _, org):
            return response(collection_settings.status(org))

    @extend_schema(operation_id="collection_settings_save", request=CollectionSettingsRequestSerializer,
                   responses={200: CollectionIntegrationSerializer, **ERRORS}, **SCHEMA)
    def put(self, request):
        data = validate(CollectionSettingsRequestSerializer, request.data)
        with scope(request, ("OWNER",)) as (token, _, org):
            return response(collection_settings.save(org_id=org, actor_id=token.user_id, data=data))


class FlowSimulationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    parser_classes = [DecimalJSONParser]

    @extend_schema(operation_id="flow_simulation_status", responses={200: FlowSimulationSerializer, **ERRORS}, tags=["projects"],
                   auth=[], parameters=[OpenApiParameter("token", str, required=True)])
    def get(self, request, link_id):
        return response(simulated_flow.payer_status(link_id=link_id, token=request.query_params.get("token", "")))

    @extend_schema(operation_id="flow_simulation_confirm", request=FlowSimulationRequestSerializer,
                   responses={200: FlowSimulationSerializer, **ERRORS}, tags=["projects"], auth=[])
    def post(self, request, link_id):
        data = validate(FlowSimulationRequestSerializer, request.data)
        return response(simulated_flow.confirm(link_id=link_id, token=data["token"], outcome=data["outcome"]))


class FiscalSimulationView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(operation_id="fiscal_simulations", responses={200: FiscalSimulationsSerializer, **ERRORS}, **SCHEMA)
    def get(self, request, project_id):
        with scope(request, READ_ROLES) as (_, _, org):
            return response(fiscal_adapter.list_simulations(org_id=org, project_id=project_id))

    @extend_schema(operation_id="fiscal_simulate", request=FiscalSimulationRequestSerializer,
                   responses={201: FiscalSimulationSerializer, **ERRORS}, **SCHEMA)
    def post(self, request, project_id):
        data = validate(FiscalSimulationRequestSerializer, request.data)
        with scope(request, WRITE_ROLES) as (token, _, org):
            return response(fiscal_adapter.simulate(org_id=org, project_id=project_id,
                actor_id=token.user_id, actor_label=token.email, data=data), status=201)


class CollectionReminderView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(operation_id="collection_reminder_prepare", request=None,
        responses={200: CollectionReminderSerializer, **ERRORS}, **SCHEMA)
    def post(self, request, project_id):
        with scope(request, ("OWNER",)) as (token, _, org):
            return response(collection_reminders.prepare(org_id=org, project_id=project_id, actor_id=token.user_id))


class CollectionReminderSendView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(operation_id="collection_reminder_send", request=CollectionReminderSendSerializer,
        responses={202: MailRecordSerializer, **ERRORS}, **SCHEMA)
    def post(self, request, project_id):
        data = validate(CollectionReminderSendSerializer, request.data)
        with scope(request, ("OWNER",)) as (token, _, org):
            return response(collection_reminders.send(org_id=org, project_id=project_id, actor_id=token.user_id, data=data), status=202)
