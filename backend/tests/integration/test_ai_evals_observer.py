"""A local eval observer must retain the product's actor/role unchanged."""

from django.db import connection, transaction
import pytest

from ai_gateway.evals.run import _snapshot
from backend.tests.integration.test_shot08_pricing import (
    committed_commercial_rows as committed_commercial_rows,
    as_user,
)

pytestmark = pytest.mark.rls_integration


def test_observer_restores_authenticated_role_and_sees_column_gated_tables(django_db_blocker):
    if connection.vendor != "postgresql":
        pytest.fail("The observer check requires real local PostgreSQL; never skipped")
    with django_db_blocker.unblock(), transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL ROLE authenticated")
            cursor.execute("SELECT current_setting('role'), current_setting('request.jwt.claims', true)")
            before = cursor.fetchone()
        snapshot = _snapshot(include_ai=True)
        assert "project_positions" in snapshot
        assert "organization" in snapshot
        assert "agent_route" in snapshot
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_setting('role'), current_setting('request.jwt.claims', true)")
            assert cursor.fetchone() == before
        transaction.set_rollback(True)


def test_manager_purchase_context_queries_supplier_types_on_postgres(committed_commercial_rows):
    """DISTINCT projects an enum as text; sorting must use that projection."""
    from ai_gateway.context import build_context

    org, _, users = committed_commercial_rows
    with as_user(users["WORKSHOP_MANAGER"]):
        result = build_context(org, "purchase_plan", {})
    assert result["coverage_verified"] is True
    assert result["suppliers"] == []
