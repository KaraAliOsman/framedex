"""Deterministic window-schedule parsing — the first extraction pass.

Extraction confidence is a review aid, never authorization: only HIGH rows
auto-check the include flag, and nothing reaches a position without the
estimator's explicit confirm."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

_LABEL = re.compile(r"\b([A-Za-z]{1,4}[-_]?[A-Za-z]?\d{1,3}|\d{1,3}[A-Za-z])\b")
_DIMENSION = re.compile(r"\b(\d{3,5})\s*[x×]\s*(\d{3,5})\b")
_INTEGER = re.compile(r"\b(\d{1,3})\b")
# Insulated-glass compositions (4-12-4, 4+16+4, 4/12/4) read as integers —
# they must be masked before quantity scanning or the pane count lands in
# quantity (a "DVH 4-12-4" row is one unit, not four).
_GLASS_COMPOSITION = re.compile(
    r"\b\d{1,3}\s*[-+/]\s*\d{1,3}(?:\s*[-+/]\s*\d{1,3})?\b"
)

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
    # Quantity: a bare small integer that is not part of the WxH pair nor of
    # the label (V-10 fijo 1200x1000 is one window, not ten).
    quantity = 1
    mask = list(line)
    spans = [dimension.span(0)]
    if label_match:
        spans.append(label_match.span(1))
    spans.extend(match.span(0) for match in _GLASS_COMPOSITION.finditer(line))
    for lo, hi in spans:
        for index in range(lo, hi):
            mask[index] = " "
    rest = "".join(mask)
    quantity_candidates = [
        int(found) for found in _INTEGER.findall(rest) if 0 < int(found) < 100
    ]
    if quantity_candidates:
        quantity = quantity_candidates[-1]
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
