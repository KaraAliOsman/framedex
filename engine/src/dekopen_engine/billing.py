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
