"""Shared render fixtures: diagram reservations corrected; sourced axes added."""

from decimal import Decimal as D
import json
from pathlib import Path
from typing import Any, cast

from dekopen_engine.models import Opening
from dekopen_engine.symbols import SymbolTravel, opening_symbol_lines
from engine.tests.advanced_cases import advanced_cases, advanced_node, advanced_typologies

SYMBOL_DIR = Path(__file__).parent / "fixtures/symbols"


def symbol_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def generated_reservations() -> bytes:
    cases = json.loads((SYMBOL_DIR / "cases.json").read_text(encoding="utf-8"))
    for case in cases:
        if not any(
            leaf["opening"]["movement"] in ("LIFT_SLIDE", "PARALLEL_SLIDE", "FOLD")
            for leaf in case["leaves"]
        ):
            continue
        for leaf, expected in zip(case["leaves"], case["expected"], strict=True):
            opening = Opening.model_validate_json(json.dumps(leaf["opening"]))
            lines = opening_symbol_lines(
                opening,
                x=D(leaf["x_mm"]),
                y=D(leaf["y_mm"]),
                width=D(leaf["width_mm"]),
                height=D(leaf["height_mm"]),
                mirror=False,
                exterior=case["view"] == "exterior",
                travel=cast(SymbolTravel | None, leaf["travel"]),
            )
            expected["lines"] = [
                {
                    "symbol": line.symbol,
                    "points": [
                        [str(D(1200) - x if case["view"] == "exterior" else x), str(y)]
                        for x, y in line.points
                    ],
                    "dashed": line.dashed,
                }
                for line in lines
            ]
    return symbol_bytes(cases)


def generated_advanced_symbols() -> bytes:
    cases = []
    calculated = advanced_cases()
    for code, recipe in advanced_typologies():
        node = advanced_node(code, recipe)
        assert node.width_mm is not None
        for view in ("interior", "exterior"):
            leaves = calculated[code + "/" + recipe]["opening_leaves"]
            expected = []
            for leaf in leaves:
                opening = Opening.model_validate_json(json.dumps(leaf["opening"]))
                data = leaf["advanced"]
                lines = opening_symbol_lines(
                    opening,
                    x=D(leaf["x_mm"]),
                    y=D(leaf["y_mm"]),
                    width=D(leaf["width_mm"]),
                    height=D(leaf["height_mm"]),
                    mirror=False,
                    exterior=view == "exterior",
                    travel=cast(SymbolTravel | None, data["travel"]),
                    axis_x=D(data["pivot_x_mm"]) if data["pivot_x_mm"] is not None else None,
                    axis_y=D(data["pivot_y_mm"]) if data["pivot_y_mm"] is not None else None,
                    closing_side=leaf["handle"]["side"] if leaf["handle"] else None,
                )
                expected.append(
                    {
                        "lines": [
                            {
                                "symbol": line.symbol,
                                "dashed": line.dashed,
                                "points": [
                                    [str(node.width_mm - x if view == "exterior" else x), str(y)]
                                    for x, y in line.points
                                ],
                            }
                            for line in lines
                        ]
                    }
                )
            cases.append(
                {
                    "name": code + "/" + recipe + "/" + view,
                    "view": view,
                    "total_width_mm": str(node.width_mm),
                    "leaves": leaves,
                    "expected": expected,
                }
            )
    return symbol_bytes(cases)
