"""Reference-window comparison and exact, recalculated catalog proposals.

No candidate is a manufacturer's fact. A human chooses a named rule and sees
the complete recalculated window before it can become a workshop value.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Literal

from dekopen_engine.geometry import calculate_geometry
from dekopen_engine.models import EngineResult, ParametricNode, ProfileRole, SystemParams
from dekopen_engine.snapshot import JsonValue, result_payload


@dataclass(frozen=True)
class Measurement:
    key: str
    group: Literal["profile_cuts", "reinforcements", "glasses"]
    index: int
    field: Literal["length_mm", "width_mm", "height_mm"]
    sku: str
    role: str
    quantity: int
    value_mm: Decimal
    angle_left: Decimal | None = None
    angle_right: Decimal | None = None


@dataclass(frozen=True)
class RuleParameter:
    resource: Literal["systems", "articles", "glazing"]
    field: str
    label: str
    previous: Decimal
    sku: str | None = None
    glass_thickness_mm: Decimal | None = None


@dataclass(frozen=True)
class CalibrationProposal:
    parameter: RuleParameter
    value: Decimal
    result: EngineResult


def measurements(result: EngineResult) -> tuple[Measurement, ...]:
    values = []
    for index, cut in enumerate(result.profile_cuts):
        values.append(Measurement(f"profile_cuts:{index}:length_mm", "profile_cuts", index,
            "length_mm", cut.sku, cut.role.value, cut.qty, cut.length_mm, cut.angle_left, cut.angle_right))
    for index, steel in enumerate(result.reinforcements):
        values.append(Measurement(f"reinforcements:{index}:length_mm", "reinforcements", index,
            "length_mm", steel.parent_profile_sku, steel.role.value, steel.qty, steel.length_mm,
            Decimal("90"), Decimal("90")))
    for index, glass in enumerate(result.glasses):
        for field in ("width_mm", "height_mm"):
            values.append(Measurement(f"glasses:{index}:{field}", "glasses", index,
                "width_mm" if field == "width_mm" else "height_mm", glass.article_sku or glass.glass_spec or "Vidrio",
                "GLASS", 1, getattr(glass, field)))
    return tuple(values)


def physical_reference(result: EngineResult) -> dict[str, JsonValue]:
    """Origin confirmations must not look like a change to a physical window."""
    payload = result_payload(result)
    payload.pop("assumptions", None)
    return payload


def measurement_comparison(result: EngineResult, declared: dict[str, Decimal]) -> list[dict[str, JsonValue]]:
    current = measurements(result)
    if set(declared) - {item.key for item in current}:
        raise ValueError("Una medida ya no pertenece al despiece calculado. Vuelve a comparar la ventana.")
    output: list[dict[str, JsonValue]] = []
    for item in current:
        expected = declared.get(item.key)
        if expected is not None and (not isinstance(expected, Decimal) or not expected.is_finite() or expected <= 0):
            raise ValueError("Escribe una medida positiva y exacta según tu manual.")
        output.append({"key": item.key, "group": item.group, "index": item.index, "field": item.field,
            "sku": item.sku, "role": item.role, "quantity": item.quantity,
            "value_mm": format(item.value_mm, "f"),
            "angle_left": format(item.angle_left, "f") if item.angle_left is not None else None,
            "angle_right": format(item.angle_right, "f") if item.angle_right is not None else None,
            "manual_mm": format(expected, "f") if expected is not None else None,
            "difference_mm": format(expected - item.value_mm, "f") if expected is not None else None,
            "matches": expected == item.value_mm if expected is not None else None})
    return output


def _parameters(params: SystemParams, measure: Measurement, *, finish: str) -> list[RuleParameter]:
    if measure.group == "glasses":
        field = "glass_clearance_white_mm" if finish == "WHITE" else "glass_clearance_foil_mm"
        return [RuleParameter("systems", field, "Holgura del vidrio por lado", getattr(params, field))]
    role = ProfileRole(measure.role)
    article = params.effective_profile_articles.get(role)
    if measure.group == "profile_cuts" and role is ProfileRole.GLAZING_BEAD:
        rules = [rule for rule in params.glazing_bead_rules.values() if rule.bead_article.sku == measure.sku]
        if len(rules) != 1:
            return []  # Reused bead codes cannot identify a unique thickness.
        rule = rules[0]
        return [RuleParameter("glazing", "cut_add_mm", "Adición al corte del junquillo",
            rule.cut_add_mm, measure.sku, rule.glass_thickness_mm)]
    if article is None or article.sku != measure.sku:
        return []  # Extra/curved/advanced members need their own declared rule.
    if measure.group == "reinforcements":
        value = article.reinforcement_rule.cut_deduction_mm if article.reinforcement_rule else article.reinforcement_gap_mm
        field = "reinforcement_rule.cut_deduction_mm" if article.reinforcement_rule else "reinforcement_gap_mm"
        return [] if value is None else [RuleParameter("articles", field, "Descuento del refuerzo", value, article.sku)]
    choices = []
    if role is ProfileRole.SASH:
        choices.append(RuleParameter("systems", "sash_overlap_mm", "Traslape de la hoja por lado", params.sash_overlap_mm))
    if article.cut_rule is not None:
        for field, label in (("joint_deduction_per_end_mm", "Descuento de unión por extremo"),
                ("welding_loss_per_end_mm", "Adición de soldadura por extremo"),
                ("meeting_deduction_mm", "Descuento de encuentro")):
            choices.append(RuleParameter("articles", "cut_rule." + field, label,
                getattr(article.cut_rule, field), article.sku))
    elif article.welding_loss_mm is not None:
        choices.append(RuleParameter("articles", "welding_loss_mm", "Adición de soldadura por extremo",
            article.welding_loss_mm, article.sku))
    return choices


def adjusted_params(params: SystemParams, parameter: RuleParameter, value: Decimal) -> SystemParams:
    """Validate a complete new model; model_copy alone would skip constraints."""
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError("La regla debe ser un decimal finito.")
    payload = params.model_dump()
    if parameter.resource == "systems":
        payload[parameter.field] = value
    elif parameter.resource == "glazing":
        rule = payload["glazing_bead_rules"][parameter.glass_thickness_mm]
        rule[parameter.field] = value
    else:
        found = False
        for article in payload["effective_profile_articles"].values():
            if article["sku"] == parameter.sku:
                found = True
                target = article
                path = parameter.field.split(".")
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
        if not found:
            raise ValueError("El perfil de esta regla ya no pertenece a la serie.")
    return SystemParams.model_validate(payload)


def propose_calibration(root: ParametricNode, params: SystemParams, *, finish: str,
        measurement_key: str, target_mm: Decimal) -> tuple[CalibrationProposal, ...]:
    """Invert named rule candidates with Decimal probes, then run the engine.

    Probes only propose an input. The ordinary engine must reproduce the exact
    requested cut; rounding plateaus, invalid geometry and ambiguous identities
    never yield an approximate match or an invented output.
    """
    if not isinstance(target_mm, Decimal) or not target_mm.is_finite() or target_mm <= 0:
        raise ValueError("La medida del manual debe ser un decimal positivo y finito.")
    def calculate(candidate: SystemParams) -> EngineResult:
        return calculate_geometry(root, candidate, is_foiled=finish != "WHITE", finish=finish)
    baseline = calculate(params)
    measure = next((item for item in measurements(baseline) if item.key == measurement_key), None)
    if measure is None:
        raise ValueError("Elige una medida del despiece actual.")
    if measure.value_mm == target_mm:
        return ()
    proposals = []
    for parameter in _parameters(params, measure, finish=finish):
        for step in (Decimal("1"), Decimal("-1")):
            try:
                probe = calculate(adjusted_params(params, parameter, parameter.previous + step))
                reading = next(item for item in measurements(probe) if item.key == measurement_key)
                if (reading.sku, reading.role, reading.quantity) != (measure.sku, measure.role, measure.quantity):
                    continue
                slope = (reading.value_mm - measure.value_mm) / step
                if slope == 0:
                    continue
                value = parameter.previous + (target_mm - measure.value_mm) / slope
                # Signed bead additions are valid catalog inputs. Other fields
                # retain their model constraints; the sheet stores NUMERIC(8,2).
                if abs(value) > Decimal("999999.99") or value.quantize(Decimal("0.01")) != value:
                    continue
                recalculated = calculate(adjusted_params(params, parameter, value))
                actual = next(item for item in measurements(recalculated) if item.key == measurement_key)
                if (actual.sku, actual.role, actual.quantity, actual.value_mm) != (
                        measure.sku, measure.role, measure.quantity, target_mm):
                    continue
                proposals.append(CalibrationProposal(parameter, value, recalculated))
                break
            except (ValueError, InvalidOperation, StopIteration):
                continue
    return tuple(proposals)
