"""Stages are facts about this solution, never inferred from a price or PDF."""

from decimal import Decimal
from contextlib import nullcontext
from uuid import uuid4

import pytest

from projects.progress import stage_from_facts
from projects import progress


@pytest.mark.parametrize(('status', 'facts', 'expected'), [
    ('DRAFT', {'shared': True, 'orders': ['INSTALLED'], 'balance': Decimal('0')}, 'QUOTING'),
    ('CANCELLED', {'orders': ['INSTALLED'], 'balance': Decimal('0')}, 'CANCELLED'),
    ('QUOTED', {}, 'QUOTING'),
    ('QUOTED', {'shared': True}, 'SENT'),
    ('QUOTED', {'accepted': True}, 'ACCEPTED'),
    ('APPROVED', {}, 'ACCEPTED'),
    ('COMPLETED', {}, 'ACCEPTED'),  # old lifecycle alone does not prove installation
    ('IN_PRODUCTION', {'orders': ['COMPLETED', 'INSTALLED']}, 'WORKSHOP'),
    ('IN_PRODUCTION', {'orders': ['INSTALLED'], 'balance': None}, 'INSTALLED'),
    ('COMPLETED', {'orders': ['INSTALLED'], 'balance': Decimal('.0001')}, 'TO_COLLECT'),
    ('COMPLETED', {'orders': ['INSTALLED'], 'balance': Decimal('0')}, 'CLOSED'),
])
def test_stage_requires_the_complete_physical_and_real_payment_facts(status, facts, expected):
    stage, reason = stage_from_facts(status, **facts)
    assert stage == expected
    assert reason


def test_missing_window_order_prevents_closure_and_money_keeps_exact_precision(monkeypatch):
    project, version = uuid4(), uuid4()
    fact = {'id': project, 'version_id': version, 'status': 'COMPLETED', 'decision': 'APPROVED',
        'total': '12345678901234567890.0001', 'currency': 'USD', 'shared': True, 'positions': ['one', 'two']}
    orders = [{'project_id': project, 'project_version_id': version, 'status': 'INSTALLED', 'position_id': 'one'}]
    paid = [{'project_id': project, 'amount': Decimal('12345678901234567890')},
            {'project_id': project, 'amount': Decimal('.0001')}]
    monkeypatch.setattr(progress, 'documentary_backend', nullcontext)
    def query(sql, params):
        if 'SELECT p.id' in sql:
            return [fact]
        return orders if 'SELECT o.project_id' in sql else paid
    monkeypatch.setattr(progress, 'rows', query)
    assert progress.project_progress(uuid4(), [project])[str(project)]['stage'] == 'WORKSHOP'
    orders.append({**orders[0], 'position_id': 'two'})
    assert progress.project_progress(uuid4(), [project])[str(project)]['stage'] == 'CLOSED'
    paid.pop()
    assert progress.project_progress(uuid4(), [project])[str(project)]['stage'] == 'TO_COLLECT'
