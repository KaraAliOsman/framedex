"""CNC workspace service — authority validation, machine profiles, staleness."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import pytest

from documents.repository import DocumentaryError
from production import cnc


def test_create_tool_rejects_unknown_kind() -> None:
    with pytest.raises(DocumentaryError) as exc:
        cnc.create_tool(
            org_id=uuid4(),
            actor_id=uuid4(),
            data={"code": "T-1", "name": "Fresa", "kind": "LASER"},
        )
    assert exc.value.code == "cnc_tool_invalid"


def test_create_tool_rejects_unknown_compatible_kind() -> None:
    with pytest.raises(DocumentaryError) as exc:
        cnc.create_tool(
            org_id=uuid4(),
            actor_id=uuid4(),
            data={
                "code": "T-1",
                "name": "Broca",
                "kind": "DRILL_BIT",
                "compatible_kinds": ["HANDLE_PREP", "TELEPORT"],
            },
        )
    assert exc.value.code == "cnc_tool_kind_invalid"


def test_clamp_zones_validate_shape() -> None:
    with pytest.raises(DocumentaryError) as exc:
        cnc._clamp_zones([{"start_mm": "500", "end_mm": "100"}])
    assert exc.value.code == "cnc_clamp_zones_invalid"
    zones = cnc._clamp_zones(
        [{"start_mm": "500", "end_mm": "1100", "label": "Mordaza B"}]
    )
    assert zones == [
        {"start_mm": "500", "end_mm": "1100", "label": "Mordaza B"}
    ]


def test_tool_ids_must_exist_in_org() -> None:
    missing = str(uuid4())
    with patch(
        "production.cnc.rows", return_value=[]
    ), pytest.raises(DocumentaryError) as exc:
        cnc._tool_ids([missing], org_id=uuid4())
    assert exc.value.code == "cnc_tool_not_in_org"


def test_machine_profile_maps_declared_authority() -> None:
    tool_id = uuid4()
    tools_by_id = {
        str(tool_id): {
            "id": tool_id,
            "code": "DR-8",
            "name": "Broca 8",
            "kind": "DRILL_BIT",
            "diameter_mm": Decimal("8"),
            "working_length_mm": Decimal("40"),
            "max_depth_mm": Decimal("30"),
            "compatible_kinds": ["DRILL", "HANDLE_PREP"],
            "active": True,
        }
    }
    machine_row = {
        "id": uuid4(),
        "code": "SBZ-01",
        "name": "Centro",
        "manufacturer": "Elumatec",
        "model": "SBZ 122",
        "controller_family": "NEUTRAL",
        "coordinate_systems": ["MEMBER_PLAN"],
        "supported_kinds": ["DRILL", "HANDLE_PREP"],
        "supported_faces": ["INSIDE_FACE", "OUTSIDE_FACE"],
        "max_member_length_mm": Decimal("3500"),
        "safe_margin_mm": Decimal("25"),
        "clamp_zones": [
            {"start_mm": "500", "end_mm": "900", "label": "Mordaza A"}
        ],
        "tool_ids": [str(tool_id)],
        "postprocessor_id": "neutral-ops-v1",
        "postprocessor_version": "1",
        "units": "mm",
        "encoding": "utf-8",
        "active": True,
    }
    profile = cnc._machine_profile(machine_row, tools_by_id)
    assert profile.machine_id == "SBZ-01"
    assert len(profile.tools) == 1
    tool = profile.tools[0]
    assert tool.tool_id == "DR-8"
    assert tool.max_depth_mm == Decimal("30")
    assert profile.max_member_length_mm == Decimal("3500")
    assert profile.clamp_zones[0].label == "Mordaza A"
    assert profile.safe_margin_mm == Decimal("25")


def test_machine_profile_skips_phantom_magazine_entries() -> None:
    """A tool row that vanished (deleted) cannot become an invented tool —
    it is dropped from the magazine and validation reports the blocker."""
    machine_row = {
        "id": uuid4(),
        "code": "SBZ-01",
        "name": "Centro",
        "manufacturer": "",
        "model": "",
        "controller_family": "NEUTRAL",
        "coordinate_systems": ["MEMBER_PLAN"],
        "supported_kinds": None,
        "supported_faces": None,
        "max_member_length_mm": None,
        "safe_margin_mm": None,
        "clamp_zones": [],
        "tool_ids": [str(uuid4())],
        "postprocessor_id": "neutral-ops-v1",
        "postprocessor_version": "1",
        "units": "mm",
        "encoding": "utf-8",
        "active": True,
    }
    profile = cnc._machine_profile(machine_row, {})
    assert profile.tools == []


def test_program_no_uses_physical_codes() -> None:
    no = cnc._program_no(
        order_code="OT-0001", member_label="M-07",
        machine_code="SBZ-01", seq=2,
    )
    assert no == "OT-0001-M07-SBZ-01-02"


def test_retired_tools_do_not_resolve_into_a_magazine():
    tool_id = str(uuid4())
    row = {"code":"CNC", "name":"Test", "tool_ids":[tool_id], "controller_family":"NEUTRAL",
           "coordinate_systems":[], "postprocessor_id":"", "postprocessor_version":"", "units":"mm","encoding":"utf-8"}
    assert cnc._machine_profile(row,{tool_id:{"active":False,"code":"end_mill"}}).tools == []


def test_declared_drains_are_scoped_per_unit_even_when_other_work_is_emitted():
    from production.cnc_coverage import declared_gaps
    from engine.tests.test_operations import _unit
    first, second = _unit(), _unit(repetition_index=2)
    snapshot = {"positions":[{"id":"pos-1","workshop_annotations":[
        {"bay_id":"B1","bottom_drain_holes_mm":["100","500","900"]}]}]}
    gaps = declared_gaps(snapshot,None,[first,second],[],[])
    assert len(gaps) == 2
    assert [g["unit_index"] for g in gaps] == [1,2]
    assert all(g["reason_code"] == "emitter_not_implemented" for g in gaps)


def test_module_scope_matches_annotations_once_without_changing_physical_identity():
    from production.cnc_coverage import declared_gaps
    from production.service import _operations_fact_units
    from engine.tests.test_operations import _unit
    base = _unit()
    snapshot = {"manufacturing": [{**base.model_dump(mode="json"), "module_id": scope}
                                  for scope in ("left", "right")],
                "positions": [{"id": "pos-1", "workshop_annotations": [
                    {"bay_id": "left|B1", "bottom_drain_holes_mm": ["100"]},
                    {"bay_id": "right|B1", "bottom_drain_holes_mm": ["200"]}]}]}
    units = _operations_fact_units(snapshot, "pos-1")
    gaps = declared_gaps(snapshot, None, units, [], [])
    assert len(gaps) == 2
    assert [g["bay_id"] for g in gaps] == ["left|B1", "right|B1"]
    assert [m.member_id for m in units[0].members] == [m.member_id for m in base.members]
    assert "module_id" not in base.model_dump()


def test_profile_setups_need_exact_sealed_section_loading_datum_and_source():
    with pytest.raises(DocumentaryError,match="cnc_profile_setup_invalid"):
        cnc._profile_setups([{"profile_sku":"P","loading_orientation":"EXTERIOR_UP"}])
    data = {"profile_sku":"P","loading_orientation":"EXTERIOR_UP","axial_datum":"MEMBER_START",
            "section_fingerprint":"a"*64,"source":"Plant review"}
    assert cnc._profile_setups([data]) == [data]
    with pytest.raises(DocumentaryError,match="cnc_profile_setup_invalid"):
        cnc._profile_setups([data,data])


@pytest.mark.parametrize("number",["NaN","Infinity","-Infinity"])
def test_nonfinite_machine_numbers_are_rejected(number):
    with pytest.raises(DocumentaryError,match="cnc_numeric_invalid"):
        cnc._dec(number)
