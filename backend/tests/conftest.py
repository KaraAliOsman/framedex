"""Shared unit-test doubles.

Branding is fetched from tenancy_organizations at document emission; every
service test that exercises an emission path would otherwise hit the real
database. Stub it globally — a test that asserts branding behavior patches
the same attribute afterwards and wins.
"""

import pytest

from projects import org_branding


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
