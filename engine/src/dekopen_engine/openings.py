"""Physical opening semantics and the one-version legacy transport adapter."""

from decimal import Decimal

from dekopen_engine.models import (
    BayOpeningType, HingeSide, HingedLayout, LeafRole, Opening, OpeningCapability,
    OpeningDirection, OpeningHandleFact, OpeningMovement, OpeningUse, ParametricNode,
    SystemParams, HardwareResolution,
)

IMPLEMENTED_MOVEMENTS = frozenset({OpeningMovement.FIXED, OpeningMovement.TURN,
    OpeningMovement.TILT, OpeningMovement.TILT_TURN, OpeningMovement.TOP_HUNG,
    OpeningMovement.SLIDE})

_LEGACY_MOTIONS = {
    BayOpeningType.FIXED: (OpeningMovement.FIXED, HingeSide.NONE),
    BayOpeningType.TURN_LEFT: (OpeningMovement.TURN, HingeSide.LEFT),
    BayOpeningType.TURN_RIGHT: (OpeningMovement.TURN, HingeSide.RIGHT),
    BayOpeningType.TILT_TURN_LEFT: (OpeningMovement.TILT_TURN, HingeSide.LEFT),
    BayOpeningType.TILT_TURN_RIGHT: (OpeningMovement.TILT_TURN, HingeSide.RIGHT),
    BayOpeningType.AWNING: (OpeningMovement.TOP_HUNG, HingeSide.TOP),
    BayOpeningType.SLIDING: (OpeningMovement.SLIDE, HingeSide.NONE),
    BayOpeningType.SLIDING_2L: (OpeningMovement.SLIDE, HingeSide.NONE),
    BayOpeningType.SLIDING_3L: (OpeningMovement.SLIDE, HingeSide.NONE),
    BayOpeningType.SLIDING_4L: (OpeningMovement.SLIDE, HingeSide.NONE),
    BayOpeningType.DOOR_ENTRY: (OpeningMovement.TURN, HingeSide.NONE),
    BayOpeningType.DOOR_DOUBLE: (OpeningMovement.TURN, HingeSide.NONE),
}
assert set(_LEGACY_MOTIONS) == set(BayOpeningType)


class OpeningCapabilityError(ValueError):
    def __init__(self, message: str, *, bay: str, compatible_systems: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.code = "opening_capability_incompatible"
        self.params = {"bay": bay, "reason": message,
                       "compatible_systems": ", ".join(compatible_systems)}


def opening_from_legacy(kind: BayOpeningType, *, door_handedness: str | None = None) -> Opening:
    movement, hinge = _LEGACY_MOTIONS[kind]
    if kind in (BayOpeningType.DOOR_ENTRY, BayOpeningType.DOOR_DOUBLE) and door_handedness:
        hinge = HingeSide(door_handedness)
    return Opening(movement=movement, hinge_side=hinge,
        direction=OpeningDirection.OUTWARD if kind is BayOpeningType.AWNING else OpeningDirection.INWARD,
        leaf_role=LeafRole.ACTIVE if kind is BayOpeningType.DOOR_DOUBLE else LeafRole.SINGLE)


def legacy_from_opening(opening: Opening, *, use: OpeningUse = OpeningUse.WINDOW,
                        layout: HingedLayout | None = None,
                        legacy_hint: BayOpeningType | None = None) -> BayOpeningType:
    """Lossless for old inputs; topology retains sliding cardinality separately.

    New motions without an exact legacy representation refuse conversion. This
    adapter never removes direction, fixed-in-sash or active/passive semantics.
    """
    if legacy_hint is not None:
        old = opening_from_legacy(legacy_hint, door_handedness=opening.hinge_side.value
            if opening.hinge_side in (HingeSide.LEFT, HingeSide.RIGHT) else None)
        if old == opening:
            return legacy_hint
        raise ValueError("La apertura estructurada contradice el alias histórico.")
    if opening.fixed_in_sash or opening.leaf_role is LeafRole.PASSIVE:
        raise ValueError("Esta apertura necesita el contrato estructurado.")
    if use is OpeningUse.DOOR:
        if (opening.movement is OpeningMovement.TURN
                and opening.direction is OpeningDirection.INWARD):
            return BayOpeningType.DOOR_DOUBLE if layout is not None else BayOpeningType.DOOR_ENTRY
        raise ValueError("Esta puerta necesita el contrato estructurado.")
    for kind, (movement, hinge) in _LEGACY_MOTIONS.items():
        if kind in (BayOpeningType.DOOR_ENTRY, BayOpeningType.DOOR_DOUBLE):
            continue
        if opening_from_legacy(kind) == opening:
            return BayOpeningType.SLIDING if movement is OpeningMovement.SLIDE else kind
    raise ValueError("Esta apertura necesita el contrato estructurado.")


def node_opening(node: ParametricNode) -> Opening:
    if node.opening is not None:
        return node.opening
    if node.opening_type is None:
        raise ValueError(f"BAY {node.id} requires opening or opening_type")
    return opening_from_legacy(node.opening_type, door_handedness=node.door_handedness)


def node_use(node: ParametricNode) -> OpeningUse:
    return node.opening_use or (OpeningUse.DOOR if node.opening_type in
        (BayOpeningType.DOOR_ENTRY, BayOpeningType.DOOR_DOUBLE) else OpeningUse.WINDOW)


def fabrication_alias(opening: Opening, use: OpeningUse, *, paired: bool = False) -> BayOpeningType:
    """Private geometric/limit decoder. It is never the saved motion authority."""
    if opening.movement is OpeningMovement.FIXED:
        return BayOpeningType.FIXED
    if opening.movement is OpeningMovement.SLIDE:
        return BayOpeningType.SLIDING
    if use is OpeningUse.DOOR:
        return BayOpeningType.DOOR_DOUBLE if paired else BayOpeningType.DOOR_ENTRY
    if opening.movement in (OpeningMovement.TOP_HUNG, OpeningMovement.TILT):
        return BayOpeningType.AWNING
    if opening.movement is OpeningMovement.TILT_TURN:
        return (BayOpeningType.TILT_TURN_LEFT if opening.hinge_side is HingeSide.LEFT
                else BayOpeningType.TILT_TURN_RIGHT)
    return BayOpeningType.TURN_LEFT if opening.hinge_side is HingeSide.LEFT else BayOpeningType.TURN_RIGHT


def matches_capability(capability: OpeningCapability, opening: Opening, use: OpeningUse) -> bool:
    return (capability.use is use and capability.movement is opening.movement
        and capability.direction is opening.direction and capability.leaf_role is opening.leaf_role
        and capability.fixed_in_sash == opening.fixed_in_sash
        and opening.hinge_side in capability.hinge_sides)


def resolve_capability(node: ParametricNode, params: SystemParams) -> OpeningCapability | None:
    # Old products continue their exact authority. New structured products may
    # never obtain permissions from a family name or an inferred legacy kit.
    if node.opening is None:
        return None
    opening, use = node_opening(node), node_use(node)
    if node.opening_type is not None:
        expected_use = OpeningUse.DOOR if node.opening_type in (
            BayOpeningType.DOOR_ENTRY, BayOpeningType.DOOR_DOUBLE) else OpeningUse.WINDOW
        if use is not expected_use or node.hinged_layout is not None:
            raise ValueError("El uso o la composición contradice el alias histórico. Usa el contrato estructurado.")
        legacy_from_opening(opening, use=use, legacy_hint=node.opening_type)
        return None  # Exact one-version migration retains the old authority.
    if opening.movement not in IMPLEMENTED_MOVEMENTS:
        raise OpeningCapabilityError("Esta apertura necesita la autoridad de geometría avanzada. "
            "Elige una tipología implementada por el sistema.", bay=node.id)
    if opening.hinge_side is HingeSide.NONE and opening.movement in (
            OpeningMovement.TURN, OpeningMovement.TILT_TURN):
        raise OpeningCapabilityError("Sin dato: declara el lado de las bisagras.", bay=node.id)
    matches = [cap for cap in params.opening_capabilities if matches_capability(cap, opening, use)]
    if len(matches) == 1:
        return matches[0]
    compatible = tuple(name for name, caps in params.compatible_opening_systems
                       if any(matches_capability(cap, opening, use) for cap in caps))
    suggestion = ("Elige " + ", ".join(compatible) + "." if compatible else
                  "Completa la capacidad con su fuente en Catálogo › Sistema.")
    reason = ("El catálogo declara capacidades contradictorias." if len(matches) > 1 else
              "El sistema no admite esta combinación de movimiento, dirección y rol.")
    raise OpeningCapabilityError(f"{reason} {suggestion}", bay=node.id, compatible_systems=compatible)


def normalize_opening_tree(node: ParametricNode, params: SystemParams) -> ParametricNode:
    children = [normalize_opening_tree(child, params) for child in node.children]
    updated = node.model_copy(update={"children": children}) if children else node
    if updated.opening is None:
        if updated.hinged_layout is not None or updated.opening_use is not None:
            raise OpeningCapabilityError("Declara la apertura estructurada de la composición.", bay=node.id)
        return updated
    opening, use = node_opening(updated), node_use(updated)
    if updated.type.value != "BAY":
        raise OpeningCapabilityError("La apertura pertenece a una bahía.", bay=node.id)
    if updated.opening_type is not None:
        legacy_from_opening(opening, use=use, legacy_hint=updated.opening_type)
    resolve_capability(updated, params)
    if updated.opening_type is not None:
        return updated
    if updated.hinged_layout is not None:
        if opening.leaf_role is not LeafRole.ACTIVE or opening not in (
                leaf.opening for leaf in updated.hinged_layout.leaves):
            raise OpeningCapabilityError("La apertura de la composición debe identificar su hoja activa.", bay=node.id)
        if params.paired_leaf_rule is None:
            raise OpeningCapabilityError("Sin dato: falta la regla del encuentro con inversor.", bay=node.id)
        for leaf in updated.hinged_layout.leaves:
            resolve_capability(updated.model_copy(update={"opening": leaf.opening}), params)
    elif opening.leaf_role is not LeafRole.SINGLE:
        raise OpeningCapabilityError("Una hoja activa/pasiva necesita su composición con inversor.", bay=node.id)
    if (opening.movement is OpeningMovement.SLIDE and updated.sliding_layout is None
            and updated.opening_type not in (BayOpeningType.SLIDING_2L,
                BayOpeningType.SLIDING_3L, BayOpeningType.SLIDING_4L)):
        raise OpeningCapabilityError("Declara los paneles y carriles de la corredera.", bay=node.id)
    if opening.movement is not OpeningMovement.SLIDE and updated.sliding_layout is not None:
        raise OpeningCapabilityError("Esta apertura no usa carriles de corredera.", bay=node.id)
    return updated


def geometry_opening_type(node: ParametricNode) -> BayOpeningType | None:
    if node.opening_type is not None:
        return node.opening_type
    if node.opening is None:
        return None
    return fabrication_alias(node.opening, node_use(node), paired=node.hinged_layout is not None)


def handle_fact(opening: Opening, capability: OpeningCapability, *, width_mm: Decimal,
                height_mm: Decimal, requested_height_mm: Decimal | None = None,
                hardware_resolution: HardwareResolution | None = None) -> OpeningHandleFact | None:
    rule = capability.handle_rule
    if rule is None:
        if requested_height_mm is not None:
            raise ValueError("Esta hoja no tiene una manilla de accionamiento.")
        return None
    side = {HingeSide.LEFT: HingeSide.RIGHT, HingeSide.RIGHT: HingeSide.LEFT,
            HingeSide.TOP: HingeSide.BOTTOM, HingeSide.BOTTOM: HingeSide.TOP}.get(opening.hinge_side)
    if side is None:  # Sliding hardware uses its own slot/track authority.
        return None
    minimum, maximum = rule.minimum_from_top_mm, height_mm - rule.minimum_from_bottom_mm
    if hardware_resolution is not None and hardware_resolution.handle_height_mm is not None:
        assert hardware_resolution.handle_minimum_mm is not None
        assert hardware_resolution.handle_maximum_mm is not None
        minimum = height_mm-hardware_resolution.handle_maximum_mm
        maximum = height_mm-hardware_resolution.handle_minimum_mm
        y = height_mm-hardware_resolution.handle_height_mm
    elif requested_height_mm is not None:
        y = height_mm - requested_height_mm
    elif side is HingeSide.TOP:
        y = rule.closing_edge_offset_mm
    elif side is HingeSide.BOTTOM:
        y = height_mm - rule.closing_edge_offset_mm
    elif rule.vertical_reference == "CENTER":
        y = height_mm / Decimal("2")
    else:
        assert rule.default_height_mm is not None
        y = (height_mm - rule.default_height_mm if rule.vertical_reference == "LEAF_BOTTOM"
             else rule.default_height_mm)
    if side in (HingeSide.LEFT, HingeSide.RIGHT) and not minimum <= y <= maximum:
        raise ValueError("La manilla queda fuera del rango de la fuente. Ajusta su altura dentro de la hoja.")
    if requested_height_mm is not None and side in (HingeSide.TOP, HingeSide.BOTTOM) and y != (
            rule.closing_edge_offset_mm if side is HingeSide.TOP else height_mm - rule.closing_edge_offset_mm):
        raise ValueError("La manilla de esta apertura debe quedar en su borde de cierre.")
    if side in (HingeSide.TOP, HingeSide.BOTTOM):
        minimum = maximum = y
    x = (width_mm - rule.closing_edge_offset_mm if side is HingeSide.RIGHT else
         rule.closing_edge_offset_mm if side is HingeSide.LEFT else width_mm / Decimal("2"))
    if not Decimal("0") <= x <= width_mm or not Decimal("0") <= y <= height_mm:
        raise ValueError("La regla de manilla queda fuera de la hoja. Revisa la fuente del catálogo.")
    return OpeningHandleFact(side=side, x_mm=x, y_mm=y,
        height_from_bottom_mm=height_mm-y,
        minimum_height_from_bottom_mm=height_mm-maximum,
        maximum_height_from_bottom_mm=height_mm-minimum,
        minimum_from_top_mm=minimum, maximum_from_top_mm=maximum,
        source=rule.source if hardware_resolution is None else hardware_resolution.source)


def opening_label(opening: Opening, use: OpeningUse = OpeningUse.WINDOW,
                  layout: HingedLayout | None = None) -> str:
    if layout is not None:
        active = next(leaf.slot for leaf in layout.leaves if leaf.opening.leaf_role is LeafRole.ACTIVE)
        return ("Puerta doble" if use is OpeningUse.DOOR else "Francesa 2 hojas") + (
            " — activa izquierda" if active == "LEFT" else " — activa derecha") + (
            " · hacia adentro" if opening.direction is OpeningDirection.INWARD else " · hacia afuera")
    if opening.movement is OpeningMovement.FIXED:
        return "Fijo en hoja" if opening.fixed_in_sash else "Fijo en marco"
    if opening.movement is OpeningMovement.TILT:
        return "Solo abatimiento (banderola)"
    if opening.movement is OpeningMovement.TOP_HUNG:
        return "Proyectante hacia afuera"
    if opening.movement is OpeningMovement.SLIDE:
        return "Corredera"
    kind = "Puerta simple" if use is OpeningUse.DOOR else (
        "Oscilobatiente" if opening.movement is OpeningMovement.TILT_TURN else "Abatible")
    direction = "hacia adentro" if opening.direction is OpeningDirection.INWARD else "hacia afuera"
    hinge = {HingeSide.LEFT: "bisagras a la izquierda", HingeSide.RIGHT: "bisagras a la derecha"}.get(
        opening.hinge_side, "Sin dato: falta el lado de las bisagras")
    return f"{kind} {direction} — {hinge}"
