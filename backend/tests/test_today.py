"""Current-revision follow-up and exact ledger projections, never repricing."""
from contextlib import nullcontext
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from urllib.parse import parse_qs, urlparse
from uuid import uuid4
from types import SimpleNamespace

import pytest

from analytics import today
from analytics.serializers import QuotationIndexQuerySerializer

DAY = date(2026, 10, 9)


def quotation(**changes):
    return {"id": uuid4(), "code": "P-000012", "name": "Obra Prat", "client_name": "Cliente Prat",
            "status": "QUOTED", "current_revision": "REV-B", "valid_until": "2026-10-11",
            "total": "12345678901234567890.12", "currency": "CLP", "response_status": "PENDING",
            "shared_at": datetime(2026, 10, 8, tzinfo=timezone.utc), "decided_note": None,
            "view_count": 2, "last_viewed_at": datetime(2026, 10, 8, tzinfo=timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(days=10), **changes}


def test_attention_uses_local_commercial_validity_separately_from_link_lifetime():
    item = today.quote_public(quotation(), DAY)
    assert today.quote_attention(item, "expiring", DAY)
    assert today.quote_attention(item, "viewed", DAY)
    expired = today.quote_public(quotation(valid_until="2026-10-08"), DAY)
    assert expired["state"] == "expired"
    assert not today.quote_attention(expired, "expiring", DAY)
    link_expired = today.quote_public(quotation(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)), DAY)
    assert link_expired["state"] == "link_expired"
    assert today.quote_attention(link_expired, "expiring", DAY)
    assert not today.quote_attention(link_expired, "viewed", DAY)
    approved = today.quote_public(quotation(status="APPROVED", valid_until="2026-10-08"), DAY)
    assert approved["state"] == "approved"
    assert not today.quote_attention(approved, "expiring", DAY)


def test_customer_response_preserves_note_and_does_not_invent_a_change_request():
    item = today.quote_public(quotation(response_status="DECLINED", decided_note="Revisar entrega"), DAY)
    assert item["state"] == "response" and item["response_note"] == "Revisar entrega"
    assert today.quote_attention(item, "response", DAY)
    assert not today.quote_attention(item, "viewed", DAY)


def test_pipeline_links_open_exact_phase_currency_and_balance_uses_live_receipts(monkeypatch):
    paid = quotation(status="IN_PRODUCTION", total="120.005", currency="USD")
    missing = quotation(status="IN_PRODUCTION", code="P-000013", total=None, currency="USD")
    rows = [quotation(), paid, missing, quotation(status="APPROVED", code="P-000014", total="10.5", currency="CLP")]
    monkeypatch.setattr(today, "quotation_rows", lambda org: rows)
    monkeypatch.setattr(today, "documentary_backend", nullcontext)
    monkeypatch.setattr(today, "rows", lambda sql, params: [
        {"project_id": paid["id"], "amount": Decimal(".005")},
        {"project_id": paid["id"], "amount": Decimal("20")},
    ])
    actions, pipeline = today.commercial_actions(uuid4(), DAY, "OWNER")
    balance = next(item for item in actions if item["key"] == f"receivable:{paid['id']}")
    assert Decimal(balance["amount"]) == Decimal("100")
    assert balance["balance_total"] == "120.005" and Decimal(balance["balance_collected"]) == Decimal("20.005")
    assert balance["due_on"] is None  # no fabricated due date
    assert "voided" not in balance["reason"]
    phase = next(item for item in pipeline if item["phase"] == "IN_PRODUCTION")
    assert phase["count"] == 2 and phase["unknown_count"] == 1
    assert Decimal(phase["amount"]) == Decimal("120.005")
    assert parse_qs(urlparse(phase["href"]).query) == {"phase": ["IN_PRODUCTION"], "currency": ["USD"]}
    estimator_actions, estimator_pipeline = today.commercial_actions(uuid4(), DAY, "ESTIMATOR")
    assert estimator_pipeline == [] and all(item["kind"] != "receivable" for item in estimator_actions)


def test_quotation_index_filters_exact_phase_currency_and_paginates_after_search(monkeypatch):
    monkeypatch.setattr(today, "local_today", lambda org: DAY)
    monkeypatch.setattr(today, "quotation_rows", lambda org: [quotation(status="IN_PRODUCTION", currency="USD"), quotation(status="APPROVED"), quotation(code="P-000015", status="IN_PRODUCTION", currency="USD")])
    result = today.quotations(uuid4(), phase="IN_PRODUCTION", currency="USD", limit=1, offset=1)
    assert result["total"] == 2 and len(result["items"]) == 1
    assert result["items"][0]["project_code"] == "P-000015"
    assert today.quotations(uuid4(), query="prat", phase="APPROVED")["total"] == 1


@pytest.mark.parametrize("body", [{"phase":"other"}, {"currency":"EUR"}, {"offset":-1}, {"limit":201}, {"q":"x" * 81}])
def test_index_rejects_unknown_filters_and_unbounded_reads(body):
    assert not QuotationIndexQuerySerializer(data=body).is_valid()


def test_draft_assembly_blocker_uses_engine_even_when_survey_confirmed(monkeypatch):
    project, position = uuid4(), uuid4()
    saved = {'id':position,'project_id':project,'position_index':3,'location_tag':'Living',
             'code':'P-000012','name':'Obra Prat','system_id':uuid4(),
             'parametric_tree':{'version':'product-v2'},'color_interior':'WHITE','survey_state':'CONFIRMED'}
    monkeypatch.setattr(today,'commercial_backend',nullcontext)
    monkeypatch.setattr(today,'rows',lambda sql,params:[saved])
    monkeypatch.setattr(today,'parse_product_model',lambda tree:tree)
    monkeypatch.setattr(today,'SystemParamsRepository',lambda:SimpleNamespace(
        load_visible=lambda *args:'authority',load_coupler_articles=lambda *args:[]))
    result=SimpleNamespace(status=SimpleNamespace(value='MANUFACTURING_INCOMPLETE'),
        modules=[],issues=[SimpleNamespace(params={'reason':'frame inset collapsed the glass pocket 6000.00 FRAME'})])
    monkeypatch.setattr(today,'evaluate_assembly_from_api',lambda **kwargs:result)
    action, = today.position_actions(uuid4())
    assert action['kind']=='position_engine_blocked' and 'autoridad técnica' in action['reason']
    assert 'FRAME' not in action['reason'] and '6000.00' not in action['reason']
    assert action['href']==f'/projects/{project}/positions/{position}/edit'
    result.status.value='VALID'
    assert today.position_actions(uuid4())==[]


def test_installer_only_sees_agenda_and_links_to_the_exact_order(monkeypatch):
    order, delivery = uuid4(), uuid4()
    supplied={'id':delivery,'order_id':order,'status':'DELIVERED','scheduled_date':DAY,
              'address':'Obra Prat','installer_name':'Equipo Sur','order_code':'OT-P-000005-REV-A-03'}
    statements=[]
    def query(sql,params):
        statements.append(sql)
        assert params[-1]==DAY
        return [supplied]
    monkeypatch.setattr(today,'documentary_backend',nullcontext)
    monkeypatch.setattr(today,'rows',query)
    action, = today.workshop_actions(uuid4(),'INSTALLER',DAY)
    assert len(statements)==1 and action['kind']=='installation'
    assert parse_qs(urlparse(action['href']).query)=={'order':[str(order)]}
    assert action['due_on']==DAY.isoformat() and 'Obra Prat' in action['reason']


def test_completed_order_never_reopens_an_old_shortage_as_todays_blocker(monkeypatch):
    supplied={'id':uuid4(),'order_code':'OT-P-000005-REV-A-03','status':'COMPLETED',
              'remake_of':None,'short':True,'optimized':True,'packed':True,
              'label':None,'note':None,'step_status':None,'scheduled_date':None}
    monkeypatch.setattr(today,'documentary_backend',nullcontext)
    monkeypatch.setattr(today,'rows',lambda sql,params:[] if 'SELECT d.id' in sql else [supplied])
    action, = today.workshop_actions(uuid4(),'WORKSHOP_MANAGER',DAY)
    assert action['kind']=='dispatch_ready' and not action['blocking']
