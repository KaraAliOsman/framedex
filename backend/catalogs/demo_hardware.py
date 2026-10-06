"""D04 synthetic class authorities. New v4 rows; v1–v3 remain unchanged."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from random import Random
from typing import Any

from backend.catalogs.demo_openings import opening_manifest

SEED = 20261231
SOURCE = f"Herrajes sintéticos DEKOPEN v4; semilla {SEED}; sin certificación"


def hardware_manifest() -> list[dict[str, Any]]:
    records = deepcopy(opening_manifest())
    rng = Random(SEED)
    for record in records:
        params = record["params"]
        record["name"] = record["name"].replace("aperturas v3", "herrajes v4")
        record["version"], record["hardware_seed"] = 4, SEED
        new_kits: list[dict[str, Any]] = []
        aliases: dict[str, list[str]] = {}
        for old in params["available_hardware_kits"]:
            opening = old["opening_type"]
            passive = old["sku"].endswith("PASSIVE")
            family = old["sku"].replace("KIT-", "HW4-")
            aliases[old["sku"]] = []
            for index, class_code in enumerate(("STANDARD", "HEAVY")):
                heavy = index == 1
                prefix = family + "-" + class_code + "-"
                components: list[dict[str, Any]] = []

                def component(key: str, name: str, category: str, qty: int = 1, *,
                              axis: str | None = None, deduction: str = "0", count_height: bool = False,
                              weight: str = "0.1000", machine: str | None = None) -> dict[str, Any]:
                    rule: dict[str, Any] = {"sku": prefix+key, "name": name+" · DEMO", "category": category,
                        "quantity": {"base": qty}, "length": None if axis is None else {
                            "axis": axis, "deduction_mm": deduction},
                        "price_unit": "EA" if axis is None else "M", "weight_kg": weight if axis is None else None,
                        "weight_kg_m": weight if axis is not None else None,
                        "purchasing_sku": "COMPRA-"+prefix+key,
                        "manufacturer_name": "Fabricante sintético · DEMO", "source": SOURCE,
                        "machining": []}
                    if count_height:
                        rule["quantity"].update(axis="HEIGHT", threshold="800", step="600", increment=1)
                    if machine:
                        rule["machining"] = [{"code": key+"-PREP", "name": "Alojamiento de "+name.lower(),
                            "kind": machine, "host_side": "HINGE" if category == "HINGE" else "CLOSING",
                            "source": SOURCE, "positions_mm": []}]
                    record["prices"].append({"sku": rule["sku"], "unit": rule["price_unit"],
                        "unit_cost": str(rng.randrange(900, 15001))})
                    return rule

                if opening == "SLIDING":
                    components.append(component("CARRO", "Carro reforzado" if heavy else "Carro", "ROLLER", 4 if heavy else 2, weight="0.3500"))
                    components.append(component("CIERRE", "Cierre de corredera", "LOCK", machine="LOCK_PREP"))
                else:
                    components.append(component("BISAGRA", "Bisagra reforzada" if heavy else "Bisagra", "HINGE", 4 if opening == "DOOR" and heavy else 3 if opening == "DOOR" or heavy else 2, weight="0.2500" if heavy else "0.1500", machine="HINGE_PREP"))
                    components.append(component("FALLEBA" if passive else "CREMONA", "Falleba pasiva" if passive else "Cremona", "LOCK", axis="HEIGHT", deduction="400" if opening == "DOOR" else "150", weight="0.2500", machine="SLOT"))
                    components.append(component("CIERRE", "Punto de cierre", "LOCK", 2, count_height=True, weight="0.0400"))
                    components.append(component("CERRADERO", "Cerradero", "LOCK", 2, count_height=True, weight="0.0350", machine="LOCK_PREP"))
                    components.append(component("TAPA", "Tapa de bisagra", "OTHER", 4 if opening == "DOOR" and heavy else 3 if opening == "DOOR" or heavy else 2, weight="0.0100"))
                    if opening == "TILT_TURN":
                        components.append(component("RENVIO", "Reenvío de esquina", "CONNECTOR", 2, weight="0.0800"))
                        components.append(component("COMPAS", "Compás", "SUPPORT", axis="WIDTH", deduction="120", weight="0.3000"))
                    if opening == "DOOR":
                        components.append(component("CILINDRO", "Cilindro", "LOCK", weight="0.2000"))
                handles = []
                if not passive:
                    for model, label in (("STANDARD", "Estándar"), ("KEY", "Con llave"), ("BUTTON", "Con botón"), ("ESCUTCHEON", "Puerta con escudo")):
                        if (opening == "DOOR") != (model == "ESCUTCHEON"):
                            continue
                        colors = [{"code": color, "name": label_color,
                            "component": component("MANILLA-"+model+"-"+color, "Manilla "+label.lower()+" "+label_color.lower(), "HANDLE", weight="0.2500")}
                            for color, label_color in (("WHITE", "Blanca"), ("BLACK", "Negra"))]
                        vertical = "FIXED" if opening == "AWNING" else "TOP_OFFSET" if opening == "TILT" else "RANGE" if opening == "DOOR" else "CENTER"
                        handles.append({"code": model, "name": label, "model": model, "colors": colors,
                            "default_color": "WHITE", "vertical_rule": vertical,
                            "default_height_mm": "37.50" if opening in ("AWNING", "TILT") else "1000" if opening == "DOOR" else None,
                            "minimum_from_bottom_mm": "0" if opening in ("AWNING", "TILT") else "100",
                            "minimum_from_top_mm": "0" if opening in ("AWNING", "TILT") else "100", "source": SOURCE})
                options = []
                if not passive:
                    for key, name, kind in (("ANTIPALANCA", "Puntos antipalanca", "SECURITY"), ("LIMITADOR", "Limitador de apertura", "LIMITER")):
                        options.append({"code": key, "name": name+" · DEMO", "kind": kind,
                            "components": [component(key, name, "LOCK" if kind == "SECURITY" else "SUPPORT", weight="0.1200")], "source": SOURCE})
                    if opening == "TILT_TURN":
                        options.append({"code": "MICRO", "name": "Microventilación · DEMO", "kind": "MICROVENTILATION",
                            "components": [component("MICRO", "Microventilación", "FITTING", weight="0.0300")], "source": SOURCE})
                    if opening != "SLIDING":
                        hidden = component("BISAGRA-OCULTA", "Bisagra oculta", "HINGE", 3 if heavy else 2, weight="0.3500", machine="HINGE_PREP")
                        options.append({"code": "OCULTAS", "name": "Bisagras ocultas · DEMO", "kind": "HIDDEN_HINGES",
                            "components": [hidden], "replaces_skus": [components[0]["sku"], prefix+"TAPA"], "source": SOURCE})
                authority = {"schema_version": 1, "family_code": family, "family_name": old["name"],
                    "class_code": class_code, "class_name": "Pesada · DEMO" if heavy else "Estándar · DEMO",
                    "priority": index, "source": SOURCE, "synthetic": True,
                    "maximum_width_height_ratio": "1.50" if opening == "TILT_TURN" else None,
                    "minimum_stay_height_mm": "500" if opening == "TILT_TURN" else None,
                    "components": components, "handles": handles,
                    "default_handle": handles[0]["code"] if handles else None, "options": options}
                sku = prefix.rstrip("-")
                kit = {**old, "sku": sku, "name": old["name"]+" · "+authority["class_name"],
                    "weight_kg": None, "contents": [], "class_authority": authority,
                    "max_leaf_weight_kg": old["max_leaf_weight_kg"] if heavy else "80.00" if opening != "SLIDING" else "100.00"}
                if opening == "SLIDING":
                    kit["carriages_qty"] = 4 if heavy else 2
                    kit["carriage_capacity_kg"] = str(Decimal(kit["max_leaf_weight_kg"])/Decimal(kit["carriages_qty"]))
                new_kits.append(kit)
                aliases[old["sku"]].append(sku)
        params["available_hardware_kits"] = new_kits
        record["prices"] = [price for price in record["prices"] if price["unit"] != "KIT"]
        for capability in params["opening_capabilities"]:
            capability["hardware_kit_skus"] = [sku for old in capability["hardware_kit_skus"] for sku in aliases[old]]
    return records
