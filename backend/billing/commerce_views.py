"""Authorized OWNER selections and human confirmation over server-frozen offers."""

from contextlib import contextmanager

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView

from authentication.errors import contract_error
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from billing import commerce, changes, customers, offers, wallet
from billing.flow import FlowError
from billing.repository import rows
from billing.serializers import (CheckoutInputSerializer, CheckoutResultSerializer, CommerceSerializer,
    ChangeInputSerializer, ChangeResultSerializer, ConfirmChangeSerializer, BillingSerializer,
    FlowConfirmationSerializer, FlowAcknowledgementSerializer)
from billing.views import FlowConfirmationView
from dekopen_engine.commercial import PricingError
from pricing.views import scope, validate, ERRORS
from projects.views import response


@contextmanager
def errors():
    try:
        yield
    except FlowError as error:
        raise contract_error(503 if error.uncertain or error.code in ('flow_unavailable','flow_not_configured') else 409,
                             error.code,'La operación requiere revisar su estado o configuración antes de continuar.') from None
    except PricingError as error:
        raise contract_error(404,error.code,'La selección no está disponible para tu organización.') from None


def _owner(request):
    # Network dispatch must be outside this transaction so its once-only claim commits.
    with scope(request,('OWNER',)) as (token,tenant,org):
        return token,tenant,org


def public_operation(operation):
    authority=operation['authority']
    return dict(id=operation['id'],state=operation['state'],kind=authority.get('transition','cancel'),
                effective_at=authority['period_end'] if authority.get('transition')!='upgrade' else None,
                amount=str(operation['preview']['balance']['amount']) if operation['preview'] else None,currency='CLP',
                product_code=authority.get('target',{}).get('product_code'))


class CommerceView(APIView):
    @extend_schema(operation_id='commerce_retrieve',tags=['billing'],parameters=[ACTIVE_ORGANIZATION_HEADER],
                   responses={200:CommerceSerializer,**ERRORS})
    def get(self,request):
        with errors():
            _,_,org=_owner(request)
            with wallet.financial_transaction(org):
                registration=rows('SELECT registration_state FROM public.flow_customer_operations WHERE org_id=%s '
                                   'AND provider_environment=%s',[org,'sandbox' if settings.FLOW_API_URL=='https://sandbox.flow.cl/api' else 'production'])
                pending=rows("SELECT * FROM public.flow_lifecycle_operations WHERE org_id=%s "
                             "AND kind IN ('change','cancel') AND state IN ('prepared','dispatching','uncertain') "
                             'ORDER BY created_at',[org])
                reconciliation=rows('SELECT id FROM public.billing_invoice_observations WHERE org_id=%s LIMIT 1',[org])
                scheduled=rows("SELECT o.* FROM public.flow_lifecycle_operations o JOIN public.billing_lifecycle_events e "
                               "ON e.org_id=o.org_id AND e.operation_key='flow:' || o.id::text "
                               "WHERE o.org_id=%s AND o.state='confirmed' AND o.kind IN ('change','cancel') "
                               'AND e.effective_at>%s ORDER BY e.effective_at',[org,timezone.now()])
            return response(dict(offers=offers.public(org),checkouts=commerce.checkouts(org),
                                 pending_change=public_operation(pending[0]) if pending else None,
                                 scheduled_changes=[public_operation(item) for item in scheduled],
                                 reconciliation_required=bool(reconciliation),
                                 registration_state=registration[0]['registration_state'] if registration else None))


class CheckoutView(APIView):
    @extend_schema(operation_id='billing_checkout',tags=['billing'],parameters=[ACTIVE_ORGANIZATION_HEADER],
                   request=CheckoutInputSerializer,responses={200:CheckoutResultSerializer,**ERRORS})
    def post(self,request):
        with errors():
            token,tenant,org=_owner(request)
            data=validate(CheckoutInputSerializer,request.data)
            client,callback,frontend,zone=offers.runtime()
            return response(commerce.checkout(org,token.user_id,**data,customer_name=tenant.active_organization.organization_name,
                customer_email=token.email,client=client,callback_origin=callback,frontend_origin=frontend,provider_timezone=zone))


class ChangePreviewView(APIView):
    @extend_schema(operation_id='billing_change_preview',tags=['billing'],parameters=[ACTIVE_ORGANIZATION_HEADER],
                   request=ChangeInputSerializer,responses={200:ChangeResultSerializer,**ERRORS})
    def post(self,request):
        with errors():
            _,_,org=_owner(request)
            data=validate(ChangeInputSerializer,request.data)
            client,_,_,zone=offers.runtime()
            if data['cancel']:
                if data.get('offer_id'):
                    raise contract_error(400,'invalid_change','Selecciona un cambio o una cancelación.')
                operation=changes.prepare_cancel(org,operation_key=str(data['operation_key']),client=client,provider_timezone=zone)
            else:
                if not data.get('offer_id'):
                    raise contract_error(400,'invalid_change','Selecciona un plan.')
                target=offers.get(org,data['offer_id'],commerce._environment(client))
                if target['kind']!='subscription':
                    raise contract_error(400,'invalid_change','Selecciona un plan.')
                operation=changes.prepare_change(org,operation_key=str(data['operation_key']),target=target,client=client,provider_timezone=zone)
            return response(public_operation(operation))


class ChangeConfirmView(APIView):
    @extend_schema(operation_id='billing_change_confirm',tags=['billing'],parameters=[ACTIVE_ORGANIZATION_HEADER],
                   request=ConfirmChangeSerializer,responses={200:ChangeResultSerializer,**ERRORS})
    def post(self,request):
        with errors():
            _,_,org=_owner(request)
            data=validate(ConfirmChangeSerializer,request.data)
            client,_,_,_=offers.runtime()
            operation=changes._read(org,data['operation_id'])
            if operation['kind'] not in ('change','cancel'):
                raise contract_error(400,'invalid_change','La operación no corresponde a un cambio de plan.')
            if operation['state'] in ('dispatching','uncertain'):
                changes.recover(org,data['operation_id'],client)
            else:
                changes.dispatch(org,data['operation_id'],client)
            return response(public_operation(changes._read(org,data['operation_id'])))


class BillingSyncView(APIView):
    @extend_schema(operation_id='billing_sync',tags=['billing'],parameters=[ACTIVE_ORGANIZATION_HEADER],
                   request=None,responses={200:BillingSerializer,**ERRORS})
    def post(self,request):
        with errors():
            _,_,org=_owner(request)
            client,_,_,zone=offers.runtime()
            return response(commerce.sync(org,client,provider_timezone=zone))


class FlowPlanConfirmationView(FlowConfirmationView):
    @extend_schema(operation_id='flow_subscription_confirm',tags=['billing'],request=FlowConfirmationSerializer,
                   responses={200:FlowAcknowledgementSerializer,**ERRORS})
    def post(self,request,offer_id):
        with errors():
            data=validate(FlowConfirmationSerializer,request.data)
            if len(request.data.getlist('token'))!=1:
                raise contract_error(400,'invalid_flow_callback','La confirmación requiere un token válido.')
            client,_,_,zone=offers.runtime()
            commerce.callback(offer_id,data['token'],client,zone)
            return response({'received':True})


class RegistrationReturnView(FlowConfirmationView):
    @extend_schema(operation_id='flow_registration_return',tags=['billing'],request=FlowConfirmationSerializer,
                   responses={303:None,**ERRORS})
    def post(self,request,operation_id):
        with errors():
            data=validate(FlowConfirmationSerializer,request.data)
            if len(request.data.getlist('token'))!=1:
                raise contract_error(400,'invalid_flow_callback','La confirmación requiere un token válido.')
            client,_,frontend,_=offers.runtime()
            customers.confirm_callback(operation_id,data['token'],client)
            result=HttpResponseRedirect(frontend+'/settings/billing')
            result.status_code=303
            result['Cache-Control']='no-store'
            return result


class ChangeAbandonView(APIView):
    @extend_schema(operation_id='billing_change_abandon',tags=['billing'],parameters=[ACTIVE_ORGANIZATION_HEADER],
                   request=ConfirmChangeSerializer,responses={200:ChangeResultSerializer,**ERRORS})
    def post(self,request):
        with errors():
            _,_,org=_owner(request)
            data=validate(ConfirmChangeSerializer,request.data)
            changes.abandon(org,data['operation_id'])
            return response(public_operation(changes._read(org,data['operation_id'])))
