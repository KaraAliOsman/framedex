"""Works pagination and legacy commercial cohorts under actual tenant RLS."""

from itertools import product
from uuid import uuid4

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from analytics.today import quotations
from authentication.errors import ContractAPIException
from backend.tests.integration.test_shot08_pricing import owner_client
from backend.tests.integration.test_shot09_documentary import (
    documentary_tenant as documentary_tenant, as_user, _seed_project, _freeze,
)
from pricing.repository import one, rows
from projects.service import list_projects, start_successor
from projects.works import WorksQuerySerializer, WorksResponseSerializer, works_index
from projects import works

pytestmark = pytest.mark.rls_integration


def seed_empty(org, owner, count):
    return rows("INSERT INTO public.projects(org_id,code,name,client_name,created_by,updated_at) "
        "SELECT %s,%s||n,'Obra '||lpad(n::text,4,'0'),'Cliente sintético',%s,now()+interval '1 day' "
        "FROM generate_series(1,%s) n RETURNING id,code", [org, uuid4().hex, owner, count])


def read(user, org, query=None, expected=200):
    result = owner_client(user).get('/api/v1/projects/works/', query or {},
                                   HTTP_X_ORGANIZATION_ID=str(org))
    assert result.status_code == expected, result.data
    return result.json()


def test_all_works_beyond_recent_500_paginate_and_count_before_stage(documentary_tenant):
    org, _, users, _ = documentary_tenant
    created = seed_empty(org, users['OWNER'], 505)
    old = created[0]['id']
    rows("UPDATE public.projects SET name='Antigua Ñandú',updated_at=now()-interval '5 years' "
         "WHERE id=%s RETURNING id", [old])
    with as_user(users['OWNER']):
        assert str(old) not in {str(item['id']) for item in list_projects(org)}
        with CaptureQueriesContext(connection) as queries:
            result = works_index(org, 'OWNER', offset=500)
        assert len(queries) < 30  # count does not scale with 505 project rows
        assert result['total'] == result['matching'] == result['counts']['QUOTING'] == 505
        assert len(result['items']) == 5
        assert str(result['items'][-1]['id']) == str(old)
        assert all(item['quotation'] is None for item in result['items'])
        assert works_index(org, 'OWNER', stage='SENT')['counts']['QUOTING'] == 505
        assert works_index(org, 'OWNER', stage='SENT')['total'] == 0
        found = works_index(org, 'OWNER', q='ñANDÚ')
        assert found['total'] == found['matching'] == 1
        assert str(found['items'][0]['id']) == str(old)
        assert works_index(org, 'OWNER', offset=9999)['items'] == []
        assert works_index(org, 'OWNER', q='does not exist')['counts']['QUOTING'] == 0
    # Explicit IDs still execute member RLS and cannot retrieve another tenant.
    assert read(users['OWNER'], org, {'offset': 500})['total'] == 505


def test_quotation_filters_keep_exact_legacy_membership_and_arbitrary_offset(documentary_tenant):
    org, _, users, _ = documentary_tenant
    owner = users['OWNER']
    issued, _, operation = _seed_project(org, owner)
    version = _freeze(org, owner, issued, operation)
    _seed_project(org, owner, apply_pricing=False)
    seed_empty(org, owner, 501)
    snapshot = one('SELECT snapshot_json::text AS value FROM project_versions WHERE id=%s', [version['id']])
    with as_user(owner):
        assert str(issued) not in {str(item['id']) for item in list_projects(org)}
        for attention, phase, currency, offset in product(
            ('', 'expiring', 'viewed', 'response', 'expired', 'unshared', 'pending', 'approved', 'link_expired'),
            ('', 'QUOTED', 'APPROVED'), ('', 'CLP', 'USD', 'unknown'), (0, 1),
        ):
            legacy = quotations(org, query='REV-A', attention=attention, phase=phase,
                                currency=currency, offset=offset, limit=1)
            current = works_index(org, 'OWNER', view='quotes', q='REV-A', attention=attention,
                                  phase=phase, currency=currency, offset=offset, limit=1)
            assert current['total'] == current['matching'] == legacy['total']
            assert [item['quotation'] for item in current['items']] == legacy['items']
            assert current['offset'] == offset
        implicit = works_index(org, 'OWNER', attention='unshared')
        assert implicit['total'] == 1 and str(implicit['items'][0]['id']) == str(issued)
        assert implicit['counts']['QUOTING'] == 1
        start_successor(org, issued)
        assert works_index(org, 'OWNER', view='quotes')['items'] == []
    assert one('SELECT snapshot_json::text AS value FROM project_versions WHERE id=%s', [version['id']]) == snapshot


def test_index_roles_cross_tenant_and_serialized_allowlist(documentary_tenant):
    org, other, users, outsider = documentary_tenant
    seed_empty(org, users['OWNER'], 1)
    with connection.cursor() as cursor:
        users['OPERATOR'] = uuid4()
        cursor.execute("INSERT INTO public.tenancy_memberships(org_id,user_id,role) VALUES(%s,%s,'OPERATOR')",
                       [org, users['OPERATOR']])
    for role, user in users.items():
        permitted = role in {'OWNER', 'ESTIMATOR', 'WORKSHOP_MANAGER'}
        output = read(user, org, expected=200 if permitted else 403)
        if permitted:
            assert len(output['items']) == 1
            assert not {'snapshot_json', 'cost', 'margin', 'profit'} & output['items'][0].keys()
            serializer = WorksResponseSerializer(data=output)
            assert serializer.is_valid(), serializer.errors
        for query in ({'view': 'quotes'}, {'attention': 'viewed'}, {'phase': 'QUOTED'}, {'currency': 'CLP'}):
            read(user, org, query, expected=200 if role in {'OWNER', 'ESTIMATOR'} else 403)
        read(user, other, expected=403)
    with as_user(outsider):
        assert works_index(other, 'OWNER')['items'] == []
        assert works_index(org, 'OWNER')['items'] == []
        assert list_projects(org, project_ids=[uuid4()]) == []


def test_changes_between_selection_and_detail_require_a_fresh_read(documentary_tenant, monkeypatch):
    org, _, users, _ = documentary_tenant
    project, = seed_empty(org, users['OWNER'], 1)
    original = works.project_progress

    def change_after_projection(org_id, identities):
        result = original(org_id, identities)
        rows("UPDATE public.projects SET name='Edición mientras se consulta',updated_at=clock_timestamp() "
             "WHERE id=%s RETURNING id", [project['id']])
        return result

    monkeypatch.setattr(works, 'project_progress', change_after_projection)
    with as_user(users['OWNER']), pytest.raises(ContractAPIException) as caught:
        works_index(org, 'OWNER')
    assert caught.value.status_code == 409
    assert caught.value.contract_code == 'works_changed'


@pytest.mark.parametrize('query', [
    {'stage': 'INVENTED'}, {'status': 'SENT'}, {'view': 'all tenants'},
    {'attention': 'invented'}, {'phase': 'DRAFT'}, {'currency': 'EUR'},
    {'offset': -1}, {'limit': 201}, {'q': 'n' * 256}, {'sort': 'cost'},
])
def test_index_rejects_invalid_filter_values(query):
    assert not WorksQuerySerializer(data=query).is_valid()
