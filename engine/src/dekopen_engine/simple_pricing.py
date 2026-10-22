"""Workshop pricing policy: resolved material costs in, exact sale breakdown out."""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, localcontext

from .commercial import (
    ONE, ZERO, CommercialLine, CommercialResult, PricingError, PricingMode, ServiceBasis,
    direct_cost, finish_lines, fraction, number, quantum, service_cost, unit_price,
)
from .extra_models import ExtraLine
from .extras import position_price, service_price


@dataclass(frozen=True)
class SimplePricingPolicy:
    currency: str
    labor_rate: Decimal
    labor_basis: ServiceBasis
    installation_rate: Decimal
    installation_basis: ServiceBasis
    margin: Decimal
    rounding_step: Decimal
    waste: Decimal = ZERO

    def __post_init__(self) -> None:
        number(self.labor_rate)
        number(self.installation_rate)
        fraction(self.margin, margin=True)
        fraction(self.waste)
        service_cost(self.labor_rate, ONE, self.labor_basis)
        service_cost(self.installation_rate, ONE, self.installation_basis)
        validate_rounding(self.rounding_step, self.currency)


@dataclass(frozen=True)
class SimplePrice:
    materials: Decimal
    waste: Decimal
    labor: Decimal
    installation: Decimal
    direct_cost: Decimal
    exact_unit_price: Decimal
    unit_net: Decimal
    rounding: Decimal
    profit: Decimal
    extras_cost: Decimal = ZERO
    extras_net: Decimal = ZERO


@dataclass(frozen=True)
class SimpleProjectPrice:
    totals: CommercialResult
    cost_lines: tuple[tuple[int, Decimal], ...]
    services_cost: Decimal
    total_cost: Decimal


def simple_project(lines: Sequence[CommercialLine], currency: str, tax_rate: Decimal,
                   services: Sequence[ExtraLine] = ()) -> SimpleProjectPrice:
    """Quantity, project services and tax share the established commercial rules."""
    if any(item.currency != currency for item in services):
        raise PricingError('incompatible_extra_currency')
    totals = finish_lines(lines, currency, tax_rate,
        [Decimal(str(service_price(item, currency)['amount'])) for item in services])
    with localcontext() as context:
        context.prec = 256
        costs = tuple((line.position_index, line.unit_cost * line.quantity) for line in lines)
        services_cost = sum((item.total_cost for item in services), ZERO)
        return SimpleProjectPrice(totals, costs, services_cost,
            sum((cost for _, cost in costs), ZERO) + services_cost)


def validate_rounding(step: Decimal, currency: str) -> None:
    number(step, positive=True)
    minimum = quantum(currency)
    with localcontext() as context:
        context.prec = 256
        if step < minimum or step % minimum != ZERO:
            raise PricingError('invalid_rounding_step')


def round_sale_up(value: Decimal, step: Decimal, currency: str) -> Decimal:
    """Round upwards to a declared currency multiple, never below the target margin."""
    number(value)
    validate_rounding(step, currency)
    with localcontext() as context:
        context.prec = 256
        return ((value / step).to_integral_value(rounding=ROUND_CEILING) * step).quantize(
            quantum(currency))


def simple_price(materials: Sequence[Decimal], area_m2: Decimal,
                 policy: SimplePricingPolicy, *, installation_included: bool = False,
                 extras: Sequence[ExtraLine] = ()) -> SimplePrice:
    """One window, before quantity/tax. Explicit extra installation is never charged twice.

    Resolved extras retain their declared selling tariff and do not receive a
    second waste charge. Rates and catalog facts are supplied by the caller.
    """
    number(area_m2, positive=True)
    if not materials:
        raise PricingError('missing_material_costs')
    if any(item.currency != policy.currency for item in extras):
        raise PricingError('incompatible_extra_currency')
    installation_included = installation_included or any(item.installation for item in extras)
    installation_rate = ZERO if installation_included else policy.installation_rate
    base_cost = direct_cost(materials, area_m2, policy.waste, policy.labor_rate, installation_rate,
        labor_basis=policy.labor_basis, installation_basis=policy.installation_basis)
    base_price = unit_price(PricingMode.COST_PLUS_MARGIN, cost=base_cost, margin=policy.margin,
        area=area_m2, width=ZERO, height=ZERO)
    exact = position_price(base_price, tuple(extras)) if extras else base_price
    net = round_sale_up(exact, policy.rounding_step, policy.currency)
    with localcontext() as context:
        context.prec = 256
        extras_cost = sum((item.total_cost for item in extras), ZERO)
        extras_net = sum((item.total_price for item in extras), ZERO)
        cost = base_cost + extras_cost
        material_total = sum(materials, ZERO)
        return SimplePrice(materials=material_total, waste=material_total * policy.waste,
            labor=service_cost(policy.labor_rate, area_m2, policy.labor_basis),
            installation=service_cost(installation_rate, area_m2, policy.installation_basis),
            direct_cost=cost, exact_unit_price=exact, unit_net=net,
            rounding=net - exact, profit=net - cost, extras_cost=extras_cost, extras_net=extras_net)
