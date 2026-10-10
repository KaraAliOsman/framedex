"""Chilean module-11 check digit; punctuation never changes the identity."""

import re


def valid_rut(value: str | None) -> bool:
    compact = re.sub(r"[.\s-]", "", value or "").upper()
    if not re.fullmatch(r"[0-9]{7,8}[0-9K]", compact):
        return False
    digits, check = compact[:-1], compact[-1]
    if int(digits) == 0:
        return False
    total = sum(int(number) * (2 + index % 6) for index, number in enumerate(reversed(digits)))
    remainder = 11 - total % 11
    return check == ("0" if remainder == 11 else "K" if remainder == 10 else str(remainder))
