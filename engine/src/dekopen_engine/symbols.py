"""Pure DIN elevation primitives. Dimensions are drawing coordinates in mm.

SYMBOL_TEMPLATES is the grammar source; scripts/generate_opening_symbols.py
exports it for React. No manufacturing capacity is implied by a glyph.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

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
    "lift_right": (("0.25", "0.6"), ("0.4", "0.6"), ("0.4", "0.5"), ("0.75", "0.5")),
    "lift_left": (("0.75", "0.6"), ("0.6", "0.6"), ("0.6", "0.5"), ("0.25", "0.5")),
    "fold_left": (("0.2", "0.2"), ("0.8", "0.5"), ("0.2", "0.8")),
    "fold_right": (("0.8", "0.2"), ("0.2", "0.5"), ("0.8", "0.8")),
    "pivot_v": (("0.5", "0.2"), ("0.5", "0.8")),
    "pivot_h": (("0.2", "0.5"), ("0.8", "0.5")),
    "vertical_slide": (("0.5", "0.75"), ("0.5", "0.25")),
    "vertical_slide_head": (("0.44", "0.35"), ("0.5", "0.25"), ("0.56", "0.35")),
    "vertical_down": (("0.5", "0.25"), ("0.5", "0.75")),
    "vertical_down_head": (("0.44", "0.65"), ("0.5", "0.75"), ("0.56", "0.65")),
}


@dataclass(frozen=True)
class SymbolLine:
    symbol: str
    points: tuple[tuple[Decimal, Decimal], ...]
    dashed: bool


SymbolTravel = SlidingTravel | Literal["LEFT", "RIGHT", "UP", "DOWN"]


def symbol_names(opening: Opening, travel: SymbolTravel | None = None) -> tuple[str, ...]:
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
        direction = travel.value if isinstance(travel, SlidingTravel) else travel
        if direction in ("LEFT", "RIGHT"):
            stem = "slide_" + direction.lower()
            names += (stem, stem + "_head")
            if movement is OpeningMovement.LIFT_SLIDE:
                names = ("lift_" + direction.lower(), stem + "_head")
        if movement is OpeningMovement.PARALLEL_SLIDE:
            names += ("tilt",)
    if movement is OpeningMovement.FOLD:
        names += ("fold_left",)
    if movement in (OpeningMovement.PIVOT_V, OpeningMovement.PIVOT_H):
        names += (movement.value.lower(),)
    if movement is OpeningMovement.VERTICAL_SLIDE:
        names += ("vertical_down", "vertical_down_head") if travel == "DOWN" else ("vertical_slide", "vertical_slide_head")
    return names


def opening_symbol_lines(opening: Opening, *, x: Decimal, y: Decimal,
                         width: Decimal, height: Decimal, exterior: bool = False,
                         mirror: bool = True, travel: SymbolTravel | None = None,
                         axis_x: Decimal | None = None, axis_y: Decimal | None = None,
                         closing_side: str | None = None) -> tuple[SymbolLine, ...]:
    """Affine drawing projection; direction and viewpoint never change intent."""
    if width <= 0 or height <= 0:
        raise ValueError("El símbolo necesita un rectángulo válido.")
    sliding = opening.movement in (OpeningMovement.SLIDE, OpeningMovement.LIFT_SLIDE,
                                  OpeningMovement.PARALLEL_SLIDE, OpeningMovement.VERTICAL_SLIDE)
    dashed = not sliding and ((opening.direction is OpeningDirection.OUTWARD) != exterior)
    names = symbol_names(opening, travel)
    if opening.movement is OpeningMovement.FOLD and closing_side == "LEFT":
        names = ("fold_right",)
    def point(name: str, px: str, py: str) -> tuple[Decimal, Decimal]:
        local_x = (axis_x-x)/width if name == "pivot_v" and axis_x is not None else Decimal(px)
        local_y = (axis_y-y)/height if name == "pivot_h" and axis_y is not None else Decimal(py)
        return (x+width*(1-local_x if exterior and mirror else local_x), y+height*local_y)
    return tuple(SymbolLine(name, tuple(point(name, px, py)
                   for px, py in SYMBOL_TEMPLATES[name]), dashed)
                 for name in names)
