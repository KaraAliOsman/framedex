"""Manual oracle: 900 net, 500 quoted; original 500 + remake 40 = 540 real."""

from typing import Any

from dekopen_engine.analytics import (
    actual_cost,
    bar_reading,
    driver_sources,
    margin_bridge,
    decimal_text,
    remnant_quantity,
)


def analytics_cases() -> dict[str, Any]:
    base = actual_cost(
        materials=[
            {
                "id": "consume",
                "kind": "CONSUMPTION",
                "quantity": "42",
                "unit_cost": "10",
                "waste_quantity": "3",
            }
        ],
        labor=[{"id": "cut", "hours": "3", "hourly_rate": "20"}],
        other="20",
        credit="0",
        closed=True,
    )
    remake = actual_cost(
        materials=[
            {
                "id": "remake",
                "kind": "CONSUMPTION",
                "quantity": "3",
                "unit_cost": "10",
                "waste_quantity": "0.5",
            }
        ],
        labor=[{"id": "recut", "hours": "0.5", "hourly_rate": "20"}],
        other="0",
        credit="0",
        closed=True,
    )
    quote = {
        "net": "900",
        "cost": "500",
        "materials": "400",
        "waste": "40",
        "labor": "50",
        "other": "10",
        "discount": "-100",
    }
    recovered = actual_cost(
        materials=[
            {
                "id": "consume",
                "kind": "CONSUMPTION",
                "quantity": "10",
                "unit_cost": "2",
                "waste_quantity": "1",
            },
            {
                "id": "return",
                "kind": "RETURN",
                "quantity": "2",
                "unit_cost": "2",
                "waste_quantity": "0",
            },
            {
                "id": "scrap",
                "kind": "SCRAP",
                "quantity": "1",
                "unit_cost": "2",
                "waste_quantity": "1",
            },
            {
                "id": "remnant",
                "kind": "REMNANT",
                "quantity": "0.5",
                "unit_cost": "2",
                "waste_quantity": "0",
            },
        ],
        labor=[{"id": "cut", "hours": "0", "hourly_rate": "2"}],
        other="0",
        credit="3",
        closed=True,
    )
    return {
        "base": base,
        "remake": remake,
        "bridge": margin_bridge(quote=quote, base=[base], remakes=[remake]),
        "sources": {
            key: driver_sources(base, key) for key in ("materials", "waste", "labor", "other")
        },
        "bars": bar_reading(
            input_mm="6000", productive_mm="5400", waste_mm="300", reusable_mm="300"
        ),
        "recovered": recovered,
        "wire": {"zero": decimal_text("0E-8"), "small": decimal_text("1E-8")},
        "remnant_quantities": {
            "bar": remnant_quantity(kind="BAR", length_mm="500", width_mm=None, height_mm=None),
            "sheet": remnant_quantity(
                kind="SHEET", length_mm=None, width_mm="1500", height_mm="1250"
            ),
        },
    }
