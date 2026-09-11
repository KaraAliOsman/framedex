"""Independent monetary examples for the SHOT-08 owner contracts."""

from decimal import Decimal
from itertools import permutations

import pytest

from dekopen_engine.commercial import (
    CommercialLine, PricingError, PricingMode, convert_cost, direct_cost,
    discount_state, finish_lines, matrix_price, quantize_currency,
    target_project, typology_price, unit_price, validate_segment,
)

D = Decimal


@pytest.mark.parametrize('currency,value,expected', [
    ('CLP','1.5','2'), ('CLP','1.4999','1'), ('USD','1.005','1.01'),
    ('USD','1.0049','1.00'),
])
def test_currency_half_up(currency: str, value: str, expected: str) -> None:
    assert quantize_currency(D(value), currency) == D(expected)


def test_line_quantity_discount_and_aggregate_tax() -> None:
    result = finish_lines([
        CommercialLine(2, 3, D('0.1'), D('1.49'), D('0.1')),
        CommercialLine(1, 1, D('0.1'), D('3')),
    ], 'CLP', D('0.19'))
    assert result.lines == ((1, D('3')), (2, D('4')))
    assert (result.project_net, result.project_tax, result.project_gross) == (
        D('7'), D('1'), D('8'))
    # Per-line taxes would be 1+1; the normative project tax is 1.


def test_mode_one_materials_fx_and_no_early_rounding() -> None:
    converted = convert_cost(D('0.1234'), 'USD', 'CLP', D('900'))
    assert converted == D('116.613')
    cost = direct_cost([converted, D('10')], D('2'), D('0.08'), D('15'), D('12'))
    assert cost == D('190.74204')
    price = unit_price(PricingMode.COST_PLUS_MARGIN, cost=D('100000'), margin=D('0.35'),
                       area=D('1'), width=D('1000'), height=D('1000'))
    assert finish_lines([CommercialLine(1, 1, D('100000'), price)], 'CLP', D('0')).project_net == D('153846')


@pytest.mark.parametrize('foil,selected,expected', [
    (False, '100', '2000'), (True, '100', '2500'),
    (False, '150', '2140'), (True, '150', '2640'),
])
def test_mode_two_foil_and_glass_separate(foil: bool, selected: str, expected: str) -> None:
    assert typology_price(D('2'), D('1000'), foil, D(selected), D('100')) == D(expected)


def test_negative_glass_is_not_a_credit_or_clamp() -> None:
    with pytest.raises(PricingError, match='negative_glass_differential'):
        typology_price(D('1'), D('100'), False, D('9.99'), D('10'))


def test_mode_three_bilinear_oracle_nodes_edges_and_interior() -> None:
    cells = {(600,600): D('100'), (800,600): D('200'),
             (600,800): D('300'), (800,800): D('500')}
    assert matrix_price(D('600'), D('600'), {(600,600): D('100')}) == D('100')
    assert matrix_price(D('700'), D('600'), cells) == D('150')
    assert matrix_price(D('650'), D('700'), cells) == D('237.5')
    with pytest.raises(PricingError, match='missing_matrix_cell'):
        matrix_price(D('700'), D('700'), {(600,600): D('100')})
    with pytest.raises(PricingError, match='matrix_out_of_domain'):
        matrix_price(D('2400.01'), D('700'), cells)


def test_mode_four_ties_use_position_index_under_every_permutation() -> None:
    costs = [(3,D('1')), (1,D('1')), (2,D('1'))]
    for order in permutations(costs):
        result = target_project(order, D('0.30'), 'CLP', D('0.19'))
        assert result.lines == ((1,D('2')), (2,D('1')), (3,D('1')))
        assert (result.project_net,result.project_tax,result.project_gross) == (D('4'),D('1'),D('5'))


def test_mode_four_non_loss_floors_take_precedence() -> None:
    # 100.1 needs 101, while the second line has room to absorb the allocation.
    result = target_project([(1,D('100.1')), (2,D('1000'))], D('0.001'), 'CLP', D('0'))
    assert result.project_net == D('1101')
    assert result.lines == ((1,D('101')), (2,D('1000')))
    with pytest.raises(PricingError, match='target_below_non_loss_minimum'):
        target_project([(1,D('1.01')), (2,D('1.01'))], D('0'), 'CLP', D('0'))


def test_mode_four_usd_residual() -> None:
    assert target_project([(2,D('0.01')), (1,D('0.01'))], D('0.2'), 'USD', D('0')).lines == (
        (1,D('0.02')), (2,D('0.01')))


@pytest.mark.parametrize('role,discount,confirmed,expected', [
    ('OWNER','0.1',False,'APPLIED'), ('ESTIMATOR','0.1',False,'APPLIED'),
    ('OWNER','0.1001',False,'APPLIED'), ('ESTIMATOR','0.1001',False,'PENDING'),
    ('ESTIMATOR','0.2',False,'PENDING'), ('OWNER','0.25',True,'APPLIED'),
])
def test_discount_governance(role: str, discount: str, confirmed: bool, expected: str) -> None:
    assert discount_state(role,D(discount),confirmed) == expected


@pytest.mark.parametrize('role,discount', [('ESTIMATOR','0.2001'), ('OWNER','0.2001'),
                                         ('WORKSHOP_MANAGER','0'), ('INSTALLER','0')])
def test_discount_permission_denied(role: str, discount: str) -> None:
    with pytest.raises(PricingError):
        discount_state(role,D(discount),False)


def test_mode_five_catalog_segment_and_loss_even_for_owner() -> None:
    price = unit_price(PricingMode.COMMERCIAL_LIST_WITH_DISCOUNTS, cost=D('1'), margin=D('0'),
                       area=D('1'),width=D('1000'),height=D('1000'),catalog_price=D('100'))
    validate_segment('CONSTRUCTION',D('0.25'),51)
    assert finish_lines([CommercialLine(1,51,D('50'),price,D('0.25'))], 'CLP',D('0')).project_net == D('3825')
    with pytest.raises(PricingError,match='invalid_segment_discount'):
        validate_segment('CONSTRUCTION',D('0.25'),50)
    with pytest.raises(PricingError,match='negative_margin'):
        finish_lines([CommercialLine(1,1,D('75.01'),price,D('0.25'))],'CLP',D('0'))


@pytest.mark.parametrize('value', ['NaN','Infinity','-1'])
def test_invalid_numeric_authorities(value: str) -> None:
    with pytest.raises(PricingError):
        convert_cost(D(value),'CLP','CLP')


def test_missing_fx_and_missing_tariff_are_typed() -> None:
    with pytest.raises(PricingError, match='missing_fx_authority'):
        convert_cost(D('1'),'USD','CLP')
    with pytest.raises(PricingError, match='missing_typology_authority'):
        unit_price(PricingMode.PRICE_PER_M2_BY_TYPOLOGY,cost=D('1'),margin=D('0'),
                   area=D('1'),width=D('1000'),height=D('1000'))
