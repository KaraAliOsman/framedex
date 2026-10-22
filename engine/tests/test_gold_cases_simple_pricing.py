"""Simple sale policy, explicit service units and frozen synthetic PRO6004 quotes."""

from dataclasses import replace
from decimal import Decimal as D, localcontext
import json
from pathlib import Path
from typing import Any

import pytest

from dekopen_engine.commercial import CommercialLine, PricingError, direct_cost, finish_lines
from dekopen_engine.simple_pricing import SimplePricingPolicy, round_sale_up, simple_price
from engine.tests.simple_pricing_cases import simple_pricing_cases


def policy(**changes: Any) -> SimplePricingPolicy:
    return replace(SimplePricingPolicy(currency='CLP', labor_rate=D('20'), labor_basis='M2',
        installation_rate=D('15'), installation_basis='WINDOW', margin=D('.20'),
        rounding_step=D('1')), **changes)


def test_fixed_and_turn_pro6004_golden_freezes_prices_and_material_quantities() -> None:
    frozen = json.loads(Path(__file__).with_name('golden_simple_pricing.json').read_text(encoding='utf-8'))
    assert simple_pricing_cases() == frozen
    fixed, turn = frozen['PRO6004-fija'], frozen['PRO6004-abatible']
    assert fixed['price']['labor'] == '19800.00'
    assert fixed['price']['installation'] == '10000'
    assert turn['price']['labor'] == '20000'
    assert turn['price']['installation'] == '6600.00'
    assert {row['sku'] for row in turn['materials']} == {
        'PRO-F', 'PRO-S', 'PRO-B', 'STEEL-F', 'STEEL-S', 'GLASS-24', 'PRO-TURN', 'SCREW-F', 'SCREW-S'}
    assert 'PRO-TURN' not in {row['sku'] for row in fixed['materials']}


def test_service_bases_apply_per_window_and_margin_is_on_sale() -> None:
    priced = simple_price([D('60'), D('40')], D('2'), policy())
    assert priced.materials == D('100')
    assert priced.labor == D('40') and priced.installation == D('15')
    assert priced.direct_cost == D('155')
    assert priced.exact_unit_price == D('193.75')
    assert priced.unit_net == D('194')
    assert priced.profit == D('39') and priced.rounding == D('.25')
    reverse = simple_price([D('100')], D('2'), policy(labor_basis='WINDOW', installation_basis='M2'))
    assert reverse.direct_cost == D('150')
    assert reverse.unit_net == D('188')


def test_explicit_installation_and_waste_do_not_duplicate_services_or_apply_waste_to_labor() -> None:
    priced = simple_price([D('100')], D('2'), policy(waste=D('.10')), installation_included=True)
    assert priced.waste == D('10') and priced.installation == D('0')
    assert priced.direct_cost == D('150') and priced.unit_net == D('188')


def test_quantity_and_tax_use_existing_commercial_line_contract() -> None:
    priced = simple_price([D('100')], D('2'), policy())
    totals = finish_lines([CommercialLine(1, 3, priced.direct_cost, priced.unit_net)], 'CLP', D('.19'))
    assert totals.project_net == D('582')
    assert totals.project_tax == D('111') and totals.project_gross == D('693')


def test_absent_materials_are_unknown_but_an_explicit_zero_price_is_allowed() -> None:
    with pytest.raises(PricingError, match='missing_material_costs'):
        simple_price([], D('1'), policy())
    free = simple_price([D('0')], D('1'), policy(labor_rate=D('0'), installation_rate=D('0')))
    assert free.unit_net == D('0')


@pytest.mark.parametrize('currency,step,value,expected', [
    ('CLP', '1000', '1500', '2000'), ('CLP', '1000', '1000', '1000'),
    ('CLP', '1000', '1000.0001', '2000'), ('USD', '.05', '1.001', '1.05'),
    ('USD', '.01', '1.0001', '1.01'), ('CLP', '1', '0', '0'),
])
def test_rounding_is_an_explicit_upwards_multiple(currency: str, step: str, value: str, expected: str) -> None:
    assert round_sale_up(D(value), D(step), currency) == D(expected)


@pytest.mark.parametrize('changes', [
    {'margin': D('1')}, {'margin': D('-.01')}, {'margin': D('NaN')},
    {'labor_rate': D('-1')}, {'installation_rate': D('Infinity')},
    {'labor_basis': 'KG'}, {'installation_basis': ''}, {'currency': 'EUR'},
    {'rounding_step': D('0')}, {'rounding_step': D('.5')},
    {'currency': 'USD', 'rounding_step': D('.015')}, {'rounding_step': D('NaN')},
    {'waste': D('1.01')}, {'labor_rate': 20},
])
def test_invalid_policy_is_rejected_before_calculation(changes: dict[str, Any]) -> None:
    with pytest.raises(PricingError):
        policy(**changes)


@pytest.mark.parametrize('material,area', [(D('-1'), D('1')), (D('NaN'), D('1')),
    (1, D('1')), (D('1'), D('0')), (D('1'), D('Infinity')), (D('1'), 2)])
def test_unknown_or_inexact_inputs_never_become_zero_prices(material: Any, area: Any) -> None:
    with pytest.raises(PricingError):
        simple_price([material], area, policy())


def test_fractional_purchase_costs_and_low_ambient_precision_are_preserved() -> None:
    with localcontext() as context:
        context.prec = 80
        material = D('12000') * D('2412') / D('6500')
    normal = simple_price([material], D('1.32'), policy())
    with localcontext() as context:
        context.prec = 6
        assert simple_price([material], D('1.32'), policy()) == normal
    assert normal.materials == material
    with localcontext() as context:
        context.prec = 256
        assert normal.direct_cost == material + D('26.4') + D('15')


def test_legacy_direct_cost_keeps_its_existing_m2_contract() -> None:
    assert direct_cost([D('100')], D('2'), D('.08'), D('20'), D('15')) == D('178')
    assert direct_cost([D('100')], D('2'), D('.08'), D('20'), D('15'),
        labor_basis='WINDOW', installation_basis='WINDOW') == D('143')
