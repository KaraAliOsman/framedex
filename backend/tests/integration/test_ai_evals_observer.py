"""A local eval observer must retain the product's actor/role unchanged."""

from django.db import connection, transaction
import pytest

from ai_gateway.evals.run import _snapshot

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
