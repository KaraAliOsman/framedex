"""Opening survey to fabrication dimensions, using explicit sourced allowances."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from dekopen_engine.extra_models import ExtraAuthority, ExtraSelection


class MountingModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", allow_inf_nan=False)

    @model_validator(mode="before")
    @classmethod
    def exact(cls, value: Any) -> Any:
        def visit(node: Any, key: str = "") -> Any:
            if isinstance(node, BaseModel):
                return node
            if isinstance(node, dict):
                return {name: visit(child, name) for name, child in node.items()}
            if isinstance(node, list):
                return [visit(child, key) for child in node]
            if key.endswith("_mm") and node is not None:
                if isinstance(node, bool) or not isinstance(node, (str, int, Decimal)):
                    raise ValueError("Las medidas requieren decimales exactos.")
                try:
                    exact = Decimal(node)
                    if not exact.is_finite() or exact != exact.quantize(Decimal("0.01")):
                        raise ValueError("Las medidas requieren precisión de 0,01 mm.")
                    return exact
                except InvalidOperation as error:
                    raise ValueError("Las medidas requieren decimales finitos de 0,01 mm.") from error
            return node
        return visit(value)


class Allowance(MountingModel):
    clearance_mm: Decimal = Field(ge=0)
    frame_mm: Decimal = Field(ge=0)
    extension_mm: Decimal = Field(ge=0)
    overlap_mm: Decimal = Field(ge=0)

    @property
    def adjustment(self) -> Decimal:
        return self.overlap_mm - self.clearance_mm - self.frame_mm - self.extension_mm


class MountingRule(MountingModel):
    code: str = Field(min_length=1, max_length=80, pattern=r"^[A-Z0-9_.-]+$")
    name: str = Field(min_length=1, max_length=150, pattern=r"\S")
    kind: Literal["IN_OPENING", "SUBFRAME", "OVERLAP", "RENOVATION"]
    source: str = Field(min_length=1, max_length=1000, pattern=r"\S")
    synthetic: bool
    tolerance_mm: Decimal = Field(ge=0)
    left: Allowance
    right: Allowance
    top: Allowance
    bottom: Allowance
    extras: list[ExtraSelection] = Field(max_length=40)

    @model_validator(mode="after")
    def accepted_extras(self) -> MountingRule:
        if any(item.decision != "ACCEPT" for item in self.extras):
            raise ValueError("Los accesorios exigidos por montaje deben estar aceptados.")
        if len({item.code for item in self.extras}) != len(self.extras):
            raise ValueError("No repitas accesorios de montaje.")
        return self


class FabricationOverride(MountingModel):
    width_mm: Decimal = Field(gt=0)
    height_mm: Decimal = Field(gt=0)
    reason: str = Field(min_length=1, max_length=1000, pattern=r"\S")


class OpeningSurvey(MountingModel):
    module_id: str | None = None
    rule_code: str = Field(min_length=1, max_length=80)
    rule_revision: int = Field(ge=1)
    widths_mm: list[Decimal] = Field(min_length=1, max_length=3)
    heights_mm: list[Decimal] = Field(min_length=1, max_length=3)
    wall: Literal["MASONRY", "CONCRETE", "PARTITION", "WOOD"]
    squareness_mm: Decimal | None = Field(default=None, ge=0)
    plumb_mm: Decimal | None = Field(default=None, ge=0)
    origin: Literal["CUSTOMER", "SITE"]
    override: FabricationOverride | None = None

    @model_validator(mode="after")
    def sample_contract(self) -> OpeningSurvey:
        for samples in (self.widths_mm, self.heights_mm):
            if len(samples) not in (1, 3) or any(item <= 0 for item in samples):
                raise ValueError("Ingresa una o tres medidas positivas por eje.")
        return self


class AxisDerivation(MountingModel):
    opening_mm: Decimal
    spread_mm: Decimal
    first: Allowance
    second: Allowance
    first_adjustment_mm: Decimal
    second_adjustment_mm: Decimal
    derived_mm: Decimal
    fabrication_mm: Decimal
    deviation_mm: Decimal


class MountingResult(MountingModel):
    width: AxisDerivation
    height: AxisDerivation
    warnings: list[str]


def derive_fabrication(survey: OpeningSurvey, rule: MountingRule) -> MountingResult:
    if survey.rule_code != rule.code:
        raise ValueError("La regla de montaje no coincide con la medición.")
    warnings: list[str] = []

    def axis(samples: list[Decimal], first: Allowance, second: Allowance,
             override: Decimal | None, label: str) -> AxisDerivation:
        opening = min(samples)
        spread = max(samples) - opening
        derived = opening + first.adjustment + second.adjustment
        if derived <= 0:
            raise ValueError("El montaje deja una medida de fabricación no positiva.")
        fabrication = derived if override is None else override
        deviation = fabrication - derived
        if spread > rule.tolerance_mm:
            warnings.append(f"{label}: la dispersión supera la tolerancia declarada.")
        if abs(deviation) > rule.tolerance_mm:
            warnings.append(f"{label}: la fijación manual no es coherente con el vano y el montaje.")
        return AxisDerivation(opening_mm=opening, spread_mm=spread, first=first, second=second,
                              first_adjustment_mm=first.adjustment, second_adjustment_mm=second.adjustment,
                              derived_mm=derived, fabrication_mm=fabrication, deviation_mm=deviation)

    width = axis(survey.widths_mm, rule.left, rule.right,
                 survey.override.width_mm if survey.override else None, "Ancho")
    height = axis(survey.heights_mm, rule.bottom, rule.top,
                  survey.override.height_mm if survey.override else None, "Alto")
    if survey.squareness_mm is not None and survey.squareness_mm > rule.tolerance_mm:
        warnings.append("La escuadra supera la tolerancia declarada.")
    if survey.plumb_mm is not None and survey.plumb_mm > rule.tolerance_mm:
        warnings.append("El desplome supera la tolerancia declarada.")
    return MountingResult(width=width, height=height, warnings=warnings)


def validate_mounting_extras(rule: MountingRule, authority: ExtraAuthority | None) -> None:
    """An explicit extension deduction needs physical accessories on those sides."""
    definitions = {item.code: item for item in authority.definitions} if authority else {}
    covered: set[str] = set()
    for selection in rule.extras:
        definition = definitions.get(selection.code)
        if definition is None or definition.scope != "POSITION":
            raise ValueError("Declara los ensanches y fijaciones en el catálogo de esta serie.")
        if selection.bay_id is not None or selection.leaf_id is not None:
            raise ValueError("Los accesorios de montaje corresponden al marco completo.")
        if definition.profile_role == "FRAME_EXTENSION":
            sides = selection.sides if selection.sides is not None else definition.default_sides
            if not sides or any(side not in definition.default_sides for side in sides):
                raise ValueError("El ensanche requiere lados compatibles con su ficha de catálogo.")
            covered.update(sides)
    for side in ("LEFT", "RIGHT", "TOP", "BOTTOM"):
        if getattr(rule, side.lower()).extension_mm > 0 and side not in covered:
            raise ValueError("Cada deducción de ensanche requiere un perfil de ensanche en ese lado.")


def resize_contour(contour: dict[str, Any], old_width: Decimal, old_height: Decimal,
                   width: Decimal, height: Decimal) -> dict[str, Any]:
    """Preserve the editor's proportional contour intent at the mm quantum."""
    quantum = Decimal("0.01")
    return {"vertices": [{"x_mm": str((Decimal(str(point["x_mm"])) * width / old_width).quantize(quantum)),
                          "y_mm": str((Decimal(str(point["y_mm"])) * height / old_height).quantize(quantum))}
                         for point in contour["vertices"]],
            "bulges": [None if value is None else str((Decimal(str(value)) * height / old_height).quantize(quantum))
                       for value in contour["bulges"]]}
