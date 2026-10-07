"""D06 HTTP roles, authority transport and tenant/history isolation."""
from uuid import uuid4
from copy import deepcopy
from dataclasses import replace
import base64
import hashlib
import hmac
import struct
import time
import json
from decimal import Decimal

import httpx
import pytest
from django.conf import settings
from django.db import connection, transaction, DatabaseError

from authentication.jwt_verifier import AuthServerTokenVerifier
from authentication.rls import authenticated_rls_context
from backend.tests.integration.test_rls_context_integration import real_rows as real_rows
from backend.tests.integration.test_shot10_catalog_api import client_for, set_role
from engine.tests.extra_cases import installation
from dekopen_engine.extra_models import ExtraPolicy, ExtraRate
from pricing.repository import json_text
from projects.extras import extra_backend

pytestmark=pytest.mark.rls_integration


@pytest.fixture(autouse=True)
def database_access(django_db_blocker):
    with django_db_blocker.unblock(),transaction.atomic():
        yield
        transaction.set_rollback(True)


def policy():
    freight = installation().model_copy(update={'code':'FREIGHT','name':'Flete por zona','basis':'ZONE','unit':'EA',
        'installation':False,'zones':{'Valdivia':ExtraRate(cost_rate=Decimal('15000'),selling_rate=Decimal('22500'))}})
    return {'schema_version':1,'services':[installation(scope='POSITION').model_dump(mode='json'), freight.model_dump(mode='json')],
        'position_defaults':[{'code':'INSTALL'}],'document_prices':'ITEMIZED'}


@pytest.fixture(scope='module')
def mfa_rows(real_rows):
    """Exercise the actual local Auth TOTP flow without weakening OWNER scope."""
    tokens = dict(real_rows.tokens)
    verifier = AuthServerTokenVerifier(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY, 5)
    with httpx.Client(timeout=10) as auth:
        for user in ('A', 'B'):
            headers = {'apikey': settings.SUPABASE_ANON_KEY,
                       'Authorization': 'Bearer ' + tokens[user].access_token}
            enrolled = auth.post(settings.SUPABASE_URL + '/auth/v1/factors', headers=headers,
                                 json={'factor_type': 'totp', 'friendly_name': 'D06-policy'})
            assert enrolled.status_code == 200, 'Local MFA enrollment failed'
            factor = enrolled.json()
            challenge = auth.post(settings.SUPABASE_URL + f"/auth/v1/factors/{factor['id']}/challenge",
                                  headers=headers, json={})
            assert challenge.status_code == 200, 'Local MFA challenge failed'
            secret = factor['totp']['secret']
            digest = hmac.new(base64.b32decode(secret + '=' * (-len(secret) % 8)),
                              struct.pack('>Q', int(time.time()) // 30), hashlib.sha1).digest()
            offset = digest[-1] & 15
            code = str((struct.unpack('>I', digest[offset:offset+4])[0] & 0x7fffffff) % 1000000).zfill(6)
            verified = auth.post(settings.SUPABASE_URL + f"/auth/v1/factors/{factor['id']}/verify",
                                 headers=headers, json={'challenge_id': challenge.json()['id'], 'code': code})
            assert verified.status_code == 200, 'Local MFA verification failed'
            tokens[user] = verifier.verify(verified.json()['access_token'])
            assert tokens[user].aal == 'aal2'
    return replace(real_rows, tokens=tokens)


def test_policy_owner_requires_real_mfa(real_rows):
    set_role(real_rows, 'OWNER')
    response = client_for(real_rows).get('/api/v1/organization/extras/')
    assert response.status_code == 403
    assert response.data['error']['code'] == 'mfa_required'


def test_policy_optimistic_revision_and_history(mfa_rows):
    real_rows = mfa_rows
    set_role(real_rows,'OWNER')
    client=client_for(real_rows)
    before=client.get('/api/v1/organization/extras/')
    assert before.status_code==200 and before.data['revision']==0
    body={'policy':policy(),'expected_revision':0,'reason':'Tarifa sintética de ensayo'}
    saved=client.put('/api/v1/organization/extras/',body,format='json')
    assert saved.status_code==200,saved.data
    assert saved.data['revision']==1
    assert client.put('/api/v1/organization/extras/',body,format='json').status_code==409
    updated=deepcopy(body)
    updated['expected_revision']=1
    updated['policy']['services'][0]['selling_rate']='1500.123456789123456789'
    saved=client.put('/api/v1/organization/extras/',updated,format='json')
    assert saved.status_code==200,saved.data
    assert saved.data['policy']['services'][0]['selling_rate']=='1500.123456789123456789'
    with connection.cursor() as cursor:
        cursor.execute('SELECT policy FROM organization_extra_history WHERE org_id=%s ORDER BY revision',[real_rows.organizations['A']])
        history=[json.loads(row[0]) if isinstance(row[0], str) else row[0] for row in cursor.fetchall()]
    assert len(history)==2 and history[0]==ExtraPolicy.model_validate(policy()).model_dump(mode='json')


@pytest.mark.parametrize('role',['ESTIMATOR','WORKSHOP_MANAGER','OPERATOR','INSTALLER'])
@pytest.mark.parametrize('method',['get','put'])
def test_policy_owner_boundary(real_rows,role,method):
    set_role(real_rows,role)
    kwargs={} if method=='get' else {'data':{'policy':policy(),'expected_revision':0,'reason':'Ensayo'},'format':'json'}
    response=getattr(client_for(real_rows),method)('/api/v1/organization/extras/',**kwargs)
    assert response.status_code==403,response.data


def test_policy_cross_tenant_and_raw_history_immutable(mfa_rows):
    real_rows = mfa_rows
    set_role(real_rows,'OWNER')
    saved=client_for(real_rows).put('/api/v1/organization/extras/',{'policy':policy(),'expected_revision':0,'reason':'Ensayo'},format='json')
    assert saved.status_code==200,saved.data
    set_role(real_rows,'OWNER',user='B',org='B')
    assert client_for(real_rows,'B','B').get('/api/v1/organization/extras/').data['revision']==0
    with authenticated_rls_context(real_rows.tokens['B'].claims),extra_backend(),connection.cursor() as cursor:
        cursor.execute('SELECT org_id FROM organization_extra_settings WHERE org_id=%s',[real_rows.organizations['A']])
        assert cursor.fetchall()==[]
    with pytest.raises(DatabaseError),transaction.atomic(),connection.cursor() as cursor:
        cursor.execute('UPDATE organization_extra_history SET reason=%s WHERE org_id=%s',['alterada',real_rows.organizations['A']])
    with pytest.raises(DatabaseError),transaction.atomic(),connection.cursor() as cursor:
        cursor.execute('UPDATE organization_extra_settings SET org_id=%s WHERE org_id=%s',[real_rows.organizations['B'],real_rows.organizations['A']])


@pytest.mark.parametrize('role',['WORKSHOP_MANAGER','OPERATOR','INSTALLER'])
def test_extras_preview_requires_commercial_role(real_rows,role):
    set_role(real_rows,role)
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM profile_systems WHERE code='DEMO_60' AND version=6")
        system=str(cursor.fetchone()[0])
    response=client_for(real_rows).post('/api/v1/projects/extras-preview/',{'system_id':system,'nominal_width_mm':'1500','nominal_height_mm':'1400','color':'WHITE',
        'parametric_tree':{'id':'vano','type':'BAY','opening_type':'FIXED','glass_thickness_mm':'24','glass_spec':'4-16-4'}},format='json')
    assert response.status_code==403,response.data


def test_extra_preview_motor_quantity_suggestions_and_no_cost_leak(real_rows):
    set_role(real_rows,'ESTIMATOR')
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM profile_systems WHERE code='DEMO_60' AND version=6")
        system=str(cursor.fetchone()[0])
    request={'system_id':system,'nominal_width_mm':'1500','nominal_height_mm':'1400','color':'WHITE',
        'parametric_tree':{'id':'vano','type':'BAY','opening_type':'FIXED','glass_thickness_mm':'24','glass_spec':'4-16-4',
            'extras':[{'code':'SILL','overhang_left_mm':'30','overhang_right_mm':'30'}]}}
    response=client_for(real_rows).post('/api/v1/projects/extras-preview/',request,format='json')
    assert response.status_code==200,response.data
    line=response.data['extras'][0]
    assert line['quantity']=='1.56' and line['amount']=='11700'
    assert 'cost_rate' not in json_text(response.data) and 'total_cost' not in json_text(response.data)
    request['parametric_tree']['extras']=[]
    response=client_for(real_rows).post('/api/v1/projects/extras-preview/',request,format='json')
    assert response.status_code==200,response.data
    assert any(item['selection']['code']=='SILL' and item['cause'] for item in response.data['suggestions'])


def test_service_project_id_cannot_cross_tenant(real_rows):
    set_role(real_rows,'ESTIMATOR')
    response=client_for(real_rows).get(f'/api/v1/projects/{uuid4()}/services/')
    assert response.status_code==404,response.data
