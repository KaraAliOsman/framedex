"""Compare independently cited cells without promoting proposals to facts."""

from collections import defaultdict
from decimal import Decimal
import json

from ingest.catalog_template import SCHEMAS, candidate

IDENTITY = {
    "Sistemas": ("system_code", "version"),
    "Perfiles": ("system_code", "sku"),
    "Roles y reglas de corte": ("system_code", "sku", "role"),
    "Refuerzos": ("system_code", "sku"),
    "Barras de refuerzo": ("system_code", "sku", "reinforcement_sku"),
    "Límites": ("system_code", "opening_type"),
    "Colores y SKU por color": ("system_code", "sku", "finish"),
    "Vidrios": ("system_code", "sku", "version"),
    "Reglas de vidrio": ("code",),
    "Herrajes": ("system_code", "sku", "opening_type"),
    "Precios de costo": ("system_code", "sku", "list_code", "valid_from"),
}
assert IDENTITY.keys() == SCHEMAS.keys()


def _identity(row):
    # Codes are text: 001 and 1 must never be merged as equal numbers.
    fields = IDENTITY[row["sheet"]]
    values = [row["values"].get(field) for field in fields]
    return json.dumps([row["sheet"], *values], ensure_ascii=False, sort_keys=True)


def same_value(column, left, right):
    if left is None or right is None:
        return left is right
    if column.kind in ("decimal", "positive", "integer", "count", "angle"):
        return Decimal(str(left)) == Decimal(str(right))
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    # Structured values retain their declared codes and ordered rules. A
    # doubtful structural difference goes to review rather than coercion.
    return left == right


def compare_reads(first, second, *, file_name, audit_ids):
    grouped = []
    for reading in (first, second):
        index = defaultdict(list)
        for row in reading:
            index[_identity(row)].append(row)
        grouped.append(index)
    output = []
    for identity in dict.fromkeys([*grouped[0], *grouped[1]]):
        left, right = grouped[0][identity], grouped[1][identity]
        unique = len(left) == len(right) == 1 and all(
            row["values"].get(key) is not None
            for row in (*left, *right) for key in IDENTITY[row["sheet"]]
        )
        pairs = [(left[0], right[0])] if unique else [(row, None) for row in left] + [(None, row) for row in right]
        for a, b in pairs:
            base = a or b
            raw, refs = {}, {}
            for column in SCHEMAS[base["sheet"]]:
                key = column.key
                readings = []
                for number, row in enumerate((a, b)):
                    field = row["fields"].get(key, {}) if row else {}
                    readings.append({**field, "value": row["values"].get(key) if row else None,
                        "audit_id": str(audit_ids[number]), "reading": number + 1})
                x, y = readings
                agreed = unique and x.get("confidence") == y.get("confidence") == "HIGH" and same_value(column, x["value"], y["value"])
                missing = unique and x.get("confidence") == y.get("confidence") == "UNKNOWN" and x["value"] is None and y["value"] is None
                if key == "source":
                    # The file name comes from storage, not either model.
                    raw[key] = file_name
                    refs[key] = {"ref": file_name, "quote": file_name, "confidence": "HIGH", "comparison": "AGREED", "readings": readings}
                else:
                    raw[key] = x["value"] if agreed else None
                    selected = x if a else y
                    refs[key] = {**selected, "confidence": "HIGH" if agreed else "UNKNOWN" if missing else "LOW",
                        "comparison": "AGREED" if agreed else "MISSING" if missing else "REVIEW", "readings": readings}
            row = candidate(base["sheet"], raw, key=f"dual{len(output)}", row=base["row"], method="AI", refs=refs)
            row["double_read"] = {"audit_ids": [str(value) for value in audit_ids], "identity_unique": unique,
                "review_fields": [key for key, field in refs.items() if field["comparison"] == "REVIEW"]}
            output.append(row)
    return output
