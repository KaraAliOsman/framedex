"""P02 addresses: real transactional counters, tenant isolation and triggers."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

from django.db import close_old_connections, connection, DatabaseError, transaction
import pytest

from backend.tests.integration.test_shot08_pricing import committed_commercial_rows as committed_commercial_rows, as_user
from backend.tests.integration.test_shot09_documentary import (
    documentary_tenant as documentary_tenant, _seed_project, _freeze, _order_for_type,
)
from documents.repository import documentary_backend
from pricing.repository import one, rows

pytestmark = pytest.mark.rls_integration


def assign(org, kind, entity):
    return one("SELECT private.assign_entity_code(%s,%s,%s) AS code", [org, kind, entity])["code"]


@pytest.mark.parametrize("kind", ["OC", "RT", "REC"])
def test_concurrent_distinct_and_same_entity_replay(committed_commercial_rows, kind):
    org, other, users = committed_commercial_rows
    barrier = Barrier(2)

    def create(entity):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            with as_user(users["WORKSHOP_MANAGER"]), documentary_backend():
                return assign(org, kind, entity)
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        codes = list(pool.map(create, [uuid4(), uuid4()]))
    assert sorted(codes) == [f"{kind}-000001", f"{kind}-000002"]
    with transaction.atomic():
        assert assign(other, kind, uuid4()) == f"{kind}-000001"
    identity = uuid4()
    with ThreadPoolExecutor(max_workers=2) as pool:
        codes = list(pool.map(create, [identity, identity]))
    assert codes == [f"{kind}-000003"] * 2
    assert one("SELECT count(*) AS n FROM public.entity_codes WHERE org_id=%s AND kind=%s", [org, kind])["n"] == 3


def test_rollback_has_no_visible_hole_and_member_cannot_write(committed_commercial_rows):
    org, other, users = committed_commercial_rows
    with transaction.atomic():
        assert assign(org, "OC", uuid4()) == "OC-000001"
        transaction.set_rollback(True)
    assert assign(org, "OC", uuid4()) == "OC-000001"
    for role in ["OWNER", "ESTIMATOR", "WORKSHOP_MANAGER", "INSTALLER"]:
        with as_user(users[role]):
            assert rows("SELECT code FROM public.entity_codes WHERE org_id=%s", [other]) == []
            with pytest.raises(DatabaseError), transaction.atomic():
                assign(org, "OC", uuid4())
    with as_user(users["WORKSHOP_MANAGER"]), documentary_backend():
        with pytest.raises(DatabaseError, match="entity_code_org_not_visible"), transaction.atomic():
            assign(other, "OC", uuid4())


def test_alias_cannot_be_renamed_deleted_or_reused(committed_commercial_rows):
    org, _, _ = committed_commercial_rows
    identity = uuid4()
    assert assign(org, "RT", identity) == "RT-000001"
    for statement in ["UPDATE public.entity_codes SET code='RT-999999' WHERE org_id=%s",
                      "DELETE FROM public.entity_codes WHERE org_id=%s"]:
        with pytest.raises(DatabaseError, match="entity_code_immutable"), transaction.atomic():
            rows(statement + " RETURNING entity_id", [org])
    assert assign(org, "RT", identity) == "RT-000001"
    assert assign(org, "RT", uuid4()) == "RT-000002"


def test_remnant_insert_trigger_and_org_cascade(committed_commercial_rows):
    org, _, _ = committed_commercial_rows
    identity = uuid4()
    rows("INSERT INTO public.inventory_remnants(id,org_id,kind,sheet_workshop_sku,width_mm,height_mm,origin)"
         " VALUES(%s,%s,'SHEET','P02-SHEET',100,200,'MANUAL') RETURNING id", [identity, org])
    assert one("SELECT private.entity_code(%s,'RT',%s) AS code", [org, identity])["code"] == "RT-000001"
    rows("DELETE FROM public.inventory_remnants WHERE id=%s RETURNING id", [identity])
    assert assign(org, "RT", uuid4()) == "RT-000002"


def test_large_unqualified_piece_history_requires_order_but_qr_stays_scoped(documentary_tenant):
    from documents.repository import DocumentaryError
    from production.pieces import entity_address
    from production.trace import trace_piece

    org, _, users, _ = documentary_tenant
    project, _, _ = _seed_project(org, users['OWNER'])
    candidates = rows("INSERT INTO public.orders(org_id,project_id,order_type,order_code,payload_json)"
        " SELECT %s,%s,'WORKSHOP_OT','OT-P02-HISTORY-'||n,'{}'::jsonb"
        " FROM generate_series(1,101) n RETURNING id", [org, project])
    with as_user(users['OWNER']):
        with pytest.raises(DocumentaryError, match="work_order_piece_order_required"):
            trace_piece(org_id=org, piece_id="P01-U01-M01")
        # The address still searches its one exact OT even in a large history;
        # these synthetic unplanned orders correctly have no physical pieces.
        report = trace_piece(org_id=org, piece_id=entity_address(
            "/production", order=candidates[0]['id'], piece="P01-U01-M01"))
        assert report['matches'] == []


def test_purchase_search_uses_authorized_read_scope_and_no_cross_tenant_leak(documentary_tenant):
    from search.service import search
    from purchasing.service import orders_index
    from inventory.service import order_receiving

    org, other, users, other_user = documentary_tenant
    for tenant, actor in ((org, users['OWNER']), (other, other_user)):
        project, _, operation = _seed_project(tenant, actor)
        frozen = _freeze(tenant, actor, project, operation)
        with as_user(actor):
            order = _order_for_type(tenant, actor, frozen['id'], 'SUPPLIER_GLASS_PO')
        receipt = uuid4()
        rows("INSERT INTO public.order_receipts(id,org_id,order_id,receipt_key)"
             " VALUES(%s,%s,%s,'P02-search') RETURNING id", [receipt, tenant, order])
    for role in ('OWNER', 'ESTIMATOR', 'WORKSHOP_MANAGER'):
        with as_user(users[role]):
            # The palette and the existing Purchasing endpoints share their
            # authorized documentary read scope, beyond direct-table grants.
            visible_order = orders_index(org)['orders'][0]
            assert visible_order['order_code'] == 'OC-000001'
            receiving = order_receiving(org_id=org, order_id=visible_order['id'])
            assert receiving['receipts'][0]['receipt_code'] == 'REC-000001'
            for code in ('OC-000001', 'REC-000001'):
                found = search(org, code, role)['results']
                assert len(found) == 1 and found[0]['title'] == code
                assert found[0]['path'].startswith('/purchasing?')
                assert search(other, code, role)['results'] == []
    with as_user(users['INSTALLER']):
        assert search(org, 'OC-000001', 'INSTALLER')['results'] == []
        assert search(org, 'REC-000001', 'INSTALLER')['results'] == []
    operator = uuid4()
    rows("INSERT INTO public.tenancy_memberships(org_id,user_id,role) VALUES(%s,%s,'OPERATOR') RETURNING user_id", [org, operator])
    with as_user(operator):
        assert search(org, 'OC-000001', 'OPERATOR')['results'] == []
