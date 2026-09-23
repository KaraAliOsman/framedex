from decimal import Decimal

import pytest
from pydantic import ValidationError

from dekopen_engine import ParametricNode, SystemParams, calculate_geometry
from dekopen_engine.geometry import compute_geometry
from dekopen_engine.technical_facts import GeometryComputation
from dekopen_engine.manufacturing import (
    HandleIntentV1,
    HandleRequirementPolicyV1,
    ManufacturingAuthorityError,
    ManufacturingFactsV1,
    ManufacturingPlacementPolicyV1,
    ReinforcementCutPolicyV1,
    VerticalReference,
    project_coupling_facts_v1,
    project_manufacturing_facts_v1,
)
from dekopen_engine.manufacturing_trace import MemberSide, TracePointV1
from dekopen_engine.models import (
    BayOpeningType,
    MaterialType,
    ProfileCut,
    ProfileRole,
    ReinforcementPiece,
)
from engine.tests.test_shot06_core import core_node

D = Decimal


def placement(**changes: object) -> ManufacturingPlacementPolicyV1:
    value: dict[str, object] = {
        "policy_id": "PLACEMENT-DEMO-V1",
        "version": 1,
        "sliding_leaf_offsets": {
            "L1": {"x_mm": D("0"), "y_mm": D("0")},
            "L2": {"x_mm": D("500"), "y_mm": D("0")},
        },
        "sliding_infill_offsets": {
            "L1": {"x_mm": D("70"), "y_mm": D("70")},
            "L2": {"x_mm": D("70"), "y_mm": D("70")},
        },
        "bead_offsets": {
            side: {"x_mm": D("0"), "y_mm": D("0")}
            for side in (MemberSide.TOP, MemberSide.RIGHT, MemberSide.BOTTOM, MemberSide.LEFT)
        },
    }
    value.update(changes)
    return ManufacturingPlacementPolicyV1.model_validate(value)


def handles(*opening_types: str) -> HandleRequirementPolicyV1:
    return HandleRequirementPolicyV1.model_validate({
        "policy_id": "HANDLE-DEMO-V1",
        "version": 1,
        "slots": [
            {
                "opening_type": BayOpeningType(opening),
                "handle_domain_slot": "PRIMARY",
                "host_member_side": MemberSide.RIGHT,
                "horizontal_offset_mm": D("-10.00"),
                "permitted_vertical_references": [VerticalReference.LEAF_TOP],
                "mounting_min_from_leaf_top_mm": D("100.00"),
                "mounting_max_from_leaf_top_mm": D("1900.00"),
            }
            for opening in opening_types
        ],
    })


def steel(*pairs: tuple[ProfileRole, str, str]) -> ReinforcementCutPolicyV1:
    return ReinforcementCutPolicyV1.model_validate({
        "policy_id": "STEEL-DEMO-V1",
        "version": 1,
        "rules": [
            {
                "role": role,
                "profile_angle_left": D(left),
                "profile_angle_right": D(right),
                "reinforcement_angle_left": D("90.0"),
                "reinforcement_angle_right": D("90.0"),
                "compatible_with_existing_length": True,
            }
            for role, left, right in pairs
        ],
    })


def project(
    node: ParametricNode,
    params: SystemParams,
    *,
    repetition: int = 1,
    placement_policy: ManufacturingPlacementPolicyV1 | None = None,
    handle_policy: HandleRequirementPolicyV1 | None = None,
    legacy: bool = False,
    confirmed: bool = False,
) -> tuple[GeometryComputation, ManufacturingFactsV1]:
    computation = compute_geometry(node, params)
    assert computation.manufacturing_trace is not None
    openings = sorted({leaf.opening_type.value for leaf in computation.manufacturing_trace.leaves})
    intents = [
        HandleIntentV1(
            bay_id=leaf.bay_id,
            leaf_id=leaf.leaf_id,
            handle_domain_slot="PRIMARY",
            requested_height_mm=D("300.00"),
            vertical_reference=VerticalReference.LEAF_TOP,
        )
        for leaf in computation.manufacturing_trace.leaves
    ]
    roles_and_angles = sorted({
        (member.role, str(member.angle_left), str(member.angle_right))
        for member in computation.manufacturing_trace.members
        if member.reinforcement_required
    }, key=lambda item: (item[0].value, item[1], item[2]))
    facts = project_manufacturing_facts_v1(
        trace=computation.manufacturing_trace,
        position_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        position_index=2,
        repetition_index=repetition,
        placement_policy=placement_policy or placement(),
        handle_policy=handle_policy or handles(*openings),
        reinforcement_policy=steel(*roles_and_angles),
        handle_intents=intents,
        resolved_reinforcement_skus={
            member.workshop_sku: f"STEEL-{member.workshop_sku}"
            for member in computation.manufacturing_trace.members
            if member.reinforcement_required
        },
        legacy_handle_height_present=legacy,
        legacy_handle_migration_confirmed=confirmed,
    )
    return computation, facts


def test_geometry_emits_physical_trace_without_changing_engine_result(
    demo_60_params: SystemParams, g4_node: ParametricNode,
) -> None:
    computation, facts = project(g4_node, demo_60_params)
    assert computation.result == calculate_geometry(g4_node, demo_60_params)
    assert computation.manufacturing_trace is not None
    assert len(facts.members) == sum(cut.qty for cut in computation.result.profile_cuts)
    assert len(facts.reinforcements) == sum(
        piece.qty for piece in computation.result.reinforcements
    )
    assert len({member.member_id for member in facts.members}) == len(facts.members)
    mullion = next(member for member in facts.members if member.identity.role is ProfileRole.MULLION_V)
    assert mullion.identity.topology_path == "root/g4"
    assert (mullion.start.x_mm, mullion.end.x_mm) == (D("900"), D("900"))
    assert any(relation.relationship == "REINFORCES" for relation in facts.relationships)
    assert any(relation.relationship == "RETAINS_INFILL" for relation in facts.relationships)


def test_handle_policy_resolves_member_and_exact_point_without_human_x(
    demo_60_params: SystemParams,
) -> None:
    _, facts = project(core_node("G6"), demo_60_params)
    assert len(facts.handles) == 1
    handle = facts.handles[0]
    host = next(member for member in facts.members if member.member_id == handle.host_member_id)
    assert host.identity.physical_member_slot == "RIGHT"
    assert (handle.point.x_mm, handle.point.y_mm) == (D("1138.00"), D("352.00"))
    with pytest.raises(ValidationError):
        HandleIntentV1.model_validate({
            "bay_id": "G6",
            "handle_domain_slot": "PRIMARY",
            "requested_height_mm": D("300.00"),
            "vertical_reference": VerticalReference.LEAF_TOP,
            "manufacturing_x_mm": D("10.00"),
        })


def test_repetition_changes_identity_but_not_authoritative_dimensions(
    demo_60_params: SystemParams,
) -> None:
    _, first = project(core_node("G6"), demo_60_params, repetition=1)
    _, second = project(core_node("G6"), demo_60_params, repetition=2)
    assert [item.cut_length_mm for item in first.members] == [
        item.cut_length_mm for item in second.members
    ]
    assert {item.member_id for item in first.members}.isdisjoint(
        {item.member_id for item in second.members}
    )
    assert first.model_dump() == project(core_node("G6"), demo_60_params, repetition=1)[1].model_dump()


def test_sliding_and_steel_authority_fail_closed(demo_60_params: SystemParams) -> None:
    missing_sliding = placement(sliding_leaf_offsets={})
    with pytest.raises(ManufacturingAuthorityError, match="sliding leaf"):
        project(core_node("G5"), demo_60_params, placement_policy=missing_sliding)
    computation = compute_geometry(core_node("G6"), demo_60_params)
    assert computation.manufacturing_trace is not None
    with pytest.raises(ManufacturingAuthorityError, match="cut authority"):
        project_manufacturing_facts_v1(
            trace=computation.manufacturing_trace,
            position_id="P",
            position_index=1,
            repetition_index=1,
            placement_policy=placement(),
            handle_policy=handles("AWNING"),
            reinforcement_policy=steel((ProfileRole.FRAME, "45.0", "45.0")),
            handle_intents=[HandleIntentV1(
                bay_id="G6", handle_domain_slot="PRIMARY", requested_height_mm=D("300"),
                vertical_reference=VerticalReference.LEAF_TOP,
            )],
            resolved_reinforcement_skus={"MARCO": "STEEL-MARCO", "HOJA": "STEEL-HOJA"},
        )


def test_overlapping_handle_rules_fail_closed(demo_60_params: SystemParams) -> None:
    rule: dict[str, object] = {
        "opening_type": BayOpeningType.SLIDING_2L,
        "handle_domain_slot": "PRIMARY",
        "host_member_side": MemberSide.RIGHT,
        "horizontal_offset_mm": D("-10.00"),
        "permitted_vertical_references": [VerticalReference.LEAF_TOP],
        "mounting_min_from_leaf_top_mm": D("100.00"),
        "mounting_max_from_leaf_top_mm": D("1900.00"),
    }
    wildcard_plus_specific = HandleRequirementPolicyV1.model_validate({
        "policy_id": "HANDLE-AMBIGUOUS-V1", "version": 1,
        "slots": [rule, {**rule, "leaf_slot": "L1"}],
    })
    with pytest.raises(ManufacturingAuthorityError, match="ambiguous"):
        project(core_node("G5"), demo_60_params, handle_policy=wildcard_plus_specific)
    duplicated = HandleRequirementPolicyV1.model_validate({
        "policy_id": "HANDLE-DUPLICATED-V1", "version": 1,
        "slots": [{**rule, "leaf_slot": "L1"}, {**rule, "leaf_slot": "L1"}],
    })
    with pytest.raises(ManufacturingAuthorityError, match="ambiguous"):
        project(core_node("G5"), demo_60_params, handle_policy=duplicated)


def test_legacy_handle_height_needs_explicit_confirmation(
    demo_60_params: SystemParams,
) -> None:
    with pytest.raises(ManufacturingAuthorityError, match="migration confirmation"):
        project(core_node("G6"), demo_60_params, legacy=True)
    _, facts = project(core_node("G6"), demo_60_params, legacy=True, confirmed=True)
    assert facts.handles[0].requested_height_mm == D("300.00")


def _coupler_cut(sku: str = "COPLE-60", bay_id: str = "c1") -> ProfileCut:
    return ProfileCut(
        sku=sku, role=ProfileRole.COUPLER, material=MaterialType.PVC,
        length_mm=D("1400.00"), angle_left=D("90.0"), angle_right=D("90.0"),
        qty=1, bay_id=bay_id,
    )


def _wedge(ax: str, ay: str, bx: str, by: str, cx: str, cy: str) -> list[TracePointV1]:
    return [
        TracePointV1(x_mm=D(ax), y_mm=D(ay)),
        TracePointV1(x_mm=D(bx), y_mm=D(by)),
        TracePointV1(x_mm=D(cx), y_mm=D(cy)),
    ]


def _coupling_facts(
    *,
    cuts: list[ProfileCut],
    reinforcements: list[ReinforcementPiece] | None = None,
    wedges: dict[str, list[TracePointV1]] | None = None,
    reinforcement_policy: ReinforcementCutPolicyV1 | None = None,
) -> ManufacturingFactsV1:
    return project_coupling_facts_v1(
        coupler_cuts=cuts,
        coupler_reinforcements=reinforcements or [],
        coupling_wedges=wedges or {},
        position_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        position_index=3,
        repetition_index=1,
        nominal_width_mm=D("2100.00"),
        nominal_height_mm=D("1400.00"),
        placement_policy=placement(),
        handle_policy=handles(),
        reinforcement_policy=reinforcement_policy
        or steel((ProfileRole.COUPLER, "90.0", "90.0")),
    )


def test_coupler_facts_carry_real_plan_coordinates() -> None:
    facts = _coupling_facts(
        cuts=[_coupler_cut("COPLE-60", "c1"), _coupler_cut("COPLE-90", "c2")],
        wedges={
            "c1": _wedge("700", "0", "700", "-65", "640", "-32"),
            "c2": _wedge("1328", "65", "1328", "0", "1390", "32"),
        },
    )
    by_slot = {member.identity.topology_path: member for member in facts.members}
    first, second = by_slot["coupling:c1"], by_slot["coupling:c2"]
    assert first.start == TracePointV1(x_mm=D("700"), y_mm=D("0"))
    assert first.end == TracePointV1(x_mm=D("670"), y_mm=D("-48.5"))
    assert second.start == TracePointV1(x_mm=D("1328"), y_mm=D("65"))
    assert second.end == TracePointV1(x_mm=D("1359"), y_mm=D("16"))
    assert first.member_id != second.member_id
    assert facts.module_id is None


def test_coupler_facts_fail_closed_without_plan_wedge() -> None:
    with pytest.raises(ManufacturingAuthorityError, match="plan wedge"):
        _coupling_facts(cuts=[_coupler_cut()], wedges={})


def test_coupler_steel_requires_coupler_cut_rule() -> None:
    steel_piece = ReinforcementPiece(
        parent_profile_sku="COPLE-60", reinforcement_sku="STEEL-COPLE",
        role=ProfileRole.COUPLER, length_mm=D("1385.00"), qty=1, bay_id="c1",
    )
    wedges = {"c1": _wedge("700", "0", "700", "-65", "640", "-32")}
    with pytest.raises(ManufacturingAuthorityError, match="authority"):
        _coupling_facts(
            cuts=[_coupler_cut()], reinforcements=[steel_piece], wedges=wedges,
            reinforcement_policy=steel((ProfileRole.FRAME, "45.0", "45.0")),
        )
    facts = _coupling_facts(
        cuts=[_coupler_cut()], reinforcements=[steel_piece], wedges=wedges,
    )
    reinforcement = facts.reinforcements[0]
    assert reinforcement.angle_left == D("90.0")
    assert reinforcement.angle_right == D("90.0")
    assert reinforcement.parent_member_id == facts.members[0].member_id
    assert reinforcement.policy_id == "STEEL-DEMO-V1"
