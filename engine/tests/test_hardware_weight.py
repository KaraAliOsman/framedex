from decimal import Decimal

import pytest
from pydantic import ValidationError

from dekopen_engine import BayOpeningType, MaterialType, ParametricNode, ProfileRole, RailType, SystemParams, calculate_geometry
from dekopen_engine.hardware import AmbiguousHardwareKit, NoCompatibleHardwareKit, normalize_opening_type, resolve_hardware_kit
from dekopen_engine.weight import ExactLeafWeight, MissingWeightAuthority, base_leaf_weight, with_hardware_weight
from engine.tests.test_shot06_core import core_node

D = Decimal


@pytest.mark.parametrize("opening,normalized", [
    (BayOpeningType.TURN_LEFT, "TURN"), (BayOpeningType.TURN_RIGHT, "TURN"),
    (BayOpeningType.TILT_TURN_LEFT, "TILT_TURN"), (BayOpeningType.TILT_TURN_RIGHT, "TILT_TURN"),
    (BayOpeningType.SLIDING_2L, "SLIDING"), (BayOpeningType.SLIDING_3L, "SLIDING"),
    (BayOpeningType.SLIDING_4L, "SLIDING"), (BayOpeningType.DOOR_ENTRY, "DOOR"),
    (BayOpeningType.DOOR_DOUBLE, "DOOR"), (BayOpeningType.AWNING, "AWNING"),
    (BayOpeningType.FIXED, "FIXED"),
])
def test_opening_normalization(opening: BayOpeningType, normalized: str) -> None:
    assert normalize_opening_type(opening) == normalized


def test_explicit_sku_and_ambiguity_are_order_independent(
    demo_60_params: SystemParams, g3_node: ParametricNode,
) -> None:
    kit = next(k for k in demo_60_params.available_hardware_kits if k.sku == "KIT-TILT-TURN")
    alternate = kit.model_copy(update={"sku": "OTHER-OB"})
    for kits in ([kit, alternate], [alternate, kit]):
        params = demo_60_params.model_copy(update={"available_hardware_kits": kits})
        with pytest.raises(AmbiguousHardwareKit):
            calculate_geometry(g3_node, params)
        result = calculate_geometry(g3_node.model_copy(update={"hardware_set_sku": "OTHER-OB"}), params)
        assert result.hardware_items[0].kit_sku == "OTHER-OB"
    for sku in ("ABSENT", "KIT-SLIDING"):
        with pytest.raises(NoCompatibleHardwareKit):
            calculate_geometry(g3_node.model_copy(update={"hardware_set_sku": sku}), demo_60_params)


@pytest.mark.parametrize("updates", [
    {"min_leaf_width_mm": D("896.01")}, {"max_leaf_width_mm": D("895.99")},
    {"min_leaf_height_mm": D("1296.01")}, {"max_leaf_height_mm": D("1295.99")},
    {"max_leaf_weight_kg": D("33.28")}, {"rail_type": RailType.MONO},
    {"opening_type": "TURN"},
])
def test_rejects_each_incompatible_criterion_even_with_explicit_sku(
    demo_60_params: SystemParams, g3_node: ParametricNode, updates: dict[str, object],
) -> None:
    kit = next(k for k in demo_60_params.available_hardware_kits if k.sku == "KIT-TILT-TURN")
    params = demo_60_params.model_copy(update={"available_hardware_kits": [kit.model_copy(update=updates)]})
    for node in (g3_node, g3_node.model_copy(update={"hardware_set_sku": kit.sku})):
        with pytest.raises(NoCompatibleHardwareKit):
            calculate_geometry(node, params)


def test_finished_dimensions_and_weight_limits_are_inclusive(demo_60_params: SystemParams) -> None:
    kit = next(k for k in demo_60_params.available_hardware_kits if k.sku == "KIT-SLIDING")
    exact_kit = kit.model_copy(update={
        "min_leaf_width_mm": D("960"), "max_leaf_width_mm": D("960"),
        "min_leaf_height_mm": D("1950"), "max_leaf_height_mm": D("1950"),
        "max_leaf_weight_kg": D("48.8868"),
    })
    params = demo_60_params.model_copy(update={"available_hardware_kits": [exact_kit]})
    assert len(calculate_geometry(core_node("G5"), params).hardware_items) == 2
    with pytest.raises(NoCompatibleHardwareKit):
        calculate_geometry(core_node("G5"), params.model_copy(update={"available_hardware_kits": []}))


def test_capacity_uses_exact_mass_before_rounding(demo_60_params: SystemParams) -> None:
    kit = next(k for k in demo_60_params.available_hardware_kits if k.sku == "KIT-AWNING-16")
    params = demo_60_params.model_copy(update={"available_hardware_kits": [
        kit.model_copy(update={"max_leaf_weight_kg": D("23.96")}),
    ]})
    # G6 displays 23.96 but weighs exactly 23.96192, which exceeds this capacity.
    with pytest.raises(NoCompatibleHardwareKit):
        calculate_geometry(core_node("G6"), params)


def test_each_candidate_contributes_its_own_hardware_mass(demo_60_params: SystemParams) -> None:
    kit = next(k for k in demo_60_params.available_hardware_kits if k.sku == "KIT-AWNING-16")
    heavy = kit.model_copy(update={"sku": "HEAVY", "weight_kg": D("24.00")})
    params = demo_60_params.model_copy(update={"available_hardware_kits": [heavy, kit]})
    assert calculate_geometry(core_node("G6"), params).hardware_items[0].kit_sku == kit.sku


@pytest.mark.parametrize("profile_missing,steel_missing", [(False, False), (True, False), (False, True), (True, True)])
def test_article_weights_precede_individual_fallbacks(
    demo_60_params: SystemParams, g3_node: ParametricNode,
    profile_missing: bool, steel_missing: bool,
) -> None:
    result = calculate_geometry(g3_node, demo_60_params)
    articles = dict(demo_60_params.effective_profile_articles)
    articles[ProfileRole.SASH] = articles[ProfileRole.SASH].model_copy(update={
        "weight_kg_m": None if profile_missing else D("2.0000"),
        "steel_weight_kg_m": None if steel_missing else D("3.0000"),
    })
    params = demo_60_params.model_copy(update={"effective_profile_articles": articles})
    mass = base_leaf_weight(profile_cuts=result.profile_cuts, reinforcements=result.reinforcements,
                            infill_weight_kg=D("18.251520"), params=params)
    assert mass.pvc_weight_kg == D("5.81856" if profile_missing else "8.8160")
    assert mass.steel_weight_kg == D("7.97368" if steel_missing else "12.7920")
    assert mass.used_fallback is (profile_missing or steel_missing)


def test_persisted_and_missing_hardware_weights(demo_60_params: SystemParams) -> None:
    base = ExactLeafWeight(D("5"), D("7"), D("18"))
    kit = demo_60_params.available_hardware_kits[0]
    persisted = with_hardware_weight(base, kit, demo_60_params)
    fallback = with_hardware_weight(base, kit.model_copy(update={"weight_kg": None}), demo_60_params)
    assert persisted.hardware_weight_kg == D("2.50") and not persisted.used_fallback
    assert fallback.hardware_weight_kg == D("2.75") and fallback.used_fallback
    cap_kit = kit.model_copy(update={"max_leaf_weight_kg": D("32.60"), "weight_kg": None})
    with pytest.raises(NoCompatibleHardwareKit):
        resolve_hardware_kit(opening=BayOpeningType.TURN_LEFT, width_mm=D("800"), height_mm=D("1200"),
                             base_weight=base, params=demo_60_params.model_copy(update={"available_hardware_kits": [cap_kit]}))


def test_missing_panel_and_non_pvc_authorities_fail_closed(
    demo_60_params: SystemParams, g3_node: ParametricNode,
) -> None:
    panels = {sku: p.model_copy(update={"weight_kg_m2": None}) for sku, p in demo_60_params.available_panel_rules.items()}
    with pytest.raises(MissingWeightAuthority, match="panel"):
        calculate_geometry(core_node("G7"), demo_60_params.model_copy(update={"available_panel_rules": panels}))
    with pytest.raises(ValueError, match="requires panel_article_sku"):
        calculate_geometry(core_node("G7").model_copy(update={"panel_article_sku": None}), demo_60_params)
    result = calculate_geometry(g3_node, demo_60_params)
    articles = dict(demo_60_params.effective_profile_articles)
    articles[ProfileRole.SASH] = articles[ProfileRole.SASH].model_copy(update={"weight_kg_m": None, "material": MaterialType.ALUMINIUM})
    with pytest.raises(MissingWeightAuthority, match="non-PVC"):
        base_leaf_weight(profile_cuts=result.profile_cuts, reinforcements=result.reinforcements,
                         infill_weight_kg=D("18.251520"), params=demo_60_params.model_copy(update={"effective_profile_articles": articles}))


def test_total_rounds_once_half_up_and_excludes_static_bom(demo_60_params: SystemParams) -> None:
    exact = ExactLeafWeight(D("1.004"), D("2.004"), D("3.004"), D("4.003"))
    public = exact.public_result("test", None)
    assert public.total_weight_kg == D("10.02")
    assert public.pvc_weight_kg + public.steel_weight_kg + public.infill_weight_kg + public.hardware_weight_kg == D("10.00")
    baseline = calculate_geometry(core_node("G7"), demo_60_params)
    articles = {role: article.model_copy(update={"weight_kg_m": D("9999")})
                if role is not ProfileRole.SASH else article
                for role, article in demo_60_params.effective_profile_articles.items()}
    beads = {t: rule.model_copy(update={"bead_article": rule.bead_article.model_copy(update={"weight_kg_m": D("9999")})})
             for t, rule in demo_60_params.glazing_bead_rules.items()}
    changed = calculate_geometry(core_node("G7"), demo_60_params.model_copy(update={"effective_profile_articles": articles, "glazing_bead_rules": beads}))
    assert changed.leaf_weights == baseline.leaf_weights


@pytest.mark.parametrize("field", ["sliding_glazing_deduction_width_mm", "sliding_glazing_deduction_height_mm", "door_leaf_side_clearance_mm"])
def test_missing_geometry_authority_is_rejected(demo_60_params: SystemParams, field: str) -> None:
    values = demo_60_params.model_dump()
    del values[field]
    with pytest.raises(ValidationError, match=field):
        SystemParams.model_validate(values)
