"""Deterministic commercial typology derived from validated design intent."""

from collections.abc import Mapping
import json
from dekopen_engine.models import Opening, OpeningUse
from dekopen_engine.openings import fabrication_alias


COMMERCIAL_TYPOLOGIES = (
    "FIXED",
    "TURN",
    "TILT_TURN",
    "SLIDING_2L",
    "SLIDING_3L",
    "SLIDING_4L",
    "SLIDING",
    "AWNING",
    "DOOR_ENTRY",
    "COMPOSITE",
)

_OPENING_TYPOLOGIES = {
    "FIXED": "FIXED",
    "TURN_LEFT": "TURN",
    "TURN_RIGHT": "TURN",
    "TILT_TURN_LEFT": "TILT_TURN",
    "TILT_TURN_RIGHT": "TILT_TURN",
    "SLIDING_2L": "SLIDING_2L",
    "SLIDING_3L": "SLIDING_3L",
    "SLIDING_4L": "SLIDING_4L",
    "SLIDING": "SLIDING",
    "AWNING": "AWNING",
    "DOOR_ENTRY": "DOOR_ENTRY",
}


def derive_typology(tree: Mapping[str, object]) -> str:
    if tree.get("version") == "product-v2":
        assembly = tree.get("assembly")
        if isinstance(assembly, Mapping):
            modules = assembly.get("modules")
            if (
                isinstance(modules, list)
                and len(modules) == 1
                and isinstance(modules[0], Mapping)
                and isinstance(modules[0].get("tree"), Mapping)
            ):
                return derive_typology(modules[0]["tree"])
        return "COMPOSITE"
    node: object = tree
    if tree.get("type") == "ROOT":
        children = tree.get("children")
        if not isinstance(children, list) or len(children) != 1:
            raise ValueError("invalid parametric root")
        node = children[0]
    if not isinstance(node, Mapping):
        raise ValueError("invalid parametric node")
    children = node.get("children")
    if isinstance(children, list) and children:
        return "COMPOSITE"
    if isinstance(node.get("opening"), Mapping) and not node.get("opening_type"):
        physical = Opening.model_validate_json(json.dumps(node["opening"]))
        if node.get("hinged_layout") or physical.fixed_in_sash:
            return "COMPOSITE"
        # Commercial buckets retain their historical tariff contract; the
        # saved physical object remains the motion/handedness authority.
        return _OPENING_TYPOLOGIES[fabrication_alias(physical,
            OpeningUse(str(node.get("opening_use") or "WINDOW"))).value]
    opening = node.get("opening_type")
    if not isinstance(opening, str) or opening not in _OPENING_TYPOLOGIES:
        raise ValueError("unsupported opening typology")
    return _OPENING_TYPOLOGIES[opening]
