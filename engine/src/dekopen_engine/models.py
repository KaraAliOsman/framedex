"""Typed, serializable contracts for Dekopen's pure calculation engine."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, SerializerFunctionWrapHandler, model_serializer, model_validator

from dekopen_engine.glass_composition import GlassComposition, GlassProcessing, GlassProduct, total_glass_thickness
from dekopen_engine.finish_models import FinishAuthority, ResolvedFinish
from dekopen_engine.extra_models import ExtraAuthority, ExtraContext, ExtraFact, ExtraSelection, ExtraSuggestion


class EngineModel(BaseModel):
    """Strict shared configuration for deterministic engine values."""

    model_config = ConfigDict(strict=True, extra="forbid", allow_inf_nan=False)


class MaterialType(str, Enum):
    PVC = "PVC"
    ALUMINIUM = "ALUMINIUM"


class SystemFamily(str, Enum):
    CASEMENT = "CASEMENT"
    SLIDING = "SLIDING"
    LIFT_SLIDE = "LIFT_SLIDE"
    DOOR = "DOOR"
    FACADE_FIXED = "FACADE_FIXED"


class RailType(str, Enum):
    DUAL = "dual"
    MONO = "mono"


class ProfileRole(str, Enum):
    FRAME = "FRAME"
    SASH = "SASH"
    MULLION_V = "MULLION_V"
    MULLION_H = "MULLION_H"
    INVERSOR = "INVERSOR"
    GLAZING_BEAD = "GLAZING_BEAD"
    COUPLER = "COUPLER"
    ADDITIONAL = "ADDITIONAL"
    THRESHOLD = "THRESHOLD"
    # Continuous edge channel seating a frameless glass pane (mandate §14).
    CHANNEL = "CHANNEL"
    SLIDING_SASH = "SLIDING_SASH"
    INTERLOCK = "INTERLOCK"
    RAIL = "RAIL"
    DOOR_SASH = "DOOR_SASH"
    FRAME_EXTENSION = "FRAME_EXTENSION"
    SILL = "SILL"
    COVER_TRIM = "COVER_TRIM"
    PLINTH = "PLINTH"


class NodeType(str, Enum):
    ROOT = "ROOT"
    SPLIT_H = "SPLIT_H"
    SPLIT_V = "SPLIT_V"
    BAY = "BAY"


class BayOpeningType(str, Enum):
    FIXED = "FIXED"
    TURN_LEFT = "TURN_LEFT"
    TURN_RIGHT = "TURN_RIGHT"
    TILT_TURN_LEFT = "TILT_TURN_LEFT"
    TILT_TURN_RIGHT = "TILT_TURN_RIGHT"
    SLIDING_2L = "SLIDING_2L"
    SLIDING_3L = "SLIDING_3L"
    SLIDING_4L = "SLIDING_4L"
    # Layout-driven sliding unit: the panel/track topology lives in
    # `sliding_layout`, so arbitrary X/O arrangements need no enum values.
    SLIDING = "SLIDING"
    AWNING = "AWNING"
    DOOR_ENTRY = "DOOR_ENTRY"
    DOOR_DOUBLE = "DOOR_DOUBLE"


class OpeningMovement(str, Enum):
    FIXED = "FIXED"
    TURN = "TURN"
    TILT = "TILT"
    TILT_TURN = "TILT_TURN"
    TOP_HUNG = "TOP_HUNG"
    BOTTOM_HUNG = "BOTTOM_HUNG"
    SLIDE = "SLIDE"
    LIFT_SLIDE = "LIFT_SLIDE"
    PARALLEL_SLIDE = "PARALLEL_SLIDE"
    FOLD = "FOLD"
    PIVOT_V = "PIVOT_V"
    PIVOT_H = "PIVOT_H"
    VERTICAL_SLIDE = "VERTICAL_SLIDE"


class HingeSide(str, Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    TOP = "TOP"
    BOTTOM = "BOTTOM"
    NONE = "NONE"


class OpeningDirection(str, Enum):
    INWARD = "INWARD"
    OUTWARD = "OUTWARD"


class LeafRole(str, Enum):
    ACTIVE = "ACTIVE"
    PASSIVE = "PASSIVE"
    SINGLE = "SINGLE"


class OpeningUse(str, Enum):
    WINDOW = "WINDOW"
    DOOR = "DOOR"


class Opening(EngineModel):
    """Physical motion; leaf count and window/door use belong to composition."""

    movement: OpeningMovement
    hinge_side: HingeSide
    direction: OpeningDirection
    leaf_role: LeafRole = LeafRole.SINGLE
    fixed_in_sash: bool = False

    @model_validator(mode="after")
    def physical_motion(self) -> Opening:
        if self.fixed_in_sash and self.movement is not OpeningMovement.FIXED:
            raise ValueError("Solo un fijo puede estar instalado en hoja.")
        if self.movement in (OpeningMovement.FIXED, OpeningMovement.SLIDE):
            if self.hinge_side is not HingeSide.NONE or self.leaf_role is not LeafRole.SINGLE:
                raise ValueError("Un fijo o una corredera no declara bisagras ni hoja activa/pasiva.")
        elif self.movement in (OpeningMovement.TURN, OpeningMovement.TILT_TURN):
            # NONE preserves the honest unknown handedness of old doors. New
            # authoring requires LEFT/RIGHT at the capability boundary.
            if self.hinge_side not in (HingeSide.LEFT, HingeSide.RIGHT, HingeSide.NONE):
                raise ValueError("Una abatible necesita bisagras laterales.")
        elif self.movement is OpeningMovement.TILT:
            if self.hinge_side is not HingeSide.BOTTOM or self.direction is not OpeningDirection.INWARD:
                raise ValueError("El abatimiento interior lleva bisagras abajo.")
        elif self.movement is OpeningMovement.TOP_HUNG:
            if self.hinge_side is not HingeSide.TOP or self.direction is not OpeningDirection.OUTWARD:
                raise ValueError("La proyectante lleva bisagras arriba y abre hacia afuera.")
        return self


class HingedLeaf(EngineModel):
    slot: Literal["LEFT", "RIGHT"]
    opening: Opening
    hardware_set_sku: str | None = None


class HingedLayout(EngineModel):
    """Two leaves meeting on an inversor, without a fixed central mullion."""

    leaves: tuple[HingedLeaf, HingedLeaf]

    @model_validator(mode="after")
    def active_and_passive(self) -> HingedLayout:
        left, right = self.leaves
        if (left.slot, right.slot) != ("LEFT", "RIGHT"):
            raise ValueError("Ordena las hojas izquierda y derecha en vista interior.")
        if (left.opening.hinge_side, right.opening.hinge_side) != (HingeSide.LEFT, HingeSide.RIGHT):
            raise ValueError("Las bisagras deben quedar en los extremos del marco.")
        if {left.opening.leaf_role, right.opening.leaf_role} != {LeafRole.ACTIVE, LeafRole.PASSIVE}:
            raise ValueError("La composición necesita una hoja activa y una pasiva con falleba.")
        if any(leaf.opening.movement not in (OpeningMovement.TURN, OpeningMovement.TILT_TURN)
               for leaf in self.leaves):
            raise ValueError("La francesa necesita dos hojas practicables.")
        if left.opening.direction is not right.opening.direction:
            raise ValueError("Ambas hojas deben abrir hacia el mismo lado.")
        if any(leaf.opening.fixed_in_sash for leaf in self.leaves):
            raise ValueError("Una hoja de la francesa no puede ser fija.")
        return self


class PairedLeafRule(EngineModel):
    meeting_overlap_mm: Decimal = Field(ge=0)
    meeting_gap_mm: Decimal = Field(ge=0)
    inversor_end_deduction_mm: Decimal = Field(ge=0)
    source: str = Field(min_length=1)


class OpeningHandleRule(EngineModel):
    """Height relative to the physical leaf, never a guessed display fraction."""

    vertical_reference: Literal["CENTER", "LEAF_BOTTOM", "LEAF_TOP"]
    default_height_mm: Decimal | None = Field(default=None, ge=0)
    minimum_from_top_mm: Decimal = Field(ge=0)
    minimum_from_bottom_mm: Decimal = Field(ge=0)
    closing_edge_offset_mm: Decimal = Field(ge=0)
    source: str = Field(min_length=1)

    @model_validator(mode="after")
    def declared_height(self) -> OpeningHandleRule:
        if self.vertical_reference != "CENTER" and self.default_height_mm is None:
            raise ValueError("La altura de manilla requiere un valor de la fuente.")
        return self


class OpeningCapability(EngineModel):
    use: OpeningUse
    movement: OpeningMovement
    direction: OpeningDirection
    leaf_role: LeafRole
    fixed_in_sash: bool = False
    hinge_sides: tuple[HingeSide, ...] = Field(min_length=1)
    hardware_kit_skus: tuple[str, ...] = ()
    handle_rule: OpeningHandleRule | None = None
    source: str = Field(min_length=1)

    @model_validator(mode="after")
    def declared_hardware(self) -> OpeningCapability:
        for hinge in self.hinge_sides:
            Opening(movement=self.movement, hinge_side=hinge, direction=self.direction,
                    leaf_role=self.leaf_role, fixed_in_sash=self.fixed_in_sash)
        if self.use is OpeningUse.DOOR and self.movement not in (OpeningMovement.FIXED, OpeningMovement.TURN):
            raise ValueError("La capacidad de puerta debe declarar un giro o un fijo lateral.")
        if self.movement is OpeningMovement.FIXED:
            if self.hardware_kit_skus or self.handle_rule is not None:
                raise ValueError("Un fijo no lleva herrajes de apertura ni manilla.")
        elif not self.hardware_kit_skus:
            raise ValueError("Declara los herrajes que respaldan esta capacidad.")
        elif (self.movement is not OpeningMovement.SLIDE and self.leaf_role is not LeafRole.PASSIVE
              and self.handle_rule is None):
            raise ValueError("Declara la regla de manilla con su fuente.")
        if self.leaf_role is LeafRole.PASSIVE and self.handle_rule is not None:
            raise ValueError("La hoja pasiva lleva falleba, sin manilla de accionamiento.")
        if len(self.hinge_sides) != len(set(self.hinge_sides)):
            raise ValueError("Las bisagras de la capacidad están duplicadas.")
        if len(self.hardware_kit_skus) != len(set(self.hardware_kit_skus)):
            raise ValueError("Los herrajes de la capacidad están duplicados.")
        return self


class SlidingPanelKind(str, Enum):
    MOVING = "MOVING"  # rides a rail — a sliding sash leaf
    FIXED = "FIXED"  # glazed in-frame — an "O" panel


class SlidingPanel(EngineModel):
    """One slot of a sliding unit, ordered left→right in elevation."""

    slot: str
    kind: SlidingPanelKind
    # 0-based rail index. Required on MOVING panels, must be null on FIXED —
    # a fixed pane has no rail. Two adjacent MOVING panels may not share a
    # track (they would collide before overlapping).
    track: int | None = None


class SlidingLayout(EngineModel):
    """Track topology of a sliding bay (mandate §12).

    `tracks` is how many of the frame's rails the layout occupies and must
    not exceed the system profile's rail capacity. `panels` lists every
    slot left→right; adjacent slots overlap by the system's central
    overlap. X/O notation: MOVING=X, FIXED=O — e.g. O/X/X/O is
    panels [FIXED, MOVING@0, MOVING@1, FIXED] on 2 tracks.
    """

    tracks: int = Field(ge=1)
    panels: list[SlidingPanel] = Field(min_length=1)


class PlanPoint(EngineModel):
    x_mm: Decimal
    y_mm: Decimal


class GlassPiece(EngineModel):
    bay_id: str
    leaf_id: str | None = None
    width_mm: Decimal
    height_mm: Decimal
    # Boundary polygon for non-rectangular pieces (sampled at arc chords).
    # When set, width/height are the bounding box only — the piece is NOT
    # a rectangle and rect-only consumers (2D sheet nesting) must report
    # it as unnested rather than silently cutting a bounding rectangle.
    shape: list[PlanPoint] | None = None
    area_m2: Decimal
    # UNKNOWN is first-class: a spec the composition authority cannot parse
    # must not quietly borrow the package thickness and fabricate a mass.
    weight_kg: Decimal | None
    thickness_net_mm: Decimal | None
    # Composition (e.g. "4-16-4") and the supplier article the piece was
    # resolved against — None on results sealed before the fields existed.
    glass_spec: str | None = None
    article_sku: str | None = None
    # Frameless panes declare which edges are exposed glass (mandate §14) —
    # polishing authority consumes this as its suggested preselection; a
    # framed pane leaves it None.
    exposed_edges: list[str] | None = None
    composition: GlassComposition | None = None
    thickness_total_mm: Decimal | None = None
    billable_area_m2: Decimal | None = None
    processing: GlassProcessing | None = None

    @model_serializer(mode="wrap")
    def serialize_glass(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        result: dict[str, Any] = handler(self)
        # Additive composition metadata must not change the hash of a
        # historical piece that never declared these fields.
        for key in ("composition", "thickness_total_mm", "billable_area_m2", "processing"):
            if key not in self.model_fields_set:
                result.pop(key, None)
        return result


HARDWARE_COMPONENT_CATEGORIES = (
    "HANDLE", "HINGE", "LOCK", "ROLLER", "CONNECTOR", "DRAINAGE", "GASKET",
    "SEAL", "SCREW", "CONSUMABLE", "FITTING", "SUPPORT", "CHANNEL", "OTHER",
)

HardwareComponentCategory = Literal[
    "HANDLE", "HINGE", "LOCK", "ROLLER", "CONNECTOR", "DRAINAGE", "GASKET",
    "SEAL", "SCREW", "CONSUMABLE", "FITTING", "SUPPORT", "CHANNEL", "OTHER",
]


class HardwareQuantityRule(EngineModel):
    """A declared count plus increments after a dimension/weight threshold."""
    base: int = Field(ge=0)
    axis: Literal["WIDTH", "HEIGHT", "PERIMETER", "WEIGHT"] | None = None
    threshold: Decimal | None = Field(default=None, ge=0)
    step: Decimal | None = Field(default=None, gt=0)
    increment: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def complete_rule(self) -> HardwareQuantityRule:
        if (self.axis is None) != (self.threshold is None and self.step is None):
            raise ValueError("La regla de cantidad requiere eje, umbral y paso.")
        if self.axis is not None and (self.threshold is None or self.step is None):
            raise ValueError("La regla de cantidad requiere umbral y paso.")
        return self


class HardwareLengthRule(EngineModel):
    axis: Literal["WIDTH", "HEIGHT", "PERIMETER", "FIXED"]
    deduction_mm: Decimal = Field(ge=0)
    fixed_mm: Decimal | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def fixed_length_is_explicit(self) -> HardwareLengthRule:
        if (self.axis == "FIXED") != (self.fixed_mm is not None):
            raise ValueError("El largo fijo requiere su medida explícita.")
        return self


class HardwareMachiningRule(EngineModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: Literal["LOCK_PREP", "HINGE_PREP", "SLOT", "DRILL", "MILLING", "HANDLE_PREP"]
    host_side: Literal["TOP", "BOTTOM", "LEFT", "RIGHT", "HINGE", "CLOSING"]
    host_scope: Literal["LEAF", "OUTER_FRAME"] | None = None
    # Distances along the physical member from its start. No coordinates =
    # declared work, not an emitted operation or a fabricated default.
    positions_mm: list[Decimal] = Field(default_factory=list)
    covered_quantity: int | None = Field(default=None, ge=1)
    face: Literal["OUTSIDE_FACE", "INSIDE_FACE", "TOP_EDGE", "BOTTOM_EDGE"] | None = None
    tool_id: str | None = None
    depth_mm: Decimal | None = Field(default=None, gt=0)
    source: str = Field(min_length=1)

    @model_validator(mode="after")
    def machining_positions_are_physical(self) -> HardwareMachiningRule:
        if any(position < 0 for position in self.positions_mm) or len(self.positions_mm) != len(set(self.positions_mm)):
            raise ValueError("Las coordenadas de mecanizado deben ser positivas y únicas.")
        return self


class HardwareComponentRule(EngineModel):
    sku: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: HardwareComponentCategory
    quantity: HardwareQuantityRule
    length: HardwareLengthRule | None = None
    price_unit: Literal["EA", "M"]
    weight_kg: Decimal | None = Field(default=None, ge=0)
    weight_kg_m: Decimal | None = Field(default=None, ge=0)
    purchasing_sku: str = Field(min_length=1)
    manufacturer_name: str = Field(min_length=1)
    source: str = Field(min_length=1)
    machining: list[HardwareMachiningRule] = Field(default_factory=list)

    @model_validator(mode="after")
    def measurement_authority(self) -> HardwareComponentRule:
        if self.price_unit == "M" and self.length is None:
            raise ValueError("El componente por metro requiere una regla de largo.")
        if self.weight_kg is not None and self.weight_kg_m is not None:
            raise ValueError("Declara una sola base de masa por componente.")
        if self.weight_kg_m is not None and self.length is None:
            raise ValueError("La masa por metro requiere una regla de largo.")
        return self


class HardwareHandleColor(EngineModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    component: HardwareComponentRule


class HardwareHandleModel(EngineModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    model: Literal["STANDARD", "KEY", "BUTTON", "ESCUTCHEON"]
    colors: list[HardwareHandleColor] = Field(min_length=1)
    default_color: str
    vertical_rule: Literal["CENTER", "FIXED", "RANGE", "TOP_OFFSET"]
    default_height_mm: Decimal | None = Field(default=None, gt=0)
    minimum_from_bottom_mm: Decimal = Field(ge=0)
    minimum_from_top_mm: Decimal = Field(ge=0)
    source: str = Field(min_length=1)

    @model_validator(mode="after")
    def explicit_handle(self) -> HardwareHandleModel:
        codes = [color.code for color in self.colors]
        if len(codes) != len(set(codes)) or self.default_color not in codes:
            raise ValueError("Los colores de manilla deben ser únicos e incluir el predeterminado.")
        if self.vertical_rule != "CENTER" and self.default_height_mm is None:
            raise ValueError("La manilla fija o por rango requiere altura declarada.")
        if any(color.component.category != "HANDLE" for color in self.colors):
            raise ValueError("El modelo de manilla debe declarar un componente manilla.")
        return self


class HardwareOption(EngineModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: Literal["SECURITY", "LIMITER", "MICROVENTILATION", "HIDDEN_HINGES", "OTHER"]
    components: list[HardwareComponentRule] = Field(min_length=1)
    replaces_skus: list[str] = Field(default_factory=list)
    security_rating: str | None = None
    source: str = Field(min_length=1)

    @model_validator(mode="after")
    def security_has_a_source(self) -> HardwareOption:
        if self.security_rating is not None and self.kind != "SECURITY":
            raise ValueError("Una clase de seguridad requiere una opción de seguridad con fuente.")
        return self


class HardwareClassAuthority(EngineModel):
    schema_version: Literal[1] = 1
    family_code: str = Field(min_length=1)
    family_name: str = Field(min_length=1)
    class_code: str = Field(min_length=1)
    class_name: str = Field(min_length=1)
    priority: int = Field(ge=0)
    source: str = Field(min_length=1)
    synthetic: bool
    minimum_width_height_ratio: Decimal | None = Field(default=None, gt=0)
    maximum_width_height_ratio: Decimal | None = Field(default=None, gt=0)
    minimum_stay_height_mm: Decimal | None = Field(default=None, gt=0)
    components: list[HardwareComponentRule] = Field(min_length=1)
    handles: list[HardwareHandleModel] = Field(default_factory=list)
    default_handle: str | None = None
    options: list[HardwareOption] = Field(default_factory=list)

    @model_validator(mode="after")
    def class_contract(self) -> HardwareClassAuthority:
        for items in (self.components, self.handles, self.options):
            codes = [item.sku if isinstance(item, HardwareComponentRule) else item.code for item in items]
            if len(codes) != len(set(codes)):
                raise ValueError("Los componentes, modelos y opciones deben tener códigos únicos.")
        if self.handles and self.default_handle not in {item.code for item in self.handles}:
            raise ValueError("La clase debe declarar su manilla predeterminada.")
        if not self.handles and self.default_handle is not None:
            raise ValueError("Una clase sin manillas no puede declarar una predeterminada.")
        if (self.minimum_width_height_ratio is not None and self.maximum_width_height_ratio is not None
                and self.minimum_width_height_ratio > self.maximum_width_height_ratio):
            raise ValueError("El rango de relación ancho/alto está invertido.")
        base_skus = {item.sku for item in self.components}
        if any(set(option.replaces_skus) - base_skus for option in self.options):
            raise ValueError("Una opción solo puede sustituir componentes declarados en la clase.")
        return self


class HardwareSelection(EngineModel):
    handle_code: str | None = None
    color_code: str | None = None
    option_codes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_options(self) -> HardwareSelection:
        if len(self.option_codes) != len(set(self.option_codes)):
            raise ValueError("Las opciones vendibles no pueden repetirse.")
        return self


class HardwareResolution(EngineModel):
    family_name: str
    class_name: str
    class_code: str
    source: str
    synthetic: bool
    width_mm: Decimal
    height_mm: Decimal
    exact_leaf_weight_kg: Decimal | None
    max_leaf_weight_kg: Decimal
    min_leaf_width_mm: Decimal
    max_leaf_width_mm: Decimal
    min_leaf_height_mm: Decimal
    max_leaf_height_mm: Decimal
    handle_code: str | None
    handle_name: str | None
    handle_color: str | None
    handle_color_code: str | None
    handle_height_mm: Decimal | None
    handle_minimum_mm: Decimal | None
    handle_maximum_mm: Decimal | None
    options: list[str]
    option_codes: list[str]


class HardwareComponent(EngineModel):
    sku: str
    name: str
    qty: Decimal = Field(gt=Decimal("0"))
    unit: str
    # Declared component kind — the catalog states what each kit line IS so
    # production can distinguish handles, hinges, locks, rollers, seals,
    # drainage and consumables instead of guessing from a name. Contents
    # sealed before the field existed decode as OTHER (mandate §9).
    category: HardwareComponentCategory = "OTHER"
    cut_length_mm: Decimal | None = Field(default=None, gt=0)
    weight_kg: Decimal | None = Field(default=None, ge=0)
    purchasing_sku: str | None = None
    manufacturer_name: str | None = None
    price_unit: Literal["EA", "M"] | None = None
    price_quantity: Decimal | None = Field(default=None, gt=0)
    reason: str | None = None
    source: str | None = None
    machining: list[HardwareMachiningRule] = Field(default_factory=list)

    @model_serializer(mode="wrap")
    def preserve_historical_component(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        result: dict[str, Any] = handler(self)
        for key in ("cut_length_mm", "weight_kg", "purchasing_sku", "manufacturer_name", "price_unit",
                    "price_quantity", "reason", "source", "machining"):
            if key not in self.model_fields_set:
                result.pop(key, None)
        return result


class HardwareItem(EngineModel):
    kit_sku: str
    name: str
    qty: int = 1
    unit: Literal["kit"] = "kit"
    bay_id: str
    leaf_id: str | None = None
    contents: list[HardwareComponent] = Field(default_factory=list)
    resolution: HardwareResolution | None = None

    @model_serializer(mode="wrap")
    def preserve_historical_item(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        result: dict[str, Any] = handler(self)
        if "resolution" not in self.model_fields_set:
            result.pop("resolution", None)
        return result


class HardwareKitRule(EngineModel):
    sku: str
    name: str
    opening_type: str
    min_leaf_width_mm: Decimal
    max_leaf_width_mm: Decimal
    min_leaf_height_mm: Decimal
    max_leaf_height_mm: Decimal
    max_leaf_weight_kg: Decimal
    rail_type: RailType = RailType.DUAL
    carriages_qty: int = 2
    stay_arms_qty: int = 1
    contents: list[HardwareComponent] = Field(default_factory=list)
    weight_kg: Decimal | None = None
    carriage_capacity_kg: Decimal | None = None
    class_authority: HardwareClassAuthority | None = None


class SectionPoint(EngineModel):
    """One vertex of a catalog section polygon, profile-local mm."""

    x_mm: Decimal
    y_mm: Decimal


class SectionAxis(EngineModel):
    """A named reference axis through the section (glazing, web, fixing)."""

    name: str
    y_mm: Decimal


def _segments_properly_intersect(
    a1: tuple[Decimal, Decimal],
    a2: tuple[Decimal, Decimal],
    b1: tuple[Decimal, Decimal],
    b2: tuple[Decimal, Decimal],
) -> bool:
    """Proper crossing test — segments share no endpoint and cross in their
    interiors. Touches/collinear overlaps at a shared vertex are the polygon's
    normal edge adjacency, not a self-intersection."""

    def orient(p: tuple[Decimal, Decimal], q: tuple[Decimal, Decimal], r: tuple[Decimal, Decimal]) -> Decimal:
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    d1 = orient(b1, b2, a1)
    d2 = orient(b1, b2, a2)
    d3 = orient(a1, a2, b1)
    d4 = orient(a1, a2, b2)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def polygon_self_intersects(points: list[tuple[Decimal, Decimal]]) -> bool:
    """True when any two non-adjacent edges of the closed polygon properly
    cross. Adjacent edges share a vertex by construction and are skipped."""
    count = len(points)
    for i in range(count):
        a1, a2 = points[i], points[(i + 1) % count]
        for j in range(i + 1, count):
            # Adjacent edges (incl. the last-first wrap pair) share an endpoint.
            if j == i + 1 or (i == 0 and j == count - 1):
                continue
            b1, b2 = points[j], points[(j + 1) % count]
            if _segments_properly_intersect(a1, a2, b1, b2):
                return True
    return False


class ProfileSection(EngineModel):
    """Simplified technical cross-section of a catalog profile (mandate §15).

    The polygon is the cross-section across the face: x spans the face width,
    y runs the depth direction (0 = exterior face). `POLYGON` is a declared
    simplified section; `DXF_REFERENCE` says the shape was taken from a real
    manufacturer drawing (`drawing_ref` points at it). When `section` is
    absent the renderer falls back to an approximate box — a visibly
    different, explicitly approximate state, never a fake declaration."""

    source: Literal["POLYGON", "DXF_REFERENCE"]
    polygon: list[SectionPoint] = Field(min_length=3)
    depth_mm: Decimal = Field(gt=0)
    axes: list[SectionAxis] = Field(default_factory=list)
    drawing_ref: str | None = None
    # Declared interpretation facts (mandate §8): which polygon edge faces the
    # building exterior, and where the declared (0,0) anchor sits in polygon
    # space. They tell renderers how to orient the drawing — they never feed
    # fabrication math.
    orientation: Literal[
        "EXTERIOR_DOWN", "EXTERIOR_UP", "EXTERIOR_LEFT", "EXTERIOR_RIGHT"
    ] = "EXTERIOR_DOWN"
    local_origin: Literal[
        "TOP_LEFT", "TOP_RIGHT", "BOTTOM_LEFT", "BOTTOM_RIGHT", "CENTROID"
    ] = "TOP_LEFT"

    @model_validator(mode="after")
    def _section_is_real(self) -> "ProfileSection":
        points = [(point.x_mm, point.y_mm) for point in self.polygon]
        if len(set(points)) != len(points):
            raise ValueError("section polygon repeats vertices")
        area = Decimal(0)
        for index, (x1, y1) in enumerate(points):
            x2, y2 = points[(index + 1) % len(points)]
            area += x1 * y2 - x2 * y1
        if area == 0:
            raise ValueError("section polygon encloses no area")
        if polygon_self_intersects(points):
            raise ValueError("section polygon self-intersects")
        if self.source == "DXF_REFERENCE" and not (self.drawing_ref or "").strip():
            raise ValueError("DXF_REFERENCE section needs a drawing_ref")
        return self


class ProfileCutRule(EngineModel):
    """Reviewed profile-specific cutting authority; all allowances are explicit."""

    angle_degrees: Literal[45, 90]
    welding_loss_per_end_mm: Decimal = Field(ge=0)
    joint_deduction_per_end_mm: Decimal = Field(ge=0)
    meeting_deduction_mm: Decimal = Field(ge=0)
    cut_step_mm: Decimal = Field(gt=0)
    rounding: Literal["UP", "NEAREST", "DOWN"]
    source: str = Field(min_length=1)


class ProfileReinforcementRule(EngineModel):
    reinforcement_sku: str = Field(min_length=1)
    reinforcement_type: str = Field(min_length=1)
    minimum_length_mm: Decimal = Field(ge=0)
    required_finishes: tuple[str, ...]
    required_non_white: bool
    cut_deduction_mm: Decimal = Field(ge=0)
    screws_per_m: Decimal = Field(gt=0)
    screw_sku: str = Field(min_length=1)
    screw_weight_kg: Decimal | None = Field(default=None, ge=0)
    source: str = Field(min_length=1)


class EffectiveProfileArticle(EngineModel):
    sku: str
    role: ProfileRole
    material: MaterialType
    face_width_mm: Decimal
    section: ProfileSection | None = None
    # UNKNOWN (None) is a first-class state — a catalog that never stated a
    # welding loss or reinforcement gap must not gain an invented one; the
    # consumers that need it (PVC weld math, steel reinforcement cuts) raise
    # honestly when it is exercised.
    welding_loss_mm: Decimal | None
    reinforcement_gap_mm: Decimal | None
    weight_kg_m: Decimal | None
    steel_weight_kg_m: Decimal | None
    reinforcement_sku: str | None = None
    # Bar length the article sells in — None means the catalog never
    # declared one and no stock-length check can run (UNKNOWN, not infinite).
    commercial_length_mm: Decimal | None = None
    cut_rule: ProfileCutRule | None = None
    reinforcement_rule: ProfileReinforcementRule | None = None


class GlazingBeadRule(EngineModel):
    glass_thickness_mm: Decimal
    bead_article: EffectiveProfileArticle
    bead_width_mm: Decimal
    gasket_interior_mm: Decimal
    gasket_exterior_mm: Decimal
    cut_add_mm: Decimal


class PanelRule(EngineModel):
    sku: str
    name: str
    kind: Literal["SANDWICH_PANEL"]
    thickness_mm: Decimal
    weight_kg_m2: Decimal | None


class PanelPiece(EngineModel):
    sku: str
    name: str
    bay_id: str
    leaf_id: str | None = None
    width_mm: Decimal
    height_mm: Decimal
    area_m2: Decimal
    weight_kg: Decimal | None


class LeafWeight(EngineModel):
    bay_id: str
    leaf_id: str | None = None
    # Any component the catalog does not declare stays UNKNOWN (None); the
    # total is only present when every component resolved. Hardware
    # compatibility is never certified on a fabricated mass.
    pvc_weight_kg: Decimal | None
    steel_weight_kg: Decimal | None
    infill_weight_kg: Decimal | None
    hardware_weight_kg: Decimal | None
    total_weight_kg: Decimal | None
    weight_unknown_reasons: list[str] = Field(default_factory=list)


class SlidingSystemParameters(EngineModel):
    pulley_height_mm: Decimal = Field(ge=0)
    central_overlap_mm: Decimal = Field(ge=0)
    lateral_clearance_mm: Decimal = Field(ge=0)
    end_add_mm: Decimal = Field(ge=0)
    glazing_deduction_width_mm: Decimal = Field(ge=0)
    glazing_deduction_height_mm: Decimal = Field(ge=0)
    rail_type: RailType
    rail_count: int = Field(ge=1)
    separate_rail: bool
    interlock_required: bool


class SystemDimensionalLimit(EngineModel):
    opening_type: BayOpeningType
    min_leaf_width_mm: Decimal = Field(gt=0)
    max_leaf_width_mm: Decimal = Field(gt=0)
    min_leaf_height_mm: Decimal = Field(gt=0)
    max_leaf_height_mm: Decimal = Field(gt=0)
    max_leaf_weight_kg: Decimal | None = Field(default=None, gt=0)
    min_aspect_ratio: Decimal = Field(gt=0)
    max_aspect_ratio: Decimal = Field(gt=0)
    source: str = Field(min_length=1)

    @model_validator(mode="after")
    def ordered(self) -> "SystemDimensionalLimit":
        if (self.min_leaf_width_mm > self.max_leaf_width_mm
                or self.min_leaf_height_mm > self.max_leaf_height_mm
                or self.min_aspect_ratio > self.max_aspect_ratio):
            raise ValueError("Los límites mínimos no pueden superar los máximos.")
        return self


class SystemParams(EngineModel):
    @model_serializer(mode="wrap")
    def preserve_historical_finish_authority(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        result: dict[str, Any] = handler(self)
        for key in ("finish_authority", "finish_profile_skus", "extra_authority"):
            if key not in self.model_fields_set:
                result.pop(key, None)
        return result

    system_code: str
    # None decodes pre-family snapshots. New catalogs must declare a family;
    # they never gain legacy mixed-family permission from a guessed value.
    system_family: SystemFamily | None = None
    legacy_authority: bool = False
    sliding: SlidingSystemParameters | None = None
    dimensional_limits: tuple[SystemDimensionalLimit, ...] = ()
    depth_mm: Decimal
    material: MaterialType = MaterialType.PVC
    effective_profile_articles: dict[ProfileRole, EffectiveProfileArticle]
    glazing_bead_rules: dict[Decimal, GlazingBeadRule]
    # Fabrication data the catalog must declare — the engine has no invented
    # constants for the rebate bite or the mullion end-milling overlap.
    rebate_depth_mm: Decimal | None = None
    end_milling_overlap_mm: Decimal | None = None
    sash_overlap_mm: Decimal = Decimal("8.00")
    glass_clearance_white_mm: Decimal = Decimal("3.00")
    glass_clearance_foil_mm: Decimal = Decimal("5.00")
    pulley_height_mm: Decimal | None = None
    central_overlap_mm: Decimal | None = None
    sliding_lateral_clearance_mm: Decimal | None = None
    sliding_end_add_mm: Decimal | None = None
    corner_bracket_loss_mm: Decimal = Decimal("0.00")
    hook_depth_mm: Decimal = Decimal("0.00")
    door_threshold_mm: Decimal = Decimal("30.00")
    door_bottom_clearance_mm: Decimal = Decimal("20.00")
    rail_type: RailType | None = None
    # Physical rails the frame profile provides. None = derive from
    # rail_type (MONO=1, DUAL=2); a catalog with a triple-rail profile
    # declares it explicitly — layouts may never exceed this capacity.
    rail_count: int | None = None
    available_hardware_kits: list[HardwareKitRule] = Field(default_factory=list)
    # Finishes the series actually sells — the estimator picks only declared
    # ones; every non-WHITE finish consumes the foil clearances.
    finishes: tuple[str, ...] = ("WHITE",)
    finish_authority: FinishAuthority | None = None
    finish_profile_skus: dict[str, dict[str, str]] = Field(default_factory=dict)
    extra_authority: ExtraAuthority | None = None
    sliding_glazing_deduction_width_mm: Decimal | None = None
    sliding_glazing_deduction_height_mm: Decimal | None = None
    door_leaf_side_clearance_mm: Decimal
    available_panel_rules: dict[str, PanelRule] = Field(default_factory=dict)
    opening_capabilities: tuple[OpeningCapability, ...] = ()
    paired_leaf_rule: PairedLeafRule | None = None
    # Visible compatible system names enrich refusals; this is presentation
    # context, never a fabrication authority or a numeric input.
    compatible_opening_systems: tuple[tuple[str, tuple[OpeningCapability, ...]], ...] = ()

    @property
    def uses_legacy_rules(self) -> bool:
        return self.system_family is None or self.legacy_authority

    @model_validator(mode="after")
    def family_parameters(self) -> "SystemParams":
        signatures: set[tuple[OpeningUse, OpeningMovement, OpeningDirection, LeafRole, bool, HingeSide]] = set()
        for capability in self.opening_capabilities:
            for hinge in capability.hinge_sides:
                signature = (capability.use, capability.movement, capability.direction,
                             capability.leaf_role, capability.fixed_in_sash, hinge)
                if signature in signatures:
                    raise ValueError("El catálogo declara capacidades de apertura contradictorias.")
                signatures.add(signature)
        if self.uses_legacy_rules:
            for name in ("sliding_glazing_deduction_width_mm", "sliding_glazing_deduction_height_mm"):
                if getattr(self, name) is None:
                    raise ValueError(f"{name}: falta la autoridad histórica explícita.")
            return self
        legacy = (self.pulley_height_mm, self.central_overlap_mm,
                  self.sliding_lateral_clearance_mm, self.sliding_end_add_mm,
                  self.sliding_glazing_deduction_width_mm,
                  self.sliding_glazing_deduction_height_mm, self.rail_type, self.rail_count)
        if self.system_family is not None and any(value is not None for value in legacy):
            raise ValueError("Los parámetros de corredera deben declararse en su familia.")
        if self.system_family in (SystemFamily.SLIDING, SystemFamily.LIFT_SLIDE):
            if self.sliding is None:
                raise ValueError("Faltan los parámetros de la familia corredera.")
        elif self.system_family is not None and self.sliding is not None:
            raise ValueError("Una familia practicable, puerta o fijo no lleva parámetros de corredera.")
        return self


class ParametricNode(EngineModel):
    extras: list[ExtraSelection] = Field(default_factory=list, max_length=30)
    extra_context: ExtraContext | None = None
    id: str
    type: NodeType
    width_mm: Decimal | None = None
    height_mm: Decimal | None = None
    split_offset_mm: Decimal | None = None
    mullion_profile_sku: str | None = None
    children: list[ParametricNode] = Field(default_factory=list)
    opening_type: BayOpeningType | None = None
    opening: Opening | None = None
    opening_use: OpeningUse | None = None
    hinged_layout: HingedLayout | None = None
    glass_thickness_mm: Decimal | None = None
    glass_spec: str | None = None
    glass_article_sku: str | None = None
    glass_product: GlassProduct | None = None
    glass_processing: GlassProcessing | None = None
    sill_height_mm: Decimal | None = Field(default=None, ge=0)
    is_sidelight: bool = False
    panel_article_sku: str | None = None
    hardware_set_sku: str | None = None
    hardware_selection: HardwareSelection | None = None
    handle_height_mm: Decimal | None = None
    # Declared hinge side of a DOOR_ENTRY leaf (DIN convention: LEFT =
    # hinges on the left, handle on the right). Doors carry no side in
    # their opening_type, so handedness must be declared — manufacturing
    # refuses to mount a handle on an undeclared door rather than assume.
    door_handedness: Literal["LEFT", "RIGHT"] | None = None
    # Sliding panel topology (mandate §12). Present on a sliding BAY it
    # fully defines the unit — slots, moving/fixed kind, rail assignment.
    # Absent, the SLIDING_*L presets map to canonical layouts.
    sliding_layout: SlidingLayout | None = None

    @model_validator(mode="after")
    def declared_glass_package(self) -> ParametricNode:
        if self.glass_product is not None:
            thickness = total_glass_thickness(self.glass_product.composition)
            if thickness is None or thickness != self.glass_thickness_mm:
                raise ValueError("El espesor del junquillo debe ser el espesor total de la composición.")
        return self

    @model_serializer(mode="wrap")
    def preserve_legacy_presence(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        result: dict[str, Any] = handler(self)
        for key in ("opening", "opening_use", "hinged_layout", "hardware_selection", "extras", "extra_context"):
            if key not in self.model_fields_set:
                result.pop(key, None)
        return result


class ProfileCut(EngineModel):
    extra_code: str | None = None
    sku: str
    role: ProfileRole
    material: MaterialType
    length_mm: Decimal
    angle_left: Decimal
    angle_right: Decimal
    qty: int
    bay_id: str | None = None
    leaf_id: str | None = None
    # Non-null marks a curved member: length_mm is the arc length and the
    # cut requires bending authority — without one it must surface as a
    # manufacturing-incomplete piece, never a straight cut of that length.
    sagitta_mm: Decimal | None = None
    commercial_sku: str | None = None
    stock_color: str | None = None

    @model_serializer(mode="wrap")
    def preserve_historical_cut(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        result: dict[str, Any] = handler(self)
        for key in ("commercial_sku", "stock_color", "extra_code"):
            if key not in self.model_fields_set:
                result.pop(key, None)
        return result


class FittingPiece(EngineModel):
    """A counted fitting — patch fitting, clamp, hinge, lock, connector,
    seal or point support (mandate §14 frameless domain). Unit pieces, not
    cut lengths; compatibility/mounting intelligence is the §22 concern."""

    kind: str
    sku: str
    qty: int = Field(gt=0)
    bay_id: str | None = None
    leaf_id: str | None = None
    extra_code: str | None = None

    @model_serializer(mode="wrap")
    def preserve_historical_extra(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        result: dict[str, Any] = handler(self)
        if "extra_code" not in self.model_fields_set:
            result.pop("extra_code", None)
        return result


class ReinforcementPiece(EngineModel):
    extra_code: str | None = None
    parent_profile_sku: str
    reinforcement_sku: str | None = None
    role: ProfileRole
    length_mm: Decimal
    qty: int
    bay_id: str | None = None
    leaf_id: str | None = None
    # Curved reinforcement follows its parent member's arc.
    sagitta_mm: Decimal | None = None

    @model_serializer(mode="wrap")
    def preserve_historical_extra(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        result: dict[str, Any] = handler(self)
        if "extra_code" not in self.model_fields_set:
            result.pop("extra_code", None)
        return result


class OpeningHandleFact(EngineModel):
    side: HingeSide
    x_mm: Decimal
    y_mm: Decimal
    height_from_bottom_mm: Decimal
    minimum_height_from_bottom_mm: Decimal
    maximum_height_from_bottom_mm: Decimal
    minimum_from_top_mm: Decimal
    maximum_from_top_mm: Decimal
    source: str


class LeafOpeningFact(EngineModel):
    bay_id: str
    leaf_id: str | None
    opening: Opening
    use: OpeningUse
    x_mm: Decimal
    y_mm: Decimal
    width_mm: Decimal
    height_mm: Decimal
    handle: OpeningHandleFact | None
    source: str


class EngineResult(EngineModel):
    extras: list[ExtraFact] = Field(default_factory=list)
    extra_suggestions: list[ExtraSuggestion] = Field(default_factory=list)
    finish: ResolvedFinish | None = None
    profile_cuts: list[ProfileCut]
    reinforcements: list[ReinforcementPiece]
    glasses: list[GlassPiece]
    panels: list[PanelPiece] = Field(default_factory=list)
    fittings: list[FittingPiece] = Field(default_factory=list)
    hardware_items: list[HardwareItem] = Field(default_factory=list)
    leaf_weights: list[LeafWeight] = Field(default_factory=list)
    opening_leaves: list[LeafOpeningFact] = Field(default_factory=list)

    @model_serializer(mode="wrap")
    def preserve_historical_bom(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        result: dict[str, Any] = handler(self)
        for key in ("opening_leaves", "finish", "extras", "extra_suggestions"):
            if key not in self.model_fields_set:
                result.pop(key, None)
        return result
