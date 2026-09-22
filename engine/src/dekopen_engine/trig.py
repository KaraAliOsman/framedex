"""Decimal trigonometry for presentation geometry.

Used only for plan-view projection of coupled assemblies; manufacturing
cut lengths never consume these values. Range reduction plus Taylor
series keeps absolute error far below the engine's 0.01 mm quantum.
"""

from decimal import Decimal

_PI = Decimal("3.1415926535897932384626433832795028841971693993751")
_TWO_PI = _PI * 2
_EPSILON = Decimal("1e-30")
_DEG_TO_RAD = _PI / Decimal("180")


def _reduce(x: Decimal) -> Decimal:
    """Fold an angle in radians into (-pi, pi]."""
    x = x % _TWO_PI
    if x > _PI:
        x -= _TWO_PI
    elif x <= -_PI:
        x += _TWO_PI
    return x


def _sin_series(x: Decimal) -> Decimal:
    term = x
    total = x
    x_squared = x * x
    n = 1
    while True:
        term = -term * x_squared / (Decimal(n + 1) * Decimal(n + 2))
        total += term
        if abs(term) < _EPSILON:
            return total
        n += 2


def _cos_series(x: Decimal) -> Decimal:
    term = Decimal(1)
    total = Decimal(1)
    x_squared = x * x
    n = 0
    while True:
        term = -term * x_squared / (Decimal(n + 1) * Decimal(n + 2))
        total += term
        if abs(term) < _EPSILON:
            return total
        n += 2


def sin_degrees(degrees: Decimal) -> Decimal:
    return _sin_series(_reduce(degrees * _DEG_TO_RAD))


def cos_degrees(degrees: Decimal) -> Decimal:
    return _cos_series(_reduce(degrees * _DEG_TO_RAD))
