"""Pure exact Best-Fit Decreasing over explicit stock and saw authorities."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from hashlib import sha256
from typing import Literal

from pydantic import Field

from dekopen_engine.models import EngineModel, EngineResult


class InvalidCutContract(ValueError):
    pass


class MissingStockAuthority(InvalidCutContract):
    pass


class AmbiguousStockAuthority(InvalidCutContract):
    pass


class MissingCuttingProfile(InvalidCutContract):
    pass


class AmbiguousCuttingProfile(InvalidCutContract):
    pass


class PieceLongerThanUsableStock(InvalidCutContract):
    pass


class CutMaterial(str, Enum):
    PVC = "PVC"
    ALUMINIUM = "ALUMINIUM"
    STEEL = "STEEL"


class CuttingProfile(EngineModel):
    id: str
    code: str
    kerf_mm: Decimal = Field(ge=Decimal("0"))
    head_trim_mm: Decimal = Field(ge=Decimal("0"))
    tail_trim_mm: Decimal = Field(ge=Decimal("0"))


class CutPiece(EngineModel):
    piece_id: str = Field(min_length=1, pattern=r"^\S(?:.*\S)?$")
    source_kind: Literal["PROFILE", "REINFORCEMENT"]
    workshop_sku: str
    material: CutMaterial
    color: str
    length_mm: Decimal = Field(gt=Decimal("0"))
    source_position_id: str | None = None
    bay_id: str | None = None
    leaf_id: str | None = None
    role: str
    unit_index: int = Field(ge=1)
    angle_left: Decimal | None = None
    angle_right: Decimal | None = None


class StockRule(EngineModel):
    stock_authority_id: str
    workshop_sku: str
    commercial_sku: str
    manufacturer_name: str
    supplier_name: str | None = None
    purchase_unit: Literal["BAR"]
    material: CutMaterial
    color: str
    stock_length_mm: Decimal = Field(gt=Decimal("0"))


class CutPlacement(CutPiece):
    sequence: int = Field(ge=1)


class CutBar(EngineModel):
    bar_index: int
    commercial_sku: str
    material: CutMaterial
    color: str
    stock_length_mm: Decimal
    head_trim_mm: Decimal
    tail_trim_mm: Decimal
    kerf_mm: Decimal
    cuts: list[CutPlacement]
    kerf_total_mm: Decimal
    productive_length_mm: Decimal
    process_consumed_mm: Decimal
    remainder_mm: Decimal
    waste_mm: Decimal
    yield_pct: Decimal
    waste_pct: Decimal


class PurchaseLine(EngineModel):
    commercial_sku: str
    manufacturer: str
    supplier: str | None
    stock_length_mm: Decimal
    material: CutMaterial
    color: str
    unit: Literal["BAR"]
    qty_bars: int


class CutOptimizationResult(EngineModel):
    purchase_list: list[PurchaseLine]
    workshop_cut_plan: list[CutBar]


def pieces_from_result(
    result: EngineResult, *, color: str, source_position_id: str | None = None,
    reinforcement_skus: dict[str, str],
) -> list[CutPiece]:
    """Project exact cuts; aggregate identical rows before stable quantity expansion."""
    rows: dict[str, tuple[CutPiece, int]] = {}
    for cut in result.profile_cuts:
        key = "PROFILE:" + cut.model_dump_json(exclude={"qty"})
        piece = CutPiece(
            piece_id=sha256(key.encode("utf-8")).hexdigest(), source_kind="PROFILE",
            workshop_sku=cut.sku, material=CutMaterial(cut.material.value), color=color,
            length_mm=cut.length_mm, source_position_id=source_position_id,
            bay_id=cut.bay_id, leaf_id=cut.leaf_id, role=cut.role.value, unit_index=1,
            angle_left=cut.angle_left, angle_right=cut.angle_right,
        )
        rows[key] = (piece, rows.get(key, (piece, 0))[1] + cut.qty)
    for steel in result.reinforcements:
        sku = steel.reinforcement_sku or reinforcement_skus.get(steel.parent_profile_sku)
        if sku is None:
            raise MissingStockAuthority("Reinforcement has no resolved stock SKU")
        key = "REINFORCEMENT:" + steel.model_dump_json(exclude={"qty"})
        piece = CutPiece(
            piece_id=sha256(key.encode("utf-8")).hexdigest(), source_kind="REINFORCEMENT",
            workshop_sku=sku, material=CutMaterial.STEEL, color=color,
            length_mm=steel.length_mm, source_position_id=source_position_id,
            bay_id=steel.bay_id, leaf_id=steel.leaf_id, role=steel.role.value, unit_index=1,
        )
        rows[key] = (piece, rows.get(key, (piece, 0))[1] + steel.qty)
    return [piece.model_copy(update={"unit_index": index})
            for key in sorted(rows) for piece, qty in [rows[key]]
            for index in range(1, qty + 1)]


def _piece_order(piece: CutPiece) -> tuple[Decimal, str, str, str, str, str, str, int]:
    return (-piece.length_mm, piece.workshop_sku, piece.source_position_id or "",
            piece.bay_id or "", piece.leaf_id or "", piece.role, piece.piece_id,
            piece.unit_index)


def optimize_cut(
    pieces: list[CutPiece], stock_rules: list[StockRule], cutting_profile: CuttingProfile,
) -> CutOptimizationResult:
    """No defaults, inferred stock compatibility, partial plans or inventory effects."""
    profile = cutting_profile
    groups: list[tuple[str, Decimal, CutMaterial, str, str]] = []
    authorities: list[StockRule] = []
    bar_pieces: list[list[CutPiece]] = []
    remainders: list[Decimal] = []
    seen: set[tuple[str | None, str, int]] = set()
    for piece in sorted(pieces, key=_piece_order):
        identity = (piece.source_position_id, piece.piece_id, piece.unit_index)
        if identity in seen:
            raise InvalidCutContract("Duplicate piece identity")
        seen.add(identity)
        matches = [r for r in stock_rules if r.workshop_sku == piece.workshop_sku
                   and r.material == piece.material and r.color == piece.color]
        if not matches:
            raise MissingStockAuthority("No effective stock rule")
        if len(matches) != 1:
            raise AmbiguousStockAuthority("Multiple effective stock rules")
        stock = matches[0]
        group = (stock.commercial_sku, stock.stock_length_mm, stock.material,
                 stock.color, profile.id)
        usable = stock.stock_length_mm - profile.head_trim_mm - profile.tail_trim_mm
        required = piece.length_mm + profile.kerf_mm
        if usable < Decimal("0"):
            raise InvalidCutContract("Trims exceed stock")
        if required > usable:
            raise PieceLongerThanUsableStock("Piece plus kerf exceeds usable stock")
        compatible: list[tuple[Decimal, int]] = []
        for index, existing in enumerate(groups):
            if existing != group:
                continue
            authority = authorities[index]
            if (authority.manufacturer_name, authority.supplier_name) != (
                stock.manufacturer_name, stock.supplier_name
            ):
                raise InvalidCutContract("Commercial stock identity has conflicting provenance")
            residual = remainders[index] - required
            if residual >= Decimal("0"):
                compatible.append((residual, index))
        if compatible:
            residual, index = min(compatible)
            bar_pieces[index].append(piece)
            remainders[index] = residual
        else:
            groups.append(group)
            authorities.append(stock)
            bar_pieces.append([piece])
            remainders.append(usable - required)
    bars: list[CutBar] = []
    purchases: dict[tuple[str, Decimal, CutMaterial, str, str], PurchaseLine] = {}
    for index, cuts in enumerate(bar_pieces):
        stock = authorities[index]
        productive = sum((p.length_mm for p in cuts), Decimal("0"))
        kerf = Decimal(len(cuts)) * profile.kerf_mm
        consumed = productive + kerf + profile.head_trim_mm + profile.tail_trim_mm
        yield_exact = productive / stock.stock_length_mm * Decimal("100")
        bars.append(CutBar(
            bar_index=index + 1, commercial_sku=stock.commercial_sku,
            material=stock.material, color=stock.color, stock_length_mm=stock.stock_length_mm,
            head_trim_mm=profile.head_trim_mm, tail_trim_mm=profile.tail_trim_mm,
            kerf_mm=profile.kerf_mm,
            cuts=[CutPlacement(**p.model_dump(), sequence=i + 1) for i, p in enumerate(cuts)],
            kerf_total_mm=kerf, productive_length_mm=productive, process_consumed_mm=consumed,
            remainder_mm=stock.stock_length_mm - consumed,
            waste_mm=stock.stock_length_mm - productive,
            yield_pct=yield_exact.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            waste_pct=(Decimal("100") - yield_exact).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP),
        ))
        group = groups[index]
        previous = purchases.get(group)
        purchases[group] = PurchaseLine(
            commercial_sku=stock.commercial_sku, manufacturer=stock.manufacturer_name,
            supplier=stock.supplier_name, stock_length_mm=stock.stock_length_mm,
            material=stock.material, color=stock.color, unit=stock.purchase_unit,
            qty_bars=1 if previous is None else previous.qty_bars + 1,
        )
    return CutOptimizationResult(
        purchase_list=[purchases[key] for key in sorted(purchases)], workshop_cut_plan=bars,
    )
