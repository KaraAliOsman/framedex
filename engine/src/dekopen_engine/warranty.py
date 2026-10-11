"""Dates projected only from an explicit, sealed warranty declaration."""

from datetime import date, timedelta


def warranty_deadline(started_on: date | None, days: int | None) -> date | None:
    if days is None or started_on is None:
        return None
    if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= 36500:
        raise ValueError("Declara un plazo de garantía entre 1 y 36 500 días.")
    return started_on + timedelta(days=days)
