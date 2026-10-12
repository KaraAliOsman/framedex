"""Physical motion, backward-compatible transport and exact new typologies."""

from decimal import Decimal as D
from pathlib import Path
import json

import pytest

from dekopen_engine.models import BayOpeningType as B, HingeSide as H, OpeningUse as U, ProfileRole
from dekopen_engine.openings import (opening_from_legacy, legacy_from_opening,
    OpeningCapabilityError, handle_fact, resolve_capability)
from dekopen_engine.geometry import calculate_geometry, compute_geometry
from dekopen_engine.snapshot import result_payload
from dekopen_engine.manufacturing import handle_rules_for_leaf
from engine.tests.opening_cases import opening_cases, opening_params, opening_node, typologies
from engine.tests.catalog import demo_60_params
from engine.tests.test_gold_cases_catalog_families import node


def test_new_typologies_match_reviewed_exact_golden() -> None:
    frozen = json.loads(Path(__file__).with_name("golden_openings.json").read_text(encoding="utf-8"))
    assert opening_cases() == frozen
    assert len(frozen) == 21
    for name, value in frozen.items():
        if name == "FIXED-FRAME":
            assert value["leaf_weights"] == []
        else:
            assert value["leaf_weights"] and all(leaf["total_weight_kg"] is not None for leaf in value["leaf_weights"])
        if name.startswith(("FRENCH-", "DOUBLE-DOOR-")):
            assert len(value["leaf_weights"]) == len(value["hardware_items"]) == 2
            assert sum(leaf["handle"] is not None for leaf in value["opening_leaves"]) == 1
            passive = next(leaf for leaf in value["opening_leaves"] if leaf["opening"]["leaf_role"] == "PASSIVE")
            inverse = [cut for cut in value["profile_cuts"] if cut["role"] == "INVERSOR"]
            assert len(inverse) == 1 and inverse[0]["leaf_id"] == passive["leaf_id"]
            kit = next(kit for kit in value["hardware_items"] if kit["leaf_id"] == passive["leaf_id"])
            assert all(component["category"] != "HANDLE" for component in kit["contents"])


@pytest.mark.parametrize("kind", list(B))
def test_total_legacy_round_trip_keeps_cardinality_and_unknown_doors(kind: B) -> None:
    opening = opening_from_legacy(kind)
    use = U.DOOR if kind in (B.DOOR_ENTRY, B.DOOR_DOUBLE) else U.WINDOW
    assert legacy_from_opening(opening, use=use, legacy_hint=kind) is kind
    if use is U.DOOR:
        assert opening.hinge_side is H.NONE


@pytest.mark.parametrize("kind", [kind for kind in B if kind not in (B.DOOR_DOUBLE, B.SLIDING)])
def test_migrated_legacy_bom_cuts_and_price_inputs_are_identical(kind: B) -> None:
    old = node(kind, "1800" if kind.value.startswith("SLIDING") else "1000",
               "2200" if kind is B.DOOR_ENTRY else "900" if kind is B.AWNING else "1400")
    if kind is B.DOOR_ENTRY:
        old = old.model_copy(update={"panel_article_sku": "PANEL-SANDWICH-DEMO-24"})
    params = demo_60_params()
    migrated = old.model_copy(update={"opening": opening_from_legacy(kind),
                                     "opening_use": U.DOOR if kind is B.DOOR_ENTRY else U.WINDOW})
    assert result_payload(calculate_geometry(old, params)) == result_payload(calculate_geometry(migrated, params))


def test_outward_refusal_names_catalog_systems_that_admit_it() -> None:
    params = opening_params("DEMO_60")
    admitted = opening_params("DEMO_ALU_PRACTICABLE")
    params = params.model_copy(update={"compatible_opening_systems": (("Aluminio practicable DEMO", admitted.opening_capabilities),)})
    with pytest.raises(OpeningCapabilityError, match="Aluminio practicable DEMO"):
        calculate_geometry(opening_node("TURN", "LEFT", "OUTWARD"), params)


def test_passive_and_fixed_sash_do_not_request_handles_in_manufacturing() -> None:
    for name in ("FRENCH-RIGHT", "FIXED-SASH", "TILT", "TOP-HUNG"):
        code, tree = typologies()[name]
        computation = compute_geometry(tree, opening_params(code))
        assert computation.manufacturing_trace is not None
        for leaf in computation.manufacturing_trace.leaves:
            rules = handle_rules_for_leaf([], leaf)
            assert len(rules) == (0 if leaf.opening_handle is None else 1)
            if rules:
                assert leaf.opening_handle is not None
                assert rules[0].host_member_side.value == leaf.opening_handle.side.value


def test_handle_height_comes_from_source_and_rejects_out_of_range() -> None:
    params = opening_params("DEMO_PUERTA_70")
    tree = opening_node("TURN", "LEFT", use="DOOR", height="2200")
    capability = resolve_capability(tree, params)
    assert capability is not None
    assert tree.opening is not None
    point = handle_fact(tree.opening, capability, width_mm=D("900"), height_mm=D("2100"))
    assert point is not None and point.side is H.RIGHT and point.y_mm == D("1100")
    with pytest.raises(ValueError, match="fuera del rango"):
        handle_fact(tree.opening, capability, width_mm=D("900"), height_mm=D("2100"), requested_height_mm=D("2099"))


@pytest.mark.parametrize("reference,expected_y", [
    ("CENTER", "1050.005"), ("LEAF_BOTTOM", "1000.005"), ("LEAF_TOP", "1100.005")])
def test_handle_reference_and_override_preserve_source_precision(reference: str, expected_y: str) -> None:
    tree = opening_node("TURN", "RIGHT", use="DOOR")
    capability = resolve_capability(tree, opening_params("DEMO_PUERTA_70"))
    assert tree.opening is not None and capability is not None and capability.handle_rule is not None
    capability = capability.model_copy(update={"handle_rule": capability.handle_rule.model_copy(update={
        "vertical_reference": reference, "default_height_mm": D("1100.005")})})
    point = handle_fact(tree.opening, capability, width_mm=D("900"), height_mm=D("2100.01"))
    assert point is not None and point.side is H.LEFT and point.y_mm == D(expected_y)
    assert point.height_from_bottom_mm + point.y_mm == D("2100.01")
    explicit = handle_fact(tree.opening, capability, width_mm=D("900"), height_mm=D("2100.01"), requested_height_mm=D("1050.005"))
    assert explicit is not None and explicit.y_mm == D("1050.005")
    assert capability.handle_rule is not None
    assert explicit.source == capability.handle_rule.source


@pytest.mark.parametrize("movement,hinge,side", [("TILT", "BOTTOM", H.TOP), ("TOP_HUNG", "TOP", H.BOTTOM)])
def test_vertical_hinges_fix_the_handle_at_the_sourced_closing_edge(movement: str, hinge: str, side: H) -> None:
    tree = opening_node(movement, hinge, "OUTWARD" if movement == "TOP_HUNG" else "INWARD")
    capability = resolve_capability(tree, opening_params("DEMO_ALU_PRACTICABLE" if movement == "TOP_HUNG" else "DEMO_60"))
    assert tree.opening is not None and capability is not None and capability.handle_rule is not None
    point = handle_fact(tree.opening, capability, width_mm=D("800"), height_mm=D("900"))
    assert point is not None and point.side is side and point.x_mm == D("400")
    assert min(point.y_mm, point.height_from_bottom_mm) == capability.handle_rule.closing_edge_offset_mm
    assert point.minimum_height_from_bottom_mm == point.maximum_height_from_bottom_mm
    with pytest.raises(ValueError, match="borde de cierre"):
        handle_fact(tree.opening, capability, width_mm=D("800"), height_mm=D("900"), requested_height_mm=D("450"))


def test_paired_half_cent_precision_is_preserved_and_old_bytes_are_untouched() -> None:
    tree = opening_node("TURN", "RIGHT", role="ACTIVE", paired=True, width="1600.01")
    payload = result_payload(calculate_geometry(tree, opening_params("DEMO_60")))
    leaves = payload["opening_leaves"]
    assert isinstance(leaves, list)
    first = leaves[0]
    assert isinstance(first, dict) and isinstance(first["width_mm"], str)
    assert first["width_mm"].endswith("005")
    assert "opening_leaves" not in result_payload(calculate_geometry(node(B.FIXED), demo_60_params()))


def test_additive_seed_does_not_change_v2_authorities() -> None:
    from scripts.generate_demo_catalog import generated_sql, MIGRATION
    from scripts.generate_demo_openings import opening_sql, MIGRATION as NEW_SEED
    assert generated_sql() == MIGRATION.read_text(encoding="utf-8")
    assert opening_sql() == NEW_SEED.read_text(encoding="utf-8")
    assert ProfileRole.INVERSOR in opening_params("DEMO_60").effective_profile_articles


def test_purchase_counts_consolidate_cut_groups_and_keep_each_leaf() -> None:
    from dekopen_engine.purchasing import fitting_selections_v1
    for code, tree in typologies().values():
        result = calculate_geometry(tree, opening_params(code))
        selections = fitting_selections_v1(result.fittings, 2)
        assert sum(piece.quantity for piece in selections) == 2 * sum(piece.qty for piece in result.fittings)
        identities = [(p.repetition_index, p.bay_id, p.leaf_id, p.technical_sku, p.kind) for p in selections]
        assert len(identities) == len(set(identities))
        assert {p.leaf_id for p in selections} == {p.leaf_id for p in result.fittings}


@pytest.mark.parametrize("name", typologies())
def test_new_typology_projects_complete_manufacturing_with_seed_authority(name: str) -> None:
    from backend.catalogs.demo_openings import opening_manifest
    from scripts.generate_demo_catalog import reinforcement_rules
    from dekopen_engine.manufacturing import (
        HandleIntentV1, ReinforcementCutPolicyV1, VerticalReference, project_manufacturing_facts_v1)
    from engine.tests.test_manufacturing import placement, handles
    code, tree = typologies()[name]
    params = opening_params(code)
    computation = compute_geometry(tree, params)
    trace = computation.manufacturing_trace
    assert trace is not None
    record = next(row for row in opening_manifest() if row["code"] == code)
    policy = ReinforcementCutPolicyV1.model_validate_json(json.dumps({
        "policy_id": code + "_REFUERZO_DEMO_V3", "version": 3, "rules": reinforcement_rules(record, 3)}))
    intents = [HandleIntentV1(bay_id=leaf.bay_id, leaf_id=leaf.leaf_id, handle_domain_slot="PRIMARY",
        requested_height_mm=leaf.opening_handle.height_from_bottom_mm, vertical_reference=VerticalReference.LEAF_BOTTOM)
        for leaf in trace.leaves if leaf.opening_handle is not None]
    facts = project_manufacturing_facts_v1(trace=trace, position_id="d0300000-0000-4000-8000-000000000001",
        position_index=1, repetition_index=1, placement_policy=placement(), handle_policy=handles(),
        reinforcement_policy=policy, handle_intents=intents,
        resolved_reinforcement_skus={a.sku: a.reinforcement_sku for a in params.effective_profile_articles.values()
            if a.reinforcement_sku is not None})
    assert len(facts.handles) == len(intents)
    assert all(leaf.opening is not None for leaf in facts.leaves)
