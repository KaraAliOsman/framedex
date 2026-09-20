"""A concurrent catalog writer cannot make a stale calculation persist."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

from django.db import connection, transaction, close_old_connections, DatabaseError
import pytest

from backend.tests.integration.catalog_fixture import copy_fixed_catalog
from backend.tests.integration.test_shot08_pricing import (
    committed_commercial_rows as committed_commercial_rows,
    as_user,
)
from backend.tests.integration.test_shot10_projects_catalogs import position_data
from projects import service
from pricing.repository import one

pytestmark = pytest.mark.rls_integration


def test_concurrent_catalog_change_rejects_stale_save(committed_commercial_rows):
    org, _, users = committed_commercial_rows
    owner = users["OWNER"]
    system = copy_fixed_catalog(org)
    with as_user(owner):
        project = service.create_project(org, owner, {"name": "Concurrent catalog"})["id"]
    ready, changed = Event(), Event()

    def old_snapshot():
        close_old_connections()
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
                with as_user(owner):
                    one("SELECT id FROM public.profile_systems WHERE id=%s", [system])
                    ready.set()
                    assert changed.wait(10)
                    service.save_position(org, project, position_data(system))
        except DatabaseError as error:
            return error.__cause__.sqlstate
        finally:
            close_old_connections()
        return "unexpected success"

    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(old_snapshot)
        assert ready.wait(10)
        try:
            with connection.cursor() as cursor:
                cursor.execute("RESET ROLE")
                cursor.execute("UPDATE public.profile_articles SET welding_loss_mm=welding_loss_mm+1 "
                               "WHERE system_id=%s AND role='FRAME'", [system])
        finally:
            changed.set()
        assert pending.result(10) == "40001"
    with as_user(owner):
        assert service.positions(org, project) == []
        saved = service.save_position(org, project, position_data(system))
        assert saved["bom"]["calculation_hash"].startswith("sha256:")
