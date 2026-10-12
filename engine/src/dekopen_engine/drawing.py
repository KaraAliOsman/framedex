"""Pure technical dimension chains, measured to authored divider axes."""
from decimal import Decimal

from pydantic import Field

from .models import EngineModel, NodeType, ParametricNode


class DimensionSegment(EngineModel):
    start_mm: Decimal
    end_mm: Decimal
    value_mm: Decimal


class DimensionChain(EngineModel):
    axis: str
    level: int
    segments: list[DimensionSegment]


class DrawingBay(EngineModel):
    bay_id: str
    x_mm: Decimal
    y_mm: Decimal
    width_mm: Decimal
    height_mm: Decimal


class DrawingHandleDatum(EngineModel):
    bay_id: str
    height_from_bottom_mm: Decimal
    y_mm: Decimal
    bottom_mm: Decimal


class DrawingFacts(EngineModel):
    width_mm: Decimal
    height_mm: Decimal
    chains: list[DimensionChain] = Field(default_factory=list)
    bays: list[DrawingBay] = Field(default_factory=list)
    authored_handles: list[DrawingHandleDatum] = Field(default_factory=list)


class DrawingEnvelope(EngineModel):
    min_x_mm: Decimal
    min_y_mm: Decimal
    width_mm: Decimal
    height_mm: Decimal


def dimension_chains(tree: ParametricNode, width: Decimal, height: Decimal) -> DrawingFacts:
    """Each split's offset is local to its region; chain lengths are exact.

    Place each nested run on its own gutter level, keeping text out of leaves.
    These are engineering drawing dimensions, not glazing/cutting measures.
    """
    facts = DrawingFacts(width_mm=width, height_mm=height)
    levels = {"V": 0, "H": 0}

    def visit(node: ParametricNode, x: Decimal, y: Decimal, w: Decimal, h: Decimal) -> None:
        if node.type is NodeType.BAY:
            facts.bays.append(DrawingBay(bay_id=node.id, x_mm=x, y_mm=y, width_mm=w, height_mm=h))
            if node.opening is None and node.handle_height_mm is not None:
                facts.authored_handles.append(DrawingHandleDatum(bay_id=node.id,
                    height_from_bottom_mm=node.handle_height_mm,
                    y_mm=height-node.handle_height_mm, bottom_mm=height))
        elif node.type is NodeType.ROOT:
            for child in node.children:
                visit(child, x, y, w, h)
        elif node.type in (NodeType.SPLIT_V, NodeType.SPLIT_H):
            if node.split_offset_mm is None or len(node.children) != 2:
                return
            axis = "V" if node.type is NodeType.SPLIT_V else "H"
            origin, extent = (x, w) if axis == "V" else (y, h)
            split = node.split_offset_mm
            if not Decimal("0") < split < extent:
                return
            marks = (origin, origin + split, origin + extent)
            facts.chains.append(DimensionChain(axis=axis, level=levels[axis], segments=[
                DimensionSegment(start_mm=a, end_mm=b, value_mm=b - a)
                for a, b in zip(marks[:-1], marks[1:], strict=True)]))
            levels[axis] += 1
            if axis == "V":
                visit(node.children[0], x, y, split, h)
                visit(node.children[1], x + split, y, w - split, h)
            else:
                visit(node.children[0], x, y, w, split)
                visit(node.children[1], x, y + split, w, h - split)

    visit(tree, Decimal("0"), Decimal("0"), width, height)
    return facts
