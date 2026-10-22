"""Automatic working money and atomic application at the legacy freeze edge."""

from decimal import Decimal as D

import pytest

from pricing.repository import commercial_backend, one, rows
from pricing.simple_policy import save_policy
from projects import service
from documents.service import revision_snapshot, prepare_documentary_inputs
from backend.tests.integration import test_shot08_pricing as commercial_tests
from backend.tests.integration import test_shot09_documentary as documentary_tests
from backend.tests.integration.test_simple_pricing_policy import policy_values

pytestmark = pytest.mark.rls_integration
commercial_rows = commercial_tests.commercial_rows
documentary_committed_tenant = documentary_tests.documentary_committed_tenant
as_user = commercial_tests.as_user


def test_saved_window_and_quantity_refresh_working_money_without_applying(commercial_rows):
    org, _, users = commercial_rows
    project = commercial_tests.seed_commercial_project(org, users['OWNER'])
    with as_user(users['OWNER']):
        save_policy(org, policy_values(), 0, 'Mis precios')
        position = service.position_row(org, one('SELECT id FROM project_positions WHERE project_id=%s', [project])['id'])
        design = {'system_id': position['system_id'], 'nominal_width_mm': position['width_mm'],
            'nominal_height_mm': position['height_mm'], 'color': position['color_interior'],
            'parametric_tree': service.decoded(position['parametric_tree'])}
        service.save_position(org, project, {'design': design, 'quantity': 3,
            'location_tag': 'Tres unidades', 'expected_updated_at': position['updated_at']}, position_id=position['id'])
        with commercial_backend():
            working = one('SELECT * FROM project_working_prices WHERE project_id=%s', [project])
            assert working['state'] == 'READY'
            assert D(service.decoded(working['result'])['project_net']) == D('1470')
            assert rows("SELECT id FROM pricing_operations WHERE project_id=%s AND state='APPLIED'", [project]) == []
        public = service.project_public(org, service.project_row(org, project), detail=True)
        assert D(public['working_price']['project_net']) == D('1470')
        assert public['pricing_current'] is False
        assert D(public['positions'][0]['commercial']['unit_net']) == D('490')
        assert service.editable(org, project)['id'] == project
        service.delete_position(org, position['id'], public['positions'][0]['updated_at'])
        public = service.project_public(org, service.project_row(org, project), detail=True)
        assert public['working_price']['state'] == 'BLOCKED'
        assert public['working_price']['project_net'] is None


@pytest.mark.parametrize('role', ['OWNER', 'ESTIMATOR'])
def test_freeze_without_manual_apply_is_atomic_idempotent_and_immutable(documentary_committed_tenant, role):
    org, _, users, _ = documentary_committed_tenant
    project, _, _ = documentary_tests._seed_project(org, users['OWNER'], apply_pricing=False)
    client = commercial_tests.owner_client(users[role])
    endpoint = f'/api/v1/documents/projects/{project}/freeze/'
    with as_user(users['OWNER']):
        save_policy(org, policy_values(), 0, 'Mis precios')
        preparation = prepare_documentary_inputs(org_id=org, project_id=project)
        assert not any(item['code'] in ('pricing_not_applied', 'working_price_required') for item in preparation['missing'])
    projected = client.get(f'/api/v1/projects/{project}/')
    assert projected.status_code == 200, projected.content
    assert projected.json()['working_price']['state'] == 'READY'
    assert ('breakdown' in projected.json()['working_price']['lines'][0]) == (role == 'OWNER')
    denied = client.post(endpoint, {'confirmed': False}, format='json')
    assert denied.status_code == 409, denied.content
    assert rows("SELECT id FROM pricing_operations WHERE project_id=%s AND state='APPLIED'", [project]) == []
    issued = client.post(endpoint, {'confirmed': True}, format='json')
    assert issued.status_code == 201, issued.content
    version = issued.json()
    with as_user(users['OWNER']):
        _, before = revision_snapshot(version['id'], org)
        assert before['pricing']['input_snapshot']['workshop_policy']['revision'] == 1
        assert before['pricing']['input_snapshot']['rules']['tax_rate_pct'] == '0.1900'
        save_policy(org, policy_values(margin='.50'), 1, 'Solo borradores')
        _, after = revision_snapshot(version['id'], org)
        assert after == before
    replay = client.post(endpoint, {'confirmed': True}, format='json')
    assert replay.status_code == 200 and replay.json()['id'] == version['id'], replay.content
    applied = rows("SELECT id FROM pricing_operations WHERE project_id=%s AND state='APPLIED'", [project])
    assert len(applied) == 1


def test_failed_freeze_rolls_back_the_automatic_application(documentary_committed_tenant):
    org, _, users, _ = documentary_committed_tenant
    project = commercial_tests.seed_commercial_project(org, users['OWNER'])
    client = commercial_tests.owner_client(users['OWNER'])
    result = client.post(f'/api/v1/documents/projects/{project}/freeze/', {'confirmed': True}, format='json')
    assert result.status_code == 422, result.content
    assert rows('SELECT id FROM pricing_operations WHERE project_id=%s', [project]) == []
    assert one('SELECT total_price_net FROM projects WHERE id=%s', [project])['total_price_net'] == 0
    with as_user(users['OWNER']):
        assert service.editable(org, project)['id'] == project
