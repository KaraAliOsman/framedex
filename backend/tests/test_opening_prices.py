"""The compatibility adapter preserves the complete production price formation."""
from decimal import Decimal as D
from types import SimpleNamespace

import pytest

from dekopen_engine.models import BayOpeningType, OpeningUse
from dekopen_engine.openings import opening_from_legacy
from engine.tests.catalog import demo_60_params
from engine.tests.test_gold_cases_catalog_families import node
from pricing import service


@pytest.mark.parametrize("kind", [kind for kind in BayOpeningType if kind not in
    (BayOpeningType.DOOR_DOUBLE, BayOpeningType.SLIDING)])
def test_dual_transport_keeps_complete_price_and_every_cost_line(kind, monkeypatch, legacy_glass_read_model):
    class Cursor:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def execute(self, _sql):
            return None

    class Repo:
        org_id = "fixture"

        def cost(self, sku, unit):
            # An explicit synthetic rate fixture, shared by both transports.
            return {"BAR": D("12345.6789"), "M2": D("31500.1250"),
                    "KIT": D("47500.0001"), "EA": D("125.2500")}[unit]

    params = demo_60_params()
    monkeypatch.setattr(service, "connection", SimpleNamespace(needs_rollback=False, cursor=Cursor))
    monkeypatch.setattr(service, "SystemParamsRepository", lambda: SimpleNamespace(
        load_visible=lambda *_: params, load_coupler_articles=lambda *_: {}))
    def stock(sku):
        return SimpleNamespace(commercial_sku=sku, stock_length_mm=D("6000"))
    monkeypatch.setattr(service, "CuttingRepository", lambda: SimpleNamespace(
        profile_stock=lambda _system, _org, sku, _color: stock(sku),
        reinforcement_stock=lambda _system, _org, _profile, sku, _color: (stock(sku), None)))
    old = node(kind, "1800" if kind.value.startswith("SLIDING") else "1000",
        "2200" if kind is BayOpeningType.DOOR_ENTRY else "900" if kind is BayOpeningType.AWNING else "1400")
    old = old.model_copy(update={"glass_article_sku": "PRICE-GLASS",
        **({"panel_article_sku": "PANEL-SANDWICH-DEMO-24"} if kind is BayOpeningType.DOOR_ENTRY else {})})
    rules = {"waste_factor_pct": D("5.25"), "labor_rate_per_m2": D("9000.2500"),
        "installation_rate_per_m2": D("3150.7500")}
    def price(tree):
        return service.position_cost(Repo(), {"system_id": "fixture", "width_mm": old.width_mm,
            "height_mm": old.height_mm, "color_interior": "WHITE", "color_exterior": "WHITE",
            "parametric_tree": tree.model_dump(mode="json", exclude_none=True)}, rules)
    original = price(old)
    migrated = price(old.model_copy(update={"opening": opening_from_legacy(kind),
        "opening_use": OpeningUse.DOOR if kind is BayOpeningType.DOOR_ENTRY else OpeningUse.WINDOW}))
    assert original == migrated
    assert original[0] > D("0") and original[3]["composition"]
