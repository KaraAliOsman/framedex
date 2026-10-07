"""Accessory quantities, suggestions and commercial sublines, all pure."""

from __future__ import annotations

from decimal import Decimal, localcontext
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict, cast, Literal

from dekopen_engine.extra_models import ExtraAuthority, ExtraContext, ExtraDefinition, ExtraFact, ExtraLine, ExtraRate, ExtraSelection, ExtraSuggestion
from dekopen_engine.commercial import quantize_currency, quantum, CommercialResult

if TYPE_CHECKING:
    from dekopen_engine.models import LeafOpeningFact, Opening, OpeningUse
    from dekopen_engine.glass_composition import GlassPrice, GlassProduct

D = Decimal


@dataclass(frozen=True)
class AccessoryLeaf:
    bay_id: str
    leaf_id: str | None
    width_mm: Decimal
    height_mm: Decimal
    opening: Opening
    use: OpeningUse


def position_price(base: Decimal, extras: list[ExtraLine] | tuple[ExtraLine, ...]) -> Decimal:
    with localcontext() as context:
        context.prec = 80
        return base + sum((item.total_price for item in extras),D(0))


def price_facts(authority: ExtraAuthority | None, facts: list[ExtraFact]) -> list[ExtraLine]:
    return [line(selected_definition(authority, ExtraSelection(code=fact.code), fact.scope),
        ExtraSelection(code=fact.code, zone=fact.zone), fact.quantity, width=fact.width_mm,
        height=fact.height_mm, bay_id=fact.bay_id, leaf_id=fact.leaf_id) for fact in facts]


def compatible(definition: ExtraDefinition, leaves: list[LeafOpeningFact] | list[AccessoryLeaf]) -> bool:
    return not definition.allowed_movements or any(leaf.opening.movement.value in definition.allowed_movements for leaf in leaves)


def selected_definition(authority: ExtraAuthority | None, selection: ExtraSelection, scope: str) -> ExtraDefinition:
    candidates = [item for item in authority.definitions if item.code == selection.code and item.scope == scope] if authority else []
    if len(candidates) != 1:
        raise ValueError("Sin dato: el extra no tiene una autoridad compatible; revisa el catálogo o Ajustes.")
    return candidates[0]


def line(definition: ExtraDefinition, selection: ExtraSelection, quantity: Decimal, *,
         width: Decimal | None = None, height: Decimal | None = None,
         bay_id: str | None = None, leaf_id: str | None = None) -> ExtraLine:
    rate: ExtraRate = definition
    if definition.basis == "ZONE":
        if selection.zone not in definition.zones:
            raise ValueError("Selecciona una zona con tarifas declaradas para el flete.")
        rate = definition.zones[selection.zone]
    elif selection.zone is not None:
        raise ValueError("Este extra no declara una tarifa por zona.")
    with localcontext() as context:
        context.prec = 80
        return ExtraLine(code=definition.code, name=definition.name, scope=definition.scope, kind=definition.kind,
            quantity=quantity, unit=definition.unit, cost_rate=rate.cost_rate, selling_rate=rate.selling_rate,
            total_cost=quantity * rate.cost_rate, total_price=quantity * rate.selling_rate,
            currency=definition.currency, source=definition.source, synthetic=definition.synthetic,
            width_mm=width, height_mm=height, bay_id=bay_id, leaf_id=leaf_id, sku=definition.sku,
            installation=definition.installation, zone=selection.zone)


def position_lines(authority: ExtraAuthority | None, selections: list[ExtraSelection], *,
                   width: Decimal, height: Decimal, leaves: list[LeafOpeningFact] | list[AccessoryLeaf]) -> list[ExtraLine]:
    result: list[ExtraLine] = []
    keys: set[tuple[str, str | None, str | None]] = set()
    covered: set[tuple[str, str | None, str | None]] = set()
    with localcontext() as context:
        context.prec = 80
        for selection in selections:
            key = (selection.code, selection.bay_id, selection.leaf_id)
            if key in keys:
                raise ValueError("No repitas el mismo extra sobre el mismo vano u hoja.")
            keys.add(key)
            definition = selected_definition(authority, selection, "POSITION")
            if selection.decision == "DISMISS":
                continue
            if not compatible(definition, leaves):
                raise ValueError("El extra no es compatible con la apertura de esta posición.")
            if definition.basis != "SIDES" and selection.sides:
                raise ValueError("Este extra no se aplica por lado.")
            if definition.basis == "SIDES" and selection.sides == []:
                raise ValueError("Elige al menos un lado o quita el extra.")
            if definition.basis != "SILL" and (selection.overhang_left_mm or selection.overhang_right_mm):
                raise ValueError("Solo el vierteaguas lleva vuelos.")
            if definition.basis != "LEAF" and (selection.bay_id is not None or selection.leaf_id is not None):
                raise ValueError("Este extra se aplica al vano completo.")
            if definition.basis == "LEAF":
                targets = [leaf for leaf in leaves if
                    (selection.bay_id is None or leaf.bay_id == selection.bay_id) and
                    (selection.leaf_id is None or leaf.leaf_id == selection.leaf_id) and
                    (not definition.allowed_movements or leaf.opening.movement.value in definition.allowed_movements)]
                if not targets:
                    raise ValueError("El extra no tiene una hoja compatible en esta posición.")
                for leaf in targets:
                    physical = (definition.code, leaf.bay_id, leaf.leaf_id)
                    if physical in covered:
                        raise ValueError("El extra ya cubre esta hoja mediante otra selección.")
                    covered.add(physical)
                    result.append(line(definition, selection, D(1), width=leaf.width_mm,
                        height=leaf.height_mm, bay_id=leaf.bay_id, leaf_id=leaf.leaf_id))
                continue
            quantity = {
                "SILL": lambda: (width + selection.overhang_left_mm + selection.overhang_right_mm) / D(1000),
                "SIDES": lambda: sum((width if side in {"TOP", "BOTTOM"} else height
                    for side in (definition.default_sides if selection.sides is None else selection.sides)), D(0)) / D(1000),
                "AREA": lambda: width * height / D(1000000),
                "PERIMETER": lambda: D(2) * (width + height) / D(1000),
                # WINDOW covers this complete frame, including divided bays.
                # LEAF above covers individual leaves; assemblies evaluate
                # WINDOW once per module, never once per internal division.
                "WINDOW": lambda: D(1), "PER_POSITION": lambda: D(1),
                "FIXED": lambda: D(1), "ZONE": lambda: D(1),
            }[definition.basis]()
            result.append(line(definition, selection, quantity, width=width, height=height))
    if sum(item.installation for item in result) > 1:
        raise ValueError("Selecciona una sola regla de instalación para la posición.")
    return result


def suggestions(authority: ExtraAuthority | None, selections: list[ExtraSelection], *, width: Decimal,
                height: Decimal, leaves: list[LeafOpeningFact] | list[AccessoryLeaf], context: ExtraContext | None) -> list[ExtraSuggestion]:
    result = []
    decided = {item.code for item in selections}
    for definition in authority.definitions if authority else []:
        if definition.scope != "POSITION" or definition.code in decided or not compatible(definition, leaves):
            continue
        cause = ""
        if definition.suggestion == "WINDOW" and any(leaf.use.value == "WINDOW" for leaf in leaves):
            cause = "La posición contiene una ventana; revisa si la fachada necesita vierteaguas."
        elif definition.suggestion == "MOVING_LEAF" and any(leaf.opening.movement.value != "FIXED" for leaf in leaves):
            cause = "Hay hojas móviles compatibles; puedes proteger su abertura con este accesorio."
        elif definition.suggestion == "OPENING_GAP" and context is not None:
            dw = (context.opening_width_mm - width) if context.opening_width_mm is not None else D(0)
            dh = (context.opening_height_mm - height) if context.opening_height_mm is not None else D(0)
            if dw > 0 or dh > 0:
                cause = f"El vano de obra declarado excede el marco en {dw} mm de ancho y {dh} mm de alto; revisa los ensanches."
        if cause:
            result.append(ExtraSuggestion(name=definition.name, cause=cause, source=definition.source,
                selection=ExtraSelection(code=definition.code, sides=definition.default_sides,
                    overhang_left_mm=definition.default_overhang_mm if definition.basis == "SILL" else D(0),
                    overhang_right_mm=definition.default_overhang_mm if definition.basis == "SILL" else D(0))))
    return result


def project_lines(authority: ExtraAuthority, selections: list[ExtraSelection],
                  positions: list[tuple[Decimal, Decimal, int]]) -> list[ExtraLine]:
    result = []
    if len({item.code for item in selections}) != len(selections):
        raise ValueError("No repitas un servicio del proyecto.")
    if not positions:
        raise ValueError("Agrega una posición antes de calcular los servicios.")
    with localcontext() as context:
        context.prec = 80
        for selection in selections:
            definition = selected_definition(authority, selection, "PROJECT")
            if selection.decision == "DISMISS":
                continue
            if selection.sides or selection.bay_id or selection.leaf_id or selection.overhang_left_mm or selection.overhang_right_mm:
                raise ValueError("El servicio del proyecto solo admite su regla y la zona declarada.")
            quantity = {"AREA": lambda: sum((w*h*qty/D(1000000) for w,h,qty in positions), D(0)),
                "PERIMETER": lambda: sum((D(2)*(w+h)*qty/D(1000) for w,h,qty in positions), D(0)),
                "PER_POSITION": lambda: D(sum(qty for _,_,qty in positions)),
                "FIXED": lambda: D(1), "ZONE": lambda: D(1)}[definition.basis]()
            result.append(line(definition, selection, quantity))
    if sum(item.installation for item in result) > 1:
        raise ValueError("Selecciona una sola regla de instalación para el proyecto.")
    return result


class PricePartition(TypedDict):
    base_net: str
    sublines: list[dict[str, str | bool | None]]


def partition_price(total: Decimal, base: Decimal, extras: list[tuple[ExtraLine, Decimal]], *,
                    quantity: int, currency: str) -> PricePartition:
    """Largest remainder in the currency quantum. Base+sublines = sealed net.

    The unit tariff remains exact; the subline records its rounding allocation
    so displaying quantity×tariff never conceals a rounding difference.
    """
    with localcontext() as context:
        context.prec = 80
        weights = [base, *(amount for _, amount in extras)]
        weight = sum(weights, D(0))
        if weight <= 0 or any(value < 0 for value in weights):
            raise ValueError("Falta autoridad de precio para distribuir las sublíneas.")
        q = quantum(currency)
        exact = [total*value/weight for value in weights]
        amounts = [(value//q)*q for value in exact]
        remainder = int((total-sum(amounts, D(0)))/q)
        order = sorted(range(len(exact)), key=lambda i: (-(exact[i]-amounts[i]), i))
        for index in order[:remainder]:
            amounts[index] += q
        sublines: list[dict[str, str | bool | None]] = []
        for index, (item, _) in enumerate(extras, 1):
            count = item.quantity*quantity
            tariff = quantize_currency(exact[index]/count, currency)
            sublines.append({"code": item.code, "name": item.name, "quantity": str(count),
                "unit": item.unit, "unit_price": str(tariff), "net": str(amounts[index]),
                "rounding": str(amounts[index]-count*tariff), "source": item.source,
                "synthetic": item.synthetic, "width_mm": None if item.width_mm is None else str(item.width_mm),
                "height_mm": None if item.height_mm is None else str(item.height_mm)})
        assert amounts[0] + sum((D(str(row["net"])) for row in sublines), D(0)) == total
        return {"base_net": str(amounts[0]), "sublines": sublines}


def service_price(item: ExtraLine, currency: str) -> dict[str, object]:
    amount = quantize_currency(item.total_price, currency)
    with localcontext() as context:
        context.prec = 80
        tariff = quantize_currency(item.selling_rate, currency)
        return {**item.model_dump(mode="json"), "unit_price":str(tariff), "amount": str(amount), "rounding": str(amount-item.quantity*tariff)}


def target_services(costs: list[tuple[int, Decimal]], services: list[ExtraLine], margin: Decimal,
                    currency: str, tax_rate: Decimal, legacy_extras: list[Decimal]) -> tuple[CommercialResult, list[dict[str, object]]]:
    """Allocate one project margin across positions and services, without drift."""
    from dekopen_engine.commercial import target_project, totals
    offset = max(index for index, _ in costs)
    combined = target_project([*costs, *((offset+i, item.total_cost) for i, item in enumerate(services, 1))],
                              margin, currency, tax_rate)
    allocated = dict(combined.lines)
    rows: list[dict[str, object]] = []
    with localcontext() as context:
        context.prec = 80
        for index, item in enumerate(services, 1):
            amount = allocated[offset+index]
            tariff = quantize_currency(amount/item.quantity, currency)
            rows.append({**item.model_dump(mode="json"), "amount": str(amount),
                         "selling_rate": str(tariff), "unit_price":str(tariff), "rounding": str(amount-item.quantity*tariff)})
    return totals([(index, allocated[index]) for index, _ in costs], currency, tax_rate,
                  [*legacy_extras, *(allocated[offset+i] for i in range(1,len(services)+1))]), rows


def glass_bar_lines(priced: GlassPrice, product: GlassProduct | None, *, bay_id: str,
                    currency: str, waste: Decimal, margin: Decimal) -> list[ExtraLine]:
    """D02's declared grid quantities and supplier tariffs, without a second BOM."""
    from dekopen_engine.commercial import fraction
    fraction(waste)
    fraction(margin,margin=True)
    rows = []
    with localcontext() as context:
        context.prec = 80
        for index, charge in enumerate(priced.charges):
            if charge.kind not in {'Palillaje por metro','Cruce de palillaje'}:
                continue
            if product is None or not product.billing.source:
                raise ValueError('Sin dato: el palillaje requiere la fuente y tarifas de la receta de vidrio.')
            rate = charge.unit_cost*(D(1)+waste)
            selling = rate/(D(1)-margin)
            rows.append(ExtraLine(code=f'GLASS-BARS-{bay_id}-{index}',name=charge.kind,scope='POSITION',kind='SERVICE',
                quantity=charge.quantity,unit=charge.unit,currency=cast(Literal['CLP','USD'],currency),cost_rate=rate,selling_rate=selling,
                total_cost=rate*charge.quantity,total_price=selling*charge.quantity,source=product.billing.source,
                synthetic=product.synthetic,bay_id=bay_id,sku=charge.sku,installation=False))
    return rows
