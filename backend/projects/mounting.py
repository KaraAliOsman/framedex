"""Sourced mounting rules and revision-bound, append-only survey evidence."""

from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from zoneinfo import ZoneInfo

from drf_spectacular.utils import extend_schema
from pydantic import TypeAdapter
from rest_framework import serializers
from rest_framework.views import APIView

from authentication.errors import contract_error
from dekopen_engine.commercial import PricingError
from dekopen_engine.documentary_canonical import documentary_canonical_json_v1
from dekopen_engine.finishes import finish_selling_delta
from dekopen_engine.mounting import MountingRule, OpeningSurvey, derive_fabrication, resize_contour, validate_mounting_extras
from engine_api.adapter import elevation_envelope, parse_product_model
from pricing.repository import json_text, one, rows
from pricing.serializers import StrictSerializer, PriceRequestSerializer
from pricing.views import DecimalJSONParser, ERRORS, scope, validate
from projects.extras import extra_backend
from projects.serializers import PositionDesignSerializer
from projects.views import SCHEMA, response

SURVEYS = TypeAdapter(list[OpeningSurvey])


def binding(design):
    return sha256(documentary_canonical_json_v1(design)).hexdigest()


def rules_for(org_id, system_id):
    with extra_backend():
        return rows("SELECT DISTINCT ON(code) code,revision,rule::text FROM public.mounting_rules "
                    "WHERE org_id=%s AND system_id=%s ORDER BY code,revision DESC",[org_id,system_id])


def public_rules(org_id, system_id):
    return [{'revision':item['revision'],'rule':MountingRule.model_validate_json(item['rule']).model_dump(mode='json')}
            for item in rules_for(org_id,system_id)]


def derive_design(org_id, design, surveys, *, stored_evidence=None):
    """The preview and save boundary run the same exact derivation."""
    design = deepcopy(design)
    tree = design['parametric_tree']
    assembly = tree.get('version') == 'product-v2'
    modules = tree['assembly']['modules'] if assembly else [{'id':None,'width_mm':design['nominal_width_mm'],
                                                          'height_mm':design['nominal_height_mm'],'tree':tree}]
    targets = {module['id'] for module in modules}
    if not surveys or len({item.module_id for item in surveys}) != len(surveys) or any(item.module_id not in targets for item in surveys):
        raise contract_error(422,'survey_target_invalid','Cada medición debe corresponder a un marco distinto del diseño.')
    latest = {item['code']:item for item in rules_for(org_id,design['system_id'])}
    from engine_api.repository import SystemParamsRepository
    with extra_backend():
        params = SystemParamsRepository().load_visible(design['system_id'],org_id)
    evidence = []
    for survey in surveys:
        original = next((item for item in stored_evidence or [] if item['survey']['module_id']==survey.module_id
                         and item['survey']['rule_code']==survey.rule_code
                         and item['survey']['rule_revision']==survey.rule_revision),None)
        found = latest.get(survey.rule_code)
        if original:
            rule = MountingRule.model_validate(original['rule'])
        elif found and found['revision']==survey.rule_revision:
            rule = MountingRule.model_validate_json(found['rule'])
        else:
            raise contract_error(409,'mounting_rule_stale','La regla cambió o no está declarada. Recarga Vano y montaje.')
        try:
            validate_mounting_extras(rule,params.extra_authority)
            result = derive_fabrication(survey,rule)
        except ValueError as error:
            raise contract_error(422,'mounting_measurement_invalid',str(error)) from error
        module = next(item for item in modules if item['id']==survey.module_id)
        width,height = result.width.fabrication_mm,result.height.fabrication_mm
        if module.get('contour'):
            module['contour'] = resize_contour(module['contour'],Decimal(str(module['width_mm'])),
                                              Decimal(str(module['height_mm'])),width,height)
        module['width_mm'],module['height_mm'] = str(width),str(height)
        intent = module['tree']
        required = {item.code:item.model_dump(mode='json') for item in rule.extras}
        existing = {item['code']:item for item in intent.get('extras',[])}
        if existing or required:
            intent['extras'] = list((existing | required).values())
        evidence.append({'survey':survey.model_dump(mode='json'), 'rule':rule.model_dump(mode='json'),
                         'result':result.model_dump(mode='json')})
    if assembly:
        width,height = elevation_envelope(parse_product_model(tree).assembly)
    else:
        width,height = Decimal(modules[0]['width_mm']),Decimal(modules[0]['height_mm'])
    design['nominal_width_mm'],design['nominal_height_mm'] = width,height
    return design,evidence


def measurement_record(org_id, position_id, revision):
    with extra_backend():
        found = rows("SELECT id,generation,measurements::text,binding,state,actor_id,reason,created_at,price_change::text "
                     "FROM public.position_measurements WHERE org_id=%s AND position_id=%s AND revision_code=%s "
                     "ORDER BY generation DESC LIMIT 1",[org_id,position_id,revision])
    if not found:
        return None
    from pricing.service import decoded
    return {**found[0],'measurements':decoded(found[0]['measurements']), 'price_change':decoded(found[0]['price_change']) if found[0]['price_change'] else None}


def measurement_public(org_id, position_id, design, revision):
    record = measurement_record(org_id,position_id,revision)
    return {**record,'current':record['binding']==binding(design)} if record else None


def append_measurement(org_id, position, revision, evidence, state, reason, price_change=None):
    from projects.service import position_public
    design = position_public(position)['design']
    with extra_backend():
        current = measurement_record(org_id,position['id'],revision)
        return one("INSERT INTO public.position_measurements(org_id,project_id,position_id,revision_code,generation,"
                   "measurements,binding,state,actor_id,reason,price_change) VALUES(%s,%s,%s,%s,%s,%s::jsonb,%s,%s,(current_setting('request.jwt.claims',true)::jsonb->>'sub')::uuid,%s,%s::jsonb) RETURNING id",
                   [org_id,position['project_id'],position['id'],revision,1 if current is None else current['generation']+1,
                    json_text(evidence),binding(design),state,reason,json_text(price_change)])


def save_measurements(org_id, position, data):
    from projects.service import project_row
    if 'measurements' not in data:
        return
    revision = project_row(org_id,position['project_id'])['current_revision']
    surveys = SURVEYS.validate_json(json_text(data['measurements']))
    current = measurement_record(org_id,position['id'],revision)
    _,evidence = derive_design(org_id,data['design'],surveys,stored_evidence=current['measurements'] if current else None)
    from projects.service import position_public
    if current and current['binding']==binding(position_public(position)['design']) and current['measurements']==evidence:
        return
    append_measurement(org_id,position,revision,evidence,
                       'SITE' if all(item.origin=='SITE' for item in surveys) else 'CUSTOMER',
                       data.get('measurement_reason') or 'Medidas de vano guardadas con el diseño')


def copy_measurements(org_id,project_id,before_revision,after_revision):
    from projects.service import position_row
    with extra_backend():
        ids=rows('SELECT id FROM public.project_positions WHERE org_id=%s AND project_id=%s',[org_id,project_id])
    for item in ids:
        record=measurement_record(org_id,item['id'],before_revision)
        position=position_row(org_id,item['id'])
        from projects.service import position_public
        # A successor must not turn stale measurements into current evidence
        # merely by binding them again to a different saved design.
        if record and record['binding']==binding(position_public(position)['design']):
            state='SITE' if all(m['survey']['origin']=='SITE' for m in record['measurements']) else 'CUSTOMER'
            append_measurement(org_id,position,after_revision,record['measurements'],state,
                               'Copiar antecedente a revisión sucesora; requiere nueva confirmación')


class SurveyListField(serializers.JSONField):
    def to_internal_value(self, data):
        try:
            return [item.model_dump(mode='json') for item in SURVEYS.validate_json(json_text(data))]
        except (TypeError,ValueError) as error:
            raise serializers.ValidationError(str(error)) from error


class RuleWriteSerializer(StrictSerializer):
    rule = serializers.JSONField()
    expected_revision = serializers.IntegerField(min_value=0)
    reason = serializers.CharField(max_length=1000)

    def validate_rule(self, value):
        try:
            return MountingRule.model_validate_json(json_text(value)).model_dump(mode='json')
        except (TypeError,ValueError) as error:
            raise serializers.ValidationError(str(error)) from error


class RulesSerializer(serializers.Serializer):
    items = serializers.ListField(child=serializers.JSONField())


class MountingRulesView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(operation_id='mountingRules',responses={200:RulesSerializer,**ERRORS},**SCHEMA)
    def get(self,request,system_id):
        with scope(request,('OWNER','ESTIMATOR','WORKSHOP_MANAGER')) as (_,_,org):
            return response({'items':public_rules(org,system_id)})

    @extend_schema(operation_id='mountingRuleSave',request=RuleWriteSerializer,responses={200:RulesSerializer,**ERRORS},**SCHEMA)
    def put(self,request,system_id):
        data = validate(RuleWriteSerializer,request.data)
        with scope(request,('OWNER','WORKSHOP_MANAGER')) as (token,_,org):
            rule = MountingRule.model_validate(data['rule'])
            with extra_backend():
                rows('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',[str(org)+str(system_id)+rule.code])
                old = next((item for item in rules_for(org,system_id) if item['code']==rule.code),None)
                if data['expected_revision'] != (old['revision'] if old else 0):
                    raise contract_error(409,'mounting_rule_stale','Otra persona cambió la regla. Recarga antes de guardar.')
                # Required extra definitions must actually belong to this series.
                from engine_api.repository import SystemParamsRepository
                params = SystemParamsRepository().load_visible(system_id,org)
                try:
                    validate_mounting_extras(rule,params.extra_authority)
                except ValueError as error:
                    raise contract_error(422,'mounting_extra_missing',str(error)) from error
                one('INSERT INTO public.mounting_rules(org_id,system_id,code,revision,rule,actor_id,reason) '
                    'VALUES(%s,%s,%s,%s,%s::jsonb,%s,%s) RETURNING code',
                    [org,system_id,rule.code,data['expected_revision']+1,json_text(data['rule']),token.user_id,data['reason']])
            return response({'items':public_rules(org,system_id)})


class MountingPreviewSerializer(StrictSerializer):
    design = PositionDesignSerializer()
    measurements = SurveyListField()


class MountingPreviewResponseSerializer(serializers.Serializer):
    design = PositionDesignSerializer()
    measurements = serializers.ListField(child=serializers.JSONField())


class MountingPreviewView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(operation_id='mountingPreview',request=MountingPreviewSerializer,
                   responses={200:MountingPreviewResponseSerializer,**ERRORS},**SCHEMA)
    def post(self,request):
        data = validate(MountingPreviewSerializer,request.data)
        with scope(request,('OWNER','ESTIMATOR')) as (_,_,org):
            try:
                design,evidence = derive_design(org,data['design'],SURVEYS.validate_json(json_text(data['measurements'])))
                from projects.service import calculate_design
                calculate_design(org,design)
                return response({'design':design,'measurements':evidence})
            except ValueError as error:
                raise contract_error(422,'mounting_measurement_invalid',str(error)) from error


class MeasurementConfirmSerializer(StrictSerializer):
    expected_updated_at = serializers.DateTimeField()
    expected_generation = serializers.IntegerField(min_value=1)
    confirmed = serializers.BooleanField()
    acknowledge_warnings = serializers.BooleanField()
    reason = serializers.CharField(max_length=1000)


class MeasurementResponseSerializer(serializers.Serializer):
    measurements = serializers.JSONField(allow_null=True)


class MeasurementConfirmView(APIView):
    @extend_schema(operation_id='measurementConfirm',request=MeasurementConfirmSerializer,
                   responses={200:MeasurementResponseSerializer,**ERRORS},**SCHEMA)
    def post(self,request,position_id):
        from projects.service import position_row,position_public,project_row,unchanged
        data = validate(MeasurementConfirmSerializer,request.data)
        with scope(request,('OWNER','ESTIMATOR','WORKSHOP_MANAGER')) as (_,_,org):
            with extra_backend():
                rows('SELECT private.lock_measurement_target(%s,%s)',[org,position_id])
            position = position_row(org,position_id)
            unchanged(position,data['expected_updated_at'])
            project = project_row(org,position['project_id'])
            record = measurement_public(org,position_id,position_public(position)['design'],project['current_revision'])
            if not data['confirmed'] or not record or not record['current'] or record['generation']!=data['expected_generation']:
                raise contract_error(409,'measurement_confirmation_stale','Guarda y revisa las medidas actuales antes de confirmar.')
            targets = {item['id'] for item in position_public(position)['design']['parametric_tree']['assembly']['modules']} if position_public(position)['design']['parametric_tree'].get('version')=='product-v2' else {None}
            if {item['survey']['module_id'] for item in record['measurements']} != targets:
                raise contract_error(422,'measurement_incomplete','Mide cada marco del conjunto antes de confirmar.')
            if any(item['result']['warnings'] for item in record['measurements']) and not data['acknowledge_warnings']:
                raise contract_error(422,'measurement_warning_ack_required','Revisa y reconoce los avisos antes de confirmar.')
            append_measurement(org,position,project['current_revision'],record['measurements'],'CONFIRMED',data['reason'],record.get('price_change'))
            return response({'measurements':measurement_public(org,position_id,position_public(position)['design'],project['current_revision'])})


class RectificationSerializer(MountingPreviewSerializer):
    expected_updated_at = serializers.DateTimeField()
    expected_current_revision = serializers.RegexField(r'^REV-[A-Z]+$')
    reason = serializers.CharField(max_length=1000)
    confirmed = serializers.BooleanField(default=False)
    proposal_token = serializers.CharField(required=False, max_length=64)


class RectificationResponseSerializer(MountingPreviewResponseSerializer):
    price_change = serializers.JSONField()
    proposal_token = serializers.CharField()
    revision_code = serializers.CharField()
    applied = serializers.BooleanField()


def rectify(org,actor,position_id,data):
    from pricing.service import preview, decoded
    from projects.service import (position_row,project_row,unchanged,_latest_version,
                                  start_successor,save_position,_typology,_pricing_authority)
    project = project_row(org,position_row(org,position_id)['project_id'],lock=True)
    position = position_row(org,position_id,lock=True)
    unchanged(position,data['expected_updated_at'])
    if project['current_revision']!=data['expected_current_revision']:
        raise contract_error(409,'measurement_revision_stale','La revisión cambió. Recarga el proyecto.')
    surveys = SURVEYS.validate_json(json_text(data['measurements']))
    if any(item.origin!='SITE' for item in surveys):
        raise contract_error(422,'site_survey_required','La rectificación requiere medidas tomadas en obra.')
    record = measurement_record(org,position_id,project['current_revision'])
    design,evidence = derive_design(org,data['design'],surveys,
        stored_evidence=record['measurements'] if record else None)
    from projects.service import calculate_design
    bom = calculate_design(org,design)
    latest = _latest_version(org,project['id'])
    sealed = project['status'] in ('QUOTED','APPROVED')
    if project['status'] not in ('DRAFT','QUOTED','APPROVED'):
        raise contract_error(409,'measurement_revision_closed','El proyecto está en producción. Gestiona la corrección con el encargado.')
    price_change = {'before_net':None,'after_net':None,'delta_net':None,'currency':None,'reason':None}
    proposed = {**position,'width_mm':design['nominal_width_mm'],'height_mm':design['nominal_height_mm'],
                'system_id':design['system_id'],'parametric_tree':design['parametric_tree'],
                'typology':_typology(design['parametric_tree']), 'bom_snapshot':bom,
                'color_interior':bom['finish']['interior']['code'] if bom.get('finish') else design['color'],
                'color_exterior':bom['finish']['exterior']['code'] if bom.get('finish') else design['color']}
    with extra_backend():
        all_positions = rows('SELECT * FROM public.project_positions WHERE org_id=%s AND project_id=%s ORDER BY position_index',
                             [org,project['id']])
        if sealed and latest:
            snapshot = decoded(latest['snapshot_json'])
            raw_request = snapshot['pricing']['request']
            before = Decimal(str(snapshot['project']['total_price_net']))
        else:
            rules = one('SELECT * FROM public.pricing_rules WHERE org_id=%s',[org],'pricing_rules_not_found')
            currency = one('SELECT currency FROM public.tenancy_organizations WHERE id=%s',[org])['currency']
            raw_request = {'project_id':str(project['id']),'pricing_mode':rules['pricing_mode'],'context_code':'DEFAULT',
                           'currency':currency,'effective_date':datetime.now(ZoneInfo('America/Santiago')).date().isoformat(),
                           'discount_pct':'0','target_margin':str(rules['default_margin_pct']), 'segment':'RETAIL',
                           'confirmed':True,'reason':data['reason']}
            before = None
        pricing_request = validate(PriceRequestSerializer,raw_request)
        try:
            if before is None:
                before = Decimal(str(preview(org,actor,pricing_request,simulate=True)['project_net']))
            after = preview(org,actor,pricing_request,simulate=True,
                            proposed_positions=[proposed if item['id']==position['id'] else item for item in all_positions])
            after_net = Decimal(str(after['project_net']))
            price_change.update(before_net=str(before),after_net=str(after_net),
                                delta_net=str(finish_selling_delta(before,after_net)),currency=pricing_request['currency'])
        except PricingError as error:
            if sealed:
                raise contract_error(422,error.code,'No se puede comparar la venta sellada: revisa la autoridad comercial antes de rectificar.') from error
            from pricing.service import pricing_public_detail
            price_change['reason'] = pricing_public_detail(error.code)
    result = {'design':design,'measurements':evidence,'price_change':price_change,
              'revision_code':project['current_revision'],'applied':False}
    token = sha256(documentary_canonical_json_v1({'position':str(position_id), 'org':str(org),
        'updated_at':position['updated_at'],'revision':project['current_revision'], 'proposal':result})).hexdigest()
    result['proposal_token'] = token
    if not data['confirmed']:
        return result
    if data.get('proposal_token')!=token:
        raise contract_error(409,'measurement_proposal_stale','La propuesta o su precio cambiaron. Revísala otra vez antes de aplicar.')
    if sealed:
        start_successor(org,project['id'],project['current_revision'])
    elif _pricing_authority(org,project['id'],project['current_revision']):
        raise contract_error(409,'commercial_revision_required','Revisa los precios aplicados antes de rectificar esta revisión en borrador.')
    current = position_row(org,position_id)
    save_position(org,project['id'],{'location_tag':position['location_tag'] or '', 'quantity':position['quantity'],
        'design':design,'expected_updated_at':current['updated_at']},position_id=position_id)
    revision = project_row(org,project['id'])['current_revision']
    append_measurement(org,position_row(org,position_id),revision,evidence,'SITE',data['reason'],price_change)
    return {**result,'revision_code':revision,'applied':True}


class RectificationView(APIView):
    parser_classes = [DecimalJSONParser]

    @extend_schema(operation_id='measurementRectify',request=RectificationSerializer,
                   responses={200:RectificationResponseSerializer,**ERRORS},**SCHEMA)
    def post(self,request,position_id):
        data = validate(RectificationSerializer,request.data)
        with scope(request,('OWNER','ESTIMATOR')) as (_,actor,org):
            return response(rectify(org,actor,position_id,data))
