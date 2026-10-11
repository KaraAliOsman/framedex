"""Advanced manufacturing authority, independent arithmetic and adversaries."""

from copy import deepcopy
from decimal import Context, Decimal as D, ROUND_DOWN, localcontext
from pathlib import Path
import json

import pytest
from pydantic import ValidationError
from backend.catalogs.demo_advanced import advanced_manifest
from dekopen_engine.geometry import calculate_geometry, compute_geometry
from dekopen_engine.models import SystemParams, ProfileRole
from dekopen_engine.openings import OpeningCapabilityError
from engine.tests.advanced_cases import (
    advanced_cases,
    advanced_node,
    advanced_params,
    advanced_typologies,
)
from engine.tests.opening_cases import opening_params


def test_all_fourteen_recipes_match_reviewed_cuts_bom_hardware_and_kinematics() -> None:
    frozen = json.loads(
        Path(__file__).with_name("golden_advanced_openings.json").read_text(encoding="utf-8")
    )
    assert advanced_cases() == frozen
    assert len(frozen) == 14
    for value in frozen.values():
        assert value["profile_cuts"] and value["hardware_items"] and value["glasses"]
        assert all(
            leaf["advanced"]["synthetic"] and "sin certificación" in leaf["advanced"]["source"]
            for leaf in value["opening_leaves"]
        )
        assert all(leaf["total_weight_kg"] is not None for leaf in value["leaf_weights"])


@pytest.mark.parametrize("code,recipe", advanced_typologies())
def test_save_pricing_and_documentary_callers_cannot_change_advanced_precision(
    code: str, recipe: str,
) -> None:
    from dekopen_engine.product import ProductModel, ProductModule, CoupledAssembly, evaluate_product
    from dekopen_engine.snapshot import result_payload

    node, params = advanced_node(code, recipe), advanced_params(code)
    assert node.width_mm is not None and node.height_mm is not None
    product = ProductModel(version="product-v2", assembly=CoupledAssembly(modules=[
        ProductModule(id="module", width_mm=node.width_mm, height_mm=node.height_mm, tree=node),
    ]))
    expected = result_payload(calculate_geometry(node, params, finish="WHITE"))
    expected_product = evaluate_product(product, params, finish="WHITE").bom
    assert expected_product is not None
    for precision in (16, 28, 256):
        with localcontext(Context(prec=precision, rounding=ROUND_DOWN)):
            assert result_payload(calculate_geometry(node, params, finish="WHITE")) == expected
            result = evaluate_product(product, params, finish="WHITE").bom
            assert result is not None and result_payload(result) == result_payload(expected_product)


@pytest.mark.parametrize("code,recipe", advanced_typologies())
def test_no_advanced_recipe_is_authorized_by_a_basic_system(code: str, recipe: str) -> None:
    with pytest.raises(OpeningCapabilityError):
        calculate_geometry(advanced_node(code, recipe), opening_params("DEMO_60"))


@pytest.mark.parametrize("code,recipe", advanced_typologies())
def test_advanced_choice_requires_explicit_known_recipe_and_no_alias(
    code: str, recipe: str
) -> None:
    node, params = advanced_node(code, recipe), advanced_params(code)
    for patch in (
        {"opening_recipe_code": None},
        {"opening_recipe_code": "NO-DECLARADA"},
        {"opening_type": "TURN_LEFT"},
        {
            "sliding_layout": {
                "tracks": 2,
                "panels": [
                    {"slot": "S1", "kind": "MOVING", "track": 0, "travel": "RIGHT"},
                    {"slot": "S2", "kind": "MOVING", "track": 1, "travel": "LEFT"},
                ],
            }
        },
    ):
        raw = {**node.model_dump(mode="json"), **patch}
        with pytest.raises((ValueError, ValidationError)):
            calculate_geometry(
                type(node).model_validate_json(json.dumps(raw)), params, finish="WHITE"
            )


@pytest.mark.parametrize(
    "code,recipe,leaf_width,leaf_height,glass_width,glass_height,cut_add",
    [
        ("DEMO_HST", "A", "1470", "2125", "1330", "1985", "0"),
        ("DEMO_PSK", "XO", "1450", "2100", "1320", "1970", "6"),
        ("DEMO_PIVOT_V", "EJE-30", "1100", "1300", "970", "1170", "6"),
        ("DEMO_PIVOT_H", "EJE-30", "1100", "1300", "970", "1170", "6"),
        ("DEMO_PUERTA_CORREDERA", "XO", "1470", "2125", "1350", "2005", "0"),
    ],
)
def test_independent_manufacturing_arithmetic(
    code: str,
    recipe: str,
    leaf_width: str,
    leaf_height: str,
    glass_width: str,
    glass_height: str,
    cut_add: str,
) -> None:
    # Reviewed by hand from frame 60/70, signed overlaps, threshold 30,
    # frame clear span, meeting 20/0, face 70, rebate 8 and clearance 3.
    # These constants are independent of the code under test.
    result = calculate_geometry(advanced_node(code, recipe), advanced_params(code), finish="WHITE")
    fact = result.opening_leaves[0]
    assert (fact.width_mm, fact.height_mm) == (D(leaf_width), D(leaf_height))
    assert (result.glasses[0].width_mm, result.glasses[0].height_mm) == (
        D(glass_width),
        D(glass_height),
    )
    cuts = [
        cut
        for cut in result.profile_cuts
        if cut.leaf_id == fact.leaf_id
        and cut.role in (ProfileRole.SASH, ProfileRole.SLIDING_SASH, ProfileRole.DOOR_SASH)
    ]
    assert sorted((cut.length_mm, cut.qty) for cut in cuts) == sorted(
        [(D(leaf_width) + D(cut_add), 2), (D(leaf_height) + D(cut_add), 2)]
    )


def test_pivot_axis_is_thirty_percent_and_plan_really_rotates_about_it() -> None:
    v = calculate_geometry(
        advanced_node("DEMO_PIVOT_V", "EJE-30"), advanced_params("DEMO_PIVOT_V"), finish="WHITE"
    ).opening_leaves[0]
    assert v.advanced is not None
    assert v.advanced.pivot_x_mm == D("380")  # 50 + 1100 × 0.30
    assert [(p.x_mm, p.depth_mm) for p in v.advanced.open_plan] == [
        (D("380"), D("-330")),
        (D("380"), D("770")),
    ]
    h = calculate_geometry(
        advanced_node("DEMO_PIVOT_H", "EJE-30"), advanced_params("DEMO_PIVOT_H"), finish="WHITE"
    ).opening_leaves[0]
    assert h.advanced is not None and h.advanced.pivot_y_mm == D("440")  # 50 + 1300 × 0.30
    assert len(h.advanced.open_plan_polygon) == 4
    assert [p.depth_mm.quantize(D("0.01")) for p in h.advanced.open_plan_polygon] == [
        D("-390"),
        D("-390"),
        D("910"),
        D("910"),
    ]


def test_folding_packet_preserves_rigid_lengths_links_and_minimum_pitch() -> None:
    for recipe in ("3+0-PASO", "2+1-SIN-PASO"):
        result = calculate_geometry(
            advanced_node("DEMO_PLEGABLE", recipe), advanced_params("DEMO_PLEGABLE"), finish="WHITE"
        )
        for leaf in result.opening_leaves:
            data = leaf.advanced
            assert data is not None and data.packet_pitch_mm == D("60")
            a, b = data.open_plan
            assert abs(a.x_mm - b.x_mm) >= D("60")
            rigid = ((a.x_mm - b.x_mm) ** 2 + (a.depth_mm - b.depth_mm) ** 2).sqrt()
            assert rigid.quantize(D("0.01")) == leaf.width_mm.quantize(D("0.01"))
        first, second = result.opening_leaves[0].advanced, result.opening_leaves[1].advanced
        assert first is not None and second is not None
        assert first.open_plan[1] == second.open_plan[0]
        if recipe == "3+0-PASO":
            passage = result.opening_leaves[2].advanced
            assert passage is not None
            assert (
                passage.pass_open_plan is not None and passage.pass_open_plan != passage.open_plan
            )
            kit = next(
                item
                for item in result.hardware_items
                if item.leaf_id == result.opening_leaves[2].leaf_id
            )
            assert any("CIERRE-PASO" in item.sku for item in kit.contents)


def test_vertical_double_slide_has_separate_tracks_and_declared_balance() -> None:
    for suffix, balance in (("MUELLES", "SPRING"), ("CONTRAPESOS", "COUNTERWEIGHT")):
        result = calculate_geometry(
            advanced_node("DEMO_GUILLOTINA", "DOBLE-" + suffix),
            advanced_params("DEMO_GUILLOTINA"),
            finish="WHITE",
        )
        facts = [leaf.advanced for leaf in result.opening_leaves if leaf.advanced is not None]
        assert len(facts) == 2
        assert [leaf.travel for leaf in facts] == ["DOWN", "UP"]
        assert [leaf.track for leaf in facts] == [0, 1]
        assert all(leaf.balance == balance and leaf.travel_mm == D("860") for leaf in facts)


def test_fixed_frame_panel_has_one_identity_and_no_fictitious_hardware() -> None:
    raw = advanced_params("DEMO_HST").model_dump(mode="json")
    raw["opening_capabilities"][1]["advanced_recipes"][0]["panels"][1]["fixed_in_sash"] = False
    params = SystemParams.model_validate_json(json.dumps(raw))
    result = calculate_geometry(advanced_node("DEMO_HST", "A"), params, finish="WHITE")
    fixed = result.opening_leaves[1]
    assert fixed.handle is None and fixed.leaf_id == "S2"
    assert result.glasses[1].leaf_id == fixed.leaf_id
    assert not any(
        cut.role is ProfileRole.SLIDING_SASH and cut.leaf_id == fixed.leaf_id
        for cut in result.profile_cuts
    )
    assert not any(item.leaf_id == fixed.leaf_id for item in result.hardware_items)


@pytest.mark.parametrize(
    "change",
    [
        "share",
        "same-track",
        "same-plane",
        "missing-pivot",
        "missing-balance",
        "missing-passage-kit",
        "wrong-order",
        "missing-guide",
        "alien-kit",
        "through-jamb",
    ],
)
def test_catalog_rejects_incomplete_or_physically_inconsistent_authority(change: str) -> None:
    code = (
        "DEMO_HST"
        if change in ("share", "same-track", "same-plane", "alien-kit", "through-jamb")
        else "DEMO_PIVOT_V"
        if change == "missing-pivot"
        else "DEMO_GUILLOTINA"
        if change == "missing-balance"
        else "DEMO_PLEGABLE"
    )
    raw = deepcopy(
        next(record for record in advanced_manifest() if record["code"] == code)["params"]
    )
    cap = raw["opening_capabilities"][1]
    recipe = cap["advanced_recipes"][
        1 if code == "DEMO_HST" else 1 if change == "missing-passage-kit" else 0
    ]
    if change == "share":
        recipe["panels"][0]["share"] = "0.26"
    elif change == "same-track":
        recipe["panels"][2]["track"] = 0
    elif change == "same-plane":
        recipe["panels"][2]["plane_offset_mm"] = "20"
    elif change == "missing-pivot":
        recipe["panels"][0]["pivot_fraction"] = None
    elif change == "missing-balance":
        recipe["panels"][0]["balance"] = None
    elif change == "missing-passage-kit":
        recipe["pass_through_hardware_kit_skus"] = []
    elif change == "wrong-order":
        recipe["panels"][0]["fold_index"] = 2
        recipe["panels"][2]["fold_index"] = 0
    elif change == "missing-guide":
        recipe["rail_profile_role"] = None
        recipe["rail_count"] = 0
        recipe["rail_sides"] = []
    elif change == "through-jamb":
        recipe["panels"][0]["travel"] = "LEFT"
    else:
        recipe["hardware_kit_skus"] = ["FOREIGN"]
    with pytest.raises(ValidationError):
        SystemParams.model_validate_json(json.dumps(raw))


def test_unknown_mass_is_not_converted_to_zero_or_a_manufacturing_permission() -> None:
    raw = advanced_params("DEMO_PIVOT_V").model_dump(mode="json")
    raw["effective_profile_articles"]["SASH"]["weight_kg_m"] = None
    params = SystemParams.model_validate_json(json.dumps(raw))
    with pytest.raises(ValueError, match="unknown|Sin dato|undecidable"):
        calculate_geometry(advanced_node("DEMO_PIVOT_V", "EJE-30"), params, finish="WHITE")


def test_diagnostic_returns_sourced_limits_without_authorizing_a_bad_leaf() -> None:
    node = advanced_node("DEMO_PIVOT_V", "EJE-30").model_copy(update={"width_mm": D("3000")})
    computation = compute_geometry(
        node,
        advanced_params("DEMO_PIVOT_V"),
        finish="WHITE",
        diagnostic=True,
        diagnose_catalog_limits=True,
    )
    assert computation.result is None
    assert (
        computation.catalog_violations
        and "sin certificación" in computation.catalog_violations[0].params["source"]
    )
