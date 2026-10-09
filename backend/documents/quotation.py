"""DOC-01 sheet composition. The engine projects money; this module lays it out."""

from decimal import Decimal, ROUND_HALF_UP
from html import escape
import json

from dekopen_engine.glass_composition import GlassProduct, format_glass_notation
from dekopen_engine.drawing import dimension_chains
from dekopen_engine.geometry import resolved_sliding_layout
from dekopen_engine.models import NodeType
from dekopen_engine.quotation import payment_amounts, quotation_line, quotation_summary, representative_index
from documents.preferences import ACCENTS, PAPERS, document_preferences
from documents.repository import DocumentaryError
from engine_api.adapter import parse_parametric_node

# Shared drawing/formatting primitives. renderers imports this module lazily.
from documents.renderers import (
    _brand_block, _cldate, _discount_label, _money, _num, _object, _opening_labels,
    _position_svg, _product_caption, _rev_display, _survey_dim, _value,
    _pt, finish_label,
)

CSS = """
@page { size: letter portrait; margin: 14mm 12mm 25mm; @bottom-center { content: element(quoteFooter); } }
.quote { font-size: 9.5pt; line-height: 1.35; }
.quote h1 { font-size: 24pt; line-height: 1.15; margin: 2mm 0 4mm; }
.quote h2 { font-size: 13pt; border-bottom: 1.5pt solid #075F5A; margin: 5mm 0 3mm; }
.quote h3 { margin: 0 0 2mm; font-size: 11pt; }
.quote p { margin: 1mm 0; }
.quote .q-num { font-family: 'IBM Plex Mono', monospace; font-variant-numeric: tabular-nums; }
.q-footer { position: running(quoteFooter); width: 191.9mm; border-top: 1.5pt solid #075F5A; padding-top: 2mm; font-size: 8.25pt; color: #465158; }
.q-footer-line { display: table; table-layout: fixed; width: 100%; }
.q-footer-line > span { display: table-cell; vertical-align: top; overflow-wrap: anywhere; }
.q-footer-line > span:last-child { width: 30%; text-align: right; }
.q-footer .q-legal { font: 8.25pt 'IBM Plex Sans', sans-serif; margin-top: 1mm; }
.q-head { position: relative; display: flex; justify-content: space-between; gap: 8mm; border-bottom: 1.5pt solid #075F5A; padding: 0 7mm 4mm 0; }
.q-head .brand { letter-spacing: 0; font-size: 16pt; }
.q-head .brand-sub { font-size: 8.25pt; letter-spacing: 0; }
.q-folio { text-align: right; font-size: 9pt; min-width: 62mm; }
.q-miter { position: absolute; right: 0; top: 0; width: 6mm; height: 6mm; }
.q-issuer { margin: 3mm 0 6mm; color: #465158; }
.q-client { display: flex; gap: 10mm; align-items: flex-start; margin: 6mm 0; }
.q-client > div { width: 50%; min-width: 0; }
.q-client-name { font-size: 17pt; font-weight: 600; line-height: 1.35; }
.quote dt, .q-label { font: 600 8.25pt 'IBM Plex Sans', sans-serif; color: #465158; }
.quote dl { margin: 0; }
.quote dd { margin: 0 0 1mm; }
.q-cover { break-after: page; }
.q-cover-drawing { margin: 5mm auto; width: 120mm; }
.q-cover-drawing svg { width: 100%; max-height: 78mm; }
.q-cover-long .q-cover-drawing svg { max-height: 55mm; }
.q-cover-total { border-top: 0.75pt solid #CDD5D6; padding-top: 4mm; display: flex; gap: 8mm; justify-content: space-between; }
.q-total { font: 700 20pt 'IBM Plex Mono', monospace; color: #075F5A; }
.q-overview { table-layout: fixed; font-size: 9pt; }
.q-overview thead { display: table-header-group; }
.quote th { font-size: 8.25pt; letter-spacing: 0; text-transform: none; padding: 2mm 1mm; }
.quote td { padding: 2mm 1mm; }
.quote table .q-num { text-align: right; }
.q-overview .q-dims { font-size: 8.25pt; white-space: normal; }
.q-overview td, .quote h1, .q-client-name, .q-spec, .q-position h3, .q-link { overflow-wrap: anywhere; }
.q-details { break-before: page; }
.q-position { break-inside: avoid; border-bottom: 0.75pt solid #CDD5D6; padding: 3mm 0; margin: 0; }
.q-position-body { display: flex; gap: 6mm; }
.q-figure { width: 72mm; flex: 0 0 72mm; }
.q-figure svg { width: 100%; max-height: 86mm; }
.q-spec { flex: 1; min-width: 0; }
.q-spec dl { display: block; }
.q-spec dt { display: inline; }
.q-spec dd { display: inline; margin: 0; }
.q-spec .q-spec-row { margin-bottom: 1mm; }
.q-position-price { display: flex; justify-content: flex-end; gap: 6mm; margin-top: 2mm; font-size: 9pt; }
.q-position-price strong { font-weight: 500; }
.q-compact .q-position { min-height: 68mm; }
.q-compact .q-figure { width: 58mm; flex-basis: 58mm; }
.q-compact .q-figure svg { max-height: 52mm; }
.q-compact .q-spec { font-size: 9pt; }
.q-dense .q-figure { width: 52mm; flex-basis: 52mm; }
.q-dense .q-figure svg { max-height: 46mm; }
.q-dense .q-position { min-height: 56mm; }
.q-dense .q-position { padding: 2mm 0; }
.q-dense .q-spec .q-spec-row { margin-bottom: 0.5mm; }
.q-dense .q-position h3 { font-size: 9.5pt; }
.q-dense .q-spec, .q-dense .q-position-price, .q-dense .q-overview { font-size: 8.25pt; }
.q-dense .q-overview td { padding: 1mm; }
.q-dense .q-plan { margin-top: 1mm; }
.q-legend { font-size: 8.25pt; color: #465158; margin-top: 2mm; }
.q-extra { font-size: 9pt; margin: 2mm 0; }
.q-extra caption { text-align: left; font-weight: 600; }
.q-extra td { padding: 1mm; }
.q-close { break-before: page; }
.q-commercial { display: flex; gap: 10mm; align-items: flex-start; }
.q-commercial > div { width: 50%; min-width: 0; }
.q-totals td { padding: 2mm 0; }
.q-totals .q-final td { border-top: 1.5pt solid #075F5A; font-size: 15pt; font-weight: 700; }
.q-terms p { margin: 0 0 3mm; }
.q-accept { break-inside: avoid; }
.q-signature { display: flex; gap: 6mm; margin: 4mm 0 8mm; }
.q-signature > div { flex: 1; padding-top: 9mm; border-bottom: 0.5pt solid #465158; position: relative; }
.q-signature span { position: absolute; top: 11mm; left: 0; font-size: 8.25pt; }
.q-online { display: flex; gap: 6mm; align-items: center; margin-top: 7mm; }
.q-online img { width: 28mm; height: 28mm; }
.q-online > div { flex: 1; min-width: 0; }
.q-link { font: 8.25pt 'IBM Plex Mono', monospace; color: #075F5A; }
.q-plan { margin-top: 3mm; font-size: 8.25pt; }
.q-plan svg { width: 100%; height: 16mm; }
.q-track { display: flex; gap: 2mm; align-items: center; margin: 1mm 0; }
.q-track-panels { display: flex; gap: 1mm; flex: 1; min-width: 0; }
.q-track-panel { flex: 1; min-width: 0; border-top: 0.4pt dotted #465158; }
.q-track-panel-active { border-top: 1.5pt solid #465158; }
.q-drawing-measures { font-size: 8.25pt; }
.q-drawing-measures p { margin: 1mm 0; }
"""


def stylesheet(snapshot: dict) -> str:
    org = snapshot.get("organization") or {}
    prefs = document_preferences(org.get("document_preferences"))
    width = {"LETTER": "191.9mm", "OFICIO": "192mm", "A4": "186mm"}[prefs["paper"]]
    return CSS.replace("191.9mm", width).replace("letter portrait", PAPERS[prefs["paper"]]).replace("#075F5A", ACCENTS[prefs["accent"]])


def known(value: object) -> str:
    if value is None or value == "" or value == "—" or value == "Sin dato":
        return ""
    return _value(value)


def spec_row(label: str, value: str, *, numeric: bool = False) -> str:
    if not value:
        return ""
    return f'<div class="q-spec-row"><dt>{escape(label)} · </dt><dd class="{"q-num" if numeric else ""}">{escape(value)}</dd></div>'


def field_specs(position: dict) -> str:
    tree = position.get("parametric_tree") or {}
    modules = (tree.get("assembly") or {}).get("modules") if tree.get("version") == "product-v2" else None
    roots = [module.get("tree") or {} for module in modules] if isinstance(modules, list) else [tree]
    rows = []
    for module_index, root in enumerate(roots, 1):
        module = modules[module_index - 1] if isinstance(modules, list) else position
        drawing = dimension_chains(parse_parametric_node(root), _num(module["width_mm"]), _num(module["height_mm"]))
        bays = []

        def walk(node):
            if not isinstance(node, dict):
                return
            if node.get("type") == "BAY":
                bays.append(node)
            for child in node.get("children") or []:
                walk(child)

        walk(root)
        for field_index, bay in enumerate(bays, 1):
            label = ", ".join(_opening_labels(bay)) or "Fijo"
            field_label = f"Campo {module_index}.{field_index}"
            if isinstance(modules, list) and len(modules) > 1:
                field_label = f"Módulo {module_index} · {field_label}"
            rows.append(spec_row(field_label, label))
            bounds = next((datum for datum in drawing.bays if datum.bay_id == bay.get("id")), None)
            if bounds is not None:
                rows.append(spec_row("Medidas del campo", f"{_survey_dim(bounds.width_mm)} × {_survey_dim(bounds.height_mm)} mm", numeric=True))
            product = bay.get("glass_product")
            if isinstance(product, dict):
                glass = GlassProduct.model_validate_json(json.dumps(product, default=str))
                description = format_glass_notation(glass.composition)
                if glass.synthetic:
                    description += " · DEMO"
                rows.append(spec_row("Vidrio", description))
                if glass.properties.ug is not None:
                    ug = glass.properties.ug
                    number = f'{ug.value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP):.2f}'.replace(".", ",")
                    rows.append(spec_row("Ug", f"{number} W/m²K · {ug.source}", numeric=True))
            elif known(bay.get("glass_spec")):
                rows.append(spec_row("Vidrio", known(bay["glass_spec"])))
            elif known(bay.get("infill_sku")):
                rows.append(spec_row("Relleno", "Panel declarado"))
    return "".join(rows)


def plan_figure(position: dict) -> str:
    """Use only the engine plan sealed at emission, never today's catalogue."""
    plan = position.get("drawing_plan")
    if not isinstance(plan, dict):
        return ""
    width, height = _num(plan["width_mm"]), _num(plan["height_mm"])
    left, bottom = _num(plan["min_x_mm"]), _num(plan["min_y_mm"])
    pad = width / Decimal("30")
    polygons = []
    for item in plan.get("modules") or []:
        points = " ".join(f'{_pt(_num(p["x_mm"]))},{_pt(-_num(p["y_mm"]))}' for p in item["corners"])
        polygons.append(f'<polygon points="{points}" fill="#E6F4F2" stroke="#465158" stroke-width="{_pt(width / 400)}"/>')
    for item in plan.get("couplings") or []:
        points = " ".join(f'{_pt(_num(p["x_mm"]))},{_pt(-_num(p["y_mm"]))}' for p in item["polygon"])
        polygons.append(f'<polygon points="{points}" fill="#CDD5D6" stroke="#465158" stroke-width="{_pt(width / 400)}"/>')
    svg = f'<svg data-drawing="sealed-plan" viewBox="{_pt(left-pad)} {_pt(-bottom-height-pad)} {_pt(width+2*pad)} {_pt(height+2*pad)}" xmlns="http://www.w3.org/2000/svg">{"".join(polygons)}</svg>'
    measures = plan.get("assembly_measures")
    dimensions = ""
    if measures:
        dimensions = '<p class="q-num">' + ' · '.join(
            f'{label} {_survey_dim(measures[key])} mm' for label,key in (
                ("Ancho desarrollado","developed_width_mm"),("Frente / cuerda","front_width_mm"),
                ("Proyección","projection_mm"),("Altura","height_mm"))) + '</p>'
    return f'<div class="q-plan"><p>Planta del conjunto · elevación desarrollada · datos sellados del motor</p>{svg}{dimensions}</div>'


def sliding_specs(position: dict) -> str:
    tree = position.get("parametric_tree") or {}
    modules = (tree.get("assembly") or {}).get("modules") if tree.get("version") == "product-v2" else None
    roots = [module.get("tree") or {} for module in modules] if isinstance(modules, list) else [tree]
    result = []
    def walk(current):
        if current.type is NodeType.BAY and (current.sliding_layout is not None or str(current.opening_type.value if current.opening_type else "").startswith("SLIDING")):
            layout = resolved_sliding_layout(current)
            rows = []
            for track in range(layout.tracks):
                strips = ''.join(f'<span class="q-track-panel{" q-track-panel-active" if panel.track == track else ""}">{"Hoja " + str(index+1) if panel.track == track else ""}</span>' for index, panel in enumerate(layout.panels))
                rows.append(f'<div class="q-track"><span class="q-num">Carril {track+1}</span><span class="q-track-panels">{strips}</span></div>')
            result.append('<div class="q-plan"><p>Planta de corredera · exterior</p>' + ''.join(rows) + '<p>Interior · orden de carriles: convención de dibujo</p></div>')
        for child in current.children:
            walk(child)
    for root in roots:
        walk(parse_parametric_node(root))
    return ''.join(result)


def extras_table(items: list, currency: str, *, prices: bool, base=None, caption="Extras incluidos") -> str:
    if not items:
        return ""
    cols = '<colgroup><col style="width:43%"><col style="width:17%"><col style="width:20%"><col style="width:20%"></colgroup>' if prices else '<colgroup><col style="width:70%"><col style="width:30%"></colgroup>'
    headings = '<th>Accesorio o servicio</th><th class="q-num">Cantidad</th>' + ('<th class="q-num">P. unit. neto</th><th class="q-num">Total neto</th>' if prices else '')
    rows = ''
    if prices and base is not None:
        rows += f'<tr><td>Base de la posición</td><td></td><td></td><td class="q-num">{escape(_money(base, currency))}</td></tr>'
    for item in items:
        unit = {"EA": "un.", "M": "m", "M2": "m²", "KG": "kg", "WINDOW": "vanos"}.get(str(item.get("unit")), "")
        name = known(item.get("name") or item.get("label")) + (" · DEMO" if item.get("synthetic") else "")
        qty = _survey_dim(item["quantity"]) if item.get("quantity") is not None else ""
        rows += f'<tr><td>{escape(name)}</td><td class="q-num">{escape(qty + " " + unit)}</td>'
        if prices:
            tariff, net = item.get("unit_price", item.get("selling_rate")), item.get("net", item.get("amount"))
            rows += f'<td class="q-num">{escape(_money(tariff, currency)) if tariff is not None else ""}</td><td class="q-num">{escape(_money(net, currency)) if net is not None else ""}</td>'
        rows += '</tr>'
        if prices and item.get("rounding") is not None and _num(item["rounding"]) != 0:
            rows += f'<tr><td colspan="4">Ajuste de redondeo incluido en el neto: <span class="q-num">{escape(_survey_dim(item["rounding"]))} {escape(currency)}</span></td></tr>'
    return f'<table class="q-extra"><caption>{escape(caption)}</caption>{cols}<thead><tr>{headings}</tr></thead><tbody>{rows}</tbody></table>'


def render(snapshot: dict, *, portal_url: str | None = None) -> str:
    project = _object(snapshot.get("project"), "invalid_frozen_revision_snapshot")
    positions = snapshot.get("positions")
    if not isinstance(positions, list):
        raise DocumentaryError("invalid_frozen_revision_snapshot")
    currency = str(project.get("currency") or "CLP")
    org = snapshot.get("organization") or {}
    prefs = document_preferences(org.get("document_preferences"))
    terms = project.get("commercial_terms") or {}
    result = (snapshot.get("pricing") or {}).get("result") or {}
    details = {str(item["position_index"]): item for item in result.get("line_detail") or []}
    line_values = {}
    for position in positions:
        if position.get("price_net") is None:
            continue
        detail = details.get(str(position["position_index"]), {})
        value = quotation_line(quantity=int(position["quantity"]), net=_num(position["price_net"]), currency=currency,
            original_unit=_num(detail["unit_price"]) if detail.get("unit_price") is not None else None,
            discount=_num(position.get("discount_pct") or "0"))
        line_values[str(position["position_index"])] = value
    revision = str(snapshot.get("revision") or "")
    if not revision.startswith("REV-"):
        revision = "REV-" + revision
    folio = f'COT-{known(project.get("code"))}-{revision}'
    date = _cldate(snapshot.get("sealed_at"))
    valid = _cldate(project["quotation_valid_until"]) if project.get("quotation_valid_until") else ""
    legal = " · ".join(value for value in [known(org.get("name")), "RUT " + known(org["tax_id"]) if known(org.get("tax_id")) else "", known(prefs.get("legal_footer"))] if value)
    fingerprint = str(snapshot.get("bom_hash") or "")[:12]
    footer = f'<footer class="q-footer"><div class="q-footer-line"><span class="q-num">{escape(folio)} · Rev. {escape(_rev_display(revision))}</span><span class="q-num">Página <span class="pg"></span></span></div><div class="q-footer-line q-legal"><span>{escape(legal)}</span><span class="q-num">Huella {escape(fingerprint)}</span></div></footer>'
    density = "q-dense q-compact" if len(positions) > 24 else "q-compact" if len(positions) > 3 else ""
    body = f'<main class="quote {density}">{footer}'
    mast = '<svg class="q-miter" viewBox="0 0 24 24"><path d="M0 0H24V24" fill="none" stroke="#075F5A" stroke-width="1.5"/><path d="M0 0L24 24" fill="none" stroke="#075F5A" stroke-width="1.5"/></svg>'
    cover_density = " q-cover-long" if len(known(project.get("client_name"))) > 70 else ""
    body += f'<section class="q-cover{cover_density}">' if len(positions) > 1 else '<section>'
    body += '<header class="q-head">' + _brand_block({**org, "brand_schema": 1}) + f'<div class="q-folio"><strong>Cotización</strong><br><span class="q-num">{escape(folio)}<br>Revisión {escape(_rev_display(revision))} · {escape(date)}</span></div>{mast}</header>'
    issuer = " · ".join(known(org.get(field)) for field in ("name", "tax_id", "giro", "brand_address", "brand_phone", "brand_email") if known(org.get(field)))
    body += f'<p class="q-issuer">{escape(issuer)}</p><h1>{escape(known(project.get("name")) or "Solución para su obra")}</h1>'
    client = ''.join(spec_row(label, known(project.get(field))) for label, field in [("RUT", "client_rut"), ("Giro", "client_giro"), ("Comuna", "client_comuna"), ("Dirección", "client_address"), ("Contacto", "client_email"), ("Teléfono", "client_phone"), ("Entrega", "delivery_address")])
    conditions = ''.join(spec_row(label, known(terms.get(field))) for label, field in [("Plazo", "delivery_text"), ("Instalación", "installation_text")])
    conditions += spec_row("Pago", known(project.get("payment_terms"))) + spec_row("Vigente hasta", valid)
    body += f'<div class="q-client"><div><p class="q-label">Preparado para</p><p class="q-client-name">{escape(known(project.get("client_name")))}</p><dl>{client}</dl></div><div><p class="q-label">Condiciones de la propuesta</p><dl>{conditions}</dl></div></div>'
    if len(positions) > 1:
        hero = positions[representative_index([(_num(item["width_mm"]), _num(item["height_mm"])) for item in positions])]
        body += f'<div class="q-cover-drawing">{_position_svg(hero, commercial=True, dimensions=True, dimension_font_divisor=Decimal("16"), include_sliding_plan=False)}</div>'
    if project.get("total_price_gross") is not None:
        body += f'<div class="q-cover-total"><div><span class="q-label">Total con impuesto · {escape(currency)}</span><p class="q-total">{escape(_money(project["total_price_gross"], currency))}</p></div><div><span class="q-label">Revisión emitida</span><p>Las especificaciones y los precios corresponden<br>a esta revisión de su cotización.</p></div></div>'
    body += '</section>'
    if positions:
        body += '<h2>Resumen de posiciones</h2><table class="q-overview"><colgroup>' + ''.join(f'<col style="width:{width}%">' for width in (4, 27, 16, 18, 5, 15, 15)) + '</colgroup><thead><tr><th>Pos.</th><th>Ubicación</th><th>Tipología</th><th>Ancho × Alto</th><th>Cant.</th><th>P. unit. neto</th><th>Total neto</th></tr></thead><tbody>'
        for position in positions:
            value = line_values.get(str(position["position_index"]))
            body += f'<tr><td class="q-num">{escape(str(position["position_index"]))}</td><td>{escape(known(position.get("location_tag")))}</td><td>{escape(_product_caption(position))}</td><td class="q-num q-dims">{escape(_survey_dim(position.get("width_mm")))} × {escape(_survey_dim(position.get("height_mm")))} mm</td><td class="q-num">{escape(str(position["quantity"]))}</td><td class="q-num">{escape(_money(value.unit_net, currency)) if value else ""}</td><td class="q-num">{escape(_money(value.net, currency)) if value else ""}</td></tr>'
        body += '</tbody></table>'
    body += '<section class="q-details"><h2>Detalle de la solución</h2>' if len(positions) > 1 else '<section><h2>Detalle de la solución</h2>'
    itemized = result.get("document_extra_prices", "ITEMIZED") == "ITEMIZED"
    body += '<p class="q-legend">Vista interior. Línea continua: abre hacia usted. Discontinua: se aleja. Flecha paralela: corredera. Las cotas representan el producto; el corte se realiza contra la orden de trabajo.</p>'
    for position in positions:
        detail = details.get(str(position["position_index"]), {})
        value = line_values.get(str(position["position_index"]))
        title = f'Posición {position["position_index"]} · {known(position.get("location_tag")) or _product_caption(position)}'
        specs = spec_row("Sistema", known(position.get("system_name")))
        specs += spec_row("Vista", "Interior")
        specs += spec_row("Medida total", f'{_survey_dim(position["width_mm"])} × {_survey_dim(position["height_mm"])} mm', numeric=True)
        finish = position.get("resolved_finish") or {}
        if finish:
            approximate = any((finish.get(face) or {}).get("approximate") for face in ("interior", "exterior"))
            specs += spec_row("Acabado", finish_label(position.get("color_interior"), position.get("color_exterior"), finish) + (" · tono aproximado" if approximate else ""))
        else:
            for face, label in [("interior", "Color interior"), ("exterior", "Color exterior")]:
                raw = position.get("color_" + face)
                specs += spec_row(label, {"WHITE": "Blanco", "FOILED": "Foliado"}.get(str(raw), ""))
        specs += field_specs(position)
        for item in position.get("commercial_hardware") or []:
            specs += spec_row("Manilla", " · ".join(known(item.get(field)) for field in ("handle_name", "handle_color") if known(item.get(field))))
            specs += spec_row("Opciones", "; ".join(item.get("options") or []))
        for index, item in enumerate((position.get("measurements") or {}).get("measurements") or [], 1):
            measured = item.get("result") or {}
            width, height = measured.get("width") or {}, measured.get("height") or {}
            if width.get("opening_mm") is not None and height.get("opening_mm") is not None:
                specs += spec_row(f"Vano · marco {index}", f'{_survey_dim(width["opening_mm"])} × {_survey_dim(height["opening_mm"])} mm', numeric=True)
        specs += spec_row("Cantidad", str(position["quantity"]) + " un.", numeric=True)
        body += f'<article class="q-position"><h3>{escape(title)}</h3><div class="q-position-body"><div class="q-figure">{_position_svg(position, commercial=True, dimensions=True, dimension_font_divisor=Decimal("12"), include_sliding_plan=False)}{plan_figure(position)}{sliding_specs(position)}</div><div class="q-spec"><dl>{specs}</dl></div></div>'
        body += extras_table(detail.get("sublines") or [], currency, prices=itemized, base=detail.get("base_net"))
        if value:
            discount = _num(position.get("discount_pct") or "0")
            body += '<div class="q-position-price">'
            if discount:
                body += f'<span>Precios incluyen descuento del {escape(_discount_label(discount))}</span>'
            body += f'<span>Unitario neto <strong class="q-num">{escape(_money(value.unit_net, currency))}</strong></span><span>Total posición <strong class="q-num">{escape(_money(value.net, currency))}</strong></span></div>'
            if value.adjustment:
                body += f'<p class="q-legend">Cantidad × unitario + ajuste de moneda <span class="q-num">{escape(_money(value.adjustment, currency))}</span> = total sellado.</p>'
        body += '</article>'
    body += '</section>'
    for alternative in snapshot.get("alternatives") or []:
        alternative_project = alternative["project"]
        alternative_currency = str(alternative_project["currency"])
        body += f'<section class="q-details"><h2>Alternativa · Revisión {escape(_rev_display(alternative["revision"]))}</h2><p><strong>No incluida en el total de esta propuesta.</strong> Corresponde a una revisión emitida anterior; se presenta para comparar.</p>'
        body += f'<p>Total de la alternativa · <span class="q-num">{escape(_money(alternative_project["total_price_gross"], alternative_currency))}</span></p>'
        for option in alternative["positions"]:
            body += f'<article class="q-position"><h3>Posición {option["position_index"]} · {escape(known(option.get("location_tag")))}</h3><div class="q-position-body"><div class="q-figure">{_position_svg(option, commercial=True, dimensions=True)}</div><div class="q-spec"><dl>{spec_row("Sistema", known(option.get("system_name")))}{field_specs(option)}{spec_row("Cantidad", str(option["quantity"]))}</dl><p>Total neto de posición · <span class="q-num">{escape(_money(option["price_net"], alternative_currency))}</span></p></div></div></article>'
        body += '</section>'
    body += '<section class="q-close"><h2>Resumen comercial</h2><div class="q-commercial"><div>'
    if project.get("total_price_net") is not None:
        # This projection never tries to repair inconsistent or incomplete
        # legacy snapshots by inventing original prices.
        summary = quotation_summary(list(line_values.values()), _num(project["total_price_net"])) if len(line_values) == len(positions) else None
        rows = ''
        if summary and summary.before_discount is not None:
            rows += f'<tr><td>Neto antes de descuento</td><td class="q-num">{escape(_money(summary.before_discount, currency))}</td></tr><tr><td>Descuento</td><td class="q-num">{escape(_money(summary.discount, currency))}</td></tr>'
        rows += f'<tr><td>Neto con descuento</td><td class="q-num">{escape(_money(project["total_price_net"], currency))}</td></tr>'
        pricing = snapshot.get("pricing") or {}
        tax_rate = (pricing.get("input_snapshot") or {}).get("rules", {}).get("tax_rate_pct")
        if tax_rate is None:
            tax_rate = pricing.get("request", {}).get("tax_rate_pct")
        tax_label = "Impuesto" if tax_rate is None else "IVA " + _discount_label(tax_rate)
        rows += f'<tr><td>{escape(tax_label)}</td><td class="q-num">{escape(_money(project["total_price_tax"], currency))}</td></tr><tr class="q-final"><td>Total · {escape(currency)}</td><td class="q-num">{escape(_money(project["total_price_gross"], currency))}</td></tr>'
        body += f'<table class="q-totals"><colgroup><col style="width:53%"><col style="width:47%"></colgroup><tbody>{rows}</tbody></table>'
        schedule = terms.get("payment_schedule") or []
        if schedule:
            amounts = payment_amounts(_num(project["total_price_gross"]), [_num(item["share"]) for item in schedule], currency)
            body += '<table><caption>Calendario de pagos</caption><colgroup><col style="width:62%"><col style="width:38%"></colgroup><thead><tr><th>Hito</th><th>Monto</th></tr></thead><tbody>'
            for item, amount in zip(schedule, amounts, strict=True):
                body += f'<tr><td>{escape(item["label"])} · <span class="q-num">{escape(_discount_label(item["share"]))}</span></td><td class="q-num">{escape(_money(amount, currency))}</td></tr>'
            body += '</tbody></table>'
    body += '</div><div class="q-terms">'
    for label, field in [("Plazo de entrega", "delivery_text"), ("Instalación", "installation_text"), ("Exclusiones", "exclusions"), ("Garantía", "warranty"), ("Jurisdicción", "jurisdiction")]:
        if known(terms.get(field)):
            body += f'<p><strong>{escape(label)}</strong><br>{escape(known(terms[field]))}</p>'
    for label, value in [("Forma de pago", project.get("payment_terms")), ("Vigencia", "Hasta el " + valid if valid else ""), ("Condiciones", project.get("notes_commercial"))]:
        if known(value):
            body += f'<p><strong>{escape(label)}</strong><br>{escape(known(value))}</p>'
    body += '</div></div>'
    body += extras_table(result.get("services") or [], currency, prices=itemized, caption="Servicios del proyecto incluidos en el neto")
    body += f'<div class="q-accept"><h2>Aceptación</h2><p>Al firmar acepta las especificaciones, condiciones y total de <span class="q-num">{escape(folio)}</span>.</p><div class="q-signature"><div><span>Nombre y RUT</span></div><div><span>Firma</span></div><div><span>Fecha</span></div></div>'
    if portal_url:
        import segno
        uri = segno.make(portal_url, micro=False, error="m").svg_data_uri(border=4, scale=8)
        body += f'<div class="q-online"><img src="{uri}" alt="QR de esta revisión"><div><strong>Acepta en línea</strong><p>Revise y apruebe esta misma revisión en el portal.</p><a class="q-link" href="{escape(portal_url, quote=True)}">{escape(portal_url)}</a></div></div>'
    body += '</div></section></main>'
    return body
