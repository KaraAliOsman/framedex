"""Billing row decoding at the Django raw-cursor boundary."""

import json

from pricing.repository import rows as raw_rows
from dekopen_engine.commercial import PricingError

_JSON_COLUMNS = frozenset({'authority', 'preview', 'result', 'provider_evidence', 'evidence'})


def rows(query, parameters=()):
    records = raw_rows(query, parameters)
    for record in records:
        for key in record.keys() & _JSON_COLUMNS:
            if isinstance(record[key], str):
                record[key] = json.loads(record[key])
    return records


def one(query, parameters=(), code='authority_not_found'):
    result = rows(query, parameters)
    if len(result) != 1:
        raise PricingError('ambiguous_authority' if result else code)
    return result[0]
