"""Presentation dimensions and candidate offsets from the canonical traversal."""

from decimal import Decimal, ROUND_HALF_UP
from typing import TypedDict

from dekopen_engine.technical_facts import GeometryComputation


class AxisOffsets(TypedDict):
    half: str
    one_third: str
    two_thirds: str


class NodeLayout(TypedDict):
    node_id: str
    width_mm: str
    height_mm: str
    vertical: AxisOffsets
    horizontal: AxisOffsets
    child_weights: list[str]


def node_layout(computation: GeometryComputation) -> list[NodeLayout]:
    def axis(size: Decimal) -> AxisOffsets:
        # Candidate manual edits use the same hundredth-mm resolution as the API.
        # They still require a fresh strict engine calculation before acceptance.
        def candidate(numerator: str, denominator: str) -> str:
            return str((size * Decimal(numerator) / Decimal(denominator)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP,
            ))
        return {
            "half": candidate("1", "2"),
            "one_third": candidate("1", "3"),
            "two_thirds": candidate("2", "3"),
        }

    def weights(key: str, width: Decimal, height: Decimal) -> list[str]:
        split = computation.split_axes.get(key)
        if split is None:
            return []
        vertical, offset = split
        return [str(offset), str((width if vertical else height) - offset)]

    return [{
        "node_id": key, "width_mm": str(width), "height_mm": str(height),
        "vertical": axis(width), "horizontal": axis(height),
        "child_weights": weights(key, width, height),
    } for key, (width, height) in computation.node_dimensions.items()]
