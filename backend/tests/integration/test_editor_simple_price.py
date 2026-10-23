"""Unsaved quotes share the draft policy, preserve storage and keep costs private."""

from datetime import date
from decimal import Decimal as D

import pytest

from backend.tests.integration import test_shot08_pricing as commercial_tests
from backend.tests.integration.test_shot08_pricing import (
    as_user, owner_client, seed_unpriced_project, tenant,
)
from backend.tests.integration.test_simple_pricing_policy import policy_values
from pricing.repository import admin_write, commercial_backend, one, rows
from pricing.simple_policy import save_policy
from pricing.working import refresh_working, working_public
from projects.ops_registry import product_from_position

pytestmark = pytest.mark.rls_integration
commercial_rows = commercial_tests.commercial_rows


def editor_fixture(org, owner):
    project = seed_unpriced_project(org, owner)
    with as_user(owner):
        parent = admin_write('cost-lists', org, {'supplier_name': 'Editor fixture',
            'currency': 'CLP', 'valid_from': date(2026, 9, 1)}, 'Ensayo sintético')
        for sku, unit in [('COMPRA-MARCO', 'BAR'), ('COMPRA-JQ-10', 'BAR'),
                ('COMPRA-ACERO-MARCO', 'BAR'), ('VIDRIO-BASE', 'M2')]:
            admin_write('cost-items', org, {'cost_list_id': parent['id'], 'sku': sku,
                'item_type': 'FIXTURE', 'unit': unit, 'unit_cost': D('100')}, 'Ensayo sintético')
    position = one('SELECT * FROM public.project_positions WHERE project_id=%s', [project])
    body = {'system_id': str(position['system_id']), 'color': position['color_interior'],
        'product': product_from_position(position), 'quantity': 1, 'ops': []}
    return project, position, body


@pytest.mark.parametrize('saved', [False, True])
@pytest.mark.parametrize('quantity', [1, 7])
def test_live_price_equals_working_line_without_advanced_rules_or_writes(commercial_rows, saved, quantity):
    org, _, users = commercial_rows
    project, position, body = editor_fixture(org, users['OWNER'])
    rows('UPDATE public.project_positions SET quantity=%s WHERE id=%s RETURNING id', [quantity, position['id']])
    original_project = one('SELECT * FROM public.projects WHERE id=%s', [project])
    original_position = one('SELECT * FROM public.project_positions WHERE id=%s', [position['id']])
    with as_user(users['OWNER']):
        if saved:
            save_policy(org, policy_values(waste='.08'), 0, 'Mis precios para el editor')
        working = working_public(refresh_working(org, tenant(org, 'OWNER'), project), 'OWNER')
    with as_user(users['OWNER']), commercial_backend():
        assert rows('SELECT * FROM public.pricing_rules WHERE org_id=%s', [org]) == []
        before_cache = one('SELECT * FROM public.project_working_prices WHERE project_id=%s', [project])
    response = owner_client(users['OWNER']).post('/api/v1/projects/operations/simulate/',
        {**body, 'quantity': quantity}, format='json', HTTP_X_ORGANIZATION_ID=str(org))
    assert response.status_code == 200, response.content
    result = response.json()
    assert result['valid'] and result['ops'] == [] and result['diff'] == []
    price, line = result['price'], working['lines'][0]
    assert D(price['net']) == D(line['line_net'])
    assert D(price['unit_net']) == D(line['unit_price'])
    assert price['breakdown'] == line['breakdown']
    assert price['policy']['saved'] is saved and price['policy_revision'] == int(saved)
    assert D(price['delta_net']) == 0 and price['use_advanced'] is False
    assert one('SELECT * FROM public.projects WHERE id=%s', [project]) == original_project
    assert one('SELECT * FROM public.project_positions WHERE id=%s', [position['id']]) == original_position
    with as_user(users['OWNER']), commercial_backend():
        assert one('SELECT * FROM public.project_working_prices WHERE project_id=%s', [project]) == before_cache
        assert rows('SELECT id FROM public.pricing_operations WHERE org_id=%s', [org]) == []


@pytest.mark.parametrize('role', ['OWNER', 'ESTIMATOR', 'WORKSHOP_MANAGER'])
def test_live_price_allowlist_and_unsaved_dimension_delta(commercial_rows, role):
    org, other, users = commercial_rows
    _, position, body = editor_fixture(org, users['OWNER'])
    with as_user(users['OWNER']):
        save_policy(org, policy_values(), 0, 'Privacidad del precio vivo')
    response = owner_client(users[role]).post('/api/v1/projects/operations/simulate/', {
        **body, 'ops': [{'op': 'set_total_width', 'width_mm': '1400'}]},
        format='json', HTTP_X_ORGANIZATION_ID=str(org))
    assert response.status_code == 200, response.content
    result = response.json()
    assert result['valid']
    before, after = result['before']['price'], result['price']
    assert D(after['net']) > D(before['net'])
    assert D(after['delta_net']) + D(before['net']) == D(after['net'])
    for price in (before, after):
        assert ('breakdown' in price) is (role == 'OWNER')
        assert ('policy' in price) is (role == 'OWNER')
        assert ('catalog_use' in price) is (role == 'OWNER')
        assert 'cost' not in price
        if role != 'OWNER':
            assert set(price) <= {'net', 'unit_net', 'delta_net', 'currency', 'reason',
                'source', 'use_advanced', 'policy_revision'}
    assert one('SELECT * FROM public.project_positions WHERE id=%s', [position['id']]) == position
    forbidden = owner_client(users[role]).post('/api/v1/projects/operations/simulate/', body,
        format='json', HTTP_X_ORGANIZATION_ID=str(other))
    assert forbidden.status_code == 403


def test_missing_cost_clears_live_price_and_installer_cannot_read_it(commercial_rows):
    org, _, users = commercial_rows
    _, _, body = editor_fixture(org, users['OWNER'])
    with as_user(users['OWNER']):
        save_policy(org, policy_values(), 0, 'Mis precios')
        rows('UPDATE public.cost_lists SET is_active=false WHERE org_id=%s RETURNING id', [org])
    response = owner_client(users['OWNER']).post('/api/v1/projects/operations/simulate/', body,
        format='json', HTTP_X_ORGANIZATION_ID=str(org))
    assert response.status_code == 200, response.content
    price = response.json()['price']
    assert price['net'] is None and price['reason'] and 'breakdown' not in price
    denied = owner_client(users['INSTALLER']).post('/api/v1/projects/operations/simulate/', body,
        format='json', HTTP_X_ORGANIZATION_ID=str(org))
    assert denied.status_code == 403
