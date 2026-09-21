"""Pure platform-billing conversion; PD-11-01 and PD-08-02 authorities."""

from decimal import Decimal, localcontext

from dekopen_engine.commercial import convert_cost, quantize_currency, number


def platform_charge_clp(net_usd: Decimal, observed_usd_clp: Decimal) -> Decimal:
    """Apply approved FX buffer and IVA, rounding only the final CLP amount."""
    number(net_usd, positive=True)
    number(observed_usd_clp, positive=True)
    with localcontext() as context:
        context.prec = 80
        return quantize_currency(
            convert_cost(net_usd, 'USD', 'CLP', observed_usd_clp) * Decimal('1.19'), 'CLP')


def upgrade_credits(old_allowance: int, new_allowance: int, *, remaining: int, total: int) -> int:
    """PD-11-03: exact time units (e.g. microseconds), never floating-point seconds."""
    if (any(type(value) is not int for value in (old_allowance, new_allowance, remaining, total))
            or min(old_allowance, new_allowance, remaining) < 0 or total <= 0 or remaining > total):
        raise ValueError('Valid integral allowance and period bounds required')
    return max(0, new_allowance - old_allowance) * remaining // total


# Frozen PRD-03 catalogue. Monetary output remains an engine result.
PLAN_ALLOWANCES: dict[str, int] = {'STARTER': 0, 'PRO': 2000, 'BUSINESS': 6000, 'BUSINESS_2X': 12000}
_PLAN_PRICES: dict[str, tuple[str, str]] = {
    'STARTER': ('39', '420'), 'PRO': ('69', '708'),
    'BUSINESS': ('129', '1188'), 'BUSINESS_2X': ('149', '1548'),
}
_PACKS: dict[str, tuple[str, int]] = {'PACK_1000': ('15', 1000), 'PACK_3000': ('40', 3000), 'PACK_7500': ('90', 7500)}


def product_terms(code: str, cycle: str | None = None) -> tuple[Decimal, int]:
    if code in _PLAN_PRICES and cycle in ('monthly', 'annual'):
        return Decimal(_PLAN_PRICES[code][0 if cycle == 'monthly' else 1]), PLAN_ALLOWANCES[code]
    if code in _PACKS and cycle is None:
        price, credits = _PACKS[code]
        return Decimal(price), credits
    raise ValueError('Unknown approved billing product')
