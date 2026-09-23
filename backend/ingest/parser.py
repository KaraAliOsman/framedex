"""Deterministic window-schedule parsing — the first extraction pass.

Extraction confidence is a review aid, never authorization: only HIGH rows
auto-check the include flag, and nothing reaches a position without the
estimator's explicit confirm."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

_LABEL = re.compile(r"\b([A-Za-z]{1,4}[-_]?[A-Za-z]?\d{1,3}|\d{1,3}[A-Za-z])\b")
_DIMENSION = re.compile(r"\b(\d{3,5})\s*[x×]\s*(\d{3,5})\b")
# A quantity needs a unit marker (`3 un`, `2 unidades`, `10 und`, `4 pzas`,
# `2 cant`) — any other integer on the row is glass composition or thickness
# and must never promote into a count.
_QUANTITY_MARKER = re.compile(
    r"\b(\d{1,3})\s*(?:un(?:idades?)?|und|uds\.?|pza?s?\.?|piezas?|cant)\b",
    re.IGNORECASE,
)
# Schedule style where the count leads the row: "3 V-1 fijo 1200x1000".
_LEADING_QUANTITY = re.compile(r"^\s*(\d{1,3})\s+")

# es-CL schedule vocabulary → canonical opening hints (TURN direction is
# ambiguous on paper — TURN_LEFT is the placeholder the estimator corrects).
OPENING_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("corred", "SLIDING_2L"),
    ("sliding", "SLIDING_2L"),
    ("oscilobatiente", "TILT_TURN_LEFT"),
    ("tilt", "TILT_TURN_LEFT"),
    ("proyectante", "AWNING"),
    ("awning", "AWNING"),
    ("abatible", "TURN_LEFT"),
    ("practicable", "TURN_LEFT"),
    ("casement", "TURN_LEFT"),
    ("puerta", "DOOR_ENTRY"),
    ("door", "DOOR_ENTRY"),
    ("fijo", "FIXED"),
    ("fixed", "FIXED"),
)

_OPENING_TYPES = {
    "FIXED",
    "TURN_LEFT",
    "TURN_RIGHT",
    "TILT_TURN_LEFT",
    "TILT_TURN_RIGHT",
    "SLIDING_2L",
    "AWNING",
    "DOOR_ENTRY",
}


def opening_hint(text: str) -> str | None:
    lowered = text.lower()
    for keyword, opening in OPENING_KEYWORDS:
        if keyword in lowered:
            return opening
    return None


def _decimal(value: str) -> Decimal | None:
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return None
    if not parsed.is_finite() or parsed <= 0:
        return None
    return parsed


def parse_line(line: str) -> dict | None:
    """One schedule line → a candidate dict, or None when nothing parses."""
    dimension = _DIMENSION.search(line)
    if dimension is None:
        return None
    width = _decimal(dimension.group(1))
    height = _decimal(dimension.group(2))
    if width is None or height is None:
        return None
    warnings: list[str] = []
    label_match = _LABEL.search(line)
    label = label_match.group(1) if label_match else None
    opening = opening_hint(line)
    # Quantity: only a unit marker ("3 un") or a leading count identifies one;
    # a bare trailing integer is ambiguous with glass thickness and defaults
    # to one — review data must err low, never high.
    quantity = 1
    marker = _QUANTITY_MARKER.search(line)
    leading = _LEADING_QUANTITY.match(line)
    if marker:
        quantity = int(marker.group(1))
    elif leading and not _LABEL.fullmatch(leading.group(0).strip()):
        quantity = int(leading.group(1))
    if label is None:
        warnings.append("import.candidate_no_label")
    if opening is None:
        warnings.append("import.candidate_no_opening")
    confidence = "HIGH" if label is not None and opening is not None else "REVIEW_REQUIRED"
    return {
        "label": label,
        "width_mm": str(width),
        "height_mm": str(height),
        "quantity": quantity,
        "opening_type": opening,
        "confidence": confidence,
        "warnings": warnings,
        "source_text": line.strip()[:200],
    }


def candidates_from_text(text: str) -> list[dict]:
    candidates = []
    for index, line in enumerate(text.splitlines()):
        candidate = parse_line(line)
        if candidate is not None:
            candidate["key"] = f"r{index}"
            candidates.append(candidate)
    return candidates


def candidates_from_rows(rows: list[list[object]]) -> list[dict]:
    text = "\n".join(
        " ".join(str(cell) for cell in row if cell is not None and str(cell).strip())
        for row in rows
    )
    return candidates_from_text(text)


def normalize_opening(value: object) -> str | None:
    """Confirm-time validation: only canonical openings are importable."""
    if isinstance(value, str) and value in _OPENING_TYPES:
        return value
    return None
