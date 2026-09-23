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


class NestPlacement(NestPiece):
    sequence: int = Field(ge=1)
    x_mm: Decimal = Field(ge=Decimal("0"))
    y_mm: Decimal = Field(ge=Decimal("0"))
    rotated: bool = False


class SheetLayout(EngineModel):
    sheet_index: int
    purchasing_sku: str
    sheet_width_mm: Decimal
    sheet_height_mm: Decimal
    placements: list[NestPlacement]
    productive_area_mm2: Decimal
    waste_area_mm2: Decimal
    yield_pct: Decimal


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


def nest_rects(pieces: list[NestPiece], rule: SheetRule) -> SheetNestingResult:
    """Best-fit guillotine nesting of ``pieces`` onto copies of ``rule`` stock."""
    usable_w = rule.sheet_width_mm - rule.edge_trim_mm * 2
    usable_h = rule.sheet_height_mm - rule.edge_trim_mm * 2
    if usable_w <= Decimal("0") or usable_h <= Decimal("0"):
        raise PieceLargerThanUsableSheet("Edge trim consumes the whole sheet")

    seen: set[tuple[str, int]] = set()
    bins: list[_SheetBin] = []
    unplaced: list[NestPiece] = []

    for piece in sorted(pieces, key=_piece_key):
        identity = (piece.piece_id, piece.unit_index)
        if identity in seen:
            raise ValueError("Duplicate piece identity")
        seen.add(identity)
        if not _piece_fits(piece, usable_w, usable_h):
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
            bins.append(_SheetBin(free=[_FreeRect(
                rule.edge_trim_mm, rule.edge_trim_mm, usable_w, usable_h,
            )]))
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
        # Guillotine split: right remainder keeps full height; bottom keeps placed width.
        for candidate in (
            _FreeRect(x + w, y, rect.width_mm - w, rect.height_mm),
            _FreeRect(x, y + h, w, rect.height_mm - h),
        ):
            if candidate.width_mm > Decimal("0") and candidate.height_mm > Decimal("0"):
                sheet_bin.free.append(candidate)
        sheet_bin.free.sort(key=lambda r: (r.y_mm, r.x_mm, -r.width_mm * r.height_mm))
        sheet_bin.placed.append(_Placed(piece, x, y, w, h, rotated))

    layouts: list[SheetLayout] = []
    sheet_area = rule.sheet_width_mm * rule.sheet_height_mm
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
        yield_exact = productive / sheet_area * Decimal("100")
        layouts.append(SheetLayout(
            sheet_index=index + 1,
            purchasing_sku=rule.purchasing_sku,
            sheet_width_mm=rule.sheet_width_mm,
            sheet_height_mm=rule.sheet_height_mm,
            placements=sequence,
            productive_area_mm2=productive,
            waste_area_mm2=sheet_area - productive,
            yield_pct=yield_exact.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
        ))
    return SheetNestingResult(
        layouts=layouts,
        purchase_list=[SheetPurchase(
            purchasing_sku=rule.purchasing_sku,
            manufacturer_name=rule.manufacturer_name,
            supplier_name=rule.supplier_name,
            sheet_width_mm=rule.sheet_width_mm,
            sheet_height_mm=rule.sheet_height_mm,
            unit="SHEET",
            qty_sheets=len(layouts),
        )] if layouts else [],
        unplaced=unplaced,
    )
