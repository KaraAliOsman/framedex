"""D07: real tenants, sealed measurements, revision sale and workshop gates."""

from decimal import Decimal as D
from uuid import UUID
from urllib.parse import urlencode

import pytest
from django.db import connection, DatabaseError, transaction
from rest_framework.test import APIClient

from backend.tests.integration.test_shot09_documentary import (
    documentary_tenant as documentary_tenant, as_user, _seed_project, _freeze, _tenant, _freeze_token,
)
from authentication.types import SupabaseUser
from backend.tests.integration.test_extras_services import fixture
from authentication.errors import ContractAPIException
from documents.repository import DocumentaryError
from documents.service import revision_snapshot
from pricing.repository import one, rows, json_text
from pricing.serializers import PriceRequestSerializer
from pricing.service import preview
from projects.extras import extra_backend
from projects.mounting import SURVEYS, derive_design, measurement_public, measurement_record, rectify, append_measurement, copy_measurements
from projects.serializers import PositionWriteSerializer
from projects.service import create_project, save_position, position_row, position_public, project_row
from production.service import release_production

pytestmark=pytest.mark.rls_integration


def client_for(user):
    # Force-authenticated requests share the fixture's outer transaction;
    # mirror a fresh PostgREST request instead of retaining as_user's GUC.
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('request.jwt.claim.sub',%s,true)",[str(user)])
    client=APIClient()
    client.force_authenticate(user=SupabaseUser(id=user,email='mounting@example.test'),token=_freeze_token(user))
    return client


def confirm_body(position):
    return {'expected_updated_at':position['updated_at'],'expected_generation':position['measurements']['generation'],
            'confirmed':True,'acknowledge_warnings':True,'reason':'Técnico verificó la obra; ensayo DEMO'}


def seed_rule(org,system,rule):
    with extra_backend():
        one('INSERT INTO mounting_rules(org_id,system_id,code,revision,rule,actor_id,reason) '
            "VALUES(%s,%s,%s,1,%s::jsonb,(current_setting('request.jwt.claims',true)::jsonb->>'sub')::uuid,%s) RETURNING code",
            [org,system,rule['code'],json_text(rule),'Ensayo de montaje explícito'])


def mounting_position(org,owner):
    from engine.tests.mounting_cases import mounting_cases
    design=fixture(org,owner)
    case=mounting_cases()['IN_OPENING']
    with as_user(owner):
        seed_rule(org,design['system_id'],case['rule'])
        surveys=SURVEYS.validate_json(json_text([case['survey']]))
        derived,evidence=derive_design(org,design,surveys)
        project=create_project(org,owner,{'name':'Obra rectificada · DEMO','client_name':'Ensayo'})
        wire={**derived,'nominal_width_mm':str(derived['nominal_width_mm']),'nominal_height_mm':str(derived['nominal_height_mm'])}
        serializer=PositionWriteSerializer(data={'location_tag':'Fachada','quantity':1,'design':wire,
                                                 'measurements':[item.model_dump(mode='json') for item in surveys]})
        serializer.is_valid(raise_exception=True)
        position=save_position(org,project['id'],serializer.validated_data)
        return project,position,surveys,evidence


def test_measurements_are_exact_bound_and_append_only(documentary_tenant):
    org,other,users,other_user=documentary_tenant
    project,position,surveys,evidence=mounting_position(org,users['OWNER'])
    assert D(position['design']['nominal_width_mm'])==D('1500')
    assert position['measurements']['state']=='SITE'
    assert position['measurements']['current'] is True
    with as_user(users['OWNER']):
        record=measurement_record(org,position['id'],'REV-A')
        assert record['actor_id']==users['OWNER']
        assert record['measurements'][0]['result']['width']['spread_mm']=='4'
        with pytest.raises(DatabaseError),transaction.atomic(),extra_backend():
            rows('UPDATE position_measurements SET state=%s WHERE org_id=%s RETURNING id',['CONFIRMED',org])
        with pytest.raises(DatabaseError),transaction.atomic():
            rows("INSERT INTO position_measurements(org_id,project_id,position_id,revision_code,generation,measurements,binding,state,actor_id,reason) "
                 "SELECT org_id,project_id,position_id,revision_code,2,measurements,binding,'CONFIRMED',actor_id,reason FROM position_measurements WHERE org_id=%s RETURNING id",[org])
        with extra_backend():
            assert rows('SELECT * FROM position_measurements WHERE org_id=%s',[other])==[]
        assert measurement_public(org,position['id'],{**position['design'],'nominal_width_mm':'1499'},'REV-A')['current'] is False
    with as_user(other_user):
        assert measurement_record(org,position['id'],'REV-A') is None


def test_saved_geometry_cannot_disagree_with_survey(documentary_tenant):
    org,_,users,_=documentary_tenant
    project,position,surveys,_=mounting_position(org,users['OWNER'])
    with as_user(users['OWNER']):
        serializer=PositionWriteSerializer(data={'location_tag':'Fachada','quantity':1,
            'design':{**position['design'],'nominal_width_mm':'1501'},'measurements':[item.model_dump(mode='json') for item in surveys]})
        serializer.is_valid(raise_exception=True)
        with pytest.raises(ContractAPIException) as error:
            save_position(org,project['id'],{**serializer.validated_data,'expected_updated_at':position_row(org,position['id'])['updated_at']},position_id=position['id'])
        assert error.value.contract_code=='measurement_design_drift'


def test_unconfirmed_sealed_measurements_block_ot_in_service_and_sql(documentary_tenant):
    org,_,users,_=documentary_tenant
    owner=users['OWNER']
    project,position,operation=_seed_project(org,owner)
    with as_user(owner):
        record=measurement_record(org,position,'REV-A')
        append_measurement(org,position_row(org,position),'REV-A',record['measurements'],'CUSTOMER','Medidas aportadas; falta confirmar')
    frozen=_freeze(org,owner,project,operation)
    assert frozen['production_allowed'] is False
    with as_user(users['WORKSHOP_MANAGER']):
        with pytest.raises(DocumentaryError,match='production_measurements_unconfirmed'):
            release_production(org_id=org,version_id=UUID(frozen['id']),actor_id=users['WORKSHOP_MANAGER'])
    # Assert the DB gate itself without relying on the service's refusal.
    with pytest.raises(DatabaseError,match='production_measurements_unconfirmed'),transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO orders(org_id,project_id,order_type,status,project_version_id,payload_json) "
                "VALUES(%s,%s,'WORKSHOP_OT','DRAFT',%s,%s::jsonb)",[org,project,frozen['id'],json_text({'position_id':str(position)})])


def test_rectification_after_approval_opens_successor_with_real_selling_delta(documentary_tenant):
    org,_,users,_=documentary_tenant
    owner=users['OWNER']
    project,position,operation=_seed_project(org,owner)
    frozen=_freeze(org,owner,project,operation)
    with as_user(owner):
        _,before=revision_snapshot(org_id=org,version_id=UUID(frozen['id']))
        from portal.service import approve_internal
        approve_internal(org_id=org,project_id=project,actor_id=owner,actor_label='Responsable del ensayo',note='Cliente aprobó cotización')
    # Independent HTTP requests re-establish verified claims, including MFA.
    with as_user(owner):
        original=position_public(position_row(org,position))
        record=measurement_record(org,position,'REV-A')
        survey={**record['measurements'][0]['survey'],'widths_mm':['1100'],'heights_mm':['1000'],'origin':'SITE'}
        request={'design':original['design'],'measurements':[survey],'expected_updated_at':position_row(org,position)['updated_at'],
            'expected_current_revision':'REV-A','reason':'Medidor rectificó fachada','confirmed':False}
        proposal=rectify(org,_tenant(org,'OWNER'),position,request)
        assert project_row(org,project)['current_revision']=='REV-A'
        assert D(proposal['price_change']['delta_net'])==D(proposal['price_change']['after_net'])-D(proposal['price_change']['before_net'])
        assert D(proposal['price_change']['delta_net'])>0
        with pytest.raises(ContractAPIException):
            rectify(org,_tenant(org,'OWNER'),position,{**request,'confirmed':True,'proposal_token':'0'*64})
        applied=rectify(org,_tenant(org,'OWNER'),position,{**request,'confirmed':True,'proposal_token':proposal['proposal_token']})
        assert applied['revision_code']=='REV-B'
        assert applied['applied'] is True
        assert project_row(org,project)['status']=='DRAFT'
        assert measurement_record(org,position,'REV-B')['state']=='SITE'
        assert measurement_record(org,position,'REV-B')['price_change']==proposal['price_change']
        _,after=revision_snapshot(org_id=org,version_id=UUID(frozen['id']))
        assert before==after
        serializer=PriceRequestSerializer(data=before['pricing']['request'])
        serializer.is_valid(raise_exception=True)
        with extra_backend():
            actual=preview(org,_tenant(org,'OWNER'),{**serializer.validated_data,'_actor_id':owner},simulate=True)
        assert D(actual['project_net'])==D(proposal['price_change']['after_net'])


@pytest.mark.parametrize('role', ['OWNER','ESTIMATOR','WORKSHOP_MANAGER','INSTALLER'])
def test_confirmation_permissions_and_actor_are_real_http_boundaries(documentary_tenant,role):
    org,_,users,_=documentary_tenant
    _,position,_,_=mounting_position(org,users['OWNER'])
    result=client_for(users[role]).post(f"/api/v1/positions/{position['id']}/measurements/confirm/",
        confirm_body(position),format='json',HTTP_X_ORGANIZATION_ID=str(org))
    if role=='INSTALLER':
        assert result.status_code==403,result.content
        return
    assert result.status_code==200,result.content
    data=result.json()['measurements']
    assert data['state']=='CONFIRMED' and data['actor_id']==str(users[role])
    assert data['generation']==position['measurements']['generation']+1


@pytest.mark.parametrize('mutation,code,status', [
    ({'confirmed':False},'measurement_confirmation_stale',409),
    ({'expected_generation':99},'measurement_confirmation_stale',409),
    ({'acknowledge_warnings':False},'measurement_warning_ack_required',422),
    ({'expected_updated_at':'2020-01-01T00:00:00Z'},'stale_edit',409),
])
def test_confirmation_rejects_stale_or_unreviewed_evidence(documentary_tenant,mutation,code,status):
    org,_,users,_=documentary_tenant
    _,position,_,_=mounting_position(org,users['OWNER'])
    result=client_for(users['ESTIMATOR']).post(f"/api/v1/positions/{position['id']}/measurements/confirm/",
        {**confirm_body(position),**mutation},format='json',HTTP_X_ORGANIZATION_ID=str(org))
    assert result.status_code==status,result.content
    assert result.json()['error']['code']==code
    with as_user(users['OWNER']):
        assert measurement_record(org,position['id'],'REV-A')['generation']==1


def test_foreign_confirmation_and_forged_actor_cannot_create_evidence(documentary_tenant):
    org,other,users,other_user=documentary_tenant
    _,position,_,_=mounting_position(org,users['OWNER'])
    result=client_for(other_user).post(f"/api/v1/positions/{position['id']}/measurements/confirm/",
        confirm_body(position),format='json',HTTP_X_ORGANIZATION_ID=str(other))
    assert result.status_code==404,result.content
    with as_user(users['OWNER']),pytest.raises(DatabaseError,match='measurement_actor_invalid'),transaction.atomic(),extra_backend():
        rows("INSERT INTO position_measurements(org_id,project_id,position_id,revision_code,generation,measurements,binding,state,actor_id,reason) "
             "SELECT org_id,project_id,position_id,revision_code,2,measurements,binding,'CONFIRMED',%s,'actor falsificado' FROM position_measurements WHERE position_id=%s RETURNING id",
             [other_user,position['id']])


def test_assembly_confirmation_requires_every_module(documentary_tenant):
    org,_,users,_=documentary_tenant
    project,position,surveys,_=mounting_position(org,users['OWNER'])
    design=position['design']
    tree={'version':'product-v2','assembly':{'modules':[
        {'id':'m1','width_mm':'1500','height_mm':'1200','tree':design['parametric_tree']},
        {'id':'m2','width_mm':'1500','height_mm':'1200','tree':{**design['parametric_tree'],'id':'otro'}}],
        'couplings':[{'id':'c1','angle_deg':'0','coupler_profile_sku':None}]}}
    # Confirming only one of the two frames must never pass.
    with as_user(users['OWNER']):
        derived,_=derive_design(org,{**design,'parametric_tree':tree},[surveys[0].model_copy(update={'module_id':'m1'})])
        wire={**derived,'nominal_width_mm':str(derived['nominal_width_mm']),'nominal_height_mm':str(derived['nominal_height_mm'])}
        data=PositionWriteSerializer(data={'location_tag':'Dos marcos · DEMO','quantity':1,'design':wire,
            'measurements':[surveys[0].model_copy(update={'module_id':'m1'}).model_dump(mode='json')]})
        data.is_valid(raise_exception=True)
        position=save_position(org,project['id'],data.validated_data)
    result=client_for(users['OWNER']).post(f"/api/v1/positions/{position['id']}/measurements/confirm/",
        confirm_body(position),format='json',HTTP_X_ORGANIZATION_ID=str(org))
    assert result.status_code==422,result.content
    assert result.json()['error']['code']=='measurement_incomplete'


def test_rules_require_revision_source_and_physical_extension(documentary_tenant):
    org,_,users,_=documentary_tenant
    _,position,_,evidence=mounting_position(org,users['OWNER'])
    rule=evidence[0]['rule']
    path=f"/api/v1/organization/mounting/{position['design']['system_id']}/"
    body={'rule':rule,'expected_revision':1,'reason':'Revisión explícita de montaje DEMO'}
    assert client_for(users['ESTIMATOR']).put(path,body,format='json',HTTP_X_ORGANIZATION_ID=str(org)).status_code==403
    owner=client_for(users['OWNER'])
    stale=owner.put(path,{**body,'expected_revision':0},format='json',HTTP_X_ORGANIZATION_ID=str(org))
    assert stale.status_code==409 and stale.json()['error']['code']=='mounting_rule_stale'
    missing=owner.put(path,{**body,'rule':{**rule,'source':''}},format='json',HTTP_X_ORGANIZATION_ID=str(org))
    assert missing.status_code==400
    extension={**rule,'left':{**rule['left'],'extension_mm':'20'}}
    invalid=owner.put(path,{**body,'rule':extension},format='json',HTTP_X_ORGANIZATION_ID=str(org))
    assert invalid.status_code==422 and invalid.json()['error']['code']=='mounting_extra_missing'
    extension['extras']=[{'code':'FRAME_EXTENSION','sides':['LEFT'],'decision':'ACCEPT'}]
    accepted=owner.put(path,{**body,'rule':extension},format='json',HTTP_X_ORGANIZATION_ID=str(org))
    assert accepted.status_code==200,accepted.content
    with as_user(users['OWNER']):
        record=measurement_record(org,position['id'],'REV-A')
        assert record['measurements'][0]['survey']['rule_revision']==1
        assert record['measurements'][0]['rule']==rule


def test_draft_position_deletion_preserves_immutable_measurement_evidence(documentary_tenant):
    org,_,users,_=documentary_tenant
    _,position,_,_=mounting_position(org,users['OWNER'])
    with as_user(users['OWNER']):
        before=measurement_record(org,position['id'],'REV-A')
    query=urlencode({'expected_updated_at':position['updated_at']})
    result=client_for(users['ESTIMATOR']).delete(f"/api/v1/positions/{position['id']}/?{query}",
        HTTP_X_ORGANIZATION_ID=str(org))
    assert result.status_code==204,result.content
    with as_user(users['OWNER']):
        assert measurement_record(org,position['id'],'REV-A')==before
        with extra_backend():
            assert not rows('SELECT id FROM project_positions WHERE org_id=%s AND id=%s',[org,position['id']])
    refused=client_for(users['ESTIMATOR']).post(f"/api/v1/positions/{position['id']}/measurements/confirm/",
        confirm_body(position),format='json',HTTP_X_ORGANIZATION_ID=str(org))
    assert refused.status_code==404,refused.content


@pytest.mark.parametrize('mutation,code', [
    ('project_id','measurement_position_invalid'),
    ('generation','measurement_generation_invalid'),
    ('revision_code','measurement_revision_closed'),
])
def test_sql_rejects_misassociated_or_out_of_sequence_evidence(documentary_tenant,mutation,code):
    org,_,users,_=documentary_tenant
    _,position,_,_=mounting_position(org,users['OWNER'])
    with as_user(users['OWNER']):
        other_project=create_project(org,users['OWNER'],{'name':'Otra obra · DEMO','client_name':'Ensayo'})
        value={'project_id':other_project['id'],'generation':99,'revision_code':'REV-B'}[mutation]
        columns=['org_id','project_id','position_id','revision_code','generation','measurements','binding','state','actor_id','reason']
        selections=['%s' if column==mutation else ('generation+1' if column=='generation' else column) for column in columns]
        with pytest.raises(DatabaseError,match=code),transaction.atomic(),extra_backend():
            rows('INSERT INTO position_measurements('+','.join(columns)+') SELECT '+','.join(selections)+
                 ' FROM position_measurements WHERE position_id=%s RETURNING id',[value,position['id']])
        assert measurement_record(org,position['id'],'REV-A')['generation']==1


def test_revision_copy_cannot_rebind_stale_survey_to_changed_fabrication(documentary_tenant):
    org,_,users,_=documentary_tenant
    project,position,_,_=mounting_position(org,users['OWNER'])
    with as_user(users['OWNER']):
        changed=PositionWriteSerializer(data={'location_tag':'Fachada','quantity':1,
            'design':{**position['design'],'nominal_width_mm':'1501'}})
        changed.is_valid(raise_exception=True)
        position=save_position(org,project['id'],{**changed.validated_data,
            'expected_updated_at':position_row(org,position['id'])['updated_at']},position_id=position['id'])
        assert position['measurements']['current'] is False
        # Exercise the revision-copy helper against the same current target:
        # a faulty rebind would append generation 2 and make confirmation legal.
        copy_measurements(org,project['id'],'REV-A','REV-A')
        assert measurement_record(org,position['id'],'REV-A')['generation']==1
        assert measurement_public(org,position['id'],position['design'],'REV-A')['current'] is False
    refused=client_for(users['ESTIMATOR']).post(f"/api/v1/positions/{position['id']}/measurements/confirm/",
        confirm_body(position),format='json',HTTP_X_ORGANIZATION_ID=str(org))
    assert refused.status_code==409,refused.content
