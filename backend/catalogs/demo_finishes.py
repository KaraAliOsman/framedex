"""Additive v5 synthetic finish chart. No supplier color is certified here."""

from copy import deepcopy
from random import Random
from typing import Any

from backend.catalogs.demo_hardware import hardware_manifest

SEED = 20270102
SOURCE = f"Acabados sintéticos DEKOPEN v5; semilla {SEED}; sin certificación"


def finish_manifest() -> list[dict[str, Any]]:
    records = deepcopy(hardware_manifest())
    rng = Random(SEED)
    for record in records:
        params = record["params"]
        pvc = params["material"] == "PVC"
        record["name"] = record["name"].replace("herrajes v4", "acabados v5")
        record["version"], record["finish_seed"] = 5, SEED
        colors: list[dict[str, Any]] = []
        for code, name, kind, rgb, gloss in (
            (("WHITE", "Blanco", "MASS", ["0.78", "0.79", "0.76"], "0.30"),
             ("CREAM", "Crema", "MASS", ["0.80", "0.71", "0.50"], "0.30"),
             ("WALNUT", "Nogal", "FOIL", ["0.12", "0.046", "0.013"], "0.18"),
             ("ANTHRACITE", "Antracita", "FOIL", ["0.034", "0.042", "0.044"], "0.18"),
             ("COEX_GREY", "Gris coextruido", "COEXTRUDED", ["0.15", "0.17", "0.18"], "0.22"))
            if pvc else
            (("RAL9016", "Blanco tráfico RAL 9016", "RAL", ["0.78", "0.79", "0.76"], "0.70"),
             ("RAL7016", "Gris antracita RAL 7016", "RAL", ["0.034", "0.042", "0.044"], "0.30"),
             ("ANODIZED_SILVER", "Anodizado plata", "ANODIZED", ["0.50", "0.52", "0.53"], None),
             ("WOOD_WALNUT", "Efecto madera nogal", "WOOD_EFFECT", ["0.12", "0.046", "0.013"], "0.18"))
        ):
            colors.append({"code": code, "name": name, "kind": kind, "linear_rgb": rgb,
                "manufacturer_code": "DEMO-"+code, "gloss": gloss, "texture_path": None,
                "approximate": True, "source": SOURCE, "synthetic": True})
        combinations: list[dict[str, Any]] = []
        pairs = [("WHITE", "WHITE", "WHITE"), ("CREAM", "CREAM", "CREAM")]
        if pvc:
            for skin in ("WALNUT", "ANTHRACITE", "COEX_GREY"):
                pairs.extend(((skin, skin, skin), ("WHITE_"+skin, "WHITE", skin),
                              (skin+"_WHITE", skin, "WHITE")))
        else:
            pairs = [("WHITE", "RAL9016", "RAL9016"), ("RAL7016", "RAL7016", "RAL7016"),
                ("ANODIZED_SILVER", "ANODIZED_SILVER", "ANODIZED_SILVER"),
                ("WOOD_WALNUT", "WOOD_WALNUT", "WOOD_WALNUT"),
                ("WHITE_RAL7016", "RAL9016", "RAL7016")]
        for code, interior, exterior in pairs:
            dark = pvc and (interior not in {"WHITE", "CREAM"} or exterior not in {"WHITE", "CREAM"})
            surcharge_kind = "NONE" if code in {"WHITE", "CREAM"} else (
                "PERCENT" if "ANTHRACITE" in code or "RAL7016" in code else
                "FIXED" if "COEX" in code or "ANODIZED" in code else "PER_M")
            amount = "0" if surcharge_kind == "NONE" else "12.5" if surcharge_kind == "PERCENT" else "6500" if surcharge_kind == "FIXED" else "750"
            combinations.append({"code": code, "interior": interior, "exterior": exterior,
                "base": ("CREAM" if interior == "CREAM" else "WHITE") if pvc else None,
                "reinforcement_required": dark, "reinforcement_stock_code": "WHITE",
                "glass_clearance_mm": "6" if dark else "5",
                "max_position_width_mm": "6000" if dark else None,
                "max_position_height_mm": "3000" if dark else None,
                "max_leaf_width_mm": ("2000" if params["system_family"] == "SLIDING" else "1400") if dark else None,
                "max_leaf_height_mm": "2500" if dark else None,
                "extra_lead_days": 5 if dark else None if "ANODIZED" in code else 0,
                "surcharge": {"kind": surcharge_kind, "amount": amount, "currency": "CLP", "source": SOURCE},
                "allowed_handle_colors": ["WHITE", "BLACK"], "source": SOURCE, "synthetic": True})
        handles = [{"code": code, "manufacturer_code": "DEMO-MANILLA-"+code, "name": name,
            "kind": "RAL", "linear_rgb": rgb, "gloss": "0.30", "texture_path": None,
            "approximate": True, "source": SOURCE, "synthetic": True}
            for code, name, rgb in (("WHITE", "Blanco", ["0.78", "0.79", "0.76"]),
                                    ("BLACK", "Negro", ["0.012", "0.014", "0.015"]))]
        params["finish_authority"] = {"schema_version": 1, "material": params["material"],
            "colors": colors, "handle_colors": handles, "combinations": combinations, "source": SOURCE}
        params["finishes"] = [combo["code"] for combo in combinations]
        maps: dict[str, dict[str, str]] = {}
        bindings = []
        prices = {price["sku"]: price for price in record["prices"]}
        for combo in combinations:
            maps[combo["code"]] = {}
            for article in record["articles"]:
                sku = article["sku"]
                commercial = "COMPRA-V5-"+sku+"-"+combo["code"]
                maps[combo["code"]][sku] = commercial
                bindings.append({"sku": sku, "finish": combo["code"], "commercial_sku": commercial})
                base_price = prices.get("COMPRA-"+sku)
                record["prices"].append({"sku": commercial, "unit": "BAR",
                    "unit_cost": base_price["unit_cost"] if base_price else str(rng.randrange(9000, 50001))})
        params["finish_profile_skus"] = maps
        record["finish_bindings"] = bindings
    return records
