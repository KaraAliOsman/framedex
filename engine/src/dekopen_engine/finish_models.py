"""Exact, sourced finish authority shared by catalog, BOM and renderers."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Code = Annotated[str, Field(min_length=1, max_length=50, pattern=r"^[A-Z0-9_+.-]+$")]
Channel = Annotated[Decimal, Field(ge=0, le=1)]


class FinishModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", allow_inf_nan=False)

    @model_validator(mode="before")
    @classmethod
    def exact_input(cls, value: Any) -> Any:
        decimal_fields = {"gloss", "amount", "glass_clearance_mm", "max_position_width_mm",
            "max_position_height_mm", "max_leaf_width_mm", "max_leaf_height_mm"}
        def check(node: Any, key: str = "") -> Any:
            if isinstance(node, FinishModel):
                return node
            if node is not None and not isinstance(node, (str, int, Decimal, dict, list, tuple)):
                raise ValueError("Los colores, las medidas y los recargos requieren decimales exactos.")
            if isinstance(node, dict):
                return {name: check(child, name) for name, child in node.items()}
            elif isinstance(node, (list, tuple)):
                return [check(child, "gloss" if key == "linear_rgb" else "") for child in node]
            if key in decimal_fields and node is not None:
                if isinstance(node, bool) or not isinstance(node, (str, int, Decimal)):
                    raise ValueError("El dato técnico requiere un decimal exacto.")
                return Decimal(node)
            return node
        return check(value)


class FinishColor(FinishModel):
    code: Code
    manufacturer_code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=150)
    kind: Literal["MASS", "FOIL", "COEXTRUDED", "RAL", "ANODIZED", "WOOD_EFFECT"]
    linear_rgb: list[Channel] = Field(min_length=3, max_length=3)
    gloss: Decimal | None = Field(ge=0, le=1)
    texture_path: str | None = Field(default=None, max_length=500, pattern=r"^/catalog-assets/[A-Za-z0-9_./-]+$")
    approximate: bool
    source: str = Field(min_length=1, pattern=r"\S")
    synthetic: bool

    @model_validator(mode="after")
    def local_texture(self) -> FinishColor:
        if self.texture_path and ".." in self.texture_path.split("/"):
            raise ValueError("La textura debe ser un recurso local del catálogo.")
        return self


class FinishSurcharge(FinishModel):
    kind: Literal["NONE", "PER_M", "PERCENT", "FIXED"]
    amount: Decimal = Field(ge=0)
    currency: Literal["CLP", "USD", "UF"]
    source: str = Field(min_length=1, pattern=r"\S")

    @model_validator(mode="after")
    def declared_zero(self) -> FinishSurcharge:
        if self.kind == "NONE" and self.amount != 0:
            raise ValueError("Un acabado sin recargo debe declarar importe cero.")
        return self


class FinishCombination(FinishModel):
    code: Code
    interior: Code
    exterior: Code
    base: Code | None
    reinforcement_required: bool
    reinforcement_stock_code: Code
    glass_clearance_mm: Decimal = Field(ge=0)
    max_position_width_mm: Decimal | None = Field(default=None, gt=0)
    max_position_height_mm: Decimal | None = Field(default=None, gt=0)
    max_leaf_width_mm: Decimal | None = Field(default=None, gt=0)
    max_leaf_height_mm: Decimal | None = Field(default=None, gt=0)
    extra_lead_days: int | None = Field(ge=0)
    surcharge: FinishSurcharge
    allowed_handle_colors: list[Code] = Field(default_factory=list)
    source: str = Field(min_length=1, pattern=r"\S")
    synthetic: bool


class FinishAuthority(FinishModel):
    schema_version: Literal[1]
    material: Literal["PVC", "ALUMINIUM"]
    colors: list[FinishColor] = Field(min_length=1, max_length=200)
    handle_colors: list[FinishColor] = Field(default_factory=list, max_length=50)
    combinations: list[FinishCombination] = Field(min_length=1, max_length=500)
    source: str = Field(min_length=1, pattern=r"\S")

    @model_validator(mode="after")
    def references(self) -> FinishAuthority:
        colors = {color.code: color for color in self.colors}
        if len(colors) != len(self.colors):
            raise ValueError("La carta repite un código de color.")
        if len({color.code for color in self.handle_colors}) != len(self.handle_colors):
            raise ValueError("La carta repite un color de manilla.")
        pairs: set[tuple[str, str]] = set()
        codes: set[str] = set()
        for color in self.colors:
            allowed = {"MASS", "FOIL", "COEXTRUDED"} if self.material == "PVC" else {"RAL", "ANODIZED", "WOOD_EFFECT"}
            if color.kind not in allowed:
                raise ValueError("El proceso de color no corresponde al material del sistema.")
        for combo in self.combinations:
            if combo.code in codes or (combo.interior, combo.exterior) in pairs:
                raise ValueError("La carta repite una combinación o su identidad de stock.")
            codes.add(combo.code)
            pairs.add((combo.interior, combo.exterior))
            if self.handle_colors and not set(combo.allowed_handle_colors).issubset({color.code for color in self.handle_colors}):
                raise ValueError("La combinación admite una manilla sin muestra declarada en la carta.")
            if combo.interior not in colors or combo.exterior not in colors:
                raise ValueError("La combinación referencia un color ausente de la carta.")
            if self.material == "PVC":
                if combo.base not in colors or colors[combo.base].kind != "MASS":
                    raise ValueError("La combinación PVC debe declarar su color de masa.")
                for face in (combo.interior, combo.exterior):
                    if colors[face].kind == "MASS" and face != combo.base:
                        raise ValueError("Una cara de masa debe coincidir con la base PVC.")
            elif combo.base is not None:
                raise ValueError("El aluminio no declara una base de masa PVC.")
        return self


class ResolvedFinish(FinishModel):
    combination: FinishCombination
    interior: FinishColor
    exterior: FinishColor
    base: FinishColor | None
    profile_skus: dict[str, str]
    handle_colors: list[FinishColor] = Field(default_factory=list)
