"""Shared unit-test doubles.

Branding is fetched from tenancy_organizations at document emission; every
service test that exercises an emission path would otherwise hit the real
database. Stub it globally — a test that asserts branding behavior patches
the same attribute afterwards and wins.
"""

import pytest

from projects import org_branding


@pytest.fixture
def legacy_glass_read_model(monkeypatch):
    """Explicit unit-only data boundary; real safety/identity guards still run.

    Calculation contracts isolate catalog I/O just as they isolate profile
    repositories. Integration tests exercise the actual tenant rule store.
    """
    from catalogs import glass

    def read(statement, _parameters):
        if statement.startswith("SELECT c.id,c.legacy_spec FROM public.glass_purchase_mappings"):
            return [{"id": "legacy-fixture", "legacy_spec": "Historical fixture notation"}]
        if statement.startswith("SELECT payload::text,revision FROM public.glass_safety_rule_sets"):
            return []
        raise AssertionError(f"Unexpected glass authority query: {statement}")

    monkeypatch.setattr(glass, "rows", read)


@pytest.fixture(autouse=True)
def _stub_branding(monkeypatch):
    monkeypatch.setattr(
        org_branding,
        "branding_for_snapshot",
        lambda *, org_id: {
            "name": "Org Prueba",
            "tax_id": "76123456-0",
            "commercial_name": None,
            "giro": None,
            "brand_address": None,
            "brand_phone": None,
            "brand_email": None,
            "brand_logo_key": None,
            "brand_logo_sha256": None,
        },
    )


@pytest.fixture(autouse=True)
def _stub_ai_job_backend(monkeypatch):
    """AI job writes run under the ai_backend role inside real transactions;
    unit tests stub rows/one but the django connection would still open a
    cursor. The sqlite-vendor stub makes _ai_backend and the cancel paths
    no-op so tests stay hermetic."""
    from types import SimpleNamespace

    from ai_gateway import jobs

    monkeypatch.setattr(
        jobs,
        "connection",
        SimpleNamespace(vendor="sqlite", needs_rollback=False),
    )

    class _Atomic:
        def __call__(self, *args, **kwargs):
            return self

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(
        jobs, "transaction", SimpleNamespace(atomic=_Atomic())
    )
