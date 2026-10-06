"""Deterministic kit selection against finished dimensions and exact mass."""

from decimal import Decimal
from dataclasses import dataclass

from dekopen_engine.models import BayOpeningType, HardwareKitRule, SystemParams, Opening, OpeningUse, OpeningMovement, HardwareSelection
from dekopen_engine.hardware_classes import HardwareExpansion, HardwareRuleViolation, expand_hardware
from dekopen_engine.weight import ExactLeafWeight, with_hardware_weight
from dekopen_engine.catalog_rules import SLIDING_OPENINGS, sliding_parameters


class NoCompatibleHardwareKit(ValueError):
    """No declared kit satisfies the leaf. `context` carries the leaf size
    and the compatible kits' dimensional envelope when the failure is
    dimensional, so the API can name the real constraint instead of an
    opaque identifier."""

    def __init__(self, message: str, *, context: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.context = context or {}


class AmbiguousHardwareKit(ValueError):
    pass


def normalize_opening_type(opening: BayOpeningType) -> str:
    if opening in (BayOpeningType.TURN_LEFT, BayOpeningType.TURN_RIGHT):
        return "TURN"
    if opening in (BayOpeningType.TILT_TURN_LEFT, BayOpeningType.TILT_TURN_RIGHT):
        return "TILT_TURN"
    if opening in (BayOpeningType.SLIDING_2L, BayOpeningType.SLIDING_3L,
                   BayOpeningType.SLIDING_4L, BayOpeningType.SLIDING):
        return "SLIDING"
    if opening in (BayOpeningType.DOOR_ENTRY, BayOpeningType.DOOR_DOUBLE):
        return "DOOR"
    return opening.value


@dataclass(frozen=True, slots=True)
class HardwareCandidateEvaluation:
    kit: HardwareKitRule
    opening_match: bool
    rail_match: bool
    width_match: bool
    height_match: bool
    exact_total_weight: ExactLeafWeight
    # None = the leaf mass is UNKNOWN — compatibility is undecidable, never
    # silently certified.
    weight_match: bool | None
    expansion: HardwareExpansion | None = None
    violations: tuple[tuple[str, str], ...] = ()

    @property
    def compatible(self) -> bool:
        return (self.opening_match and self.rail_match and self.width_match
                and self.height_match and self.weight_match is True and not self.violations)


def evaluate_hardware_candidates(
    *, opening: BayOpeningType, width_mm: Decimal, height_mm: Decimal,
    base_weight: ExactLeafWeight, params: SystemParams, explicit_sku: str | None = None,
    physical_opening: Opening | None = None, opening_use: OpeningUse = OpeningUse.WINDOW,
    allowed_skus: tuple[str, ...] | None = None,
    selection: HardwareSelection | None = None,
    requested_handle_height_mm: Decimal | None = None,
) -> list[HardwareCandidateEvaluation]:
    candidates: list[HardwareCandidateEvaluation] = []
    for kit in params.available_hardware_kits:
        if allowed_skus is not None and kit.sku not in allowed_skus:
            continue
        if explicit_sku is not None and kit.sku != explicit_sku:
            continue
        expansion = None
        violations: list[tuple[str, str]] = []
        if kit.class_authority is not None:
            authority = kit.class_authority
            ratio = width_mm / height_mm
            if authority.minimum_width_height_ratio is not None and ratio < authority.minimum_width_height_ratio:
                violations.append(("ratio", f"Relación ancho/alto {ratio}: {authority.class_name} exige al menos {authority.minimum_width_height_ratio}. Aumenta el ancho o reduce el alto."))
            if authority.maximum_width_height_ratio is not None and ratio > authority.maximum_width_height_ratio:
                violations.append(("ratio", f"Relación ancho/alto {ratio}: {authority.class_name} admite hasta {authority.maximum_width_height_ratio}. Reduce el ancho o divide la bahía."))
            if authority.minimum_stay_height_mm is not None and height_mm < authority.minimum_stay_height_mm:
                violations.append(("stay", f"Alto de hoja {height_mm} mm: el compás de {authority.class_name} requiere al menos {authority.minimum_stay_height_mm} mm. Aumenta el alto o elige otra apertura."))
            try:
                expansion = expand_hardware(kit, width_mm=width_mm, height_mm=height_mm,
                    base_weight_kg=base_weight.total_weight_kg, selection=selection,
                    requested_handle_height_mm=requested_handle_height_mm)
            except HardwareRuleViolation as error:
                violations.append((error.axis, str(error)))
                if error.axis == "handle":
                    try:
                        expansion = expand_hardware(kit, width_mm=width_mm, height_mm=height_mm,
                            base_weight_kg=base_weight.total_weight_kg, selection=selection)
                    except HardwareRuleViolation:
                        pass
            mass = expansion.hardware_weight_kg if expansion is not None else None
            exact = with_hardware_weight(base_weight, kit.model_copy(update={"weight_kg": mass}), params)
            if expansion is not None:
                if expansion.unknown_reasons:
                    exact = ExactLeafWeight(exact.pvc_weight_kg, exact.steel_weight_kg, exact.infill_weight_kg,
                        exact.hardware_weight_kg, base_weight.weight_unknown_reasons + expansion.unknown_reasons)
                expansion = HardwareExpansion(expansion.contents, expansion.hardware_weight_kg,
                    expansion.unknown_reasons, expansion.resolution.model_copy(update={"exact_leaf_weight_kg": exact.total_weight_kg}))
        else:
            if selection is not None and (selection.handle_code or selection.color_code or selection.option_codes):
                violations.append(("option", "Este kit histórico no declara opciones ni modelos de manilla. Selecciona una clase con autoridad de catálogo."))
            exact = with_hardware_weight(base_weight, kit, params)
        total = exact.total_weight_kg
        normalized = ("DOOR" if opening_use is OpeningUse.DOOR else
            "AWNING" if physical_opening.movement is OpeningMovement.TOP_HUNG else
            "SLIDING" if physical_opening.movement is OpeningMovement.SLIDE else
            physical_opening.movement.value) if physical_opening is not None else normalize_opening_type(opening)
        candidates.append(HardwareCandidateEvaluation(
            kit=kit, opening_match=kit.opening_type == normalized,
            rail_match=(kit.rail_type is params.rail_type if params.uses_legacy_rules
                        else kit.rail_type is sliding_parameters(params).rail_type
                        if opening in SLIDING_OPENINGS else True),
            width_match=kit.min_leaf_width_mm <= width_mm <= kit.max_leaf_width_mm,
            height_match=kit.min_leaf_height_mm <= height_mm <= kit.max_leaf_height_mm,
            exact_total_weight=exact,
            weight_match=(None if total is None else total <= kit.max_leaf_weight_kg),
            expansion=expansion, violations=tuple(violations),
        ))
    return candidates


def resolve_hardware_evaluations(
    evaluations: list[HardwareCandidateEvaluation], *, opening: BayOpeningType,
    explicit_sku: str | None = None,
    leaf_width_mm: Decimal | None = None,
    leaf_height_mm: Decimal | None = None,
) -> tuple[HardwareKitRule, ExactLeafWeight]:
    candidates = [candidate for candidate in evaluations if candidate.compatible]
    # Kits matching opening and rail but failing a concrete check — their
    # merged envelope is the constraint the user must satisfy.
    matched = [
        candidate for candidate in evaluations
        if candidate.opening_match and candidate.rail_match
    ]

    def failure_context(axis: str) -> dict[str, str]:
        context: dict[str, str] = {"axis": axis, "opening": explicit_sku or opening.value}
        if leaf_width_mm is not None and leaf_height_mm is not None:
            context["leaf_width_mm"] = str(leaf_width_mm)
            context["leaf_height_mm"] = str(leaf_height_mm)
        if matched:
            context["kit_min_width_mm"] = str(min(c.kit.min_leaf_width_mm for c in matched))
            context["kit_max_width_mm"] = str(max(c.kit.max_leaf_width_mm for c in matched))
            context["kit_min_height_mm"] = str(min(c.kit.min_leaf_height_mm for c in matched))
            context["kit_max_height_mm"] = str(max(c.kit.max_leaf_height_mm for c in matched))
        return context

    if not candidates:
        invalid_rule = [c for c in matched if c.width_match and c.height_match and c.violations]
        if invalid_rule:
            axis, message = invalid_rule[0].violations[0]
            raise NoCompatibleHardwareKit(message, context={**failure_context(axis), "message": message})
        undecidable = [
            candidate for candidate in evaluations
            if candidate.weight_match is None and candidate.opening_match
            and candidate.rail_match and candidate.width_match and candidate.height_match
        ]
        if undecidable:
            reasons = sorted({
                reason
                for candidate in undecidable
                for reason in candidate.exact_total_weight.weight_unknown_reasons
            })
            raise NoCompatibleHardwareKit(
                "Hardware compatibility undecidable — leaf mass unknown: "
                + ", ".join(reasons),
                context=failure_context("undecidable"),
            )
        # Axis of failure: a kit whose envelope the leaf escapes fails on
        # size; a kit it fits that still rejects carries a mass violation.
        if matched and all(c.width_match and c.height_match for c in matched):
            axis = "weight"
        elif matched:
            axis = "size"
        else:
            axis = ""
        context = failure_context(axis)
        if axis == "weight":
            overweight = [c for c in matched if c.weight_match is False]
            totals = [
                c.exact_total_weight.total_weight_kg
                for c in overweight
                if c.exact_total_weight.total_weight_kg is not None
            ]
            if totals:
                context["leaf_weight_kg"] = str(min(totals))
                context["kit_max_weight_kg"] = str(
                    max(c.kit.max_leaf_weight_kg for c in matched)
                )
        if any(c.kit.class_authority is not None for c in matched):
            name = matched[0].kit.class_authority.class_name if matched[0].kit.class_authority is not None else matched[0].kit.name
            size = f"Hoja de {leaf_width_mm} × {leaf_height_mm} mm"
            if axis == "weight":
                message = f"{size}, {context.get('leaf_weight_kg')} kg: {name} admite hasta {context.get('kit_max_weight_kg')} kg. Usa la siguiente clase compatible o reduce el ancho."
            else:
                message = f"{size}: {name} admite ancho {context.get('kit_min_width_mm')}–{context.get('kit_max_width_mm')} mm y alto {context.get('kit_min_height_mm')}–{context.get('kit_max_height_mm')} mm. Ajusta la medida o divide la bahía."
            context["message"] = message
        else:
            message = f"No compatible hardware kit: {explicit_sku or opening.value}"
        raise NoCompatibleHardwareKit(message, context=context)
    if len(candidates) > 1 and all(c.kit.class_authority is not None for c in candidates):
        families = {c.kit.class_authority.family_code for c in candidates if c.kit.class_authority is not None}
        if len(families) == 1:
            priority = min(c.kit.class_authority.priority for c in candidates if c.kit.class_authority is not None)
            candidates = [c for c in candidates if c.kit.class_authority is not None and c.kit.class_authority.priority == priority]
    if len(candidates) != 1:
        raise AmbiguousHardwareKit(f"Ambiguous hardware kits: {opening.value}")
    return candidates[0].kit, candidates[0].exact_total_weight


def resolve_hardware_kit(
    *, opening: BayOpeningType, width_mm: Decimal, height_mm: Decimal,
    base_weight: ExactLeafWeight, params: SystemParams, explicit_sku: str | None = None,
) -> tuple[HardwareKitRule, ExactLeafWeight]:
    return resolve_hardware_evaluations(evaluate_hardware_candidates(
        opening=opening, width_mm=width_mm, height_mm=height_mm, base_weight=base_weight,
        params=params, explicit_sku=explicit_sku,
    ), opening=opening, explicit_sku=explicit_sku)
