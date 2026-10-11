from datetime import date
from typing import cast

import pytest

from dekopen_engine.warranty import warranty_deadline


@pytest.mark.parametrize(
    "started,days,expected",
    [
        (date(2028, 2, 28), 2, date(2028, 3, 1)),
        (date(2027, 12, 31), 1, date(2028, 1, 1)),
        (date(2026, 10, 11), 365, date(2027, 10, 11)),
        (None, 365, None),
        (date(2026, 10, 11), None, None),
    ],
)
def test_sealed_warranty_dates(started: date | None, days: int | None, expected: date | None) -> None:
    assert warranty_deadline(started, days) == expected


@pytest.mark.parametrize("days", [0, -1, True, "365", 36501])
def test_warranty_rejects_invented_duration(days: object) -> None:
    with pytest.raises(ValueError):
        warranty_deadline(date(2026, 10, 11), cast(int, days))
