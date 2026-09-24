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


def _atan_series(x: Decimal) -> Decimal:
    """atan(x) for small |x|; converges geometrically, ~1e-30 at |x|<=0.05."""
    term = x
    total = x
    x_squared = x * x
    n = 1
    while True:
        term = -term * x_squared
        contribution = term / Decimal(n + 2)
        total += contribution
        if abs(contribution) < _EPSILON:
            return total
        n += 2


def _atan_full(x: Decimal) -> Decimal:
    """atan(x) in radians via the half-angle identity.

    atan(x) = 2 * atan(x / (1 + sqrt(1 + x²))) halves the argument's
    magnitude each step; a few iterations bring |x| under 0.05 where the
    Taylor series converges to far below the engine quantum. The returned
    value is the series result times 2^halvings.
    """
    factor = 1
    while abs(x) > Decimal("0.05"):
        x = x / (Decimal(1) + (Decimal(1) + x * x).sqrt())
        factor *= 2
    return _atan_series(x) * factor


def atan2_degrees(y: Decimal, x: Decimal) -> Decimal:
    """atan2(y, x) in degrees, range (-180, 180]."""
    if x == 0:
        if y > 0:
            return Decimal("90")
        if y < 0:
            return Decimal("-90")
        return Decimal("0")
    base = _atan_full(y / x) / _DEG_TO_RAD
    if x > 0:
        return base
    if y >= 0:
        return base + Decimal("180")
    return base - Decimal("180")


def asin_degrees(x: Decimal) -> Decimal:
    """asin(x) in degrees for |x| <= 1, range [-90, 90]."""
    if x >= 1:
        return Decimal("90")
    if x <= -1:
        return Decimal("-90")
    return atan2_degrees(x, (Decimal(1) - x * x).sqrt())
