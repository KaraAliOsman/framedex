from datetime import date

from dekopen_engine.warranty import warranty_deadline


def warranty_cases() -> dict[str, dict[str, str | int | None]]:
    cases: list[tuple[str, str | None, int | None]] = [
        ("LEAP_DAY", "2028-02-28", 2),
        ("YEAR_BOUNDARY", "2027-12-31", 1),
        ("SEALED_YEAR", "2026-10-11", 365),
        ("NO_EVENT", None, 365),
        ("HISTORICAL_PROSE_ONLY", "2026-10-11", None),
    ]
    result: dict[str, dict[str, str | int | None]] = {}
    for code, started, days in cases:
        expires = warranty_deadline(date.fromisoformat(started) if started else None, days)
        result[code] = {
            "started_on": started,
            "declared_days": days,
            "expires_on": expires.isoformat() if expires else None,
        }
    return result
