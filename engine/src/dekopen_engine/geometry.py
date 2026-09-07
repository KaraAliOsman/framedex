"""Pure deterministic geometry for the SHOT-06 Core Gate."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from dekopen_engine.bom import build_engine_result
from dekopen_engine.glass import build_glass_piece, exact_glass_weight, exact_glass_area_m2
from dekopen_engine.hardware import (
    NoCompatibleHardwareKit, evaluate_hardware_candidates, resolve_hardware_evaluations,
)
from dekopen_engine.technical_facts import (
    GeometryComputation, InfillTechnicalFacts, LeafTechnicalFacts, OpeningTechnicalFacts,
    SpanTechnicalFacts,
)
from dekopen_engine.panel import build_panel_piece, exact_panel_weight
from dekopen_engine.weight import base_leaf_weight
from dekopen_engine.models import (
    BayOpeningType,
    EffectiveProfileArticle,
    EngineResult,
    GlassPiece,
    GlazingBeadRule,
    HardwareItem,
    LeafWeight,
    PanelPiece,
    MaterialType,
    NodeType,
    ParametricNode,
    ProfileCut,
    ProfileRole,
    RailType,
    ReinforcementPiece,
    SystemParams,
)

_TWO = Decimal("2")
_ANGLE_WELDED = Decimal("45.0")
_ANGLE_SQUARE = Decimal("90.0")

SUPPORTED_OPENING_TYPES = frozenset(
    {
        BayOpeningType.FIXED,
        BayOpeningType.TURN_LEFT,
        BayOpeningType.TURN_RIGHT,
        BayOpeningType.TILT_TURN_LEFT,
        BayOpeningType.TILT_TURN_RIGHT,
        BayOpeningType.SLIDING_2L,
        BayOpeningType.AWNING,
        BayOpeningType.DOOR_ENTRY,
    }
)

_OPERABLE_OPENING_TYPES = frozenset(
    {
        BayOpeningType.TURN_LEFT,
        BayOpeningType.TURN_RIGHT,
        BayOpeningType.TILT_TURN_LEFT,
        BayOpeningType.TILT_TURN_RIGHT,
        BayOpeningType.AWNING,
    }
)


@dataclass(frozen=True, slots=True)
class _Rect:
    x_mm: Decimal
    y_mm: Decimal
    width_mm: Decimal
    height_mm: Decimal

    @property
    def right_mm(self) -> Decimal:
        return self.x_mm + self.width_mm

    @property
    def bottom_mm(self) -> Decimal:
        return self.y_mm + self.height_mm


@dataclass(slots=True)
class _GeometryAccumulator:
    computation: GeometryComputation = field(default_factory=GeometryComputation)
    diagnostic: bool = False
    contract_valid: bool = True
    top_node_id: str = ""
    nominal_width_mm: Decimal = Decimal("0")
    nominal_height_mm: Decimal = Decimal("0")
    profile_cuts: list[ProfileCut] = field(default_factory=list)
    reinforcements: list[ReinforcementPiece] = field(default_factory=list)
    glasses: list[GlassPiece] = field(default_factory=list)
    panels: list[PanelPiece] = field(default_factory=list)
    hardware_items: list[HardwareItem] = field(default_factory=list)
    leaf_weights: list[LeafWeight] = field(default_factory=list)


def welding_loss_per_end(article: EffectiveProfileArticle) -> Decimal:
    """Derive a per-end loss from the effective article's sole DB authority."""

    return article.welding_loss_mm / _TWO


def _article(params: SystemParams, role: ProfileRole) -> EffectiveProfileArticle:
    try:
        article = params.effective_profile_articles[role]
    except KeyError as error:
        raise ValueError(f"Missing effective profile article for role {role.value}") from error
    if article.role is not role:
        raise ValueError(f"Effective profile article key {role.value} has role {article.role.value}")
    return article


def _normalize_top_node(root: ParametricNode) -> tuple[ParametricNode, Decimal, Decimal]:
    if root.type is NodeType.ROOT:
        if len(root.children) != 1:
            raise ValueError("ROOT must wrap exactly one parametric node")
        top = root.children[0]
        width_mm = root.width_mm if root.width_mm is not None else top.width_mm
        height_mm = root.height_mm if root.height_mm is not None else top.height_mm
        if root.width_mm is not None and top.width_mm not in (None, root.width_mm):
            raise ValueError("ROOT and wrapped node widths disagree")
        if root.height_mm is not None and top.height_mm not in (None, root.height_mm):
            raise ValueError("ROOT and wrapped node heights disagree")
    else:
        top = root
        width_mm = root.width_mm
        height_mm = root.height_mm

    if width_mm is None or height_mm is None:
        raise ValueError("Top-level width_mm and height_mm are required")
    if width_mm <= Decimal("0") or height_mm <= Decimal("0"):
        raise ValueError("Top-level dimensions must be positive")
    return top, width_mm, height_mm


def reinforcement_cut_length(
    cut_mm: Decimal, article: EffectiveProfileArticle, welded_end_count: int,
) -> Decimal:
    return (cut_mm - Decimal(welded_end_count) * welding_loss_per_end(article)
            - _TWO * article.reinforcement_gap_mm)


def _append_profile(
    accumulator: _GeometryAccumulator, *, article: EffectiveProfileArticle,
    length_mm: Decimal, qty: int, welded_ends: int | None,
    angle_left: Decimal = _ANGLE_WELDED, angle_right: Decimal = _ANGLE_WELDED,
    bay_id: str | None = None, leaf_id: str | None = None,
) -> None:
    if length_mm <= Decimal("0"):
        raise ValueError("Profile cut must be positive")
    accumulator.profile_cuts.append(ProfileCut(
        sku=article.sku, role=article.role, material=article.material, length_mm=length_mm,
        angle_left=angle_left, angle_right=angle_right, qty=qty, bay_id=bay_id, leaf_id=leaf_id,
    ))
    if welded_ends is not None:
        steel_length = reinforcement_cut_length(length_mm, article, welded_ends)
        if steel_length <= Decimal("0"):
            raise ValueError("Reinforcement cut must be positive")
        accumulator.reinforcements.append(ReinforcementPiece(
            parent_profile_sku=article.sku, reinforcement_sku=article.reinforcement_sku,
            role=article.role, length_mm=steel_length, qty=qty, bay_id=bay_id, leaf_id=leaf_id,
        ))


def _append_frame(
    accumulator: _GeometryAccumulator, *, frame_article: EffectiveProfileArticle,
    nominal_width_mm: Decimal, nominal_height_mm: Decimal,
) -> None:
    for length in (nominal_width_mm, nominal_height_mm):
        _append_profile(
            accumulator, article=frame_article,
            length_mm=length + _TWO * welding_loss_per_end(frame_article), qty=2, welded_ends=2,
        )


def resolve_bead_rule(infill_thickness_mm: Decimal, params: SystemParams) -> GlazingBeadRule:
    try:
        rule = params.glazing_bead_rules[infill_thickness_mm]
    except KeyError as error:
        raise ValueError(f"Missing glazing bead rule for {infill_thickness_mm} mm infill") from error
    if rule.bead_article.role is not ProfileRole.GLAZING_BEAD:
        raise ValueError("Glazing bead rule must reference a GLAZING_BEAD article")
    return rule


def _append_glazing_beads(
    accumulator: _GeometryAccumulator, *, params: SystemParams, bay_id: str,
    leaf_id: str | None, infill_thickness_mm: Decimal, width_mm: Decimal, height_mm: Decimal,
) -> None:
    if accumulator.diagnostic and infill_thickness_mm not in params.glazing_bead_rules:
        accumulator.contract_valid = False
        return
    rule = resolve_bead_rule(infill_thickness_mm, params)
    for length in (width_mm, height_mm):
        _append_profile(
            accumulator, article=rule.bead_article, length_mm=length + rule.cut_add_mm,
            qty=2, welded_ends=None, bay_id=bay_id, leaf_id=leaf_id,
        )


@dataclass(frozen=True, slots=True)
class SashGeometry:
    finished_width_mm: Decimal
    finished_height_mm: Decimal
    cut_width_mm: Decimal
    cut_height_mm: Decimal


def _welded_sash(width: Decimal, height: Decimal, article: EffectiveProfileArticle) -> SashGeometry:
    loss = _TWO * welding_loss_per_end(article)
    return SashGeometry(width, height, width + loss, height + loss)


def single_rectangular_sash_geometry(
    inner_width_mm: Decimal, inner_height_mm: Decimal,
    article: EffectiveProfileArticle, params: SystemParams,
) -> SashGeometry:
    """Shared finished-and-cut primitive for TURN, TILT_TURN and AWNING."""
    return _welded_sash(
        inner_width_mm + _TWO * params.sash_overlap_mm,
        inner_height_mm + _TWO * params.sash_overlap_mm, article,
    )


def _pocket_dimension(
    finished_mm: Decimal, article: EffectiveProfileArticle,
    params: SystemParams, clearance_mm: Decimal,
) -> Decimal:
    return (finished_mm - _TWO * article.face_width_mm
            + _TWO * params.rebate_depth_mm - _TWO * clearance_mm)


def _append_leaf(
    accumulator: _GeometryAccumulator, *, node: ParametricNode, leaf_id: str | None,
    sash: SashGeometry, params: SystemParams, clearance_mm: Decimal,
) -> None:
    article = _article(params, ProfileRole.SASH)
    cut_start = len(accumulator.profile_cuts)
    steel_start = len(accumulator.reinforcements)
    for length in (sash.cut_width_mm, sash.cut_height_mm):
        _append_profile(accumulator, article=article, length_mm=length, qty=2,
                        welded_ends=2, bay_id=node.id, leaf_id=leaf_id)
    width = _pocket_dimension(sash.finished_width_mm, article, params, clearance_mm)
    height = _pocket_dimension(sash.finished_height_mm, article, params, clearance_mm)
    if node.opening_type is BayOpeningType.SLIDING_2L:
        width -= params.sliding_glazing_deduction_width_mm
        height -= params.sliding_glazing_deduction_height_mm
    if node.opening_type is BayOpeningType.DOOR_ENTRY:
        if node.panel_article_sku is None:
            raise ValueError(f"DOOR_ENTRY {node.id} requires panel_article_sku")
        try:
            rule = params.available_panel_rules[node.panel_article_sku]
        except KeyError as error:
            raise ValueError(f"Missing panel article: {node.panel_article_sku}") from error
        infill_thickness = rule.thickness_mm
        infill_weight = exact_panel_weight(width, height, rule)
        accumulator.panels.append(build_panel_piece(
            bay_id=node.id, leaf_id=leaf_id, width_mm=width, height_mm=height, rule=rule,
        ))
    else:
        if node.glass_thickness_mm is None or node.glass_spec is None:
            raise ValueError(f"BAY {node.id} requires glass_thickness_mm and glass_spec")
        infill_thickness = node.glass_thickness_mm
        infill_weight = exact_glass_weight(width, height, node.glass_spec, infill_thickness)
        accumulator.glasses.append(build_glass_piece(
            bay_id=node.id, leaf_id=leaf_id, width_mm=width, height_mm=height,
            glass_spec=node.glass_spec, fallback_thickness_mm=infill_thickness,
        ))
    accumulator.computation.infills.append(InfillTechnicalFacts(
        bay_id=node.id, leaf_id=leaf_id,
        kind="PANEL" if node.opening_type is BayOpeningType.DOOR_ENTRY else "GLASS",
        thickness_mm=infill_thickness, glass_spec=node.glass_spec,
        width_mm=width, height_mm=height, exact_area_m2=exact_glass_area_m2(width, height),
        bead_supported=infill_thickness in params.glazing_bead_rules,
    ))
    _append_glazing_beads(
        accumulator, params=params, bay_id=node.id, leaf_id=leaf_id,
        infill_thickness_mm=infill_thickness, width_mm=width, height_mm=height,
    )
    base = base_leaf_weight(
        profile_cuts=accumulator.profile_cuts[cut_start:],
        reinforcements=accumulator.reinforcements[steel_start:],
        infill_weight_kg=infill_weight, params=params,
    )
    assert node.opening_type is not None
    candidates = evaluate_hardware_candidates(
        opening=node.opening_type, width_mm=sash.finished_width_mm,
        height_mm=sash.finished_height_mm, base_weight=base, params=params,
        explicit_sku=node.hardware_set_sku,
    )
    try:
        kit, exact_weight = resolve_hardware_evaluations(
            candidates, opening=node.opening_type, explicit_sku=node.hardware_set_sku,
        )
    except NoCompatibleHardwareKit:
        if not accumulator.diagnostic:
            raise
        accumulator.contract_valid = False
        kit, exact_weight = None, None
    accumulator.computation.leaves.append(LeafTechnicalFacts(
        bay_id=node.id, leaf_id=leaf_id, opening_type=node.opening_type,
        rail_type=params.rail_type, finished_width_mm=sash.finished_width_mm,
        finished_height_mm=sash.finished_height_mm, base_weight=base,
        candidates=candidates, selected_kit=kit, exact_weight=exact_weight,
    ))
    if kit is None or exact_weight is None:
        return
    accumulator.hardware_items.append(HardwareItem(
        kit_sku=kit.sku, name=kit.name, bay_id=node.id, leaf_id=leaf_id,
        contents=[component.model_copy() for component in kit.contents],
    ))
    accumulator.leaf_weights.append(exact_weight.public_result(node.id, leaf_id))


def _append_bay(
    accumulator: _GeometryAccumulator, *, node: ParametricNode, rect: _Rect,
    params: SystemParams, clearance_mm: Decimal,
) -> None:
    opening = node.opening_type
    if opening is None:
        raise ValueError(f"BAY {node.id} requires opening_type")
    if opening not in SUPPORTED_OPENING_TYPES:
        raise NotImplementedError(f"{opening.value} geometry is outside SHOT-06 Core")
    if opening is BayOpeningType.DOOR_ENTRY:
        raise NotImplementedError("DOOR_ENTRY requires a top-level BAY in SHOT-06 Core")
    accumulator.computation.openings.append(OpeningTechnicalFacts(
        bay_id=node.id,
        width_mm=(accumulator.nominal_width_mm if node.id == accumulator.top_node_id
                  else rect.width_mm),
        height_mm=(accumulator.nominal_height_mm if node.id == accumulator.top_node_id
                   else rect.height_mm),
    ))
    if opening is BayOpeningType.FIXED:
        if node.glass_thickness_mm is None or node.glass_spec is None:
            raise ValueError(f"BAY {node.id} requires glass_thickness_mm and glass_spec")
        width = rect.width_mm + _TWO * params.rebate_depth_mm - _TWO * clearance_mm
        height = rect.height_mm + _TWO * params.rebate_depth_mm - _TWO * clearance_mm
        accumulator.glasses.append(build_glass_piece(
            bay_id=node.id, width_mm=width, height_mm=height,
            glass_spec=node.glass_spec, fallback_thickness_mm=node.glass_thickness_mm,
        ))
        accumulator.computation.infills.append(InfillTechnicalFacts(
            bay_id=node.id, leaf_id=None, kind="GLASS", thickness_mm=node.glass_thickness_mm,
            glass_spec=node.glass_spec, width_mm=width, height_mm=height,
            exact_area_m2=exact_glass_area_m2(width, height),
            bead_supported=node.glass_thickness_mm in params.glazing_bead_rules,
        ))
        _append_glazing_beads(
            accumulator, params=params, bay_id=node.id, leaf_id=None,
            infill_thickness_mm=node.glass_thickness_mm, width_mm=width, height_mm=height,
        )
        return
    article = _article(params, ProfileRole.SASH)
    if opening in _OPERABLE_OPENING_TYPES:
        sash = single_rectangular_sash_geometry(rect.width_mm, rect.height_mm, article, params)
        _append_leaf(accumulator, node=node, leaf_id=None, sash=sash,
                     params=params, clearance_mm=clearance_mm)
    elif opening is BayOpeningType.SLIDING_2L:
        if params.rail_type is not RailType.DUAL:
            raise NotImplementedError("G10 monorail geometry is deferred to SHOT-24")
        cut_width = (rect.width_mm + params.central_overlap_mm) / _TWO + params.sliding_end_add_mm
        cut_height = rect.height_mm - _TWO * params.pulley_height_mm
        sash = SashGeometry(
            cut_width - article.welding_loss_mm, cut_height - article.welding_loss_mm,
            cut_width, cut_height,
        )
        for suffix in ("L1", "L2"):
            _append_leaf(accumulator, node=node, leaf_id=f"{node.id}:{suffix}",
                         sash=sash, params=params, clearance_mm=clearance_mm)


def _append_door(
    accumulator: _GeometryAccumulator, *, node: ParametricNode, params: SystemParams,
    nominal_width_mm: Decimal, nominal_height_mm: Decimal, clearance_mm: Decimal,
) -> None:
    accumulator.computation.openings.append(OpeningTechnicalFacts(
        bay_id=node.id, width_mm=nominal_width_mm, height_mm=nominal_height_mm,
    ))
    frame = _article(params, ProfileRole.FRAME)
    per_end = welding_loss_per_end(frame)
    _append_profile(accumulator, article=frame,
                    length_mm=nominal_width_mm + _TWO * per_end, qty=1, welded_ends=2)
    _append_profile(accumulator, article=frame,
                    length_mm=nominal_height_mm + per_end, qty=2, welded_ends=1,
                    angle_right=_ANGLE_SQUARE)
    clear_width = nominal_width_mm - _TWO * frame.face_width_mm
    _append_profile(accumulator, article=_article(params, ProfileRole.THRESHOLD),
                    length_mm=clear_width, qty=1, welded_ends=None,
                    angle_left=_ANGLE_SQUARE, angle_right=_ANGLE_SQUARE, bay_id=node.id)
    outer_width = clear_width - _TWO * params.door_leaf_side_clearance_mm
    outer_height = (nominal_height_mm - frame.face_width_mm - params.door_threshold_mm
                    - params.door_bottom_clearance_mm + params.sash_overlap_mm)
    sash = _welded_sash(outer_width, outer_height, _article(params, ProfileRole.SASH))
    _append_leaf(accumulator, node=node, leaf_id=None, sash=sash,
                 params=params, clearance_mm=clearance_mm)


def _append_mullion(
    accumulator: _GeometryAccumulator,
    *,
    article: EffectiveProfileArticle,
    length_mm: Decimal,
) -> None:
    accumulator.profile_cuts.append(
        ProfileCut(
            sku=article.sku,
            material=article.material,
            role=article.role,
            length_mm=length_mm,
            angle_left=_ANGLE_SQUARE,
            angle_right=_ANGLE_SQUARE,
            qty=1,
        )
    )
    accumulator.reinforcements.append(
        ReinforcementPiece(
            parent_profile_sku=article.sku,
            reinforcement_sku=article.reinforcement_sku,
            role=article.role,
            length_mm=length_mm - _TWO * article.reinforcement_gap_mm,
            qty=1,
        )
    )


def _walk_node(
    accumulator: _GeometryAccumulator,
    *,
    node: ParametricNode,
    rect: _Rect,
    local_origin_x_mm: Decimal,
    local_origin_y_mm: Decimal,
    params: SystemParams,
    clearance_mm: Decimal,
    is_top: bool,
) -> None:
    if not is_top and (node.width_mm is not None or node.height_mm is not None):
        raise ValueError("Child node dimensions are derived and must not be supplied")

    if node.type is NodeType.BAY:
        _append_bay(
            accumulator,
            node=node,
            rect=rect,
            params=params,
            clearance_mm=clearance_mm,
        )
        return

    if node.type not in (NodeType.SPLIT_V, NodeType.SPLIT_H):
        raise ValueError("Only a top-level ROOT wrapper is allowed")
    if node.split_offset_mm is None or node.mullion_profile_sku is None:
        raise ValueError(f"{node.type.value} requires split offset and mullion SKU")
    if len(node.children) != 2:
        raise ValueError(f"{node.type.value} must contain exactly two children")

    if node.type is NodeType.SPLIT_V:
        mullion_role = ProfileRole.MULLION_V
    else:
        mullion_role = ProfileRole.MULLION_H
    mullion_article = _article(params, mullion_role)
    if mullion_article.sku != node.mullion_profile_sku:
        raise ValueError(
            f"Split requests {node.mullion_profile_sku}, but effective article is "
            f"{mullion_article.sku}"
        )

    half_mullion_face = mullion_article.face_width_mm / _TWO
    if node.type is NodeType.SPLIT_V:
        centerline_mm = local_origin_x_mm + node.split_offset_mm
        first_width_mm = centerline_mm - half_mullion_face - rect.x_mm
        second_x_mm = centerline_mm + half_mullion_face
        second_width_mm = rect.right_mm - second_x_mm
        if first_width_mm <= Decimal("0") or second_width_mm <= Decimal("0"):
            raise ValueError("SPLIT_V produces a non-positive BAY width")
        first_rect = _Rect(rect.x_mm, rect.y_mm, first_width_mm, rect.height_mm)
        second_rect = _Rect(second_x_mm, rect.y_mm, second_width_mm, rect.height_mm)
        mullion_length_mm = (
            rect.height_mm + _TWO * params.end_milling_overlap_mm
        )
    else:
        centerline_mm = local_origin_y_mm + node.split_offset_mm
        first_height_mm = centerline_mm - half_mullion_face - rect.y_mm
        second_y_mm = centerline_mm + half_mullion_face
        second_height_mm = rect.bottom_mm - second_y_mm
        if first_height_mm <= Decimal("0") or second_height_mm <= Decimal("0"):
            raise ValueError("SPLIT_H produces a non-positive BAY height")
        first_rect = _Rect(rect.x_mm, rect.y_mm, rect.width_mm, first_height_mm)
        second_rect = _Rect(rect.x_mm, second_y_mm, rect.width_mm, second_height_mm)
        mullion_length_mm = rect.width_mm + _TWO * params.end_milling_overlap_mm

    _append_mullion(
        accumulator,
        article=mullion_article,
        length_mm=mullion_length_mm,
    )
    accumulator.computation.spans.append(SpanTechnicalFacts(
        target_id=node.id, parent_profile_sku=mullion_article.sku,
        span_mm=rect.height_mm if node.type is NodeType.SPLIT_V else rect.width_mm,
    ))
    _walk_node(
        accumulator,
        node=node.children[0],
        rect=first_rect,
        local_origin_x_mm=first_rect.x_mm,
        local_origin_y_mm=first_rect.y_mm,
        params=params,
        clearance_mm=clearance_mm,
        is_top=False,
    )
    _walk_node(
        accumulator,
        node=node.children[1],
        rect=second_rect,
        local_origin_x_mm=second_rect.x_mm,
        local_origin_y_mm=second_rect.y_mm,
        params=params,
        clearance_mm=clearance_mm,
        is_top=False,
    )


def compute_geometry(
    root: ParametricNode,
    params: SystemParams,
    *,
    is_foiled: bool = False,
    diagnostic: bool = False,
) -> GeometryComputation:
    """Calculate Core geometry, mobile-leaf weights and selected hardware."""

    if params.material is not MaterialType.PVC:
        raise NotImplementedError("SHOT-03 implements PVC geometry only")

    top, nominal_width_mm, nominal_height_mm = _normalize_top_node(root)
    frame_article = _article(params, ProfileRole.FRAME)
    clear_width_mm = nominal_width_mm - _TWO * frame_article.face_width_mm
    clear_height_mm = nominal_height_mm - _TWO * frame_article.face_width_mm
    if clear_width_mm <= Decimal("0") or clear_height_mm <= Decimal("0"):
        raise ValueError("FRAME face produces a non-positive clear rectangle")

    accumulator = _GeometryAccumulator(
        diagnostic=diagnostic, top_node_id=top.id, nominal_width_mm=nominal_width_mm,
        nominal_height_mm=nominal_height_mm,
    )
    clearance_mm = (
        params.glass_clearance_foil_mm if is_foiled else params.glass_clearance_white_mm
    )
    if top.type is NodeType.BAY and top.opening_type is BayOpeningType.DOOR_ENTRY:
        _append_door(accumulator, node=top, params=params,
                     nominal_width_mm=nominal_width_mm, nominal_height_mm=nominal_height_mm,
                     clearance_mm=clearance_mm)
    else:
        _append_frame(
            accumulator, frame_article=frame_article,
            nominal_width_mm=nominal_width_mm, nominal_height_mm=nominal_height_mm,
        )
        frame_clear_rect = _Rect(
            x_mm=frame_article.face_width_mm, y_mm=frame_article.face_width_mm,
            width_mm=clear_width_mm, height_mm=clear_height_mm,
        )
        _walk_node(
            accumulator, node=top, rect=frame_clear_rect,
            local_origin_x_mm=Decimal("0"), local_origin_y_mm=Decimal("0"),
            params=params, clearance_mm=clearance_mm, is_top=True,
        )
    if accumulator.contract_valid:
        accumulator.computation.result = build_engine_result(
            profile_cuts=accumulator.profile_cuts,
            reinforcements=accumulator.reinforcements,
            glasses=accumulator.glasses,
            panels=accumulator.panels,
            hardware_items=accumulator.hardware_items,
            leaf_weights=accumulator.leaf_weights,
        )
    return accumulator.computation


def calculate_geometry(
    root: ParametricNode, params: SystemParams, *, is_foiled: bool = False,
) -> EngineResult:
    """Strict public SHOT-06 contract; diagnostic facts never replace a valid BOM."""
    computation = compute_geometry(root, params, is_foiled=is_foiled)
    assert computation.result is not None
    return computation.result
