"""P03's projections execute under the five roles on the migrated database."""
from uuid import uuid4
from datetime import timedelta

import pytest
from django.db import connection

from backend.tests.integration.test_shot08_pricing import (
    committed_commercial_rows as committed_commercial_rows,
    seed_commercial_project, owner_client, price_payload,
)
from pricing.repository import one, rows
from documents.repository import documentary_backend
from backend.tests.integration.test_shot09_documentary import (
    documentary_tenant as documentary_tenant, _seed_project, _freeze,
)

pytestmark = pytest.mark.rls_integration


def read(client, org, path):
    response = client.get('/api/v1' + path, HTTP_X_ORGANIZATION_ID=str(org))
    assert response.status_code == 200, response.data
    return response.json()


def test_empty_today_runs_every_query_for_five_roles_and_role_gates_quotes(committed_commercial_rows):
    org, _, users = committed_commercial_rows
    users['OPERATOR'] = uuid4()
    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO public.tenancy_memberships(org_id,user_id,role) VALUES(%s,%s,'OPERATOR')",
                       [org, users['OPERATOR']])
    for role, user in users.items():
        client = owner_client(user)
        output = read(client, org, '/analytics/today/')
        assert output['actions'] == [] and output['pipeline'] == []
        assert output['today'] and output['source']
        response = client.get('/api/v1/analytics/quotations/', HTTP_X_ORGANIZATION_ID=str(org))
        assert response.status_code == (200 if role in {'OWNER', 'ESTIMATOR'} else 403), response.data
        if response.status_code == 200:
            assert response.json()['items'] == []


@pytest.mark.parametrize('reject', [False, True])
def test_price_action_decision_detail_and_receipt_share_real_authority(committed_commercial_rows, reject):
    org, other, users = committed_commercial_rows
    project = seed_commercial_project(org, users['OWNER'])
    estimator, owner = owner_client(users['ESTIMATOR']), owner_client(users['OWNER'])
    headers = {'HTTP_X_ORGANIZATION_ID': str(org)}
    preview = estimator.post('/api/v1/pricing/preview/', {
        **price_payload(project), 'target_margin': '.20', 'reason': 'Acuerdo Prat bajo la banda',
    }, format='json', **headers)
    assert preview.status_code == 200, preview.data
    operation = preview.json()['id']
    pending = read(owner, org, '/analytics/today/')['actions']
    action = next(item for item in pending if item['operation_id'] == operation)
    assert action['kind'] == 'price_pending' and action['consequence'] == 'blocking'
    assert action['href'] == f'/projects/{project}/pricing?operation={operation}'
    for private in ('workspace', 'result', 'total_cost', 'margin', 'profit'):
        assert private not in action
    owner_detail = read(owner, org, f'/pricing/operations/{operation}/')
    public_detail = read(estimator, org, f'/pricing/operations/{operation}/')
    assert owner_detail['costs_visible'] and public_detail['total_cost'] is None
    assert not {'cost', 'margin', 'profit'} & public_detail['workspace']['comparison'].keys()
    frozen = one('SELECT input_snapshot,result FROM public.pricing_operations WHERE id=%s', [operation])
    decision = owner.post(f'/api/v1/pricing/operations/{operation}/apply/', {
        'reason': 'Decisión explícita del dueño', 'confirmed': True, 'reject': reject,
    }, format='json', **headers)
    assert decision.status_code == 200, decision.data
    assert not any(item['operation_id'] == operation for item in read(owner, org, '/analytics/today/')['actions'])
    notified = next(item for item in read(estimator, org, '/analytics/today/')['actions'] if item['operation_id'] == operation)
    assert notified['kind'] == 'price_decision' and notified['reason'] == 'Decisión explícita del dueño'
    assert read(estimator, org, f'/pricing/operations/{operation}/')['notification_unread']
    for _ in range(2):
        acknowledged = estimator.post('/api/v1/pricing/acknowledge/', {'operation_ids': [operation]}, format='json', **headers)
        assert acknowledged.status_code == 200, acknowledged.data
    assert not any(item['operation_id'] == operation for item in read(estimator, org, '/analytics/today/')['actions'])
    assert not read(estimator, org, f'/pricing/operations/{operation}/')['notification_unread']
    assert one('SELECT count(*) AS n FROM pricing_attention_receipts WHERE operation_id=%s', [operation])['n'] == 1
    assert one('SELECT input_snapshot,result FROM public.pricing_operations WHERE id=%s', [operation]) == frozen
    # Known identifiers confer no tenancy or role capability.
    for path in ('/analytics/today/', f'/pricing/operations/{operation}/'):
        denied = estimator.get('/api/v1' + path, HTTP_X_ORGANIZATION_ID=str(other))
        assert denied.status_code == 403, denied.data
    denied = owner_client(users['WORKSHOP_MANAGER']).get(f'/api/v1/pricing/operations/{operation}/', **headers)
    assert denied.status_code == 403, denied.data
    # Another estimator in this tenant cannot read someone else's proposal.
    colleague = uuid4()
    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO public.tenancy_memberships(org_id,user_id,role) VALUES(%s,%s,'ESTIMATOR')", [org, colleague])
    denied = owner_client(colleague).get(f'/api/v1/pricing/operations/{operation}/', **headers)
    assert denied.status_code == 404, denied.data
    assert read(owner_client(colleague), org, '/analytics/today/')['actions'] == []
    assert rows('SELECT id FROM public.pricing_operations WHERE id=%s', [operation])


def test_quotation_follow_up_and_pipeline_read_only_current_sealed_revision(documentary_tenant):
    from analytics.today import local_today
    org, _, users, _ = documentary_tenant
    owner = users['OWNER']
    project, _, operation = _seed_project(org, owner)
    due = local_today(org) + timedelta(days=2)
    with connection.cursor() as cursor:
        cursor.execute('UPDATE project_documentary_inputs SET quotation_valid_until=%s WHERE project_id=%s', [due,project])
    version = _freeze(org,owner,project,operation)
    before = one('SELECT snapshot_json::text AS evidence FROM project_versions WHERE id=%s', [version['id']])
    client = owner_client(owner)
    headers = {'HTTP_X_ORGANIZATION_ID': str(org)}
    index = read(client,org,'/analytics/quotations/?attention=expiring')
    assert index['total'] == 1 and index['items'][0]['valid_until'] == due.isoformat()
    assert index['items'][0]['revision_code'] == 'REV-A'
    work = read(client,org,'/analytics/today/')
    assert next(a for a in work['actions'] if a['kind']=='quote_expiring')['href'] == f'/projects/{project}'
    assert work['pipeline'][0]['href'] == '/quotes?phase=QUOTED&currency=CLP'
    # The PDF has a document link. Viewing a separate share link must not
    # disappear behind that unopened token, even when created_at ties.
    shared = client.post(f'/api/v1/projects/{project}/quote-link/',{},format='json',**headers)
    assert shared.status_code == 200, shared.data
    from portal.service import portal_quote
    portal_quote(shared.json()['token'])
    viewed = read(client,org,'/analytics/quotations/?attention=viewed')['items']
    assert len(viewed)==1 and viewed[0]['view_count']==1
    assert any(a['kind']=='quote_viewed' for a in read(client,org,'/analytics/today/')['actions'])
    successor = client.post(f'/api/v1/projects/{project}/successor/', {
        'confirmed':True,'expected_current_revision':'REV-A',
    }, format='json', **headers)
    assert successor.status_code == 201, successor.data
    assert read(client,org,'/analytics/quotations/')['items'] == []
    assert not any(a['kind'].startswith('quote_') for a in read(client,org,'/analytics/today/')['actions'])
    with documentary_backend():
        assert one('SELECT snapshot_json::text AS evidence FROM project_versions WHERE id=%s', [version['id']]) == before
