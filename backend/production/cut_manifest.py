"""Read projections of a sealed cut plan; never a second manufacturing model."""

from decimal import Decimal

from documents.renderers import _piece_labels, _ROLE_ES, _role_name


def ordered_bars(plan: dict) -> list[dict]:
    return sorted((plan.get("bars") or {}).get("workshop_cut_plan") or [],
                  key=lambda item: int(item.get("bar_index") or 0))


def ordered_cuts(bar: dict) -> list[dict]:
    return sorted(bar.get("cuts") or [], key=lambda item: int(item.get("sequence") or 0))


def ordered_pieces(plan: dict) -> list[dict]:
    pieces = [cut for bar in ordered_bars(plan) for cut in ordered_cuts(bar)]
    for sheet in sorted(plan.get("sheets") or [], key=lambda item: int(item.get("sheet_index") or 0)):
        pieces.extend(sorted(sheet.get("placements") or [], key=lambda item: (
            Decimal(str(item.get("y_mm") or 0)), Decimal(str(item.get("x_mm") or 0)),
        )))
    return pieces


def next_piece_station(piece: dict, route: list[dict]) -> str:
    """Use the real route, respecting the material branch of the piece.

    A bead or infill joins the glazing station directly. Reinforcement joins
    its parent's fabrication after the steel cut, when that station exists.
    """
    role = _role_name(piece.get("role"))
    if role == "GLAZING_BEAD" or piece.get("width_mm") is not None:
        return next((step["label"] for step in route if step.get("code") == "GLAZE"),
                    "Sin dato · consulte la ruta de la OT")
    cut_code = "CUT_STEEL" if piece.get("source_kind") == "REINFORCEMENT" and any(
        step.get("code") == "CUT_STEEL" for step in route) else "CUT"
    index = next((index for index, step in enumerate(route) if step.get("code") == cut_code), None)
    return next((str(step["label"]) for step in route[index + 1:]
                 if step.get("code") not in ("CUT", "CUT_STEEL")),
                "Sin dato · consulte la ruta de la OT") if index is not None else "Sin dato · consulte la ruta de la OT"


def grouped_cuts(plan: dict) -> list[dict]:
    """Equal saw settings in first-appearance order, with every physical address."""
    groups: dict[tuple, dict] = {}
    for bar in ordered_bars(plan):
        for cut in ordered_cuts(bar):
            key = (bar.get("stock_authority_id"), bar.get("commercial_sku"),
                   bar.get("color"), cut.get("source_kind"), cut.get("role"),
                   *(Decimal(str(cut[field])) if cut.get(field) is not None else None
                     for field in ("length_mm", "angle_left", "angle_right", "sagitta_mm")))
            group = groups.setdefault(key, {
                "sku": bar.get("commercial_sku"), "color": bar.get("color"),
                "source_kind": cut.get("source_kind"), "role": cut.get("role"),
                "length_mm": cut.get("length_mm"), "angle_left": cut.get("angle_left"),
                "angle_right": cut.get("angle_right"), "pieces": [],
            })
            group["pieces"].append({"code": cut.get("piece_code"),
                "stable_id": cut.get("piece_stable_id"), "bar_index": bar.get("bar_index"),
                "sequence": cut.get("sequence"), "qr_payload": cut.get("piece_qr")})
    return [{**group, "quantity": len(group["pieces"])} for group in groups.values()]


def piece_context(snapshot: dict) -> dict[str, dict]:
    """Physical homes and sourced parents, read from the frozen facts."""
    labels = _piece_labels({"manufacturing": [], "positions": [], **snapshot})
    result = {}
    for fact in snapshot.get("manufacturing") or []:
        member_homes = {member.get("member_id"): member for member in fact.get("members") or []}
        relations = {}
        for relationship in fact.get("relationships") or []:
            relations.setdefault(relationship.get("source_id"), []).append(relationship)
        for kind, identity, entries in (
            ("PROFILE", "member_id", fact.get("members") or []),
            ("REINFORCEMENT", "reinforcement_id", fact.get("reinforcements") or []),
            ("INFILL", "infill_id", fact.get("infills") or []),
        ):
            for entry in entries:
                entity = entry.get(identity)
                parent = entry.get("parent_member_id")
                home = member_homes.get(parent, entry)
                role = _role_name((home.get("identity") or {}).get("role") or home.get("role"))
                # Beads belong to their frozen leaf/bay; never guess a frame
                # parent just because it occupies the same rectangle.
                targets = [relation.get("target_id") for relation in relations.get(entity, [])]
                parent_code = labels["member"].get(parent)
                if parent_code is None:
                    parent_code = next((labels["member"].get(target) or labels["infill"].get(target)
                                        or labels["leaf_fact"].get(target)
                                        for target in targets if labels["member"].get(target) or labels["infill"].get(target)
                                        or labels["leaf_fact"].get(target)), None)
                result[str(entity)] = {
                    "position_id": str(fact.get("position_id") or ""),
                    "position": labels["position"].get(fact.get("position_id")),
                    "unit_index": fact.get("repetition_index"),
                    "role_label": ("Refuerzo · " if kind == "REINFORCEMENT" else "")
                                  + (_ROLE_ES.get(role, "Sin dato") if kind != "INFILL" else
                                     ("Vidrio" if entry.get("kind") == "GLASS" else "Panel")),
                    "parent_code": parent_code,
                    "bay_code": labels["bay"].get(home.get("bay_id")),
                    "leaf_code": labels["leaf"].get(home.get("leaf_id")),
                    "composition": entry.get("composition"),
                    "width_mm": (entry.get("rect") or {}).get("width_mm"),
                    "height_mm": (entry.get("rect") or {}).get("height_mm"),
                    "technical_sku": entry.get("technical_sku"),
                    "kind": kind,
                }
    return result
