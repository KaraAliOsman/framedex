"""Workshop documents the cutter, the glazier and the assembler read (P12f).

Same sealed revision as the technical matrix (DOC-03), composed for people:

- «Orden de trabajo» (DOC-03 · OT): one sheet per window — its drawing with
  dimensions, and what to cut, reinforce, mount and glaze, each line with a box
  to tick. Pieces are named by what they are and where they go («Marco · arr ·
  aba»), never by an internal identifier.
- «Informe de vidrios» (DOC-03 · VIDRIOS): every glass per window, for the
  glazier or the supplier, with pieces, area and weight.
- «Listado de montaje» (DOC-03 · MONTAJE): the work's windows on a few sheets,
  each with its drawing and the assembly checks.

Nothing is recalculated: lengths, angles, glass sizes and quantities are the
engine's sealed results.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from html import escape

from documents.renderers import (
    _ROLE_ES, _array, _dim, _finish, _object, _opening_labels, _position_svg, _product_caption,
    _require_production, _revision_header, _value,
)
from documents.repository import DocumentaryError

SIDES = {"TOP": "arr", "BOTTOM": "aba", "LEFT": "izq", "RIGHT": "der", "CENTER": "centro",
         "THRESHOLD": "umbral"}
SIDE_ORDER = ("arr", "aba", "izq", "der", "centro", "umbral")
CATEGORY_ES = {"LOCK": "Cierre", "HINGE": "Bisagra", "HANDLE": "Manilla", "ROLLER": "Carro",
               "SEAL": "Sello", "DRAINAGE": "Desagüe", "CONSUMABLE": "Insumo", "OTHER": "Otro"}

CSS = """
<style>
.ot-sheet { break-after: page; }
.ot-sheet:last-child { break-after: auto; }
.ot-title { display: flex; align-items: baseline; gap: 3mm; margin: 1mm 0 0.5mm; }
.ot-title h2 { margin: 0; font-size: 13pt; }
.ot-title .ot-qty { font-size: 10pt; color: #465158; }
.ot-sub { margin: 0 0 3mm; font-size: 9pt; color: #465158; }
.ot-left { float: left; width: 58mm; }
.ot-right { margin-left: 64mm; }
.ot-clear { clear: both; }
.ot-figure svg { width: 100%; max-height: 86mm; }
.ot-facts { width: 100%; border-collapse: collapse; font-size: 8.75pt; margin-top: 2mm; }
main.workshop .ot-facts th { text-align: left; font-weight: 600; color: #465158; padding: 1mm 0; width: 40%;
  border-bottom: 0.4pt solid #DDE3E4; vertical-align: top; background: none; text-transform: none;
  letter-spacing: 0; font-size: 8.75pt; }
.ot-facts td { padding: 1mm 0; border-bottom: 0.4pt solid #DDE3E4; }
.ot-block { margin: 0 0 3.5mm; break-inside: avoid; }
.ot-block h3 { margin: 0 0 1mm; font-size: 9.5pt; letter-spacing: 0; color: #161C1F; }
.ot-table { width: 100%; border-collapse: collapse; font-size: 8.75pt; }
main.workshop .ot-table th { text-align: left; font-weight: 600; color: #465158; font-size: 8pt;
  border-bottom: 0.75pt solid #161C1F; padding: 0.8mm 1mm; background: none; text-transform: none;
  letter-spacing: 0; }
main.workshop .ot-table td { border-bottom: 0.4pt solid #DDE3E4; padding: 0.7mm 1mm; vertical-align: top; }
main.workshop .ot-table .num, main.workshop .ot-table th.num { text-align: right; font-family: 'IBM Plex Mono', monospace; white-space: nowrap; }
.ot-table .len { text-align: right; font-family: 'IBM Plex Mono', monospace; font-size: 10.5pt;
  font-weight: 600; white-space: nowrap; }
.ot-table .code { white-space: nowrap; font-family: 'IBM Plex Mono', monospace; font-size: 8.25pt; color: #465158; }
.ot-table .kit td { font-weight: 600; background: #F2F4F4; }
.box { display: inline-block; width: 3.2mm; height: 3.2mm; border: 0.75pt solid #161C1F; }
.ot-table .tick { width: 5mm; }
.ot-sign { width: 100%; border-collapse: collapse; margin-top: 5mm; font-size: 8.75pt; }
.ot-sign td { padding: 0 3mm 0 0; }
.ot-sign .line { border-bottom: 0.75pt solid #161C1F; height: 7mm; }
.glass-window { margin: 4mm 0 1mm; font-size: 10pt; break-after: avoid; }
.glass-total { margin-top: 4mm; font-size: 9.5pt; }
.glass-note { margin-top: 3mm; font-size: 9pt; color: #465158; }
.mount-grid { width: 100%; border-collapse: separate; border-spacing: 3mm; }
main.workshop .mount-card { width: 50%; vertical-align: top; border: 0.75pt solid #CDD5D6; padding: 3mm; break-inside: avoid; }
.mount-card h3 { margin: 0 0 1mm; font-size: 10pt; }
.mount-card p { margin: 0 0 1.5mm; font-size: 8.5pt; color: #465158; }
.mount-card svg { width: 100%; max-height: 52mm; }
.mount-checks { width: 100%; border-collapse: collapse; margin-top: 2mm; font-size: 7.75pt; }
main.workshop .mount-checks td { border: 0.5pt solid #CDD5D6; padding: 1mm 0.5mm; text-align: center;
  font-size: 7pt; white-space: nowrap; }
main.workshop .mount-grid td.mount-empty { border: none; }
</style>
"""


def _num(value: object) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as error:  # noqa: BLE001 - any malformed number is a sealed-data error
        raise DocumentaryError("invalid_frozen_revision_snapshot") from error


def _mm(value: object) -> str:
    return _dim(value)


def _angles(left: object, right: object) -> str:
    if left is None or right is None:
        return "recto"
    a, b = _num(left).normalize(), _num(right).normalize()
    return f"{a:f}° / {b:f}°"


def _positions(snapshot: dict) -> list[dict]:
    return [_object(item, "invalid_frozen_position")
            for item in _array(snapshot.get("positions"), "invalid_frozen_revision_snapshot")]


def _bom_by_position(snapshot: dict) -> dict[str, dict]:
    result = {}
    for item in _array(snapshot.get("bom"), "invalid_frozen_revision_snapshot"):
        item = _object(item, "invalid_frozen_bom")
        result[str(item.get("position_id"))] = _object(item.get("engine_result"), "invalid_frozen_bom")
    return result


def _first_fact(snapshot: dict, index: object) -> dict | None:
    for item in _array(snapshot.get("manufacturing"), "invalid_frozen_revision_snapshot"):
        fact = _object(item, "invalid_manufacturing_fact")
        if fact.get("position_index") == index and fact.get("repetition_index") in (1, None):
            return fact
    return None


def _sides(fact: dict | None) -> dict[tuple[str, str, str], list[str]]:
    """(role, sku, length) → sides where those pieces go, from the sealed unit."""
    sides: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    if fact is None:
        return sides
    for member in _array(fact.get("members"), "invalid_manufacturing_fact"):
        member = _object(member, "invalid_manufacturing_member")
        identity = _object(member.get("identity"), "invalid_member_identity")
        key = (str(identity.get("role")), str(member.get("workshop_sku")), str(_num(member.get("cut_length_mm"))))
        side = SIDES.get(str(identity.get("physical_member_slot")))
        if side and side not in sides[key]:
            sides[key].append(side)
    return sides


def _title(position: dict) -> str:
    location = _value(position.get("location_tag"))
    return f"Ventana {_value(position.get('position_index'))}" + (f" · {location}" if location != "—" else "")


def _glass_name(glass: dict) -> str:
    return _value(glass.get("glass_spec"))


def _work_order_sheet(snapshot: dict, position: dict, bom: dict) -> str:
    quantity = int(position.get("quantity") or 1)
    fact = _first_fact(snapshot, position.get("position_index"))
    sides = _sides(fact)
    tree = _object(position.get("parametric_tree"), "invalid_frozen_parametric_tree")
    openings = " · ".join(_opening_labels(tree)) or "Fijo"
    glasses = [_object(item, "invalid_frozen_bom") for item in bom.get("glasses") or []]
    compositions = sorted({_glass_name(item) for item in glasses}) or ["—"]
    facts = [
        ("Medida", f'<span class="num">{escape(_mm(position.get("width_mm")))} × {escape(_mm(position.get("height_mm")))} mm</span>'),
        ("Cantidad", f"{quantity} un."),
        ("Línea", escape(_value(position.get("system_name")))),
        ("Color", escape(_finish(position.get("color_interior"), position.get("color_exterior")))),
        ("Vidrio", escape(" · ".join(compositions))),
        ("Apertura", escape(openings)),
    ]
    left = (
        f'<div class="ot-figure">{_position_svg(position, dimensions=True, caption=False)}</div>'
        '<table class="ot-facts"><tbody>'
        + "".join(f"<tr><th>{label}</th><td>{value}</td></tr>" for label, value in facts)
        + "</tbody></table>"
    )
    blocks: list[str] = []

    rows = []
    for cut in bom.get("profile_cuts") or []:
        cut = _object(cut, "invalid_frozen_bom")
        role = str(cut.get("role"))
        key = (role, str(cut.get("sku")), str(_num(cut.get("length_mm"))))
        where = " · ".join(sorted(sides.get(key, []), key=lambda side: SIDE_ORDER.index(side) if side in SIDE_ORDER else 9))
        rows.append(
            '<tr><td class="tick"><span class="box"></span></td>'
            f"<td>{escape(_ROLE_ES.get(role, role.title()))} <span class=\"code\">{escape(_value(cut.get('sku')))}</span></td>"
            f"<td>{escape(where or '—')}</td>"
            f"<td>{escape(_angles(cut.get('angle_left'), cut.get('angle_right')))}</td>"
            f'<td class="num">{int(cut.get("qty") or 0) * quantity}</td>'
            f'<td class="len">{escape(_mm(cut.get("length_mm")))}</td></tr>'
        )
    if rows:
        blocks.append('<div class="ot-block"><h3>Perfiles</h3><table class="ot-table"><thead><tr><th></th>'
                      '<th>Pieza</th><th>Lados</th><th>Ángulos</th><th class="num">Cant.</th>'
                      '<th class="num">Largo mm</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")

    rows = []
    for item in bom.get("reinforcements") or []:
        item = _object(item, "invalid_frozen_bom")
        role = str(item.get("role"))
        rows.append(
            '<tr><td class="tick"><span class="box"></span></td>'
            f"<td>Acero de {escape(_ROLE_ES.get(role, role.title()).lower())} "
            f"<span class=\"code\">{escape(_value(item.get('reinforcement_sku')))}</span></td>"
            f'<td class="num">{int(item.get("qty") or 0) * quantity}</td>'
            f'<td class="len">{escape(_mm(item.get("length_mm")))}</td></tr>'
        )
    if rows:
        blocks.append('<div class="ot-block"><h3>Refuerzos · corte recto</h3><table class="ot-table"><thead><tr><th></th>'
                      '<th>Acero</th><th class="num">Cant.</th><th class="num">Largo mm</th>'
                      "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>")

    rows = []
    for kit in bom.get("hardware_items") or []:
        kit = _object(kit, "invalid_frozen_bom")
        kits = int(kit.get("qty") or 1) * quantity
        rows.append(f'<tr class="kit"><td class="tick"><span class="box"></span></td>'
                    f'<td colspan="2">{escape(_value(kit.get("name")))}</td><td class="num">{kits}</td></tr>')
        for component in kit.get("contents") or []:
            component = _object(component, "invalid_frozen_bom")
            amount = _num(component.get("qty")) * kits
            rows.append(
                '<tr><td></td>'
                f"<td>{escape(_value(component.get('name')))}</td>"
                f"<td class=\"code\">{escape(_value(component.get('purchasing_sku') or component.get('sku')))}</td>"
                f'<td class="num">{amount.normalize():f}</td></tr>'
            )
    screws: dict[str, int] = defaultdict(int)
    for fitting in bom.get("fittings") or []:
        fitting = _object(fitting, "invalid_frozen_bom")
        screws[str(fitting.get("sku"))] += int(fitting.get("qty") or 0) * quantity
    for sku, amount in sorted(screws.items()):
        rows.append(f'<tr><td class="tick"><span class="box"></span></td><td>Tornillo de refuerzo</td>'
                    f'<td class="code">{escape(sku)}</td><td class="num">{amount}</td></tr>')
    if rows:
        blocks.append('<div class="ot-block"><h3>Herrajes y fijaciones</h3><table class="ot-table"><thead><tr><th></th>'
                      '<th>Componente</th><th>Código</th><th class="num">Cant.</th></tr></thead><tbody>'
                      + "".join(rows) + "</tbody></table></div>")

    rows = []
    for glass in glasses:
        rows.append(
            '<tr><td class="tick"><span class="box"></span></td>'
            f"<td>{escape(_glass_name(glass))}</td>"
            f'<td class="num">{quantity}</td>'
            f'<td class="len">{escape(_mm(glass.get("width_mm")))} × {escape(_mm(glass.get("height_mm")))}</td></tr>'
        )
    if rows:
        blocks.append('<div class="ot-block"><h3>Vidrios</h3><table class="ot-table"><thead><tr><th></th>'
                      '<th>Composición</th><th class="num">Cant.</th><th class="num">Ancho × alto mm</th>'
                      "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>")

    sign = ('<table class="ot-sign"><tbody><tr>'
            + "".join(f'<td>{label}<div class="line"></div></td>' for label in ("Cortó", "Armó", "Revisó", "Fecha"))
            + "</tr></tbody></table>")
    return (
        '<section class="ot-sheet">'
        f'<div class="ot-title"><h2>{escape(_title(position))}</h2>'
        f'<span class="ot-qty">{quantity} {"unidad" if quantity == 1 else "unidades"}</span></div>'
        f'<p class="ot-sub">{escape(_product_caption(position))} · {escape(_value(position.get("system_name")))}</p>'
        f'<div class="ot-left">{left}</div><div class="ot-right">{"".join(blocks)}</div>'
        f'<div class="ot-clear"></div>{sign}</section>'
    )


def work_order(snapshot: dict) -> str:
    """One sheet per window: drawing, what to cut, reinforce, mount and glaze."""
    _require_production(snapshot)
    boms = _bom_by_position(snapshot)
    body, _ = _revision_header(snapshot, "Orden de trabajo", "DOC-03", workshop=True)
    body += CSS
    for position in _positions(snapshot):
        body += _work_order_sheet(snapshot, position, boms.get(str(position.get("id")), {}))
    return body + "</main>"


def glass_report(snapshot: dict) -> str:
    """Every glass per window, with pieces, area and weight, for the glazier."""
    _require_production(snapshot)
    boms = _bom_by_position(snapshot)
    body, _ = _revision_header(snapshot, "Informe de vidrios", "Informe de vidrios", workshop=True)
    body += CSS
    pieces, area, weight = 0, Decimal("0"), Decimal("0")
    for position in _positions(snapshot):
        quantity = int(position.get("quantity") or 1)
        glasses = [_object(item, "invalid_frozen_bom") for item in boms.get(str(position.get("id")), {}).get("glasses") or []]
        if not glasses:
            continue
        rows = []
        for glass in glasses:
            glass_area = _num(glass.get("area_m2")) * quantity
            glass_weight = _num(glass.get("weight_kg") or 0) * quantity
            pieces += quantity
            area += glass_area
            weight += glass_weight
            rows.append(
                '<tr><td class="tick"><span class="box"></span></td>'
                f"<td>{escape(_glass_name(glass))}</td>"
                f'<td class="num">{quantity}</td>'
                f'<td class="len">{escape(_mm(glass.get("width_mm")))} × {escape(_mm(glass.get("height_mm")))}</td>'
                f'<td class="num">{glass_area.quantize(Decimal("0.01"))}</td>'
                f'<td class="num">{glass_weight.quantize(Decimal("0.1")) if glass.get("weight_kg") is not None else "—"}</td></tr>'
            )
        body += (
            f'<p class="glass-window"><strong>{escape(_title(position))}</strong> · '
            f'{escape(_mm(position.get("width_mm")))} × {escape(_mm(position.get("height_mm")))} mm · '
            f'{quantity} {"unidad" if quantity == 1 else "unidades"}</p>'
            '<div class="ot-block"><table class="ot-table"><thead><tr><th></th><th>Composición</th><th class="num">Cant.</th>'
            '<th class="num">Ancho × alto mm</th><th class="num">m²</th><th class="num">kg</th></tr></thead>'
            "<tbody>" + "".join(rows) + "</tbody></table></div>"
        )
    body += (
        f'<p class="glass-total"><strong>{pieces} {"pieza" if pieces == 1 else "piezas"}</strong> · '
        f'{area.quantize(Decimal("0.01"))} m² · {weight.quantize(Decimal("0.1"))} kg</p>'
        '<p class="glass-note">Verifique las medidas en obra antes de cortar el vidrio. '
        "Medidas del vidrio terminado, ancho × alto.</p>"
    )
    return body + "</main>"


def assembly_list(snapshot: dict) -> str:
    """The work's windows, two per row, each with its assembly checks."""
    _require_production(snapshot)
    boms = _bom_by_position(snapshot)
    body, _ = _revision_header(snapshot, "Listado de montaje", "Listado de montaje", workshop=True)
    body += CSS
    checks = ("Marco", "Hoja", "Acero", "Herraje", "Vidrio", "Junq.", "Sello", "Revisó")
    cards = []
    for position in _positions(snapshot):
        quantity = int(position.get("quantity") or 1)
        glasses = boms.get(str(position.get("id")), {}).get("glasses") or []
        composition = " · ".join(sorted({_value(_object(item, "invalid_frozen_bom").get("glass_spec")) for item in glasses})) or "Sin vidrio"
        cards.append(
            '<td class="mount-card">'
            f"<h3>{escape(_title(position))}</h3>"
            f'<p>{escape(_product_caption(position))} · {escape(_mm(position.get("width_mm")))} × '
            f'{escape(_mm(position.get("height_mm")))} mm · {quantity} un.</p>'
            f'<p>{escape(_finish(position.get("color_interior"), position.get("color_exterior")))} · {escape(composition)}</p>'
            f"{_position_svg(position, dimensions=True, caption=False)}"
            '<table class="mount-checks"><tbody><tr>'
            + "".join(f"<td>{label}<br><span class=\"box\"></span></td>" for label in checks)
            + "</tr></tbody></table></td>"
        )
    rows = ["<tr>" + "".join(cards[index:index + 2]) + ('<td class="mount-empty"></td>' if len(cards[index:index + 2]) == 1 else "") + "</tr>"
            for index in range(0, len(cards), 2)]
    body += '<table class="mount-grid"><tbody>' + "".join(rows) + "</tbody></table>"
    return body + "</main>"
