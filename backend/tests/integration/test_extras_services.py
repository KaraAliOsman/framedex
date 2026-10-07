"""D06 complete seal, actual saw members, services and successor authority."""
from datetime import date
from decimal import Decimal as D
from uuid import UUID
import json

import pytest
from django.db import connection

from backend.tests.integration.test_shot09_documentary import documentary_tenant as documentary_tenant, as_user, _seed_project, _tenant
from catalogs.glass import load_products
from catalogs.readiness import catalog_readiness
from documents.service import prepare_documentary_inputs, save_documentary_inputs, revision_snapshot, freeze_revision_a
from documents.repository import documentary_backend, DocumentaryError
from documents.renderers import _doc01
from engine.tests.extra_cases import installation
from dekopen_engine.extra_models import ExtraPolicy
from pricing.repository import admin_write, commercial_backend, one, rows, json_text
from pricing.service import preview, apply_operation
from production.service import release_production, optimize_work_order, get_work_order
from projects.extras import extra_backend, policy_record, apply_position_defaults, services_response
from projects.serializers import PositionWriteSerializer
from projects.service import create_project, save_position, project_row, start_successor, clone_project

pytestmark=pytest.mark.rls_integration


def fixture(org,owner):
    _seed_project(org,owner)
    with as_user(owner):
        system=one("SELECT id FROM profile_systems WHERE code='DEMO_60' AND version=6")['id']
        assert catalog_readiness(system,org)['quote_ready'], 'Nonstructural extras must remain quoteable with declared cuts and purchase bindings'
        cost_list=one('SELECT id FROM cost_lists WHERE org_id=%s',[org])['id']
        for item in rows('SELECT sku,unit,unit_cost FROM catalog_demo_prices WHERE system_id=%s UNION SELECT commercial_sku,purchase_unit,100 FROM reinforcement_articles WHERE system_id=%s',[system,system]):
            if not rows('SELECT id FROM cost_list_items WHERE cost_list_id=%s AND sku=%s',[cost_list,item['sku']]):
                admin_write('cost-items',org,{'cost_list_id':cost_list,'sku':item['sku'],'unit':item['unit'],'item_type':'FIXTURE','unit_cost':D(item['unit_cost'])},'D06 synthetic price')
        glass=next(row for row in load_products(system,org) if row['technical_sku'].endswith('-GLASS-SAFE'))
        # Glass/process authorities remain the supplied D02 recipe.
        from dekopen_engine.glass_composition import glass_rate_requirements
        for sku,unit in [(glass['technical_sku'],'M2'),*glass_rate_requirements(glass['resolved_product'],None)]:
            if not rows('SELECT id FROM cost_list_items WHERE cost_list_id=%s AND sku=%s',[cost_list,sku]):
                admin_write('cost-items',org,{'cost_list_id':cost_list,'sku':sku,'unit':unit,'item_type':'FIXTURE','unit_cost':D(100)},'D06 glass price')
        design={'system_id':str(system),'nominal_width_mm':'1500','nominal_height_mm':'1400','color':'WHITE',
            'parametric_tree':{'id':'vano','type':'BAY','opening_type':'FIXED','glass_thickness_mm':'24','glass_spec':'4-16-4',
                'glass_article_sku':glass['technical_sku'],'glass_product':glass['resolved_product'].model_dump(mode='json'),'sill_height_mm':'900'}}
        return design


def save_policy(org,policy):
    with extra_backend():
        revision=policy_record(org)['revision']+1
        rows('INSERT INTO organization_extra_settings(org_id,policy,revision) VALUES(%s,%s::jsonb,%s) '
             'ON CONFLICT(org_id) DO UPDATE SET policy=EXCLUDED.policy,revision=EXCLUDED.revision RETURNING revision',[org,json_text(policy.model_dump(mode='json')),revision])


@pytest.mark.parametrize('next_action', ['PRODUCTION', 'SUCCESSOR'])
def test_extras_services_seal_ot_saw_and_policy_drift(documentary_tenant, next_action):
    org,_,users,_=documentary_tenant
    owner=users['OWNER']
    design=fixture(org,owner)
    with as_user(owner):
        project=create_project(org,owner,{'name':'Extras de fachada · DEMO','client_name':'Ensayo','client_rut':'1-9','client_email':'cliente@example.test','delivery_address':'Valdivia'})
        design['parametric_tree']['extras']=[{'code':'SILL','overhang_left_mm':'30','overhang_right_mm':'30'},
            {'code':'FRAME_EXTENSION','sides':['LEFT','RIGHT']},{'code':'SCREEN_FIXED'}]
        serializer=PositionWriteSerializer(data={'location_tag':'Fachada · DEMO','quantity':2,'design':design})
        serializer.is_valid(raise_exception=True)
        position=save_position(org,project['id'],serializer.validated_data)
        assert D(position['bom']['extras'][0]['quantity'])==D('1.56')
        policy=ExtraPolicy(services=[installation()])
        save_policy(org,policy)
        with extra_backend():
            rows('INSERT INTO project_extra_services(org_id,project_id,revision_code,selections) VALUES(%s,%s,%s,%s::jsonb) RETURNING project_id',[org,project['id'],'REV-A',json_text([{'code':'INSTALL'}])])
        prepared=prepare_documentary_inputs(org_id=org,project_id=project['id'])
        inputs=[]
        for pos in prepared['positions']:
            annotations={}
            for row in pos['workshop_suggestions']:
                key=(row['bay_id'],row.get('leaf_id'))
                annotations[key]={**annotations.get(key,{}),**{k:v for k,v in row.items() if v is not None}}
            inputs.append({'position_id':pos['position_id'],'calculation_hash':pos['calculation_hash'],'location_tag':pos['location_tag'],
                'manufacturing_placement_policy_id':pos['placement_options'][0]['id'],'handle_requirement_policy_id':pos['handle_options'][0]['id'],
                'reinforcement_cut_policy_id':pos['reinforcement_options'][0]['id'],'workshop_annotations':list(annotations.values()),
                'structural_inputs':[],'glass_polishing':pos['polishing_suggestions'],'handle_intents':[],
                'accessory_schedule':{'schema_version':1,'coverage':'NONE_REQUIRED','items':[]},'legacy_handle_migration_confirmed':True})
        save_documentary_inputs(org_id=org,actor_id=owner,project_id=project['id'],data={'payment_terms':'Anticipo 50 %','quotation_valid_until':date(2026,10,25),'positions':inputs})
        request={'project_id':project['id'],'pricing_mode':'COST_PLUS_MARGIN','currency':'CLP','effective_date':date(2026,10,6),
            'context_code':'DEFAULT','discount_pct':D(0),'target_margin':D('0.35'),'segment':'RETAIL','confirmed':False,'reason':'D06 price','_actor_id':owner}
        with commercial_backend():
            stale=preview(org,_tenant(org,'OWNER'),request)
        save_policy(org,policy.model_copy(update={'document_prices':'GROUPED'}))
        from dekopen_engine.commercial import PricingError
        with commercial_backend(),pytest.raises(PricingError,match='stale_pricing_operation'):
            apply_operation(org,owner,'OWNER',UUID(stale['id']),'D06 stale',False)
        save_policy(org,policy)
        with commercial_backend():
            priced=preview(org,_tenant(org,'OWNER'),request)
            assert D(priced['services'][0]['quantity'])==D('11.6')
            detail=priced['line_detail'][0]
            assert D(detail['base_net'])+sum((D(row['net']) for row in detail['sublines']),D(0))==D(dict(priced['lines'])[detail['position_index']])
            operation=one('SELECT input_snapshot FROM pricing_operations WHERE id=%s',[priced['id']])
            snapshot=operation['input_snapshot']
            if isinstance(snapshot,str):
                snapshot=json.loads(snapshot)
            assert snapshot['positions'][0]['installation_rate_per_m2']=='0'
            apply_operation(org,owner,'OWNER',UUID(priced['id']),'D06 apply',False)
        # New policy cannot reprice a closed/applied revision or its PDF.
        save_policy(org,ExtraPolicy())
        closed=services_response(org,project_row(org,project['id']))
        assert closed['locked'] and closed['lines'][0]['amount']=='17400' and closed['definitions']
        try:
            frozen=freeze_revision_a(org_id=org,actor_id=owner,project_id=project['id'],pricing_operation_id=UUID(priced['id']),confirmed=True,allow_incomplete_workshop=True)
        except DocumentaryError as error:
            pytest.fail(str(error.extra))
        _,sealed=revision_snapshot(org_id=org,version_id=UUID(frozen['id']))
        assert frozen['production_allowed'] and frozen['documentary_complete']
        html=_doc01(sealed)
        assert 'Vierteaguas' in html and 'Instalación estándar' in html and 'Extras incluidos' in html
        assert 'FRAME_EXTENSION' not in html and 'SCREEN_FIXED' not in html
        save_policy(org,policy)
        copied=clone_project(org,owner,project['id'],{'expected_updated_at':project_row(org,project['id'])['updated_at']})
        copied_services=services_response(org,project_row(org,UUID(str(copied['id']))))
        assert not copied_services['locked'] and copied_services['selections'][0]['code']=='INSTALL'
        if next_action=='SUCCESSOR':
            successor=start_successor(org,project['id'],'REV-A')
            assert successor['current_revision']=='REV-B'
            successor_services=services_response(org,project_row(org,project['id']))
            assert not successor_services['locked'] and successor_services['selections'][0]['code']=='INSTALL'
            _,after=revision_snapshot(org_id=org,version_id=UUID(frozen['id']))
            assert after==sealed
            return
        released=release_production(org_id=org,version_id=UUID(frozen['id']),actor_id=owner)
        assert released['orders']
        for order in released['orders']:
            detail=get_work_order(org_id=org,order_id=UUID(order['id']))
            assert detail['payload']['materials']['extras']
            plan=optimize_work_order(org_id=org,order_id=UUID(order['id']),actor_id=owner,color='',strategy='fast')
            assert 'EXTRA-FRAME_EXTENSION' in json_text(plan)
        with documentary_backend():
            requirements=rows("SELECT technical_identity,purchasing_sku,specification FROM purchase_requirement_lines WHERE project_version_id=%s AND org_id=%s AND order_type='SUPPLIER_PROFILE_PO'",[frozen['id'],org])
            assert 'EXTRA-FRAME_EXTENSION' in json_text(requirements)
        _,after=revision_snapshot(org_id=org,version_id=UUID(frozen['id']))
        assert after==sealed


def test_new_position_template_is_motor_intent_not_a_past_revision_rewrite(documentary_tenant):
    org,_,users,_=documentary_tenant
    owner=users['OWNER']
    design=fixture(org,owner)
    with as_user(owner):
        save_policy(org,ExtraPolicy(services=[installation(scope='POSITION')],position_defaults=[{'code':'INSTALL'}]))
        effective=apply_position_defaults(org,design)
        assert effective['parametric_tree']['extras'][0]['code']=='INSTALL'
        assert 'extras' not in design['parametric_tree']
        project=create_project(org,owner,{'name':'Plantilla nueva · DEMO','client_name':'Ensayo'})
        serializer=PositionWriteSerializer(data={'location_tag':'Patio · DEMO','quantity':1,'design':design})
        serializer.is_valid(raise_exception=True)
        saved=save_position(org,project['id'],serializer.validated_data)
        assert saved['design']['parametric_tree']['extras'][0]['code']=='INSTALL'
        assert D(saved['bom']['extras'][0]['quantity'])==D('5.8')


def test_services_without_fx_keep_selection_and_explain_the_missing_authority(documentary_tenant):
    org,_,users,_=documentary_tenant
    owner=users['OWNER']
    design=fixture(org,owner)
    # Fixture setup stays outside the member role; production code never
    # broadens organization update permissions to resolve a missing rate.
    with connection.cursor() as cursor:
        cursor.execute("UPDATE public.tenancy_organizations SET currency='USD' WHERE id=%s",[org])
    with as_user(owner):
        project=create_project(org,owner,{'name':'Servicios en otra moneda · DEMO','client_name':'Ensayo'})
        serializer=PositionWriteSerializer(data={'location_tag':'Patio · DEMO','quantity':2,'design':design})
        serializer.is_valid(raise_exception=True)
        save_position(org,project['id'],serializer.validated_data)
        save_policy(org,ExtraPolicy(services=[installation()]))
        with extra_backend():
            rows('INSERT INTO project_extra_services(org_id,project_id,revision_code,selections) '
                 'VALUES(%s,%s,%s,%s::jsonb) RETURNING project_id',
                 [org,project['id'],'REV-A',json_text([{'code':'INSTALL'}])])
        response=services_response(org,project_row(org,project['id']))
        assert response['currency']=='USD' and response['lines']==[]
        assert response['selections'][0]['code']=='INSTALL'
        assert response['reason'].startswith('Sin dato: Falta la cotización de moneda')
        assert 'regístrala antes de cotizar en otra moneda' in response['reason']
        assert 'missing_fx_authority' not in response['reason']
