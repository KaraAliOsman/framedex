"""Independent v8 advanced-motion fixtures. Every authority is synthetic."""

from copy import deepcopy
from decimal import Decimal
from random import Random
from typing import Any

from backend.catalogs.demo_couplings import coupling_manifest

SEED = 20270126
SOURCE = f"Tipologías avanzadas sintéticas DEKOPEN v8; semilla {SEED}; sin certificación"


def _rename(value: Any, old: str, new: str) -> Any:
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, dict):
        return {_rename(key, old, new): _rename(item, old, new) for key, item in value.items()}
    if isinstance(value, list):
        return [_rename(item, old, new) for item in value]
    return value


def _panel(
    slot: str,
    *,
    fixed: bool = False,
    share: str = "0.5",
    track: int | None = None,
    plane: str = "0",
    travel: str | None = None,
    fraction: str = "0",
    closing: str = "RIGHT",
    **extra: Any,
) -> dict[str, Any]:
    return {
        "slot": slot,
        "kind": "FIXED" if fixed else "MOVING",
        "share": share,
        "fixed_in_sash": fixed,
        "track": track,
        "plane_offset_mm": plane,
        "travel": travel,
        "travel_fraction": fraction,
        "closing_side": "NONE" if fixed else closing,
        "pivot_fraction": None,
        "fold_group": None,
        "fold_index": None,
        "stack_side": None,
        "pass_through": False,
        "balance": None,
        **extra,
    }


def advanced_manifest() -> list[dict[str, Any]]:
    templates = {record["code"]: record for record in coupling_manifest()}
    rng = Random(SEED)
    records: list[dict[str, Any]] = []
    for code, base, name, family, motion, use in (
        (
            "DEMO_HST",
            "DEMO_CORREDERA_60",
            "Elevable-corredera HST",
            "LIFT_SLIDE",
            "LIFT_SLIDE",
            "WINDOW",
        ),
        ("DEMO_PSK", "DEMO_70", "Osciloparalela PSK", "CASEMENT", "PARALLEL_SLIDE", "WINDOW"),
        ("DEMO_PLEGABLE", "DEMO_PUERTA_70", "Puerta plegable", "DOOR", "FOLD", "DOOR"),
        ("DEMO_PIVOT_V", "DEMO_70", "Pivotante vertical", "CASEMENT", "PIVOT_V", "WINDOW"),
        ("DEMO_PIVOT_H", "DEMO_70", "Pivotante horizontal", "CASEMENT", "PIVOT_H", "WINDOW"),
        (
            "DEMO_GUILLOTINA",
            "DEMO_CORREDERA_60",
            "Guillotina",
            "SLIDING",
            "VERTICAL_SLIDE",
            "WINDOW",
        ),
        ("DEMO_PUERTA_CORREDERA", "DEMO_CORREDERA_60", "Puerta corredera", "DOOR", "SLIDE", "DOOR"),
    ):
        record = _rename(deepcopy(templates[base]), base, code)
        record.update(
            code=code, name=name + " · tipologías v8 · DEMO", version=8, advanced_seed=SEED
        )
        params = record["params"]
        params["system_family"] = family
        if family == "DOOR" and params.get("sliding") is not None:
            params["sliding"] = None
            for article in record["articles"]:
                if article["role"] == "SLIDING_SASH":
                    article["role"] = "DOOR_SASH"
        role = (
            "DOOR_SASH"
            if family == "DOOR"
            else "SLIDING_SASH"
            if family in ("SLIDING", "LIFT_SLIDE")
            else "SASH"
        )
        params["effective_profile_articles"] = {
            article["role"]: {key: value for key, value in article.items() if key != "name"}
            for article in record["articles"]
            if article["role"] not in ("GLAZING_BEAD", "COUPLER")
        }
        params["available_hardware_kits"] = []
        record["prices"] = [price for price in record["prices"] if "HW4-" not in price["sku"]]

        def profile(profile_role: str, face: str, mass: str) -> None:
            if profile_role in params["effective_profile_articles"]:
                return
            item = deepcopy(
                next(article for article in record["articles"] if article["role"] == "FRAME")
            )
            item.update(
                role=profile_role,
                sku=code + "-" + profile_role,
                name={"RAIL": "Guía", "THRESHOLD": "Umbral", "INTERLOCK": "Encuentro"}[profile_role]
                + " específico · DEMO",
                face_width_mm=face,
                weight_kg_m=mass,
                reinforcement_rule=None,
                reinforcement_sku=None,
                steel_weight_kg_m=None,
                reinforcement_gap_mm=None,
            )
            item["cut_rule"] = {
                "angle_degrees": 90,
                "welding_loss_per_end_mm": "0",
                "joint_deduction_per_end_mm": "0",
                "meeting_deduction_mm": "0",
                "cut_step_mm": "0.01",
                "rounding": "UP",
                "source": SOURCE,
            }
            record["articles"].append(item)
            params["effective_profile_articles"][profile_role] = {
                key: value for key, value in item.items() if key != "name"
            }
            for finish in params["finish_authority"]["combinations"]:
                commercial = "COMPRA-V8-" + item["sku"] + "-" + finish["code"]
                params["finish_profile_skus"][finish["code"]][item["sku"]] = commercial
                record["finish_bindings"].append(
                    {"sku": item["sku"], "finish": finish["code"], "commercial_sku": commercial}
                )
                record["prices"].append(
                    {"sku": commercial, "unit": "BAR", "unit_cost": str(rng.randrange(9000, 25001))}
                )

        if motion in ("LIFT_SLIDE", "FOLD", "SLIDE"):
            profile("THRESHOLD", "30", "0.4000")
        if motion not in ("PIVOT_V", "PIVOT_H"):
            profile("RAIL", "10", "0.8000")

        def kits(suffix: str = "", *, balance: str | None = None) -> list[str]:
            skus = []
            for index, class_code in enumerate(("STANDARD", "HEAVY")):
                prefix = code + "-HW8-" + class_code + ("-" + suffix if suffix else "") + "-"

                def component(
                    key: str, label: str, category: str, qty: int = 1, *, weight: str = "0.2000"
                ) -> dict[str, Any]:
                    item: dict[str, Any] = {
                        "sku": prefix + key,
                        "name": label + " · DEMO",
                        "category": category,
                        "quantity": {"base": qty},
                        "length": None,
                        "price_unit": "EA",
                        "weight_kg": weight,
                        "weight_kg_m": None,
                        "purchasing_sku": "COMPRA-" + prefix + key,
                        "manufacturer_name": "Fabricante sintético · DEMO",
                        "source": SOURCE,
                        "machining": [],
                    }
                    record["prices"].append(
                        {
                            "sku": item["sku"],
                            "unit": "EA",
                            "unit_cost": str(rng.randrange(900, 22001)),
                        }
                    )
                    return item

                components = [
                    component(
                        "CIERRE",
                        "Cerradura de puerta corredera"
                        if use == "DOOR" and motion == "SLIDE"
                        else "Cierre específico",
                        "LOCK",
                    )
                ]
                carriages = 4 if index else 2
                if motion in ("LIFT_SLIDE", "PARALLEL_SLIDE", "FOLD", "SLIDE"):
                    components.append(
                        component(
                            "CARRO",
                            "Carro de elevación" if motion == "LIFT_SLIDE" else "Carro guiado",
                            "ROLLER",
                            carriages,
                            weight="0.3500",
                        )
                    )
                if motion == "PARALLEL_SLIDE":
                    components.append(component("COMPAS", "Compás osciloparalelo", "SUPPORT", 2))
                if motion == "FOLD":
                    components.append(component("BISAGRA", "Bisagra de plegado", "HINGE", 3))
                    if suffix == "PASO":
                        components.append(
                            component("CIERRE-PASO", "Cerradura de hoja de paso", "LOCK")
                        )
                        components.append(
                            component("BISAGRA-PASO", "Bisagra de paso independiente", "HINGE", 2)
                        )
                if motion in ("PIVOT_V", "PIVOT_H"):
                    components.append(
                        component(
                            "PIVOTE", "Pivote con eje desplazado", "HINGE", 2, weight="0.5000"
                        )
                    )
                    carriages = 0
                if motion == "VERTICAL_SLIDE":
                    components.append(
                        component(
                            "BALANCE",
                            "Contrapeso" if balance == "COUNTERWEIGHT" else "Muelle de balance",
                            "SUPPORT",
                            2,
                            weight="1.0000" if balance == "COUNTERWEIGHT" else "0.4000",
                        )
                    )
                    carriages = 0
                handles = [
                    {
                        "code": "ELEVACION" if motion == "LIFT_SLIDE" else "ACCIONAMIENTO",
                        "name": "Manilla de elevación"
                        if motion == "LIFT_SLIDE"
                        else "Manilla de accionamiento",
                        "model": "STANDARD",
                        "colors": [
                            {
                                "code": color,
                                "name": label,
                                "component": component(
                                    "MANILLA-" + color,
                                    "Manilla " + label.lower(),
                                    "HANDLE",
                                    weight="0.2500",
                                ),
                            }
                            for color, label in (("WHITE", "Blanca"), ("BLACK", "Negra"))
                        ],
                        "default_color": "WHITE",
                        "vertical_rule": "FIXED"
                        if motion in ("PIVOT_H", "VERTICAL_SLIDE")
                        else "CENTER",
                        "default_height_mm": "37.50"
                        if motion in ("PIVOT_H", "VERTICAL_SLIDE")
                        else None,
                        "minimum_from_bottom_mm": "0"
                        if motion in ("PIVOT_H", "VERTICAL_SLIDE")
                        else "100",
                        "minimum_from_top_mm": "0"
                        if motion in ("PIVOT_H", "VERTICAL_SLIDE")
                        else "100",
                        "source": SOURCE,
                    }
                ]
                maximum = "300" if index else "120"
                sku = prefix.rstrip("-")
                params["available_hardware_kits"].append(
                    {
                        "sku": sku,
                        "name": name + " · " + ("Pesada" if index else "Estándar") + " · DEMO",
                        "opening_type": "SLIDING" if motion == "SLIDE" else motion,
                        "min_leaf_width_mm": "250",
                        "max_leaf_width_mm": "2200",
                        "min_leaf_height_mm": "250",
                        "max_leaf_height_mm": "3000",
                        "max_leaf_weight_kg": maximum,
                        "weight_kg": None,
                        "rail_type": "dual",
                        "carriages_qty": carriages,
                        "carriage_capacity_kg": str(Decimal(maximum) / Decimal(carriages))
                        if carriages
                        else None,
                        "stay_arms_qty": 2 if motion == "PARALLEL_SLIDE" else 0,
                        "contents": [],
                        "class_authority": {
                            "schema_version": 1,
                            "family_code": code + "-HW8" + ("-" + suffix if suffix else ""),
                            "family_name": name + " · DEMO",
                            "class_code": class_code,
                            "class_name": ("Pesada" if index else "Estándar") + " · DEMO",
                            "priority": index,
                            "source": SOURCE,
                            "synthetic": True,
                            "components": components,
                            "handles": handles,
                            "default_handle": handles[0]["code"],
                            "options": [],
                        },
                    }
                )
                skus.append(sku)
            return skus

        common_kits = kits() if motion != "VERTICAL_SLIDE" else []
        pass_kits = kits("PASO") if motion == "FOLD" else []
        recipes = []

        def recipe(
            scheme: str,
            panels: list[dict[str, Any]],
            *,
            width: str,
            height: str,
            suffix: str = "",
            selected_kits: list[str] | None = None,
        ) -> None:
            threshold = motion in ("LIFT_SLIDE", "FOLD", "SLIDE")
            rails = (
                []
                if motion in ("PIVOT_V", "PIVOT_H")
                else ["LEFT", "RIGHT"]
                if motion == "VERTICAL_SLIDE"
                else ["TOP", "BOTTOM"]
                if motion == "FOLD"
                else ["BOTTOM", "BOTTOM"]
                if motion == "LIFT_SLIDE"
                else ["BOTTOM"]
            )
            recipes.append(
                {
                    "schema_version": 1,
                    "code": scheme + ("-" + suffix if suffix else ""),
                    "scheme": scheme,
                    "name": name
                    + " · "
                    + scheme
                    + (" · " + suffix.lower() if suffix else "")
                    + " · DEMO",
                    "source": SOURCE,
                    "synthetic": True,
                    "distribution_axis": "Y" if motion == "VERTICAL_SLIDE" else "X",
                    "panels": panels,
                    "leaf_profile_role": role,
                    "inset_left_mm": "-20",
                    "inset_right_mm": "-20",
                    "inset_top_mm": "-20",
                    "inset_bottom_mm": "5" if threshold else "-20",
                    "meeting_overlap_mm": "20" if motion in ("LIFT_SLIDE", "SLIDE") else "0",
                    "meeting_gap_mm": "3" if motion == "FOLD" else "0",
                    "glazing_deduction_width_mm": "20" if role == "SLIDING_SASH" else "0",
                    "glazing_deduction_height_mm": "20" if role == "SLIDING_SASH" else "0",
                    "threshold_height_mm": "30" if threshold else None,
                    "rail_profile_role": "RAIL" if rails else None,
                    "rail_count": len(rails),
                    "rail_sides": rails,
                    "rail_end_deduction_mm": "2",
                    "interlock_required": motion in ("LIFT_SLIDE", "SLIDE"),
                    "interlock_end_deduction_mm": "2",
                    "lift_mm": "8" if motion == "LIFT_SLIDE" else None,
                    "parallel_offset_mm": "35" if motion == "PARALLEL_SLIDE" else None,
                    "opening_angle_deg": "85" if motion == "FOLD" else "90",
                    "packet_pitch_mm": "60" if motion == "FOLD" else None,
                    "hardware_kit_skus": selected_kits or common_kits,
                    "pass_through_hardware_kit_skus": pass_kits
                    if any(panel["pass_through"] for panel in panels)
                    else [],
                    "min_leaf_width_mm": "250",
                    "max_leaf_width_mm": "2200",
                    "min_leaf_height_mm": "250",
                    "max_leaf_height_mm": "3000",
                    "max_leaf_weight_kg": "300",
                    "starter_width_mm": width,
                    "starter_height_mm": height,
                }
            )

        if motion in ("LIFT_SLIDE", "PARALLEL_SLIDE", "SLIDE"):
            recipe(
                "A" if motion == "LIFT_SLIDE" else "XO",
                [
                    _panel("S1", track=0, plane="20", travel="RIGHT", fraction="0.5"),
                    _panel("S2", fixed=True, plane="65"),
                ],
                width="3000",
                height="2200",
            )
            if motion == "LIFT_SLIDE":
                recipe(
                    "C",
                    [
                        _panel("S1", fixed=True, share="0.25", plane="20"),
                        _panel(
                            "S2",
                            share="0.25",
                            track=0,
                            plane="20",
                            travel="LEFT",
                            fraction="0.25",
                            closing="RIGHT",
                        ),
                        _panel(
                            "S3",
                            share="0.25",
                            track=1,
                            plane="65",
                            travel="RIGHT",
                            fraction="0.25",
                            closing="LEFT",
                        ),
                        _panel("S4", fixed=True, share="0.25", plane="65"),
                    ],
                    width="4000",
                    height="2200",
                )
        elif motion == "FOLD":
            for scheme, groups in (
                ("3+0", [("L", 0, "LEFT"), ("L", 1, "LEFT"), ("L", 2, "LEFT")]),
                ("2+1", [("L", 0, "LEFT"), ("L", 1, "LEFT"), ("R", 0, "RIGHT")]),
            ):
                for passage in (False, True):
                    panels = [
                        _panel(
                            f"S{index + 1}",
                            share="0.3333333333333333333333333333"
                            if index < 2
                            else "0.3333333333333333333333333334",
                            fold_group=group,
                            fold_index=order,
                            stack_side=side,
                            pass_through=passage and index == 2,
                            closing="LEFT" if side == "RIGHT" else "RIGHT",
                        )
                        for index, (group, order, side) in enumerate(groups)
                    ]
                    recipe(
                        scheme,
                        panels,
                        width="2400",
                        height="2200",
                        suffix="PASO" if passage else "SIN-PASO",
                    )
        elif motion in ("PIVOT_V", "PIVOT_H"):
            recipe(
                "EJE-30",
                [
                    _panel(
                        "S1",
                        share="1",
                        pivot_fraction="0.30",
                        closing="BOTTOM" if motion == "PIVOT_H" else "RIGHT",
                    )
                ],
                width="1200",
                height="1400",
            )
        else:
            for balance, label in (("SPRING", "MUELLES"), ("COUNTERWEIGHT", "CONTRAPESOS")):
                balance_kits = kits(label, balance=balance)
                for double in (False, True):
                    recipe(
                        "DOBLE" if double else "SIMPLE",
                        [
                            _panel(
                                "S1",
                                track=0,
                                plane="20",
                                travel="DOWN",
                                fraction="0.5",
                                closing="BOTTOM",
                                balance=balance,
                            ),
                            _panel(
                                "S2",
                                fixed=not double,
                                track=1 if double else None,
                                plane="65",
                                travel="UP" if double else None,
                                fraction="0.5" if double else "0",
                                closing="BOTTOM",
                                balance=balance if double else None,
                            ),
                        ],
                        width="1200",
                        height="1800",
                        suffix=label,
                        selected_kits=balance_kits,
                    )
        cap = {
            "use": use,
            "movement": motion,
            "direction": "INWARD",
            "leaf_role": "SINGLE",
            "fixed_in_sash": False,
            "hinge_sides": ["NONE"],
            "hardware_kit_skus": [kit["sku"] for kit in params["available_hardware_kits"]],
            "handle_rule": {
                "vertical_reference": "CENTER",
                "default_height_mm": None,
                "minimum_from_top_mm": "100",
                "minimum_from_bottom_mm": "100",
                "closing_edge_offset_mm": "37.50",
                "source": SOURCE,
            },
            "source": SOURCE,
            "advanced_recipes": recipes,
        }
        params["opening_capabilities"] = [
            {
                "use": use,
                "movement": "FIXED",
                "direction": "INWARD",
                "leaf_role": "SINGLE",
                "fixed_in_sash": False,
                "hinge_sides": ["NONE"],
                "hardware_kit_skus": [],
                "handle_rule": None,
                "source": SOURCE,
            },
            cap,
        ]
        # Historical aliases remain their old families. Advanced authority is
        # carried by the recipes, never by adding synthetic alias limits.
        params["dimensional_limits"] = [
            rule for rule in params["dimensional_limits"] if rule["opening_type"] == "FIXED"
        ]
        records.append(record)
    return records
