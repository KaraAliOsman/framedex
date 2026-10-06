"""Catalog-defined hardware expansion, exact prices and sealed picking.

Rules are data, never executable expressions. Mass and cost are accumulated
before any display rounding; a missing mass cannot certify a class.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING
import json

from dekopen_engine.models import (
    HardwareClassAuthority, HardwareComponent, HardwareComponentRule,
    HardwareItem, HardwareKitRule, HardwareResolution, HardwareSelection,
)
from dekopen_engine.pricing import price_from_cost_and_margin

D = Decimal


def parse_hardware_class(raw: object) -> HardwareClassAuthority:
    if isinstance(raw, str):
        return HardwareClassAuthority.model_validate_json(raw)
    return HardwareClassAuthority.model_validate_json(json.dumps(raw, default=str, allow_nan=False))


@dataclass(frozen=True, slots=True)
class HardwareExpansion:
    contents: list[HardwareComponent]
    hardware_weight_kg: Decimal | None
    unknown_reasons: tuple[str, ...]
    resolution: HardwareResolution


class HardwareRuleViolation(ValueError):
    def __init__(self, message: str, axis: str) -> None:
        super().__init__(message)
        self.axis = axis


def _component(rule: HardwareComponentRule, *, width: Decimal, height: Decimal,
               base_weight: Decimal | None) -> HardwareComponent | None:
    count = rule.quantity
    quantity = D(count.base)
    reason = f"{count.base} unidades declaradas"
    if count.axis is not None:
        dimension = {"WIDTH": width, "HEIGHT": height, "PERIMETER": D(2)*(width+height),
                     "WEIGHT": base_weight}[count.axis]
        if dimension is None:
            raise HardwareRuleViolation("Sin dato: falta masa de hoja para la regla de cantidad.", "undecidable")
        assert count.threshold is not None and count.step is not None
        extra = (max(D(0), dimension-count.threshold)/count.step).to_integral_value(rounding=ROUND_CEILING)
        quantity += extra * count.increment
        axis_label = {"WIDTH": "ancho", "HEIGHT": "alto", "PERIMETER": "perímetro", "WEIGHT": "masa sin herraje"}[count.axis]
        reason = f"{count.base} + {count.increment} por cada {count.step} sobre {count.threshold}; {axis_label} = {dimension}"
    if quantity == 0:
        return None
    length = None
    if rule.length is not None:
        base = {"WIDTH": width, "HEIGHT": height, "PERIMETER": D(2)*(width+height),
                "FIXED": rule.length.fixed_mm}[rule.length.axis]
        assert base is not None
        length = base-rule.length.deduction_mm
        if length <= 0:
            raise HardwareRuleViolation(
                f"{rule.name}: largo {base} − {rule.length.deduction_mm} = {length} mm; aumenta la medida o revisa la fuente.", "length")
        reason += f"; largo {base} − {rule.length.deduction_mm} = {length} mm"
    mass = rule.weight_kg
    if rule.weight_kg_m is not None:
        assert length is not None
        mass = rule.weight_kg_m * length/D(1000)
    weight = None if mass is None else mass * quantity
    price_qty = quantity
    if rule.price_unit == "M":
        assert length is not None
        price_qty = quantity*length/D(1000)
    return HardwareComponent(sku=rule.sku, name=rule.name, qty=quantity,
        unit="unidad", category=rule.category, cut_length_mm=length, weight_kg=weight,
        purchasing_sku=rule.purchasing_sku, manufacturer_name=rule.manufacturer_name,
        price_unit=rule.price_unit, price_quantity=price_qty, reason=reason,
        source=rule.source, machining=rule.machining)


def expand_hardware(kit: HardwareKitRule, *, width_mm: Decimal, height_mm: Decimal,
                    base_weight_kg: Decimal | None, selection: HardwareSelection | None = None,
                    requested_handle_height_mm: Decimal | None = None) -> HardwareExpansion:
    authority = kit.class_authority
    if authority is None:
        raise ValueError("La expansión requiere autoridad de clase.")
    selection = selection or HardwareSelection()
    unknown = set(selection.option_codes) - {option.code for option in authority.options}
    if unknown:
        raise HardwareRuleViolation("La opción vendible no está declarada para esta clase. Elige una opción del catálogo.", "option")
    options = [option for option in authority.options if option.code in selection.option_codes]
    replacements = [sku for option in options for sku in option.replaces_skus]
    if len(replacements) != len(set(replacements)):
        raise HardwareRuleViolation("Dos opciones sustituyen el mismo componente. Elige una combinación compatible.", "option")
    rules = [rule for rule in authority.components if rule.sku not in replacements]
    rules.extend(rule for option in options for rule in option.components)
    if len({rule.sku for rule in rules}) != len(rules):
        raise HardwareRuleViolation("Las opciones repiten un componente. Revisa su combinación y fuente de catálogo.", "option")
    handle = None
    color = None
    height = minimum = maximum = None
    if authority.handles:
        code = selection.handle_code or authority.default_handle
        handle = next((item for item in authority.handles if item.code == code), None)
        if handle is None:
            raise HardwareRuleViolation("La manilla no está declarada para esta clase. Elige un modelo del catálogo.", "handle")
        color_code = selection.color_code or handle.default_color
        color = next((item for item in handle.colors if item.code == color_code), None)
        if color is None:
            raise HardwareRuleViolation("El color de manilla no está declarado. Elige un color con su artículo de catálogo.", "handle")
        minimum, maximum = handle.minimum_from_bottom_mm, height_mm-handle.minimum_from_top_mm
        height = requested_handle_height_mm
        if height is None:
            height = (height_mm/D(2) if handle.vertical_rule == "CENTER" else
                height_mm-handle.default_height_mm if handle.vertical_rule == "TOP_OFFSET" and handle.default_height_mm is not None
                else handle.default_height_mm)
        assert height is not None
        if handle.vertical_rule == "FIXED":
            minimum = maximum = handle.default_height_mm
        elif handle.vertical_rule == "TOP_OFFSET":
            assert handle.default_height_mm is not None
            minimum = maximum = height_mm-handle.default_height_mm
        assert minimum is not None and maximum is not None
        if not minimum <= height <= maximum:
            raise HardwareRuleViolation(
                f"Manilla a {height} mm desde la base; {handle.name} admite {minimum}–{maximum} mm. Ajusta la altura dentro del rango de su fuente.", "handle")
        rules.append(color.component)
    elif selection.handle_code is not None or selection.color_code is not None:
        raise HardwareRuleViolation("Esta clase no declara manilla de accionamiento.", "handle")
    contents = [item for rule in rules if (item := _component(rule, width=width_mm,
        height=height_mm, base_weight=base_weight_kg)) is not None]
    if not contents:
        raise HardwareRuleViolation("La clase no produce componentes para esta medida. Revisa las reglas del catálogo.", "length")
    reasons = tuple(f"missing_hardware_component_mass:{item.sku}" for item in contents if item.weight_kg is None)
    mass = None if reasons else sum((item.weight_kg for item in contents if item.weight_kg is not None), D(0))
    resolution = HardwareResolution(family_name=authority.family_name, class_name=authority.class_name,
        class_code=authority.class_code, source=authority.source, synthetic=authority.synthetic,
        width_mm=width_mm, height_mm=height_mm, exact_leaf_weight_kg=None,
        max_leaf_weight_kg=kit.max_leaf_weight_kg, min_leaf_width_mm=kit.min_leaf_width_mm,
        max_leaf_width_mm=kit.max_leaf_width_mm, min_leaf_height_mm=kit.min_leaf_height_mm,
        max_leaf_height_mm=kit.max_leaf_height_mm, handle_code=None if handle is None else handle.code,
        handle_name=None if handle is None else handle.name, handle_color=None if color is None else color.name,
        handle_color_code=None if color is None else color.code, handle_height_mm=height,
        handle_minimum_mm=minimum, handle_maximum_mm=maximum,
        options=[option.name for option in options], option_codes=[option.code for option in options])
    return HardwareExpansion(contents, mass, reasons, resolution)


def hardware_component_cost(item: HardwareComponent, rate: Decimal) -> Decimal:
    if item.price_unit is None or item.price_quantity is None:
        raise ValueError("Falta la base de precio del componente.")
    if rate < 0:
        raise ValueError("El costo unitario no puede ser negativo.")
    return item.price_quantity * rate


def hardware_cost(items: Sequence[HardwareItem], rates: Mapping[tuple[str, str], Decimal]) -> Decimal:
    total = D(0)
    for kit in items:
        if kit.resolution is None:
            total += rates[(kit.kit_sku, "KIT")] * kit.qty
        else:
            for component in kit.contents:
                assert component.price_unit is not None
                total += hardware_component_cost(component, rates[(component.sku, component.price_unit)]) * kit.qty
    return total


def hardware_sale_price(item: HardwareItem, rates: Mapping[tuple[str, str], Decimal], *,
                        waste_pct: Decimal, margin_pct: Decimal) -> Decimal:
    return hardware_total_sale_price([item], rates, waste_pct=waste_pct, margin_pct=margin_pct)


def hardware_total_sale_price(items: Sequence[HardwareItem], rates: Mapping[tuple[str, str], Decimal], *,
                              waste_pct: Decimal, margin_pct: Decimal) -> Decimal:
    if waste_pct < 0:
        raise ValueError("La merma no puede ser negativa.")
    return price_from_cost_and_margin(hardware_cost(items, rates)*(D(1)+waste_pct), margin_pct)


def hardware_price_delta(reference: Decimal, alternative: Decimal) -> Decimal:
    return alternative-reference


def hardware_picking(items: Sequence[tuple[HardwareItem, int, str]]) -> list[dict[str, object]]:
    """Sum sealed engine component counts, preserving length and source targets."""
    rows: dict[tuple[str, str, Decimal | None, str | None], dict[str, object]] = {}
    for kit, repetitions, target in items:
        if repetitions < 1:
            raise ValueError("El picking requiere cantidad positiva de posiciones.")
        for component in kit.contents:
            key = (component.sku, component.unit, component.cut_length_mm, component.source)
            row = rows.setdefault(key, {"sku": component.sku, "name": component.name,
                "unit": component.unit, "quantity": D(0), "cut_length_mm": component.cut_length_mm,
                "source": component.source, "targets": []})
            quantity = row["quantity"]
            assert isinstance(quantity, Decimal)
            row["quantity"] = quantity + component.qty * kit.qty * repetitions
            targets = row["targets"]
            assert isinstance(targets, list)
            targets.append(target)
    return sorted(rows.values(), key=lambda row: (str(row["name"]), str(row["sku"]), str(row["cut_length_mm"])))
