"""Authenticated pricing endpoints with separate public and confidential data."""

from contextlib import contextmanager
from decimal import Decimal
import json
import logging

from django.db import DatabaseError
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.errors import contract_error
from authentication.rls import authenticated_rls_context
from authentication.serializers import ACTIVE_ORGANIZATION_HEADER, ErrorResponseSerializer
from authentication.tenancy import MembershipRepository, enforce_owner_mfa, resolve_tenant_context
from authentication.views import verified_request_token
from dekopen_engine.commercial import PricingError
from engine_api.adapter import calculate_from_api, UnsupportedEngineContract
from engine_api.repository import SystemParamsRepository, UnsupportedCatalogContract, SystemNotFound
from pricing.repository import (admin_list, admin_write, audit_reason, commercial_backend,
                                json_text, one, rows)
from pricing.serializers import (
    AdminResponseSerializer, AdminWriteSerializer, ApplySerializer, DraftProjectSerializer,
    DraftResponseSerializer, PriceRequestSerializer, PriceResponseSerializer, RESOURCE_SERIALIZERS,
    ImportRequestSerializer,
)
from pricing.service import apply_operation, operation_public, preview
from pricing.xlsx_import import import_rows, parse_xlsx

logger = logging.getLogger(__name__)
ERRORS = {code:OpenApiResponse(ErrorResponseSerializer) for code in (400,401,403,404,409,422,503)}


class DecimalJSONParser(JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        try:
            return json.load(stream,parse_float=Decimal,
                             parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite')))
        except (ValueError,UnicodeDecodeError) as error:
            raise contract_error(400,'invalid_json','Revisa el formato de los datos.') from error


def validate(serializer_type, data):
    serializer = serializer_type(data=data)
    if not serializer.is_valid():
        raise contract_error(400,'validation_error','Revisa los campos y los valores ingresados.')
    return serializer.validated_data


@contextmanager
def scope(request, allowed=('OWNER',)):
    token = verified_request_token(request)
    try:
        with authenticated_rls_context(token.claims):
            tenant = resolve_tenant_context(MembershipRepository().list_active_for_user(token.user_id),
                                            request.headers.get('X-Organization-ID'))
            enforce_owner_mfa(tenant,token.aal)
            if tenant.active_organization.role not in allowed:
                raise PricingError('pricing_permission_denied')
            yield token,tenant,tenant.active_organization.organization_id
    except PricingError as error:
        forbidden = error.code in ('pricing_permission_denied','owner_confirmation_required','owner_approval_required')
        raise contract_error(403 if forbidden else 422,error.code,
                             'La operación comercial requiere revisar sus permisos, datos o configuración.') from error
    except (UnsupportedEngineContract,UnsupportedCatalogContract,SystemNotFound) as error:
        raise contract_error(422,'technical_authority_required','Revisa el diseño y su catálogo técnico antes de cotizar.') from error
    except DatabaseError as error:
        cause = error.__cause__
        logger.warning('Pricing transaction rejected (%s, SQLSTATE=%s, constraint=%s)',
            type(error).__name__,getattr(cause,'sqlstate',None),
            getattr(getattr(cause,'diag',None),'constraint_name',None))
        raise contract_error(409,'pricing_transaction_rejected',
                             'No se guardó el cambio. Revisa duplicados, vigencia y permisos; vuelve a cargar los datos.') from error


def price_response(value):
    return {**value,'lines':[{'position_index':index,'line_net':str(amount)} for index,amount in value['lines']],
            'project_net':str(value['project_net']),'project_tax':str(value['project_tax']),
            'project_gross':str(value['project_gross'])}


class AdminView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(operation_id='pricing_admin_list',parameters=[ACTIVE_ORGANIZATION_HEADER],
                   responses={200:AdminResponseSerializer,**ERRORS},tags=['pricing'])
    def get(self,request,resource):
        allowed = ('OWNER','WORKSHOP_MANAGER') if resource in ('cost-lists','cost-items') else ('OWNER',)
        with scope(request,allowed) as (_,_,org):
            output = admin_list(resource,org)
        return Response(json.loads(json_text({'items':output})))

    @extend_schema(operation_id='pricing_admin_write',parameters=[ACTIVE_ORGANIZATION_HEADER],
                   request=AdminWriteSerializer,responses={200:AdminResponseSerializer,**ERRORS},tags=['pricing'])
    def post(self,request,resource):
        data = validate(AdminWriteSerializer,request.data)
        if resource not in RESOURCE_SERIALIZERS:
            raise contract_error(404,'unknown_resource','Configuración no disponible.')
        values = validate(RESOURCE_SERIALIZERS[resource],data['values'])
        with scope(request) as (_,_,org):
            output = admin_write(resource,org,values,data['reason'],data.get('id'))
        return Response(json.loads(json_text({'items':[output]})))


class PreviewView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(operation_id='pricing_preview',parameters=[ACTIVE_ORGANIZATION_HEADER],
                   request=PriceRequestSerializer,responses={200:PriceResponseSerializer,**ERRORS},tags=['pricing'])
    def post(self,request):
        data = validate(PriceRequestSerializer,request.data)
        with scope(request,('OWNER','ESTIMATOR')) as (token,tenant,org):
            data['_actor_id'] = token.user_id
            with commercial_backend():
                output = preview(org,tenant,data)
        return Response(price_response(output))


class ApplyView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(operation_id='pricing_apply',parameters=[ACTIVE_ORGANIZATION_HEADER],
                   request=ApplySerializer,responses={200:PriceResponseSerializer,**ERRORS},tags=['pricing'])
    def post(self,request,operation_id):
        data = validate(ApplySerializer,request.data)
        with scope(request,('OWNER','ESTIMATOR')) as (token,tenant,org):
            with commercial_backend():
                output = apply_operation(org,token.user_id,tenant.active_organization.role,
                                         operation_id,**data)
        return Response(price_response(output))


class OperationsView(APIView):
    @extend_schema(operation_id='pricing_operations',parameters=[ACTIVE_ORGANIZATION_HEADER],
                   responses={200:PriceResponseSerializer(many=True),**ERRORS},tags=['pricing'])
    def get(self,request):
        with scope(request,('OWNER','ESTIMATOR')) as (token,tenant,org):
            with commercial_backend():
                condition = '' if tenant.active_organization.role=='OWNER' else ' AND requested_by=%s'
                parameters = [org] if not condition else [org,token.user_id]
                result = rows('SELECT * FROM public.pricing_operations WHERE org_id=%s'+condition+
                              ' ORDER BY created_at DESC,id LIMIT 100',parameters)
                output = [price_response(operation_public(item)) for item in result]
        return Response(output)


class DraftView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(operation_id='pricing_create_draft',parameters=[ACTIVE_ORGANIZATION_HEADER],
                   request=DraftProjectSerializer,responses={201:DraftResponseSerializer,**ERRORS},tags=['pricing'])
    def post(self,request):
        data = validate(DraftProjectSerializer,request.data)
        with scope(request,('OWNER','ESTIMATOR')) as (token,_,org):
            audit_reason(data['reason'])
            project = one('INSERT INTO public.projects(org_id,code,name,client_name,created_by) '
                          'VALUES(%s,%s,%s,%s,%s) RETURNING id',
                          [org,data['code'],data['name'],data['client_name'],token.user_id])
            for position in data['positions']:
                params = SystemParamsRepository().load_visible(position['system_id'],org)
                arguments = {key:position[key] for key in ('parametric_tree','nominal_width_mm','nominal_height_mm','color')}
                result = calculate_from_api(**arguments,params=params)
                one('INSERT INTO public.project_positions(project_id,org_id,position_index,quantity,typology,'
                    'system_id,width_mm,height_mm,parametric_tree,bom_snapshot,color_interior,color_exterior) '
                    'VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s) RETURNING id',
                    [project['id'],org,position['position_index'],position['quantity'],position['typology'],
                     position['system_id'],position['nominal_width_mm'],position['nominal_height_mm'],
                     json_text(position['parametric_tree']),result.model_dump_json(),position['color'],position['color']])
        return Response({'id':str(project['id'])},status=201)


class ImportView(APIView):
    parser_classes = [MultiPartParser]

    @extend_schema(operation_id='pricing_import_xlsx',parameters=[ACTIVE_ORGANIZATION_HEADER],
                   request=ImportRequestSerializer,
                   responses={200:AdminResponseSerializer,**ERRORS},tags=['pricing'])
    def post(self,request):
        with scope(request) as (_,_,org):
            try:
                upload = request.FILES['file']
                mapping = json.loads(request.data['mapping'])
                parsed = parse_xlsx(upload.read(5*1024*1024+1),mapping,request.data.get('decimal_separator','.'))
                output = import_rows(org,request.data['cost_list_id'],parsed,request.data['reason'],
                                     request.data.get('apply')=='true')
            except (KeyError,ValueError,TypeError) as error:
                if isinstance(error,PricingError):
                    raise
                raise PricingError('invalid_import_request') from error
        return Response(json.loads(json_text({'items':output})))
