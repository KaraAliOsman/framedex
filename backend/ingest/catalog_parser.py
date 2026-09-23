"""Deterministic catalog-article parser — supplier rows become article candidates.

A row is HIGH-confidence when sku + name + role + face width all parse; anything
missing drops to REVIEW_REQUIRED with a reason, never to invented values.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

ROLES = (
    "FRAME",
    "SASH",
    "MULLION_V",
    "MULLION_H",
    "INVERSOR",
    "GLAZING_BEAD",
    "COUPLER",
    "THRESHOLD",
    "ADDITIONAL",
)

_ROLE_KEYWORDS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("marco", "frame", "kasa"), "FRAME"),
    (("hoja", "sash", "ventana"), "SASH"),
    (("montante", "mullion", "vertical"), "MULLION_V"),
    (("travesa", "horizontal", "jamba", "riel", "guia", "rail"), "MULLION_H"),
    (("inversor", "adaptador", "inverter"), "INVERSOR"),
    (("contravidrio", "junta", "vidrio", "bead", "clip"), "GLAZING_BEAD"),
    (("acoplamiento", "bayo", "coupler", "union", "acople"), "COUPLER"),
    (("umbral", "threshold", "zocalo"), "THRESHOLD"),
    (("refuerzo", "steel", "acero", "reinforcement"), "ADDITIONAL"),
    (("tapa", "tapacanal", "cover", "cap"), "ADDITIONAL"),
)

_SKU = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\-_/]{0,29}$")
_NUMBER = re.compile(r"\d{1,5}(?:[.,]\d{1,4})?")
_KG_M = re.compile(r"(\d{1,3}(?:[.,]\d{1,4})?)\s*kg/?m", re.IGNORECASE)
_MM = re.compile(r"(\d{1,4}(?:[.,]\d{1,4})?)\s*mm", re.IGNORECASE)
_REINFORCEMENT = re.compile(
    r"(?:refuerzo|acero|steel|ref\.)\s*[:#]?\s*([A-Za-z0-9][A-Za-z0-9.\-_/]{0,29})",
    re.IGNORECASE,
)


def _decimal(token: str) -> Decimal | None:
    try:
        return Decimal(token.replace(",", "."))
    except InvalidOperation:
        return None


def _role_of(text: str) -> str | None:
    lowered = text.lower()
    for keywords, role in _ROLE_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return role
    return None


def parse_article_line(line: str, key: str) -> dict[str, Any] | None:
    """Parse one catalog row; None when the line carries no article signal."""
    stripped = line.strip()
    if len(stripped) < 4:
        return None
    tokens = stripped.split()
    if not tokens or not _SKU.match(tokens[0]):
        return None
    sku = tokens[0].upper()
    if not any(ch.isdigit() for ch in sku):
        return None
    rest = " ".join(tokens[1:])

    warnings: list[str] = []
    name_parts: list[str] = []
    numeric_spans: list[tuple[int, int]] = []

    kg_match = _KG_M.search(rest)
    weight = _decimal(kg_match.group(1)) if kg_match else None
    if kg_match:
        numeric_spans.append(kg_match.span(1))

    reinforcement = _REINFORCEMENT.search(rest)
    reinforcement_sku = reinforcement.group(1).upper() if reinforcement else None

    face_width: Decimal | None = None
    for match in _MM.finditer(rest):
        value = _decimal(match.group(1))
        if value is not None and Decimal(5) <= value <= Decimal(300):
            face_width = value
            numeric_spans.append(match.span(0))
            break

    role = _role_of(rest)

    def _masked(span: tuple[int, int]) -> bool:
        return any(
            span[0] < other[1] and span[1] > other[0] for other in numeric_spans
        )

    for match in _NUMBER.finditer(rest):
        if _masked(match.span(0)):
            continue
        start, end = match.span(0)
        if start > 0 and not name_parts:
            name_parts.append(rest[:start])
        break

    name = re.sub(r"[|,;:\s]+$", "", (name_parts[0] if name_parts else rest).strip(" |,;:"))
    name = re.sub(r"\s{2,}", " ", name).strip()
    if len(name) > 120:
        name = name[:117].rstrip() + "..."

    if not name:
        warnings.append("catalog_name_missing")
        name = sku
    if role is None:
        warnings.append("catalog_role_unknown")
    if face_width is None:
        warnings.append("catalog_face_width_missing")

    return {
        "key": key,
        "sku": sku,
        "name": name,
        "role": role or "ADDITIONAL",
        "face_width_mm": face_width,
        "commercial_length_mm": None,
        "welding_loss_mm": None,
        "reinforcement_sku": reinforcement_sku,
        "weight_kg_m": weight,
        "steel_weight_kg_m": None,
        "confidence": "HIGH" if not warnings else "REVIEW_REQUIRED",
        "warnings": warnings,
        "source_text": stripped[:300],
    }


def parse_catalog_lines(lines: list[str]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, line in enumerate(lines):
        parsed = parse_article_line(line, key=f"c{index}")
        if parsed is None or parsed["sku"] in seen:
            continue
        seen.add(parsed["sku"])
        candidates.append(parsed)
    return candidates
