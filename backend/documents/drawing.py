"""Technical SVG annotations from pure engine drawing facts and sealed intent."""
from decimal import Decimal, ROUND_HALF_UP
from html import escape

from dekopen_engine.drawing import dimension_chains
from dekopen_engine.models import ParametricNode
from engine_api.adapter import parse_parametric_node


def annotations(tree: object, *, x: Decimal, y: Decimal, width: Decimal,
                height: Decimal, handles: list[dict[str, object]], color: str,
                exterior: bool = False, right_edge: Decimal | None = None,
                bottom_edge: Decimal | None = None, vertical_offset: int = 0,
                bottom_offset: int = 0, font_mm: Decimal | None = None,
                outer_top: Decimal | None = None, outer_height: Decimal | None = None,
                assembly_totals: tuple[Decimal, Decimal] | None = None) -> tuple[str, Decimal, Decimal, int, int]:
    node = parse_parametric_node(tree)
    facts = dimension_chains(node, width, height)
    out: list[str] = []
    right = width
    bottom = height
    font = font_mm if font_mm is not None else min(width, height) / Decimal("28")
    step = font * 3
    gutter_x = x + width if right_edge is None else right_edge
    gutter_y = y + height if bottom_edge is None else bottom_edge

    def text(tx: Decimal, ty: Decimal, label: str, *, rotate: bool = False,
             anchor: str = "start") -> None:
        nonlocal right, bottom
        transforms = f'translate({tx*2} 0) scale(-1 1)' if exterior else ''
        if rotate:
            transforms += f' rotate(-90 {tx} {ty})'
        elif exterior and anchor != "middle":
            anchor = "end" if anchor == "start" else "start"
        out.append(f'<text x="{tx}" y="{ty}" text-anchor="{anchor}" transform="{transforms}" '
                   f'font-family="IBM Plex Mono" font-size="{font}" fill="{color}">{escape(label)}</text>')
        right = max(right, tx - x + (font * 2 if rotate else font * len(label) * Decimal("0.65")))
        bottom = max(bottom, ty - y + font * 2)

    def line(a: Decimal, b: Decimal, at: Decimal, vertical: bool, label: str) -> None:
        nonlocal right, bottom
        tx, ty = (at - font / 2, (a + b) / 2) if vertical else ((a + b) / 2, at - font / 2)
        coords = f'x1="{at}" y1="{a}" x2="{at}" y2="{b}"' if vertical else f'x1="{a}" y1="{at}" x2="{b}" y2="{at}"'
        out.append(f'<line {coords} stroke="{color}" stroke-width="{font / 25}"/>')
        for mark in (a, b):
            px, py = (at, mark) if vertical else (mark, at)
            extension = (f'x1="{gutter_x}" y1="{mark}" x2="{at+font/3}" y2="{mark}"'
                         if vertical else f'x1="{mark}" y1="{gutter_y}" x2="{mark}" y2="{at+font/3}"')
            out.append(f'<line {extension} stroke="{color}" stroke-width="{font/40}"/>')
            out.append(f'<line x1="{px-font/5}" y1="{py+font/5}" x2="{px+font/5}" y2="{py-font/5}" '
                       f'stroke="{color}" stroke-width="{font/20}"/>')
        text(tx, ty, label + " mm", rotate=vertical, anchor="middle")

    def mm(value: Decimal) -> str:
        return f'{value.quantize(Decimal("1"), rounding=ROUND_HALF_UP):,}'.replace(',', '\u2009')

    v_levels = max([(chain.level + 1) * 2 for chain in facts.chains if chain.axis == "V"], default=0)
    h_levels = max([(chain.level + 1) * 2 for chain in facts.chains if chain.axis == "H"], default=0)
    for chain in facts.chains:
        vertical = chain.axis == "H"
        at = (gutter_x + step * (vertical_offset + chain.level * 2 + 1) if vertical
              else gutter_y + step * (bottom_offset + chain.level * 2 + 1))
        labels = [mm(segment.value_mm) + " mm" for segment in chain.segments]
        centers = [(segment.start_mm + segment.end_mm) / 2 for segment in chain.segments]
        stagger = len(centers) == 2 and abs(centers[1] - centers[0]) < font * (
            Decimal(len(labels[0]) + len(labels[1])) * Decimal("0.325") + Decimal("0.5"))
        for index, segment in enumerate(chain.segments):
            origin = y if vertical else x
            line(origin + segment.start_mm, origin + segment.end_mm,
                 at + step * index if stagger else at, vertical, mm(segment.value_mm))
    line(x, x + width, gutter_y + step * (bottom_offset + v_levels + 1), False, mm(width))
    silhouette_y = y if outer_top is None else outer_top
    silhouette_h = height if outer_height is None else outer_height
    line(silhouette_y, silhouette_y + silhouette_h, gutter_x + step * (vertical_offset + h_levels + 1), True, mm(silhouette_h))
    for index, leaf in enumerate(handles):
        handle = leaf.get("handle")
        if not isinstance(handle, dict):
            continue
        ly = y + Decimal(str(leaf["y_mm"]))
        line(ly + Decimal(str(handle["y_mm"])), ly + Decimal(str(leaf["height_mm"])),
             gutter_x + step * (vertical_offset + h_levels + 2 + index), True,
             mm(Decimal(str(handle["height_from_bottom_mm"]))))

    known_bays = {str(leaf.get("bay_id")).split("|")[-1] for leaf in handles}
    for index, datum in enumerate(facts.authored_handles):
        if datum.bay_id not in known_bays:
            line(y + datum.y_mm, y + datum.bottom_mm,
                 gutter_x + step * (vertical_offset + h_levels + 2 + len(handles) + index), True,
                 mm(datum.height_from_bottom_mm))
    nodes: dict[str, ParametricNode] = {}
    def collect(current: ParametricNode) -> None:
        nodes[current.id] = current
        for child in current.children:
            collect(child)
    collect(node)
    plan_y = gutter_y + step * (v_levels + 3 + bottom_offset)
    for bay in facts.bays:
        current = nodes[bay.bay_id]
        if current.sliding_layout is not None:
            layout = current.sliding_layout
            bx, bw = x + bay.x_mm, bay.width_mm
            text(bx, plan_y, "EXTERIOR")
            for track in range(layout.tracks):
                ty = plan_y + step * (track + 1)
                out.append(f'<line x1="{bx}" x2="{bx+bw}" y1="{ty}" y2="{ty}" '
                           f'stroke="{color}" stroke-width="{font/25}" stroke-dasharray="{font/4} {font/4}"/>')
                text(bx+bw+font, ty, f"Carril {track+1}")
                for index, panel in enumerate(layout.panels):
                    if panel.track == track:
                        start = bx + bw * index / len(layout.panels) + font / 5
                        end = bx + bw * (index + 1) / len(layout.panels) - font / 5
                        out.append(f'<line data-plan-slot="{escape(panel.slot)}" x1="{start}" x2="{end}" '
                                   f'y1="{ty}" y2="{ty}" stroke="{color}" stroke-width="{font/4}"/>')
            inside = plan_y + step * (layout.tracks + 1)
            text(bx, inside, "INTERIOR")
            for index, panel in enumerate(layout.panels):
                if panel.kind.value == "FIXED" and panel.track is None:
                    text(bx+bw*(Decimal(index)+Decimal("0.5"))/len(layout.panels), inside+step,
                         "Fijo · plano sin dato", anchor="middle")
            plan_y = inside + step * 3
    if any(nodes[bay.bay_id].sliding_layout for bay in facts.bays):
        text(x, plan_y, "Orden de carriles: convención de dibujo")
    next_vertical = vertical_offset + h_levels + 2 + len(handles) + len(facts.authored_handles)
    next_bottom = (int((plan_y - gutter_y) / step) + 2
                   if any(nodes[bay.bay_id].sliding_layout for bay in facts.bays)
                   else bottom_offset + v_levels + 2)
    if assembly_totals is not None:
        total_width, total_height = assembly_totals
        line(Decimal("0"), total_width, gutter_y + step * (next_bottom + 1), False, mm(total_width))
        line(Decimal("0"), total_height, gutter_x + step * (next_vertical + 1), True, mm(total_height))
        next_vertical += 2
        next_bottom += 2
    return "".join(out), right, bottom, next_vertical, next_bottom
