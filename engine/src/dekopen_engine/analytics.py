"""Exact analytical readings over resolved, immutable domain evidence.

No inferred cost, labor time or manufacturing loss. A physical remnant is
valued once, as stock consumed by its receiving order; reusable output is
credited explicitly at closure. Money keeps its original currency.
"""

from collections.abc import Mapping, Sequence
from decimal import Decimal, localcontext
from typing import Any, overload

D = Decimal
ZERO = D(0)


def number(value: object, *, signed: bool = False) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError("invalid_analytics_number")
    result = D(str(value))
    if not result.is_finite() or (not signed and result < ZERO):
        raise ValueError("invalid_analytics_number")
    return result


@overload
def decimal_text(value: None) -> None: ...


@overload
def decimal_text(value: object) -> str: ...


def decimal_text(value: object | None) -> str | None:
    """Exact, editable wire text; Decimal exponent notation is not UI input."""
    return format(number(value, signed=True), "f") if value is not None else None


def ratio(numerator: object, denominator: object) -> str | None:
    with localcontext() as context:
        context.prec = 256
        top, bottom = number(numerator, signed=True), number(denominator)
        return decimal_text(top / bottom) if bottom else None


def total(values: Sequence[object | None]) -> str | None:
    if not values or any(value is None for value in values):
        return None
    with localcontext() as context:
        context.prec = 256
        return decimal_text(sum((number(value, signed=True) for value in values), ZERO))


def average(values: Sequence[object | None]) -> str | None:
    value = total(values)
    return ratio(value, len(values)) if value is not None else None


def remnant_quantity(*, kind: str, length_mm: object, width_mm: object, height_mm: object) -> str:
    """Physical stock conversion to the same M/M2 cost units as the ledger."""
    with localcontext() as context:
        context.prec = 256
        if kind == "BAR":
            return decimal_text(number(length_mm) / D(1000))
        if kind == "SHEET":
            return decimal_text(number(width_mm) * number(height_mm) / D(1000000))
        raise ValueError("invalid_remnant_kind")


def actual_cost(
    *,
    materials: Sequence[Mapping[str, Any]],
    labor: Sequence[Mapping[str, Any]],
    other: object | None,
    credit: object | None,
    closed: bool,
) -> dict[str, Any]:
    """Quantities come from the ledger, rates/hours from signed evidence.

    SCRAP movements are additional stock destroyed, not waste already included
    in a CONSUMPTION movement. A waste quantity inside consumption allocates
    that same cost; it never adds a second cost. RETURN is negative. Credits
    refer only to reusable stock produced by this OT, never discarded waste.
    """
    causes = []
    if not closed:
        causes.append("Falta confirmar el cierre de costos de la OT.")
    if not materials:
        causes.append("No hay consumos de inventario ligados a la OT.")
    if any(m.get("unit_cost") is None or m.get("waste_quantity") is None for m in materials):
        causes.append("Falta valorar consumos, devoluciones, merma o retazos.")
    if not labor or any(s.get("hours") is None or s.get("hourly_rate") is None for s in labor):
        causes.append("Faltan horas laborales y su tarifa por estación.")
    if other is None:
        causes.append("Faltan los servicios y otros costos reales, incluso su declaración de cero.")
    if credit is None:
        causes.append(
            "Falta valorar el material reutilizable producido, incluso su declaración de cero."
        )
    if causes:
        return {
            "cost": None,
            "materials": None,
            "waste": None,
            "labor": None,
            "other": None,
            "credit": None,
            "lines": [],
            "causes": causes,
        }
    with localcontext() as context:
        context.prec = 256
        material, waste, hours_cost = ZERO, ZERO, ZERO
        lines = []
        for m in materials:
            quantity, rate = number(m["quantity"]), number(m["unit_cost"])
            lost = number(m["waste_quantity"])
            kind = m["kind"]
            if kind not in {"CONSUMPTION", "SCRAP", "RETURN", "REMNANT"}:
                raise ValueError("invalid_consumption_kind")
            if lost > quantity or (kind == "RETURN" and lost):
                raise ValueError("invalid_waste_quantity")
            if kind == "SCRAP" and lost != quantity:
                raise ValueError("scrap_must_be_all_waste")
            sign = -D(1) if kind == "RETURN" else D(1)
            amount, loss = quantity * rate * sign, lost * rate
            material += amount
            waste += loss
            lines.append(
                {
                    "id": m["id"],
                    "kind": kind,
                    "amount": decimal_text(amount),
                    "waste": decimal_text(loss),
                    "quantity": decimal_text(quantity),
                    "unit_cost": decimal_text(rate),
                }
            )
        for station in labor:
            amount = number(station["hours"]) * number(station["hourly_rate"])
            hours_cost += amount
            lines.append(
                {
                    "id": station["id"],
                    "kind": "LABOR",
                    "amount": decimal_text(amount),
                    "hours": decimal_text(number(station["hours"])),
                    "hourly_rate": decimal_text(number(station["hourly_rate"])),
                }
            )
        services, stock_credit = number(other), number(credit)
        if material < ZERO or stock_credit > material - waste:
            raise ValueError("actual_cost_credit_bounds")
        return {
            "cost": decimal_text(material + hours_cost + services - stock_credit),
            "materials": decimal_text(material - waste - stock_credit),
            "waste": decimal_text(waste),
            "labor": decimal_text(hours_cost),
            "other": decimal_text(services),
            "credit": decimal_text(stock_credit),
            "lines": lines,
            "causes": [],
        }


def margin_bridge(
    *,
    quote: Mapping[str, Any],
    base: Sequence[Mapping[str, Any]],
    remakes: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Selected revision is the sole quotation authority.

    Drivers partition costs, so each peso occurs exactly once. Discount is
    already included in quoted profit; the baseline waterfall shows its
    signed amount but the deviation does not subtract it again.
    """
    with localcontext() as context:
        context.prec = 256
        net, cost = number(quote["net"]), number(quote["cost"])
        margin = ratio(net - cost, net)
        unavailable = [cause for report in [*base, *remakes] for cause in report["causes"]]
        if not base:
            unavailable.append("La revisión aprobada todavía no tiene OT con cierre de costos.")
        if any(report["cost"] is None for report in [*base, *remakes]):
            unavailable.append("Una OT original o de reposición tiene costos incompletos.")
        common = {
            "quoted_cost": decimal_text(cost),
            "quoted_profit": decimal_text(net - cost),
            "quoted_margin": margin,
            "net": decimal_text(net),
        }
        if unavailable:
            return {
                **common,
                "real_cost": None,
                "real_profit": None,
                "real_margin": None,
                "delta_profit": None,
                "delta_margin": None,
                "drivers": [],
                "causes": list(dict.fromkeys(unavailable)),
            }
        quoted = {key: number(quote[key]) for key in ("materials", "waste", "labor", "other")}
        if quote.get("composition_known", True) is False or sum(quoted.values(), ZERO) != cost:
            return {
                **common,
                "real_cost": None,
                "real_profit": None,
                "real_margin": None,
                "delta_profit": None,
                "delta_margin": None,
                "drivers": [],
                "causes": [
                    "La revisión histórica no conserva una composición de costo que cierre."
                ],
            }
        actual = {key: sum((number(report[key]) for report in base), ZERO) for key in quoted}
        remake = sum((number(report["cost"]) for report in remakes), ZERO)
        drivers = [
            {"key": key, "amount": decimal_text(quoted[key] - actual[key])} for key in quoted
        ]
        drivers.append({"key": "remake", "amount": decimal_text(-remake)})
        real = sum(actual.values(), ZERO) + remake
        delta = cost - real
        if sum((D(driver["amount"]) for driver in drivers), ZERO) != delta:
            raise ValueError("analytics_bridge_does_not_close")
        real_margin = ratio(net - real, net)
        return {
            **common,
            "real_cost": decimal_text(real),
            "real_profit": decimal_text(net - real),
            "real_margin": real_margin,
            "delta_profit": decimal_text(delta),
            "delta_margin": decimal_text(D(real_margin) - D(margin))
            if margin is not None and real_margin is not None
            else None,
            "discount": decimal_text(number(quote["discount"], signed=True))
            if quote.get("discount") is not None
            else None,
            "drivers": drivers,
            "causes": [],
        }


def driver_sources(result: Mapping[str, Any], driver: str) -> list[dict[str, str]]:
    """Signed real contributions to a deviation, without allocating a residual."""
    if result["cost"] is None:
        return []
    with localcontext() as context:
        context.prec = 256
        parts = []
        for line in result["lines"]:
            labor = line["kind"] == "LABOR"
            if driver == "labor" and labor:
                amount = number(line["amount"], signed=True)
            elif driver == "waste" and not labor:
                amount = number(line["waste"])
            elif driver == "materials" and not labor:
                amount = number(line["amount"], signed=True) - number(line["waste"])
            elif driver == "remake":
                amount = number(line["amount"], signed=True)
            else:
                continue
            parts.append({"id": line["id"], "amount": decimal_text(-amount)})
        if driver in ("other", "remake"):
            parts.append({"id": "other", "amount": decimal_text(-number(result["other"]))})
        if driver in ("materials", "remake"):
            parts.append({"id": "credit", "amount": decimal_text(number(result["credit"]))})
        return parts


def bar_reading(
    *,
    input_mm: object | None,
    productive_mm: object | None,
    waste_mm: object | None,
    reusable_mm: object | None,
    complete: bool = True,
) -> dict[str, Any]:
    if not complete or any(
        value is None for value in (input_mm, productive_mm, waste_mm, reusable_mm)
    ):
        return {
            "waste_ratio": None,
            "utilization": None,
            "cause": "Falta medir y confirmar todas las barras: entrada, piezas, pérdida y retazo reutilizable del corte real.",
        }
    with localcontext() as context:
        context.prec = 256
        stock, used, lost, kept = (
            number(value) for value in (input_mm, productive_mm, waste_mm, reusable_mm)
        )
        if stock <= ZERO or used + lost + kept != stock:
            raise ValueError("actual_cut_does_not_close")
        return {"waste_ratio": ratio(lost, stock), "utilization": ratio(used, stock), "cause": None}
