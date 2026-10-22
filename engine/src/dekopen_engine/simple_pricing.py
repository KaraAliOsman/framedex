"""Workshop pricing policy: resolved material costs in, exact sale breakdown out."""

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, localcontext

from .commercial import (
    ONE, ZERO, PricingError, PricingMode, ServiceBasis, direct_cost, fraction,
    number, quantum, service_cost, unit_price,
)


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
                 policy: SimplePricingPolicy, *, installation_included: bool = False) -> SimplePrice:
    """One window, before quantity/tax. Explicit extra installation is never charged twice.

    Material costs include the resolved physical extras. Rates and catalog facts
    are supplied by the caller; this pure function cannot infer missing prices.
    """
    number(area_m2, positive=True)
    if not materials:
        raise PricingError('missing_material_costs')
    installation_rate = ZERO if installation_included else policy.installation_rate
    cost = direct_cost(materials, area_m2, policy.waste, policy.labor_rate, installation_rate,
        labor_basis=policy.labor_basis, installation_basis=policy.installation_basis)
    exact = unit_price(PricingMode.COST_PLUS_MARGIN, cost=cost, margin=policy.margin,
        area=area_m2, width=ZERO, height=ZERO)
    net = round_sale_up(exact, policy.rounding_step, policy.currency)
    with localcontext() as context:
        context.prec = 256
        material_total = sum(materials, ZERO)
        return SimplePrice(materials=material_total, waste=material_total * policy.waste,
            labor=service_cost(policy.labor_rate, area_m2, policy.labor_basis),
            installation=service_cost(installation_rate, area_m2, policy.installation_basis),
            direct_cost=cost, exact_unit_price=exact, unit_net=net,
            rounding=net - exact, profit=net - cost)
