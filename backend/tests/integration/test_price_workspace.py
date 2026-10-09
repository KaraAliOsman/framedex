"""P07 live authorities, approval, private traces and deterministic replay."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from decimal import Decimal, localcontext

import pytest
from django.db import connection

from backend.tests.integration.test_shot08_pricing import (
    committed_commercial_rows as committed_commercial_rows,
    seed_commercial_project, owner_client, as_user, price_payload,
)
from pricing.repository import admin_write, one, rows, commercial_backend, json_text
from pricing.service import decoded
from pricing.workspace import replay_state, _reprice, project_price_attention
from projects.service import reset_draft_pricing

pytestmark = pytest.mark.rls_integration
D = Decimal


def request(client, org, route, body=None):
    headers = {'HTTP_X_ORGANIZATION_ID':str(org)}
    response = (client.post('/api/v1'+route,body,format='json',**headers) if body is not None
        else client.get('/api/v1'+route,**headers))
    assert response.status_code == 200, response.data
    return response.json()


def test_projection_is_read_only_closes_and_keeps_quantity_authority(committed_commercial_rows):
    org, _, users = committed_commercial_rows
    project = seed_commercial_project(org,users['OWNER'])
    with connection.cursor() as cursor:
        cursor.execute('UPDATE project_positions SET quantity=3 WHERE project_id=%s',[project])
    owner = owner_client(users['OWNER'])
    before = rows('SELECT id FROM pricing_operations WHERE project_id=%s',[project])
    result = request(owner,org,'/pricing/workspace/',price_payload(project))
    assert result['id'] is None and result['created_at'] is None
    assert rows('SELECT id FROM pricing_operations WHERE project_id=%s',[project]) == before
    workspace = result['workspace']
    assert workspace['comparison']['net']['current'] is None
    assert workspace['explanation']['available'] is False
    with localcontext() as context:
        context.prec = 256
        assert sum((D(step['amount']) for step in workspace['cascade']['steps']),D(0)) == D(result['project_gross'])
        line = workspace['positions'][0]
        assert sum((D(step['amount']) for step in line['cascade']['steps']),D(0)) == D(line['line_net'])
        assert line['quantity'] == 3 and line['unit_price'] == '499.8074'
        assert line['traces']['line_net']['inputs'][1]['value'] == '3'
        assert 'Costo base' in [entry['label'] for entry in line['traces']['unit_price']['inputs']]
        assert line['traces']['margin']['formula'] == '(Neto − costo) ÷ neto'
        assert line['line_net'] == '1499'


@pytest.mark.parametrize('reject',[False,True])
def test_band_request_decision_actor_attention_and_idempotent_receipt(committed_commercial_rows,reject):
    org, _, users = committed_commercial_rows
    project = seed_commercial_project(org,users['OWNER'])
    estimator, owner = owner_client(users['ESTIMATOR']),owner_client(users['OWNER'])
    payload = {**price_payload(project),'target_margin':'0.20','reason':'Acuerdo bajo el mínimo'}
    pending = request(estimator,org,'/pricing/preview/',payload)
    assert pending['state'] == 'PENDING' and pending['workspace']['policy']['requires_approval']
    public = pending['workspace']
    assert set(public['comparison']) == {'net','tax','total'}
    assert not {'cost','profit','margin'} & public['cascade'].keys()
    assert not {'cost','profit','profit_at_list'} & public['cascade']['traces'].keys()
    assert not {'unit_cost','margin','composition'} & public['positions'][0].keys()
    assert 'unit_cost' not in public['positions'][0]['traces']
    assert all('Costo' not in entry['label'] for trace in public['positions'][0]['traces'].values() for entry in trace['inputs'])
    assert all('Costo' not in entry['label'] for trace in public['cascade']['traces'].values() for entry in trace['inputs'])
    denied = estimator.post(f"/api/v1/pricing/operations/{pending['id']}/apply/",
        {'reason':'Intento sin autorización','confirmed':False},format='json',HTTP_X_ORGANIZATION_ID=str(org))
    assert denied.status_code == 403 and denied.json()['error']['code'] == 'owner_approval_required'
    with as_user(users['OWNER']),commercial_backend():
        assert project_price_attention(org,users['OWNER'],'OWNER')['pricing_pending'] == 1
    frozen = one('SELECT input_snapshot,result FROM pricing_operations WHERE id=%s',[pending['id']])
    decided = request(owner,org,f"/pricing/operations/{pending['id']}/apply/",
        {'reason':'El dueño confirma el acuerdo','confirmed':True,'reject':reject})
    assert decided['state'] == ('REJECTED' if reject else 'APPLIED')
    assert decided['approved_by'] == str(users['OWNER'])
    assert one('SELECT input_snapshot,result FROM pricing_operations WHERE id=%s',[pending['id']]) == frozen
    listed = request(estimator,org,'/pricing/operations/')
    assert listed[0]['notification_unread'] is True
    with as_user(users['ESTIMATOR']),commercial_backend():
        assert project_price_attention(org,users['ESTIMATOR'],'ESTIMATOR')['pricing_decisions'] == 1
    for _ in range(2):
        request(estimator,org,'/pricing/acknowledge/',{'operation_ids':[pending['id']]})
    assert one('SELECT count(*) AS n FROM pricing_attention_receipts WHERE operation_id=%s',[pending['id']])['n'] == 1
    assert request(estimator,org,'/pricing/operations/')[0]['notification_unread'] is False
    audits = rows('SELECT actor_user_id,reason,new_record FROM price_audit_logs WHERE entity_id=%s ORDER BY created_at',[pending['id']])
    assert any(a['actor_user_id'] == users['OWNER'] and a['reason'] == 'El dueño confirma el acuerdo' for a in audits)


def test_new_rules_are_rechecked_at_estimator_apply(committed_commercial_rows):
    org, _, users = committed_commercial_rows
    project = seed_commercial_project(org,users['OWNER'])
    estimator = owner_client(users['ESTIMATOR'])
    proposal = request(estimator,org,'/pricing/preview/',price_payload(project))
    assert proposal['state'] == 'PREVIEW'
    with as_user(users['OWNER']):
        rule = one('SELECT id FROM pricing_rules WHERE org_id=%s',[org])
        admin_write('rules',org,{'default_margin_pct':D('.40'),'minimum_margin_pct':D('.40')},'Subir mínimo',rule['id'])
    response = estimator.post(f"/api/v1/pricing/operations/{proposal['id']}/apply/",
        {'reason':'Aplicar después del cambio','confirmed':False},format='json',HTTP_X_ORGANIZATION_ID=str(org))
    assert response.status_code == 403 and response.json()['error']['code'] == 'owner_approval_required'
    assert one('SELECT state FROM pricing_operations WHERE id=%s',[proposal['id']])['state'] == 'PREVIEW'


def test_discount_threshold_is_configurable_and_margin_remains_authority(committed_commercial_rows):
    org, _, users = committed_commercial_rows
    project = seed_commercial_project(org,users['OWNER'])
    with as_user(users['OWNER']):
        rule = one('SELECT id FROM pricing_rules WHERE org_id=%s',[org])
        admin_write('rules',org,{'discount_approval_pct':D('.18'),'minimum_margin_pct':D('.10')},'Declarar umbral',rule['id'])
    estimator = owner_client(users['ESTIMATOR'])
    proposal = request(estimator,org,'/pricing/preview/',price_payload(project,discount='.15'))
    assert proposal['state'] == 'PREVIEW' and not proposal['workspace']['policy']['requires_approval']
    applied = request(estimator,org,f"/pricing/operations/{proposal['id']}/apply/",{'reason':'Aplicar acuerdo permitido','confirmed':False})
    assert applied['state'] == 'APPLIED'


def test_frozen_replay_has_no_io_and_canonical_delta_closes(committed_commercial_rows,monkeypatch):
    org, _, users = committed_commercial_rows
    project = seed_commercial_project(org,users['OWNER'])
    owner = owner_client(users['OWNER'])
    from projects.service import calculate_design
    position = one('SELECT * FROM project_positions WHERE project_id=%s',[project])
    with as_user(users['OWNER']):
        calculated = calculate_design(org,{'system_id':position['system_id'],
            'nominal_width_mm':position['width_mm'],'nominal_height_mm':position['height_mm'],
            'color':'WHITE','parametric_tree':decoded(position['parametric_tree'])})
    with connection.cursor() as cursor:
        cursor.execute('UPDATE project_positions SET bom_snapshot=%s::jsonb WHERE project_id=%s',
            [json_text(calculated),project])
    previous = request(owner,org,'/pricing/preview/',price_payload(project))
    request(owner,org,f"/pricing/operations/{previous['id']}/apply/",{'reason':'Aplicar precio inicial','confirmed':True})
    with as_user(users['OWNER']):
        reset_draft_pricing(org,project,previous['id'],'Revisar el acuerdo')
    with connection.cursor() as cursor:
        cursor.execute('UPDATE project_positions SET quantity=3 WHERE project_id=%s',[project])
    proposed = request(owner,org,'/pricing/workspace/',{**price_payload(project),'discount_pct':'.05','target_margin':'.40'})
    explanation = proposed['workspace']['explanation']
    assert explanation['available'] and explanation['closes'], explanation
    assert sum(D(item['delta']['net']) for item in explanation['contributions']) == D(proposed['project_net'])-D(previous['project_net'])
    assert explanation['contributions'][0]['driver'] == 'quantity'
    sealed = decoded(one('SELECT input_snapshot FROM pricing_operations WHERE id=%s',[previous['id']])['input_snapshot'])
    state = replay_state(sealed['replay'])
    def forbidden(*args,**kwargs):
        raise AssertionError('Frozen repricing tried database I/O')
    with monkeypatch.context() as isolated:
        for module in ('pricing.repository','pricing.resolved','pricing.service','projects.extras'):
            isolated.setattr(module+'.rows',forbidden)
        isolated.setattr(connection,'cursor',forbidden)
        assert _reprice(org,state,state,state)['net'] == D(previous['project_net'])


@pytest.mark.parametrize('role',['ESTIMATOR','WORKSHOP_MANAGER','INSTALLER'])
def test_options_are_selling_only_and_admin_stays_owner_only(committed_commercial_rows,role):
    org, _, users = committed_commercial_rows
    seed_commercial_project(org,users['OWNER'])
    client = owner_client(users[role])
    options = client.get('/api/v1/pricing/options/',HTTP_X_ORGANIZATION_ID=str(org))
    assert options.status_code == (200 if role == 'ESTIMATOR' else 403)
    if role == 'ESTIMATOR':
        assert set(options.json()) == {'fx','commercial_lists','band'}
    assert client.get('/api/v1/pricing/admin/fx/',HTTP_X_ORGANIZATION_ID=str(org)).status_code == 403


def test_coverage_matches_buying_skus_and_refuses_future_or_wrong_unit(committed_commercial_rows):
    org, _, users = committed_commercial_rows
    seed_commercial_project(org,users['OWNER'])
    owner = owner_client(users['OWNER'])
    coverage = request(owner,org,'/pricing/admin/coverage/')['items']
    assert next(item for item in coverage if item['sku'] == 'COMPRA-MARCO')['active_cost_items'] == 1
    assert next(item for item in coverage if item['sku'] == 'VIDRIO-BASE')['active_cost_items'] == 1
    today = datetime.now(ZoneInfo('America/Santiago')).date()
    with as_user(users['OWNER']):
        original = one("SELECT id FROM cost_lists WHERE org_id=%s AND supplier_name='Gate'",[org])
        admin_write('cost-lists',org,{'valid_to':today-timedelta(days=1)},'Cerrar lista',original['id'])
        future = admin_write('cost-lists',org,{'supplier_name':'Futura','currency':'CLP','valid_from':today+timedelta(days=1)},'Lista futura')
        admin_write('cost-items',org,{'cost_list_id':future['id'],'sku':'VIDRIO-BASE','item_type':'GLASS','unit':'M2','unit_cost':D(100)},'Costo futuro')
    missing = next(item for item in request(owner,org,'/pricing/admin/coverage/')['items'] if item['sku'] == 'VIDRIO-BASE')
    assert missing['active_cost_items'] == 0 and missing['blocker']
