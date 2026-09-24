"""§10 production stock loop — reservation caps at physical availability,
consumption settles the hold at the routing step, and coverage reports
required vs on-hand vs ordered vs remnant pool honestly."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from inventory import production_stock


ORG = uuid4()
ORDER = uuid4()
ACTOR = uuid4()


def _need(sku: str = "PROF-6000", *, kind: str = "BAR", needed: int = 4,
          variant_key: str = "", unit: str = "BAR") -> dict:
    return {
        "kind": kind, "sku": sku, "variant_key": variant_key,
        "name": sku, "category": kind, "unit": unit,
        "needed": Decimal(needed),
    }


def test_reserve_caps_at_available_and_reports_short() -> None:
    movements: list[dict] = []

    def fake_one(query, params, code=None):
        if "INSERT INTO public.inventory_items" in query:
            return {"id": "item-1"}
        if "FROM public.inventory_movements" in query:
            # on_hand 5, already reserved 3 → only 2 available
            return {"on_hand": Decimal("5"), "reserved": Decimal("3")}
        raise AssertionError(query[:80])

    def fake_rows(query, params=None):
        if "INSERT INTO public.inventory_movements" in query:
            movements.append({"quantity": params[2]})
            return [{"id": "mv-1"}]
        raise AssertionError(query[:80])

    with patch.object(production_stock, "one", side_effect=fake_one), patch(
        "inventory.production_stock.rows", side_effect=fake_rows
    ):
        report = production_stock.reserve_for_order(
            org_id=ORG, order_id=ORDER, actor_id=ACTOR, needs=[_need(needed=10)]
        )
    assert len(movements) == 1
    assert movements[0]["quantity"] == Decimal("2")
    assert report[0]["reserved"] == "2"
    assert report[0]["short"] == "8"
    assert report[0]["consumed_at"] is None


def test_reserve_with_zero_available_writes_no_movement() -> None:
    def fake_one(query, params, code=None):
        if "INSERT INTO public.inventory_items" in query:
            return {"id": "item-1"}
        if "FROM public.inventory_movements" in query:
            return {"on_hand": Decimal("3"), "reserved": Decimal("3")}
        raise AssertionError(query[:80])

    def fake_rows(query, params=None):
        if "INSERT INTO public.inventory_movements" in query:
            raise AssertionError("must not reserve empty stock")
        raise AssertionError(query[:80])

    with patch.object(production_stock, "one", side_effect=fake_one), patch(
        "inventory.production_stock.rows", side_effect=fake_rows
    ):
        report = production_stock.reserve_for_order(
            org_id=ORG, order_id=ORDER, actor_id=ACTOR, needs=[_need(needed=2)]
        )
    assert report[0]["reserved"] == "0"
    assert report[0]["short"] == "2"


def test_release_settles_only_outstanding() -> None:
    written: list[Decimal] = []

    def fake_rows(query, params=None):
        if "GROUP BY item_id" in query:
            return [
                {"item_id": "a", "outstanding": Decimal("4")},
                {"item_id": "b", "outstanding": Decimal("0")},  # consumed
            ]
        if "INSERT INTO public.inventory_movements" in query:
            written.append(Decimal(str(params[2])))
            return [{"id": "mv"}]
        raise AssertionError(query[:80])

    with patch("inventory.production_stock.rows", side_effect=fake_rows):
        released = production_stock.release_for_order(
            org_id=ORG, order_id=ORDER, actor_id=ACTOR
        )
    assert released == 1
    assert written == [Decimal("4")]


def test_consume_writes_consumption_and_stamps_entries() -> None:
    reservations = [
        {"kind": "BAR", "sku": "S", "variant_key": "", "reserved": "2",
         "consumed_at": None},
        {"kind": "BAR", "sku": "S", "variant_key": "", "reserved": "1",
         "consumed_at": None},
        {"kind": "HARDWARE_KIT", "sku": "K", "variant_key": "", "reserved": "3",
         "consumed_at": None},
    ]
    movements: list[dict] = []

    def fake_one(query, params, code=None):
        return {"id": "item-1"}

    def fake_rows(query, params=None):
        if "SELECT now()" in query:
            return [{"at": "2026-01-01T00:00:00Z"}]
        if "INSERT INTO public.inventory_movements" in query:
            movements.append({"qty": params[2]})
            return [{"id": "mv"}]
        raise AssertionError(query[:80])

    with patch.object(production_stock, "one", side_effect=fake_one), patch(
        "inventory.production_stock.rows", side_effect=fake_rows
    ):
        out = production_stock.consume_for_order(
            org_id=ORG, order_id=ORDER, actor_id=ACTOR,
            kinds={"BAR", "SHEET"}, reservations=reservations,
        )
    # one summed CONSUMPTION for the two BAR rows on the same item; the kit
    # stays held for ASSEMBLE.
    assert len(movements) == 1
    assert movements[0]["qty"] == Decimal("3")
    assert out[0]["consumed_at"] == "2026-01-01T00:00:00Z"
    assert out[2]["consumed_at"] is None


def test_bar_stock_needs_groups_by_purchasing_identity() -> None:
    def fake_rows(query, params=None):
        if "profile_purchase_mappings" in query:
            return [{
                "authority_id": "auth-1", "commercial_sku": "PROF-X",
                "physical_stock_identity": "11111111-1111-1111-1111-111111111111",
            }]
        if "reinforcement_articles" in query:
            return []
        raise AssertionError(query[:80])

    bars = [
        {"source": "NEW", "stock_authority_id": "auth-1", "commercial_sku": "PROF-X"},
        {"source": "NEW", "stock_authority_id": "auth-1", "commercial_sku": "PROF-X"},
        # remnant bars never consume new stock
        {"source": "REMNANT", "stock_authority_id": "auth-1", "commercial_sku": "PROF-X"},
        # unmapped authority → reported at commercial sku, not fabricated
        {"source": "NEW", "stock_authority_id": "ghost", "commercial_sku": "PROF-Y"},
    ]
    with patch("inventory.production_stock.rows", side_effect=fake_rows):
        needs = production_stock.bar_stock_needs(org_id=ORG, bars=bars)
    assert len(needs) == 2
    grouped = [n for n in needs if n["sku"] == "PROF-X"]
    assert grouped[0]["needed"] == Decimal("2")
    assert grouped[0]["variant_key"] == "11111111-1111-1111-1111-111111111111"
    assert any(n["sku"] == "PROF-Y" and n["needed"] == 1 for n in needs)


def test_unit_stock_needs_scales_by_quantity_and_surfaces_unmapped() -> None:
    def fake_rows(query, params=None):
        if "hardware_purchase_mappings" in query:
            return [{"technical_sku": "KIT-1", "purchasing_sku": "P-KIT-1"}]
        if "fitting_purchase_mappings" in query:
            return []
        if "panel_purchase_authorities" in query:
            return [{"technical_sku": "PAN-A", "purchasing_sku": "P-PAN-A"}]
        raise AssertionError(query[:80])

    with patch("inventory.production_stock.rows", side_effect=fake_rows):
        needs, unmapped = production_stock.unit_stock_needs(
            org_id=ORG, system_id="sys", quantity=2,
            hardware_items=[{"kit_sku": "KIT-1", "qty": 1, "name": "Kit 1"}],
            fittings=[{"sku": "FT-GHOST", "qty": 4}],
            panels=[{"sku": "PAN-A", "name": "Panel A"}],
            sheet_purchases=[
                # Real SheetPurchase dumps carry purchasing_sku + group_kind.
                {"purchasing_sku": "GL-4", "qty_sheets": 2, "group_kind": "GLASS"},
                # Panel-group sheets already have a PANEL authority need —
                # counting the sheet too would double-book the same stock.
                {"purchasing_sku": "PAN-SHEET", "qty_sheets": 3, "group_kind": "PANEL"},
            ],
        )
    by_kind = {n["kind"]: n for n in needs}
    assert by_kind["HARDWARE_KIT"]["needed"] == Decimal("2")
    assert by_kind["PANEL"]["needed"] == Decimal("2")
    assert by_kind["SHEET"]["needed"] == Decimal("2")
    assert by_kind["SHEET"]["sku"] == "GL-4"
    assert unmapped == ["FT-GHOST"]


def test_coverage_computes_shortage_and_recommendation() -> None:
    line_id = uuid4()

    def fake_rows(query, params=None):
        if "purchase_requirement_lines" in query:
            return [{
                "id": str(line_id), "order_type": "SUPPLIER_PROFILE_PO",
                "category": "PROFILE", "purchasing_sku": "PROF-X",
                "physical_stock_identity": "a" * 32,
                "unit": "BAR", "quantity": Decimal("10"),
                "technical_identity": "{}", "specification": "{}",
            }]
        if "order_receipt_lines" in query:
            return [{"requirement_line_id": str(line_id), "qty": Decimal("4")}]
        if "order_requirement_lines" in query:
            return [{"requirement_line_id": str(line_id), "qty": Decimal("6")}]
        if "inventory_stock" in query:
            return [{"sku": "PROF-X", "variant_key": "a" * 32,
                     "on_hand_qty": Decimal("5"), "reserved_qty": Decimal("2")}]
        if "inventory_remnants" in query and "BAR" in query:
            return [{"psi": "a" * 32, "count": 2, "total_mm": Decimal("800")}]
        return []

    with patch("inventory.production_stock.rows", side_effect=fake_rows):
        report = production_stock.coverage_for_version(org_id=ORG, version_id=uuid4())
    (line,) = report["lines"]
    # available = 5 - 2 = 3; open_ordered = 6 - 4 = 2
    assert line["required"] == "10"
    assert line["available"] == "3"
    assert line["open_ordered"] == "2"
    # shortage 7 vs open 2 → buy 5 more, not 7
    assert line["shortage"] == "7"
    assert line["recommended_purchase"] == "5"
    assert line["remnant_pool"]["count"] == 2
    assert report["shortages"] == 1


def test_identity_lookup_matches_global_authorities() -> None:
    # Global stock authorities (org_id IS NULL) are accepted by the cutting
    # repository's effective scope — the reservation lookup must match them
    # too, or a globally-mapped bar reserves against an empty variant key.
    queries: list[str] = []

    def fake_rows(query, params=None):
        queries.append(query)
        return []

    with patch("inventory.production_stock.rows", side_effect=fake_rows):
        needs = production_stock.bar_stock_needs(
            org_id=ORG,
            bars=[{"source": "NEW", "stock_authority_id": "g1",
                   "commercial_sku": "PROF-G"}],
        )
    identity_queries = [q for q in queries if "physical_stock_identity" in q]
    assert len(identity_queries) == 2
    assert all("org_id IS NULL" in q for q in identity_queries)
    assert needs[0]["sku"] == "PROF-G"
