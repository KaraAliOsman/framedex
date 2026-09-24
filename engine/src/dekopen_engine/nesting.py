"""2D guillotine nesting for sheet stock (panels, monolithic glass).

Pure, deterministic, Decimal — mirrors cutting.py conventions. Pieces are placed
into sheet free-rectangles with a guillotine split (right + bottom remainders),
best-fit by remaining free area. No inferred compatibility: the caller groups
pieces by sheet rule; pieces larger than the usable sheet are returned under
``unplaced`` rather than silently dropped.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from pydantic import Field

from dekopen_engine.models import EngineModel


class PieceLargerThanUsableSheet(ValueError):
    pass


class NestPiece(EngineModel):
    piece_id: str = Field(min_length=1)
    workshop_sku: str
    width_mm: Decimal = Field(gt=Decimal("0"))
    height_mm: Decimal = Field(gt=Decimal("0"))
    source_position_id: str | None = None
    bay_id: str | None = None
    leaf_id: str | None = None
    unit_index: int = Field(ge=1, default=1)
    allow_rotation: bool = True


class SheetRule(EngineModel):
    workshop_sku: str
    purchasing_sku: str
    manufacturer_name: str | None = None
    supplier_name: str | None = None
    purchase_unit: Literal["SHEET"] = "SHEET"
    sheet_width_mm: Decimal = Field(gt=Decimal("0"))
    sheet_height_mm: Decimal = Field(gt=Decimal("0"))
    edge_trim_mm: Decimal = Field(ge=Decimal("0"), default=Decimal("0"))
    # Saw/score gap between pieces — 0 keeps legacy flush-abutment packing.
    kerf_mm: Decimal = Field(ge=Decimal("0"), default=Decimal("0"))
    # Smallest side a leftover rectangle must have to be reported as a
    # produced remnant; 0 reports every non-zero free rectangle.
    min_remnant_side_mm: Decimal = Field(ge=Decimal("0"), default=Decimal("0"))


class NestPlacement(NestPiece):
    sequence: int = Field(ge=1)
    x_mm: Decimal = Field(ge=Decimal("0"))
    y_mm: Decimal = Field(ge=Decimal("0"))
    rotated: bool = False


class SheetRemnant(EngineModel):
    """One on-hand sheet offcut available to the nest — zero procurement,
    consumed before any new sheet is opened."""

    remnant_id: str = Field(min_length=1)
    width_mm: Decimal = Field(gt=Decimal("0"))
    height_mm: Decimal = Field(gt=Decimal("0"))


class ProducedRemnant(EngineModel):
    """A free rectangle surviving on a packed sheet — returned so the caller
    can route it back into remnant stock."""

    x_mm: Decimal
    y_mm: Decimal
    width_mm: Decimal
    height_mm: Decimal


class SheetLayout(EngineModel):
    sheet_index: int
    purchasing_sku: str
    sheet_width_mm: Decimal
    sheet_height_mm: Decimal
    placements: list[NestPlacement]
    productive_area_mm2: Decimal
    waste_area_mm2: Decimal
    yield_pct: Decimal
    # REMNANT layouts consume on-hand stock and never appear on the purchase
    # list; their id is the ledger handle for reservation.
    source: Literal["NEW", "REMNANT"] = "NEW"
    remnant_id: str | None = None
    produced_remnants: list[ProducedRemnant] = Field(default_factory=list)


class SheetPurchase(EngineModel):
    purchasing_sku: str
    manufacturer_name: str | None
    supplier_name: str | None
    sheet_width_mm: Decimal
    sheet_height_mm: Decimal
    unit: Literal["SHEET"]
    qty_sheets: int


class SheetNestingResult(EngineModel):
    layouts: list[SheetLayout]
    purchase_list: list[SheetPurchase]
    unplaced: list[NestPiece]


@dataclass
class _FreeRect:
    x_mm: Decimal
    y_mm: Decimal
    width_mm: Decimal
    height_mm: Decimal


@dataclass
class _Placed:
    piece: NestPiece
    x_mm: Decimal
    y_mm: Decimal
    width_mm: Decimal
    height_mm: Decimal
    rotated: bool


@dataclass
class _SheetBin:
    free: list[_FreeRect] = field(default_factory=list)
    placed: list[_Placed] = field(default_factory=list)
    source: Literal["NEW", "REMNANT"] = "NEW"
    remnant_id: str | None = None
    bin_width_mm: Decimal = Decimal("0")
    bin_height_mm: Decimal = Decimal("0")


def _fits(width: Decimal, height: Decimal, rect: _FreeRect) -> bool:
    return width <= rect.width_mm and height <= rect.height_mm


def _piece_key(piece: NestPiece) -> tuple[Decimal, Decimal, str, int]:
    return (
        -max(piece.width_mm, piece.height_mm),
        -(piece.width_mm * piece.height_mm),
        piece.piece_id,
        piece.unit_index,
    )


def _piece_fits(piece: NestPiece, usable_w: Decimal, usable_h: Decimal) -> bool:
    rect = _FreeRect(Decimal("0"), Decimal("0"), usable_w, usable_h)
    if _fits(piece.width_mm, piece.height_mm, rect):
        return True
    return piece.allow_rotation and _fits(piece.height_mm, piece.width_mm, rect)


def _split(rect: _FreeRect, w: Decimal, h: Decimal, kerf: Decimal, mode: str) -> list[_FreeRect]:
    """Guillotine-split ``rect`` around a w×h placement at its origin,
    leaving ``kerf`` of saw gap between the piece and each remainder.

    mode "A": right remainder keeps full height, bottom keeps placed width.
    mode "B": right keeps placed height, bottom keeps full width.
    A remainder narrower than the kerf cannot host another cut — it is scrap
    and is not emitted."""
    x, y = rect.x_mm, rect.y_mm
    if mode == "A":
        candidates = (
            _FreeRect(x + w + kerf, y, rect.width_mm - w - kerf, rect.height_mm),
            _FreeRect(x, y + h + kerf, w, rect.height_mm - h - kerf),
        )
    else:
        candidates = (
            _FreeRect(x + w + kerf, y, rect.width_mm - w - kerf, h),
            _FreeRect(x, y + h + kerf, rect.width_mm, rect.height_mm - h - kerf),
        )
    return [c for c in candidates
            if c.width_mm > Decimal("0") and c.height_mm > Decimal("0")]


def _prune(free: list[_FreeRect]) -> list[_FreeRect]:
    """Drop free rectangles fully contained inside another — they can never
    host a piece the container could not, and they fragment the best-fit."""
    pruned: list[_FreeRect] = []
    for i, rect in enumerate(free):
        contained = any(
            j != i
            and rect.x_mm >= other.x_mm
            and rect.y_mm >= other.y_mm
            and rect.x_mm + rect.width_mm <= other.x_mm + other.width_mm
            and rect.y_mm + rect.height_mm <= other.y_mm + other.height_mm
            for j, other in enumerate(free)
        )
        if not contained:
            pruned.append(rect)
    return pruned


def _choose_split(
    rect: _FreeRect, w: Decimal, h: Decimal, kerf: Decimal, mode: str,
) -> list[_FreeRect]:
    """``mode`` "A"/"B" force one guillotine convention; "ADAPTIVE" picks the
    split preserving the largest single free rectangle (ties → A)."""
    if mode != "ADAPTIVE":
        return _split(rect, w, h, kerf, mode)
    splits = {m: _split(rect, w, h, kerf, m) for m in ("A", "B")}

    def score(rects: list[_FreeRect]) -> tuple[Decimal, Decimal]:
        if not rects:
            return (Decimal("0"), Decimal("0"))
        biggest = max(r.width_mm * r.height_mm for r in rects)
        total = sum((r.width_mm * r.height_mm for r in rects), Decimal("0"))
        return (biggest, total)

    score_a, score_b = score(splits["A"]), score(splits["B"])
    return splits["B"] if score_b > score_a else splits["A"]


def _pack(
    pieces: list[NestPiece],
    rule: SheetRule,
    remnant_bins: list[_SheetBin],
    split_mode: str,
) -> tuple[list[_SheetBin], list[NestPiece]]:
    """One full deterministic run of the guillotine packer. Remnant bins are
    already seeded (ascending area); new sheets append at the end, so a piece
    that fits any remnant never opens a new sheet."""
    usable_w = rule.sheet_width_mm - rule.edge_trim_mm * 2
    usable_h = rule.sheet_height_mm - rule.edge_trim_mm * 2
    kerf = rule.kerf_mm
    bins = [_SheetBin(free=list(rb.free), placed=[], source=rb.source,
                      remnant_id=rb.remnant_id, bin_width_mm=rb.bin_width_mm,
                      bin_height_mm=rb.bin_height_mm) for rb in remnant_bins]
    remnant_count = len(bins)
    unplaced: list[NestPiece] = []

    for piece in sorted(pieces, key=_piece_key):
        hostable = _piece_fits(piece, usable_w, usable_h) or any(
            _piece_fits(
                piece, b.bin_width_mm - rule.edge_trim_mm * 2,
                b.bin_height_mm - rule.edge_trim_mm * 2,
            )
            for b in bins[:remnant_count]
        )
        if not hostable:
            unplaced.append(piece)
            continue

        best: tuple[Decimal, int, int, bool] | None = None
        for sheet_i, sheet_bin in enumerate(bins):
            for rect_i, rect in enumerate(sheet_bin.free):
                orientations = [(False, piece.width_mm, piece.height_mm)]
                if piece.allow_rotation:
                    orientations.append((True, piece.height_mm, piece.width_mm))
                for rotated, w, h in orientations:
                    if not _fits(w, h, rect):
                        continue
                    leftover = rect.width_mm * rect.height_mm - w * h
                    if best is None or leftover < best[0]:
                        best = (leftover, sheet_i, rect_i, rotated)
        if best is None:
            bins.append(_SheetBin(
                free=[_FreeRect(
                    rule.edge_trim_mm, rule.edge_trim_mm, usable_w, usable_h,
                )],
                bin_width_mm=rule.sheet_width_mm,
                bin_height_mm=rule.sheet_height_mm,
            ))
            rect = bins[-1].free[0]
            rotated = False
            w, h = piece.width_mm, piece.height_mm
            if not _fits(w, h, rect) and piece.allow_rotation:
                w, h, rotated = h, w, True
            if not _fits(w, h, rect):
                unplaced.append(piece)
                continue
            best = (Decimal("0"), len(bins) - 1, 0, rotated)

        _, sheet_i, rect_i, rotated = best
        sheet_bin = bins[sheet_i]
        rect = sheet_bin.free.pop(rect_i)
        w = piece.height_mm if rotated else piece.width_mm
        h = piece.width_mm if rotated else piece.height_mm
        x, y = rect.x_mm, rect.y_mm
        sheet_bin.free.extend(_choose_split(rect, w, h, kerf, split_mode))
        sheet_bin.free = _prune(sheet_bin.free)
        sheet_bin.free.sort(key=lambda r: (r.y_mm, r.x_mm, -r.width_mm * r.height_mm))
        sheet_bin.placed.append(_Placed(piece, x, y, w, h, rotated))
    return bins, unplaced


def nest_rects(
    pieces: list[NestPiece],
    rule: SheetRule,
    *,
    remnants: list[SheetRemnant] | None = None,
) -> SheetNestingResult:
    """Best-fit guillotine nesting of ``pieces`` onto copies of ``rule`` stock.

    ``remnants``: on-hand sheet offcuts seeded as bins before any new sheet —
    smallest area first, so a piece lands on the tightest leftover that fits.
    Each layout reports surviving free rectangles as ``produced_remnants``.

    The packer runs all three split conventions (A, B, adaptive) and keeps the
    lexicographically best result — fewest unplaced, fewest sheets, most
    productive area. Deterministic: each run is itself deterministic and the
    comparison is a fixed key.
    """
    usable_w = rule.sheet_width_mm - rule.edge_trim_mm * 2
    usable_h = rule.sheet_height_mm - rule.edge_trim_mm * 2
    if usable_w <= Decimal("0") or usable_h <= Decimal("0"):
        raise PieceLargerThanUsableSheet("Edge trim consumes the whole sheet")

    seen: set[tuple[str, int]] = set()
    for piece in pieces:
        identity = (piece.piece_id, piece.unit_index)
        if identity in seen:
            raise ValueError("Duplicate piece identity")
        seen.add(identity)

    remnant_bins: list[_SheetBin] = []
    for remnant in sorted(
        remnants or [], key=lambda r: (r.width_mm * r.height_mm, r.remnant_id)
    ):
        rem_w = remnant.width_mm - rule.edge_trim_mm * 2
        rem_h = remnant.height_mm - rule.edge_trim_mm * 2
        if rem_w <= Decimal("0") or rem_h <= Decimal("0"):
            continue  # consumed entirely by trim — already scrap
        remnant_bins.append(_SheetBin(
            free=[_FreeRect(rule.edge_trim_mm, rule.edge_trim_mm, rem_w, rem_h)],
            source="REMNANT", remnant_id=remnant.remnant_id,
            bin_width_mm=remnant.width_mm, bin_height_mm=remnant.height_mm,
        ))

    candidates = [_pack(pieces, rule, remnant_bins, mode)
                  for mode in ("ADAPTIVE", "A", "B")]

    def plan_key(candidate: tuple[list[_SheetBin], list[NestPiece]]) -> tuple[int, int, Decimal]:
        plan_bins, plan_unplaced = candidate
        used = [b for b in plan_bins if b.placed]
        new_used = [b for b in used if b.source == "NEW"]
        productive = sum(
            (p.width_mm * p.height_mm for b in used for p in b.placed),
            Decimal("0"),
        )
        return (len(plan_unplaced), len(new_used), -productive)

    bins, unplaced = min(candidates, key=plan_key)

    layouts: list[SheetLayout] = []
    remnant_index = 0
    new_index = 0
    for index, sheet_bin in enumerate(bins):
        if not sheet_bin.placed:
            continue
        sequence: list[NestPlacement] = []
        productive = Decimal("0")
        for seq, placed in enumerate(sheet_bin.placed, start=1):
            sequence.append(NestPlacement(
                **placed.piece.model_dump(exclude={"width_mm", "height_mm"}),
                sequence=seq, x_mm=placed.x_mm, y_mm=placed.y_mm,
                rotated=placed.rotated, width_mm=placed.width_mm,
                height_mm=placed.height_mm,
            ))
            productive += placed.width_mm * placed.height_mm
        bin_area = sheet_bin.bin_width_mm * sheet_bin.bin_height_mm
        yield_exact = productive / bin_area * Decimal("100")
        if sheet_bin.source == "REMNANT":
            remnant_index += 1
            sheet_index = remnant_index
        else:
            new_index += 1
            sheet_index = new_index
        keep = rule.min_remnant_side_mm
        produced = [
            ProducedRemnant(x_mm=r.x_mm, y_mm=r.y_mm,
                            width_mm=r.width_mm, height_mm=r.height_mm)
            for r in sheet_bin.free
            if r.width_mm >= keep and r.height_mm >= keep
        ]
        layouts.append(SheetLayout(
            sheet_index=sheet_index,
            purchasing_sku=rule.purchasing_sku,
            sheet_width_mm=sheet_bin.bin_width_mm,
            sheet_height_mm=sheet_bin.bin_height_mm,
            placements=sequence,
            productive_area_mm2=productive,
            waste_area_mm2=bin_area - productive,
            yield_pct=yield_exact.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            source=sheet_bin.source,
            remnant_id=sheet_bin.remnant_id,
            produced_remnants=produced,
        ))
    new_layouts = [layout for layout in layouts if layout.source == "NEW"]
    return SheetNestingResult(
        layouts=layouts,
        purchase_list=[SheetPurchase(
            purchasing_sku=rule.purchasing_sku,
            manufacturer_name=rule.manufacturer_name,
            supplier_name=rule.supplier_name,
            sheet_width_mm=rule.sheet_width_mm,
            sheet_height_mm=rule.sheet_height_mm,
            unit="SHEET",
            qty_sheets=len(new_layouts),
        )] if new_layouts else [],
        unplaced=unplaced,
    )
