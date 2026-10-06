"""D03 versions extend the synthetic catalog without changing v2 authorities."""

from copy import deepcopy
from random import Random
from typing import Any

from backend.catalogs.demo_fixture import manifest

SEED = 20261006
SOURCE = f"Aperturas sintéticas DEKOPEN v3; semilla {SEED}; sin certificación"


def opening_manifest() -> list[dict[str, Any]]:
    records = deepcopy(manifest())
    door = deepcopy(next(record for record in records if record["code"] == "DEMO_70"))
    # The door is a separate family. Reuse the explicit synthetic profile math,
    # not a permission that allows doors inside a casement series.
    def renamed(value):
        if isinstance(value, str):
            return value.replace("DEMO_70", "DEMO_PUERTA_70")
        if isinstance(value, dict):
            return {renamed(key): renamed(item) for key, item in value.items()}
        if isinstance(value, list):
            return [renamed(item) for item in value]
        return value
    door = renamed(door)
    door["code"], door["name"] = "DEMO_PUERTA_70", "PVC puerta 70 mm · DEMO"
    door["params"]["system_family"] = "DOOR"
    door["params"]["available_hardware_kits"] = []
    door["prices"] = [row for row in door["prices"] if "KIT-" not in row["sku"]]
    for article in door["articles"]:
        if article["role"] == "SASH":
            article["role"] = "DOOR_SASH"
    door["params"]["effective_profile_articles"] = {
        article["role"]: {key: value for key, value in article.items() if key != "name"}
        for article in door["articles"] if article["role"] != "GLAZING_BEAD"}
    fixed_limit = deepcopy(door["params"]["dimensional_limits"][0])
    door_limit = {**deepcopy(door["params"]["dimensional_limits"][1]),
        "min_leaf_width_mm": "500.00", "min_leaf_height_mm": "1500.00",
        "max_leaf_width_mm": "1400.00", "max_leaf_height_mm": "2800.00", "source": SOURCE}
    door["params"]["dimensional_limits"] = [fixed_limit,
        {**door_limit, "opening_type": "DOOR_ENTRY"},
        {**door_limit, "opening_type": "DOOR_DOUBLE"}]
    records.append(door)
    rng = Random(SEED)
    for record in records:
        code, params = record["code"], record["params"]
        family, prefix = params["system_family"], code + "-"
        is_door, sliding = family == "DOOR", family == "SLIDING"
        record["version"], record["opening_seed"] = 3, SEED
        record["name"] = record["name"].replace(" · DEMO", " · aperturas v3 · DEMO")
        capabilities = []
        use = "DOOR" if is_door else "WINDOW"
        def capability(movement, direction, role="SINGLE", *, fixed_in_sash=False,
                       kit=None, handle=True):
            hinges = (["NONE"] if movement in ("FIXED", "SLIDE") else ["BOTTOM"]
                if movement == "TILT" else ["TOP"] if movement == "TOP_HUNG" else ["LEFT", "RIGHT"])
            rule = None
            if handle and movement not in ("FIXED", "SLIDE") and role != "PASSIVE":
                rule = {"vertical_reference": "LEAF_BOTTOM" if is_door else "CENTER",
                    "default_height_mm": "1000.00" if is_door else None,
                    "minimum_from_top_mm": "100.00", "minimum_from_bottom_mm": "100.00",
                    "closing_edge_offset_mm": "37.50", "source": SOURCE}
            capabilities.append({"use": use, "movement": movement, "direction": direction,
                "leaf_role": role, "fixed_in_sash": fixed_in_sash, "hinge_sides": hinges,
                "hardware_kit_skus": [kit] if kit else [], "handle_rule": rule, "source": SOURCE})
        capability("FIXED", "INWARD", handle=False)
        if sliding:
            capability("SLIDE", "INWARD", kit=prefix + "KIT-SLIDING", handle=False)
        else:
            # Additional profile rows do not consume v2's random draws.
            template = deepcopy(params["effective_profile_articles"]["MULLION_V"])
            template.update(sku=prefix + "INVERSOR", name="Inversor sintético · DEMO",
                role="INVERSOR", face_width_mm="24.00", weight_kg_m="0.8000",
                steel_weight_kg_m="0.6000" if params["material"] == "PVC" else None,
                reinforcement_sku=prefix + "ACERO-INVERSOR" if params["material"] == "PVC" else None)
            if template["reinforcement_rule"]:
                template["reinforcement_rule"].update(reinforcement_sku=template["reinforcement_sku"], source=SOURCE)
            template["cut_rule"].update(source=SOURCE)
            record["articles"].append(template)
            params["effective_profile_articles"]["INVERSOR"] = {
                key: value for key, value in template.items() if key != "name"}
            record["prices"].append({"sku": template["sku"], "unit": "BAR", "unit_cost": str(rng.randrange(12000, 30001))})
            if template["reinforcement_sku"]:
                record["prices"].append({"sku": template["reinforcement_sku"], "unit": "BAR", "unit_cost": str(rng.randrange(7000, 12001))})
            params["paired_leaf_rule"] = {"meeting_overlap_mm": "20.00", "meeting_gap_mm": "0.00",
                "inversor_end_deduction_mm": "2.00", "source": SOURCE}
            if is_door:
                threshold = deepcopy(template)
                threshold.update(sku=prefix + "UMBRAL", name="Umbral sintético · DEMO",
                    role="THRESHOLD", face_width_mm="30.00", weight_kg_m="0.4000",
                    reinforcement_rule=None, reinforcement_sku=None, steel_weight_kg_m=None)
                record["articles"].append(threshold)
                params["effective_profile_articles"]["THRESHOLD"] = {
                    key: value for key, value in threshold.items() if key != "name"}
                record["prices"].append({"sku": threshold["sku"], "unit": "BAR", "unit_cost": "12000"})
            def kit(kind, label, *, passive=False, max_weight="150.00"):
                sku = prefix + "KIT-" + kind
                components = [{"sku": prefix + "BISAGRA", "name": "Bisagra DEMO",
                    "qty": "3" if is_door else "2", "unit": "EA", "category": "HINGE"},
                    {"sku": prefix + ("FALLEBA" if passive else "CIERRE"),
                     "name": "Falleba pasiva DEMO" if passive else "Cierre DEMO",
                     "qty": "1", "unit": "EA", "category": "LOCK"}]
                if not passive:
                    components.insert(0, {"sku": prefix + "MANILLA", "name": "Manilla DEMO",
                        "qty": "1", "unit": "EA", "category": "HANDLE"})
                params["available_hardware_kits"].append({"sku": sku, "name": label + " · DEMO",
                    "opening_type": "DOOR" if is_door else "TILT" if kind == "TILT" else "TURN",
                    "min_leaf_width_mm": "500.00" if is_door else "200.00",
                    "max_leaf_width_mm": "1400.00" if is_door else "1600.00",
                    "min_leaf_height_mm": "1500.00" if is_door else "200.00",
                    "max_leaf_height_mm": "2800.00" if is_door else "2500.00",
                    "max_leaf_weight_kg": max_weight, "weight_kg": "2.5000", "rail_type": "dual",
                    "carriages_qty": 0, "stay_arms_qty": 0, "contents": components})
                record["prices"].append({"sku": sku, "unit": "KIT", "unit_cost": str(rng.randrange(18000, 60001))})
                return sku
            active = kit("DOOR", "Herraje puerta") if is_door else prefix + "KIT-TURN"
            outward = kit("OUTWARD", "Herraje hacia afuera") if (is_door or params["material"] == "ALUMINIUM") else None
            passive = kit("PASSIVE", "Herraje pasivo con falleba", passive=True)
            for direction, active_kit in (("INWARD", active), ("OUTWARD", outward)):
                if active_kit is None:
                    continue
                capability("TURN", direction, kit=active_kit)
                capability("TURN", direction, "ACTIVE", kit=active_kit)
                capability("TURN", direction, "PASSIVE", kit=passive, handle=False)
            if not is_door:
                capability("TILT_TURN", "INWARD", kit=prefix + "KIT-TILT_TURN")
                capability("TOP_HUNG", "OUTWARD", kit=prefix + "KIT-AWNING")
                capability("TILT", "INWARD", kit=kit("TILT", "Herraje banderola", max_weight="45.00"))
                capability("FIXED", "INWARD", fixed_in_sash=True, handle=False)
        params["opening_capabilities"] = capabilities
    return records
