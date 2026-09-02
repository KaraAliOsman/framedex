"""Pure deterministic geometry for SHOT-03 core opening types."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from dekopen_engine.bom import build_engine_result
from dekopen_engine.glass import build_glass_piece
from dekopen_engine.models import (
    BayOpeningType,
    EffectiveProfileArticle,
    EngineResult,
    GlassPiece,
    MaterialType,
    NodeType,
    ParametricNode,
    ProfileCut,
    ProfileRole,
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
    }
)

_OPERABLE_OPENING_TYPES = frozenset(
    {
        BayOpeningType.TURN_LEFT,
        BayOpeningType.TURN_RIGHT,
        BayOpeningType.TILT_TURN_LEFT,
        BayOpeningType.TILT_TURN_RIGHT,
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
    profile_cuts: list[ProfileCut] = field(default_factory=list)
    reinforcements: list[ReinforcementPiece] = field(default_factory=list)
    glasses: list[GlassPiece] = field(default_factory=list)


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


def _append_frame(
    accumulator: _GeometryAccumulator,
    *,
    frame_article: EffectiveProfileArticle,
    nominal_width_mm: Decimal,
    nominal_height_mm: Decimal,
) -> None:
    loss_per_end = welding_loss_per_end(frame_article)
    horizontal_cut = nominal_width_mm + _TWO * loss_per_end
    vertical_cut = nominal_height_mm + _TWO * loss_per_end
    horizontal_steel = horizontal_cut - _TWO * (
        loss_per_end + frame_article.reinforcement_gap_mm
    )
    vertical_steel = vertical_cut - _TWO * (
        loss_per_end + frame_article.reinforcement_gap_mm
    )

    for length_mm in (horizontal_cut, vertical_cut):
        accumulator.profile_cuts.append(
            ProfileCut(
                sku=frame_article.sku,
                role=ProfileRole.FRAME,
                length_mm=length_mm,
                angle_left=_ANGLE_WELDED,
                angle_right=_ANGLE_WELDED,
                qty=2,
            )
        )
    for length_mm in (horizontal_steel, vertical_steel):
        accumulator.reinforcements.append(
            ReinforcementPiece(
                parent_profile_sku=frame_article.sku,
                reinforcement_sku=frame_article.reinforcement_sku,
                role=ProfileRole.FRAME,
                length_mm=length_mm,
                qty=2,
            )
        )


def _require_bay_glass(node: ParametricNode) -> tuple[BayOpeningType, Decimal, str]:
    if node.opening_type is None:
        raise ValueError(f"BAY {node.id} requires opening_type")
    if node.glass_thickness_mm is None or node.glass_spec is None:
        raise ValueError(f"BAY {node.id} requires glass_thickness_mm and glass_spec")
    return node.opening_type, node.glass_thickness_mm, node.glass_spec


def _append_glazing_beads(
    accumulator: _GeometryAccumulator,
    *,
    params: SystemParams,
    bay_id: str,
    glass_thickness_mm: Decimal,
    glass_width_mm: Decimal,
    glass_height_mm: Decimal,
) -> None:
    try:
        bead_rule = params.glazing_bead_rules[glass_thickness_mm]
    except KeyError as error:
        raise ValueError(
            f"Missing glazing bead rule for {glass_thickness_mm} mm glass"
        ) from error
    if bead_rule.bead_article.role is not ProfileRole.GLAZING_BEAD:
        raise ValueError("Glazing bead rule must reference a GLAZING_BEAD article")

    for glass_length_mm in (glass_width_mm, glass_height_mm):
        accumulator.profile_cuts.append(
            ProfileCut(
                sku=bead_rule.bead_article.sku,
                role=ProfileRole.GLAZING_BEAD,
                length_mm=glass_length_mm + bead_rule.cut_add_mm,
                angle_left=_ANGLE_WELDED,
                angle_right=_ANGLE_WELDED,
                qty=2,
                bay_id=bay_id,
            )
        )


def _append_bay(
    accumulator: _GeometryAccumulator,
    *,
    node: ParametricNode,
    rect: _Rect,
    params: SystemParams,
    clearance_mm: Decimal,
) -> None:
    opening_type, glass_thickness_mm, glass_spec = _require_bay_glass(node)
    if opening_type not in SUPPORTED_OPENING_TYPES:
        raise NotImplementedError(
            f"{opening_type.value} geometry is outside SHOT-03"
        )

    if opening_type is BayOpeningType.FIXED:
        glass_width_mm = (
            rect.width_mm + _TWO * params.rebate_depth_mm - _TWO * clearance_mm
        )
        glass_height_mm = (
            rect.height_mm + _TWO * params.rebate_depth_mm - _TWO * clearance_mm
        )
    else:
        sash_article = _article(params, ProfileRole.SASH)
        sash_loss_per_end = welding_loss_per_end(sash_article)
        sash_outer_width_mm = rect.width_mm + _TWO * params.sash_overlap_mm
        sash_outer_height_mm = rect.height_mm + _TWO * params.sash_overlap_mm
        sash_horizontal_cut = sash_outer_width_mm + _TWO * sash_loss_per_end
        sash_vertical_cut = sash_outer_height_mm + _TWO * sash_loss_per_end

        for length_mm in (sash_horizontal_cut, sash_vertical_cut):
            accumulator.profile_cuts.append(
                ProfileCut(
                    sku=sash_article.sku,
                    role=ProfileRole.SASH,
                    length_mm=length_mm,
                    angle_left=_ANGLE_WELDED,
                    angle_right=_ANGLE_WELDED,
                    qty=2,
                    bay_id=node.id,
                )
            )
        for length_mm in (sash_horizontal_cut, sash_vertical_cut):
            steel_length_mm = length_mm - _TWO * (
                sash_loss_per_end + sash_article.reinforcement_gap_mm
            )
            accumulator.reinforcements.append(
                ReinforcementPiece(
                    parent_profile_sku=sash_article.sku,
                    reinforcement_sku=sash_article.reinforcement_sku,
                    role=ProfileRole.SASH,
                    length_mm=steel_length_mm,
                    qty=2,
                    bay_id=node.id,
                )
            )

        glass_width_mm = (
            sash_outer_width_mm
            - _TWO * sash_article.face_width_mm
            + _TWO * params.rebate_depth_mm
            - _TWO * clearance_mm
        )
        glass_height_mm = (
            sash_outer_height_mm
            - _TWO * sash_article.face_width_mm
            + _TWO * params.rebate_depth_mm
            - _TWO * clearance_mm
        )

    accumulator.glasses.append(
        build_glass_piece(
            bay_id=node.id,
            width_mm=glass_width_mm,
            height_mm=glass_height_mm,
            glass_spec=glass_spec,
            fallback_thickness_mm=glass_thickness_mm,
        )
    )
    _append_glazing_beads(
        accumulator,
        params=params,
        bay_id=node.id,
        glass_thickness_mm=glass_thickness_mm,
        glass_width_mm=glass_width_mm,
        glass_height_mm=glass_height_mm,
    )


def _append_mullion(
    accumulator: _GeometryAccumulator,
    *,
    article: EffectiveProfileArticle,
    length_mm: Decimal,
) -> None:
    accumulator.profile_cuts.append(
        ProfileCut(
            sku=article.sku,
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


def calculate_geometry(
    root: ParametricNode,
    params: SystemParams,
    *,
    is_foiled: bool = False,
) -> EngineResult:
    """Calculate SHOT-03 FRAME/BAY/MULLION geometry and its deterministic BOM."""

    if params.material is not MaterialType.PVC:
        raise NotImplementedError("SHOT-03 implements PVC geometry only")

    top, nominal_width_mm, nominal_height_mm = _normalize_top_node(root)
    frame_article = _article(params, ProfileRole.FRAME)
    clear_width_mm = nominal_width_mm - _TWO * frame_article.face_width_mm
    clear_height_mm = nominal_height_mm - _TWO * frame_article.face_width_mm
    if clear_width_mm <= Decimal("0") or clear_height_mm <= Decimal("0"):
        raise ValueError("FRAME face produces a non-positive clear rectangle")

    accumulator = _GeometryAccumulator()
    _append_frame(
        accumulator,
        frame_article=frame_article,
        nominal_width_mm=nominal_width_mm,
        nominal_height_mm=nominal_height_mm,
    )
    frame_clear_rect = _Rect(
        x_mm=frame_article.face_width_mm,
        y_mm=frame_article.face_width_mm,
        width_mm=clear_width_mm,
        height_mm=clear_height_mm,
    )
    clearance_mm = (
        params.glass_clearance_foil_mm
        if is_foiled
        else params.glass_clearance_white_mm
    )
    _walk_node(
        accumulator,
        node=top,
        rect=frame_clear_rect,
        local_origin_x_mm=Decimal("0"),
        local_origin_y_mm=Decimal("0"),
        params=params,
        clearance_mm=clearance_mm,
        is_top=True,
    )
    return build_engine_result(
        profile_cuts=accumulator.profile_cuts,
        reinforcements=accumulator.reinforcements,
        glasses=accumulator.glasses,
    )
