"""Source-backed glass recipes, safety, billing and supplier instructions.

Exterior is first. Unknown chambers/interlayers remain unknown; neither a
thermal rating nor a safety certification can be inferred from a trade name.
"""

from __future__ import annotations

from decimal import Decimal
import re
from typing import Literal, TYPE_CHECKING, Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator

D = Decimal

if TYPE_CHECKING:
    from dekopen_engine.models import PlanPoint


class GlassModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", allow_inf_nan=False)


GlassType = Literal["FLOAT", "TEMPERED", "HEAT_STRENGTHENED", "LOW_E", "SOLAR",
                    "REFLECTIVE", "MIRROR", "SATIN", "PRINTED"]


class GlassPly(GlassModel):
    thickness_mm: Decimal = Field(gt=0)
    type: GlassType = "FLOAT"
    color: Literal["CLEAR", "BRONZE", "GREY", "GREEN"] = "CLEAR"
    coating_face: int | None = Field(default=None, ge=1, le=12)
    supplier_sku: str | None = None


class GlassInterlayer(GlassModel):
    thickness_mm: Decimal | None = Field(default=None, gt=0)
    type: Literal["PVB", "ACOUSTIC_PVB"] = "PVB"
    # PVB mass authority is an explicitly declared material density. The
    # synthetic fixture declares 1070; an acoustic supplier may differ.
    density_kg_m3: Decimal | None = Field(default=None, gt=0)
    source: str | None = None

    @model_validator(mode="after")
    def density_has_source(self) -> GlassInterlayer:
        if self.density_kg_m3 is not None and not self.source:
            raise ValueError("La densidad del PVB necesita una fuente.")
        return self


class GlassPane(GlassModel):
    kind: Literal["PANE"] = "PANE"
    plies: tuple[GlassPly, ...] = Field(min_length=1, max_length=6)
    interlayers: tuple[GlassInterlayer, ...] = ()

    @model_validator(mode="after")
    def laminate(self) -> GlassPane:
        if len(self.interlayers) != len(self.plies) - 1:
            raise ValueError("Cada unión de láminas necesita su interlámina.")
        return self


class GlassChamber(GlassModel):
    kind: Literal["CHAMBER"] = "CHAMBER"
    width_mm: Decimal = Field(gt=0)
    spacer: Literal["ALUMINIUM", "WARM_EDGE"] | None = None
    gas: Literal["AIR", "ARGON"] | None = None
    sealant: str | None = None


class GlassComposition(GlassModel):
    layers: tuple[GlassPane | GlassChamber, ...] = Field(min_length=1, max_length=11)

    @model_validator(mode="after")
    def alternating(self) -> GlassComposition:
        if len(self.layers) % 2 != 1 or any(
            not isinstance(layer, GlassPane if index % 2 == 0 else GlassChamber)
            for index, layer in enumerate(self.layers)
        ):
            raise ValueError("Ordena lámina, cámara y lámina desde el exterior.")
        faces = sum(len(layer.plies) * 2 for layer in self.layers if isinstance(layer, GlassPane))
        if any(ply.coating_face is not None and ply.coating_face > faces
               for layer in self.layers if isinstance(layer, GlassPane) for ply in layer.plies):
            raise ValueError("La cara de la capa no existe en esta composición.")
        return self


class SupplierValue(GlassModel):
    value: Decimal = Field(ge=0)
    source: str = Field(min_length=1)


class SupplierSafety(GlassModel):
    value: Literal["A", "B", "C"]
    source: str = Field(min_length=1)


class GlassProperties(GlassModel):
    ug: SupplierValue | None = None
    solar_factor: SupplierValue | None = None
    light_transmittance: SupplierValue | None = None
    safety_class: SupplierSafety | None = None
    weight_kg_m2: SupplierValue | None = None

    @model_validator(mode="after")
    def fractions(self) -> GlassProperties:
        if any(datum is not None and datum.value <= 0 for datum in (self.ug, self.weight_kg_m2)):
            raise ValueError("Ug y peso declarado deben ser positivos.")
        for value in (self.solar_factor, self.light_transmittance):
            if value is not None and value.value > 1:
                raise ValueError("El factor solar y la transmisión se declaran entre 0 y 1.")
        return self


class GlassLimits(GlassModel):
    min_width_mm: Decimal | None = Field(default=None, gt=0)
    max_width_mm: Decimal | None = Field(default=None, gt=0)
    min_height_mm: Decimal | None = Field(default=None, gt=0)
    max_height_mm: Decimal | None = Field(default=None, gt=0)
    max_area_m2: Decimal | None = Field(default=None, gt=0)
    max_aspect_ratio: Decimal | None = Field(default=None, ge=1)
    source: str | None = None

    @model_validator(mode="after")
    def source_and_order(self) -> GlassLimits:
        if any(value is not None for key, value in self.model_dump().items() if key != "source") and not self.source:
            raise ValueError("Los límites del vidrio necesitan una fuente.")
        for low, high in ((self.min_width_mm, self.max_width_mm), (self.min_height_mm, self.max_height_mm)):
            if low is not None and high is not None and low > high:
                raise ValueError("El mínimo no puede superar el máximo.")
        return self


class GlassBilling(GlassModel):
    minimum_area_m2: Decimal = Field(default=D("0"), ge=0)
    tempering_sku: str | None = None
    polishing_sku: str | None = None
    drilling_sku: str | None = None
    bars_per_m_sku: str | None = None
    bars_per_crossing_sku: str | None = None
    source: str | None = None

    @model_validator(mode="after")
    def minimum_has_source(self) -> GlassBilling:
        if (self.minimum_area_m2 or any(self.model_dump().get(key) for key in (
            "tempering_sku", "polishing_sku", "drilling_sku", "bars_per_m_sku", "bars_per_crossing_sku"
        ))) and not self.source:
            raise ValueError("El área mínima y los recargos necesitan una fuente.")
        return self


class GlassProduct(GlassModel):
    authority_id: str | None = None
    name: str = Field(min_length=1)
    composition: GlassComposition
    source: str = Field(min_length=1)
    synthetic: bool = False
    properties: GlassProperties = Field(default_factory=GlassProperties)
    limits: GlassLimits = Field(default_factory=GlassLimits)
    billing: GlassBilling = Field(default_factory=GlassBilling)


class GlassProcessing(GlassModel):
    polished_edges: tuple[Literal["TOP", "BOTTOM", "LEFT", "RIGHT"], ...] = ()
    holes: int = Field(default=0, ge=0, le=200)
    # Rectangular grid: vertical/horizontal bars between panes.
    bars_vertical: int = Field(default=0, ge=0, le=50)
    bars_horizontal: int = Field(default=0, ge=0, le=50)

    @model_validator(mode="after")
    def unique_edges(self) -> GlassProcessing:
        if len(set(self.polished_edges)) != len(self.polished_edges):
            raise ValueError("No repitas un canto de pulido.")
        return self


class GlassSafetyRule(GlassModel):
    code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    zone: Literal["DOOR", "SIDELIGHT", "LOW_PANE", "LARGE_PANE"]
    maximum_sill_mm: Decimal | None = Field(default=None, ge=0)
    minimum_area_m2: Decimal | None = Field(default=None, gt=0)
    required_classes: tuple[Literal["A", "B", "C"], ...] = ("A", "B", "C")
    mandatory: bool = False
    synthetic: bool = False
    source: str = Field(min_length=1)

    @model_validator(mode="after")
    def complete(self) -> GlassSafetyRule:
        if self.zone == "LOW_PANE" and self.maximum_sill_mm is None:
            raise ValueError("La regla de paño bajo necesita su altura de antepecho.")
        if self.zone == "LARGE_PANE" and self.minimum_area_m2 is None:
            raise ValueError("La regla de gran ventanal necesita su área de referencia.")
        if not self.required_classes:
            raise ValueError("Declara las clases de seguridad aceptadas.")
        return self


class GlassAssessment(GlassModel):
    code: str
    message: str
    source: str | None = None
    blocking: bool = False
    synthetic: bool = False


_NUMBER = r"\d+(?:[.,]\d+)?"
_PLY = re.compile(rf"^({_NUMBER})\s*(.*)$", re.I)
_TYPES: dict[str, GlassType] = {
    "float": "FLOAT", "incoloro": "FLOAT", "templado": "TEMPERED",
    "termoendurecido": "HEAT_STRENGTHENED", "low-e": "LOW_E", "low e": "LOW_E",
    "control solar": "SOLAR", "reflectivo": "REFLECTIVE", "espejo": "MIRROR",
    "satinado": "SATIN", "arenado": "SATIN", "impreso": "PRINTED",
}
_COLORS = {"bronce": "BRONZE", "gris": "GREY", "verde": "GREEN"}
_TYPE_LABELS = {"FLOAT": "", "TEMPERED": "templado", "HEAT_STRENGTHENED": "termoendurecido",
    "LOW_E": "Low-E", "SOLAR": "control solar", "REFLECTIVE": "reflectivo", "MIRROR": "espejo",
    "SATIN": "satinado", "PRINTED": "impreso"}


def _number(text: str) -> Decimal:
    value = D(text.replace(",", "."))
    if value <= 0:
        raise ValueError("Los espesores deben ser positivos.")
    return value


def _pane(text: str) -> GlassPane:
    # A group-wide treatment ("3+3 templado") applies to each ply. Per-ply
    # treatments and supplier SKUs also round-trip through the formatter.
    detailed = re.search(r"\[([^\[\]]+)\]", text)
    detailed_interlayers = None
    if detailed:
        detailed_interlayers = []
        for token in detailed.group(1).split(";"):
            match = re.fullmatch(rf"\s*PVB(\s+ac[uú]stico)?\s+({_NUMBER}|\?)\s*", token, re.I)
            if not match:
                raise ValueError("Revisa cada interlámina de la composición.")
            detailed_interlayers.append(GlassInterlayer(type="ACOUSTIC_PVB" if match.group(1) else "PVB",
                thickness_mm=None if match.group(2) == "?" else _number(match.group(2))))
        text = text[:detailed.start()] + text[detailed.end():]
    interlayer_match = re.search(rf"\bPVB(?:\s+ac[uú]stico)?(?:\s+({_NUMBER}|\?))?", text, re.I)
    interlayer: GlassInterlayer | None = None
    if interlayer_match:
        thickness = interlayer_match.group(1)
        interlayer = GlassInterlayer(
            thickness_mm=_number(thickness) if thickness and thickness != "?" else None,
            type="ACOUSTIC_PVB" if re.search(r"ac[uú]stico", interlayer_match.group(0), re.I) else "PVB",
        )
        text = text[:interlayer_match.start()] + text[interlayer_match.end():]
    text = re.sub(r"\blaminado\b", "", text, flags=re.I).strip()
    parts = [part.strip() for part in text.split("+")]
    group_suffix = ""
    if len(parts) > 1 and all(re.fullmatch(_NUMBER, part) for part in parts[:-1]):
        last = _PLY.fullmatch(parts[-1])
        if last:
            group_suffix = last.group(2)
    plies = []
    for part in parts:
        match = _PLY.fullmatch(part)
        if not match:
            raise ValueError("No se reconoce una lámina de la composición.")
        original_suffix = (match.group(2) or group_suffix).strip()
        suffix = original_suffix.lower()
        sku_match = re.search(r"\{([^{}]+)\}", original_suffix)
        sku = sku_match.group(1) if sku_match else None
        if sku_match:
            suffix = suffix[:sku_match.start()] + suffix[sku_match.end():]
        face_match = re.search(r"\(\s*c(?:ara)?\s*(\d+)\s*\)", suffix)
        face = int(face_match.group(1)) if face_match else None
        if face_match:
            suffix = suffix[:face_match.start()] + suffix[face_match.end():]
        color: Literal["CLEAR", "BRONZE", "GREY", "GREEN"] = "CLEAR"
        for token, code in _COLORS.items():
            if re.search(rf"\b{token}\b", suffix):
                color = code  # type: ignore[assignment]
                suffix = re.sub(rf"\b{token}\b", "", suffix).strip()
                break
        suffix = " ".join(suffix.split())
        if suffix in ("float incoloro", "incoloro float"):
            suffix = "float"
        kind = _TYPES.get(suffix) if suffix else "FLOAT"
        if kind is None:
            raise ValueError("El tratamiento de esta lámina necesita revisión.")
        plies.append(GlassPly(thickness_mm=_number(match.group(1)), type=kind,
                             color=color, coating_face=face, supplier_sku=sku))
    return GlassPane(plies=tuple(plies), interlayers=tuple(detailed_interlayers) if detailed_interlayers is not None else tuple(
        (interlayer or GlassInterlayer()).model_copy() for _ in range(len(plies) - 1)
    ))


def _chamber(text: str) -> GlassChamber:
    match = _PLY.fullmatch(text.strip())
    if not match:
        raise ValueError("No se reconoce el ancho de la cámara.")
    suffix = match.group(2).strip()
    gas: Literal["AIR", "ARGON"] | None = None
    spacer: Literal["ALUMINIUM", "WARM_EDGE"] | None = None
    sealant = None
    seal = re.search(r"sellante\s*\{([^{}]+)\}", suffix, re.I)
    if seal:
        sealant = seal.group(1)
        suffix = suffix[:seal.start()] + suffix[seal.end():]
    suffix = suffix.lower()
    for pattern, value in ((r"\baire\b", "AIR"), (r"\b(?:ar|arg[oó]n)\b", "ARGON")):
        if re.search(pattern, suffix):
            gas = value  # type: ignore[assignment]
            suffix = re.sub(pattern, "", suffix)
    for pattern, value in ((r"\baluminio\b", "ALUMINIUM"), (r"\bborde c[aá]lido\b", "WARM_EDGE")):
        if re.search(pattern, suffix):
            spacer = value  # type: ignore[assignment]
            suffix = re.sub(pattern, "", suffix)
    if suffix.strip():
        raise ValueError("El gas o separador necesita revisión.")
    return GlassChamber(width_mm=_number(match.group(1)), gas=gas, spacer=spacer, sealant=sealant)


def parse_glass_notation(notation: str) -> GlassComposition:
    text = re.sub(r"^\s*(?:DVH|TVH|termopanel)\s*", "", notation.strip(), flags=re.I)
    # Hyphens between numbers are legacy chamber separators; Low-E survives.
    text = re.sub(r"(?<=[\d])\s*-\s*(?=\d)", " / ", text)
    parts = [part.strip() for part in text.split("/")]
    if not parts or len(parts) % 2 != 1 or any(not part for part in parts):
        raise ValueError("La composición debe alternar lámina y cámara.")
    return GlassComposition(layers=tuple(
        _pane(part) if index % 2 == 0 else _chamber(part) for index, part in enumerate(parts)
    ))


def _format_number(value: Decimal) -> str:
    exact = format(value, "f")
    return (exact.rstrip("0").rstrip(".") if "." in exact else exact).replace(".", ",")


def format_glass_notation(composition: GlassComposition) -> str:
    parts = []
    for layer in composition.layers:
        if isinstance(layer, GlassChamber):
            gas = {"AIR": "aire", "ARGON": "Ar"}.get(layer.gas or "", "")
            spacer = {"ALUMINIUM": "aluminio", "WARM_EDGE": "borde cálido"}.get(layer.spacer or "", "")
            seal = f"sellante {{{layer.sealant}}}" if layer.sealant else ""
            parts.append(" ".join(part for part in (_format_number(layer.width_mm), gas, spacer, seal) if part))
        else:
            plies = []
            for ply in layer.plies:
                color = {"BRONZE": "bronce", "GREY": "gris", "GREEN": "verde"}.get(ply.color, "")
                face = f"(c{ply.coating_face})" if ply.coating_face is not None else ""
                sku = f"{{{ply.supplier_sku}}}" if ply.supplier_sku else ""
                plies.append(" ".join(part for part in (_format_number(ply.thickness_mm),
                    _TYPE_LABELS[ply.type], color, face, sku) if part))
            part = " + ".join(plies)
            # Notation can express homogeneous interlayers. Heterogeneous
            # supplier recipes keep their full JSON as the purchase authority.
            if layer.interlayers:
                def pvb_notation(interlayer: GlassInterlayer) -> str:
                    acoustic = " acústico" if interlayer.type == "ACOUSTIC_PVB" else ""
                    return f"PVB{acoustic} " + (_format_number(interlayer.thickness_mm).replace(".", ",")
                        if interlayer.thickness_mm is not None else "?")
                if len({(value.type, value.thickness_mm) for value in layer.interlayers}) != 1:
                    part += " [" + "; ".join(pvb_notation(value) for value in layer.interlayers) + "]"
                else:
                    part += " " + pvb_notation(layer.interlayers[0])
            parts.append(part)
    return " / ".join(parts)


def net_glass_thickness(composition: GlassComposition) -> Decimal:
    return sum((ply.thickness_mm for layer in composition.layers if isinstance(layer, GlassPane)
                for ply in layer.plies), D("0"))


def total_glass_thickness(composition: GlassComposition) -> Decimal | None:
    total = net_glass_thickness(composition)
    for layer in composition.layers:
        if isinstance(layer, GlassChamber):
            total += layer.width_mm
        else:
            for value in layer.interlayers:
                if value.thickness_mm is None:
                    return None
                total += value.thickness_mm
    return total


def glass_mass_per_m2(product: GlassProduct) -> Decimal | None:
    if product.properties.weight_kg_m2 is not None:
        return product.properties.weight_kg_m2.value
    mass = net_glass_thickness(product.composition) * D("2.50")
    for layer in product.composition.layers:
        if isinstance(layer, GlassPane):
            for value in layer.interlayers:
                if value.thickness_mm is None or value.density_kg_m3 is None:
                    return None
                mass += value.thickness_mm * value.density_kg_m3 / D("1000")
    return mass


def assess_glass_safety(*, safety_class: SupplierSafety | None, synthetic: bool,
                       width_mm: Decimal, height_mm: Decimal,
                       rules: tuple[GlassSafetyRule, ...], door: bool = False,
                       sidelight: bool = False, sill_mm: Decimal | None = None
                       ) -> tuple[GlassAssessment, ...]:
    """Safety applies to legacy writes too; notation never certifies a class."""
    if min(width_mm, height_mm) <= 0:
        raise ValueError("Las medidas de corte del vidrio deben ser positivas.")
    area = width_mm * height_mm / D("1000000")
    findings = []
    for rule in rules:
        safety_supported = (safety_class is not None
            and safety_class.value in rule.required_classes
            and (not synthetic or rule.synthetic))
        if rule.zone == "LOW_PANE" and sill_mm is None and not safety_supported:
            findings.append(GlassAssessment(code=rule.code + "_height_unknown",
                message="Sin dato · declara la altura del paño sobre el piso para revisar su seguridad.",
                source=rule.source, blocking=rule.mandatory, synthetic=rule.synthetic))
        applies = ((rule.zone == "DOOR" and door) or (rule.zone == "SIDELIGHT" and sidelight)
            or (rule.zone == "LOW_PANE" and sill_mm is not None and rule.maximum_sill_mm is not None and sill_mm < rule.maximum_sill_mm)
            or (rule.zone == "LARGE_PANE" and rule.minimum_area_m2 is not None and area >= rule.minimum_area_m2))
        if applies and not safety_supported:
            findings.append(GlassAssessment(code=rule.code, message=f"{rule.name} · elige un vidrio con clase de seguridad respaldada por su proveedor.",
                source=rule.source, blocking=rule.mandatory, synthetic=rule.synthetic))
    return tuple(findings)


def assess_glass(product: GlassProduct, *, width_mm: Decimal, height_mm: Decimal,
                 bead_thicknesses: tuple[Decimal, ...], rules: tuple[GlassSafetyRule, ...] = (),
                 door: bool = False, sidelight: bool = False, sill_mm: Decimal | None = None,
                 leaf_weight_kg: Decimal | None = None, hardware_limit_kg: Decimal | None = None
                 ) -> tuple[GlassAssessment, ...]:
    if min(width_mm, height_mm) <= 0:
        raise ValueError("Las medidas de corte del vidrio deben ser positivas.")
    findings = []
    thickness = total_glass_thickness(product.composition)
    if thickness is None:
        findings.append(GlassAssessment(code="interlayer_unknown", message="Sin dato · falta el espesor del PVB. Completa la composición.", blocking=True))
    elif thickness not in bead_thicknesses:
        findings.append(GlassAssessment(code="bead_incompatible", message="El espesor total no tiene un junquillo declarado en esta serie.", blocking=True, source=product.source))
    if glass_mass_per_m2(product) is None:
        findings.append(GlassAssessment(code="mass_unknown", message="Sin dato · falta la densidad del PVB o el peso declarado por el proveedor."))
    limits = product.limits
    area = width_mm * height_mm / D("1000000")
    failed = any((value is not None and observed < value) for observed, value in (
        (width_mm, limits.min_width_mm), (height_mm, limits.min_height_mm))) or any(
        value is not None and observed > value for observed, value in (
            (width_mm, limits.max_width_mm), (height_mm, limits.max_height_mm),
            (area, limits.max_area_m2), (max(width_mm, height_mm) / min(width_mm, height_mm), limits.max_aspect_ratio)))
    if failed:
        findings.append(GlassAssessment(code="glass_limit", message="La pieza supera los límites declarados del producto de vidrio.", source=limits.source, blocking=True))
    findings.extend(assess_glass_safety(safety_class=product.properties.safety_class,
        synthetic=product.synthetic, width_mm=width_mm, height_mm=height_mm,
        rules=rules, door=door, sidelight=sidelight, sill_mm=sill_mm))
    if hardware_limit_kg is not None:
        if leaf_weight_kg is None:
            findings.append(GlassAssessment(code="hardware_mass_unknown", message="Sin dato · falta el peso completo de la hoja para comprobar el herraje."))
        elif leaf_weight_kg > hardware_limit_kg:
            findings.append(GlassAssessment(code="hardware_mass_limit", message="El peso de la hoja supera la capacidad declarada del herraje.", blocking=True))
    if any(ply.type == "TEMPERED" for layer in product.composition.layers if isinstance(layer, GlassPane) for ply in layer.plies):
        findings.append(GlassAssessment(code="tempered_exact", message="El templado se pide a medida exacta; no se recorta en taller.", source=product.source))
    return tuple(findings)


class GlassCharge(GlassModel):
    kind: str
    sku: str
    quantity: Decimal
    unit: Literal["M2", "M", "EA"]
    unit_cost: Decimal = Field(ge=0)
    total_cost: Decimal = Field(ge=0)


class GlassPrice(GlassModel):
    area_m2: Decimal
    billable_area_m2: Decimal
    charges: tuple[GlassCharge, ...]
    total_cost: Decimal
    bars_length_m: Decimal
    bars_crossings: int


def price_glass(*, product: GlassProduct | None, sku: str, width_mm: Decimal,
                height_mm: Decimal, rates: dict[str, Decimal],
                processing: GlassProcessing | None = None, shape_area_m2: Decimal | None = None,
                shape_perimeter_m: Decimal | None = None) -> GlassPrice:
    if min(width_mm, height_mm) <= 0:
        raise ValueError("Las medidas del vidrio deben ser positivas.")
    processing = processing or GlassProcessing()
    billing = product.billing if product else GlassBilling()
    area = shape_area_m2 if shape_area_m2 is not None else width_mm * height_mm / D("1000000")
    billable = max(area, billing.minimum_area_m2)
    charges = []

    def add(kind: str, rate_sku: str | None, qty: Decimal, unit: Literal["M2", "M", "EA"]) -> None:
        if qty == 0:
            return
        if rate_sku is None or rate_sku not in rates:
            raise ValueError(f"Sin dato · falta la tarifa de {kind}.")
        rate = rates[rate_sku]
        if rate < 0 or not rate.is_finite():
            raise ValueError("La tarifa debe ser un Decimal finito no negativo.")
        charges.append(GlassCharge(kind=kind, sku=rate_sku, quantity=qty, unit=unit,
            unit_cost=rate, total_cost=qty * rate))

    add("Vidrio", sku, billable, "M2")
    tempered = product is not None and any(ply.type == "TEMPERED"
        for layer in product.composition.layers if isinstance(layer, GlassPane) for ply in layer.plies)
    if tempered and billing.tempering_sku:
        add("Templado", billing.tempering_sku, billable, "M2")
    edge_length = sum((width_mm if edge in ("TOP", "BOTTOM") else height_mm
                       for edge in processing.polished_edges), D("0")) / D("1000")
    if shape_area_m2 is not None and processing.polished_edges:
        if shape_perimeter_m is None or set(processing.polished_edges) != {"TOP", "BOTTOM", "LEFT", "RIGHT"}:
            raise ValueError("El pulido de un contorno necesita su perímetro y todos sus cantos declarados.")
        edge_length = shape_perimeter_m
    add("Canto pulido", billing.polishing_sku, edge_length, "M")
    add("Perforación", billing.drilling_sku, D(processing.holes), "EA")
    bars_length = (height_mm * processing.bars_vertical + width_mm * processing.bars_horizontal) / D("1000")
    crossings = processing.bars_vertical * processing.bars_horizontal
    if shape_area_m2 is not None and bars_length:
        raise ValueError("El palillaje rectangular no es compatible con este contorno.")
    add("Palillaje por metro", billing.bars_per_m_sku, bars_length, "M")
    add("Cruce de palillaje", billing.bars_per_crossing_sku, D(crossings), "EA")
    return GlassPrice(area_m2=area, billable_area_m2=billable, charges=tuple(charges),
        total_cost=sum((value.total_cost for value in charges), D("0")),
        bars_length_m=bars_length, bars_crossings=crossings)


def relative_glass_prices(rates: dict[str, Decimal]) -> dict[str, str]:
    """Only compare resolved rates; unknown prices never rank as free."""
    if not rates:
        return {}
    minimum = min(rates.values())
    return {sku: "Menor costo del catálogo" if rate == minimum else "Mayor costo relativo"
            for sku, rate in rates.items()}


def glass_polygon_perimeter_m(points: Sequence[PlanPoint]) -> Decimal:
    if len(points) < 3:
        raise ValueError("El contorno necesita al menos tres puntos.")
    return sum((((points[(i + 1) % len(points)].x_mm - point.x_mm) ** 2
                 + (points[(i + 1) % len(points)].y_mm - point.y_mm) ** 2).sqrt()
                for i, point in enumerate(points)), D("0")) / D("1000")


def candidate_leaf_mass(*, total_kg: Decimal | None, previous_infill_kg: Decimal | None,
                        candidate: GlassProduct, area_m2: Decimal) -> Decimal | None:
    mass = glass_mass_per_m2(candidate)
    if total_kg is None or previous_infill_kg is None or mass is None:
        return None
    return total_kg - previous_infill_kg + mass * area_m2


def glass_section(composition: GlassComposition) -> list[dict[str, str]]:
    """Exact millimetre coordinates for the compositor's section drawing."""
    parts: list[dict[str, str]] = []
    x = D("0")
    for layer in composition.layers:
        if isinstance(layer, GlassChamber):
            gas = {"AIR": "Aire", "ARGON": "Argón"}.get(layer.gas or "", "Sin dato · gas")
            spacer = {"ALUMINIUM": "Separador de aluminio", "WARM_EDGE": "Separador de borde cálido"}.get(layer.spacer or "", "Sin dato · separador")
            parts.append({"kind": "CHAMBER", "x_mm": str(x), "width_mm": str(layer.width_mm),
                "label": gas + " · " + spacer})
            x += layer.width_mm
        else:
            for index, ply in enumerate(layer.plies):
                parts.append({"kind": "PANE", "x_mm": str(x), "width_mm": str(ply.thickness_mm),
                    "label": (_TYPE_LABELS[ply.type] or "Float incoloro") +
                        (f" · cara {ply.coating_face}" if ply.coating_face is not None else "")})
                x += ply.thickness_mm
                if index < len(layer.interlayers):
                    interlayer = layer.interlayers[index]
                    if interlayer.thickness_mm is None:
                        raise ValueError("Sin dato · falta el espesor del PVB para dibujar el corte a escala.")
                    parts.append({"kind": "PVB", "x_mm": str(x), "width_mm": str(interlayer.thickness_mm), "label": "PVB"})
                    x += interlayer.thickness_mm
    return parts


def glass_rate_requirements(product: GlassProduct | None, processing: GlassProcessing | None) -> tuple[tuple[str, str], ...]:
    if product is None:
        return ()
    processing = processing or GlassProcessing()
    billing = product.billing
    tempered = any(ply.type == "TEMPERED" for layer in product.composition.layers
                   if isinstance(layer, GlassPane) for ply in layer.plies)
    return tuple((sku, unit) for sku, unit, required in (
        (billing.tempering_sku, "M2", tempered),
        (billing.polishing_sku, "M", bool(processing.polished_edges)),
        (billing.drilling_sku, "EA", processing.holes > 0),
        (billing.bars_per_m_sku, "M", processing.bars_vertical + processing.bars_horizontal > 0),
        (billing.bars_per_crossing_sku, "EA", processing.bars_vertical * processing.bars_horizontal > 0),
    ) if sku is not None and required)
