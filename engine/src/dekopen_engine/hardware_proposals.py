"""A priced split uses the same geometry execution as the accepted design."""

from decimal import Decimal

from dekopen_engine.geometry import calculate_geometry
from dekopen_engine.models import EngineResult, NodeType, OpeningMovement, ParametricNode, ProfileRole, SystemParams


def split_hardware_bay(root: ParametricNode, params: SystemParams, *, bay_id: str,
                       dimensions: dict[str, tuple[Decimal, Decimal]]) -> tuple[ParametricNode, EngineResult] | None:
    """Propose two equal operable bays only when catalog + engine accept them."""
    mullion = params.effective_profile_articles.get(ProfileRole.MULLION_V)
    if mullion is None or bay_id not in dimensions:
        return None
    found = False

    def split(node: ParametricNode) -> ParametricNode:
        nonlocal found
        if node.id != bay_id:
            return node.model_copy(update={"children": [split(child) for child in node.children]})
        if (node.type is not NodeType.BAY or node.hinged_layout is not None
                or node.opening_use is not None and node.opening_use.value == "DOOR"
                or node.opening is None or node.opening.movement not in (OpeningMovement.TURN, OpeningMovement.TILT_TURN)):
            return node
        found = True
        children = [node.model_copy(update={"id": f"{node.id}:division:{index}",
            "width_mm": None, "height_mm": None, "hardware_set_sku": None}) for index in (1, 2)]
        return ParametricNode(id=node.id, type=NodeType.SPLIT_V, width_mm=node.width_mm, height_mm=node.height_mm,
            split_offset_mm=dimensions[bay_id][0]/Decimal(2), mullion_profile_sku=mullion.sku, children=children)

    alternative = split(root)
    if not found:
        return None
    try:
        return alternative, calculate_geometry(alternative, params)
    except ValueError:
        return None
