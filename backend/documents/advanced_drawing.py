"""Sourced plan points projected onto a document. No manufacturing formulas."""

from decimal import Decimal as D
from html import escape


def plan_annotations(
    leaves: list[dict], *, x: D, y: D, font: D, color: str, exterior: bool
) -> tuple[str, D, D]:
    out = []
    right, bottom = x, y
    groups = {}
    for leaf in leaves:
        if isinstance(leaf.get("advanced"), dict):
            groups.setdefault(leaf["bay_id"], []).append(leaf)
    for values in groups.values():
        points = [
            point
            for leaf in values
            for field in ("closed_plan", "open_plan", "open_plan_polygon")
            for point in leaf["advanced"].get(field, [])
        ]
        top = min(D(str(point["depth_mm"])) for point in points)
        low = max(D(str(point["depth_mm"])) for point in points)
        transform = f"translate({x * 2} 0) scale(-1 1)" if exterior else ""
        label = values[0]["advanced"]["recipe_name"] + " · planta"
        out.append(
            f'<text x="{x}" y="{y}" transform="{transform}" font-family="IBM Plex Sans" '
            f'font-size="{font}" fill="{color}">{escape(label)}</text>'
        )
        baseline = y + font * 2 - top
        for leaf in values:
            data = leaf["advanced"]
            for field, dashed in (
                ("closed_plan", True),
                ("open_plan", False),
                ("open_plan_polygon", False),
            ):
                values_points = data.get(field, [])
                if not values_points:
                    continue
                path = "".join(
                    f"{'M' if index == 0 else 'L'}{x + D(str(point['x_mm']))} "
                    f"{baseline + D(str(point['depth_mm']))}"
                    for index, point in enumerate(values_points)
                )
                if field == "open_plan_polygon":
                    path += "Z"
                dash = f' stroke-dasharray="{font / 3} {font / 3}"' if dashed else ""
                out.append(
                    f'<path data-engine-plan="{field}" d="{path}" fill="none" stroke="{color}" '
                    f'stroke-width="{font / 15}"{dash}/>'
                )
            if data.get("pivot_x_mm") is not None:
                out.append(
                    f'<circle data-engine-axis="true" cx="{x + D(str(data["pivot_x_mm"]))}" '
                    f'cy="{baseline + D(str(data["plane_offset_mm"]))}" r="{font / 8}" fill="{color}"/>'
                )
        right = max(
            right,
            *(x + D(str(point["x_mm"])) for point in points),
            x + font * D(len(label)) * D("0.65"),
        )
        bottom = baseline + low + font * 2
        y = bottom + font * 2
    return "".join(out), right, bottom
