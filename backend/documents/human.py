"""How a stored entity code reads to people: «N° 385», never «P-000385».

The stored code remains the identity in the database, evidence and search;
documents and messages show this form."""

import re

_CODE = re.compile(r"^([A-Z]{1,4})-0*(\d+)$")
_KINDS = {"P": "Obra", "OT": "OT", "OC": "Compra", "RT": "Retazo", "REC": "Recepción"}


def human_code(code, *, with_kind=False):
    if not code:
        return ""
    match = _CODE.match(str(code))
    if not match:
        return str(code)
    kind = _KINDS.get(match.group(1))
    return f"{kind} N° {match.group(2)}" if with_kind and kind else f"N° {match.group(2)}"
