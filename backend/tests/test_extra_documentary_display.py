from decimal import Decimal

from documents.renderers import _extra_table, _money


def line(**changes):
    return {
        'name': 'Vierteaguas <fachada>', 'quantity': '1.56', 'unit': 'M',
        'unit_price': '1538', 'net': '2400', 'rounding': '0.72',
        'synthetic': True, 'cost_rate': 'secret-internal-cost', **changes,
    }


def test_itemized_document_keeps_exact_allocation_and_discloses_rounding():
    html = _extra_table([line()], 'CLP', prices=True, base=Decimal('10000'))
    assert '1,56 m' in html and '$1.538' in html and '$\xa02.400' in html
    assert 'Base de la posición' in html and '$\xa010.000' in html
    assert '0,72 CLP' in html and '· DEMO' in html
    assert '&lt;fachada&gt;' in html
    assert 'secret-internal-cost' not in html and ',0000' not in html


def test_grouped_document_identifies_quantity_without_disclosing_tariffs_or_costs():
    html = _extra_table([line()], 'CLP', prices=False, base=Decimal('10000'))
    assert 'Vierteaguas' in html and '1,56 m' in html
    assert 'Precio unitario' not in html and 'Base de la posición' not in html
    assert '1.538' not in html and '2.400' not in html and 'secret-internal-cost' not in html


def test_usd_tariff_uses_decimal_comma_and_no_spurious_zeroes():
    html = _extra_table([line(unit_price='21.50', net='33.54', rounding='0')], 'USD', prices=True)
    assert 'US$ 21,5' in html and '21.5000' not in html
    assert 'Ajuste de redondeo' not in html


def test_document_money_matches_half_up_currency_presentation_at_quantity_split():
    assert _money('379690.5', 'CLP') == '$\xa0379.691'
    assert _money('21.505', 'USD') == 'USD\xa021.51'
