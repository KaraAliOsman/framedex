"""Pure DIN elevation primitives. Dimensions are drawing coordinates in mm.

SYMBOL_TEMPLATES is the grammar source; scripts/generate_opening_symbols.py
exports it for React. No manufacturing capacity is implied by a glyph.
"""

from dataclasses import dataclass
from decimal import Decimal

from .models import Opening, OpeningDirection, OpeningMovement, SlidingTravel

# Normalized coordinates are strings, avoiding binary floats in the engine.
SYMBOL_TEMPLATES: dict[str, tuple[tuple[str, str], ...]] = {
    "turn_left": (("0.2", "0.2"), ("0.8", "0.5"), ("0.2", "0.8")),
    "turn_right": (("0.8", "0.2"), ("0.2", "0.5"), ("0.8", "0.8")),
    "tilt": (("0.2", "0.8"), ("0.5", "0.2"), ("0.8", "0.8")),
    "awning": (("0.2", "0.2"), ("0.5", "0.8"), ("0.8", "0.2")),
    "slide_right": (("0.25", "0.5"), ("0.75", "0.5")),
    "slide_right_head": (("0.65", "0.44"), ("0.75", "0.5"), ("0.65", "0.56")),
    "slide_left": (("0.75", "0.5"), ("0.25", "0.5")),
    "slide_left_head": (("0.35", "0.44"), ("0.25", "0.5"), ("0.35", "0.56")),
    "lift": (("0.5", "0.7"), ("0.5", "0.6")),
    "parallel": (("0.3", "0.65"), ("0.5", "0.7"), ("0.7", "0.65")),
    "fold": (("0.2", "0.2"), ("0.4", "0.8"), ("0.6", "0.2"), ("0.8", "0.8")),
    "pivot_v": (("0.5", "0.2"), ("0.5", "0.8")),
    "pivot_h": (("0.2", "0.5"), ("0.8", "0.5")),
    "vertical_slide": (("0.5", "0.75"), ("0.5", "0.25")),
    "vertical_slide_head": (("0.44", "0.35"), ("0.5", "0.25"), ("0.56", "0.35")),
}


@dataclass(frozen=True)
class SymbolLine:
    symbol: str
    points: tuple[tuple[Decimal, Decimal], ...]
    dashed: bool


def symbol_names(opening: Opening, travel: SlidingTravel | None = None) -> tuple[str, ...]:
    movement = opening.movement
    names: tuple[str, ...] = ()
    if movement in (OpeningMovement.TURN, OpeningMovement.TILT_TURN):
        # Unknown historical door handing stays unknown; never assume left.
        if opening.hinge_side.value in ("LEFT", "RIGHT"):
            names += ("turn_" + opening.hinge_side.value.lower(),)
    if movement in (OpeningMovement.TILT, OpeningMovement.TILT_TURN, OpeningMovement.BOTTOM_HUNG):
        names += ("tilt",)
    if movement is OpeningMovement.TOP_HUNG:
        names += ("awning",)
    if movement in (OpeningMovement.SLIDE, OpeningMovement.LIFT_SLIDE, OpeningMovement.PARALLEL_SLIDE):
        if travel is not None:
            stem = "slide_" + travel.value.lower()
            names += (stem, stem + "_head")
        if movement is OpeningMovement.LIFT_SLIDE:
            names += ("lift",)
        if movement is OpeningMovement.PARALLEL_SLIDE:
            names += ("parallel",)
    if movement is OpeningMovement.FOLD:
        names += ("fold",)
    if movement in (OpeningMovement.PIVOT_V, OpeningMovement.PIVOT_H):
        names += (movement.value.lower(),)
    if movement is OpeningMovement.VERTICAL_SLIDE:
        names += ("vertical_slide", "vertical_slide_head")
    return names


def opening_symbol_lines(opening: Opening, *, x: Decimal, y: Decimal,
                         width: Decimal, height: Decimal, exterior: bool = False,
                         mirror: bool = True, travel: SlidingTravel | None = None) -> tuple[SymbolLine, ...]:
    """Affine drawing projection; direction and viewpoint never change intent."""
    if width <= 0 or height <= 0:
        raise ValueError("El símbolo necesita un rectángulo válido.")
    sliding = opening.movement in (OpeningMovement.SLIDE, OpeningMovement.LIFT_SLIDE,
                                  OpeningMovement.PARALLEL_SLIDE, OpeningMovement.VERTICAL_SLIDE)
    dashed = not sliding and ((opening.direction is OpeningDirection.OUTWARD) != exterior)
    return tuple(SymbolLine(name, tuple((x + width * (Decimal("1") - Decimal(px)
                   if exterior and mirror else Decimal(px)), y + height * Decimal(py))
                   for px, py in SYMBOL_TEMPLATES[name]), dashed)
                 for name in symbol_names(opening, travel))
