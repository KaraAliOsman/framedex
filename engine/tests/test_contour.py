"""Contour-kernel tests: shape math, member cuts, and honest rejections."""

from decimal import Decimal as D


from dekopen_engine.contour import (
    Contour,
    arc_params,
    contour_area,
    contour_points,
    edge_length,
    ensure_ccw,
    interior_angle,
    offset_contour,
    validate_contour,
)
from dekopen_engine.trig import asin_degrees
from dekopen_engine.models import (
    BayOpeningType,
    NodeType,
    ParametricNode,
    PlanPoint,
)
from dekopen_engine.product import (
    IssueCode,
    ProductModel,
    ProductStatus,
    contour_module_computation,
    evaluate_product,
)

from engine.tests.catalog import demo_60_params


def _pt(x: str, y: str) -> PlanPoint:
    return PlanPoint(x_mm=D(x), y_mm=D(y))


def _bay(**over) -> ParametricNode:
    return ParametricNode.model_validate(
        {
            "id": "B1",
            "type": NodeType.BAY,
            "opening_type": BayOpeningType.FIXED,
            "glass_spec": "4-16-4",
            "glass_thickness_mm": D("24"),
            "glass_article_sku": "DVH-4-16-4",
            **over,
        }
    )


def _product(contour: Contour, tree: ParametricNode | None = None) -> ProductModel:
    return ProductModel.model_validate(
        {
            "version": "product-v2",
            "assembly": {
                "modules": [
                    {
                        "id": "m1",
                        "width_mm": D("2400"),
                        "height_mm": D("1400"),
                        "contour": contour,
                        "tree": tree if tree is not None else _bay(),
                    }
                ],
                "couplings": [],
            },
        }
    )


class TestContourMath:
    def test_rect_area_and_lengths(self) -> None:
        c = Contour.rect(D("1000"), D("500"))
        assert validate_contour(c) == []
        assert contour_area(c.vertices, c.bulges) == D("500000")
        assert edge_length(c, 0) == D("1000")
        assert interior_angle(c, 0) == D("90")

    def test_trapezoid_miters_are_real_corner_angles(self) -> None:
        c = Contour.trapezoid(D("2400"), D("1400"), D("200"), D("200"))
        # Top corners inset 200 over 1400 rise → interior 180-atan(1400/200)
        top = interior_angle(c, 2)
        bottom = interior_angle(c, 1)
        assert bottom < D("90")
        assert top + bottom == D("180") + D("0.0000000000001") or abs(top + bottom - D("180")) < D(
            "0.001"
        )

    def test_cw_input_normalizes(self) -> None:
        cw = Contour(
            vertices=[_pt("0", "0"), _pt("0", "1400"), _pt("2400", "1400"), _pt("2400", "0")],
            bulges=[None] * 4,
        )
        ccw = ensure_ccw(cw)
        assert signed_area_helper(ccw) > 0

    def test_arc_params_and_length(self) -> None:
        p0, p1 = _pt("2400", "1400"), _pt("0", "1400")
        center, radius, span = arc_params(p0, p1, D("300"))
        assert radius == D("2550")  # (300²+1200²)/(2·300)
        assert abs(span - D("56.144974")) < D("0.001")
        # center sits below the chord (arc bulges up-right of the edge)
        assert center.y_mm < D("1400")
        assert abs(
            edge_length(Contour.arch_top(D("2400"), D("1400"), D("300")), 2) - D("2498.782")
        ) < D("0.01")

    def test_arc_sampling_reaches_the_apex(self) -> None:
        # A positive bulge must rise above its chord, never sag below it —
        # inverted travel direction samples the arc on the concave side.
        points = contour_points(Contour.arch_top(D("2400"), D("1400"), D("300")))
        assert max(p.y_mm for p in points) > D("1690")
        assert min(p.y_mm for p in points) == D("0")

    def test_cw_input_with_curved_closing_edge_flips_sagitta(self) -> None:
        # Wound CW, the arch's curved edge travels rightward and its bulge is
        # left-of-edge (inward): sagitta reads -300. Normalization must give
        # the same geometric arc back: +300 on the top edge.
        cw = Contour(
            vertices=[
                PlanPoint(x_mm=D("0"), y_mm=D("0")),
                PlanPoint(x_mm=D("0"), y_mm=D("1400")),
                PlanPoint(x_mm=D("2400"), y_mm=D("1400")),
                PlanPoint(x_mm=D("2400"), y_mm=D("0")),
            ],
            bulges=[None, D("-300"), None, None],
        )
        normalized = ensure_ccw(cw)
        assert normalized.bulges == [None, None, D("300"), None]
        assert contour_area(normalized.vertices, normalized.bulges) == contour_area(
            Contour.arch_top(D("2400"), D("1400"), D("300")).vertices,
            [None, None, D("300"), None],
        )

    def test_offset_rect_is_exact_inset(self) -> None:
        fill = offset_contour(Contour.rect(D("1000"), D("500")), D("20"))
        xs = sorted(v.x_mm for v in fill.vertices)
        ys = sorted(v.y_mm for v in fill.vertices)
        assert xs == [D("20"), D("20"), D("980"), D("980")]
        assert ys == [D("20"), D("20"), D("480"), D("480")]

    def test_offset_arch_shrinks_radius(self) -> None:
        fill = offset_contour(Contour.arch_top(D("2400"), D("1400"), D("300")), D("20"))
        assert fill.bulges[2] is not None and fill.bulges[2] < D("300")
        # side walls meet the shrunken arc between the offset chord (1380)
        # and the chord itself (1400) — the arc is shallower at its ends
        assert D("1380") < fill.vertices[2].y_mm < D("1400")
        # offset preserves exact area accounting (arch adds area above the
        # chord, so the bound is the original contour's area)
        area = contour_area(fill.vertices, fill.bulges)
        assert (
            D("0")
            < area
            < contour_area(
                Contour.arch_top(D("2400"), D("1400"), D("300")).vertices,
                Contour.arch_top(D("2400"), D("1400"), D("300")).bulges,
            )
        )

    def test_self_intersection_rejected(self) -> None:
        bow = Contour(
            vertices=[_pt("0", "0"), _pt("1000", "1000"), _pt("1000", "0"), _pt("0", "1000")],
            bulges=[None] * 4,
        )
        problems = validate_contour(bow)
        assert any("self-intersect" in p for p in problems)

    def test_self_touching_edge_rejected(self) -> None:
        # The third edge ends ON the first edge's interior — a touch, not a
        # strict crossing; a non-simple loop must not validate.
        touching = Contour(
            vertices=[
                _pt("0", "0"),
                _pt("100", "0"),
                _pt("100", "100"),
                _pt("50", "0"),
                _pt("0", "100"),
            ],
            bulges=[None] * 5,
        )
        problems = validate_contour(touching)
        assert any("self-intersect" in p for p in problems)

    def test_collinear_overlap_rejected(self) -> None:
        overlapping = Contour(
            vertices=[
                _pt("0", "0"),
                _pt("100", "0"),
                _pt("100", "100"),
                _pt("60", "0"),
                _pt("40", "0"),
                _pt("0", "100"),
            ],
            bulges=[None] * 6,
        )
        problems = validate_contour(overlapping)
        assert any("self-intersect" in p for p in problems)

    def test_repeated_nonadjacent_vertex_rejected(self) -> None:
        repeated = Contour(
            vertices=[
                _pt("0", "0"),
                _pt("100", "0"),
                _pt("100", "100"),
                _pt("100", "0"),
                _pt("0", "100"),
            ],
            bulges=[None] * 5,
        )
        problems = validate_contour(repeated)
        assert problems

    def test_oversized_sagitta_rejected(self) -> None:
        c = Contour(
            vertices=[_pt("0", "0"), _pt("1000", "0"), _pt("0", "0")],
            bulges=[None, D("600"), None],
        )
        # chord 1000, sagitta 600 > 500 → non-minor arc
        assert any("sagitta" in p for p in validate_contour(c))


def signed_area_helper(c: Contour) -> D:
    return contour_area(c.vertices, c.bulges)


class TestContourEvaluation:
    def test_trapezoid_end_to_end(self) -> None:
        ev = evaluate_product(
            _product(Contour.trapezoid(D("2400"), D("1400"), D("200"), D("200"))),
            demo_60_params(),
        )
        assert ev.status == ProductStatus.VALID
        bom = ev.bom
        assert bom is not None
        frames = [c for c in bom.profile_cuts if c.role.value == "FRAME"]
        beads = [c for c in bom.profile_cuts if c.role.value == "GLAZING_BEAD"]
        assert len(frames) == 4 and len(beads) == 4
        by_len = sorted(c.length_mm for c in frames)
        # 2×sqrt(200²+1400²) sides, 2000 top, 2400 bottom + weld allowances
        assert by_len[0] == by_len[1] == D("1420.21")
        assert by_len[2] == D("2006.00")
        assert by_len[3] == D("2406.00")
        glass = bom.glasses[0]
        assert glass.shape is not None and len(glass.shape) == 4
        # pocket = nominal - 2*(face - rebate + clearance) per side
        assert glass.width_mm == D("2296.22")  # trapezoid sloped sides widen the inset
        assert glass.area_m2 > 0 and glass.weight_kg > 0

    def test_arch_emits_bent_member_and_incomplete_status(self) -> None:
        ev = evaluate_product(
            _product(Contour.arch_top(D("2400"), D("1400"), D("300"))),
            demo_60_params(),
        )
        assert ev.status == ProductStatus.MANUFACTURING_INCOMPLETE
        codes = [i.code for i in ev.issues]
        assert IssueCode.MEMBER_BENDING_REQUIRED.value in codes
        arc_cuts = [c for c in ev.bom.profile_cuts if c.sagitta_mm is not None]
        assert arc_cuts and all(c.length_mm > D("2400") for c in arc_cuts)
        glass = ev.bom.glasses[0]
        assert glass.shape is not None and len(glass.shape) > 4  # arc sampled
        # Bounds come from the sampled arc, not the vertex box: the crown
        # overshoots the springline, so the reported height must cover it
        # (springline ~1400 − inset + ~300 rise − inset ≫ the vertex span).
        assert glass.height_mm > D("1400")
        assert glass.height_mm == D(
            max(p.y_mm for p in glass.shape) - min(p.y_mm for p in glass.shape)
        ).quantize(D("0.01"))
        # Welded PVC contour frames carry reinforcement like the rect path —
        # even when the catalog leaves the steel SKU for downstream to resolve.
        bom = ev.bom
        assert bom is not None
        assert any(piece.role.value == "FRAME" for piece in bom.reinforcements)

    def test_rect_contour_matches_rect_convention(self) -> None:
        # A rectangular contour must reproduce the classic frame: 4 members,
        # 45/45 miters, glass pocket = nominal - 2*(face - rebate + clearance).
        ev = evaluate_product(_product(Contour.rect(D("1200"), D("800"))), demo_60_params())
        assert ev.status == ProductStatus.VALID
        frames = sorted(c.length_mm for c in ev.bom.profile_cuts if c.role.value == "FRAME")
        assert frames == [D("806.00"), D("806.00"), D("1206.00"), D("1206.00")]
        assert all(
            c.angle_left == D("45") and c.angle_right == D("45")
            for c in ev.bom.profile_cuts
            if c.role.value == "FRAME"
        )
        glass = ev.bom.glasses[0]
        # face 60 - rebate 20 + clearance 5 (demo catalog) → inset 45 per side
        assert glass.width_mm == D("1110.00")
        assert glass.height_mm == D("710.00")
        # A rectangular fill stays shape=None so production sheet-nests it.
        assert glass.shape is None

    def test_arch_corner_angles_follow_the_arc(self) -> None:
        c = Contour.arch_top(D("2400"), D("1400"), D("300"))
        # r=2550 → span = 2·asin(1200/2550) ≈ 56.14°; each springline corner
        # = 90° + span/2, the bottom stays square.
        span = D("2") * asin_degrees(D("1200") / D("2550"))
        expected = D("90") + span / D("2")
        assert abs(interior_angle(c, 2) - expected) < D("0.01")
        assert abs(interior_angle(c, 3) - expected) < D("0.01")
        assert interior_angle(c, 0) == D("90")
        assert interior_angle(c, 1) == D("90")

    def test_degenerate_arc_edge_reports_not_crashes(self) -> None:
        bad = Contour(
            vertices=[_pt("0", "0"), _pt("0", "0"), _pt("100", "100")],
            bulges=[D("300"), None, None],
        )
        problems = validate_contour(bad)
        assert problems and "zero-length" in problems[0]

    def test_narrow_contour_collapses_fill_honestly(self) -> None:
        # 80 mm wide module with a 45 mm per-side inset: the pocket inverts.
        ev = evaluate_product(
            _product(Contour.rect(D("80"), D("800"))), demo_60_params()
        )
        assert ev.status is ProductStatus.INVALID
        codes = [i.code for i in ev.issues]
        assert codes == [IssueCode.CONTOUR_INVALID.value]

    def test_split_tree_rejected(self) -> None:
        tree = ParametricNode.model_validate(
            {
                "id": "R",
                "type": NodeType.SPLIT_H,
                "children": [_bay(id="A"), _bay(id="B")],
            }
        )
        ev = evaluate_product(_product(Contour.rect(D("1200"), D("800")), tree), demo_60_params())
        assert ev.status == ProductStatus.INVALID
        assert any(i.code == IssueCode.CONTOUR_SPLITS_UNSUPPORTED.value for i in ev.issues)

    def test_operable_opening_warns_and_still_builds_frame(self) -> None:
        ev = evaluate_product(
            _product(
                Contour.trapezoid(D("2400"), D("1400"), D("200"), D("200")),
                _bay(opening_type=BayOpeningType.TILT_TURN_LEFT),
            ),
            demo_60_params(),
        )
        assert ev.status == ProductStatus.MANUFACTURING_INCOMPLETE
        assert any(i.code == IssueCode.CONTOUR_OPENING_UNSUPPORTED.value for i in ev.issues)
        assert len([c for c in ev.bom.profile_cuts if c.role.value == "FRAME"]) == 4

    def test_panel_infill_warns(self) -> None:
        ev = evaluate_product(
            _product(Contour.rect(D("1200"), D("800")), _bay(panel_article_sku="PNL-24")),
            demo_60_params(),
        )
        assert any(i.code == IssueCode.CONTOUR_PANEL_UNSUPPORTED.value for i in ev.issues)

    def test_degenerate_contour_invalid(self) -> None:
        ev = evaluate_product(
            _product(
                Contour(
                    vertices=[_pt("0", "0"), _pt("0", "0"), _pt("10", "10")],
                    bulges=[None, None, None],
                )
            ),
            demo_60_params(),
        )
        assert ev.status == ProductStatus.INVALID
        assert any(i.code == IssueCode.CONTOUR_INVALID.value for i in ev.issues)

    def test_documentary_trace_carries_contour_geometry(self) -> None:
        """The freeze path must seal real contour members + glass polygon —
        never the rectangular approximation compute_geometry would emit."""
        product = _product(Contour.trapezoid(D("2400"), D("1400"), D("200"), D("200")))
        computation, issues = contour_module_computation(
            product.assembly.modules[0], demo_60_params()
        )
        assert not [i for i in issues if i.severity.value == "error"]
        assert computation is not None
        assert computation.result is not None
        trace = computation.manufacturing_trace
        assert trace is not None
        frames = [m for m in trace.members if m.role.value == "FRAME"]
        beads = [m for m in trace.members if m.role.value == "GLAZING_BEAD"]
        assert len(frames) == 4 and len(beads) == 4
        # Each frame member seals its own contour edge as a direct segment —
        # the slanted sides have non-axis-aligned chords.
        chords = {
            (
                m.direct_segment.start.x_mm,
                m.direct_segment.start.y_mm,
                m.direct_segment.end.x_mm,
                m.direct_segment.end.y_mm,
            )
            for m in frames
            if m.direct_segment is not None
        }
        assert len(chords) == 4
        assert any(x0 != x1 and y0 != y1 for (x0, y0, x1, y1) in chords)
        # PVC authority → reinforcement declared with its emitted length.
        assert all(m.reinforcement_required for m in frames)
        assert all(
            m.reinforcement_length_mm is not None and m.reinforcement_length_mm > 0
            for m in frames
        )
        (infill,) = trace.infills
        assert infill.kind == "GLASS" and infill.bay_id == "B1"
        assert infill.width_mm > 0 and infill.height_mm > 0
        assert [i.bay_id for i in computation.infills] == ["B1"]
        assert [o.bay_id for o in computation.openings] == ["B1"]

    def test_arch_trace_seals_sagitta_and_sampled_shape(self) -> None:
        product = _product(Contour.arch_top(D("2400"), D("1400"), D("300")))
        computation, _issues = contour_module_computation(
            product.assembly.modules[0], demo_60_params()
        )
        assert computation is not None
        trace = computation.manufacturing_trace
        arc_members = [m for m in trace.members if m.sagitta_mm is not None]
        assert arc_members
        (infill,) = trace.infills
        assert infill.shape is not None and len(infill.shape) > 4
