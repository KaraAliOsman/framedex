"""Exact configuration, observations and declarative Inspector contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import Field, field_validator

from dekopen_engine.models import EngineModel
from dekopen_engine.technical_facts import GeometryComputation


class InspectorConfigurationError(ValueError):
    pass


class InspectorRuleId(str, Enum):
    R01 = "R01"
    R02 = "R02"
    R03 = "R03"
    R04 = "R04"
    R05 = "R05"
    R06 = "R06"
    R07 = "R07"
    R08 = "R08"
    R09 = "R09"
    R10 = "R10"
    R11 = "R11"
    R12 = "R12"
    R13 = "R13"
    R14 = "R14"


class InspectorSeverity(str, Enum):
    YELLOW = "YELLOW"
    RED = "RED"


class RuleEvaluationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    MISSING_INPUT = "MISSING_INPUT"


class Fixability(str, Enum):
    AUTO_FIXABLE = "AUTO_FIXABLE"
    SUGGESTION_ONLY = "SUGGESTION_ONLY"
    BLOCKED_MISSING_AUTHORITY = "BLOCKED_MISSING_AUTHORITY"


class InspectionMode(str, Enum):
    DESIGN = "DESIGN"
    WORKSHOP_QC = "WORKSHOP_QC"


class InspectorTarget(EngineModel):
    bay_id: str
    leaf_id: str | None = None


class WorkshopAnnotations(EngineModel):
    bay_id: str
    leaf_id: str | None = None
    bottom_drain_holes_mm: list[Decimal] | None = None
    closing_points_perimeter_mm: list[Decimal] | None = None
    continuous_width_mm: Decimal | None = Field(default=None, gt=Decimal("0"))
    finish_class: Literal["WHITE", "FOILED"] | None = None
    has_coupler: bool | None = None
    measured_d1_mm: Decimal | None = Field(default=None, gt=Decimal("0"))
    measured_d2_mm: Decimal | None = Field(default=None, gt=Decimal("0"))

    @field_validator("bottom_drain_holes_mm", "closing_points_perimeter_mm")
    @classmethod
    def unique_coordinates(cls, value: list[Decimal] | None) -> list[Decimal] | None:
        if value is not None and (len(value) != len(set(value)) or any(x < 0 for x in value)):
            raise ValueError("Coordinates must be distinct and nonnegative")
        return value


class StructuralInput(EngineModel):
    target_id: str
    required_ix_cm4: Decimal | None = Field(default=None, gt=Decimal("0"))
    structural_basis: str | None = None


class AddBottomDrainHole(EngineModel):
    kind: Literal["ADD_BOTTOM_DRAIN_HOLE"] = "ADD_BOTTOM_DRAIN_HOLE"
    target: InspectorTarget
    old_value: list[Decimal]
    new_value: list[Decimal]


class DiffPreconditions(EngineModel):
    opening_width_mm: Decimal
    bottom_drain_holes_mm: list[Decimal]


class InspectorDiff(EngineModel):
    diff_id: str
    rule_id: Literal["R07"] = "R07"
    target: InspectorTarget
    preconditions: DiffPreconditions
    operations: list[AddBottomDrainHole]


class InspectorFinding(EngineModel):
    rule_id: InspectorRuleId
    severity: InspectorSeverity
    title: str
    diagnosis: str
    risk: str
    recommendation: str
    fixability: Fixability
    bay_id: str | None = None
    leaf_id: str | None = None
    fix: InspectorDiff | None = None


class RuleEvaluation(EngineModel):
    rule_id: InspectorRuleId
    status: RuleEvaluationStatus
    bay_id: str | None = None
    leaf_id: str | None = None


class InspectorResult(EngineModel):
    status: Literal["GREEN", "YELLOW", "RED"]
    production_allowed: bool
    evaluations: list[RuleEvaluation]
    findings: list[InspectorFinding]
    source_calculation_hash: str | None = None


class ExactRuleConfig(EngineModel):
    @field_validator("*", mode="before")
    @classmethod
    def exact_decimal_strings(cls, value: object) -> object:
        return Decimal(value) if isinstance(value, str) else value


class R01Config(ExactRuleConfig):
    pass


class R02Config(ExactRuleConfig):
    min_ratio: Decimal = Field(gt=Decimal("0"))
    max_ratio: Decimal = Field(gt=Decimal("0"))
    suggested_ratio: Decimal = Field(gt=Decimal("0"))


class R03Config(ExactRuleConfig):
    min_width_mm: Decimal = Field(gt=Decimal("0"))
    max_width_mm: Decimal = Field(gt=Decimal("0"))
    max_height_mm: Decimal = Field(gt=Decimal("0"))


class R04Config(ExactRuleConfig):
    monolithic_4_max_area_m2: Decimal = Field(gt=Decimal("0"))
    dvh_4_any_4_max_area_m2: Decimal = Field(gt=Decimal("0"))


class R05Config(ExactRuleConfig):
    span_trigger_mm: Decimal = Field(gt=Decimal("0"))


class R06Config(ExactRuleConfig):
    pass


class R07Config(ExactRuleConfig):
    width_trigger_mm: Decimal = Field(gt=Decimal("0"))
    required_bottom_drains: Decimal = Field(gt=Decimal("0"), multiple_of=1)


class R08Config(ExactRuleConfig):
    max_spacing_mm: Decimal = Field(gt=Decimal("0"))


class R09Config(ExactRuleConfig):
    white_limit_mm: Decimal = Field(gt=Decimal("0"))
    foiled_limit_mm: Decimal = Field(gt=Decimal("0"))


class R10Config(ExactRuleConfig):
    tolerance_mm: Decimal = Field(ge=Decimal("0"))


class R11Config(ExactRuleConfig):
    expected_mm: Decimal = Field(gt=Decimal("0"))
    tolerance_mm: Decimal = Field(ge=Decimal("0"))
    suggested_sash_overlap_mm: Decimal = Field(gt=Decimal("0"))


class R12Config(ExactRuleConfig):
    width_trigger_mm: Decimal = Field(gt=Decimal("0"))
    minimum_ix_cm4: Decimal = Field(gt=Decimal("0"))


class R13Config(ExactRuleConfig):
    height_trigger_mm: Decimal = Field(gt=Decimal("0"))
    required_stay_arms: Decimal = Field(gt=Decimal("0"), multiple_of=1)


class R14Config(ExactRuleConfig):
    weight_trigger_kg: Decimal = Field(gt=Decimal("0"))
    required_carriages: Decimal = Field(gt=Decimal("0"), multiple_of=1)
    minimum_capacity_kg: Decimal = Field(gt=Decimal("0"))


class InspectorConfig(EngineModel):
    R01: R01Config
    R02: R02Config
    R03: R03Config
    R04: R04Config
    R05: R05Config
    R06: R06Config
    R07: R07Config
    R08: R08Config
    R09: R09Config
    R10: R10Config
    R11: R11Config
    R12: R12Config
    R13: R13Config
    R14: R14Config


@dataclass(frozen=True)
class InspectorInput:
    computation: GeometryComputation
    chamber_clearance_mm: Decimal | None
    annotations: list[WorkshopAnnotations] = field(default_factory=list)
    structural_inputs: list[StructuralInput] = field(default_factory=list)
    reinforcement_ix_by_target: dict[str, Decimal | None] = field(default_factory=dict)
    mode: InspectionMode = InspectionMode.DESIGN
    source_calculation_hash: str | None = None
