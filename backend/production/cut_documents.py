"""Compact workshop sheets and physical labels, projected from a live plan."""

from datetime import datetime, timezone
from decimal import Decimal
from html import escape

from documents.renderers import (
    _CSS, _COLOR_ES, _cldate, _pct, _ROLE_ES, _role_name, _survey_dim, _table,
)
from production.cut_manifest import grouped_cuts, ordered_bars, ordered_cuts, piece_context

CSS = """
@page { size: letter landscape; margin: 8mm 9mm 15mm;
  @bottom-center { content: element(titleblock); } }
body { font-size: 8.5pt; line-height: 1.2; }
.workshop { font-size: 8.5pt; }
h2 { font-size: 10pt; margin: 1.5mm 0; }
h3 { font-size: 9pt; margin: 0 0 1mm; }
.cut-cover { display: flex; justify-content: space-between; align-items: baseline;
 border-bottom: 1.5pt solid #075F5A; padding-bottom: 1.5mm; margin-bottom: 2mm; }
.cut-cover h1 { font-size: 14pt; margin: 0; white-space: nowrap; flex: 1; }
.cut-identity { display: flex; align-items: center; gap: 3mm; }
.cut-identity svg { width: 15mm; height: 15mm; }
.cut-convention { margin: 0 0 1.5mm; font-size: 8pt; }
.compact-bar { break-inside: avoid; margin: 0 0 2mm; padding-top: 1mm;
 border-top: 0.5pt solid #CDD5D6; }
.compact-bar svg { display: block; width: 100%; }
.compact-bar table { margin: 0; width: 100%; table-layout: fixed; }
table th { font-size: 8pt; padding: 0.4mm 1mm; background: #EEF2F1; color: #161C1F; }
table td { font-size: 8pt; padding: 0.4mm 1mm; overflow-wrap: break-word; }
.compact-bar td.dimension { font-size: 8pt; }
.compact-bar th:nth-child(1) { width: 5%; }
.compact-bar th:nth-child(2) { width: 21%; }
.compact-bar th:nth-child(3) { width: 20%; }
.compact-bar th:nth-child(4) { width: 20%; }
.compact-bar th:nth-child(5) { width: 12%; }
.compact-bar th:nth-child(6), .compact-bar th:nth-child(7) { width: 7%; }
.compact-bar th:nth-child(8) { width: 8%; }
.cut-balance, .cut-destination { font: 8pt 'IBM Plex Mono'; margin: 0.8mm 0 0; }
.cut-balance { color: #075F5A; }
.cut-balance.invalid { color: #7E1F19; }
.cut-section { break-before: page; }
.cut-section table { width: 100%; table-layout: fixed; }
.cut-section tr { break-inside: avoid; }
.cut-section p { font-size: 8.5pt; }
.technical-label { font-family: 'IBM Plex Mono'; font-variant-numeric: tabular-nums; }
.tb-label, .tb-value { font-size: 8pt; }
.sheet-layout { break-inside: avoid; }
.sheet-layout svg { max-height: 110mm; }
"""


def mm(value: object) -> str:
    return _survey_dim(value) if value is not None else "Sin dato"


def angle(value: object) -> str:
    return mm(value) + "°" if value is not None else "Sin dato"


def compact_bar_svg(bar: dict) -> str:
    """True longitudinal scale, constant 8.5pt text, no shrunk glyphs.

    Wide cuts show their physical code. Narrow cuts use sequence callouts in
    separate lanes; the table carries the complete code at the same sequence.
    A lane's occupied interval is never reused. Height grows with real density.
    """
    width = Decimal("258")
    stock = Decimal(str(bar["stock_length_mm"]))
    scale = width / stock
    font = Decimal("3")  # 8.5pt in physical mm
    labels = []
    boxes = []
    lanes: list[Decimal] = []
    cursor = Decimal(str(bar.get("head_trim_mm") or 0)) * scale
    for cut in ordered_cuts(bar):
        length = Decimal(str(cut["length_mm"])) * scale
        center = cursor + length / 2
        code = str(cut.get("piece_code") or "Sin dato")
        estimated = Decimal(len(code)) * font * Decimal("0.62")
        if estimated + 2 <= length:
            labels.append((code, center, Decimal("5"), False, center))
        else:
            code = str(cut.get("sequence") or "?")
            estimated = Decimal(len(code)) * font * Decimal("0.62")
            left = max(Decimal("0"), min(center - estimated / 2, width - estimated))
            lane = next((i for i, occupied in enumerate(lanes) if left >= occupied + 2), len(lanes))
            if lane == len(lanes):
                lanes.append(Decimal("-2"))
            lanes[lane] = left + estimated
            labels.append((code, left + estimated / 2, Decimal("12") + lane * 4, True, center))
        boxes.append((cursor, length, cut))
        cursor += length + Decimal(str(bar.get("kerf_mm") or 0)) * scale
    height = Decimal("9") + max(1, len(lanes)) * 4
    result = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
              f'width="{width}mm" height="{height}mm">']
    result.append(f'<rect x="0" y="1" width="{width}" height="7" fill="#EEF2F1" stroke="#465158" stroke-width="0.2"/>')
    for left, length, cut in boxes:
        result.append(f'<rect x="{left}" y="1" width="{length}" height="7" fill="#D4EFEA" stroke="#465158" stroke-width="0.2"/>')
        for x, value, direction in ((left, cut.get("angle_left"), 1), (left + length, cut.get("angle_right"), -1)):
            if value is not None and Decimal(str(value)) != 90:
                result.append(f'<path d="M{x} 1 l{direction * min(Decimal("2"), length / 2)} 0 l{-direction * min(Decimal("2"), length / 2)} 2 Z" fill="#075F5A"/>')
    for text, x, y, leader, source in labels:
        if leader:
            result.append(f'<path d="M{source} 8 L{x} {y - 2}" stroke="#465158" stroke-width="0.15" fill="none"/>')
        result.append(f'<text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="middle" '
                      f'font-family="IBM Plex Mono" font-size="{font}" fill="#161C1F">{escape(text)}</text>')
    result.append('</svg>')
    return ''.join(result)


def titleblock(order_code: str, fingerprint: str, title: str) -> str:
    return ('<div class="titleblock">'
            f'<div class="tb-cell tb-wide"><span class="tb-label">Orden de trabajo</span><span class="tb-value">{escape(order_code)} · {escape(title)}</span></div>'
            f'<div class="tb-cell"><span class="tb-label">Huella del plan</span><span class="tb-value">{escape(fingerprint[:16])}</span></div>'
            f'<div class="tb-cell"><span class="tb-label">Fecha</span><span class="tb-value">{escape(_cldate(datetime.now(timezone.utc).isoformat()))}</span></div>'
            '<div class="tb-cell"><span class="tb-label">Página</span><span class="tb-value pg"></span></div></div>')


def remnant_destination(bar: dict) -> str:
    remainder = Decimal(str(bar.get("remainder_mm") or 0))
    if remainder <= 0:
        return "Sin sobrante"
    if not bar.get("remainder_reusable"):
        return f"{mm(remainder)} mm → desecho; no vuelve a stock"
    remnant = bar.get("produced_remnant") or {}
    if not remnant.get("code"):
        return f"{mm(remainder)} mm → Sin dato · plan histórico sin dirección; reoptimiza antes de cortar"
    return f"{mm(remainder)} mm → {remnant['code']} · {remnant.get('rack_location') or 'Sin dato · declara destino'} · alta en stock al completar corte"


def compact_sheet_svg(sheet: dict) -> str:
    width = Decimal(str(sheet["sheet_width_mm"]))
    height = Decimal(str(sheet["sheet_height_mm"]))
    scale = min(Decimal("250") / width, Decimal("95") / height)
    w, h = width * scale, height * scale
    result = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">',
              f'<rect x="0" y="0" width="{w}" height="{h}" fill="#EEF2F1" stroke="#465158" stroke-width="0.2"/>']
    for index, piece in enumerate(sorted(sheet.get("placements") or [],key=lambda item:(
            Decimal(str(item.get("y_mm") or 0)),Decimal(str(item.get("x_mm") or 0)))),1):
        x,y = Decimal(str(piece["x_mm"])) * scale,Decimal(str(piece["y_mm"])) * scale
        pw,ph = Decimal(str(piece["width_mm"])) * scale,Decimal(str(piece["height_mm"])) * scale
        code = str(piece.get("piece_code") or "Sin dato")
        result.append(f'<rect x="{x}" y="{y}" width="{pw}" height="{ph}" fill="#D4EFEA" stroke="#075F5A" stroke-width="0.2"/>')
        if pw >= Decimal(len(code))*Decimal("1.9")+2 and ph >= 6:
            text = code
        elif pw >= Decimal(len(str(index)))*Decimal("1.9")+2 and ph >= 6:
            text = str(index)
        else:
            continue  # The full-size ledger below remains the label callout.
        result.append(f'<text x="{x+pw/2}" y="{y+ph/2}" text-anchor="middle" dominant-baseline="middle" '
            f'font-family="IBM Plex Mono" font-size="3.2" fill="#161C1F">{escape(text)}</text>')
    return ''.join(result)+'</svg>'


UNNESTED = {
    "no_declared_sheet": "Sin lámina declarada → Catálogo › Vidrios › Formatos: declara un formato compatible y vuelve a optimizar.",
    "piece_larger_than_usable_sheet": "Mayor que la lámina útil → Catálogo › Vidrios › Formatos: revisa el suministro; no reduzcas la medida fabricada.",
    "shaped_glass_outline": "Vidrio con forma → prepara la plantilla del contorno sellado para el vidriero.",
}


def pack_html(*, order: dict, optimization: dict, snapshot: dict, fingerprint: str,
              grouped: bool = False, **unused) -> str:
    from production.pieces import addressed_plan

    if any(not cut.get("piece_code") for bar in ordered_bars(optimization) for cut in ordered_cuts(bar)):
        optimization = addressed_plan(snapshot, optimization, order_id=order.get("id"))
    homes = piece_context(snapshot)
    order_code = str(order["order_code"])
    import segno
    from production.pieces import entity_address

    qr = segno.make(entity_address("/production", order=order.get("id", ""), code=order_code), error="m").svg_inline(border=4, scale=4, omitsize=True)
    body = titleblock(order_code, fingerprint, "Pack de corte")
    body += '<main class="workshop"><div class="cut-cover"><h1>Pack de corte</h1><div class="cut-identity"><span class="technical-label">'+escape(order_code)+'</span>'+qr+'</div></div>'
    if snapshot.get("is_demo") or any(pos.get("is_demo") for pos in snapshot.get("positions") or []):
        body += '<p>DEMO · Catálogo sintético, sin certificación.</p>'
    body += '<p class="cut-convention">Extremo inicial a la izquierda; alimentación →. Ángulos izq./der. desde arriba; marca de esquina = inglete. La tabla conserva la secuencia del motor.</p>'
    for bar in ordered_bars(optimization):
        source = "barra nueva" if bar.get("source") != "REMNANT" else f"retazo {bar.get('remnant_code') or 'Sin dato · falta dirección'}"
        kind = "Refuerzos" if all(cut.get("source_kind") == "REINFORCEMENT" for cut in ordered_cuts(bar)) else (
            "Junquillos" if all(_role_name(cut.get("role")) == "GLAZING_BEAD" for cut in ordered_cuts(bar)) else "Perfiles")
        body += f'<section class="compact-bar"><h3>{kind} · Barra {bar["bar_index"]} · {escape(str(bar.get("commercial_sku") or "Sin dato"))} · {escape(_COLOR_ES.get(str(bar.get("color")), str(bar.get("color") or "Sin dato")))} · {mm(bar["stock_length_mm"])} mm · {escape(source)} · {_pct(bar.get("yield_pct"))} %</h3>'
        body += compact_bar_svg(bar)
        data = []
        for cut in ordered_cuts(bar):
            home = homes.get(str(cut.get("piece_stable_id")), {})
            role = home.get("role_label") or _ROLE_ES.get(_role_name(cut.get("role")), "Sin dato")
            location = ' · '.join(str(value) for value in (home.get("position"), home.get("bay_code"), home.get("leaf_code")) if value)
            parent = home.get("parent_code")
            if parent:
                location += ' → '+parent
            notes = f"Flecha {mm(cut['sagitta_mm'])} mm" if cut.get("sagitta_mm") not in (None, "0", "0.00") else ""
            data.append([cut.get("sequence"), cut.get("piece_code"), role, location or "Sin dato · ubicación histórica",
                         mm(cut.get("length_mm")), angle(cut.get("angle_left")), angle(cut.get("angle_right")), notes])
        body += _table(["Sec.", "Pieza", "Función", "Destino / relación", "Corte mm", "∠ izq.", "∠ der.", "Obs."], data,
                       ["dimension", "technical-label", "", "", "dimension", "dimension", "dimension", ""])
        parts = sum((Decimal(str(cut["length_mm"])) for cut in ordered_cuts(bar)), Decimal(0))
        kerf = Decimal(str(bar.get("kerf_total_mm") or 0))
        trims = Decimal(str(bar.get("head_trim_mm") or 0)) + Decimal(str(bar.get("tail_trim_mm") or 0))
        remainder = Decimal(str(bar.get("remainder_mm") or 0))
        difference = Decimal(str(bar["stock_length_mm"])) - parts - kerf - trims - remainder
        closure = "cierra exacto" if difference == 0 else f"diferencia sin asignar {mm(difference)} mm"
        body += f'<p class="cut-balance{ " invalid" if difference else ""}">{mm(bar["stock_length_mm"])} mm = {mm(parts)} mm piezas + {mm(kerf)} mm disco + {mm(trims)} mm despuntes + {mm(remainder)} mm remanente — {closure}</p>'
        body += f'<p class="cut-destination">{escape(remnant_destination(bar))}</p></section>'
    if grouped:
        body += '<section class="cut-section"><h2>Cortes agrupados · sierra manual</h2><p>Agrupación por suministro, color, función, largo y ángulos exactos. Las direcciones B/Sec. conservan el orden del plan.</p>'
        body += _table(["Material / color", "Función", "Corte mm", "∠ izq. / der.", "Cant.", "Etiquetas / secuencia"], [
            [f"{group['sku']} · {_COLOR_ES.get(str(group['color']),str(group['color']))}", _ROLE_ES.get(_role_name(group['role']),"Sin dato"),
             mm(group['length_mm']), f"{angle(group['angle_left'])} / {angle(group['angle_right'])}",group['quantity'],
             ' · '.join(f"B{piece['bar_index']}/{piece['sequence']} → {piece['code']}" for piece in group['pieces'])]
            for group in grouped_cuts(optimization)], ["", "", "dimension", "dimension", "dimension", "technical-label"])
        body += '</section>'
    relations = []
    for bar in ordered_bars(optimization):
        for cut in ordered_cuts(bar):
            if cut.get("source_kind") == "REINFORCEMENT" or _role_name(cut.get("role")) == "GLAZING_BEAD":
                home = homes.get(str(cut.get("piece_stable_id")), {})
                relations.append([cut.get("piece_code"),home.get("role_label") or "Sin dato",
                    home.get("parent_code") or "Sin dato · relación histórica no declarada",
                    f"B{bar['bar_index']}/{cut.get('sequence')}",mm(cut.get("length_mm"))])
    if relations:
        body += '<section class="cut-section"><h2>Refuerzos y junquillos · relación física</h2>'
        body += _table(["Pieza", "Función", "Pieza / paño padre", "Barra / sec.", "Corte mm"],relations,
                       ["technical-label", "", "technical-label", "technical-label", "dimension"])
        body += '</section>'
    # Scope glazing by the OT's position, not every sibling in the revision.
    positions = {str(cut.get("source_position_id")) for bar in ordered_bars(optimization) for cut in ordered_cuts(bar) if cut.get("source_position_id")}
    if order.get("payload"):
        positions.add(str(order["payload"].get("position_id")))
    from documents.renderers import _piece_labels

    infill_codes = _piece_labels(snapshot)["infill"]
    glasses = [[infill_codes.get(entity),home.get("position") or "Sin dato",home.get("unit_index"),
                f"{mm(home.get('width_mm'))} × {mm(home.get('height_mm'))} mm",home.get("composition") or "Sin dato · declara composición",1]
               for entity,home in homes.items() if home["kind"] == "INFILL"
               and (not positions or home["position_id"] in positions)]
    if glasses or optimization.get("unnested") or optimization.get("sheets"):
        body += '<section class="cut-section"><h2>Vidrios y paneles</h2>'
        body += _table(["Pieza", "Posición", "Unidad", "Medidas del motor", "Composición", "Cant."],glasses,
                       ["technical-label", "", "dimension", "dimension", "", "dimension"])
        if optimization.get("unnested"):
            body += '<h2>Piezas no ubicadas · qué falta</h2>' + _table(["Pieza / material", "Medidas", "Causa y acción"], [[
                item.get('group'),f"{mm(item.get('width_mm'))} × {mm(item.get('height_mm'))} mm",
                UNNESTED.get(item.get('reason'),"Sin dato · revisa la autoridad de suministro en Catálogo y vuelve a optimizar.")]
                for item in optimization['unnested']], ["", "dimension", ""])
        for sheet in optimization.get("sheets") or []:
            origin = ("retazo " + str(sheet.get("remnant_code") or "Sin dato · falta dirección")
                      if sheet.get("source") == "REMNANT" else "lámina nueva")
            body += f'<div class="sheet-layout"><h3>Lámina {sheet["sheet_index"]} · {escape(str(sheet.get("purchasing_sku")))} · {mm(sheet["sheet_width_mm"])} × {mm(sheet["sheet_height_mm"])} mm · {escape(origin)} · {_pct(sheet.get("yield_pct"))} %</h3>'
            body += compact_sheet_svg(sheet)
            placements = sorted(sheet.get("placements") or [],key=lambda item:(
                Decimal(str(item.get("y_mm") or 0)),Decimal(str(item.get("x_mm") or 0))))
            body += _table(["Sec.","Pieza","X mm","Y mm","Medidas mm","Giro"],[[
                index,piece.get("piece_code"),mm(piece["x_mm"]),mm(piece["y_mm"]),
                f"{mm(piece['width_mm'])} × {mm(piece['height_mm'])}","Sí" if piece.get("rotated") else "No"]
                for index,piece in enumerate(placements,1)],
                ["dimension","technical-label","dimension","dimension","dimension",""])
            if sheet.get("produced_remnant_labels"):
                body += _table(["Retazo recuperable", "Medidas mm", "Destino al completar corte"], [[
                    entry["code"], f"{mm(entry['width_mm'])} × {mm(entry['height_mm'])}",
                    entry.get("rack_location") or "Sin dato · declare destino en Ajustes"]
                    for entry in sheet["produced_remnant_labels"]], ["technical-label","dimension",""])
            elif sheet.get("produced_remnants"):
                body += '<p>Retazos recuperables sin dirección histórica · vuelva a optimizar antes de cortar.</p>'
            body += '<p>Los sobrantes no recuperables se descartan; no vuelven a stock.</p>'
            body += '</div>'
        body += '</section>'
    body += '</main>'
    return '<!doctype html><html lang="es-CL"><head><meta charset="utf-8"><style>'+_CSS+CSS+'</style></head><body>'+body+'</body></html>'
