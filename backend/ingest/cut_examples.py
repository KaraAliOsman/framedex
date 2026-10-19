"""Manufacturer cut templates (worked cut sheets) read deterministically.

A cut template is a set of solved examples: for one window size it lists each
profile, quantity, cut length, cut angles and position. It is not a rule
book. DEKOPEN keeps the examples with their page and literal row so they can
verify declared cut rules, reports offsets that hold across examples of
different size as observations for a technical reviewer — never as published
authority — and reports the source's own inconsistencies without fixing them.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
import re

_SIZE = re.compile(r"Tama[ñn]o:\s*(\d+)\s*mm\s*x\s*(\d+)\s*mm", re.I)
_LINE = re.compile(r"Linea:\s*(.+)", re.I)
# DESCRIPCION ... CANT LARGO A1° A2° [POSICION]
_ROW = re.compile(
    r"^(?P<desc>.+?)\s+(?P<qty>\d+)\s+(?P<length>\d+(?:[.,]\d+)?)\s+(?P<a1>\d{2})°\s+(?P<a2>\d{2})°\s*(?P<pos>.*)$"
)
# A row whose length cell carries a spreadsheet error instead of a number.
_BROKEN = re.compile(r"^(?P<desc>.+?)\s+(?P<qty>\d+)\s+(?P<value>#[A-Z/0!?]+)\s+(?P<a1>\d{2})°")
_CODE = re.compile(r"\b(PRO[\s-]?R?\d+[A-Z]?|R\d)\b")
_GLASS = re.compile(r"^V\d+\s+(\d+)\s+(\d+)\s+(\d+)(?:\s+(\w+))?")


def _decimal(text: str) -> Decimal:
    return Decimal(text.replace(",", "."))


def _rows(lines: list[str], page: int) -> tuple[list[dict], list[dict], list[dict]]:
    rows: list[dict] = []
    glass: list[dict] = []
    broken: list[dict] = []
    for line in lines:
        match = _ROW.match(line)
        if match:
            description = match["desc"].strip()
            code = _CODE.search(description)
            rows.append({
                "description": description,
                "code": re.sub(r"[\s-]+", "", code.group(1)) if code else None,
                "quantity": int(match["qty"]),
                "length_mm": str(_decimal(match["length"])),
                "angles": [int(match["a1"]), int(match["a2"])],
                "position": match["pos"].strip() or None,
                "literal": line,
                "page": page,
            })
            continue
        bad = _BROKEN.match(line)
        if bad:
            broken.append({"page": page, "literal": line, "value": bad["value"]})
            continue
        glass_match = _GLASS.match(line)
        if glass_match:
            glass.append({
                "width_mm": glass_match[1],
                "height_mm": glass_match[2],
                "quantity": int(glass_match[3]),
                "position": glass_match[4],
                "literal": line,
                "page": page,
            })
        elif re.match(r"^V\d+\s+#", line):
            broken.append({"page": page, "literal": line, "value": "#"})
    return rows, glass, broken


def parse_sheet(text: str, page: int) -> dict | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    size = next((_SIZE.search(line) for line in lines if _SIZE.search(line)), None)
    if not size or not any("ANGULO DE CORTE" in line.upper() for line in lines):
        return None
    line_name = next((_LINE.search(line).group(1).strip() for line in lines if _LINE.search(line)), None)
    title_index = next((index for index, line in enumerate(lines) if line.upper() == "HOJA DE CORTE"), None)
    typology = None
    if title_index is not None:
        typology = " ".join(lines[title_index + 1:title_index + 4]).strip(" -") or None
    rows, glass, broken = _rows(lines, page)
    return {
        "page": page,
        "pages": [page],
        "line": line_name,
        "typology": typology,
        "width_mm": size.group(1),
        "height_mm": size.group(2),
        "rows": rows,
        "glass": glass,
        "source_errors": broken,
    }


def parse_template(tagged: list[tuple[str, str]]) -> list[dict]:
    """tagged = [(text line, «página N»)] → one example per cut sheet,
    joining a table that continues on the following page."""
    pages: dict[int, list[str]] = defaultdict(list)
    for text, ref in tagged:
        match = re.search(r"(\d+)", ref or "")
        if match:
            pages[int(match.group(1))].append(text)
    examples: list[dict] = []
    for page in sorted(pages):
        text = "\n".join(pages[page])
        sheet = parse_sheet(text, page)
        if sheet:
            examples.append(sheet)
            continue
        if examples and page == examples[-1]["pages"][-1] + 1:
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            rows, glass, broken = _rows(lines, page)
            if rows or glass or broken:
                examples[-1]["pages"].append(page)
                examples[-1]["rows"].extend(rows)
                examples[-1]["glass"].extend(glass)
                examples[-1]["source_errors"].extend(broken)
    for example in examples:
        example["notes"] = _notes(example)
    return [example for example in examples if example["rows"]]


def _notes(example: dict) -> list[str]:
    """Inconsistencies of the source itself, reported, never corrected."""
    notes = []
    title = (example.get("typology") or "").upper()
    descriptions = " ".join(row["description"].upper() for row in example["rows"])
    if "PUERTA" in title and "CORREDERA" in descriptions and "HOJA PUERTA" not in descriptions:
        notes.append("El título dice puerta pero los perfiles son de corredera.")
    if example["source_errors"]:
        notes.append(
            f"{len(example['source_errors'])} medida(s) traen un error de planilla "
            f"({example['source_errors'][0]['value']}) en vez de un número."
        )
    if any(not row.get("position") for row in example["rows"]):
        notes.append("Algunas filas no indican su posición en la misma página.")
    return notes


def _base(row: dict, example: dict) -> tuple[str, Decimal] | None:
    position = (row.get("position") or "").replace("A:", "")
    if "Abajo" in position or "Arriba" in position:
        return "width", _decimal(example["width_mm"])
    if "Der" in position or "Izq" in position:
        return "height", _decimal(example["height_mm"])
    return None


def _groups(examples: list[dict], with_typology: bool) -> dict:
    groups: dict[tuple, list[tuple[Decimal, int, str, Decimal]]] = defaultdict(list)
    for example in examples:
        for row in example["rows"]:
            base = _base(row, example)
            if not base or not row.get("code"):
                continue
            side, dimension = base
            key = (
                example["line"],
                example["typology"] if with_typology else None,
                row["code"],
                side,
                tuple(row["angles"]),
            )
            groups[key].append((_decimal(row["length_mm"]) - dimension, row["page"], row["literal"], dimension))
    return groups


def consistent_offsets(examples: list[dict]) -> list[dict]:
    """Offset between cut length and the window dimension per (line, profile,
    side, angles), kept only when identical in examples of two or more sizes:
    first across every typology, otherwise per typology."""
    observations: list[dict] = []
    covered: set = set()
    for with_typology in (False, True):
        for key, values in _groups(examples, with_typology).items():
            line, typology, code, side, angles = key
            if (line, code, side, angles) in covered:
                continue
            offsets = {value[0] for value in values}
            sizes = {value[3] for value in values}
            if len(values) >= 2 and len(sizes) >= 2 and len(offsets) == 1:
                covered.add((line, code, side, angles))
                observations.append({
                    "line": line,
                    "typology": typology,
                    "code": code,
                    "side": side,
                    "angles": list(angles),
                    "offset_mm": str(next(iter(offsets))),
                    "examples": [{"page": value[1], "literal": value[2]} for value in values],
                })
    return observations


def summary(examples: list[dict]) -> dict:
    return {
        "sheets": len(examples),
        "lines": sorted({example["line"] for example in examples if example["line"]}),
        "typologies": sorted({example["typology"] for example in examples if example["typology"]}),
        "profiles": sorted({row["code"] for example in examples for row in example["rows"] if row["code"]}),
        "consistent_offsets": consistent_offsets(examples),
        "source_notes": [
            {"pages": example["pages"], "note": note} for example in examples for note in example["notes"]
        ],
    }
