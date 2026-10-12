from decimal import Decimal as D

from dekopen_engine.inventory import purchase_total, stock_shortfall
from dekopen_engine.inventory import purchase_source_ledger
from dekopen_engine.inventory import purchase_glass_areas
from dekopen_engine.geometry import compute_geometry
from dekopen_engine.models import SystemParams
from engine.tests.test_purchasing import position_source, project_one
from engine.tests.test_shot06_core import core_node


def test_golden_partial_receipt_reservation_and_transit() -> None:
    # Ten required, two held, three usable received, one damaged excluded by
    # the receiving ledger, two usable still on their way: buy exactly three.
    assert stock_shortfall(required=D(10), own_reserved=D(2), available=D(3), incoming=D(2)) == {
        "reserved": D(2), "stock": D(3), "incoming": D(2), "purchase": D(3)}
    assert purchase_total([(D(3), D("12500.25")), (D(2), D("1000"))]) == D("39500.75")


def test_missing_purchase_price_is_unknown() -> None:
    assert purchase_total([(D(3), None)]) is None


def test_golden_purchase_glass_area_preserves_exact_receiving_units() -> None:
    assert purchase_glass_areas([(D('910.00'), D('910.00'), 2), (D('1000.01'), D('2000.00'), 3)]) == ([D('1.6562'), D('6.00006')], D('7.65626'))


def test_shared_pool_is_only_allocated_once() -> None:
    first = stock_shortfall(required=D(4), own_reserved=D(0), available=D(6), incoming=D(0))
    second = stock_shortfall(required=D(4), own_reserved=D(0), available=D(6)-first["stock"], incoming=D(0))
    assert first["purchase"] == D(0)
    assert second["purchase"] == D(2)


def test_golden_sealed_sources_reconcile_to_positions(demo_60_params: SystemParams) -> None:
    node = core_node("G6").model_copy(update={"glass_article_sku": "GLASS-TECH"})
    position, bindings = position_source(node, demo_60_params, position_id="P-1", position_index=1, quantity=2)
    computation = compute_geometry(node, demo_60_params)
    assert computation.result is not None
    snapshot = {
        "manufacturing": [unit.model_dump(mode="json") for unit in position.manufacturing_units],
        "bom": [{"position_id": "P-1", "quantity": 2, "engine_result": computation.result.model_dump(mode="json")}],
        "positions": [{"id": "P-1", "quantity": 2, "accessory_schedule": position.accessory_schedule.model_dump(mode="json")}],
    }
    ledger = purchase_source_ledger(snapshot)
    requirements = project_one(position, bindings).requirements
    assert all(ledger[source][0] == "P-1" for req in requirements for source in req.source_trace)
    assert all(sum((ledger[source][1] for source in req.source_trace), D(0)) == D(req.quantity)
               for req in requirements if req.unit != "BAR")
