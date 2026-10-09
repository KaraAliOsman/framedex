"""Exact commercial readings and canonical counterfactual attribution.

All inputs are resolved authorities, never connections or provider clients.
The replay callback must be a pure calculator over frozen inputs. Applying
one driver at a time deliberately assigns interactions to the later driver.
Money is rounded once per selling line, HALF_UP at the currency quantum.
An allocated target-project unit is indicative: the sealed line is authority.
"""

from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from decimal import Decimal, localcontext
from typing import Any

from .commercial import PricingError, fraction, number, quantize_currency

D = Decimal
ZERO = D(0)
DRIVERS = (
    'quantity', 'dimensions', 'glass', 'hardware', 'design', 'cost_list',
    'fx', 'commercial_list', 'margin', 'discount', 'segment', 'services', 'tax',
)


def percent_points(value: Decimal) -> str:
    with localcontext() as context:
        context.prec = 80
        return f"{value * D(100):f} %"


def money_trace(formula: str, result: Decimal,
                inputs: Sequence[tuple[str, Decimal, str]],
                authority: str = 'Autoridades resueltas y congeladas de la operación') -> dict[str, Any]:
    return {'formula': formula, 'result': str(result),
            'inputs': [{'label': label, 'value': str(value), 'unit': unit}
                       for label, value, unit in inputs],
            'authority': authority, 'engineVersion': 'price-workspace-v1'}


def linear_purchase(rate: Decimal, unit: str, length_mm: Decimal,
                    stock_length_mm: Decimal, currency: str) -> dict[str, Any]:
    number(rate)
    number(length_mm)
    number(stock_length_mm,positive=True)
    if unit not in {'BAR','M'}:
        raise PricingError('incompatible_cost_unit')
    with localcontext() as context:
        context.prec = 80
        divisor = stock_length_mm if unit == 'BAR' else D(1000)
        cost = rate * length_mm / divisor
        return {'amount':cost,'trace':money_trace('Costo de compra × largo consumido ÷ largo de compra',cost,
            [('Costo de compra',rate,currency),('Largo consumido',length_mm,'mm'),
             ('Largo de compra',divisor,'mm')])}


def gross_margin(cost: Decimal, net: Decimal) -> Decimal | None:
    number(cost)
    number(net)
    with localcontext() as context:
        context.prec = 80
        return (net - cost) / net if net else None


def policy(*, cost: Decimal, net: Decimal, minimum: Decimal, maximum: Decimal,
           discount: Decimal, discount_limit: Decimal) -> dict[str, Any]:
    fraction(minimum, margin=True)
    fraction(maximum, margin=True)
    if minimum > maximum:
        raise PricingError('invalid_margin_band')
    fraction(discount)
    fraction(discount_limit)
    margin = gross_margin(cost, net)
    causes = []
    if margin is None:
        causes.append('undefined_margin')
    elif margin < minimum:
        causes.append('below_minimum')
    elif margin > maximum:
        causes.append('above_maximum')
    if discount > discount_limit:
        causes.append('discount_limit')
    return {'requires_approval': bool(causes), 'causes': causes, 'margin': margin}


def comparison(before: Mapping[str, Decimal | None], after: Mapping[str, Decimal | None],
               currency: str = 'CLP') -> dict[str, dict[str, Any]]:
    with localcontext() as context:
        context.prec = 256
        result: dict[str,dict[str,Any]] = {}
        for key, proposed in after.items():
            current = before.get(key)
            delta = None if current is None or proposed is None else proposed - current
            result[key] = {
                'current': current, 'proposed': proposed, 'delta': delta,
                'delta_pct': (delta / current if delta is not None and current else None),
                'delta_pp': delta * D(100) if key == 'margin' and delta is not None else None,
            }
            unit = 'fracción' if key == 'margin' else currency
            traces = {}
            for stage, value in (('current',current),('proposed',proposed)):
                if value is not None:
                    traces[stage] = money_trace('Valor de la operación comercial sellada',value,
                        [('Actual' if stage == 'current' else 'Propuesto',value,unit)])
            if delta is not None and current is not None and proposed is not None:
                inputs = [('Actual',current,unit),('Propuesto',proposed,unit)]
                traces['delta'] = money_trace('Propuesto − actual',delta,inputs)
                if current:
                    traces['delta_pct'] = money_trace('(Propuesto − actual) ÷ actual',delta/current,inputs)
                if key == 'margin':
                    traces['delta_pp'] = money_trace('(Margen propuesto − margen actual) × 100',delta*D(100),inputs)
            result[key]['traces'] = traces
        return result


def cascade(*, components: Sequence[tuple[str, Decimal]], cost: Decimal,
            list_net: Decimal, net: Decimal, tax: Decimal, gross: Decimal,
            extras_net: Decimal = ZERO, currency: str = 'CLP',
            tax_rate: Decimal | None = None) -> dict[str, Any]:
    """Each contribution is additive. Unrounded buying costs stay exact.

    Components must include waste/labor/services. There is no balancing
    plug: missing composition is rejected, never relabelled as rounding.
    """
    with localcontext() as context:
        context.prec = 256
        grouped: dict[str, Decimal] = {}
        for key, amount in components:
            grouped[key] = grouped.get(key, ZERO) + number(amount)
        if sum(grouped.values(), ZERO) != cost or net + tax != gross:
            raise PricingError('cascade_does_not_close')
        steps: list[dict[str,Any]] = [{'key': key, 'amount': amount} for key, amount in grouped.items()]
        steps.extend((
            {'key': 'profit_at_list', 'amount': list_net - cost},
            {'key': 'discount', 'amount': net - extras_net - list_net},
            {'key': 'project_charges', 'amount': extras_net},
            {'key': 'tax', 'amount': tax},
        ))
        if sum((step['amount'] for step in steps), ZERO) != gross:
            raise PricingError('cascade_does_not_close')
        def trace(formula: str, result: Decimal, inputs: Sequence[tuple[str,Decimal]]) -> dict[str,Any]:
            return money_trace(formula,result,[(key,value,currency) for key,value in inputs])
        traces = {key:trace('Suma de componentes consumidos de esta categoría',amount,
                           [(kind,value) for kind,value in components if kind == key]) for key,amount in grouped.items()}
        traces.update({
            'cost':trace('Suma exacta de componentes, merma, proceso y servicios',cost,list(grouped.items())),
            'profit_at_list':trace('Precio de lista − costo',list_net-cost,[('Precio de lista',list_net),('Costo',cost)]),
            'discount':trace('Neto − otros cargos − precio de lista',net-extras_net-list_net,
                            [('Neto',net),('Otros cargos',extras_net),('Precio de lista',list_net)]),
            'project_charges':trace('Otros cargos declarados del proyecto',extras_net,[('Cargos',extras_net)]),
            'list_net':trace('Suma de precios de lista por línea y servicios',list_net,[('Precio de lista',list_net)]),
            'net':trace('Precio de lista + descuento firmado + otros cargos',net,
                       [('Precio de lista',list_net),('Descuento firmado',net-extras_net-list_net),('Otros cargos',extras_net)]),
            'tax':trace('Neto × tasa declarada; mitades alejándose de cero al quantum de moneda' if tax_rate is not None else 'IVA definitivo por proyecto',tax,
                       [('Neto',net)]+([('Tasa de IVA',tax_rate)] if tax_rate is not None else [])),
            'gross':trace('Neto + IVA',gross,[('Neto',net),('IVA',tax)]),
            'profit':trace('Neto − costo',net-cost,[('Neto',net),('Costo',cost)]),
        })
        if tax_rate is not None:
            traces['tax']['inputs'][-1]['unit'] = 'fracción'
        margin = gross_margin(cost,net)
        if margin is not None:
            traces['margin'] = money_trace('(Neto − costo) ÷ neto',margin,
                [('Neto',net,currency),('Costo',cost,currency)])
        return {'steps': steps, 'traces':traces,'cost': cost, 'list_net': list_net, 'net': net,
                'tax': tax, 'gross': gross, 'profit': net - cost,
                'margin': margin, 'closes': True}


def unit_price_trace(mode: str, result: Decimal, *, currency: str, cost: Decimal,
                     margin: Decimal, area: Decimal, width: Decimal, height: Decimal,
                     foil: bool, rates: Mapping[str, Any], extras: Sequence[tuple[str,Decimal]]
                     ) -> dict[str,Any]:
    """Explain the existing unit-price calculator with its resolved inputs."""
    formulas = {
        'COST_PLUS_MARGIN':'Costo base ÷ (1 − margen) + venta de extras',
        'PRICE_PER_M2_BY_TYPOLOGY':'Área × tarifa × factor de foliado + diferencia de vidrio × área × 1,40 + extras',
        'FIXED_PRICE_MATRIX_DIMENSIONAL':'Interpolación bilineal de las celdas vecinas por ancho y alto + extras',
        'COMMERCIAL_LIST_WITH_DISCOUNTS':'Precio declarado de la lista comercial + extras',
    }
    inputs = []
    if mode == 'COST_PLUS_MARGIN':
        inputs = [('Costo base',cost,currency),('Margen solicitado',margin,'fracción')]
    elif mode == 'PRICE_PER_M2_BY_TYPOLOGY':
        inputs = [('Área',area,'m²'),('Tarifa por m²',rates['rate'],currency),
            ('Factor de foliado',D('1.25') if foil else D(1),'factor'),
            ('Tarifa del vidrio seleccionado',rates['selected_glass'],currency),
            ('Tarifa del vidrio base',rates['base_glass'],currency)]
    elif mode == 'FIXED_PRICE_MATRIX_DIMENSIONAL':
        inputs = [('Ancho',width,'mm'),('Alto',height,'mm')]
        x0,y0 = int(width // D(200))*200,int(height // D(200))*200
        x1,y1 = x0 if width == x0 else x0+200,y0 if height == y0 else y0+200
        inputs.extend((f'Celda {x} × {y} mm',rates['cells'][x,y],currency)
            for x,y in sorted({(x0,y0),(x1,y0),(x0,y1),(x1,y1)}))
    elif mode == 'COMMERCIAL_LIST_WITH_DISCOUNTS':
        inputs = [('Precio de lista',rates['catalog_price'],currency)]
    else:
        raise PricingError('project_mode_requires_project')
    return money_trace(formulas[mode]+'; lectura con mitades alejándose de cero a cuatro decimales',result,
        inputs+[(label,amount,currency) for label,amount in extras])


def composition(*, materials: Sequence[tuple[str, Decimal]], waste: Decimal,
                area: Decimal, labor: Decimal, installation: Decimal,
                extras: Sequence[tuple[str, Decimal]], quantity: int
                ) -> tuple[tuple[str, Decimal], ...]:
    if isinstance(quantity, bool) or quantity < 1:
        raise PricingError('invalid_positions')
    with localcontext() as context:
        context.prec = 256
        base = sum((number(amount) for _, amount in materials), ZERO)
        return tuple((key, amount * quantity) for key, amount in materials) + (
            ('waste', base * number(waste) * quantity),
            ('labor', number(area) * number(labor) * quantity),
            ('installation', area * number(installation) * quantity),
        ) + tuple((key, number(amount) * quantity) for key, amount in extras)


def undiscounted_lines(lines: Sequence[tuple[Decimal, int]], currency: str) -> Decimal:
    with localcontext() as context:
        context.prec = 80
        return sum((quantize_currency(price * quantity, currency)
                    for price, quantity in lines), ZERO)


def explain(before: Mapping[str, Any], after: Mapping[str, Any],
            reprice: Callable[[Mapping[str, Any]], Mapping[str, Decimal]],
            ) -> dict[str, Any]:
    """Canonical full reprice, with exact closure for project and each line.

    A state is split into DRIVERS by the resolver. Every stage uses the same
    frozen pure calculator, including tax and the currency rounding rule.
    No percent-weighted allocation or unexplained residual is permitted.
    """
    if set(before) != set(DRIVERS) or set(after) != set(DRIVERS):
        raise PricingError('incomplete_repricing_evidence')
    with localcontext() as context:
        context.prec = 80
        state = deepcopy(dict(before))
        start = dict(reprice(state))
        previous = start
        contributions: list[dict[str,Any]] = []
        fx = after['fx']
        currency = fx.get('currency','CLP') if isinstance(fx,Mapping) else 'CLP'
        for driver in DRIVERS:
            if before[driver] == after[driver]:
                current = previous
            else:
                state[driver] = deepcopy(after[driver])
                current = dict(reprice(state))
            keys = set(previous) | set(current)
            delta = {key: current.get(key, ZERO) - previous.get(key, ZERO) for key in sorted(keys)}
            contributions.append({'driver': driver, 'delta': delta,
                'traces':{key:money_trace('Etapa actual − etapa anterior del reprecio canónico',amount,
                    [('Etapa anterior',previous.get(key,ZERO),currency),('Etapa actual',current.get(key,ZERO),currency)])
                    for key,amount in delta.items()}})
            previous = current
        end = dict(reprice(after))
        if previous != end:
            raise PricingError('repricing_does_not_close')
        delta = {key: end.get(key, ZERO) - start.get(key, ZERO) for key in sorted(set(start) | set(end))}
        if any(sum((item['delta'].get(key, ZERO) for item in contributions), ZERO) != amount
               for key, amount in delta.items()):
            raise PricingError('repricing_does_not_close')
        return {'available': True, 'order': list(DRIVERS), 'contributions': contributions,
                'current': start, 'proposed': end, 'delta': delta, 'closes': True}
