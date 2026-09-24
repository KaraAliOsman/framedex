"""Mandate §13 optimization benchmark — the pre-§4 algorithms (pinned, verbatim
semantics) vs the industrial tiers on an adversarial corpus.

Legacy bar packer = ``optimize_cut`` at commit 09f0957: sorted best-fit into a
single stock length — no alternative lengths, no remnant pool, no deep tier,
no unplaced reporting (oversize raised), no kerf accounting differences.
Legacy sheet nester = ``nest_rects`` at commit b96be61: best-fit guillotine
with right+bottom split only — no alternate split, no free-rect pruning, no
kerf, no remnant sheets.

Every case is deterministic; the report is a markdown table for PR evidence.
Run: ``PYTHONPATH=engine/src python engine/scripts/benchmark_optimization.py``
"""

from __future__ import annotations

import random
from decimal import Decimal as D

from dekopen_engine.cutting import (
    CutBar,
    CutMaterial,
    CutPiece,
    CutPlacement,
    CuttingProfile,
    PieceLongerThanUsableStock,
    RemnantBar,
    StockRule,
    optimize_cut,
)
from dekopen_engine.nesting import (
    NestPiece,
    SheetRule,
    SheetRemnant,
    nest_rects,
)

# ── Frozen legacy algorithms ────────────────────────────────────────────


def _legacy_piece_order(piece: CutPiece) -> tuple[object, ...]:
    return (
        -piece.length_mm,
        piece.workshop_sku,
        piece.source_position_id or "",
        piece.bay_id or "",
        piece.leaf_id or "",
        piece.role,
        piece.piece_id,
        piece.unit_index,
    )


def legacy_cut_plan(
    pieces: list[CutPiece],
    stock_rules: list[StockRule],
    profile: CuttingProfile,
) -> list[CutBar]:
    """optimize_cut @09f0957 verbatim — BFD into one stock length, nothing else."""
    groups: list[tuple[object, ...]] = []
    authorities: list[StockRule] = []
    bar_pieces: list[list[CutPiece]] = []
    remainders: list[D] = []
    for piece in sorted(pieces, key=_legacy_piece_order):
        matches = [
            r
            for r in stock_rules
            if r.workshop_sku == piece.workshop_sku
            and r.material == piece.material
            and r.color == piece.color
        ]
        stock = matches[0]
        group = (
            stock.commercial_sku,
            stock.stock_length_mm,
            stock.material,
            stock.color,
            profile.id,
        )
        usable = stock.stock_length_mm - profile.head_trim_mm - profile.tail_trim_mm
        required = piece.length_mm + profile.kerf_mm
        if required > usable:
            raise PieceLongerThanUsableStock("Piece plus kerf exceeds usable stock")
        compatible: list[tuple[D, int]] = []
        for index, existing in enumerate(groups):
            if existing != group:
                continue
            residual = remainders[index] - required
            if residual >= D("0"):
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
    for index, cuts in enumerate(bar_pieces):
        stock = authorities[index]
        productive = sum((p.length_mm for p in cuts), D("0"))
        kerf = D(len(cuts)) * profile.kerf_mm
        consumed = productive + kerf + profile.head_trim_mm + profile.tail_trim_mm
        yield_exact = productive / stock.stock_length_mm * D("100")
        bars.append(
            CutBar(
                bar_index=index + 1,
                commercial_sku=stock.commercial_sku,
                material=stock.material,
                color=stock.color,
                stock_length_mm=stock.stock_length_mm,
                head_trim_mm=profile.head_trim_mm,
                tail_trim_mm=profile.tail_trim_mm,
                kerf_mm=profile.kerf_mm,
                cuts=[
                    CutPlacement(**p.model_dump(), sequence=i + 1)
                    for i, p in enumerate(cuts)
                ],
                kerf_total_mm=kerf,
                productive_length_mm=productive,
                process_consumed_mm=consumed,
                remainder_mm=stock.stock_length_mm - consumed,
                waste_mm=stock.stock_length_mm - productive,
                yield_pct=yield_exact.quantize(D("0.0001")),
                waste_pct=(D("100") - yield_exact).quantize(D("0.0001")),
            )
        )
    return bars


class _Rect:
    __slots__ = ("x", "y", "w", "h")

    def __init__(self, x: D, y: D, w: D, h: D) -> None:
        self.x, self.y, self.w, self.h = x, y, w, h


class _Bin:
    __slots__ = ("free", "placed")

    def __init__(self, free: list[_Rect]) -> None:
        self.free = free
        self.placed: list[tuple[NestPiece, D, D, D, D, bool]] = []


def legacy_nest(pieces: list[NestPiece], rule: SheetRule) -> tuple[int, D, int]:
    """nest_rects @b96be61 verbatim — best-fit guillotine, right+bottom split,
    no kerf, no alternate split, no pruning, no remnants.
    Returns (sheets_used, productive_area, unplaced_count)."""
    usable_w = rule.sheet_width_mm - rule.edge_trim_mm * 2
    usable_h = rule.sheet_height_mm - rule.edge_trim_mm * 2

    def fits(w: D, h: D, rect: _Rect) -> bool:
        return w <= rect.w and h <= rect.h

    bins: list[_Bin] = []
    unplaced: list[NestPiece] = []
    for piece in sorted(
        pieces,
        key=lambda p: (
            -max(p.width_mm, p.height_mm),
            -(p.width_mm * p.height_mm),
            p.piece_id,
            p.unit_index,
        ),
    ):
        oriented = [(False, piece.width_mm, piece.height_mm)]
        if piece.allow_rotation:
            oriented.append((True, piece.height_mm, piece.width_mm))
        if not any(fits(w, h, _Rect(D("0"), D("0"), usable_w, usable_h)) for _, w, h in oriented):
            unplaced.append(piece)
            continue
        best = None
        for sheet_i, sheet_bin in enumerate(bins):
            for rect_i, rect in enumerate(sheet_bin.free):
                for rotated, w, h in oriented:
                    if not fits(w, h, rect):
                        continue
                    leftover = rect.w * rect.h - w * h
                    if best is None or leftover < best[0]:
                        best = (leftover, sheet_i, rect_i, rotated)
        if best is None:
            bins.append(_Bin([_Rect(D("0"), D("0"), usable_w, usable_h)]))
            sheet_bin = bins[-1]
            rect = sheet_bin.free[0]
            rotated = False
            w, h = piece.width_mm, piece.height_mm
            if not fits(w, h, rect) and piece.allow_rotation:
                w, h, rotated = h, w, True
            if not fits(w, h, rect):
                unplaced.append(piece)
                continue
            best = (D("0"), len(bins) - 1, 0, rotated)
        _, sheet_i, rect_i, rotated = best
        sheet_bin = bins[sheet_i]
        rect = sheet_bin.free.pop(rect_i)
        w = piece.height_mm if rotated else piece.width_mm
        h = piece.width_mm if rotated else piece.height_mm
        x, y = rect.x, rect.y
        for candidate in (
            _Rect(x + w, y, rect.w - w, rect.h),
            _Rect(x, y + h, w, rect.h - h),
        ):
            if candidate.w > D("0") and candidate.h > D("0"):
                sheet_bin.free.append(candidate)
        sheet_bin.free.sort(key=lambda r: (r.y, r.x, -r.w * r.h))
        sheet_bin.placed.append((piece, x, y, w, h, rotated))
    productive = sum(
        (placed[3] * placed[4] for sheet_bin in bins for placed in sheet_bin.placed),
        D("0"),
    )
    return sum(1 for b in bins if b.placed), productive, len(unplaced)


# ── Corpus ───────────────────────────────────────────────────────────────

SAW = CuttingProfile(
    id="saw-std",
    code="SAW",
    kerf_mm=D("4"),
    head_trim_mm=D("15"),
    tail_trim_mm=D("15"),
)


def _saw(**overrides: object) -> CuttingProfile:
    base: dict[str, object] = {
        "id": "saw-std",
        "code": "SAW",
        "kerf_mm": D("4"),
        "head_trim_mm": D("15"),
        "tail_trim_mm": D("15"),
    }
    base.update(overrides)
    return CuttingProfile.model_validate(base)


def _rule(sku: str, length: str = "6000", material: str = "PVC", color: str = "WHITE",
          alts: list[D] | None = None) -> StockRule:
    return StockRule(
        stock_authority_id=f"auth-{sku}-{material}-{color}",
        workshop_sku=sku,
        commercial_sku=f"COM-{sku}-{color}",
        manufacturer_name="MFG",
        supplier_name="SUP",
        purchase_unit="BAR",
        material=CutMaterial(material),
        color=color,
        stock_length_mm=D(length),
        alternative_lengths_mm=alts or [],
    )


def _piece(length: str, index: int, sku: str = "FRAME", material: str = "PVC",
           color: str = "WHITE", angles: tuple[str, str] | None = None,
           prefix: str = "p") -> CutPiece:
    data: dict[str, object] = {
        "piece_id": f"{prefix}{index}",
        "source_kind": "PROFILE",
        "workshop_sku": sku,
        "material": CutMaterial(material),
        "color": color,
        "length_mm": D(length),
        "role": "FRAME",
        "unit_index": 1,
    }
    if angles:
        data["angle_left"], data["angle_right"] = D(angles[0]), D(angles[1])
    return CutPiece.model_validate(data)


def _pieces(lengths: list[str], prefix: str = "p", *, sku: str = "FRAME",
            material: str = "PVC", color: str = "WHITE") -> list[CutPiece]:
    return [
        _piece(length, i, sku=sku, material=material, color=color,
               prefix=prefix)
        for i, length in enumerate(lengths)
    ]


def _remnant(rid: str, length: str, authority: str) -> RemnantBar:
    return RemnantBar(remnant_id=rid, stock_authority_id=authority, length_mm=D(length))


class _Case:
    def __init__(self, name: str, pieces: list[CutPiece], rules: list[StockRule],
                 profile: CuttingProfile | None = None,
                 remnants: list[RemnantBar] | None = None) -> None:
        self.name = name
        self.pieces = pieces
        self.rules = rules
        self.profile = profile or SAW
        self.remnants = remnants or []


def _bar_cases() -> list[_Case]:
    rng = random.Random(42)
    many_tiny = [str(rng.randint(150, 400)) for _ in range(40)]
    large_batch = [str(150 + rng.randint(0, 2750)) for _ in range(200)]
    cases = [
        _Case(
            "tiny-pieces-40",
            _pieces(many_tiny),
            [_rule("FRAME")],
        ),
        _Case(
            "almost-stock",
            _pieces(["5960", "2000", "1500"]),
            [_rule("FRAME")],
        ),
        _Case(
            "bfd-fragmentation",
            _pieces(["3000", "3000", "3000", "2000", "2000", "2000", "1400", "800", "800"]),
            [_rule("FRAME")],
            profile=_saw(kerf_mm=D("0"), head_trim_mm=D("0"), tail_trim_mm=D("0")),
        ),
        _Case(
            "mixed-colors",
            _pieces(["1200", "1400", "1600"], color="WHITE")
            + _pieces(["1200", "1400", "1600"], color="ANTRACITA", prefix="c"),
            [_rule("FRAME", color="WHITE"), _rule("FRAME", color="ANTRACITA")],
        ),
        _Case(
            "material-mix",
            _pieces(["1200", "1400", "1600", "1800"], material="PVC")
            + _pieces(
                ["1100", "1300", "1500", "1700"],
                material="ALUMINIUM",
                sku="FRAME-ALU",
                prefix="a",
            ),
            [_rule("FRAME", material="PVC"), _rule("FRAME-ALU", material="ALUMINIUM")],
        ),
        _Case(
            "angled-saw-limit†",
            [
                _piece("1000", 0, angles=("30", "60")),
                _piece("1000", 1, angles=("45", "45")),
                _piece("1000", 2, angles=("30", "30")),
            ],
            [_rule("FRAME")],
            profile=_saw(max_angle_deg=D("45")),
        ),
        _Case(
            "reinforcement-vs-pvc",
            _pieces(["2000", "2100", "2200"], material="PVC")
            + _pieces(
                ["1950", "2050", "2150"], material="STEEL", sku="REFORCE", prefix="r"
            ),
            [_rule("FRAME", material="PVC"), _rule("REFORCE", material="STEEL")],
        ),
        _Case(
            "variant-lengths",
            _pieces(["3200"] * 12),
            [_rule("FRAME", alts=[D("6500")])],
        ),
        _Case(
            "remnant-pool",
            _pieces(["2000", "2000", "1500", "600"]),
            [_rule("FRAME")],
            profile=_saw(min_keep_remnant_mm=D("500")),
            remnants=[
                _remnant("r-big", "5900", "auth-FRAME-PVC-WHITE"),
                _remnant("r-mid", "4000", "auth-FRAME-PVC-WHITE"),
                _remnant("r-small", "700", "auth-FRAME-PVC-WHITE"),
            ],
        ),
        _Case(
            "large-batch-200",
            _pieces(large_batch),
            [_rule("FRAME")],
        ),
        _Case(
            "oversize-honest†",
            _pieces(["6200", "2000", "1800"]),
            [_rule("FRAME")],
            remnants=[_remnant("r-oversize", "6400", "auth-FRAME-PVC-WHITE")],
        ),
        _Case(
            "shared-commercial-sku",
            _pieces(["2000", "2100"], sku="MARCO")
            + _pieces(["1900", "1800"], sku="TRANSOM", prefix="t"),
            [
                _rule("MARCO"),
                StockRule(
                    stock_authority_id="auth-TRANSOM-PVC-WHITE",
                    workshop_sku="TRANSOM",
                    commercial_sku="COM-FRAME-WHITE",
                    manufacturer_name="MFG",
                    supplier_name="SUP",
                    purchase_unit="BAR",
                    material=CutMaterial.PVC,
                    color="WHITE",
                    stock_length_mm=D("6000"),
                ),
            ],
        ),
    ]
    return cases


class _SheetCase:
    def __init__(self, name: str, pieces: list[NestPiece], rule: SheetRule,
                 remnants: list[SheetRemnant] | None = None) -> None:
        self.name = name
        self.pieces = pieces
        self.rule = rule
        self.remnants = remnants or []


def _npiece(w: str, h: str, index: int, **kwargs: object) -> NestPiece:
    return NestPiece.model_validate({
        "piece_id": f"np{index}",
        "workshop_sku": "PANEL",
        "width_mm": D(w),
        "height_mm": D(h),
        **kwargs,
    })


def _sheet_cases() -> list[_SheetCase]:
    rng = random.Random(7)
    sheet = SheetRule(
        workshop_sku="PANEL",
        purchasing_sku="PANEL-2000x1500",
        sheet_width_mm=D("2000"),
        sheet_height_mm=D("1500"),
        edge_trim_mm=D("10"),
    )
    awkward: list[tuple[str, str]] = [
        ("1240", "820"), ("900", "600"), ("1100", "400"), ("700", "1300"), ("500", "500"),
        ("1400", "300"), ("800", "900"), ("600", "1100"), ("950", "450"), ("1300", "700"),
        ("400", "1200"), ("1050", "350"), ("850", "650"), ("1150", "550"), ("750", "950"),
    ]
    large = [(str(150 + rng.randint(0, 1300)), str(150 + rng.randint(0, 1100))) for _ in range(100)]
    cases = [
        _SheetCase(
            "panel-grid-24",
            [_npiece("600", "400", i) for i in range(24)],
            sheet,
        ),
        _SheetCase(
            "awkward-mix-15",
            [_npiece(w, h, i) for i, (w, h) in enumerate(awkward)],
            sheet,
        ),
        _SheetCase(
            "rotation-critical",
            [
                _npiece("1600", "900", 0),
                _npiece("900", "1600", 1),
                _npiece("1600", "900", 2),
                _npiece("500", "500", 3),
            ],
            sheet,
        ),
        _SheetCase(
            "kerf-correctness†",
            [_npiece("490", "490", i) for i in range(24)],
            SheetRule(
                workshop_sku="PANEL",
                purchasing_sku="PANEL-2000x1500",
                sheet_width_mm=D("2000"),
                sheet_height_mm=D("1500"),
                edge_trim_mm=D("10"),
                kerf_mm=D("6"),
            ),
        ),
        _SheetCase(
            "alternate-split-win",
            [_npiece("1900", "700", 0), _npiece("980", "680", 1), _npiece("980", "680", 2)],
            sheet,
        ),
        _SheetCase(
            "remnant-sheets",
            [_npiece("800", "600", i) for i in range(4)]
            + [_npiece("1000", "700", 4)],
            sheet,
            remnants=[
                SheetRemnant(remnant_id="rs-1", width_mm=D("1500"), height_mm=D("900")),
                SheetRemnant(remnant_id="rs-2", width_mm=D("1200"), height_mm=D("1200")),
            ],
        ),
        _SheetCase(
            "large-batch-100",
            [_npiece(w, h, i) for i, (w, h) in enumerate(large)],
            sheet,
        ),
    ]
    return cases


# ── Runner ───────────────────────────────────────────────────────────────


def _bar_metrics(bars: list[CutBar]) -> dict[str, D]:
    purchased = sum((bar.stock_length_mm for bar in bars), D("0"))
    productive = sum((bar.productive_length_mm for bar in bars), D("0"))
    return {
        "units": D(len(bars)),
        "purchased": purchased,
        "productive": productive,
        "waste": purchased - productive,
    }


def _pct(part: D, whole: D) -> str:
    if whole <= 0:
        return "—"
    return f"{(part / whole * D('100')).quantize(D('0.1'))}%"


def run_benchmark() -> str:
    lines: list[str] = []
    lines.append("## §13 Optimization benchmark — legacy vs industrial tiers\n")
    lines.append(
        "Legacy = pre-§4 algorithms pinned verbatim (BFD single-length packing; "
        "guillotine right+bottom split; no remnants, variants, deep tier, kerf "
        "on sheets, or unplaced reporting). Current = `optimize_cut`/`nest_rects` "
        "at strategy `auto` with the remnant pool.\n"
    )
    lines.append("### Bar cutting (mm)\n")
    lines.append(
        "| Case | Legacy bars | Current bars | Legacy waste | Current waste | "
        "Waste Δ | Remnant bars | Unplaced (cur.) |"
    )
    lines.append("|---|---|---|---|---|---|---|---|")
    totals = {"legacy_waste": D("0"), "new_waste": D("0"), "legacy_units": D("0"), "new_units": D("0")}
    for case in _bar_cases():
        legacy_failed = False
        try:
            legacy_bars = legacy_cut_plan(case.pieces, case.rules, case.profile)
        except PieceLongerThanUsableStock:
            legacy_failed = True
            # Legacy raised — plan the fittable pieces it could host.
            fittable = [
                p
                for p in case.pieces
                if p.length_mm + case.profile.kerf_mm
                <= max(r.stock_length_mm for r in case.rules)
                - case.profile.head_trim_mm
                - case.profile.tail_trim_mm
            ]
            legacy_bars = legacy_cut_plan(fittable, case.rules, case.profile)
        old = _bar_metrics(legacy_bars)
        result = optimize_cut(
            case.pieces,
            case.rules,
            case.profile,
            remnants=case.remnants or None,
            strategy="auto",
        )
        new_bars = result.workshop_cut_plan
        remnant_bars = sum(1 for b in new_bars if b.source == "REMNANT")
        purchased_bars = sum(1 for b in new_bars if b.source == "NEW")
        productive = sum((b.productive_length_mm for b in new_bars), D("0"))
        new_purchased_mm = sum(
            (b.stock_length_mm for b in new_bars if b.source == "NEW"), D("0")
        )
        # Waste = purchased stock not productive + remnant stock not productive
        remnant_used_mm = sum(
            (b.stock_length_mm for b in new_bars if b.source == "REMNANT"), D("0")
        )
        new_waste = new_purchased_mm + remnant_used_mm - productive
        delta = old["waste"] - new_waste
        totals["legacy_waste"] += old["waste"]
        totals["new_waste"] += new_waste
        totals["legacy_units"] += old["units"]
        totals["new_units"] += D(len(new_bars))
        unplaced = len(result.unplaced)
        flag = " (raised†)" if legacy_failed else ""
        lines.append(
            f"| {case.name}{flag} | {old['units']} | {len(new_bars)} "
            f"({purchased_bars} new) | {old['waste']} | {new_waste} | "
            f"{delta} | {remnant_bars} | {unplaced} |"
        )
    saved = totals["legacy_waste"] - totals["new_waste"]
    lines.append(
        f"| **TOTAL** | {totals['legacy_units']} | {totals['new_units']} | "
        f"{totals['legacy_waste']} | {totals['new_waste']} | **{saved} "
        f"({_pct(saved, totals['legacy_waste'])})** | | |"
    )
    lines.append("")
    lines.append(
        "† correctness evidence, not a waste regression: the legacy row either "
        "cut angles the saw cannot make (angled-saw-limit), left a piece unmade "
        "entirely (oversize-honest — its waste counts only the pieces it could "
        "plan), or would report fewer units because it never models saw "
        "feasibility or offcut stock."
    )
    lines.append("")
    lines.append("### Sheet nesting (mm²)\n")
    lines.append(
        "| Case | Legacy sheets | Current sheets | Legacy waste | Current waste | "
        "Waste Δ | Remnant sheets | Unplaced (leg./cur.) |"
    )
    lines.append("|---|---|---|---|---|---|---|---|")
    s_totals = {"legacy_waste": D("0"), "new_waste": D("0"), "legacy_units": D("0"), "new_units": D("0")}
    for scase in _sheet_cases():
        old_sheets, old_productive, old_unplaced = legacy_nest(scase.pieces, scase.rule)
        old_area = scase.rule.sheet_width_mm * scase.rule.sheet_height_mm * old_sheets
        old_waste = old_area - old_productive
        sresult = nest_rects(scase.pieces, scase.rule, remnants=scase.remnants or None)
        new_layouts = sresult.layouts
        remnant_sheets = sum(1 for s in new_layouts if s.source == "REMNANT")
        new_sheets = len(new_layouts)
        new_productive = sum((s.productive_area_mm2 for s in new_layouts), D("0"))
        new_area = sum(
            (s.sheet_width_mm * s.sheet_height_mm for s in new_layouts), D("0")
        )
        new_waste = new_area - new_productive
        delta = old_waste - new_waste
        s_totals["legacy_waste"] += old_waste
        s_totals["new_waste"] += new_waste
        s_totals["legacy_units"] += D(old_sheets)
        s_totals["new_units"] += D(new_sheets)
        lines.append(
            f"| {scase.name} | {old_sheets} | {new_sheets} | {old_waste} | "
            f"{new_waste} | {delta} | {remnant_sheets} | "
            f"{old_unplaced}/{len(sresult.unplaced)} |"
        )
    s_saved = s_totals["legacy_waste"] - s_totals["new_waste"]
    lines.append(
        f"| **TOTAL** | {s_totals['legacy_units']} | {s_totals['new_units']} | "
        f"{s_totals['legacy_waste']} | {s_totals['new_waste']} | "
        f"**{s_saved} ({_pct(s_saved, s_totals['legacy_waste'])})** | | |"
    )
    lines.append("")
    lines.append(
        "† kerf-correctness: the legacy algorithm ignored saw kerf entirely — "
        "its 2-sheet plan is physically impossible (pieces packed flush); the "
        "current engine honestly buys the third sheet."
    )
    return "\n".join(lines)


if __name__ == "__main__":
    print(run_benchmark())
