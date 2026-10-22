"""Working prices remain editable, tenant-private and separate from APPLIED."""

from decimal import Decimal as D
from uuid import uuid4

from django.db import DatabaseError, transaction
import pytest

from dekopen_engine.commercial import PricingError
from pricing.repository import commercial_backend, one, rows, json_text
from pricing.simple_policy import save_policy
from pricing.working import refresh_working, working_public
from projects.service import editable
from backend.tests.integration import test_shot08_pricing as commercial_tests
from backend.tests.integration.test_shot08_pricing import (
    as_user, tenant, seed_commercial_project, price_request, preview, apply_operation,
)
from backend.tests.integration.test_simple_pricing_policy import policy_values

pytestmark = pytest.mark.rls_integration
commercial_rows = commercial_tests.commercial_rows


def test_three_windows_get_a_working_total_and_policy_change_never_applies_it(commercial_rows):
    org, _, users = commercial_rows
    project = seed_commercial_project(org, users['OWNER'])
    for index in (2, 3):
        one('INSERT INTO public.project_positions(org_id,project_id,position_index,quantity,typology,system_id,'
            'width_mm,height_mm,parametric_tree,bom_snapshot) SELECT org_id,project_id,%s,quantity,typology,system_id,'
            'width_mm,height_mm,parametric_tree,bom_snapshot FROM public.project_positions '
            'WHERE project_id=%s AND position_index=1 RETURNING id', [index, project])
    before = one('SELECT * FROM public.projects WHERE id=%s', [project])
    with as_user(users['OWNER']):
        save_policy(org, policy_values(), 0, 'Mis precios')
        first = refresh_working(org, tenant(org, 'OWNER'), project)
        public = working_public(first, 'OWNER')
        assert public['state'] == 'READY'
        assert D(public['project_net']) == D('1470') and D(public['project_gross']) == D('1749')
        assert len(public['lines']) == 3 and all(D(item['unit_price']) == D('490') for item in public['lines'])
        assert all('e' not in amount.lower() for item in public['lines'] for amount in item['breakdown'].values())
        assert editable(org, project)['id'] == project
        assert first['policy_revision'] == 1
        save_policy(org, policy_values(margin='.50'), 1, 'Margen nuevo')
        second = refresh_working(org, tenant(org, 'OWNER'), project)
        assert second['policy_revision'] == 2
        assert D(working_public(second, 'OWNER')['project_net']) == D('1920')
        with commercial_backend():
            assert rows('SELECT id FROM public.pricing_operations WHERE org_id=%s', [org]) == []
    assert one('SELECT * FROM public.projects WHERE id=%s', [project]) == before
    assert all(item['price_net'] == 0 for item in rows('SELECT price_net FROM public.project_positions WHERE project_id=%s', [project]))


def test_suggested_policy_prices_a_quotable_window_without_implicit_confirmation(commercial_rows):
    org, _, users = commercial_rows
    project = seed_commercial_project(org, users['OWNER'])
    with as_user(users['OWNER']):
        value = refresh_working(org, tenant(org, 'OWNER'), project)
        assert value['state'] == 'READY' and value['policy_revision'] == 0
        assert D(working_public(value, 'OWNER')['project_net']) == D('1000')
        assert rows('SELECT id FROM public.workshop_pricing_policies WHERE org_id=%s', [org]) == []


def test_missing_material_price_clears_old_working_total_without_erasing_design(commercial_rows):
    org, _, users = commercial_rows
    project = seed_commercial_project(org, users['OWNER'])
    with as_user(users['OWNER']):
        save_policy(org, policy_values(), 0, 'Mis precios')
        assert refresh_working(org, tenant(org, 'OWNER'), project)['state'] == 'READY'
        rows('UPDATE public.cost_lists SET is_active=false WHERE org_id=%s RETURNING id', [org])
        blocked = refresh_working(org, tenant(org, 'OWNER'), project)
        public = working_public(blocked, 'OWNER')
        assert public['state'] == 'BLOCKED' and public['project_net'] is None and public['lines'] == []
        assert public['error']['code'] == 'cost_list_not_found'
        assert editable(org, project)['id'] == project
    assert len(rows('SELECT id FROM public.project_positions WHERE project_id=%s', [project])) == 1


def test_working_cache_and_breakdown_keep_tenant_and_cost_privacy(commercial_rows):
    org, other, users = commercial_rows
    project = seed_commercial_project(org, users['OWNER'])
    with as_user(users['OWNER']):
        save_policy(org, policy_values(), 0, 'Mis precios')
    with as_user(users['ESTIMATOR']):
        value = refresh_working(org, tenant(org, 'ESTIMATOR'), project)
        public = working_public(value, 'ESTIMATOR')
        assert public['state'] == 'READY' and D(public['project_net']) == D('490')
        assert set(public['lines'][0]) == {'position_index', 'quantity', 'unit_price', 'discount_pct', 'line_net'}
        with pytest.raises(DatabaseError), transaction.atomic():
            rows('SELECT * FROM public.project_working_prices')
        with pytest.raises(PricingError):
            refresh_working(other, tenant(other, 'ESTIMATOR'), project)
        with commercial_backend():
            assert rows('SELECT * FROM public.project_working_prices WHERE org_id=%s', [other]) == []
    with as_user(users['INSTALLER']), pytest.raises(PricingError, match='pricing_permission_denied'):
        refresh_working(org, tenant(org, 'INSTALLER'), project)


def test_an_applied_revision_keeps_its_working_cache_and_money_unchanged(commercial_rows):
    org, _, users = commercial_rows
    project = seed_commercial_project(org, users['OWNER'])
    with as_user(users['OWNER']):
        cached = refresh_working(org, tenant(org, 'OWNER'), project)
        with commercial_backend():
            operation = preview(org, tenant(org, 'OWNER'), price_request(project, users['OWNER']))
            apply_operation(org, users['OWNER'], 'OWNER', operation['id'], 'Aplicar histórico', False)
        save_policy(org, policy_values(margin='.50'), 0, 'Solo trabajo futuro')
        assert refresh_working(org, tenant(org, 'OWNER'), project) is None
        with commercial_backend():
            assert one('SELECT * FROM public.project_working_prices WHERE project_id=%s', [project]) == cached
            with pytest.raises(DatabaseError), transaction.atomic():
                rows("UPDATE public.project_working_prices SET state='BLOCKED' WHERE project_id=%s RETURNING project_id", [project])
    assert one('SELECT total_price_net FROM public.projects WHERE id=%s', [project])['total_price_net'] == D('500')


@pytest.mark.parametrize('mode', ['COST_PLUS_MARGIN', 'PRICE_PER_M2_BY_TYPOLOGY',
    'FIXED_PRICE_MATRIX_DIMENSIONAL', 'TARGET_GROSS_MARGIN_PROJECT', 'COMMERCIAL_LIST_WITH_DISCOUNTS'])
def test_advanced_modes_keep_their_projection_and_do_not_apply(commercial_rows, mode):
    org, _, users = commercial_rows
    project = seed_commercial_project(org, users['OWNER'])
    with as_user(users['OWNER']):
        rows('UPDATE public.pricing_rules SET pricing_mode=%s WHERE org_id=%s RETURNING id', [mode, org])
        save_policy(org, policy_values(use_advanced=True), 0, 'Usar precios avanzados')
        working = refresh_working(org, tenant(org, 'OWNER'), project)
        assert working['state'] == 'READY'
        public = working_public(working, 'OWNER')
        expected = '500' if mode in ('COST_PLUS_MARGIN', 'TARGET_GROSS_MARGIN_PROJECT') else '2000'
        assert D(public['project_net']) == D(expected)
        with commercial_backend():
            assert rows('SELECT id FROM public.pricing_operations WHERE org_id=%s', [org]) == []


def test_working_cache_identity_and_draft_guard_cannot_be_bypassed(commercial_rows):
    org, _, users = commercial_rows
    project = seed_commercial_project(org, users['OWNER'])
    with as_user(users['OWNER']):
        refresh_working(org, tenant(org, 'OWNER'), project)
        with commercial_backend():
            for assignment in ("revision_code='REV-B'", f"project_id='{uuid4()}'"):
                with pytest.raises(DatabaseError), transaction.atomic():
                    rows('UPDATE public.project_working_prices SET ' + assignment +
                        ' WHERE project_id=%s RETURNING project_id', [project])


def test_explicit_project_installation_replaces_the_simple_window_installation(commercial_rows):
    from dekopen_engine.extra_models import ExtraPolicy
    from engine.tests.extra_cases import installation
    from projects.extras import extra_backend

    org, _, users = commercial_rows
    project = seed_commercial_project(org, users['OWNER'])
    with as_user(users['OWNER']):
        save_policy(org, policy_values(), 0, 'Mis precios')
        with extra_backend():
            rows('INSERT INTO public.organization_extra_settings(org_id,policy,revision) '
                'VALUES(%s,%s::jsonb,1) RETURNING org_id',
                [org, json_text(ExtraPolicy(services=[installation()]).model_dump(mode='json'))])
            rows('INSERT INTO public.project_extra_services(org_id,project_id,revision_code,selections) '
                "VALUES(%s,%s,'REV-A',%s::jsonb) RETURNING project_id", [org, project, json_text([{'code': 'INSTALL'}])])
        priced = refresh_working(org, tenant(org, 'OWNER'), project)
        assert priced['state'] == 'READY'
        public = working_public(priced, 'OWNER')
        assert D(public['lines'][0]['breakdown']['installation']) == 0
        assert D(public['project_net']) == D('6480')
