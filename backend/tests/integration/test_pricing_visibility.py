"""Confidential services stay sealed; each selling endpoint applies role limits."""
from copy import deepcopy
from uuid import UUID

import pytest

from backend.tests.integration.test_shot08_pricing import (
    committed_commercial_rows as committed_commercial_rows,
    seed_commercial_project, owner_client, as_user, price_payload,
)
from backend.tests.integration.test_extras_services import save_policy
from dekopen_engine.extra_models import ExtraPolicy
from engine.tests.extra_cases import installation
from pricing.repository import rows, one, json_text
from pricing.service import decoded
from projects.extras import extra_backend

pytestmark = pytest.mark.rls_integration


def assert_private_costs_absent(public):
    assert public['costs_visible'] is False and public['total_cost'] is None
    assert 'confidenciales' in public['costs_reason']
    assert public['cost_lines'] == public['positions_breakdown'] == public['authorities'] == []
    assert not {'labor_rate_per_m2', 'installation_rate_per_m2'} & public['rules'].keys()
    assert 'services_cost' not in public
    assert public['services'] and public['services'][0]['amount'] != '0'
    for item in public['services']:
        assert 'cost_rate' not in item and 'total_cost' not in item


def test_estimator_preview_apply_list_and_withdraw_cannot_read_costs(committed_commercial_rows):
    org, _, users = committed_commercial_rows
    project = seed_commercial_project(org, users['OWNER'])
    with as_user(users['OWNER']):
        save_policy(org, ExtraPolicy(services=[installation()]))
        with extra_backend():
            rows('INSERT INTO project_extra_services(org_id,project_id,revision_code,selections) '
                 'VALUES(%s,%s,%s,%s::jsonb) RETURNING project_id',
                 [org, project, 'REV-A', json_text([{'code': 'INSTALL'}])])
    client = owner_client(users['ESTIMATOR'])
    headers = {'HTTP_X_ORGANIZATION_ID': str(org)}
    response = client.post('/api/v1/pricing/preview/', price_payload(project), format='json', **headers)
    assert response.status_code == 200, response.data
    public = response.json()
    assert_private_costs_absent(public)
    operation = UUID(public['id'])
    sealed = one('SELECT input_snapshot,result FROM pricing_operations WHERE id=%s', [operation])
    preserved = deepcopy(sealed)
    assert decoded(sealed['result'])['services'][0]['cost_rate'] == '1000'
    listed = client.get('/api/v1/pricing/operations/', **headers)
    assert listed.status_code == 200, listed.data
    assert_private_costs_absent(next(item for item in listed.json() if item['id'] == public['id']))
    # OWNER sees the exact same frozen buying authority, including services.
    owner = owner_client(users['OWNER']).get('/api/v1/pricing/operations/', **headers)
    assert owner.status_code == 200, owner.data
    full = next(item for item in owner.json() if item['id'] == public['id'])
    assert full['costs_visible'] and full['costs_reason'] is None
    assert full['total_cost'] is not None and full['cost_lines'] and full['authorities']
    assert full['services'][0]['cost_rate'] == '1000'
    pending = client.post('/api/v1/pricing/preview/', price_payload(project, discount='0.15'), format='json', **headers)
    assert pending.status_code == 200 and pending.json()['state'] == 'PENDING', pending.data
    withdrawn = client.post(f"/api/v1/pricing/operations/{pending.json()['id']}/withdraw/",
                            {'reason': 'Retirar la solicitud'}, format='json', **headers)
    assert withdrawn.status_code == 200, withdrawn.data
    assert_private_costs_absent(withdrawn.json())
    applied = client.post(f'/api/v1/pricing/operations/{operation}/apply/',
                          {'reason': 'Aplicar la venta revisada', 'confirmed': False}, format='json', **headers)
    assert applied.status_code == 200, applied.data
    assert_private_costs_absent(applied.json())
    assert one('SELECT input_snapshot,result FROM pricing_operations WHERE id=%s', [operation]) == preserved


@pytest.mark.parametrize('role', ['OWNER', 'ESTIMATOR'])
def test_batch_cost_visibility_uses_membership_not_client_input(committed_commercial_rows, role):
    org, _, users = committed_commercial_rows
    project = seed_commercial_project(org, users['OWNER'])
    position = one('SELECT * FROM project_positions WHERE project_id=%s', [project])
    body = {'project_id': str(project), 'effective_date': '2026-09-10', 'items': [
        {'position_id': str(position['id']), 'design': {
            'system_id': str(position['system_id']), 'color': position['color_interior'],
            'nominal_width_mm': str(position['width_mm']), 'nominal_height_mm': str(position['height_mm']),
            'parametric_tree': decoded(position['parametric_tree'])}}]}
    response = owner_client(users[role]).post('/api/v1/pricing/design-batch-preview/', body,
                                            format='json', HTTP_X_ORGANIZATION_ID=str(org))
    assert response.status_code == 200, response.data
    entry = response.json()['items'][0]
    assert entry['ok'], response.data
    assert response.json()['costs_visible'] == (role == 'OWNER')
    if role == 'OWNER':
        assert entry['unit_cost_before'] == entry['unit_cost_after'] != '0'
    else:
        assert all(entry[key] is None for key in ['unit_cost_before', 'unit_cost_after', 'line_cost_before', 'line_cost_after'])
