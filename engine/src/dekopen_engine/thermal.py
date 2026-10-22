"""Pure Decimal daylight-area Uw and scoped, reviewed OGUC window checks.

This is a calculation record, not a certificate or whole-building assessment.
All authority/time/context is passed in; the engine performs no I/O.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, localcontext
import hashlib
import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from dekopen_engine.thermal_rules import AIR_MINIMUM, EQUIPMENT_U_MAX, RULE_SOURCE, RULE_VERSION, maximum_percentage
from dekopen_engine.technical_facts import GeometryComputation
from dekopen_engine.glass_composition import GlassProduct
from dekopen_engine.models import BayOpeningType
from dekopen_engine.manufacturing_trace import PlacementDomain

D = Decimal
Orientation = Literal["N", "E", "S", "W", "OGT"]
Verdict = Literal["PASS", "FAIL", "UNKNOWN"]


class ThermalModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


def fingerprint(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


class ThermalAuthority(ThermalModel):
    id: str = ""
    kind: Literal["FRAME", "GLASS", "SPACER", "PERFORMANCE"]
    profile_skus: tuple[str, ...] = ()
    glass_sku: str | None = None
    glass_fingerprint: str | None = None
    spacer_code: str | None = None
    catalog_fingerprint: str
    construction_fingerprint: str | None = None
    uf: Decimal | None = Field(default=None, gt=0)
    ug: Decimal | None = Field(default=None, gt=0)
    solar_factor: Decimal | None = Field(default=None, ge=0, le=1)
    psi_g: Decimal | None = Field(default=None, ge=0)
    air_class: int | None = Field(default=None, ge=0, le=4)
    air_pressure_pa: Decimal | None = Field(default=None, gt=0)
    water_class: str | None = None
    wind_class: str | None = None
    min_width_mm: Decimal = Field(gt=0)
    max_width_mm: Decimal = Field(gt=0)
    min_height_mm: Decimal = Field(gt=0)
    max_height_mm: Decimal = Field(gt=0)
    opening_types: tuple[str, ...] = Field(min_length=1)
    source_document: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    source_page: str = Field(min_length=1)
    laboratory: str = Field(min_length=1)
    laboratory_registration: str = ""
    report_date: date
    valid_until: date
    standard: str = Field(min_length=1)
    applicability: str = Field(min_length=1)
    synthetic: bool = False
    review_state: Literal["PENDING", "REVIEWED", "REJECTED", "REVOKED"] = "PENDING"
    reviewed_by: str | None = None
    reviewed_at: str | None = None

    @model_validator(mode="after")
    def complete(self) -> ThermalAuthority:
        for field in ("source_document", "source_url", "source_page", "laboratory", "standard", "applicability"):
            if not getattr(self, field).strip():
                raise ValueError("El informe necesita referencia, laboratorio, norma y alcance explícitos.")
        if not set(self.opening_types) <= {opening.value for opening in BayOpeningType}:
            raise ValueError("Una apertura del alcance no pertenece al contrato físico del motor.")
        if self.min_width_mm > self.max_width_mm or self.min_height_mm > self.max_height_mm:
            raise ValueError("El mínimo no puede superar el máximo ensayado.")
        if self.valid_until < self.report_date:
            raise ValueError("La vigencia no puede terminar antes del informe.")
        if len(set(self.profile_skus)) != len(self.profile_skus) or len(set(self.opening_types)) != len(self.opening_types):
            raise ValueError("No repitas perfiles ni aperturas del alcance.")
        if self.kind != "GLASS" and not self.profile_skus:
            raise ValueError("Declara la combinación exacta de perfiles del informe.")
        if self.kind in ("GLASS", "SPACER") and not (self.glass_sku and self.glass_fingerprint):
            raise ValueError("El informe necesita un vidrio y su composición vigente.")
        required = {"FRAME": self.uf is not None, "GLASS": self.ug is not None,
                    "SPACER": self.psi_g is not None and bool(self.spacer_code),
                    "PERFORMANCE": any(v is not None for v in (self.air_class, self.water_class, self.wind_class))}
        allowed = {"FRAME": {"uf"}, "GLASS": {"ug", "solar_factor"}, "SPACER": {"psi_g"},
                   "PERFORMANCE": {"air_class", "air_pressure_pa", "water_class", "wind_class"}}
        if not required[self.kind] or any(getattr(self, field) is not None for field in
            {"uf", "ug", "solar_factor", "psi_g", "air_class", "air_pressure_pa", "water_class", "wind_class"} - allowed[self.kind]):
            raise ValueError("Declara solo los valores que corresponden a este informe.")
        if self.air_class is not None and self.air_pressure_pa != D("100"):
            raise ValueError("La clasificación de aire para este panel debe estar declarada a 100 Pa.")
        if self.air_class is not None and not (
            self.laboratory_registration.strip()
            and all(re.search(rf"NCh\s*{number}\b", self.standard, re.IGNORECASE) for number in (3296, 3297))
        ):
            raise ValueError("El aire necesita NCh3296/3297 y la inscripción vigente del laboratorio MINVU.")
        return self


class ThermalPane(ThermalModel):
    bay_id: str
    leaf_id: str | None = None
    glass_sku: str
    glass_fingerprint: str
    spacer_code: str | None
    visible_width_mm: Decimal = Field(gt=0)
    visible_height_mm: Decimal = Field(gt=0)


class ThermalGeometry(ThermalModel):
    width_mm: Decimal = Field(gt=0)
    height_mm: Decimal = Field(gt=0)
    profile_skus: tuple[str, ...]
    opening_types: tuple[str, ...]
    panes: tuple[ThermalPane, ...]
    construction_fingerprint: str
    reasons: tuple[str, ...] = ()


def glass_binding(product: GlassProduct | None) -> tuple[str, str | None]:
    if product is None:
        return "", None
    layers = product.composition.layers
    chambers = [getattr(layer, "spacer", None) for layer in layers if layer.kind == "CHAMBER"]
    spacer = "NONE" if not chambers else chambers[0] if len(set(chambers)) == 1 else None
    return fingerprint(product.composition.model_dump(mode="json")), spacer


def thermal_geometry(computation: GeometryComputation) -> ThermalGeometry | None:
    trace = computation.manufacturing_trace
    if trace is None or computation.result is None:
        return None
    reasons = []
    panes = []
    for infill, physical in zip(computation.infills, trace.infills, strict=True):
        if infill.kind != "GLASS":
            reasons.append("El relleno opaco necesita un método térmico y Up propios.")
            continue
        if infill.glass_product is not None and infill.glass_product.synthetic:
            reasons.append("DEMO: la composición del vidrio es sintética, sin certificación del fabricante.")
        if physical.placement_domain is PlacementDomain.SLIDING_INFILL:
            reasons.append("La corredera necesita áreas proyectadas sin solapes y el puente del encuentro declarado; no se suman vidrios solapados.")
            continue
        if physical.shape or infill.visible_width_mm is None or infill.visible_height_mm is None:
            reasons.append("La geometría de vidrio visible de este contorno no está declarada para el método de áreas.")
            continue
        if infill.visible_width_mm <= 0 or infill.visible_height_mm <= 0:
            reasons.append("Las caras de perfil no dejan un vidrio visible positivo.")
            continue
        binding, spacer = glass_binding(infill.glass_product)
        panes.append(ThermalPane(bay_id=infill.bay_id, leaf_id=infill.leaf_id,
            glass_sku=physical.technical_sku, glass_fingerprint=binding, spacer_code=spacer,
            visible_width_mm=infill.visible_width_mm, visible_height_mm=infill.visible_height_mm))
    profiles = tuple(sorted({m.workshop_sku for m in trace.members if m.role.value not in
        ("GLAZING_BEAD", "ADDITIONAL", "COVER_TRIM", "SILL", "PLINTH")}))
    openings = tuple(sorted({leaf.opening_type.value for leaf in computation.leaves}
        | {"FIXED" for infill in trace.infills if infill.parent_leaf_id is None}))
    # Test results do not transfer to another glazing, hardware, topology or
    # size. Remove storage identities only; retain all physical coordinates.
    def physical_projection(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: physical_projection(v) for k, v in value.items()
                    if k != "topology_path" and not k.endswith("_id") and k != "id"}
        if isinstance(value, list):
            return [physical_projection(v) for v in value]
        return value
    construction = fingerprint({"trace": physical_projection(trace.model_dump(mode="json")),
        "glass": [glass_binding(i.glass_product)[0] for i in computation.infills],
        "hardware": [leaf.selected_kit.model_dump(mode="json") if leaf.selected_kit else None
                     for leaf in computation.leaves]})
    return ThermalGeometry(width_mm=trace.nominal_width_mm, height_mm=trace.nominal_height_mm,
        profile_skus=profiles, opening_types=openings, panes=tuple(panes),
        construction_fingerprint=construction, reasons=tuple(dict.fromkeys(reasons)))


def authority_matches(authority: ThermalAuthority, geometry: ThermalGeometry, *, catalog_fingerprint: str,
                      as_of: date, pane: ThermalPane | None = None) -> bool:
    if (authority.synthetic or authority.review_state != "REVIEWED" or not authority.reviewed_by or not authority.reviewed_at
        or authority.catalog_fingerprint != catalog_fingerprint or not authority.report_date <= as_of <= authority.valid_until
        or not authority.min_width_mm <= geometry.width_mm <= authority.max_width_mm
        or not authority.min_height_mm <= geometry.height_mm <= authority.max_height_mm
        or not set(geometry.opening_types) <= set(authority.opening_types)):
        return False
    if authority.kind != "GLASS" and set(authority.profile_skus) != set(geometry.profile_skus):
        return False
    if authority.kind in ("GLASS", "SPACER") and (pane is None or authority.glass_sku != pane.glass_sku
        or authority.glass_fingerprint != pane.glass_fingerprint):
        return False
    if authority.kind == "SPACER" and (pane is None or authority.spacer_code != pane.spacer_code):
        return False
    if authority.kind == "PERFORMANCE" and (not authority.construction_fingerprint or authority.construction_fingerprint != geometry.construction_fingerprint):
        return False
    return True


def calculate_uw(geometry: ThermalGeometry | None, authorities: tuple[ThermalAuthority, ...], *,
                 catalog_fingerprint: str, as_of: date, synthetic: bool = False,
                 geometry_authoritative: bool = True) -> dict[str, Any]:
    missing = []
    if synthetic:
        missing.append("DEMO: catálogo sintético, sin certificación del fabricante.")
    if not geometry_authoritative:
        missing.append("La geometría de caras y galces necesita evidencia vigente revisada del catálogo.")
    if geometry is None:
        return {"state": "UNKNOWN", "uw": None, "missing": missing + ["Falta geometría térmica exacta del motor."], "trace": None,
                "air_class": None, "water_class": None, "wind_class": None}
    missing.extend(geometry.reasons)
    if not geometry.panes:
        missing.append("No hay vidrio visible evaluable por este método.")

    def pick(kind: str, pane: ThermalPane | None = None) -> ThermalAuthority | None:
        found = [a for a in authorities if a.kind == kind and authority_matches(a, geometry,
            catalog_fingerprint=catalog_fingerprint, as_of=as_of, pane=pane)]
        # Two overlapping reports are ambiguous. Never pick the most favourable.
        return found[0] if len(found) == 1 else None

    frame = pick("FRAME")
    performance = None if synthetic or not geometry_authoritative or geometry.reasons else pick("PERFORMANCE")
    if frame is None:
        missing.append("Uf: falta un informe vigente, único y revisado para la combinación exacta de perfiles y dimensiones.")
    inputs = []
    for index, pane in enumerate(geometry.panes, 1):
        glass, spacer = pick("GLASS", pane), pick("SPACER", pane)
        if glass is None:
            missing.append(f"Ug: falta un informe vigente, único y revisado del vidrio del paño {index}.")
        if spacer is None:
            missing.append(f"Ψg: falta un informe vigente, único y revisado del separador y combinación del paño {index}.")
        inputs.append((pane, glass, spacer))
    with localcontext() as context:
        context.prec = 50
        area = geometry.width_mm * geometry.height_mm / D("1000000")
        ag = sum((p.visible_width_mm*p.visible_height_mm/D("1000000") for p in geometry.panes), D(0))
        af = area-ag
        lg = sum((2*(p.visible_width_mm+p.visible_height_mm)/D("1000") for p in geometry.panes), D(0))
        if af <= 0:
            missing.append("El área visible no deja un área de marco positiva; revisa la geometría del catálogo.")
        numerator = None
        if not missing:
            assert frame is not None and frame.uf is not None
            numerator = af*frame.uf
            for p, glass, spacer in inputs:
                assert glass is not None and glass.ug is not None and spacer is not None and spacer.psi_g is not None
                numerator += (p.visible_width_mm*p.visible_height_mm/D("1000000")*glass.ug
                    +2*(p.visible_width_mm+p.visible_height_mm)/D("1000")*spacer.psi_g)
        uw = numerator/area if numerator is not None else None
    trace = {"method": "ISO 10077-1 · método de áreas", "formula": "Uw = (ΣAg·Ug + Af·Uf + Σlg·Ψg) / (Ag + Af)",
        "area_m2": area, "ag_m2": ag, "af_m2": af, "lg_m": lg, "numerator_w_k": numerator,
        "uf": frame.uf if frame and not synthetic else None,
        "frame_report": frame.model_dump(mode="json") if frame else None,
        "performance_report": performance.model_dump(mode="json") if performance else None,
        "panes": [{**p.model_dump(mode="python"), "ug": g.ug if g and not synthetic else None,
            "solar_factor": g.solar_factor if g and not synthetic else None,
            "psi_g": s.psi_g if s and not synthetic else None,
            "glass_report": g.model_dump(mode="json") if g else None,
            "spacer_report": s.model_dump(mode="json") if s else None} for p,g,s in inputs]}
    return {"state": "KNOWN" if uw is not None else "UNKNOWN", "uw": uw,
        "missing": list(dict.fromkeys(missing)), "trace": trace,
        "air_class": performance.air_class if performance else None,
        "water_class": performance.water_class if performance else None,
        "wind_class": performance.wind_class if performance else None}


def thermal_delta(before: Decimal | None, after: Decimal | None) -> Decimal | None:
    if before is None or after is None:
        return None
    with localcontext() as context:
        context.prec = 50
        return after - before


class ThermalPositionContext(ThermalModel):
    position_id: str
    orientation: Orientation | None = None
    surface: Literal["WALL", "ROOF"] | None = None


class ThermalProjectInput(ThermalModel):
    zone: Literal["A", "B", "C", "D", "E", "F", "G", "H", "I"] | None = None
    zone_source: str = ""
    use: Literal["RESIDENTIAL", "EDUCATION", "HEALTH", "HOTEL"] | None = None
    walls_m2: dict[Orientation, Decimal] = Field(default_factory=dict)
    exposed_wall_area_m2: Decimal | None = Field(default=None, ge=0)
    envelope_complete: bool = False
    wall_source: str = ""
    positions: tuple[ThermalPositionContext, ...] = ()
    include_doc01: bool = False
    regulatory_scope_confirmed: bool = False
    regulatory_calculation_source: str = ""
    regulatory_method_confirmed: bool = False

    @model_validator(mode="after")
    def valid_areas(self) -> ThermalProjectInput:
        if any(value <= 0 or not value.is_finite() for value in self.walls_m2.values()):
            raise ValueError("Ingresa superficies interiores de muro positivas, incluyendo vanos y medianeros.")
        if "OGT" in self.walls_m2:
            raise ValueError("OGT se deriva del total de muros; declara Norte, Oriente, Sur y Poniente.")
        if self.exposed_wall_area_m2 is not None and self.exposed_wall_area_m2 > sum(self.walls_m2.values(), D(0)):
            raise ValueError("La superficie expuesta no puede superar el total de muros perimetrales.")
        if len({p.position_id for p in self.positions}) != len(self.positions):
            raise ValueError("No repitas la orientación de una posición.")
        if self.zone and not self.zone_source.strip():
            raise ValueError("Indica la referencia oficial de la zona elegida; no se infiere por comuna.")
        if self.walls_m2 and not self.wall_source.strip():
            raise ValueError("Indica de qué plano o medición provienen los muros.")
        return self


def assess_project(inputs: ThermalProjectInput, positions: list[dict[str, Any]]) -> dict[str, Any]:
    with localcontext() as context:
        context.prec = 50
        return _assess_project(inputs, positions)


def _assess_project(inputs: ThermalProjectInput, positions: list[dict[str, Any]]) -> dict[str, Any]:
    zone = inputs.zone
    total_walls = sum(inputs.walls_m2.values(), D(0))
    ogt = (inputs.exposed_wall_area_m2/total_walls < D("0.6")
           if total_walls > 0 and inputs.exposed_wall_area_m2 is not None else None)
    contexts = {p.position_id: p for p in inputs.positions}
    general = []
    if zone is None:
        general.append("Elige la zona térmica A–I y registra su referencia oficial.")
    if inputs.use is None:
        general.append("Declara el uso de la unidad térmica.")
    if not inputs.regulatory_scope_confirmed:
        general.append("Confirma con el responsable que aplica OGUC 4.1.10 y revisa el plan de descontaminación local.")
    if not inputs.regulatory_method_confirmed or not inputs.regulatory_calculation_source.strip():
        general.append("El responsable debe cotejar el cálculo con NCh3137/1 y NCh3137/2 y registrar la memoria; ISO 10077-1 por sí sola no acredita OGUC.")
    if not inputs.envelope_complete:
        general.append("Confirma que están incluidas todas las ventanas de la unidad térmica.")
    if inputs.use == "RESIDENTIAL" and ogt is None:
        general.append("Ingresa la superficie de muros y su parte expuesta; el motor determinará si corresponde OGT.")
    if any(p["position_id"] not in contexts or contexts[p["position_id"]].surface is None for p in positions):
        general.append("Ubica todas las ventanas en la envolvente; una posición sin ubicación puede alterar cualquier grupo.")
    groups: dict[str, list[dict[str, Any]]] = {}
    output = []
    for position in positions:
        item = {**position, "verdict": "UNKNOWN", "causes": [*general, *position["thermal"]["missing"]],
                "minimum_air_class": AIR_MINIMUM.get(zone) if zone else None, "maximum_percentage": None, "actual_percentage": None,
                "maximum_uw": None, "group": None}
        context = contexts.get(position["position_id"])
        metric = position["thermal"]
        if metric["uw"] is None:
            item["causes"].append("Falta calcular Uw: completa sus informes y la geometría antes de evaluar cumplimiento.")
        if zone and AIR_MINIMUM[zone] is not None:
            if metric["air_class"] is None:
                item["causes"].append("Falta la clase de aire: agrega el ensayo vigente a 100 Pa (NCh3296/3297).")
            elif metric["air_class"] < AIR_MINIMUM[zone]:
                item["verdict"] = "FAIL"
                item["causes"].append("La clase de permeabilidad al aire no alcanza el mínimo de la zona a 100 Pa.")
        if context is None or context.surface is None:
            item["causes"].append("Declara si la posición está en fachada o techumbre y su orientación.")
        elif context.surface == "ROOF":
            item["group"] = "ROOF"
            if zone and zone != "A":
                item["maximum_uw"] = D("3.6")
            if inputs.use in ("EDUCATION", "HEALTH", "HOTEL") and zone:
                limit = EQUIPMENT_U_MAX[zone]
                item["maximum_uw"] = min(item["maximum_uw"], limit) if item["maximum_uw"] is not None else limit
        elif inputs.use in ("EDUCATION", "HEALTH", "HOTEL") and zone:
            item["maximum_uw"] = EQUIPMENT_U_MAX[zone]
        elif inputs.use == "RESIDENTIAL":
            orientation_key: Orientation | None = "OGT" if ogt is True else context.orientation
            if orientation_key is None or (orientation_key == "OGT" and ogt is not True):
                item["causes"].append("Declara la orientación real de fachada; OGT se determina con la superficie expuesta.")
            else:
                item["group"] = orientation_key
                groups.setdefault(orientation_key, []).append(item)
        if item["maximum_uw"] is not None and metric["uw"] is not None and metric["uw"] > item["maximum_uw"]:
            item["verdict"] = "FAIL"
            item["causes"].append("Uw supera el máximo de transmitancia aplicable a esta ventana.")
        output.append(item)
    group_records = []
    for key, members in groups.items():
        wall = total_walls if key == "OGT" else next((value for side,value in inputs.walls_m2.items() if side == key), None)
        area_known = all(p.get("window_area_m2") is not None for p in members)
        area = sum((p["window_area_m2"]*p["quantity"] for p in members), D(0)) if area_known else None
        complete = all(p["thermal"]["uw"] is not None for p in members)
        largest = max((p["thermal"]["uw"] for p in members), default=None) if complete else None
        allowed = maximum_percentage(zone, key, largest) if zone and largest is not None else None
        percentage = area/wall*100 if wall and area is not None else None
        for member in members:
            member.update(maximum_percentage=allowed, actual_percentage=percentage)
            if not complete:
                member["causes"].append("Falta Uw de otra ventana del grupo; gobierna el mayor Uw, nunca un promedio.")
            elif allowed is None:
                member["causes"].append("Uw está fuera de la tabla oficial; no se extrapola el porcentaje permitido.")
            if wall is None:
                member["causes"].append("Falta la superficie de muro: ingrésala desde el plano, incluyendo aberturas de obra y medianeros.")
            elif area is None:
                member["causes"].append("Falta el área exacta de otra ventana del grupo.")
            elif area > wall:
                member["causes"].append("Las ventanas superan el área de muro declarada; corrige la medición.")
            elif allowed is not None and percentage is not None and percentage > allowed:
                member["verdict"] = "FAIL"
                member["causes"].append("El porcentaje de ventanas supera el máximo de la orientación para el mayor Uw del grupo.")
        group_records.append({"orientation": key, "window_area_m2": area, "wall_area_m2": wall,
            "largest_uw": largest, "maximum_percentage": allowed, "actual_percentage": percentage})
    for item in output:
        item["causes"] = list(dict.fromkeys(item["causes"]))
        if item["verdict"] != "FAIL" and not item["causes"]:
            item["verdict"] = "PASS"
    verdict = "FAIL" if any(p["verdict"] == "FAIL" for p in output) else "PASS" if output and all(p["verdict"] == "PASS" for p in output) else "UNKNOWN"
    return {"verdict": verdict, "causes": general if output else [*general, "El proyecto aún no tiene ventanas evaluables."],
        "positions": output, "groups": group_records, "ogt": ogt, "rules_version": RULE_VERSION,
        "source_url": RULE_SOURCE, "source_label": "OGUC 4.1.10 · DS15/2024 · tablas 3, 9, 12 y 16",
        "scope": "Evaluación de ventanas; no acredita condensación, ventilación, hermeticidad de la envolvente ni cumplimiento completo del edificio."}
