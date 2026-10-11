"""Strict, sourced advanced recipes and Decimal physical projections.

The catalog owns manufacturing deductions and kinematics. Plan projection is
presentation geometry; trigonometry never changes a cut or a glass dimension.
"""

from __future__ import annotations

from collections.abc import Callable
from decimal import Context, Decimal, localcontext
from functools import wraps
from typing import ParamSpec, TypeVar

from .models import (
    AdvancedOpeningRecipe,
    AdvancedPanel,
    HingeSide,
    OpeningCapability,
    OpeningMovement,
    OpeningPlanPoint,
    OpeningUse,
    ParametricNode,
    SystemFamily,
    SystemParams,
)
from .trig import cos_degrees, sin_degrees

ADVANCED_MOVEMENTS = frozenset(
    {
        OpeningMovement.LIFT_SLIDE,
        OpeningMovement.PARALLEL_SLIDE,
        OpeningMovement.FOLD,
        OpeningMovement.PIVOT_V,
        OpeningMovement.PIVOT_H,
        OpeningMovement.VERTICAL_SLIDE,
    }
)
ADVANCED_NAMES = {
    OpeningMovement.LIFT_SLIDE: "Elevable-corredera (HST)",
    OpeningMovement.PARALLEL_SLIDE: "Osciloparalela (PSK)",
    OpeningMovement.FOLD: "Plegable",
    OpeningMovement.PIVOT_V: "Pivotante vertical",
    OpeningMovement.PIVOT_H: "Pivotante horizontal",
    OpeningMovement.VERTICAL_SLIDE: "Guillotina",
}

# Advanced recipes have exact finite authored shares and presentation square
# roots. Their transport cannot depend on a caller's monetary Decimal context.
# This precision preserves the sourced shares before a catalog cut-step rule
# is applied; kinematic projections never feed manufacturing dimensions.
ADVANCED_GEOMETRY_CONTEXT = Context(prec=80)
_P = ParamSpec("_P")
_T = TypeVar("_T")


def recipe_geometry_context(function: Callable[_P, _T]) -> Callable[_P, _T]:
    """Preserve the geometry signature and source while isolating new recipes."""
    @wraps(function)
    def calculate(*args: _P.args, **kwargs: _P.kwargs) -> _T:
        root = kwargs.get("root", args[0] if args else None)
        if isinstance(root, ParametricNode) and has_advanced_opening(root):
            with localcontext(ADVANCED_GEOMETRY_CONTEXT):
                return function(*args, **kwargs)
        return function(*args, **kwargs)

    return calculate


def has_advanced_opening(node: ParametricNode) -> bool:
    return (
        node.opening_recipe_code is not None
        or node.opening is not None
        and requires_recipe(node.opening.movement, node.opening_use or OpeningUse.WINDOW)
        or any(has_advanced_opening(child) for child in node.children)
    )


def requires_recipe(movement: OpeningMovement, use: OpeningUse) -> bool:
    return movement in ADVANCED_MOVEMENTS or (
        movement is OpeningMovement.SLIDE and use is OpeningUse.DOOR
    )


def capability_family(movement: OpeningMovement, use: OpeningUse) -> SystemFamily | None:
    if use is OpeningUse.DOOR:
        return SystemFamily.DOOR
    if movement is OpeningMovement.LIFT_SLIDE:
        return SystemFamily.LIFT_SLIDE
    if movement in (OpeningMovement.SLIDE, OpeningMovement.VERTICAL_SLIDE):
        return SystemFamily.SLIDING
    if movement is OpeningMovement.FIXED:
        return None
    return SystemFamily.CASEMENT


def validate_capability_recipes(capability: OpeningCapability) -> None:
    advanced = requires_recipe(capability.movement, capability.use)
    if advanced != bool(capability.advanced_recipes):
        raise ValueError(
            "La apertura avanzada exige recetas con autoridad; una básica no las admite."
        )
    if not advanced:
        return
    if capability.leaf_role.value != "SINGLE" or capability.fixed_in_sash:
        raise ValueError("Los paneles avanzados se componen por receta, sin alias activo/pasivo.")
    if capability.hinge_sides != (HingeSide.NONE,):
        raise ValueError("La receta declara sus ejes y cierre; no infiere una bisagra lateral.")
    if capability.handle_rule is None:
        raise ValueError("La apertura avanzada requiere regla de manilla con fuente.")
    codes = [recipe.code for recipe in capability.advanced_recipes]
    if len(codes) != len(set(codes)):
        raise ValueError("Las recetas deben tener códigos distintos.")
    movement = capability.movement
    for recipe in capability.advanced_recipes:
        if (set(recipe.hardware_kit_skus) | set(recipe.pass_through_hardware_kit_skus)) - set(
            capability.hardware_kit_skus
        ):
            raise ValueError("Los kits de la receta deben pertenecer a la capacidad.")
        moving = [panel for panel in recipe.panels if panel.kind == "MOVING"]
        if movement in (
            OpeningMovement.LIFT_SLIDE,
            OpeningMovement.PARALLEL_SLIDE,
            OpeningMovement.SLIDE,
        ):
            if recipe.distribution_axis != "X" or any(
                panel.track is None or panel.travel not in ("LEFT", "RIGHT") for panel in moving
            ):
                raise ValueError("La corredera declara carril y recorrido horizontal por hoja.")
        if movement is OpeningMovement.LIFT_SLIDE and (
            recipe.lift_mm is None or recipe.threshold_height_mm is None
        ):
            raise ValueError("La elevable necesita elevación y umbral específicos.")
        if movement is OpeningMovement.PARALLEL_SLIDE and recipe.parallel_offset_mm is None:
            raise ValueError("La osciloparalela necesita la separación paralela de su fuente.")
        if (
            capability.use is OpeningUse.DOOR
            and movement is OpeningMovement.SLIDE
            and recipe.threshold_height_mm is None
        ):
            raise ValueError("La puerta corredera requiere su umbral.")
        if movement is OpeningMovement.FOLD:
            if (
                recipe.distribution_axis != "X"
                or recipe.rail_profile_role is None
                or recipe.packet_pitch_mm is None
            ):
                raise ValueError("La plegable declara guías y espesor del paquete.")
            if any(
                panel.fold_group is None
                or panel.fold_index is None
                or panel.stack_side is None
                or panel.travel is not None
                or panel.track is not None
                for panel in moving
            ):
                raise ValueError("Cada hoja plegable declara grupo, orden y lado del paquete.")
            for group in {panel.fold_group for panel in moving}:
                panels = [panel for panel in moving if panel.fold_group == group]
                if sorted(
                    panel.fold_index for panel in panels if panel.fold_index is not None
                ) != list(range(len(panels))):
                    raise ValueError("El orden de cada paquete plegable debe ser continuo.")
                if len({panel.stack_side for panel in panels}) != 1:
                    raise ValueError("Las hojas de un paquete deben plegar al mismo lado.")
                slots = [recipe.panels.index(panel) for panel in panels]
                expected = list(range(len(panels)))
                if panels[0].stack_side == "RIGHT":
                    expected.reverse()
                if (
                    slots != list(range(min(slots), max(slots) + 1))
                    or [panel.fold_index for panel in panels] != expected
                ):
                    raise ValueError(
                        "El paquete declara hojas contiguas y orden desde su borde de anclaje."
                    )
                if any(
                    panel.pass_through and panel.fold_index != len(panels) - 1 for panel in panels
                ):
                    raise ValueError("La hoja de paso debe estar en el extremo libre del paquete.")
        elif any(
            panel.fold_group is not None
            or panel.fold_index is not None
            or panel.stack_side is not None
            or panel.pass_through
            for panel in moving
        ):
            raise ValueError("La hoja de paso y el paquete pertenecen a una plegable.")
        if movement in (OpeningMovement.PIVOT_V, OpeningMovement.PIVOT_H):
            if (
                len(recipe.panels) != 1
                or moving[0].pivot_fraction is None
                or moving[0].track is not None
            ):
                raise ValueError("La pivotante declara un eje desplazado por hoja.")
        elif any(panel.pivot_fraction is not None for panel in moving):
            raise ValueError("El eje desplazado pertenece a una pivotante.")
        if movement is OpeningMovement.VERTICAL_SLIDE:
            if recipe.distribution_axis != "Y" or any(
                panel.track is None or panel.travel not in ("UP", "DOWN") or panel.balance is None
                for panel in moving
            ):
                raise ValueError(
                    "La guillotina declara recorrido vertical, plano y balance por hoja."
                )
        elif any(panel.balance is not None for panel in moving):
            raise ValueError("El balance pertenece a una guillotina.")
        if movement in (OpeningMovement.PIVOT_V, OpeningMovement.PIVOT_H) and any(
            panel.travel is not None for panel in moving
        ):
            raise ValueError("El pivote declara rotación, sin recorrido de corredera.")
        if (
            movement not in (OpeningMovement.PIVOT_V, OpeningMovement.PIVOT_H)
            and recipe.rail_profile_role is None
        ):
            raise ValueError("La apertura guiada requiere su perfil de guía.")
        if movement is not OpeningMovement.FOLD and recipe.packet_pitch_mm is not None:
            raise ValueError("Solo la plegable declara espesor del paquete.")
        if movement is not OpeningMovement.LIFT_SLIDE and recipe.lift_mm is not None:
            raise ValueError("Solo la elevable declara elevación.")
        if movement is not OpeningMovement.PARALLEL_SLIDE and recipe.parallel_offset_mm is not None:
            raise ValueError("Solo la osciloparalela declara separación paralela.")


def validate_recipe_bindings(cap: OpeningCapability, params: SystemParams) -> None:
    for recipe in cap.advanced_recipes:
        roles: set[str] = {recipe.leaf_profile_role}
        if recipe.rail_profile_role is not None:
            roles.add(recipe.rail_profile_role)
        if recipe.threshold_height_mm is not None:
            roles.add("THRESHOLD")
        if recipe.interlock_required:
            roles.add("INTERLOCK")
        if not roles.issubset({role.value for role in params.effective_profile_articles}):
            raise ValueError("Sin dato: faltan perfiles específicos de la receta avanzada.")
        for sku in (*recipe.hardware_kit_skus, *recipe.pass_through_hardware_kit_skus):
            kit = next((kit for kit in params.available_hardware_kits if kit.sku == sku), None)
            expected = "SLIDING" if cap.movement is OpeningMovement.SLIDE else cap.movement.value
            if kit is None or kit.opening_type != expected or kit.class_authority is None:
                raise ValueError(
                    "Sin dato: la receta avanzada requiere un herraje específico con autoridad de clase."
                )
            if cap.movement in (
                OpeningMovement.LIFT_SLIDE,
                OpeningMovement.PARALLEL_SLIDE,
                OpeningMovement.FOLD,
                OpeningMovement.SLIDE,
            ):
                if (
                    kit.carriages_qty <= 0
                    or kit.carriage_capacity_kg is None
                    or kit.carriage_capacity_kg <= 0
                    or kit.max_leaf_weight_kg > kit.carriage_capacity_kg * kit.carriages_qty
                ):
                    raise ValueError(
                        "Sin dato: los carros requieren cantidad y capacidad coherentes con el peso de hoja."
                    )
            if cap.movement is OpeningMovement.PARALLEL_SLIDE and kit.stay_arms_qty <= 0:
                raise ValueError("Sin dato: la osciloparalela requiere compases declarados.")


def resolve_recipe(node: ParametricNode, params: SystemParams) -> AdvancedOpeningRecipe | None:
    from .openings import OpeningCapabilityError, node_use, resolve_capability

    if node.opening is None or not requires_recipe(node.opening.movement, node_use(node)):
        if node.opening_recipe_code is not None:
            raise OpeningCapabilityError(
                "La receta no corresponde a esta apertura. Elige una apertura avanzada del catálogo.",
                bay=node.id,
            )
        return None
    cap = resolve_capability(node, params)
    assert cap is not None
    matches = [recipe for recipe in cap.advanced_recipes if recipe.code == node.opening_recipe_code]
    if len(matches) != 1:
        raise OpeningCapabilityError(
            "Sin dato: elige un esquema avanzado declarado en el catálogo del sistema.", bay=node.id
        )
    if (
        node.opening_type is not None
        or node.hinged_layout is not None
        or node.sliding_layout is not None
    ):
        raise OpeningCapabilityError(
            "La receta avanzada conserva su composición; retira el alias o composición histórica.",
            bay=node.id,
        )
    return matches[0]


def validate_recipe_limits(
    recipe: AdvancedOpeningRecipe,
    *,
    bay_id: str,
    width_mm: Decimal,
    height_mm: Decimal,
    weight_kg: Decimal | None = None,
    check_weight: bool = False,
) -> None:
    from .catalog_rules import CatalogRuleError
    from .weight import MissingFabricationAuthority

    if (
        not recipe.min_leaf_width_mm <= width_mm <= recipe.max_leaf_width_mm
        or not recipe.min_leaf_height_mm <= height_mm <= recipe.max_leaf_height_mm
        or check_weight
        and weight_kg is not None
        and weight_kg > recipe.max_leaf_weight_kg
    ):
        raise CatalogRuleError(
            "system_dimensional_limit",
            "La hoja está fuera de los límites de la receta avanzada. Revisa medidas, peso y fuente del catálogo.",
            {
                "bay": bay_id,
                "source": recipe.source,
                "leaf_width_mm": str(width_mm),
                "leaf_height_mm": str(height_mm),
                "min_width_mm": str(recipe.min_leaf_width_mm),
                "max_width_mm": str(recipe.max_leaf_width_mm),
                "min_height_mm": str(recipe.min_leaf_height_mm),
                "max_height_mm": str(recipe.max_leaf_height_mm),
                "max_weight_kg": str(recipe.max_leaf_weight_kg),
            },
        )
    if check_weight and weight_kg is None:
        raise MissingFabricationAuthority(
            "Sin dato: falta la masa de la hoja avanzada para verificar el límite de su receta."
        )


def plan_endpoints(
    movement: OpeningMovement,
    panel: AdvancedPanel,
    *,
    x: Decimal,
    width: Decimal,
    travel_mm: Decimal,
    angle_deg: Decimal,
    inward: bool,
    parallel_offset_mm: Decimal | None = None,
    fold_start: OpeningPlanPoint | None = None,
    packet_pitch_mm: Decimal | None = None,
) -> tuple[OpeningPlanPoint, OpeningPlanPoint]:
    depth = panel.plane_offset_mm
    sign = Decimal(1) if inward else Decimal(-1)
    start, end = (
        OpeningPlanPoint(x_mm=x, depth_mm=depth),
        OpeningPlanPoint(x_mm=x + width, depth_mm=depth),
    )
    if panel.kind == "FIXED":
        return start, end
    if movement in (
        OpeningMovement.SLIDE,
        OpeningMovement.LIFT_SLIDE,
        OpeningMovement.PARALLEL_SLIDE,
    ):
        dx = travel_mm * (-1 if panel.travel == "LEFT" else 1)
        dz = sign * (parallel_offset_mm or Decimal(0))
        return (
            OpeningPlanPoint(x_mm=x + dx, depth_mm=depth + dz),
            OpeningPlanPoint(x_mm=x + width + dx, depth_mm=depth + dz),
        )
    cos = Decimal(0) if angle_deg == 90 else cos_degrees(angle_deg)
    sin = Decimal(1) if angle_deg == 90 else sin_degrees(angle_deg)
    if movement is OpeningMovement.PIVOT_V:
        assert panel.pivot_fraction is not None
        pivot = x + width * panel.pivot_fraction
        left = -width * panel.pivot_fraction
        right = width * (1 - panel.pivot_fraction)
        return (
            OpeningPlanPoint(x_mm=pivot + left * cos, depth_mm=depth + left * sin * sign),
            OpeningPlanPoint(x_mm=pivot + right * cos, depth_mm=depth + right * sin * sign),
        )
    if movement is OpeningMovement.FOLD:
        assert (
            panel.fold_index is not None and panel.stack_side is not None and fold_start is not None
        )
        horizontal = -1 if panel.stack_side == "RIGHT" else 1
        alternating = -1 if panel.fold_index % 2 else 1
        assert packet_pitch_mm is not None
        if packet_pitch_mm >= width:
            raise ValueError("El espesor del paquete debe ser menor que el ancho de cada hoja.")
        projection = max(width * cos, packet_pitch_mm)
        depth_projection = (width * width - projection * projection).sqrt()
        other = OpeningPlanPoint(
            x_mm=fold_start.x_mm + projection * horizontal,
            depth_mm=fold_start.depth_mm + depth_projection * sign * alternating,
        )
        return (other, fold_start) if horizontal == -1 else (fold_start, other)
    # A horizontal pivot and vertical slider stay in the same plan footprint;
    # their actual vertical displacement/elevation is carried in the leaf fact.
    return start, end


def passage_endpoints(
    panel: AdvancedPanel, *, x: Decimal, width: Decimal, angle_deg: Decimal, inward: bool
) -> tuple[OpeningPlanPoint, OpeningPlanPoint] | None:
    """Independent access leaf rotation while the folding packet stays closed."""
    if not panel.pass_through:
        return None
    closing_right = panel.closing_side is HingeSide.RIGHT
    anchor = x if closing_right else x + width
    sign = Decimal(1) if inward else Decimal(-1)
    horizontal = Decimal(1) if closing_right else Decimal(-1)
    cos = Decimal(0) if angle_deg == 90 else cos_degrees(angle_deg)
    sin = Decimal(1) if angle_deg == 90 else sin_degrees(angle_deg)
    hinge = OpeningPlanPoint(x_mm=anchor, depth_mm=panel.plane_offset_mm)
    free = OpeningPlanPoint(
        x_mm=anchor + horizontal * width * cos, depth_mm=panel.plane_offset_mm + width * sin * sign
    )
    return (hinge, free) if closing_right else (free, hinge)
