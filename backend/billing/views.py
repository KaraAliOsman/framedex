from drf_spectacular.utils import extend_schema
from django.conf import settings
from rest_framework.parsers import FormParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from billing import wallet, customers
from billing.serializers import WalletSerializer, BillingSerializer
from pricing.views import scope, ERRORS
from projects.views import response
from authentication.errors import contract_error
from billing.flow import FlowClient, FlowError
from billing.settlement import confirm
from billing.serializers import FlowConfirmationSerializer, FlowAcknowledgementSerializer


class WalletView(APIView):
    @extend_schema(operation_id='wallet_retrieve', tags=['billing'],
                   parameters=[ACTIVE_ORGANIZATION_HEADER], responses={200: WalletSerializer, **ERRORS})
    def get(self, request):
        with scope(request, ('OWNER',)) as (_, _, org):
            return response(wallet.summary(org))


class BillingView(APIView):
    @extend_schema(operation_id='billing_retrieve', tags=['billing'],
                   parameters=[ACTIVE_ORGANIZATION_HEADER], responses={200: BillingSerializer, **ERRORS})
    def get(self, request):
        with scope(request, ('OWNER',)) as (_, _, org):
            return response(wallet.billing_summary(org))


class FlowConfirmationView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = [FormParser]

    @extend_schema(operation_id='flow_payment_confirm', tags=['billing'],
                   request=FlowConfirmationSerializer,
                   responses={200: FlowAcknowledgementSerializer, **ERRORS})
    def post(self, request, order_id):
        data = FlowConfirmationSerializer(data=request.data)
        if not data.is_valid() or len(request.data.getlist('token')) != 1:
            raise contract_error(400, 'invalid_flow_callback', 'La confirmación requiere un token válido.')
        try:
            client = FlowClient(api_url=settings.FLOW_API_URL, api_key=settings.FLOW_API_KEY,
                                secret_key=settings.FLOW_SECRET_KEY)
            confirm(order_id, data.validated_data['token'], client)
        except FlowError as error:
            raise contract_error(404 if error.code == 'flow_unknown_order' else 503,
                                 error.code, 'El pago requiere confirmación del proveedor.') from None
        return response({'received': True})


class FlowRegistrationView(FlowConfirmationView):
    @extend_schema(operation_id='flow_registration_confirm', tags=['billing'],
                   request=FlowConfirmationSerializer,
                   responses={200: FlowAcknowledgementSerializer, **ERRORS})
    def post(self, request, operation_id):
        data = FlowConfirmationSerializer(data=request.data)
        if not data.is_valid() or len(request.data.getlist('token')) != 1:
            raise contract_error(400, 'invalid_flow_callback', 'La confirmación requiere un token válido.')
        try:
            client = FlowClient(api_url=settings.FLOW_API_URL, api_key=settings.FLOW_API_KEY,
                                secret_key=settings.FLOW_SECRET_KEY)
            customers.confirm_callback(operation_id, data.validated_data['token'], client)
        except FlowError as error:
            raise contract_error(404 if error.code == 'flow_unknown_customer_operation' else 503,
                                 error.code, 'El registro requiere confirmación del proveedor.') from None
        return response({'received': True})
