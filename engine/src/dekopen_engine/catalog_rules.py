"""Pure catalog authorities for family compatibility and exact manufacturing."""

from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal

from dekopen_engine.models import (
    BayOpeningType, EffectiveProfileArticle, FittingPiece, ParametricNode, ProfileRole,
    MaterialType, RailType, SlidingSystemParameters, SystemFamily, SystemParams,
)
from dekopen_engine.weight import MissingFabricationAuthority
from dekopen_engine.openings import geometry_opening_type

SLIDING_OPENINGS = frozenset({BayOpeningType.SLIDING, BayOpeningType.SLIDING_2L,
                             BayOpeningType.SLIDING_3L, BayOpeningType.SLIDING_4L})
FAMILY_OPENINGS = {
    SystemFamily.CASEMENT: frozenset({BayOpeningType.FIXED, BayOpeningType.TURN_LEFT,
        BayOpeningType.TURN_RIGHT, BayOpeningType.TILT_TURN_LEFT,
        BayOpeningType.TILT_TURN_RIGHT, BayOpeningType.AWNING}),
    SystemFamily.SLIDING: SLIDING_OPENINGS | {BayOpeningType.FIXED},
    SystemFamily.LIFT_SLIDE: SLIDING_OPENINGS | {BayOpeningType.FIXED},
    SystemFamily.DOOR: frozenset({BayOpeningType.FIXED, BayOpeningType.DOOR_ENTRY,
                                 BayOpeningType.DOOR_DOUBLE}),
    SystemFamily.FACADE_FIXED: frozenset({BayOpeningType.FIXED}),
}
FAMILY_NAMES = {SystemFamily.CASEMENT: "practicable", SystemFamily.SLIDING: "corredera",
                SystemFamily.LIFT_SLIDE: "elevable", SystemFamily.DOOR: "puerta de entrada",
                SystemFamily.FACADE_FIXED: "fijos de gran formato"}


class CatalogRuleError(ValueError):
    def __init__(self, code: str, message: str, params: dict[str, str]) -> None:
        super().__init__(message)
        self.code = code
        self.params = {**params, "reason": message}


def validate_family(root: ParametricNode, params: SystemParams) -> None:
    if params.system_family is None:  # Only pre-family snapshot replay.
        return
    allowed = FAMILY_OPENINGS[params.system_family]
    pending = [root]
    while pending:
        node = pending.pop()
        pending.extend(node.children)
        opening = geometry_opening_type(node)
        if opening is not None and opening not in allowed:
            compatible = [family.value for family, choices in FAMILY_OPENINGS.items()
                          if opening in choices]
            names = ", ".join(FAMILY_NAMES[SystemFamily(value)] for value in compatible)
            raise CatalogRuleError("system_family_incompatible",
                f"El sistema {params.system_code} es {FAMILY_NAMES[params.system_family]} "
                f"y no admite esta apertura. Elige un sistema de {names}.",
                {"bay": node.id, "system": params.system_code,
                 "family": params.system_family.value, "opening": opening.value,
                 "compatible_families": ",".join(compatible)})


def sliding_parameters(params: SystemParams) -> SlidingSystemParameters:
    if params.sliding is not None:
        return params.sliding
    if not params.uses_legacy_rules:
        raise MissingFabricationAuthority("Sin dato: faltan los parámetros de corredera del sistema.")
    # Legacy snapshots carry explicit flat values; missing values never acquire
    # a synthetic sliding allowance. This decoder does not authorize new rows.
    values = (params.pulley_height_mm, params.central_overlap_mm,
              params.sliding_lateral_clearance_mm, params.sliding_end_add_mm,
              params.sliding_glazing_deduction_width_mm,
              params.sliding_glazing_deduction_height_mm, params.rail_type)
    if any(value is None for value in values):
        raise MissingFabricationAuthority("Sin dato: la autoridad histórica de corredera está incompleta.")
    assert params.pulley_height_mm is not None and params.central_overlap_mm is not None
    assert params.sliding_lateral_clearance_mm is not None and params.sliding_end_add_mm is not None
    assert params.sliding_glazing_deduction_width_mm is not None
    assert params.sliding_glazing_deduction_height_mm is not None and params.rail_type is not None
    return SlidingSystemParameters(
        pulley_height_mm=params.pulley_height_mm, central_overlap_mm=params.central_overlap_mm,
        lateral_clearance_mm=params.sliding_lateral_clearance_mm, end_add_mm=params.sliding_end_add_mm,
        glazing_deduction_width_mm=params.sliding_glazing_deduction_width_mm,
        glazing_deduction_height_mm=params.sliding_glazing_deduction_height_mm,
        rail_type=params.rail_type,
        rail_count=params.rail_count if params.rail_count is not None else
                   1 if params.rail_type is RailType.MONO else 2,
        separate_rail=False, interlock_required=False,
    )


def leaf_profile_role(opening: BayOpeningType, params: SystemParams) -> ProfileRole:
    if params.uses_legacy_rules:
        return ProfileRole.SASH
    if opening in SLIDING_OPENINGS:
        return ProfileRole.SLIDING_SASH
    if opening in (BayOpeningType.DOOR_ENTRY, BayOpeningType.DOOR_DOUBLE):
        return ProfileRole.DOOR_SASH
    return ProfileRole.SASH


def rounded_profile_cut(length_mm: Decimal, article: EffectiveProfileArticle) -> Decimal:
    rule = article.cut_rule
    if rule is None:
        return length_mm
    modes = {"UP": ROUND_CEILING, "DOWN": ROUND_FLOOR, "NEAREST": ROUND_HALF_UP}
    return ((length_mm - rule.meeting_deduction_mm) / rule.cut_step_mm
            ).to_integral_value(rounding=modes[rule.rounding]) * rule.cut_step_mm


def validate_profile_authority(article: EffectiveProfileArticle, *, legacy: bool,
                               reinforced_member: bool) -> None:
    if legacy:
        return
    if article.cut_rule is None:
        raise MissingFabricationAuthority(f"Sin dato: falta la regla de corte de {article.sku}.")
    if reinforced_member and article.material is MaterialType.PVC and article.reinforcement_rule is None:
        raise MissingFabricationAuthority(f"Sin dato: falta la regla de refuerzo de {article.sku}.")


def reinforcement_sku(article: EffectiveProfileArticle) -> str | None:
    return (article.reinforcement_rule.reinforcement_sku
            if article.reinforcement_rule is not None else article.reinforcement_sku)


def reinforcement_required(article: EffectiveProfileArticle, length_mm: Decimal,
                           *, finish: str, is_foiled: bool) -> bool:
    rule = article.reinforcement_rule
    if rule is None:
        return True  # Historical behavior, only on legacy authorities.
    return (length_mm >= rule.minimum_length_mm or finish in rule.required_finishes
            or (is_foiled and rule.required_non_white))


def reinforcement_screws(article: EffectiveProfileArticle, steel_length_mm: Decimal,
                         *, qty: int, bay_id: str | None,
                         leaf_id: str | None) -> FittingPiece | None:
    rule = article.reinforcement_rule
    if rule is None:
        return None
    count = int((steel_length_mm / Decimal("1000") * rule.screws_per_m
                 ).to_integral_value(rounding=ROUND_CEILING)) * qty
    return FittingPiece(kind="REINFORCEMENT_SCREW", sku=rule.screw_sku, qty=count,
                        bay_id=bay_id, leaf_id=leaf_id)


def validate_leaf_limits(params: SystemParams, opening: BayOpeningType, *, bay_id: str,
                         width_mm: Decimal, height_mm: Decimal,
                         weight_kg: Decimal | None = None, check_weight: bool = False) -> None:
    rules = [rule for rule in params.dimensional_limits if rule.opening_type is opening]
    if not rules:
        if not params.uses_legacy_rules:
            raise MissingFabricationAuthority("Sin dato: faltan los límites de esta apertura en el catálogo.")
        return
    if len(rules) != 1:
        raise ValueError("El catálogo declara límites contradictorios para la apertura.")
    rule = rules[0]
    dimensions_ok = (rule.min_leaf_width_mm <= width_mm <= rule.max_leaf_width_mm
        and rule.min_leaf_height_mm <= height_mm <= rule.max_leaf_height_mm
        and rule.min_aspect_ratio <= height_mm / width_mm <= rule.max_aspect_ratio)
    if not dimensions_ok or (check_weight and rule.max_leaf_weight_kg is not None
                            and weight_kg is not None and weight_kg > rule.max_leaf_weight_kg):
        raise CatalogRuleError("system_dimensional_limit",
            "La hoja está fuera de los límites del sistema. Revisa sus medidas y la fuente del catálogo.",
            {"bay": bay_id, "source": rule.source, "leaf_width_mm": str(width_mm),
             "leaf_height_mm": str(height_mm), "min_width_mm": str(rule.min_leaf_width_mm),
             "max_width_mm": str(rule.max_leaf_width_mm), "min_height_mm": str(rule.min_leaf_height_mm),
             "max_height_mm": str(rule.max_leaf_height_mm), "min_aspect_ratio": str(rule.min_aspect_ratio),
             "max_aspect_ratio": str(rule.max_aspect_ratio),
             "max_weight_kg": str(rule.max_leaf_weight_kg) if rule.max_leaf_weight_kg is not None else ""})
    if check_weight and rule.max_leaf_weight_kg is not None and weight_kg is None:
        raise MissingFabricationAuthority("Sin dato: falta la masa de la hoja para verificar el límite del sistema.")
