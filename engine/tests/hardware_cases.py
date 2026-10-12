"""Synthetic v4 cases exercise manufacturing counts, lengths, mass and prices."""

from __future__ import annotations

from decimal import Decimal
import json
from typing import Any

from backend.catalogs.demo_hardware import hardware_manifest
from dekopen_engine.models import ParametricNode, SystemParams
from dekopen_engine.geometry import calculate_geometry, compute_geometry
from dekopen_engine.hardware_classes import hardware_cost, hardware_picking
from dekopen_engine.manufacturing import ManufacturingFactsV1


def hardware_case_inputs() -> list[tuple[str, SystemParams, ParametricNode, dict[tuple[str, str], Decimal]]]:
    records = {record["code"]: record for record in hardware_manifest()}
    cases = []
    for label, code, movement, use, width, height, glass in (
        ("oscilobatiente-pequena", "DEMO_60", "TILT_TURN", "WINDOW", "900", "1400", "4-16-4"),
        ("oscilobatiente-alta", "DEMO_60", "TILT_TURN", "WINDOW", "1100", "2100", "4-16-4"),
        ("corredera-pesada", "DEMO_CORREDERA_60", "SLIDE", "WINDOW", "3000", "2400", "6-12-6"),
        ("puerta", "DEMO_PUERTA_70", "TURN", "DOOR", "1000", "2200", "4-16-4"),
    ):
        record = records[code]
        params = SystemParams.model_validate_json(json.dumps(record["params"]))
        node = ParametricNode.model_validate_json(json.dumps({"id": "vano", "type": "BAY", "opening_use": use,
            "opening": {"movement": movement, "hinge_side": "NONE" if movement == "SLIDE" else "LEFT",
                "direction": "INWARD", "leaf_role": "SINGLE", "fixed_in_sash": False},
            "width_mm": width, "height_mm": height, "glass_thickness_mm": "24", "glass_spec": glass,
            "glass_article_sku": code+"-GLASS"}))
        if movement == "SLIDE":
            from dekopen_engine.models import SlidingLayout, SlidingPanel, SlidingPanelKind
            node = node.model_copy(update={"sliding_layout": SlidingLayout(tracks=2, panels=[
                SlidingPanel(slot="L1", kind=SlidingPanelKind.MOVING, track=0),
                SlidingPanel(slot="L2", kind=SlidingPanelKind.MOVING, track=1),
            ])})
        rates = {(price["sku"], price["unit"]): Decimal(price["unit_cost"]) for price in record["prices"]}
        cases.append((label, params, node, rates))
    return cases


def hardware_cases() -> dict[str, Any]:
    return {label: {"bom": (result := calculate_geometry(node, params)).model_dump(mode="json"),
        "cost": str(hardware_cost(result.hardware_items, rates)),
        "interlocks": [member.model_dump(mode="json") for member in manufacturing_case(node, params).members
            if member.identity.role.value == "INTERLOCK"],
        "picking": [{key: str(value) if isinstance(value, Decimal) else value for key, value in row.items()}
            for row in hardware_picking([(item, 1, label) for item in result.hardware_items])]}
        for label, params, node, rates in hardware_case_inputs()}


def manufacturing_case(node: ParametricNode, params: SystemParams) -> ManufacturingFactsV1:
    from dekopen_engine.manufacturing import (
        HandleIntentV1, ReinforcementCutPolicyV1, VerticalReference, project_manufacturing_facts_v1)
    from engine.tests.test_manufacturing import placement, handles
    from scripts.generate_demo_catalog import reinforcement_rules
    from dekopen_engine.models import ProfileRole

    record = next(row for row in hardware_manifest() if row["code"] == params.system_code)
    trace = compute_geometry(node, params).manufacturing_trace
    assert trace is not None
    policy = ReinforcementCutPolicyV1.model_validate_json(json.dumps({
        "policy_id": record["code"]+"_REFUERZO_DEMO_V4", "version": 4,
        "rules": reinforcement_rules(record, 4)}))
    intents = [HandleIntentV1(bay_id=leaf.bay_id, leaf_id=leaf.leaf_id, handle_domain_slot="PRIMARY",
        requested_height_mm=leaf.opening_handle.height_from_bottom_mm, vertical_reference=VerticalReference.LEAF_BOTTOM)
        for leaf in trace.leaves if leaf.opening_handle is not None]
    facts = project_manufacturing_facts_v1(trace=trace, position_id="d0400000-0000-4000-8000-000000000001",
        position_index=1, repetition_index=1, placement_policy=placement(), handle_policy=handles(),
        reinforcement_policy=policy, handle_intents=intents,
        resolved_reinforcement_skus={a.sku: a.reinforcement_sku for a in params.effective_profile_articles.values()
            if a.reinforcement_sku is not None})
    for member in facts.members:
        if member.identity.role is ProfileRole.INTERLOCK:
            leaf = next(leaf for leaf in facts.leaves if leaf.leaf_id == member.leaf_id)
            x = leaf.rect.x_mm if member.identity.physical_member_slot == "INTERLOCK-LEFT" else leaf.rect.x_mm+leaf.rect.width_mm
            assert member.start.x_mm == member.end.x_mm == x
            assert member.start.y_mm == leaf.rect.y_mm
            assert member.end.y_mm == leaf.rect.y_mm+leaf.rect.height_mm
    return facts
