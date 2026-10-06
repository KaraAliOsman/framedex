"""Real price and supply regressions: the selector must agree with quotation authority."""
from copy import deepcopy
from datetime import date
from decimal import Decimal as D
import json

import pytest
from django.db import connection

from backend.tests.integration.test_shot09_documentary import (
    documentary_tenant as documentary_tenant, as_user, _seed_project, _tenant,
)
from backend.tests.integration.catalog_fixture import copy_fixed_catalog
from catalogs.readiness import catalog_readiness
from catalogs.glass import load_products
from dekopen_engine.glass_composition import glass_rate_requirements
from pricing.repository import admin_write, commercial_backend, json_text, one, rows
from pricing.service import preview
from projects.finishes import finish_preview
from projects.serializers import PositionWriteSerializer
from projects.service import create_project, save_position

pytestmark = pytest.mark.rls_integration


def price_fixture(org, owner, *, currency, mode):
    _seed_project(org, owner)
    with connection.cursor() as cursor:
        cursor.execute("UPDATE tenancy_organizations SET currency=%s WHERE id=%s", [currency, org])
    with as_user(owner):
        system = one("SELECT id FROM profile_systems WHERE code='DEMO_60' AND version=5")["id"]
        cost_list = admin_write("cost-lists", org, {"supplier_name": "Ensayo D05 DEMO", "currency": currency,
            "valid_from": date(2026, 10, 6)}, "D05 price-mode fixture")
        glass = next(item for item in load_products(system, org) if item["technical_sku"].endswith("-GLASS-SAFE"))
        required = rows("SELECT sku,unit FROM catalog_demo_prices WHERE system_id=%s "
            "UNION SELECT commercial_sku,purchase_unit FROM reinforcement_articles WHERE system_id=%s", [system, system])
        # Shared glass/process prices belong to the earlier DEMO version. A
        # USD workshop must supply those in USD too, without a CLP fallback.
        required.extend({"sku": sku, "unit": unit} for sku, unit in (
            (glass["technical_sku"], "M2"), *glass_rate_requirements(glass["resolved_product"], None)))
        for item in {entry["sku"]: entry for entry in required}.values():
            admin_write("cost-items", org, {"cost_list_id": cost_list["id"], "sku": item["sku"],
                "unit": item["unit"], "item_type": "FIXTURE",
                "unit_cost": D(200 if currency == "USD" and item["sku"].endswith("-CREAM") else 100)},
                "D05 synthetic sourced price")
        rule_id = one("SELECT id FROM pricing_rules WHERE org_id=%s", [org])["id"]
        admin_write("rules", org, {"pricing_mode": mode}, "D05 configured mode", rule_id)
        design = {"system_id": system, "nominal_width_mm": D("900"), "nominal_height_mm": D("850"),
            "color": "CREAM", "baseline_color": "WHITE", "parametric_tree": {"id": "vano", "type": "BAY",
                "opening_type": "FIXED", "glass_thickness_mm": "24.00", "glass_spec": "4-16-4",
                "glass_article_sku": glass["technical_sku"], "glass_product": glass["resolved_product"].model_dump(mode="json")}}
        return design


@pytest.mark.parametrize("currency,mode", [
    ("USD", "COST_PLUS_MARGIN"),
    ("CLP", "COMMERCIAL_LIST_WITH_DISCOUNTS"),
    ("CLP", "FIXED_PRICE_MATRIX_DIMENSIONAL"),
    ("CLP", "PRICE_PER_M2_BY_TYPOLOGY"),
])
def test_finish_delta_matches_actual_configured_selling_price(documentary_tenant, currency, mode):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    design = price_fixture(org, owner, currency=currency, mode=mode)
    with as_user(owner):
        if mode != "COST_PLUS_MARGIN":
            configuration = admin_write("configurations", org, {"context_code": "DEFAULT", "typology": "FIXED",
                "pricing_mode": mode, "currency": currency, "catalog_price": D(1000000),
                "rate_per_m2": D(1000000), "base_glass_sku": design["parametric_tree"]["glass_article_sku"],
                "is_active": True}, "D05 selling-price fixture")
            if mode == "FIXED_PRICE_MATRIX_DIMENSIONAL":
                for width in (800, 1000):
                    for height in (800, 1000):
                        admin_write("matrix-cells", org, {"configuration_id": configuration["id"],
                            "width_mm": width, "height_mm": height, "price": D(1000000)}, "D05 matrix fixture")
        delta = finish_preview(org, design)
        assert delta["currency"] == currency
        assert delta["delta_price_net"] is not None, delta["reason"]
        project = create_project(org, owner, {"name": "D05 precio por modo · DEMO", "client_name": "Ensayo"})
        for color in ("WHITE", "CREAM"):
            serialized = {**design, "system_id": str(design["system_id"]), "color": color,
                "nominal_width_mm": "900", "nominal_height_mm": "850"}
            serialized.pop("baseline_color")
            serializer = PositionWriteSerializer(data={"location_tag": color, "quantity": 1, "design": serialized})
            serializer.is_valid(raise_exception=True)
            save_position(org, project["id"], serializer.validated_data)
        with commercial_backend():
            quote = preview(org, _tenant(org, "OWNER"), {"project_id": project["id"], "pricing_mode": mode,
                "currency": currency, "effective_date": date(2026, 10, 6), "context_code": "DEFAULT",
                "discount_pct": D(0), "target_margin": D("0.35"), "segment": "RETAIL",
                "confirmed": False, "reason": "D05 compare actual quote", "_actor_id": owner})
        detail = quote["line_detail"]
        actual = D(detail[1]["unit_price"]) - D(detail[0]["unit_price"])
        assert D(delta["delta_price_net"]).quantize(D("0.0001")) == actual
        if currency == "USD":
            assert actual > 0
        if mode in {"COMMERCIAL_LIST_WITH_DISCOUNTS", "FIXED_PRICE_MATRIX_DIMENSIONAL"}:
            assert actual == 0  # A higher finish cost is not an unconfigured selling-price increase.


def test_usd_finish_with_foreign_tariff_returns_missing_fx_reason(documentary_tenant):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    design = price_fixture(org, owner, currency="USD", mode="COST_PLUS_MARGIN")
    with as_user(owner):
        result = finish_preview(org, {**design, "color": "WHITE_WALNUT"})
    assert result["currency"] == "USD" and result["delta_price_net"] is None
    assert "cotización de moneda" in result["reason"]


def test_project_target_margin_does_not_invent_a_position_delta(documentary_tenant):
    org, _, users, _ = documentary_tenant
    owner = users["OWNER"]
    design = price_fixture(org, owner, currency="CLP", mode="TARGET_GROSS_MARGIN_PROJECT")
    with as_user(owner):
        result = finish_preview(org, design)
    assert result["delta_price_net"] is None and "proyecto completo" in result["reason"]


def test_chart_without_white_checks_every_declared_combination(documentary_tenant):
    org, _, users, _ = documentary_tenant
    target = copy_fixed_catalog(org, version=5)
    authority = json.loads(one("SELECT finish_authority FROM profile_systems WHERE id=%s", [target])["finish_authority"])
    cream = next(combo for combo in authority["combinations"] if combo["code"] == "CREAM")
    walnut = deepcopy(next(combo for combo in authority["combinations"] if combo["code"] == "WHITE_WALNUT"))
    walnut.update(code="CREAM_WALNUT", interior="CREAM", base="CREAM")
    authority["combinations"] = [cream, walnut]
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM catalog_color_skus WHERE system_id=%s AND finish NOT IN ('CREAM','WHITE_WALNUT')", [target])
        cursor.execute("UPDATE profile_systems SET finishes=%s::jsonb,finish_authority=%s::jsonb WHERE id=%s",
            [json_text(["CREAM", "CREAM_WALNUT"]), json_text(authority), target])
        cursor.execute("UPDATE catalog_color_skus SET finish='CREAM_WALNUT',stock_color='CREAM_WALNUT' "
            "WHERE system_id=%s AND finish='WHITE_WALNUT'", [target])
    with as_user(users["OWNER"]):
        assert "purchase" not in catalog_readiness(target, org)["reasons"]
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM catalog_color_skus WHERE id=(SELECT id FROM catalog_color_skus "
            "WHERE system_id=%s AND finish='CREAM_WALNUT' LIMIT 1)", [target])
    with as_user(users["OWNER"]):
        assert "purchase" in catalog_readiness(target, org)["reasons"]
