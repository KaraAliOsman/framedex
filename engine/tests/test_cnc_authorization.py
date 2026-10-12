"""P14: physical unknowns cannot authorize a newly generated interchange."""
from copy import deepcopy
from decimal import Decimal
from typing import Any, cast

import pytest

from dekopen_engine.cnc_authorization import authorize_member_operations, member_preview, program_diff, section_fingerprint
from dekopen_engine.operations import (ClampZone, CoordinateSystem, MachineProfile, ManufacturingOperation,
    MemberFace, NeutralOpsPostProcessor, OperationKind, OperationValidation, Tool, ToolKind, member_program)

D = Decimal
SECTION: dict[str, Any] = {"polygon": [{"x_mm": "0", "y_mm": "0"}, {"x_mm": "60", "y_mm": "0"}, {"x_mm": "60", "y_mm": "70"}, {"x_mm": "0", "y_mm": "70"}],
           "orientation_declared": True, "origin_declared": True, "authority_source": "Test declared section"}


def machining_fixture() -> tuple[list[ManufacturingOperation], MachineProfile, dict[str, Any]]:
    ops = [ManufacturingOperation(operation_id=f"end-{end}", kind=OperationKind.END_MACHINING,
        host_kind="MEMBER", host="member", coordinate_system=CoordinateSystem.MEMBER_PLAN,
        u_mm=D(u), reference=reference, face=face, depth_mm=D("5"), tool_id="end_mill",
        basis="member_end_overlap")
        for end, u, reference, face in ((1, "0", "member_start", MemberFace.START_EDGE),
                                       (2, "1000", "member_end", MemberFace.END_EDGE))]
    machine = MachineProfile(machine_id="CNC-TEST", name="Test reviewed neutral target",
        coordinate_systems=[CoordinateSystem.MEMBER_PLAN], supported_kinds=[OperationKind.END_MACHINING],
        supported_faces=[MemberFace.START_EDGE, MemberFace.END_EDGE], max_member_length_mm=D("6000"),
        safe_margin_mm=D("10"), clamp_zones=[ClampZone(start_mm=D("450"), end_mm=D("550"), label="Clamp A")],
        postprocessor_id="neutral-ops-v1", postprocessor_version="1",
        tools=[Tool(tool_id="end_mill", kind=ToolKind.END_MILL, name="Test end mill",
                    diameter_mm=D("10"), working_length_mm=D("30"), max_depth_mm=D("20"),
                    compatible_kinds=[OperationKind.END_MACHINING])])
    authority = {"supported_kinds":["END_MACHINING"], "supported_faces":["START_EDGE","END_EDGE"],
                 "coordinate_systems":["MEMBER_PLAN"], "axes":["X"], "clamps_declared":True,
                 "authority_source":"Test fixture · not manufacturer evidence", "machine_type":"END_MILLER",
                 "tool_sources":{"end_mill":"Tool declaration"}, "profile_setups":[
                     {"profile_sku":"TEST-PROFILE", "section_fingerprint":section_fingerprint(SECTION),
                      "loading_orientation":"EXTERIOR_UP","axial_datum":"MEMBER_START","source":"Loading fixture"}]}
    return ops, machine, authority


def validations(ops: list[ManufacturingOperation], machine: MachineProfile,
                authority: dict[str, Any], section: dict[str, Any] = SECTION) -> list[OperationValidation]:
    return authorize_member_operations(ops,machine,authority=authority,member_length_mm=D("1000"),
                                       section=section,member_label="P01-U01-M01",profile_sku="TEST-PROFILE")


def test_end_work_is_at_the_end_from_start_datum_and_section_plane_is_explicit() -> None:
    ops,machine,authority = machining_fixture()
    assert all(v.level == "PASS" for v in validations(ops,machine,authority))
    preview = member_preview(ops=ops,length_mm=D("1000"),section=SECTION)
    assert preview["marks"] == [
        {"operation_id":"end-1","x_mm":"0","face":"START_EDGE","section_coverage":"END_PLANE"},
        {"operation_id":"end-2","x_mm":"1000","face":"END_EDGE","section_coverage":"END_PLANE"}]
    assert member_preview(ops=ops,length_mm=None,section=None)["length_mm"] is None


@pytest.mark.parametrize("field",["supported_kinds","supported_faces","coordinate_systems","axes","authority_source","machine_type","profile_setups","tool_sources","clamps_declared"])
def test_every_missing_physical_declaration_blocks(field: str) -> None:
    ops,machine,authority = machining_fixture()
    authority.pop(field)
    assert any(v.level == "BLOCK" for v in validations(ops,machine,authority))


def test_drawing_orientation_is_never_a_loading_authority_and_changed_section_requires_review() -> None:
    ops,machine,authority = machining_fixture()
    authority["profile_setups"] = []
    assert any(v.code == "profile_setup_undeclared" for v in validations(ops,machine,authority))
    ops,machine,authority = machining_fixture()
    changed = deepcopy(SECTION)
    changed["polygon"][1]["x_mm"] = "65"
    assert any(v.code == "profile_setup_undeclared" for v in validations(ops,machine,authority,changed))


def test_missing_tool_and_explicit_empty_capability_are_blocked() -> None:
    ops,machine,authority = machining_fixture()
    assert any(v.code == "no_compatible_tool" for v in validations(ops,machine.model_copy(update={"tools":[]}),authority))
    assert any(v.code == "unsupported_kind" for v in validations(ops,machine.model_copy(update={"supported_kinds":[]}),authority))


def test_end_work_checks_the_whole_penetration_span_against_clamps() -> None:
    ops,machine,authority = machining_fixture()
    machine = machine.model_copy(update={"clamp_zones":[ClampZone(start_mm=D("996"),end_mm=D("999"))]})
    result = validations(ops,machine,authority)
    assert any(v.operation_id == "end-2" and v.code == "clamp_conflict" and v.level == "BLOCK" for v in result)


def test_plan_xy_cannot_be_used_as_transverse_tool_coordinates_and_unknown_depth_blocks() -> None:
    ops,machine,authority = machining_fixture()
    op = ops[0].model_copy(update={"face":MemberFace.INSIDE_FACE, "x_mm":D("60"),"y_mm":D("500"),"depth_mm":None})
    result = validations([op],machine,authority)
    assert {"transverse_coordinate_undeclared","depth_undeclared"} <= {v.code for v in result}


def test_same_reviewed_input_has_identical_files_and_changed_depth_has_a_physical_diff() -> None:
    ops,machine,authority = machining_fixture()
    def document(items: list[ManufacturingOperation]) -> dict[str, Any]:
        d = member_program(items,member_id="member",member_label="P01-U01-M01",machine=machine,
                           identity={"plan_seed":"42"},validations=validations(items,machine,authority))
        d["preview"] = member_preview(ops=items,length_mm=D("1000"),section=SECTION)
        return d
    first = document(ops)
    assert NeutralOpsPostProcessor().render(first) == NeutralOpsPostProcessor().render(document(ops))
    after = document([ops[0],ops[1].model_copy(update={"depth_mm":D("6")})])
    assert first["fingerprint"] != after["fingerprint"]
    changed = cast(list[dict[str, Any]], program_diff(first,after)["changed"])
    assert changed[0]["after"]["depth_mm"] == "6"
