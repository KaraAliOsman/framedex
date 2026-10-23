"""P05 projections on real snapshots, ledger, orders and caller RLS."""

from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from analytics.prepared import prepared_quotations
from analytics.today import quotation_rows, quote_public, local_today
from backend.tests.integration.test_shot09_documentary import (
    documentary_tenant as documentary_tenant, as_user, _seed_project, _freeze,
)
from pricing.repository import json_text, one, rows
from production.service import release_production
from projects.progress import project_progress
from projects.service import list_projects, start_successor

pytestmark = pytest.mark.rls_integration


def progress(org, actor, project):
    with as_user(actor):
        return project_progress(org, [project])[str(project)]


def link(org, actor, project, version, source):
    return one("INSERT INTO public.customer_approvals(org_id,project_id,project_version_id,token_hash,"
        "expires_at,created_by,link_source) VALUES(%s,%s,%s,%s,now()+interval '30 days',%s,%s) RETURNING id",
        [org, project, version, uuid4().hex + uuid4().hex, actor, source])['id']


def test_document_is_not_a_send_and_successor_does_not_inherit_progress(documentary_tenant):
    org, other, users, outsider = documentary_tenant
    owner = users['OWNER']
    project, _, operation = _seed_project(org, owner)
    assert progress(org, owner, project)['stage'] == 'QUOTING'
    frozen = _freeze(org, owner, project, operation)
    before = one('SELECT snapshot_json::text AS snapshot FROM project_versions WHERE id=%s', [frozen['id']])
    link(org, owner, project, frozen['id'], 'DOCUMENT')
    assert progress(org, owner, project)['stage'] == 'QUOTING'
    with as_user(owner):
        assert quote_public(quotation_rows(org)[0], local_today(org))['state'] == 'unshared'
    link(org, owner, project, frozen['id'], 'SHARE')
    for role in ('OWNER', 'ESTIMATOR', 'WORKSHOP_MANAGER'):
        with as_user(users[role]):
            item, = list_projects(org)
            assert item['progress']['stage'] == 'SENT'
            assert item['progress']['quoted_total'] == item['total_price_gross']
            assert not {'snapshot_json', 'cost', 'margin', 'profit'} & item['progress'].keys()
    with as_user(outsider):
        assert project_progress(org, [project]) == {}
        assert list_projects(other) == []
    with as_user(owner):
        start_successor(org, project)
    assert progress(org, owner, project) == {
        'stage': 'QUOTING', 'reason': 'Revisión en preparación.', 'quoted_total': None, 'currency': None,
    }
    assert one('SELECT snapshot_json::text AS snapshot FROM project_versions WHERE id=%s', [frozen['id']]) == before


def test_complete_installation_requires_real_payments(documentary_tenant):
    org, _, users, _ = documentary_tenant
    owner = users['OWNER']
    project, _, operation = _seed_project(org, owner)
    frozen = _freeze(org, owner, project, operation)
    with as_user(users['WORKSHOP_MANAGER']):
        released = release_production(org_id=org, version_id=UUID(frozen['id']), actor_id=users['WORKSHOP_MANAGER'])
    assert released['orders']
    assert progress(org, owner, project)['stage'] == 'WORKSHOP'
    # Seed the physical event only in this rolled-back synthetic fixture.
    rows("UPDATE public.orders SET status='INSTALLED' WHERE org_id=%s AND project_id=%s RETURNING id", [org, project])
    result = progress(org, owner, project)
    assert result['stage'] == 'TO_COLLECT'
    total = Decimal(result['quoted_total'])

    def payment(simulated):
        return one("INSERT INTO public.project_payments(org_id,project_id,kind,amount,method,operation_key,recorded_by,simulated,recorded_at) "
            "VALUES(%s,%s,'SALDO',%s,'TRANSFER',%s,%s,%s,now()) RETURNING id",
            [org, project, total, str(uuid4()), owner, simulated])['id']

    simulated = payment(True)
    assert progress(org, owner, project)['stage'] == 'TO_COLLECT'
    rows("UPDATE public.project_payments SET voided_at=now(),voided_by=%s,void_reason='Fin de simulación' WHERE id=%s RETURNING id", [owner, simulated])
    real = payment(False)
    assert progress(org, owner, project)['stage'] == 'CLOSED'
    remake = one("INSERT INTO public.orders(org_id,project_id,order_type,order_code,status,payload_json,project_version_id) "
        "SELECT org_id,project_id,order_type,order_code||'-R1','RELEASED',"
        "payload_json||jsonb_build_object('remake_of',id::text),project_version_id "
        "FROM public.orders WHERE org_id=%s AND project_id=%s ORDER BY id LIMIT 1 RETURNING id", [org, project])['id']
    assert progress(org, owner, project)['stage'] == 'WORKSHOP'
    rows("UPDATE public.orders SET status='CANCELLED' WHERE id=%s RETURNING id", [remake])
    assert progress(org, owner, project)['stage'] == 'CLOSED'
    rows("UPDATE public.project_payments SET voided_at=now(),voided_by=%s,void_reason='Pago equivocado' WHERE id=%s RETURNING id", [owner, real])
    assert progress(org, owner, project)['stage'] == 'TO_COLLECT'


def test_progress_uses_chosen_alternative_orders_and_total(documentary_tenant):
    from backend.tests.integration.test_proposal_v2 import offered_alternative, response
    from portal.service import decide_quote

    org, _, users, _ = documentary_tenant
    project, _, version_a, version_b, token = offered_alternative(org, users['OWNER'])
    accepted = decide_quote(**response(token, selected='REV-A'))
    with as_user(users['WORKSHOP_MANAGER']):
        release_production(org_id=org, version_id=version_a, actor_id=users['WORKSHOP_MANAGER'])
    result = progress(org, users['OWNER'], project)
    assert result['stage'] == 'WORKSHOP'
    assert result['quoted_total'] == accepted['total_price_gross']
    assert version_a != version_b


def test_ai_prepared_requires_saved_windows_verified_object_and_same_user(documentary_tenant):
    org, other, users, outsider = documentary_tenant
    owner = users['OWNER']
    project, _, _ = _seed_project(org, owner, apply_pricing=False)
    empty = one("INSERT INTO public.projects(org_id,code,name,client_name,created_by) VALUES(%s,%s,'Vacía','',%s) RETURNING id",
                [org, 'P-' + uuid4().hex[:8], owner])['id']

    def job(identity, *, user=owner, status='applied', state='SUCCEEDED'):
        one("INSERT INTO public.ai_jobs(org_id,user_id,surface,goal,state,result,receipt) "
            "VALUES(%s,%s,'projects','Cotiza las ventanas',%s,%s::jsonb,%s::jsonb) RETURNING id",
            [org, user, state, json_text({'created_project': {'project_id': str(identity)}}),
             json_text({'objects': [{'kind': 'project', 'id': str(identity), 'status': status}]})])

    job(project, status='blocked')
    job(empty)
    with as_user(owner):
        assert prepared_quotations(org, owner, 'OWNER') == {'count': 0, 'items': []}
    job(project)
    job(project)  # two rounds/runs still describe one saved quotation
    with as_user(owner):
        result = prepared_quotations(org, owner, 'OWNER')
        assert result['count'] == 1 and result['items'][0]['project_id'] == str(project)
    with as_user(users['ESTIMATOR']):
        assert prepared_quotations(org, users['ESTIMATOR'], 'ESTIMATOR')['count'] == 0
        # Supplying the other member's id cannot bypass ai_jobs RLS.
        assert prepared_quotations(org, owner, 'ESTIMATOR')['count'] == 0
    with as_user(outsider):
        assert prepared_quotations(other, outsider, 'OWNER')['count'] == 0
        assert prepared_quotations(org, owner, 'OWNER')['count'] == 0
    with as_user(users['WORKSHOP_MANAGER']):
        assert prepared_quotations(org, users['WORKSHOP_MANAGER'], 'WORKSHOP_MANAGER')['count'] == 0


def test_five_hundred_projects_use_three_progress_reads(documentary_tenant):
    org, _, users, _ = documentary_tenant
    rows("INSERT INTO public.projects(org_id,code,name,client_name,created_by) "
         "SELECT %s,'P-'||n,'Nombre largo de obra '||repeat('Ñ',180),'',%s FROM generate_series(1,500) n RETURNING id",
         [org, users['OWNER']])
    with as_user(users['OWNER']), CaptureQueriesContext(connection) as queries:
        result = list_projects(org)
    assert len(result) == 500
    assert all(item['progress']['stage'] == 'QUOTING' for item in result)
    # Role enter/restore statements count too; no query count scales with rows.
    assert len(queries) < 30


def test_suggested_queue_only_uses_current_values_of_series_in_drafts(documentary_tenant):
    from analytics.today import suggested_actions
    from backend.tests.integration.test_catalog_series_sheet import create
    from catalogs.series import confirm_cells

    org, _, users, _ = documentary_tenant
    owner = users['OWNER']
    project, position, _ = _seed_project(org, owner, apply_pricing=False)
    with as_user(owner):
        sheet = create(org, owner)
    rows('UPDATE public.project_positions SET system_id=%s WHERE id=%s RETURNING id', [sheet['id'], position])
    with as_user(owner):
        item, = suggested_actions(org)
        assert item['entity_name'] == 'Proline PRO6004'
        assert item['href'] == f"/catalogs/systems?system={sheet['id']}"
        assert not item['blocking']
        suggested = [{key: value[key] for key in ('resource', 'row_id', 'field')}
                     for value in sheet['cells'] if value['origin'] == 'SUGGESTED']
        confirm_cells(org, sheet['id'], owner, {'revision': sheet['revision'], 'cells': suggested})
        assert suggested_actions(org) == []
