"""Bounded proposal reads retain exact stock, confidentiality and MFA gates."""

from datetime import date
from decimal import Decimal

from django.db import connection
import pytest

from authentication.rls import authenticated_rls_context
from backend.tests.integration.test_rls_context_integration import real_rows as real_rows
from backend.tests.integration.test_shot08_pricing import (
    commercial_rows as commercial_rows, as_user, make_list,
)
from dekopen_engine.commercial import PricingError
from dekopen_engine.cutting import MissingStockAuthority
from engine_api.cutting_repository import CuttingRepository
from pricing.repository import PricingRepository, commercial_backend, rows

pytestmark = pytest.mark.rls_integration


@pytest.mark.parametrize('role', ['OWNER', 'ESTIMATOR', 'WORKSHOP_MANAGER', 'INSTALLER'])
@pytest.mark.parametrize('aal', ['aal1', 'aal2'])
def test_set_read_scope_matches_existing_permission_and_mfa(commercial_rows, role, aal):
    org, other, users = commercial_rows
    with connection.cursor() as cursor:
        cursor.execute('UPDATE public.tenancy_organizations SET require_mfa=true WHERE id=%s', [org])
    with authenticated_rls_context({'sub':str(users[role]), 'aal':aal}), commercial_backend():
        allowed = rows('SELECT private.pricing_role(%s,ARRAY[\'OWNER\',\'ESTIMATOR\',\'WORKSHOP_MANAGER\']) AS allowed', [org])[0]['allowed']
        visible = {row['org_id'] for row in rows('SELECT private.pricing_read_org_ids() AS org_id')}
        assert (org in visible) == allowed == (role != 'INSTALLER' and aal == 'aal2')
        assert other not in visible
    with connection.cursor() as cursor:
        cursor.execute('UPDATE public.tenancy_memberships SET is_active=false WHERE org_id=%s AND user_id=%s', [org, users[role]])
    with authenticated_rls_context({'sub':str(users[role]), 'aal':'aal2'}), commercial_backend():
        assert rows('SELECT private.pricing_read_org_ids() AS org_id') == []


def test_cost_reuse_keeps_unit_refusal_and_new_proposal_reads_updates(commercial_rows):
    org, _, users = commercial_rows
    with as_user(users['OWNER']):
        parent = make_list(org, date(2026,9,1), '1.2345')
        with commercial_backend():
            repo = PricingRepository(org, date(2026,9,10), 'CLP', request_cache=True)
            assert repo.cost('SKU-A','M') == Decimal('1.2345')
            with connection.execute_wrapper(lambda *_: pytest.fail('Repeated authority performed SQL')):
                assert repo.cost('SKU-A','M') == Decimal('1.2345')
                with pytest.raises(PricingError, match='incompatible_cost_unit'):
                    repo.cost('SKU-A','BAR')
        with connection.cursor() as cursor:
            cursor.execute('UPDATE public.cost_list_items SET unit_cost=2.3456 WHERE cost_list_id=%s', [parent])
        with commercial_backend():
            assert PricingRepository(org,date(2026,9,10),'CLP',request_cache=True).cost('SKU-A','M') == Decimal('2.3456')


def test_prefetched_stock_matches_live_reads_without_further_queries(real_rows, django_db_blocker):
    with django_db_blocker.unblock(), authenticated_rls_context(real_rows.tokens['A'].claims):
        system, org = real_rows.demo_system, real_rows.organizations['A']
        live = CuttingRepository()
        profile = live.profile_stock(system,org,'MARCO','WHITE')
        steel = live.reinforcement_stock(system,org,'MARCO',None,'WHITE')
        snapshot = CuttingRepository(request_cache=True)
        snapshot.prefetch_stocks(system,org)
        with connection.execute_wrapper(lambda *_: pytest.fail('Prefetched authority performed SQL')):
            assert snapshot.profile_stock(system,org,'MARCO','WHITE') == profile
            assert snapshot.reinforcement_stock(system,org,'MARCO',None,'WHITE') == steel
            assert snapshot.reinforcement_stock(system,org,'MARCO',steel[0].workshop_sku,'WHITE') == steel
            with pytest.raises(MissingStockAuthority):
                snapshot.profile_stock(system,org,'UNKNOWN','WHITE')
