"""Sourced accessory and service contracts; no guessed quantities or rates."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Code = Annotated[str, Field(min_length=1, max_length=80, pattern=r"^[A-Z0-9_+.-]+$")]
Side = Literal["TOP", "RIGHT", "BOTTOM", "LEFT"]


class ExtraModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", allow_inf_nan=False)

    @model_validator(mode="before")
    @classmethod
    def exact(cls, value: Any) -> Any:
        decimals = {"cost_rate", "selling_rate", "overhang_left_mm", "overhang_right_mm",
                    "default_overhang_mm", "opening_width_mm", "opening_height_mm",
                    "quantity", "width_mm", "height_mm", "total_cost", "total_price"}

        def visit(node: Any, key: str = "") -> Any:
            if isinstance(node, ExtraModel):
                return node
            if isinstance(node, dict):
                return {name: visit(child, name) for name, child in node.items()}
            if isinstance(node, (list, tuple)):
                return [visit(child) for child in node]
            if key in decimals and node is not None:
                if isinstance(node, bool) or not isinstance(node, (str, int, Decimal)):
                    raise ValueError("Los extras requieren decimales exactos.")
                return Decimal(node)
            return node

        return visit(value)


class ExtraRate(ExtraModel):
    cost_rate: Decimal = Field(ge=0)
    selling_rate: Decimal = Field(ge=0)

    @model_validator(mode="after")
    def covers_cost(self) -> ExtraRate:
        if self.selling_rate < self.cost_rate:
            raise ValueError("La tarifa de venta no puede ser menor que su costo declarado.")
        return self


class ExtraDefinition(ExtraRate):
    code: Code
    name: str = Field(min_length=1, max_length=150, pattern=r"\S")
    scope: Literal["POSITION", "PROJECT"]
    kind: Literal["PROFILE", "SCREEN", "FITTING", "SERVICE"]
    basis: Literal["SILL", "SIDES", "WINDOW", "LEAF", "AREA", "PERIMETER", "PER_POSITION", "FIXED", "ZONE"]
    unit: Literal["M", "M2", "EA"]
    currency: Literal["CLP", "USD"]
    source: str = Field(min_length=1, max_length=1000, pattern=r"\S")
    synthetic: bool
    # A profile resolves the effective article of this role, including its
    # cut, stock, reinforcement and finish authorities. Unit items are bought
    # to the exact dimensions in the BOM; they are never imaginary saw cuts.
    profile_role: Literal["SILL", "FRAME_EXTENSION", "COVER_TRIM", "ADDITIONAL"] | None = None
    sku: Code | None = None
    allowed_movements: list[str] = Field(default_factory=list, max_length=20)
    default_sides: list[Side] = Field(default_factory=list, max_length=4)
    default_overhang_mm: Decimal = Field(default=Decimal("0"), ge=0)
    suggestion: Literal["NONE", "WINDOW", "MOVING_LEAF", "OPENING_GAP"] = "NONE"
    replaces_handle: bool = False
    installation: bool = False
    zones: dict[str, ExtraRate] = Field(default_factory=dict)

    @model_validator(mode="after")
    def contract(self) -> ExtraDefinition:
        units = {"SILL": "M", "SIDES": "M", "WINDOW": "EA", "LEAF": "EA",
                 "AREA": "M2", "PERIMETER": "M", "PER_POSITION": "EA", "FIXED": "EA", "ZONE": "EA"}
        if self.unit != units[self.basis] or len(set(self.default_sides)) != len(self.default_sides):
            raise ValueError("La unidad debe corresponder a la regla y los lados no se repiten.")
        if self.kind == "PROFILE":
            if self.scope != "POSITION" or self.basis not in {"SILL", "SIDES"} or self.profile_role is None or self.sku:
                raise ValueError("El perfil requiere su rol y una regla de largo por posición.")
            if self.basis == "SIDES" and not self.default_sides:
                raise ValueError("Declara los lados del perfil.")
        elif self.profile_role is not None:
            raise ValueError("Solo un extra de perfil puede declarar rol de corte.")
        if self.kind in {"SCREEN", "FITTING"} and (self.scope != "POSITION" or self.basis not in {"WINDOW", "LEAF"} or self.sku is None):
            raise ValueError("El accesorio requiere un artículo por vano u hoja.")
        if self.scope == "PROJECT" and (self.kind != "SERVICE" or self.basis in {"SILL", "SIDES", "WINDOW", "LEAF"}):
            raise ValueError("El servicio del proyecto requiere una regla de cantidad del proyecto.")
        if self.kind == "SERVICE" and self.basis not in {"AREA", "PERIMETER", "PER_POSITION", "FIXED", "ZONE"}:
            raise ValueError("El servicio requiere una regla de área, perímetro, cantidad o zona.")
        if self.replaces_handle and (self.kind != "FITTING" or self.basis != "LEAF"):
            raise ValueError("La manilla especial reemplaza una manilla por hoja.")
        if (self.basis == "ZONE") != bool(self.zones):
            raise ValueError("El flete por zona requiere tarifas declaradas por zona.")
        if self.installation and self.kind != "SERVICE":
            raise ValueError("La instalación es un servicio.")
        return self


class ExtraSelection(ExtraModel):
    code: Code
    decision: Literal["ACCEPT", "DISMISS"] = "ACCEPT"
    bay_id: str | None = None
    leaf_id: str | None = None
    sides: list[Side] | None = Field(default=None, max_length=4)
    overhang_left_mm: Decimal = Field(default=Decimal("0"), ge=0)
    overhang_right_mm: Decimal = Field(default=Decimal("0"), ge=0)
    zone: str | None = None

    @model_validator(mode="after")
    def unique_sides(self) -> ExtraSelection:
        if (self.sides is not None and len(self.sides) != len(set(self.sides))) or self.leaf_id is not None and self.bay_id is None:
            raise ValueError("No repitas lados y declara el vano de la hoja.")
        return self


class ExtraContext(ExtraModel):
    opening_width_mm: Decimal | None = Field(default=None, gt=0)
    opening_height_mm: Decimal | None = Field(default=None, gt=0)


class ExtraAuthority(ExtraModel):
    schema_version: Literal[1]
    definitions: list[ExtraDefinition] = Field(max_length=100)
    source: str = Field(min_length=1, pattern=r"\S")

    @model_validator(mode="after")
    def unique_codes(self) -> ExtraAuthority:
        if len({item.code for item in self.definitions}) != len(self.definitions):
            raise ValueError("La autoridad repite un extra.")
        return self


class ExtraPolicy(ExtraModel):
    schema_version: Literal[1] = 1
    services: list[ExtraDefinition] = Field(default_factory=list, max_length=100)
    position_defaults: list[ExtraSelection] = Field(default_factory=list, max_length=30)
    document_prices: Literal["ITEMIZED", "GROUPED"] = "ITEMIZED"

    @model_validator(mode="after")
    def service_policy(self) -> ExtraPolicy:
        if any(item.kind != "SERVICE" for item in self.services):
            raise ValueError("Los servicios de organización no pueden fabricar artículos técnicos.")
        ExtraAuthority(schema_version=1, definitions=self.services, source="Organización")
        if len({item.code for item in self.position_defaults}) != len(self.position_defaults):
            raise ValueError("La plantilla no puede repetir un extra.")
        return self


class ExtraFact(ExtraModel):
    code: str
    name: str
    scope: Literal["POSITION", "PROJECT"]
    kind: Literal["PROFILE", "SCREEN", "FITTING", "SERVICE"]
    quantity: Decimal = Field(gt=0)
    unit: Literal["M", "M2", "EA"]
    source: str
    synthetic: bool
    width_mm: Decimal | None = None
    height_mm: Decimal | None = None
    bay_id: str | None = None
    leaf_id: str | None = None
    sku: str | None = None
    installation: bool
    zone: str | None = None


class ExtraLine(ExtraFact):
    cost_rate: Decimal = Field(ge=0)
    selling_rate: Decimal = Field(ge=0)
    total_cost: Decimal = Field(ge=0)
    total_price: Decimal = Field(ge=0)
    currency: Literal["CLP", "USD"]

    def fact(self) -> ExtraFact:
        return ExtraFact.model_validate({key: getattr(self, key) for key in ExtraFact.model_fields})


class ExtraSuggestion(ExtraModel):
    selection: ExtraSelection
    name: str
    cause: str
    source: str
