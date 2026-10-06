"""Source-backed D03 typologies, shared with the reviewed golden generator."""

from decimal import Decimal as D
import json
from typing import Any, Literal

from backend.catalogs.demo_openings import opening_manifest
from dekopen_engine.models import (SystemParams, ParametricNode, NodeType, Opening,
    OpeningMovement as M, HingeSide as H, OpeningDirection as Dir, LeafRole as R,
    OpeningUse as U, HingedLayout, HingedLeaf)
from dekopen_engine.geometry import calculate_geometry
from dekopen_engine.snapshot import result_payload


def opening_params(code: str) -> SystemParams:
    record = next(row for row in opening_manifest() if row["code"] == code)
    return SystemParams.model_validate_json(json.dumps(record["params"]))


def opening_node(motion: str, hinge: str = "NONE", direction: str = "INWARD", *,
                 use: str = "WINDOW", role: str = "SINGLE", fixed_in_sash: bool = False,
                 width: str = "1000", height: str = "1400", paired: bool = False) -> ParametricNode:
    opening = Opening(movement=M(motion), hinge_side=H(hinge), direction=Dir(direction),
        leaf_role=R(role), fixed_in_sash=fixed_in_sash)
    layout = None
    if paired:
        def leaf(side: Literal["LEFT", "RIGHT"]) -> HingedLeaf:
            return HingedLeaf(slot=side, opening=Opening(
            movement=M.TURN, hinge_side=H(side), direction=Dir(direction),
            leaf_role=R.ACTIVE if side == hinge else R.PASSIVE))
        layout = HingedLayout(leaves=(leaf("LEFT"), leaf("RIGHT")))
    return ParametricNode(id="bay", type=NodeType.BAY, width_mm=D(width), height_mm=D(height),
        opening=opening, opening_use=U(use), hinged_layout=layout, glass_thickness_mm=D("24"),
        glass_spec="4-16-4 Float Incoloro", glass_article_sku="DEMO-GLASS")


def typologies() -> dict[str, tuple[str, ParametricNode]]:
    cases = {}
    for motion in ("TURN", "TILT_TURN"):
        for side in ("LEFT", "RIGHT"):
            cases[f"{motion}-{side}-INWARD"] = ("DEMO_60", opening_node(motion, side))
    for side in ("LEFT", "RIGHT"):
        cases[f"TURN-{side}-OUTWARD"] = ("DEMO_ALU_PRACTICABLE", opening_node("TURN", side, "OUTWARD"))
        cases[f"FRENCH-{side}"] = ("DEMO_60", opening_node("TURN", side, role="ACTIVE", paired=True, width="1600"))
        for direction in ("INWARD", "OUTWARD"):
            cases[f"DOOR-{side}-{direction}"] = ("DEMO_PUERTA_70", opening_node("TURN", side, direction,
                use="DOOR", height="2200"))
            cases[f"DOUBLE-DOOR-{side}-{direction}"] = ("DEMO_PUERTA_70", opening_node("TURN", side,
                direction, use="DOOR", role="ACTIVE", paired=True, width="1800", height="2200"))
    cases["TILT"] = ("DEMO_60", opening_node("TILT", "BOTTOM"))
    cases["TOP-HUNG"] = ("DEMO_ALU_PRACTICABLE", opening_node("TOP_HUNG", "TOP", "OUTWARD"))
    cases["FIXED-FRAME"] = ("DEMO_60", opening_node("FIXED"))
    cases["FIXED-SASH"] = ("DEMO_60", opening_node("FIXED", fixed_in_sash=True))
    door = opening_node("TURN", "LEFT", use="DOOR", height="2200")
    fixed = opening_node("FIXED", use="DOOR", height="2200")
    split = ParametricNode(id="door-lateral", type=NodeType.SPLIT_V, width_mm=D("1600"), height_mm=D("2200"),
        split_offset_mm=D("1000"), mullion_profile_sku="DEMO_PUERTA_70-POSTE-V",
        children=[door.model_copy(update={"width_mm": None, "height_mm": None}),
                  fixed.model_copy(update={"id": "lateral", "width_mm": None, "height_mm": None, "is_sidelight": True})])
    cases["DOOR-SIDELIGHT"] = ("DEMO_PUERTA_70", split)
    return cases


def opening_cases() -> dict[str, dict[str, Any]]:
    return {name: result_payload(calculate_geometry(node, opening_params(code)))
            for name, (code, node) in typologies().items()}
