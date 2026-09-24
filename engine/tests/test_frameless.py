"""Frameless glass-only modules (mandate §14).

The pane IS the module — real support/fitting concepts, never fake
FRAME/SASH profiles. Channels become profile-cut runs on the declared edge,
clamps and fittings are counted pieces, and anything we can't honestly
evaluate surfaces as an issue instead of silently fitting the old model.
"""

from decimal import Decimal

from dekopen_engine.contour import Contour
from dekopen_engine.models import (
    BayOpeningType,
    EffectiveProfileArticle,
    MaterialType,
    NodeType,
    ParametricNode,
    PlanPoint,
    ProfileRole,
    SystemParams,
)
from dekopen_engine.product import (
    CoupledAssembly,
    EdgeSide,
    FramelessFitting,
    FramelessFittingKind,
    FramelessSpec,
    FramelessSupport,
    FramelessSupportKind,
    IssueCode,
    ProductIssue,
    ProductModel,
    ProductModule,
    ProductStatus,
    Severity,
    evaluate_product,
)

GLASS_4_MM = Decimal("4.00")
GLASS_4_SPEC = "4"

CHANNEL_ARTICLE = EffectiveProfileArticle(
    sku="UCHANNEL-12",
    role=ProfileRole.COUPLER,
    material=MaterialType.ALUMINIUM,
    face_width_mm=Decimal("12.00"),
    welding_loss_mm=Decimal("0.00"),
    reinforcement_gap_mm=Decimal("0.00"),
    weight_kg_m=Decimal("0.3500"),
    steel_weight_kg_m=None,
    reinforcement_sku=None,
)


def _frameless_module(
    module_id: str = "g1",
    width: str = "1200",
    height: str = "2100",
    *,
    opening: BayOpeningType = BayOpeningType.FIXED,
    panel_sku: str | None = None,
    spec: FramelessSpec | None = None,
    tree_children: list[ParametricNode] | None = None,
    contour: Contour | None = None,
) -> ProductModule:
    tree = (
        ParametricNode(id=module_id, type=NodeType.BAY, children=tree_children)
        if tree_children is not None
        else ParametricNode(
            id=module_id,
            type=NodeType.BAY,
            opening_type=opening,
            glass_thickness_mm=GLASS_4_MM,
            glass_spec=GLASS_4_SPEC,
            panel_article_sku=panel_sku,
        )
    )
    return ProductModule(
        id=module_id,
        width_mm=Decimal(width),
        height_mm=Decimal(height),
        contour=contour,
        frameless=spec if spec is not None else FramelessSpec(),
        tree=tree,
    )


def _product(modules: list[ProductModule]) -> ProductModel:
    return ProductModel(
        version="product-v2",
        assembly=CoupledAssembly(modules=modules, couplings=[]),
    )


def _issues(module_eval) -> dict[str, ProductIssue]:  # type: ignore[no-untyped-def]
    return {issue.code: issue for issue in module_eval.issues}


class TestFramelessPane:
    def test_fixed_pane_emits_glass_and_real_concepts(
        self, demo_60_params: SystemParams
    ) -> None:
        # A 1200x2100 pane on a bottom channel with a patch fitting and two
        # clamps: glass + one channel cut + counted fittings — no FRAME/SASH.
        module = _frameless_module(
            spec=FramelessSpec(
                supports=[
                    FramelessSupport(
                        kind=FramelessSupportKind.CHANNEL,
                        edge=EdgeSide.BOTTOM,
                        article_sku="UCHANNEL-12",
                    ),
                    FramelessSupport(
                        kind=FramelessSupportKind.CLAMPS,
                        edge=EdgeSide.TOP,
                        article_sku="CLAMP-SQ",
                        qty=2,
                    ),
                ],
                fittings=[
                    FramelessFitting(
                        kind=FramelessFittingKind.PATCH_FITTING,
                        sku="PATCH-PT20",
                        qty=2,
                    ),
                    FramelessFitting(
                        kind=FramelessFittingKind.LOCK, sku="LOCK-L1", qty=1
                    ),
                ],
            )
        )
        evaluation = evaluate_product(
            _product([module]),
            demo_60_params,
            coupler_articles={"UCHANNEL-12": CHANNEL_ARTICLE},
        )
        assert evaluation.status is ProductStatus.VALID
        module_eval = evaluation.modules[0]
        assert module_eval.issues == []
        result = module_eval.result
        assert result is not None
        assert [cut.role for cut in result.profile_cuts] == [ProfileRole.CHANNEL]
        cut = result.profile_cuts[0]
        assert (cut.sku, cut.length_mm, cut.qty, cut.bay_id) == (
            "UCHANNEL-12",
            Decimal("1200.00"),
            1,
            "g1",
        )
        assert len(result.glasses) == 1
        glass = result.glasses[0]
        assert (glass.width_mm, glass.height_mm) == (
            Decimal("1200.00"),
            Decimal("2100.00"),
        )
        assert glass.glass_spec == GLASS_4_SPEC
        # The whole pane is exposed → all four edges declared.
        assert glass.exposed_edges == ["top", "right", "bottom", "left"]
        assert {(item.kind, item.sku, item.qty) for item in result.fittings} == {
            ("CLAMP", "CLAMP-SQ", 2),
            ("PATCH_FITTING", "PATCH-PT20", 2),
            ("LOCK", "LOCK-L1", 1),
        }

    def test_exposed_edges_subset_flows_to_glass(
        self, demo_60_params: SystemParams
    ) -> None:
        module = _frameless_module(
            spec=FramelessSpec(exposed_edges=[EdgeSide.BOTTOM])
        )
        evaluation = evaluate_product(_product([module]), demo_60_params)
        result = evaluation.modules[0].result
        assert result is not None
        assert result.glasses[0].exposed_edges == ["bottom"]

    def test_vertical_edge_channel_uses_height(
        self, demo_60_params: SystemParams
    ) -> None:
        module = _frameless_module(
            spec=FramelessSpec(
                supports=[
                    FramelessSupport(
                        kind=FramelessSupportKind.CHANNEL,
                        edge=EdgeSide.LEFT,
                        article_sku="UCHANNEL-12",
                        qty=2,
                    )
                ]
            )
        )
        evaluation = evaluate_product(
            _product([module]),
            demo_60_params,
            coupler_articles={"UCHANNEL-12": CHANNEL_ARTICLE},
        )
        cut = evaluation.modules[0].result.profile_cuts[0]  # type: ignore[union-attr]
        assert cut.length_mm == Decimal("2100.00")
        assert cut.qty == 2

    def test_unknown_channel_sku_is_a_honest_warning(
        self, demo_60_params: SystemParams
    ) -> None:
        # An undeclared channel article can't be invented — warn and drop the
        # run rather than cutting a phantom profile.
        module = _frameless_module(
            spec=FramelessSpec(
                supports=[
                    FramelessSupport(
                        kind=FramelessSupportKind.CHANNEL,
                        edge=EdgeSide.BOTTOM,
                        article_sku="NOEXISTE",
                    )
                ]
            )
        )
        evaluation = evaluate_product(_product([module]), demo_60_params)
        module_eval = evaluation.modules[0]
        issues = _issues(module_eval)
        assert IssueCode.FRAMELESS_ARTICLE_UNKNOWN.value in issues
        assert issues[IssueCode.FRAMELESS_ARTICLE_UNKNOWN.value].severity is (
            Severity.WARNING
        )
        assert module_eval.result is not None
        assert module_eval.result.profile_cuts == []

    def test_opening_type_warns_but_keeps_fixed_bom(
        self, demo_60_params: SystemParams
    ) -> None:
        # A declared swing opening on a glass-only pane is honest advice that
        # the operable-leaf path isn't implemented — the fixed BOM still lands.
        module = _frameless_module(opening=BayOpeningType.TILT_TURN_LEFT)
        evaluation = evaluate_product(_product([module]), demo_60_params)
        module_eval = evaluation.modules[0]
        issues = _issues(module_eval)
        assert IssueCode.FRAMELESS_OPENING_UNSUPPORTED.value in issues
        assert issues[IssueCode.FRAMELESS_OPENING_UNSUPPORTED.value].severity is (
            Severity.WARNING
        )
        assert module_eval.result is not None
        assert len(module_eval.result.glasses) == 1

    def test_split_tree_is_an_error(self, demo_60_params: SystemParams) -> None:
        # A mullioned frameless pane has members we haven't modeled — refuse,
        # don't evaluate half of it.
        module = _frameless_module(
            tree_children=[
                ParametricNode(
                    id="left",
                    type=NodeType.BAY,
                    opening_type=BayOpeningType.FIXED,
                    glass_thickness_mm=GLASS_4_MM,
                    glass_spec=GLASS_4_SPEC,
                ),
                ParametricNode(
                    id="right",
                    type=NodeType.BAY,
                    opening_type=BayOpeningType.FIXED,
                    glass_thickness_mm=GLASS_4_MM,
                    glass_spec=GLASS_4_SPEC,
                ),
            ]
        )
        evaluation = evaluate_product(_product([module]), demo_60_params)
        module_eval = evaluation.modules[0]
        issues = _issues(module_eval)
        assert IssueCode.FRAMELESS_SPLITS_UNSUPPORTED.value in issues
        assert issues[IssueCode.FRAMELESS_SPLITS_UNSUPPORTED.value].severity is (
            Severity.ERROR
        )
        assert module_eval.result is None
        assert evaluation.status is ProductStatus.INVALID

    def test_contour_plus_frameless_is_rejected(
        self, demo_60_params: SystemParams
    ) -> None:
        module = _frameless_module(
            contour=Contour(
                vertices=[
                    PlanPoint(x_mm=Decimal("0"), y_mm=Decimal("0")),
                    PlanPoint(x_mm=Decimal("1200"), y_mm=Decimal("0")),
                    PlanPoint(x_mm=Decimal("1200"), y_mm=Decimal("2100")),
                    PlanPoint(x_mm=Decimal("0"), y_mm=Decimal("2100")),
                ],
                bulges=[Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0")],
            )
        )
        evaluation = evaluate_product(_product([module]), demo_60_params)
        module_eval = evaluation.modules[0]
        issues = _issues(module_eval)
        assert IssueCode.FRAMELESS_CONTOUR_UNSUPPORTED.value in issues
        assert issues[IssueCode.FRAMELESS_CONTOUR_UNSUPPORTED.value].severity is (
            Severity.ERROR
        )
        assert module_eval.result is None

    def test_panel_fill_on_pane_warns(self, demo_60_params: SystemParams) -> None:
        module = _frameless_module(panel_sku="PANEL-SANDWICH")
        evaluation = evaluate_product(_product([module]), demo_60_params)
        issues = _issues(evaluation.modules[0])
        assert IssueCode.FRAMELESS_PANEL_UNSUPPORTED.value in issues

    def test_documentary_computation_carries_pane_and_channel_members(
        self, demo_60_params: SystemParams
    ) -> None:
        # The freeze/seal path needs a GeometryComputation, not a framed
        # approximation: pane infill + channel member on the declared edge.
        from dekopen_engine.product import frameless_module_computation

        module = _frameless_module(
            spec=FramelessSpec(
                supports=[
                    FramelessSupport(
                        kind=FramelessSupportKind.CHANNEL,
                        edge=EdgeSide.LEFT,
                        article_sku="UCHANNEL-12",
                        qty=2,
                    )
                ],
                exposed_edges=[EdgeSide.LEFT],
            )
        )
        computation, issues = frameless_module_computation(
            module, coupler_articles={"UCHANNEL-12": CHANNEL_ARTICLE}
        )
        assert issues == []
        assert computation is not None
        trace = computation.manufacturing_trace
        assert trace is not None
        assert len(trace.members) == 2  # qty=2 → one semantic member each
        member = trace.members[0]
        assert member.role is ProfileRole.CHANNEL
        assert member.workshop_sku == "UCHANNEL-12"
        assert member.cut_length_mm == Decimal("2100.00")
        assert member.axis.value == "VERTICAL"
        assert member.direct_segment is not None
        assert member.direct_segment.start.x_mm == Decimal("0")
        assert member.direct_segment.end.y_mm == Decimal("2100")
        assert len(trace.infills) == 1
        infill = trace.infills[0]
        assert infill.kind == "GLASS"
        assert infill.direct_rect is not None
        assert (infill.direct_rect.width_mm, infill.direct_rect.height_mm) == (
            Decimal("1200"),
            Decimal("2100"),
        )
        assert computation.openings[0].bay_id == "g1"
        assert computation.infills[0].bead_supported is True
        # The computation result is the same BOM the evaluation emits.
        evaluation = evaluate_product(
            _product([module]),
            demo_60_params,
            coupler_articles={"UCHANNEL-12": CHANNEL_ARTICLE},
        )
        assert computation.result == evaluation.modules[0].result

    def test_documentary_computation_maps_edges_and_retention(
        self, demo_60_params: SystemParams
    ) -> None:
        # Manufacturing origin is top-left, y down: TOP sits at y=0,
        # BOTTOM at y=height. A pane with no declared retention must stay
        # unsupported (inspector R06 blocks the freeze).
        from dekopen_engine.product import (
            frameless_module_computation,
            frameless_retention_declared,
        )

        module = _frameless_module(
            spec=FramelessSpec(
                supports=[
                    FramelessSupport(
                        kind=FramelessSupportKind.CHANNEL,
                        edge=EdgeSide.TOP,
                        article_sku="UCHANNEL-12",
                        qty=1,
                    ),
                    FramelessSupport(
                        kind=FramelessSupportKind.CHANNEL,
                        edge=EdgeSide.BOTTOM,
                        article_sku="UCHANNEL-12",
                        qty=1,
                    ),
                ],
                exposed_edges=[],
            )
        )
        computation, issues = frameless_module_computation(
            module, coupler_articles={"UCHANNEL-12": CHANNEL_ARTICLE}
        )
        assert issues == []
        assert computation is not None
        segments = {
            m.physical_member_slot: m.direct_segment
            for m in computation.manufacturing_trace.members
        }
        top = segments["channel-0-top"]
        assert top is not None
        assert top.start.y_mm == Decimal("0") and top.end.y_mm == Decimal("0")
        bottom = segments["channel-1-bottom"]
        assert bottom is not None
        assert bottom.start.y_mm == Decimal("2100")
        assert bottom.end.y_mm == Decimal("2100")

        bare = _frameless_module(spec=FramelessSpec())
        bare_computation, _ = frameless_module_computation(
            bare, coupler_articles={}
        )
        assert bare_computation is not None
        assert bare_computation.infills[0].bead_supported is False
        assert frameless_retention_declared(
            FramelessSpec(fittings=[])
        ) is False
        assert frameless_retention_declared(
            FramelessSpec(
                fittings=[
                    FramelessFitting(
                        kind=FramelessFittingKind.PATCH_FITTING,
                        sku="PF-1",
                        qty=2,
                    )
                ]
            )
        ) is True
