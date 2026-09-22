from __future__ import annotations

from decimal import Decimal

import pytest

from dekopen_engine.models import (
    BayOpeningType,
    EffectiveProfileArticle,
    MaterialType,
    ProfileRole,
    SystemParams,
)
from dekopen_engine.product import (
    IssueCode,
    ProductModel,
    ProductStatus,
    Severity,
    coupling_ids,
    equalize_coupling_angles,
    equalize_module_widths,
    evaluate_product,
    make_bow_assembly,
    module_ids,
    nominal_height_mm,
    nominal_width_mm,
    set_coupler_sku,
    set_coupling_angle,
    set_module_count,
    set_module_opening,
    set_module_width,
)
from dekopen_engine.trig import cos_degrees, sin_degrees

GLASS_4_MM = Decimal("4.00")
GLASS_4_SPEC = "4"

COUPLER_ARTICLE = EffectiveProfileArticle(
    sku="ACOPLE-60",
    role=ProfileRole.COUPLER,
    material=MaterialType.PVC,
    face_width_mm=Decimal("40.00"),
    welding_loss_mm=Decimal("0.00"),
    reinforcement_gap_mm=Decimal("0.00"),
    weight_kg_m=Decimal("0.9000"),
    steel_weight_kg_m=None,
    reinforcement_sku="REF-ACOPLE",
)


def bow_3(module_count: int = 3) -> ProductModel:
    return make_bow_assembly(
        module_count=module_count,
        width_mm=Decimal("2100"),
        height_mm=Decimal("1400"),
        angle_deg=Decimal("15"),
        glass_thickness_mm=GLASS_4_MM,
        glass_spec=GLASS_4_SPEC,
    )


def with_couplers(
    product: ProductModel, sku: str | None = "ACOPLE-60"
) -> ProductModel:
    for coupling in product.assembly.couplings:
        product = set_coupler_sku(product, coupling.id, sku)
    return product


class TestTrig:
    @pytest.mark.parametrize(
        ("degrees", "expected"),
        [
            ("0", "0"),
            ("30", "0.5"),
            ("45", "0.70710678118654752440"),
            ("60", "0.86602540378443864676"),
            ("90", "1"),
            ("180", "0"),
            ("270", "-1"),
            ("-30", "-0.5"),
            ("360", "0"),
            ("450", "1"),
        ],
    )
    def test_sin(self, degrees: str, expected: str) -> None:
        assert abs(sin_degrees(Decimal(degrees)) - Decimal(expected)) < Decimal(
            "1e-16"
        )

    @pytest.mark.parametrize(
        ("degrees", "expected"),
        [
            ("0", "1"),
            ("60", "0.5"),
            ("90", "0"),
            ("120", "-0.5"),
            ("180", "-1"),
            ("-90", "0"),
            ("360", "1"),
        ],
    )
    def test_cos(self, degrees: str, expected: str) -> None:
        assert abs(cos_degrees(Decimal(degrees)) - Decimal(expected)) < Decimal(
            "1e-16"
        )


class TestConstruction:
    def test_make_bow(self) -> None:
        product = bow_3()
        assert module_ids(product) == ["m1", "m2", "m3"]
        assert coupling_ids(product) == ["c1", "c2"]
        assert nominal_width_mm(product) == Decimal("2100")
        assert nominal_height_mm(product) == Decimal("1400")
        widths = [m.width_mm for m in product.assembly.modules]
        assert sum(widths) == Decimal("2100")

    def test_make_bow_requires_two_modules(self) -> None:
        with pytest.raises(ValueError):
            bow_3(module_count=1)


class TestEvaluation:
    def test_bow_without_coupler_is_geometry_valid_manufacturing_incomplete(
        self, demo_60_params: SystemParams
    ) -> None:
        evaluation = evaluate_product(bow_3(), demo_60_params)
        assert evaluation.status is ProductStatus.MANUFACTURING_INCOMPLETE
        assert evaluation.plan is not None
        assert len(evaluation.plan.modules) == 3
        assert len(evaluation.plan.couplings) == 2
        missing = [
            issue
            for issue in evaluation.issues
            if issue.code == IssueCode.COUPLER_PROFILE_MISSING.value
        ]
        assert len(missing) == 2
        # Module geometry still resolves into a BOM.
        assert evaluation.bom is not None
        assert any(
            cut.sku == "MARCO" for cut in evaluation.bom.profile_cuts
        )

    def test_bow_with_couplers_is_valid(self, demo_60_params: SystemParams) -> None:
        product = with_couplers(bow_3())
        evaluation = evaluate_product(
            product, demo_60_params, coupler_articles={"ACOPLE-60": COUPLER_ARTICLE}
        )
        assert evaluation.status is ProductStatus.VALID
        assert evaluation.issues == []
        assert evaluation.bom is not None
        coupler_cuts = [
            cut
            for cut in evaluation.bom.profile_cuts
            if cut.role is ProfileRole.COUPLER
        ]
        assert len(coupler_cuts) == 2
        assert all(cut.sku == "ACOPLE-60" for cut in coupler_cuts)
        assert all(cut.length_mm == Decimal("1400") for cut in coupler_cuts)
        assert all(cut.angle_left == Decimal("90") for cut in coupler_cuts)
        reinf = [
            piece
            for piece in evaluation.bom.reinforcements
            if piece.role is ProfileRole.COUPLER
        ]
        assert [p.reinforcement_sku for p in reinf] == ["REF-ACOPLE"] * 2

    def test_unknown_coupler_sku_is_reported_never_faked(
        self, demo_60_params: SystemParams
    ) -> None:
        product = with_couplers(bow_3(), sku="DOES-NOT-EXIST")
        evaluation = evaluate_product(product, demo_60_params, coupler_articles={})
        assert evaluation.status is ProductStatus.MANUFACTURING_INCOMPLETE
        codes = {issue.code for issue in evaluation.issues}
        assert codes == {IssueCode.COUPLER_PROFILE_UNKNOWN.value}

    def test_height_mismatch_marks_coupling_incomplete(
        self, demo_60_params: SystemParams
    ) -> None:
        product = with_couplers(bow_3())
        m2 = product.assembly.modules[1].model_copy(
            update={"height_mm": Decimal("1200")}
        )
        product = product.model_copy(
            update={
                "assembly": product.assembly.model_copy(
                    update={
                        "modules": [
                            product.assembly.modules[0],
                            m2,
                            product.assembly.modules[2],
                        ]
                    }
                )
            }
        )
        evaluation = evaluate_product(
            product, demo_60_params, coupler_articles={"ACOPLE-60": COUPLER_ARTICLE}
        )
        assert evaluation.status is ProductStatus.MANUFACTURING_INCOMPLETE
        mismatched = {
            issue.target
            for issue in evaluation.issues
            if issue.code == IssueCode.COUPLER_HEIGHT_MISMATCH.value
        }
        assert mismatched == {"coupling:c1", "coupling:c2"}

    def test_module_geometry_failure_is_a_warning(
        self, demo_60_params: SystemParams
    ) -> None:
        # DOOR_ENTRY requires a panel SKU the module does not declare.
        product = set_module_opening(bow_3(), "m2", BayOpeningType.DOOR_ENTRY)
        evaluation = evaluate_product(product, demo_60_params)
        assert evaluation.status is ProductStatus.MANUFACTURING_INCOMPLETE
        failed = [
            issue
            for issue in evaluation.issues
            if issue.code == IssueCode.MODULE_GEOMETRY_FAILED.value
        ]
        assert len(failed) == 1
        assert failed[0].target == "module:m2"
        m2_eval = next(m for m in evaluation.modules if m.module_id == "m2")
        assert m2_eval.result is None

    def test_excessive_turn_is_invalid(self, demo_60_params: SystemParams) -> None:
        product = equalize_coupling_angles(bow_3(), Decimal("95"))
        evaluation = evaluate_product(product, demo_60_params)
        assert evaluation.status is ProductStatus.INVALID
        codes = {issue.code for issue in evaluation.issues}
        assert IssueCode.ASSEMBLY_FOLDS_BACK.value in codes

    def test_coupler_reinforcement_uses_gap_adjusted_length(
        self, demo_60_params: SystemParams
    ) -> None:
        coupler = COUPLER_ARTICLE.model_copy(
            update={"reinforcement_gap_mm": Decimal("15.00")}
        )
        evaluation = evaluate_product(
            with_couplers(bow_3()),
            demo_60_params,
            coupler_articles={"ACOPLE-60": coupler},
        )
        assert evaluation.status is ProductStatus.VALID
        assert evaluation.bom is not None
        steel = [
            piece
            for piece in evaluation.bom.reinforcements
            if piece.parent_profile_sku == "ACOPLE-60"
        ]
        assert len(steel) == 2
        # height 1400 - 2*15 gap; coupler posts are square-cut (no weld loss)
        assert {piece.length_mm for piece in steel} == {Decimal("1370.00")}

    def test_coupler_reinforcement_nonpositive_is_flagged(
        self, demo_60_params: SystemParams
    ) -> None:
        coupler = COUPLER_ARTICLE.model_copy(
            update={"reinforcement_gap_mm": Decimal("700.00")}
        )
        evaluation = evaluate_product(
            with_couplers(bow_3()),
            demo_60_params,
            coupler_articles={"ACOPLE-60": coupler},
        )
        assert evaluation.status is ProductStatus.MANUFACTURING_INCOMPLETE
        assert any(
            issue.code == IssueCode.COUPLER_REINFORCEMENT_NONPOSITIVE.value
            for issue in evaluation.issues
        )
        assert evaluation.bom is not None
        assert not any(
            piece.parent_profile_sku == "ACOPLE-60"
            for piece in evaluation.bom.reinforcements
        )

    def test_duplicate_coupling_ids_raise(
        self, demo_60_params: SystemParams
    ) -> None:
        product = bow_3()
        product = product.model_copy(
            update={
                "assembly": product.assembly.model_copy(
                    update={
                        "couplings": [
                            product.assembly.couplings[0],
                            product.assembly.couplings[0],
                        ]
                    }
                )
            }
        )
        with pytest.raises(ValueError, match="unique"):
            evaluate_product(product, demo_60_params)

    def test_couplings_count_mismatch_is_invalid(
        self, demo_60_params: SystemParams
    ) -> None:
        product = bow_3()
        product = product.model_copy(
            update={
                "assembly": product.assembly.model_copy(
                    update={"couplings": product.assembly.couplings[:1]}
                )
            }
        )
        evaluation = evaluate_product(product, demo_60_params)
        assert evaluation.status is ProductStatus.INVALID
        assert any(
            issue.code == IssueCode.COUPLINGS_COUNT_MISMATCH.value
            and issue.severity is Severity.ERROR
            for issue in evaluation.issues
        )

    def test_plan_depth_overlap_is_invalid(
        self, demo_60_params: SystemParams
    ) -> None:
        # Three 200 mm modules folding -85°/-85° on a deep (300 mm) system:
        # m3 swings back over m1 so their depth rectangles collide even
        # though no front-chain segments cross.
        deep = demo_60_params.model_copy(update={"depth_mm": Decimal("300.00")})
        product = make_bow_assembly(
            module_count=3,
            width_mm=Decimal("600"),
            height_mm=Decimal("1400"),
            angle_deg=Decimal("-85"),
            glass_thickness_mm=GLASS_4_MM,
            glass_spec=GLASS_4_SPEC,
        )
        evaluation = evaluate_product(product, deep)
        assert evaluation.status is ProductStatus.INVALID
        assert any(
            issue.code == IssueCode.PLAN_SELF_INTERSECTION.value
            and issue.severity is Severity.ERROR
            for issue in evaluation.issues
        )

    def test_plan_depth_no_false_positive_on_shallow_system(
        self, demo_60_params: SystemParams
    ) -> None:
        # Same fold magnitude in the positive direction on the real 60 mm
        # depth: the assembly fans outward so modules stay clear of each other.
        product = make_bow_assembly(
            module_count=3,
            width_mm=Decimal("600"),
            height_mm=Decimal("1400"),
            angle_deg=Decimal("85"),
            glass_thickness_mm=GLASS_4_MM,
            glass_spec=GLASS_4_SPEC,
        )
        evaluation = evaluate_product(product, demo_60_params)
        assert not any(
            issue.code == IssueCode.PLAN_SELF_INTERSECTION.value
            for issue in evaluation.issues
        )

    def test_plan_adjacent_negative_angle_is_invalid(
        self, demo_60_params: SystemParams
    ) -> None:
        # A negative deflection swings the next module's depth rectangle into
        # the previous one — a real collision at the joint even on the shallow
        # 60 mm system, with no front-chain crossing.
        product = make_bow_assembly(
            module_count=2,
            width_mm=Decimal("400"),
            height_mm=Decimal("1400"),
            angle_deg=Decimal("-20"),
            glass_thickness_mm=GLASS_4_MM,
            glass_spec=GLASS_4_SPEC,
        )
        evaluation = evaluate_product(product, demo_60_params)
        assert evaluation.status is ProductStatus.INVALID
        assert any(
            issue.code == IssueCode.PLAN_SELF_INTERSECTION.value
            and issue.severity is Severity.ERROR
            for issue in evaluation.issues
        )

    def test_plan_straight_and_positive_joints_stay_clean(
        self, demo_60_params: SystemParams
    ) -> None:
        # Adjacent rectangles share only their joint boundary at 0° and fan
        # apart at positive angles — neither is a collision.
        for angle in (Decimal("0"), Decimal("20")):
            product = make_bow_assembly(
                module_count=2,
                width_mm=Decimal("400"),
                height_mm=Decimal("1400"),
                angle_deg=angle,
                glass_thickness_mm=GLASS_4_MM,
                glass_spec=GLASS_4_SPEC,
            )
            evaluation = evaluate_product(product, demo_60_params)
            assert not any(
                issue.code == IssueCode.PLAN_SELF_INTERSECTION.value
                for issue in evaluation.issues
            ), f"angle {angle} must not collide"

    def test_plan_polygon_shape(self, demo_60_params: SystemParams) -> None:
        evaluation = evaluate_product(bow_3(), demo_60_params)
        plan = evaluation.plan
        assert plan is not None
        # 3 modules, 4 corners each; coupler wedges between them.
        for module in plan.modules:
            assert len(module.corners) == 4
        for coupling in plan.couplings:
            assert len(coupling.polygon) == 3
        # Bow with +15° joints curves upward: overall depth exceeds 60 mm.
        assert plan.height_mm > Decimal("60")
        # Front chain has 4 vertices: module 1 is the baseline (flat),
        # then the chain turns +15° at each coupling.
        assert len(plan.front_chain) == 4
        ys = [p.y_mm for p in plan.front_chain]
        assert ys[0] == ys[1] == Decimal("0.00")
        assert ys[2] > ys[1] and ys[3] > ys[2]

    def test_traceable_bay_ids_are_module_prefixed(
        self, demo_60_params: SystemParams
    ) -> None:
        evaluation = evaluate_product(
            with_couplers(bow_3()),
            demo_60_params,
            coupler_articles={"ACOPLE-60": COUPLER_ARTICLE},
        )
        assert evaluation.bom is not None
        bay_ids = {
            cut.bay_id for cut in evaluation.bom.profile_cuts if cut.bay_id
        }
        assert any(bay_id.startswith("m1|") for bay_id in bay_ids)
        assert {"c1", "c2"} <= bay_ids

    def test_bom_prefixes_panel_leaf_ids(
        self, demo_60_params: SystemParams
    ) -> None:
        product = make_bow_assembly(
            module_count=3,
            width_mm=Decimal("2100"),
            height_mm=Decimal("2000"),
            angle_deg=Decimal("15"),
            glass_thickness_mm=GLASS_4_MM,
            glass_spec=GLASS_4_SPEC,
        )
        product = set_module_opening(product, "m2", BayOpeningType.DOOR_ENTRY)
        product = set_module_width(product, "m2", Decimal("950"))
        modules = [
            module.model_copy(
                update={
                    "tree": module.tree.model_copy(
                        update={
                            "panel_article_sku": "PANEL-SANDWICH-DEMO-24",
                            "glass_thickness_mm": None,
                            "glass_spec": None,
                        }
                    )
                }
            )
            if module.id == "m2"
            else module
            for module in product.assembly.modules
        ]
        product = product.model_copy(
            update={
                "assembly": product.assembly.model_copy(
                    update={"modules": modules}
                )
            }
        )
        evaluation = evaluate_product(
            with_couplers(product),
            demo_60_params,
            coupler_articles={"ACOPLE-60": COUPLER_ARTICLE},
        )
        assert evaluation.status is ProductStatus.VALID
        assert evaluation.bom is not None and evaluation.bom.panels
        assert all(
            panel.bay_id.startswith("m2|")
            and (panel.leaf_id is None or panel.leaf_id.startswith("m2|"))
            for panel in evaluation.bom.panels
        )


class TestCommands:
    def test_set_module_count_grows_and_shrinks(self) -> None:
        product = bow_3()
        grown = set_module_count(product, 5)
        assert len(grown.assembly.modules) == 5
        assert len(grown.assembly.couplings) == 4
        assert grown.assembly.couplings[-1].angle_deg == Decimal("15")
        shrunk = set_module_count(grown, 2)
        assert module_ids(shrunk) == ["m1", "m2"]
        assert coupling_ids(shrunk) == ["c1"]

    def test_equalize_widths_preserves_total(self) -> None:
        product = set_module_width(bow_3(), "m1", Decimal("900"))
        product = equalize_module_widths(product)
        widths = [m.width_mm for m in product.assembly.modules]
        assert sum(widths) == Decimal("2300")
        assert max(widths) - min(widths) <= Decimal("0.01")

    def test_commands_are_pure_and_return_new_models(self) -> None:
        product = bow_3()
        updated = set_coupling_angle(product, "c1", Decimal("20"))
        assert updated.assembly.couplings[0].angle_deg == Decimal("20")
        assert product.assembly.couplings[0].angle_deg == Decimal("15")

    def test_single_unit_is_a_degenerate_assembly(
        self, demo_60_params: SystemParams
    ) -> None:
        product = make_bow_assembly(
            module_count=2,
            width_mm=Decimal("1000"),
            height_mm=Decimal("1200"),
            angle_deg=Decimal("0"),
            glass_thickness_mm=GLASS_4_MM,
            glass_spec=GLASS_4_SPEC,
        )
        unit = set_module_count(product, 1)
        assert len(unit.assembly.couplings) == 0
        evaluation = evaluate_product(unit, demo_60_params)
        assert evaluation.status is ProductStatus.VALID
