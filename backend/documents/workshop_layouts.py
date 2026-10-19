"""Additional compositions of sealed workshop data (v1 06).

Same sealed revision payload as DOC-05, different purpose:

- «Corte · Lista compacta»: identical cuts together (length × angles × count)
  per profile, for batching at the saw on limited paper.
- «Corte · Por ventana»: each window's cuts together, for assembly.
- «Plano técnico» (DOC-03 · PLANO): one sheet per position with the dominant
  elevation in its declared view, hand/sense of opening, a technical table and
  the titleblock. No commercial price or customer data beyond the titleblock.
- «Pedido · Por obra»: the work's material needs grouped by kind, bars and
  remnants to buy — an internal preparation, never a supplier order.

Nothing is recalculated here: lengths, bars and remnants are the engine's.
"""

from __future__ import annotations

from decimal import Decimal
from html import escape

from documents.renderers import (
    _CATEGORY_ES, _ROLE_ES, _array, _cut_key, _cut_member_map, _dim, _location, _object,
    _opening_labels, _piece_labels, _position_svg, _product_caption, _revision_header,
    _short_id, _value,
)
from documents.repository import DocumentaryError

COMPACT_CSS = """
<style>
.compact-cuts { width: 100%; border-collapse: collapse; font-size: 8.25pt; }
.compact-cuts th { text-align: left; border-bottom: 0.75pt solid #161C1F; padding: 1mm 1mm; }
.compact-cuts td { border-bottom: 0.4pt solid #CDD5D6; padding: 0.8mm 1mm; }
.compact-cuts .num { text-align: right; font-family: 'IBM Plex Mono', monospace; }
.compact-group th { background: #EEF2F1; color: #161C1F; font-size: 8.75pt; text-transform: none; letter-spacing: 0; }
.window-head { font-size: 11pt; margin: 5mm 0 1.5mm; break-after: avoid; }
.work-needs td.num, .work-needs th.num { text-align: right; }
.work-needs { width: 100%; border-collapse: collapse; font-size: 9pt; margin-bottom: 4mm; }
.work-needs th { text-align: left; border-bottom: 0.75pt solid #161C1F; padding: 1.2mm 1mm; }
.work-needs td { border-bottom: 0.4pt solid #CDD5D6; padding: 1.2mm 1mm; }
.internal-note { border: 0.75pt dashed #465158; padding: 2mm 3mm; font-size: 8.75pt; }
</style>
"""


def _require_production(snapshot: dict) -> None:
    if snapshot.get("draft") is True:  # quick draft: stamped «Borrador», never stored
        return
    if snapshot.get("production_allowed") is not True:
        raise DocumentaryError("production_document_blocked")
    if snapshot.get("documentary_complete") is not True:
        raise DocumentaryError("manufacturing_document_incomplete")


def _groups(snapshot: dict) -> list[dict]:
    purchase = _object(snapshot.get("purchase_requirements"), "invalid_purchase_projection")
    return [_object(item, "invalid_stock_group") for item in _array(purchase.get("stock_groups"), "invalid_purchase_projection")]


def _cuts(group: dict) -> list[tuple[dict, dict]]:
    out = []
    for bar_value in _array(group.get("bars"), "invalid_stock_group"):
        bar = _object(bar_value, "invalid_cut_bar")
        for cut_value in _array(bar.get("cuts"), "invalid_cut_bar"):
            out.append((bar, _object(cut_value, "invalid_cut_piece")))
    return out


def _angles(cut: dict) -> str:
    return f"{_value(cut.get('angle_left'))}° / {_value(cut.get('angle_right'))}°"


def cut_compact(snapshot: dict) -> str:
    """Identical cuts together: the saw is set once per length and angle pair.
    The sequence per bar stays in «Secuencia»; this list is for batching."""
    _require_production(snapshot)
    labels = _piece_labels(snapshot)
    cut_map = _cut_member_map(snapshot, labels)
    body, _ = _revision_header(snapshot, "Corte · lista compacta", "DOC-05", workshop=True)
    body += COMPACT_CSS
    body += ('<table class="compact-cuts"><colgroup><col style="width:16%"><col style="width:16%"><col style="width:10%">'
             '<col style="width:34%"><col style="width:24%"></colgroup><thead><tr><th class="num">Largo mm</th><th>Ángulos</th>'
             '<th class="num">Cant.</th><th>Piezas</th><th>Ventanas</th></tr></thead><tbody>')
    for group in _groups(snapshot):
        kind = _CATEGORY_ES.get(_value(group.get("source_kind")), _value(group.get("source_kind")))
        bars = [_object(item, "invalid_cut_bar") for item in _array(group.get("bars"), "invalid_stock_group")]
        rests = " · ".join(f'{_value(bar.get("remainder_mm"))}' for bar in bars if bar.get("remainder_mm") is not None)
        body += (f'<tr class="compact-group"><th colspan="5">{escape(_value(group.get("purchasing_sku")))} · {escape(kind)} · '
                 f'{escape(_value(group.get("purchased_bar_count")))} barras de {escape(_value(group.get("stock_length_mm")))} mm'
                 f'{f" · sobrantes {escape(rests)} mm" if rests else ""}</th></tr>')
        same: dict[tuple, dict] = {}
        for _, cut in _cuts(group):
            key = (Decimal(str(cut.get("length_mm"))), _angles(cut))
            entry = same.setdefault(key, {"count": 0, "pieces": [], "windows": []})
            entry["count"] += 1
            piece = cut_map.get(_cut_key(cut), _short_id(cut.get("piece_id")))
            window = labels["position"].get(cut.get("source_position_id"), _short_id(cut.get("source_position_id")))
            if piece not in entry["pieces"]:
                entry["pieces"].append(piece)
            if window not in entry["windows"]:
                entry["windows"].append(window)
        for (length, angles), entry in sorted(same.items(), key=lambda item: item[0][0], reverse=True):
            body += (f'<tr><td class="num">{escape(_value(length))}</td><td>{escape(angles)}</td>'
                     f'<td class="num">{entry["count"]}</td><td>{escape(", ".join(entry["pieces"]))}</td>'
                     f'<td>{escape(", ".join(entry["windows"]))}</td></tr>')
    return body + "</tbody></table></main>"


def cut_by_window(snapshot: dict) -> str:
    """Every cut of each window together, for assembly: the operator collects
    one window's pieces without reading the whole bar plan."""
    _require_production(snapshot)
    labels = _piece_labels(snapshot)
    cut_map = _cut_member_map(snapshot, labels)
    body, _ = _revision_header(snapshot, "Corte · por ventana", "DOC-05", workshop=True)
    body += COMPACT_CSS
    by_window: dict[str, list[tuple[dict, dict, dict]]] = {}
    order: list[str] = []
    for group in _groups(snapshot):
        for bar, cut in _cuts(group):
            window = labels["position"].get(cut.get("source_position_id"), _short_id(cut.get("source_position_id")))
            if window not in by_window:
                by_window[window] = []
                order.append(window)
            by_window[window].append((group, bar, cut))
    positions = {str(item.get("id")): item for item in snapshot.get("positions") or [] if isinstance(item, dict)}
    for window in order:
        items = by_window[window]
        position = positions.get(str(items[0][2].get("source_position_id")), {})
        size = (f' · {escape(_value(position.get("width_mm")))} × {escape(_value(position.get("height_mm")))} mm'
                if position.get("width_mm") else "")
        place = f' · {escape(_value(position.get("location_tag")))}' if position.get("location_tag") else ""
        body += (f'<h2 class="window-head">{escape(window)}{place}{size}</h2>'
                 '<table class="compact-cuts"><colgroup><col style="width:22%"><col style="width:22%"><col style="width:20%">'
                 '<col style="width:14%"><col style="width:12%"><col style="width:10%"></colgroup><thead><tr><th>Pieza</th><th>Ubicación</th>'
                 '<th>Material</th><th class="num">Largo mm</th><th>Ángulos</th><th class="num">Barra</th></tr></thead><tbody>')
        for group, bar, cut in sorted(items, key=lambda item: (_location(labels, item[2].get("bay_id"), item[2].get("leaf_id")), -Decimal(str(item[2].get("length_mm"))))):
            body += (f'<tr><td>{escape(cut_map.get(_cut_key(cut), _short_id(cut.get("piece_id"))))}</td>'
                     f'<td>{escape(_location(labels, cut.get("bay_id"), cut.get("leaf_id")))}</td>'
                     f'<td>{escape(_value(cut.get("workshop_sku") or group.get("purchasing_sku")))}</td>'
                     f'<td class="num">{escape(_value(cut.get("length_mm")))}</td><td>{escape(_angles(cut))}</td>'
                     f'<td class="num">{escape(_value(bar.get("bar_index")))}</td></tr>')
        body += "</tbody></table>"
    return body + "</main>"


def purchase_by_work(snapshot: dict) -> str:
    _require_production(snapshot)
    body, _ = _revision_header(snapshot, "Pedido por obra · preparación interna", "DOC-05", workshop=True)
    body += COMPACT_CSS
    body += ('<p class="internal-note">Documento interno para preparar el abastecimiento de esta obra. '
             'No es una orden de compra: los pedidos a proveedores se emiten por separado.</p>')
    by_kind: dict[str, list[dict]] = {}
    for group in _groups(snapshot):
        kind = _CATEGORY_ES.get(_value(group.get("source_kind")), _value(group.get("source_kind")))
        by_kind.setdefault(kind, []).append(group)
    for kind, groups in by_kind.items():
        body += (f'<h2>{escape(kind)}</h2><table class="work-needs"><thead><tr><th>Material</th>'
                 '<th class="num">Largo barra mm</th><th class="num">Barras</th><th class="num">Piezas</th>'
                 '<th class="num">Retazos reutilizables</th></tr></thead><tbody>')
        for group in groups:
            bars = [_object(item, "invalid_cut_bar") for item in _array(group.get("bars"), "invalid_stock_group")]
            pieces = sum(len(_array(bar.get("cuts"), "invalid_cut_bar")) for bar in bars)
            reusable = sum(1 for bar in bars if bar.get("remainder_reusable"))
            body += (f'<tr><td>{escape(_value(group.get("purchasing_sku")))}</td>'
                     f'<td class="num">{escape(_value(group.get("stock_length_mm")))}</td>'
                     f'<td class="num">{escape(_value(group.get("purchased_bar_count")))}</td>'
                     f'<td class="num">{pieces}</td><td class="num">{reusable}</td></tr>')
        body += "</tbody></table>"
    total_bars = sum(Decimal(str(group.get("purchased_bar_count") or 0)) for group in _groups(snapshot))
    body += f'<p>Total de barras de la obra: <strong>{escape(str(total_bars))}</strong></p>'
    return body + "</main>"


PLAN_CSS = """
<style>
.plan-sheet { break-after: page; }
.plan-sheet:last-child { break-after: auto; }
.plan-sheet h2 { margin: 2mm 0 1mm; font-size: 12pt; }
.plan-meta { margin: 0 0 3mm; color: #465158; font-size: 9.5pt; }
.plan-figure { text-align: center; margin: 2mm 0 3mm; }
.plan-figure > div { display: inline-block; max-width: 100%; }
.plan-figure svg { width: 100%; max-height: 120mm; }
.plan-view { font-size: 9.5pt; color: #465158; margin: 0 0 3mm; }
.plan-table { width: 100%; border-collapse: collapse; font-size: 9.5pt; }
.plan-table th { text-align: left; width: 32%; font-weight: 600; padding: 1.2mm 1mm;
  border-bottom: 0.4pt solid #CDD5D6; vertical-align: top; }
.plan-table td { padding: 1.2mm 1mm; border-bottom: 0.4pt solid #CDD5D6; }
.plan-table .num { font-family: 'IBM Plex Mono', monospace; }
</style>
"""


def technical_plan(snapshot: dict) -> str:
    """Technical drawing of the sealed revision: one sheet per position."""
    _require_production(snapshot)
    positions = [_object(item, "invalid_frozen_position")
                 for item in _array(snapshot.get("positions"), "invalid_frozen_revision_snapshot")]
    facts = [_object(item, "invalid_manufacturing_fact")
             for item in _array(snapshot.get("manufacturing"), "invalid_frozen_revision_snapshot")]
    body, _ = _revision_header(snapshot, "Plano técnico", "DOC-03", workshop=True)
    body += PLAN_CSS
    for position in positions:
        index = position.get("position_index")
        own = [fact for fact in facts if fact.get("position_index") == index]
        profiles: dict[tuple[str, str], int] = {}
        handles = 0
        infills: list[str] = []
        for fact in own[:1]:  # one repetition describes the unit; quantity is stated apart
            for member in _array(fact.get("members"), "invalid_manufacturing_fact"):
                member = _object(member, "invalid_manufacturing_member")
                role = _value(_object(member.get("identity"), "invalid_member_identity").get("role"))
                key = (_ROLE_ES.get(role, role), _value(member.get("workshop_sku")))
                profiles[key] = profiles.get(key, 0) + 1
            handles += len(_array(fact.get("handles"), "invalid_manufacturing_fact"))
            for infill in _array(fact.get("infills"), "invalid_manufacturing_fact"):
                composition = _value(_object(infill, "invalid_infill_fact").get("composition"))
                if composition not in infills:
                    infills.append(composition)
        tree = _object(position.get("parametric_tree"), "invalid_frozen_parametric_tree")
        openings = _opening_labels(tree) or ["Fijo"]
        location = _value(position.get("location_tag"))
        title = f"Posición {_value(index)}" + (f" · {location}" if location != "—" else "")
        rows = [
            ("Producto", escape(_product_caption(position))),
            ("Sistema", escape(_value(position.get("system_name")))),
            ("Medida total", f'<span class="num">{escape(_dim(position.get("width_mm")))} × '
                             f'{escape(_dim(position.get("height_mm")))} mm</span>'),
            ("Cantidad", f'<span class="num">{escape(_value(position.get("quantity")))}</span> un.'),
            ("Apertura y mano (vista interior)", escape(" · ".join(openings))),
            ("Perfiles por función", "<br>".join(
                f"{escape(role)} · {escape(sku)} · {count} pzs" for (role, sku), count in sorted(profiles.items()))
             or "Sin dato · faltan hechos de fabricación sellados"),
            ("Vidrio / relleno", escape(" · ".join(infills)) or "Sin dato"),
            ("Manillas", f"{handles}" if own else "Sin dato"),
        ]
        body += (
            '<section class="plan-sheet">'
            f"<h2>{escape(title)}</h2>"
            '<p class="plan-view">Vista interior declarada · cotas en mm · continuo: abre hacia '
            "el observador; discontinuo: se aleja; flecha: recorrido de la corredera.</p>"
            '<div class="plan-figure"><div style="width:170mm">'
            f"{_position_svg(position, dimensions=True)}</div></div>"
            '<table class="plan-table"><tbody>'
            + "".join(f"<tr><th>{label}</th><td>{value}</td></tr>" for label, value in rows)
            + "</tbody></table></section>"
        )
    return body + "</main>"
