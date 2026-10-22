"""Real policy tenancy, optimistic writes, immutable history and BOM preview."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal as D, localcontext
from threading import Barrier, Event
from uuid import uuid4

from django.db import close_old_connections, transaction, DatabaseError
import pytest

from authentication.errors import ContractAPIException
from pricing.repository import commercial_backend, one, rows, PricingRepository
from pricing.simple_policy import POLICY_FIELDS, read_policy, save_policy, policy_example
from backend.tests.integration import test_shot08_pricing as commercial_tests
from backend.tests.integration.test_shot08_pricing import (
    as_user, owner_client,
    seed_commercial_project, preview, apply_operation, tenant, price_request,
)
from backend.tests.test_simple_pricing_policy import values

pytestmark = pytest.mark.rls_integration
commercial_rows = commercial_tests.commercial_rows
committed_commercial_rows = commercial_tests.committed_commercial_rows


def policy_values(**changes):
    from pricing.simple_serializers import SimplePolicyValuesSerializer
    serializer = SimplePolicyValuesSerializer(data=values(**({'labor_rate': '30.1234',
        'installation_rate': '12.3456', 'rounding_step': '10'} | changes)))
    assert serializer.is_valid(), serializer.errors
    return serializer.validated_data


def fixture_materials():
    # Bar fractions are individually resolved at precision 80, then summed at
    # 256: keep their finite tail rather than substitute the rational 275.81.
    with localcontext() as context:
        context.prec = 256
        return D('275.81') - D('2e-78')


def test_suggestions_are_read_only_and_saved_policy_has_exact_audit(commercial_rows):
    org, _, users = commercial_rows
    with as_user(users['OWNER']):
        suggested = read_policy(org)
        assert not suggested['saved'] and suggested['revision'] == 0
        assert set(suggested['suggested_fields']) == set(POLICY_FIELDS)
        assert rows('SELECT id FROM public.workshop_pricing_policies WHERE org_id=%s', [org]) == []
        first = save_policy(org, policy_values(), 0, 'Configurar mis precios')
        assert first['saved'] and first['revision'] == 1 and first['suggested_fields'] == []
        assert first['labor_rate'] == D('30.1234')
        next_values = {key: first[key] for key in POLICY_FIELDS} | {'margin': D('.40')}
        second = save_policy(org, next_values, 1, 'Ajustar margen')
        assert second['revision'] == 2
        with pytest.raises(ContractAPIException) as stale:
            save_policy(org, policy_values(), 1, 'Otra pestaña obsoleta')
        assert stale.value.status_code == 409
        assert read_policy(org) == second
        audit = rows("SELECT old_record,new_record,actor_user_id,reason, "
            "new_record->>'labor_rate' AS labor,old_record->>'margin' AS old_margin,new_record->>'margin' AS new_margin "
            "FROM public.price_audit_logs "
            "WHERE org_id=%s AND entity='workshop_pricing_policies' ORDER BY event_order", [org])
        assert len(audit) == 2
        assert audit[0]['old_record'] is None
        assert D(audit[0]['labor']) == D('30.1234')
        assert D(audit[1]['old_margin']) == D('.35') and D(audit[1]['new_margin']) == D('.4')
        assert audit[1]['actor_user_id'] == users['OWNER'] and audit[1]['reason'] == 'Ajustar margen'


def test_existing_advanced_rates_are_suggested_without_mutating_them(commercial_rows):
    org, _, users = commercial_rows
    seed_commercial_project(org, users['OWNER'])
    with as_user(users['OWNER']):
        before = one('SELECT * FROM public.pricing_rules WHERE org_id=%s', [org])
        current = read_policy(org)
        assert current['labor_rate'] == D('15') and current['installation_rate'] == D('12')
        save_policy(org, policy_values(), 0, 'Nueva política simple')
        assert one('SELECT * FROM public.pricing_rules WHERE org_id=%s', [org]) == before


@pytest.mark.parametrize('role', ['ESTIMATOR', 'WORKSHOP_MANAGER', 'INSTALLER'])
def test_policy_costs_and_edits_are_owner_only(commercial_rows, role):
    org, other, users = commercial_rows
    with as_user(users['OWNER']):
        save_policy(org, policy_values(), 0, 'Privacidad')
        assert rows('SELECT id FROM public.workshop_pricing_policies WHERE org_id=%s', [other]) == []
    with as_user(users[role]):
        assert rows('SELECT * FROM public.workshop_pricing_policies') == []
        assert rows('UPDATE public.workshop_pricing_policies SET margin=.5 RETURNING id') == []
    client = owner_client(users[role])
    assert client.get('/api/v1/pricing/simple-policy/').status_code == 403
    assert client.put('/api/v1/pricing/simple-policy/', {'values': values(), 'expected_revision': 0,
        'reason': 'No autorizado'}, format='json').status_code == 403


def test_database_enforces_currency_revision_identity_and_append_only_history(commercial_rows):
    org, other, users = commercial_rows
    with as_user(users['OWNER']):
        save_policy(org, policy_values(), 0, 'Reglas persistidas')
        for assignment in ('rounding_step=.5', 'margin=1', "labor_basis='BAR'", "labor_rate='NaN'",
            f"org_id='{other}'", f"id='{uuid4()}'"):
            with pytest.raises(DatabaseError), transaction.atomic():
                rows('UPDATE public.workshop_pricing_policies SET ' + assignment + ' WHERE org_id=%s RETURNING id', [org])
        record = one('UPDATE public.workshop_pricing_policies SET revision=99 WHERE org_id=%s RETURNING revision', [org])
        assert record['revision'] == 2
        with pytest.raises(DatabaseError), transaction.atomic():
            rows('DELETE FROM public.workshop_pricing_policies WHERE org_id=%s RETURNING id', [org])
        with pytest.raises(DatabaseError), transaction.atomic():
            rows("UPDATE public.price_audit_logs SET reason='Cambio de historia' WHERE org_id=%s RETURNING id", [org])


def test_real_example_preserves_material_authority_without_persisting_prices(commercial_rows):
    org, other, users = commercial_rows
    project = seed_commercial_project(org, users['OWNER'])
    position = one('SELECT * FROM public.project_positions WHERE project_id=%s', [project])
    before = one('SELECT * FROM public.projects WHERE id=%s', [project])
    with as_user(users['OWNER']):
        result = policy_example(org, policy_values(), position['id'])
        # Independent fixed-window oracle: bars 193 + glass .8281*100 = 275.81.
        assert result['breakdown']['materials'] == fixture_materials()
        with localcontext() as context:
            context.prec = 256
            assert result['breakdown']['direct_cost'] == fixture_materials() + D('30.1234') + D('12.3456')
        assert result['breakdown']['unit_net'] == D('490')
        assert result['project_tax'] == D('93') and result['project_gross'] == D('583')
        with pytest.raises(ContractAPIException) as missing:
            policy_example(other, policy_values(), position['id'])
        assert missing.value.status_code == 404
        with commercial_backend():
            assert rows('SELECT id FROM public.pricing_operations WHERE org_id=%s', [org]) == []
    assert one('SELECT * FROM public.project_positions WHERE id=%s', [position['id']]) == position
    assert one('SELECT * FROM public.projects WHERE id=%s', [project]) == before


def test_changing_workshop_policy_never_rewrites_an_applied_operation(commercial_rows):
    org, _, users = commercial_rows
    project = seed_commercial_project(org, users['OWNER'])
    with as_user(users['OWNER']), commercial_backend():
        candidate = preview(org, tenant(org, 'OWNER'), price_request(project, users['OWNER']))
        apply_operation(org, users['OWNER'], 'OWNER', candidate['id'], 'Aplicar histórico', False)
    operation = one('SELECT * FROM public.pricing_operations WHERE id=%s', [candidate['id']])
    prior = one('SELECT * FROM public.projects WHERE id=%s', [project])
    with as_user(users['OWNER']):
        save_policy(org, policy_values(margin='.50'), 0, 'Solo borradores nuevos')
    assert one('SELECT * FROM public.pricing_operations WHERE id=%s', [candidate['id']]) == operation
    assert one('SELECT * FROM public.projects WHERE id=%s', [project]) == prior


@pytest.mark.parametrize('saved', [False, True])
def test_concurrent_first_or_later_save_never_loses_an_edit(committed_commercial_rows, saved):
    org, _, users = committed_commercial_rows
    if saved:
        with as_user(users['OWNER']):
            save_policy(org, policy_values(), 0, 'Preparar concurrencia')
    ready = Barrier(2)

    def writer(margin):
        close_old_connections()
        try:
            ready.wait(timeout=10)
            return owner_client(users['OWNER']).put('/api/v1/pricing/simple-policy/', {
                'values': values(margin=margin), 'expected_revision': int(saved), 'reason': 'Guardar concurrente'}, format='json')
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = [pool.submit(writer, margin) for margin in ('.40', '.50')]
        responses = [item.result(timeout=15) for item in pending]
    assert sorted(response.status_code for response in responses) == [200, 409]
    with as_user(users['OWNER']):
        current = read_policy(org)
        assert current['revision'] == int(saved) + 1
        winner = next(response.json() for response in responses if response.status_code == 200)
        assert current['margin'] == D(winner['margin'])


def test_example_http_is_one_read_snapshot_and_owner_only(committed_commercial_rows, monkeypatch):
    org, _, users = committed_commercial_rows
    project = seed_commercial_project(org, users['OWNER'])
    position = one('SELECT id FROM public.project_positions WHERE project_id=%s', [project])['id']
    paused, resume = Event(), Event()
    original = PricingRepository.cost

    def paused_cost(repo, sku, unit):
        result = original(repo, sku, unit)
        if not paused.is_set():
            paused.set()
            assert resume.wait(10)
        return result

    monkeypatch.setattr(PricingRepository, 'cost', paused_cost)
    payload = {'values': values(labor_rate='30.1234', installation_rate='12.3456', rounding_step='10'),
        'position_id': str(position)}

    def request():
        close_old_connections()
        try:
            return owner_client(users['OWNER']).post('/api/v1/pricing/simple-policy/example/', payload, format='json')
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(request)
        assert paused.wait(10)
        with as_user(users['OWNER']):
            rows('UPDATE public.cost_list_items SET unit_cost=200 WHERE org_id=%s RETURNING id', [org])
        resume.set()
        result = pending.result(timeout=15)
    assert result.status_code == 200, result.content
    assert D(result.json()['breakdown']['materials']) == fixture_materials()
    assert D(result.json()['project_net']) == D('490')
    assert owner_client(users['ESTIMATOR']).post('/api/v1/pricing/simple-policy/example/', payload, format='json').status_code == 403
    assert rows('SELECT id FROM public.pricing_operations WHERE org_id=%s', [org]) == []


def test_policy_http_exact_round_trip_mfa_and_active_tenant(committed_commercial_rows):
    org, other, users = committed_commercial_rows
    client = owner_client(users['OWNER'])
    endpoint = '/api/v1/pricing/simple-policy/'
    suggested = client.get(endpoint)
    assert suggested.status_code == 200 and suggested.json()['saved'] is False
    payload = {'values': values(), 'expected_revision': 0, 'reason': 'Configuración del taller'}
    saved = client.put(endpoint, payload, format='json')
    assert saved.status_code == 200, saved.content
    assert saved.json()['labor_rate'] == '15000.1234' and saved.json()['revision'] == 1
    assert client.get(endpoint).json() == saved.json()
    assert client.put(endpoint, payload, format='json').status_code == 409
    assert client.get(endpoint, HTTP_X_ORGANIZATION_ID=str(other)).status_code == 403
    token = commercial_tests.VerifiedSupabaseToken(access_token='verified-token',
        user_id=users['OWNER'], email='owner@fixture.local', aal='aal1',
        claims={'sub': str(users['OWNER']), 'role': 'authenticated', 'aal': 'aal1'})
    client.force_authenticate(user=commercial_tests.SupabaseUser(id=users['OWNER'], email='owner@fixture.local'), token=token)
    assert client.get(endpoint).status_code == 403


def test_empty_example_asks_for_a_window_without_inventing_a_price(committed_commercial_rows):
    _, _, users = committed_commercial_rows
    response = owner_client(users['OWNER']).post('/api/v1/pricing/simple-policy/example/',
        {'values': values()}, format='json')
    assert response.status_code == 200, response.content
    assert response.json()['position_id'] is None
    assert response.json()['breakdown'] is None and response.json()['project_net'] is None
