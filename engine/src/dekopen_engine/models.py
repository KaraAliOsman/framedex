"""Typed, serializable contracts for Dekopen's pure calculation engine."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class EngineModel(BaseModel):
    """Strict shared configuration for deterministic engine values."""

    model_config = ConfigDict(strict=True, extra="forbid")


class MaterialType(str, Enum):
    PVC = "PVC"
    ALUMINIUM = "ALUMINIUM"


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
    AWNING = "AWNING"
    DOOR_ENTRY = "DOOR_ENTRY"
    DOOR_DOUBLE = "DOOR_DOUBLE"


class GlassPiece(EngineModel):
    bay_id: str
    width_mm: Decimal
    height_mm: Decimal
    area_m2: Decimal
    weight_kg: Decimal
    thickness_net_mm: Decimal


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
    contents: list[dict[str, str]] = Field(default_factory=list)


class EffectiveProfileArticle(EngineModel):
    sku: str
    role: ProfileRole
    face_width_mm: Decimal
    welding_loss_mm: Decimal
    reinforcement_gap_mm: Decimal
    weight_kg_m: Decimal
    steel_weight_kg_m: Decimal
    reinforcement_sku: str | None = None


class GlazingBeadRule(EngineModel):
    glass_thickness_mm: Decimal
    bead_article: EffectiveProfileArticle
    bead_width_mm: Decimal
    gasket_interior_mm: Decimal
    gasket_exterior_mm: Decimal
    cut_add_mm: Decimal


class SystemParams(EngineModel):
    system_code: str
    depth_mm: Decimal
    material: MaterialType = MaterialType.PVC
    effective_profile_articles: dict[ProfileRole, EffectiveProfileArticle]
    glazing_bead_rules: dict[Decimal, GlazingBeadRule]
    rebate_depth_mm: Decimal = Decimal("20.00")
    end_milling_overlap_mm: Decimal = Decimal("0.00")
    sash_overlap_mm: Decimal = Decimal("8.00")
    glass_clearance_white_mm: Decimal = Decimal("3.00")
    glass_clearance_foil_mm: Decimal = Decimal("5.00")
    pulley_height_mm: Decimal = Decimal("12.00")
    central_overlap_mm: Decimal = Decimal("35.00")
    sliding_lateral_clearance_mm: Decimal = Decimal("0.00")
    sliding_end_add_mm: Decimal = Decimal("6.00")
    corner_bracket_loss_mm: Decimal = Decimal("0.00")
    hook_depth_mm: Decimal = Decimal("0.00")
    door_threshold_mm: Decimal = Decimal("30.00")
    door_bottom_clearance_mm: Decimal = Decimal("20.00")
    rail_type: RailType = RailType.DUAL
    pvc_weight_kg_m: Decimal = Decimal("1.2000")
    steel_weight_kg_m: Decimal = Decimal("1.7000")
    hardware_kit_weight_kg: Decimal = Decimal("2.50")
    available_hardware_kits: list[HardwareKitRule] = Field(default_factory=list)


class ParametricNode(EngineModel):
    id: str
    type: NodeType
    width_mm: Decimal | None = None
    height_mm: Decimal | None = None
    split_offset_mm: Decimal | None = None
    mullion_profile_sku: str | None = None
    children: list[ParametricNode] = Field(default_factory=list)
    opening_type: BayOpeningType | None = None
    glass_thickness_mm: Decimal | None = None
    glass_spec: str | None = None
    glass_article_sku: str | None = None
    hardware_set_sku: str | None = None
    handle_height_mm: Decimal | None = None


class ProfileCut(EngineModel):
    sku: str
    role: ProfileRole
    length_mm: Decimal
    angle_left: Decimal
    angle_right: Decimal
    qty: int
    bay_id: str | None = None


class ReinforcementPiece(EngineModel):
    parent_profile_sku: str
    reinforcement_sku: str | None = None
    role: ProfileRole
    length_mm: Decimal
    qty: int
    bay_id: str | None = None


class EngineResult(EngineModel):
    profile_cuts: list[ProfileCut]
    reinforcements: list[ReinforcementPiece]
    glasses: list[GlassPiece]
    hardware_items: list[dict[str, str]] = Field(default_factory=list)
