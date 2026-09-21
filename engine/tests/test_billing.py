from decimal import Decimal

import pytest

from dekopen_engine.billing import platform_charge_clp


def test_owner_approved_net_usd_plus_buffer_and_iva():
    # Independent exact oracle: 39 * 900 * 105/100 * 119/100 = 43857.45.
    assert platform_charge_clp(Decimal('39'), Decimal('900')) == Decimal('43857')
    assert platform_charge_clp(Decimal('420'), Decimal('900')) == Decimal('472311')


def test_rounds_once_after_tax():
    assert platform_charge_clp(Decimal('39'), Decimal('900.0011')) == Decimal('43858')


@pytest.mark.parametrize('amount,rate', [('0', '900'), ('39', '0'), ('39', '-1'),
                                       ('NaN', '900'), ('39', 'Infinity')])
def test_rejects_missing_or_nonpositive_money_authority(amount, rate):
    with pytest.raises(ValueError):
        platform_charge_clp(Decimal(amount), Decimal(rate))
