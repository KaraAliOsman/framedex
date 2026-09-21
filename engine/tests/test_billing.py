from decimal import Decimal

import pytest

from dekopen_engine.billing import platform_charge_clp


def test_owner_approved_net_usd_plus_buffer_and_iva() -> None:
    # Independent exact oracle: 39 * 900 * 105/100 * 119/100 = 43857.45.
    assert platform_charge_clp(Decimal('39'), Decimal('900')) == Decimal('43857')
    assert platform_charge_clp(Decimal('420'), Decimal('900')) == Decimal('472311')


def test_rounds_once_after_tax() -> None:
    assert platform_charge_clp(Decimal('39'), Decimal('900.0011')) == Decimal('43858')


@pytest.mark.parametrize('amount,rate', [('0', '900'), ('39', '0'), ('39', '-1'),
                                       ('NaN', '900'), ('39', 'Infinity')])
def test_rejects_missing_or_nonpositive_money_authority(amount: str, rate: str) -> None:
    with pytest.raises(ValueError):
        platform_charge_clp(Decimal(amount), Decimal(rate))


@pytest.mark.parametrize('old,new,remaining,total,expected', [
    (2000,6000,1,3,1333), (6000,2000,1,2,0), (2000,6000,0,100,0),
    (2000,6000,100,100,4000), (0,2000,1,2001,0),
])
def test_upgrade_exact_floor(old: int, new: int, remaining: int, total: int, expected: int) -> None:
    from dekopen_engine.billing import upgrade_credits
    assert upgrade_credits(old, new, remaining=remaining, total=total) == expected
