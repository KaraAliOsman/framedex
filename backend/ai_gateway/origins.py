"""Where each window the agent creates comes from (P08).

A window proposed from a request (a pasted WhatsApp, an email, a dictated
note) cites the literal phrase it was read from. The server locates that
phrase in the request and checks that the window's measures and quantity
are written there; a window without a locatable origin is not created —
the line stays without price instead of being guessed.

Assumptions are computed here, never taken from the model: every
non-numeric choice the phrase does not state (series, glass, finish,
opening) is listed so the person confirms it before issuing.
"""

from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Any

MAX_QUOTE = 400
MEASURES = frozenset({"width_mm", "height_mm"})

_NUMBER = re.compile(
    r"(?<![\d.,])(\d{1,5}(?:[.,]\d{1,3})?)(?![\d])"
    r"(?:\s*(mm|cm|mts?|metros?|m)(?![a-záéíóúñ]))?",
    re.IGNORECASE,
)
_WORD_COUNTS = {
    "un": 1, "una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12,
}
# Words that state an opening; without one the opening is an assumption.
_OPENING_WORDS = re.compile(
    r"fij|oscilo|abat|batient|abr[aei]|hojas?\b|corred|proyect|puerta|guillotin|plegab|pivot",
    re.IGNORECASE,
)


def _folded(text: str) -> tuple[str, list[int]]:
    """Case- and accent-folded text plus, per folded character, the index of
    the source character it came from — so a match maps back exactly."""
    chars: list[str] = []
    origin: list[int] = []
    for index, char in enumerate(text):
        for part in unicodedata.normalize("NFKD", char.casefold()):
            if not unicodedata.combining(part):
                chars.append(part)
                origin.append(index)
    return "".join(chars), origin


def _fold(text: str) -> str:
    return _folded(text)[0]


def locate(quote: str, sources: list[str]) -> dict | None:
    """The span of ``quote`` inside one of ``sources``, tolerant only to
    case, accents and whitespace — never to different words or numbers."""
    words = _fold(quote).split()
    if not words or len(quote) > MAX_QUOTE:
        return None
    pattern = re.compile(r"\s+".join(re.escape(word) for word in words))
    for index, source in enumerate(sources):
        folded, origin = _folded(source)
        match = pattern.search(folded)
        if match:
            start, end = origin[match.start()], origin[match.end() - 1] + 1
            return {"source": index, "start": start, "end": end, "quote": source[start:end]}
    return None


def _decimal(raw: str) -> Decimal | None:
    try:
        return Decimal(raw.replace(",", "."))
    except InvalidOperation:
        return None


def measures_mm(quote: str) -> set[Decimal]:
    """Every millimetre value the phrase can mean. A bare number reads as
    mm, as metres when it has decimals or is under 10, and as centimetres
    between 10 and 300 («120x150»). The window still has to match one."""
    values: set[Decimal] = set()
    for raw, unit in _NUMBER.findall(quote):
        value = _decimal(raw)
        if value is None or value <= 0:
            continue
        unit = unit.lower()
        if unit == "mm":
            values.add(value)
        elif unit == "cm":
            values.add(value * 10)
        elif unit:
            values.add(value * 1000)
        else:
            values.add(value)
            if "," in raw or "." in raw or value < 10:
                values.add(value * 1000)
            if 10 <= value <= 300:
                values.add(value * 10)
    return {value.normalize() for value in values}


def counts(quote: str) -> set[int]:
    found = {int(raw) for raw, unit in _NUMBER.findall(quote)
             if not unit and raw.isdigit() and int(raw) <= 999}
    found |= {_WORD_COUNTS[word] for word in re.findall(r"[a-záéíóúñ]+", _fold(quote))
              if word in _WORD_COUNTS}
    return found


def _mm(value: Any) -> Decimal | None:
    parsed = _decimal(str(value)) if value is not None else None
    return parsed.normalize() if parsed is not None else None


def check(op: dict, quote: str) -> str | None:
    """None when the phrase states this window's measures and quantity;
    otherwise the reason the window cannot be created from it. A measure the
    client did not give is never assumed: the agent asks for it."""
    dims = op.get("dims") if isinstance(op.get("dims"), dict) else {}
    stated = measures_mm(quote)
    for field in sorted(MEASURES):
        value = _mm(dims.get(field))
        if value is None or value not in stated:
            return "origin_measure_missing"
    quantity = op.get("quantity", 1)
    if quantity != 1 and quantity not in counts(quote):
        return "origin_quantity_missing"
    return None


def _reason(value: Any) -> str:
    """A model-written reason is shown only when it cites no number."""
    text = str(value or "").strip()[:200]
    return "" if re.search(r"\d", text) else text


# A sentence: a dot ends it only before a space («1.800» stays one number).
_SEGMENT = re.compile(r"(?:[^\n.;!?]|\.(?!\s|$))+(?:[.;!?](?=\s|$))?")


# A clause boundary: a comma not between digits, a semicolon or « y ».
_CLAUSE = re.compile(r",(?!\d)|;|\s+y\s+", re.IGNORECASE)


def _clauses(source: str) -> list[tuple[int, int]]:
    """Spans of each sentence and of each run of its clauses."""
    spans: list[tuple[int, int]] = []
    for match in _SEGMENT.finditer(source):
        start, end = match.span()
        pieces, cursor = [], start
        for cut in _CLAUSE.finditer(source, start, end):
            pieces.append((cursor, cut.start()))
            cursor = cut.end()
        pieces.append((cursor, end))
        for first in range(len(pieces)):
            for last in range(first, len(pieces)):
                spans.append((pieces[first][0], pieces[last][1]))
    return spans


def _find(op: dict, sources: list[str]) -> dict | None:
    """Without a cited phrase, the shortest clause run of the request that
    states this window's measures and quantity becomes its origin."""
    best: dict | None = None
    for index, source in enumerate(sources):
        for start, end in _clauses(source):
            segment = source[start:end]
            stripped = segment.strip(" \t\n.,;")
            if not stripped or len(stripped) > MAX_QUOTE or check(op, stripped) is not None:
                continue
            if best is None or len(stripped) < len(best["quote"]):
                begin = start + segment.index(stripped)
                best = {"source": index, "start": begin, "end": begin + len(stripped), "quote": stripped}
    return best


def bind(ops: Any, sources: list[str]) -> tuple[Any, list[dict], list[dict]]:
    """Split each ``add_position`` from its cited origin. Returns the ops the
    engine may preview (origins removed), the origins aligned to those ops
    and the windows refused because their origin is missing or mismatched."""
    if not isinstance(ops, list):
        return ops, [], []
    kept: list = []
    origins: list[dict] = []
    refused: list[dict] = []
    for op in ops:
        if not isinstance(op, dict):
            kept.append(op)
            continue
        op = dict(op)
        raw = op.pop("origin", None)
        if op.get("op") != "add_position":
            kept.append(op)
            continue
        raw = raw if isinstance(raw, dict) else {"quote": raw}
        quote = raw.get("quote")
        span = locate(quote, sources) if isinstance(quote, str) else _find(op, sources)
        reason = "origin_missing" if span is None else check(op, span["quote"])
        if reason:
            refused.append({"op": "add_position", "reason": reason,
                            "location": str(op.get("location") or "")[:120],
                            **({"quote": span["quote"]} if span else {})})
            continue
        notes = raw.get("reasons") if isinstance(raw.get("reasons"), dict) else {}
        origins.append({"op_index": len(kept), **span,
                        "reasons": {str(key): _reason(value) for key, value in notes.items()}})
        kept.append(op)
    return kept, origins, refused


def _appended(op: dict) -> int:
    name = op.get("op")
    if name in ("add_position", "add_design_position"):
        return 1
    if name == "duplicate_position":
        return int(op.get("count") or 0)
    if name == "duplicate_positions":
        return len(op.get("position_ids") or [])
    return 0


def attach(origins: list[dict], ops: list, simulation: dict) -> list[dict]:
    """Bind each origin to the window the engine preview created for its op."""
    if not origins:
        return []
    before = {change["after"]["id"] for change in simulation.get("diff") or []
              if change.get("kind") != "add" and change.get("after")}
    added = [change["after"] for change in simulation.get("diff") or []
             if change.get("kind") == "add" and change.get("after")]
    added = [position for position in added if position["id"] not in before]
    offsets, cursor = {}, 0
    for index, op in enumerate(ops):
        if isinstance(op, dict):
            offsets[index] = cursor
            cursor += _appended(op)
    if cursor != len(added):
        return [{key: value for key, value in origin.items() if key != "op_index"}
                for origin in origins]
    bound = []
    for origin in origins:
        position = added[offsets[origin["op_index"]]]
        bound.append({
            "position_id": str(position["id"]),
            "location": str(position.get("location_tag") or ""),
            **{key: value for key, value in origin.items() if key not in ("op_index", "reasons")},
        })
    return bound


def assumptions(origins: list[dict], ops: list, usual: dict, labels: dict, request: str = "") -> list[dict]:
    """The choices the windows make that the request does not state.

    «usual» entries (the company's habitual series, glass or finish) are
    grouped once per value; «agent» entries — a series, glass, finish or
    opening the agent chose — are listed per window for the person to
    confirm before issuing. Measures are never assumed."""
    found: list[dict] = []
    habitual: dict[tuple[str, str], dict] = {}
    by_index = {origin["op_index"]: origin for origin in origins}
    usual_values = {key: (value or {}).get("value") for key, value in (usual or {}).items()}
    stated = _fold(request)

    def note(window: str, field: str, value: str, usual_key: str, raw: str, reasons: dict) -> None:
        if raw == str(usual_values.get(usual_key) or ""):
            entry = habitual.setdefault((field, value), {"field": field, "value": value, "source": "usual", "locations": []})
            entry["locations"].append(window)
        else:
            found.append({"location": window, "field": field, "value": value, "source": "agent",
                          "reason": reasons.get(usual_key, "")})

    for index, op in enumerate(ops):
        origin = by_index.get(index)
        if origin is None or not isinstance(op, dict):
            continue
        quote = _fold(origin["quote"])
        window = str(op.get("location") or "")[:120]
        reasons = origin.get("reasons") or {}
        system = str(op.get("system_id") or "")
        system_label = labels.get(system, "")
        if system_label and not any(_fold(part) in stated for part in system_label.split(" · ") if part):
            note(window, "series", system_label, "system_id", system, reasons)
        glass = str(op.get("glass_sku") or "")
        if glass and _fold(glass) not in stated:
            note(window, "glass", labels.get(glass, glass), "glass_article_sku", glass, reasons)
        color = str(op.get("color") or "")
        if color and _fold(labels.get(color, color)) not in stated:
            note(window, "color", labels.get(color, color), "color", color, reasons)
        if not _OPENING_WORDS.search(quote):
            template = str(op.get("template") or "")
            found.append({"location": window, "field": "opening", "value": labels.get(template, template),
                          "source": "agent", "reason": reasons.get("template", "")})
    return [*found, *habitual.values()]


__all__ = ["assumptions", "attach", "bind", "check", "counts", "locate", "measures_mm"]
