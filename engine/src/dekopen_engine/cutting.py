"""Pure exact Best-Fit Decreasing over explicit stock and saw authorities."""

from __future__ import annotations

import json
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
    # Bar remainder at or above this length goes back to stock as a usable
    # remnant; below it the remainder is process waste. `0` keeps the
    # historical every-remainder-counted-the-same accounting.
    min_keep_remnant_mm: Decimal = Field(ge=Decimal("0"), default=Decimal("0"))
    # Saw capability: absolute end-angle limit per cut. Pieces exceeding it
    # land in ``unplaced`` with a reason instead of silently packing.
    max_angle_deg: Decimal | None = Field(default=None, gt=Decimal("0"))


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
    # Set on pieces cut from a curved member: the shop bends to this sagitta
    # instead of cutting straight.
    sagitta_mm: Decimal | None = None


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
    # Additional purchasable lengths of the same commercial stock (e.g. the
    # supplier sells 6000 and 6500 mm bars under one contract). When empty the
    # rule offers exactly ``stock_length_mm``.
    alternative_lengths_mm: list[Decimal] = Field(default_factory=list)


class CutPlacement(CutPiece):
    sequence: int = Field(ge=1)


class RemnantBar(EngineModel):
    """One on-hand bar offcut available to the plan — a single bin of exact
    length carrying zero procurement cost. ``stock_authority_id`` scopes it to
    the identity that produced it; ``remnant_id`` is the ledger handle for
    reservation."""

    remnant_id: str = Field(min_length=1)
    stock_authority_id: str = Field(min_length=1)
    length_mm: Decimal = Field(gt=Decimal("0"))


class CutBar(EngineModel):
    bar_index: int
    commercial_sku: str
    material: CutMaterial
    color: str
    stock_length_mm: Decimal
    # The stock authority this bar was bought under — lets the workshop link
    # the plan back to the physical stock identity (remnant ledger, purchase
    # mapping) without re-resolving the commercial sku.
    stock_authority_id: str | None = None
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
    # REMNANT bars consume on-hand stock and never appear on the purchase list.
    source: Literal["NEW", "REMNANT"] = "NEW"
    remnant_id: str | None = None
    # remainder_mm >= profile.min_keep_remnant_mm — this drop returns to stock.
    remainder_reusable: bool = False


class UnplacedCut(EngineModel):
    """A feasible piece the chosen plan could not place, or a piece that
    violates a declared machine limit — reported honestly, never dropped."""

    piece: CutPiece
    reason: str


class CutPlanMetrics(EngineModel):
    """Lexicographic cost view of a plan: feasibility first, then what the
    workshop must buy, then real process waste (kerf + trims + sub-keep
    remainders — reusable remnants are NOT waste), then cut count."""

    bars: int
    purchased_bars: int
    remnant_bars: int
    cuts: int
    productive_length_mm: Decimal
    process_waste_mm: Decimal
    reusable_remnant_mm: Decimal
    unplaced: int


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
    unplaced: list[UnplacedCut] = Field(default_factory=list)
    metrics: CutPlanMetrics | None = None
    # Set when strategy="auto": per-strategy metrics + which won and why.
    strategy_comparison: dict[str, object] | None = None
    # sha256 over the canonical input bundle (pieces, stock, profile,
    # strategy): identical inputs -> identical seed -> identical plan.
    plan_seed: str | None = None


def pieces_from_result(
    result: EngineResult, *, color: str, source_position_id: str | None = None,
    reinforcement_skus: dict[str, str],
    reinforcement_angles: dict[
        tuple[str, str, str, str | None, str | None], tuple[str, str] | None
    ] | None = None,
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
            sagitta_mm=cut.sagitta_mm,
        )
        rows[key] = (piece, rows.get(key, (piece, 0))[1] + cut.qty)
    for steel in result.reinforcements:
        sku = steel.reinforcement_sku or reinforcement_skus.get(steel.parent_profile_sku)
        if sku is None:
            raise MissingStockAuthority("Reinforcement has no resolved stock SKU")
        angles: tuple[str, str] | None = None
        if reinforcement_angles is not None:
            angles = reinforcement_angles.get(
                (sku, str(steel.length_mm), steel.role.value, steel.bay_id, steel.leaf_id)
            )
            if angles is None:  # absent or marked ambiguous by conflicting facts
                raise MissingStockAuthority(
                    "Reinforcement cut angles are missing or ambiguous in the "
                    "sealed manufacturing facts"
                )
        key = "REINFORCEMENT:" + steel.model_dump_json(exclude={"qty"})
        piece = CutPiece(
            piece_id=sha256(key.encode("utf-8")).hexdigest(), source_kind="REINFORCEMENT",
            workshop_sku=sku, material=CutMaterial.STEEL, color=color,
            length_mm=steel.length_mm, source_position_id=source_position_id,
            bay_id=steel.bay_id, leaf_id=steel.leaf_id, role=steel.role.value, unit_index=1,
            angle_left=Decimal(angles[0]) if angles else None,
            angle_right=Decimal(angles[1]) if angles else None,
            sagitta_mm=steel.sagitta_mm,
        )
        rows[key] = (piece, rows.get(key, (piece, 0))[1] + steel.qty)
    return [piece.model_copy(update={"unit_index": index})
            for key in sorted(rows) for piece, qty in [rows[key]]
            for index in range(1, qty + 1)]


def _piece_order(piece: CutPiece) -> tuple[Decimal, str, str, str, str, str, str, int]:
    return (-piece.length_mm, piece.workshop_sku, piece.source_position_id or "",
            piece.bay_id or "", piece.leaf_id or "", piece.role, piece.piece_id,
            piece.unit_index)


def _variants_of(stock: StockRule) -> list[Decimal]:
    """All purchasable lengths of one stock identity, ascending, deduplicated."""
    lengths = {stock.stock_length_mm, *stock.alternative_lengths_mm}
    return sorted(lengths)


def _usable(length: Decimal, profile: CuttingProfile) -> Decimal:
    return length - profile.head_trim_mm - profile.tail_trim_mm


def _piece_fits(piece: CutPiece, usable: Decimal, kerf: Decimal) -> bool:
    return piece.length_mm + kerf <= usable


def _angle_ok(piece: CutPiece, profile: CuttingProfile) -> bool:
    if profile.max_angle_deg is None:
        return True
    for angle in (piece.angle_left, piece.angle_right):
        if angle is not None and abs(angle) > profile.max_angle_deg:
            return False
    return True


def _pack_remnant(
    pieces: list[CutPiece], remnant: RemnantBar, usable: Decimal, kerf: Decimal,
) -> tuple[list[CutPiece], list[CutPiece]]:
    """Greedy fill of one remnant with the largest pieces that still fit.
    Returns (placed, remaining). Deterministic: pieces arrive in _piece_order."""
    placed: list[CutPiece] = []
    remaining: list[CutPiece] = []
    residual = usable
    for piece in pieces:
        required = piece.length_mm + kerf
        if required <= residual:
            placed.append(piece)
            residual -= required
        else:
            remaining.append(piece)
    return placed, remaining


def _bfd_fill(
    pieces: list[CutPiece], stock_length: Decimal, profile: CuttingProfile,
) -> tuple[list[list[CutPiece]], list[CutPiece]]:
    """Best-fit decreasing over open bins of one stock length.
    Returns (bins, unplaced) — unplaced can only occur when a piece exceeds
    this length's usable span (the caller filters those earlier)."""
    usable = _usable(stock_length, profile)
    required_of = [piece.length_mm + profile.kerf_mm for piece in pieces]
    bins: list[list[CutPiece]] = []
    remainders: list[Decimal] = []
    for piece, required in zip(pieces, required_of):
        if required > usable:
            return bins, pieces  # unreachable: caller pre-checks
        best: tuple[Decimal, int] | None = None
        for index, residual in enumerate(remainders):
            leftover = residual - required
            if leftover >= Decimal("0") and (best is None or leftover < best[0]):
                best = (leftover, index)
        if best is None:
            bins.append([piece])
            remainders.append(usable - required)
        else:
            bins[best[1]].append(piece)
            remainders[best[1]] = best[0]
    return bins, []


# Patterns are count vectors over the distinct lengths, enumerated
# lexicographically descending on the longest piece first so reconstruction is
# fully determined. State-space cap keeps the deep tier bounded.
_DEEP_STATE_CAP = 200_000


def _enumerate_patterns(
    lengths: list[Decimal], usable: Decimal, kerf: Decimal,
) -> list[tuple[int, ...]]:
    """All non-empty count vectors fitting one bar. Deterministic order."""
    patterns: list[tuple[int, ...]] = []

    def walk(index: int, used: Decimal, counts: list[int]) -> None:
        if index == len(lengths):
            if any(counts):
                patterns.append(tuple(counts))
            return
        unit = lengths[index] + kerf
        max_count = int((usable - used) / unit) if unit > Decimal("0") else 0
        for count in range(max_count, -1, -1):
            counts.append(count)
            walk(index + 1, used + unit * count, counts)
            counts.pop()

    walk(0, Decimal("0"), [])
    return patterns


def _deep_bins(
    pieces: list[CutPiece], stock_length: Decimal, profile: CuttingProfile,
) -> list[list[CutPiece]] | None:
    """Minimum-bar pattern packing via DP over the demand multiset.
    Returns None when the state space exceeds the cap (caller falls back)."""
    usable = _usable(stock_length, profile)
    kerf = profile.kerf_mm
    lengths = sorted({p.length_mm for p in pieces}, reverse=True)
    demand = tuple(
        sum(1 for p in pieces if p.length_mm == length) for length in lengths
    )
    states = 1
    for count in demand:
        states *= count + 1
        if states > _DEEP_STATE_CAP:
            return None
    patterns = _enumerate_patterns(lengths, usable, kerf)

    from functools import lru_cache

    @lru_cache(maxsize=None)
    def solve(state: tuple[int, ...]) -> tuple[int, tuple[int, ...]] | None:
        if not any(state):
            return (0, ())
        best: tuple[int, tuple[int, ...]] | None = None
        for pattern_index, pattern in enumerate(patterns):
            if any(pattern[i] > state[i] for i in range(len(state))):
                continue
            sub = solve(tuple(state[i] - pattern[i] for i in range(len(state))))
            if sub is None:
                continue
            candidate = (sub[0] + 1, (pattern_index,) + sub[1])
            if best is None or candidate[0] < best[0] or (
                candidate[0] == best[0] and candidate[1] < best[1]
            ):
                best = candidate
        return best

    solved = solve(demand)
    if solved is None:
        return None
    pools: dict[Decimal, list[CutPiece]] = {}
    for piece in pieces:
        pools.setdefault(piece.length_mm, []).append(piece)
    bins: list[list[CutPiece]] = []
    for pattern_index in solved[1]:
        pattern = patterns[pattern_index]
        bar: list[CutPiece] = []
        for i, length in enumerate(lengths):
            for _ in range(pattern[i]):
                bar.append(pools[length].pop())
        bins.append(bar)
    return bins


def _metrics_of(
    bars: list[CutBar], unplaced: list[UnplacedCut], profile: CuttingProfile,
) -> CutPlanMetrics:
    productive = sum((b.productive_length_mm for b in bars), Decimal("0"))
    kerf_total = sum((b.kerf_total_mm for b in bars), Decimal("0"))
    trims = sum(
        (b.head_trim_mm + b.tail_trim_mm for b in bars), Decimal("0")
    )
    reusable = sum(
        (b.remainder_mm for b in bars if b.remainder_reusable), Decimal("0")
    )
    scrapped = sum(
        (b.remainder_mm for b in bars if not b.remainder_reusable), Decimal("0")
    )
    return CutPlanMetrics(
        bars=len(bars),
        purchased_bars=sum(1 for b in bars if b.source == "NEW"),
        remnant_bars=sum(1 for b in bars if b.source == "REMNANT"),
        cuts=sum(len(b.cuts) for b in bars),
        productive_length_mm=productive,
        process_waste_mm=kerf_total + trims + scrapped,
        reusable_remnant_mm=reusable,
        unplaced=len(unplaced),
    )


def _cost_key(metrics: CutPlanMetrics) -> tuple[int, int, Decimal, int]:
    """Lexicographic objective: feasibility -> procurement -> process waste
    -> cuts. Reusable remnants are value, not waste, so they never enter
    the waste term."""
    return (
        metrics.unplaced,
        metrics.purchased_bars,
        metrics.process_waste_mm,
        metrics.cuts,
    )


def _emit_bars(
    bins: list[list[CutPiece]],
    sources: list[tuple[StockRule, Decimal, str, str | None]],
    group_stock: StockRule,
    profile: CuttingProfile,
) -> tuple[list[CutBar], dict[tuple[str, Decimal, CutMaterial, str, str], PurchaseLine]]:
    bars: list[CutBar] = []
    purchases: dict[
        tuple[str, Decimal, CutMaterial, str, str], PurchaseLine
    ] = {}
    for index, (cuts, (stock, length, source, remnant_id)) in enumerate(
        zip(bins, sources)
    ):
        productive = sum((p.length_mm for p in cuts), Decimal("0"))
        kerf = Decimal(len(cuts)) * profile.kerf_mm
        consumed = productive + kerf + profile.head_trim_mm + profile.tail_trim_mm
        remainder = length - consumed
        yield_exact = productive / length * Decimal("100")
        reusable = remainder >= profile.min_keep_remnant_mm and remainder > Decimal("0")
        bars.append(CutBar(
            bar_index=index + 1, commercial_sku=stock.commercial_sku,
            material=stock.material, color=stock.color, stock_length_mm=length,
            stock_authority_id=stock.stock_authority_id,
            head_trim_mm=profile.head_trim_mm, tail_trim_mm=profile.tail_trim_mm,
            kerf_mm=profile.kerf_mm,
            cuts=[CutPlacement(**p.model_dump(), sequence=i + 1) for i, p in enumerate(cuts)],
            kerf_total_mm=kerf, productive_length_mm=productive,
            process_consumed_mm=consumed,
            remainder_mm=remainder,
            waste_mm=length - productive,
            yield_pct=yield_exact.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
            waste_pct=(Decimal("100") - yield_exact).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP),
            source=source, remnant_id=remnant_id,
            remainder_reusable=reusable,
        ))
        if source == "NEW":
            key = (stock.commercial_sku, length, stock.material, stock.color,
                   profile.id)
            previous = purchases.get(key)
            purchases[key] = PurchaseLine(
                commercial_sku=stock.commercial_sku,
                manufacturer=stock.manufacturer_name,
                supplier=stock.supplier_name, stock_length_mm=length,
                material=stock.material, color=stock.color,
                unit=stock.purchase_unit,
                qty_bars=1 if previous is None else previous.qty_bars + 1,
            )
    return bars, purchases


def _pack_group(
    pieces: list[CutPiece],
    stock: StockRule,
    remnants: list[RemnantBar],
    profile: CuttingProfile,
    strategy: Literal["fast", "deep"],
) -> tuple[list[CutBar], dict[tuple[str, Decimal, CutMaterial, str, str], PurchaseLine]]:
    """One stock identity: remnants first (smallest fitting — zero
    procurement always beats buying), then new bars on the variant that
    minimizes the cost tuple."""
    bins: list[list[CutPiece]] = []
    sources: list[tuple[StockRule, Decimal, str, str | None]] = []
    remaining = pieces
    for remnant in sorted(remnants, key=lambda r: (r.length_mm, r.remnant_id)):
        usable = _usable(remnant.length_mm, profile)
        if usable < Decimal("0"):
            continue  # shorter than the mandatory trims — already scrap
        placed, remaining = _pack_remnant(remaining, remnant, usable, profile.kerf_mm)
        if not placed:
            continue
        bins.append(placed)
        sources.append((stock, remnant.length_mm, "REMNANT", remnant.remnant_id))
    if remaining:
        best_bins: list[list[CutPiece]] | None = None
        best_length: Decimal | None = None
        for length in _variants_of(stock):
            usable = _usable(length, profile)
            if usable < Decimal("0"):
                raise InvalidCutContract("Trims exceed stock")
            if strategy == "deep":
                candidate = _deep_bins(remaining, length, profile)
                if candidate is None:
                    candidate, _ = _bfd_fill(remaining, length, profile)
            else:
                candidate, _ = _bfd_fill(remaining, length, profile)
            key = (len(candidate), Decimal(len(candidate)) * length)
            if best_bins is None or key < (
                len(best_bins), Decimal(len(best_bins)) * (best_length or length)
            ):
                best_bins, best_length = candidate, length
        assert best_bins is not None and best_length is not None
        for bar in best_bins:
            bins.append(bar)
            sources.append((stock, best_length, "NEW", None))
    return _emit_bars(bins, sources, stock, profile)


def optimize_cut(
    pieces: list[CutPiece], stock_rules: list[StockRule], cutting_profile: CuttingProfile,
    *,
    remnants: list[RemnantBar] | None = None,
    strategy: Literal["fast", "deep", "auto"] = "fast",
) -> CutOptimizationResult:
    """No defaults, inferred stock compatibility, partial plans or inventory effects.

    ``strategy``: ``fast`` is deterministic best-fit; ``deep`` runs a
    minimum-bar pattern DP per stock variant; ``auto`` runs both and keeps
    the lexicographically better plan, reporting ``strategy_comparison``.
    ``remnants``: on-hand bar offcuts matched per stock identity and consumed
    before any new bar is opened.
    """
    profile = cutting_profile
    # Group pieces by commercial stock identity (commercial_sku + material +
    # color + saw): different workshop SKUs share a bar iff they map to the
    # same commercial stock. The authority check is unchanged: exactly one
    # effective rule per (workshop_sku, material, color).
    grouped: dict[tuple[str, str, str], list[CutPiece]] = {}
    rules: dict[tuple[str, str, str], StockRule] = {}
    authority_ids: dict[tuple[str, str, str], set[str]] = {}
    unplaced: list[UnplacedCut] = []
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
        provenance = (stock.manufacturer_name, stock.supplier_name)
        for existing in rules.values():
            if (
                existing.commercial_sku == stock.commercial_sku
                and existing.material == stock.material
                and existing.color == stock.color
                and (existing.manufacturer_name, existing.supplier_name)
                != provenance
            ):
                raise InvalidCutContract(
                    "Commercial stock identity has conflicting provenance"
                )
        if not _angle_ok(piece, profile):
            unplaced.append(UnplacedCut(piece=piece, reason="angle_exceeds_saw"))
            continue
        key = (stock.commercial_sku, stock.material.value, stock.color)
        grouped.setdefault(key, []).append(piece)
        rules.setdefault(key, stock)
        authority_ids.setdefault(key, set()).add(stock.stock_authority_id)

    group_remnants: dict[tuple[str, str, str], list[RemnantBar]] = {
        key: [
            r for r in (remnants or [])
            if r.stock_authority_id in authority_ids[key]
        ]
        for key in rules
    }

    def run(solve_as: Literal["fast", "deep"]) -> tuple[
        list[CutBar], list[PurchaseLine]
    ]:
        bars: list[CutBar] = []
        purchases: dict[
            tuple[str, Decimal, CutMaterial, str, str], PurchaseLine
        ] = {}
        for key in sorted(grouped):
            stock = rules[key]
            group_pieces = grouped[key]
            for length in _variants_of(stock):
                if _usable(length, profile) < Decimal("0"):
                    raise InvalidCutContract("Trims exceed stock")
            # Feasibility: a piece that no variant and no remnant can host is
            # an input error — raise, as before.
            group_remnant_lengths = [
                _usable(r.length_mm, profile) for r in group_remnants[key]
            ]
            for piece in group_pieces:
                required = piece.length_mm + profile.kerf_mm
                can_host = any(
                    required <= u for u in
                    [_usable(v, profile) for v in _variants_of(stock)]
                ) or any(required <= u for u in group_remnant_lengths)
                if not can_host:
                    raise PieceLongerThanUsableStock(
                        "Piece plus kerf exceeds usable stock"
                    )
            group_bars, group_purchases = _pack_group(
                group_pieces, stock, group_remnants[key], profile, solve_as
            )
            for purchase in group_purchases.values():
                merge_key = (
                    purchase.commercial_sku, purchase.stock_length_mm,
                    purchase.material, purchase.color, profile.id,
                )
                previous = purchases.get(merge_key)
                purchases[merge_key] = PurchaseLine(
                    commercial_sku=purchase.commercial_sku,
                    manufacturer=purchase.manufacturer,
                    supplier=purchase.supplier,
                    stock_length_mm=purchase.stock_length_mm,
                    material=purchase.material, color=purchase.color,
                    unit=purchase.unit,
                    qty_bars=purchase.qty_bars
                    + (previous.qty_bars if previous else 0),
                )
            bars.extend(group_bars)
        # Re-index bars deterministically across groups.
        for index, bar in enumerate(bars):
            bars[index] = bar.model_copy(update={"bar_index": index + 1})
        return bars, list(purchases[k] for k in sorted(purchases))

    if strategy == "auto":
        fast_bars, fast_purchases = run("fast")
        fast_metrics = _metrics_of(fast_bars, unplaced, profile)
        deep_bars, deep_purchases = run("deep")
        deep_metrics = _metrics_of(deep_bars, unplaced, profile)
        if _cost_key(deep_metrics) < _cost_key(fast_metrics):
            bars, purchase_lines, chosen = deep_bars, deep_purchases, "deep"
        else:
            bars, purchase_lines, chosen = fast_bars, fast_purchases, "fast"
        comparison: dict[str, object] | None = {
            "fast": fast_metrics.model_dump(mode="json"),
            "deep": deep_metrics.model_dump(mode="json"),
            "chosen": chosen,
        }
        metrics = deep_metrics if chosen == "deep" else fast_metrics
    else:
        bars, purchase_lines = run(strategy)
        metrics = _metrics_of(bars, unplaced, profile)
        comparison = None

    seed_payload = {
        "pieces": [
            [p.piece_id, str(p.length_mm), p.unit_index]
            for p in sorted(pieces, key=_piece_order)
        ],
        "profile": profile.model_dump(mode="json"),
        "stocks": [
            s.model_dump(mode="json")
            for s in sorted(rules.values(), key=lambda s: s.stock_authority_id)
        ],
        "remnants": [
            [r.remnant_id, str(r.length_mm)]
            for r in sorted(remnants or [], key=lambda r: r.remnant_id)
        ],
        "strategy": strategy,
        "v": 2,
    }
    plan_seed = sha256(
        json.dumps(seed_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()

    return CutOptimizationResult(
        purchase_list=purchase_lines,
        workshop_cut_plan=bars,
        unplaced=unplaced,
        metrics=metrics,
        strategy_comparison=comparison,
        plan_seed=plan_seed,
    )
