"""DOC-01 sheet composition. The engine projects money; this module lays it out."""

from decimal import Decimal, ROUND_HALF_UP
from html import escape
import json

from dekopen_engine.glass_composition import GlassProduct, format_glass_notation
from dekopen_engine.drawing import dimension_chains
from dekopen_engine.geometry import resolved_sliding_layout
from dekopen_engine.models import NodeType
from dekopen_engine.quotation import payment_amounts, quotation_line, quotation_summary, representative_index
from documents.preferences import ACCENTS, PAPERS, declared, document_preferences
from documents.repository import DocumentaryError
from engine_api.adapter import parse_parametric_node

# Shared drawing/formatting primitives. renderers imports this module lazily.
from documents.renderers import (
    _brand_block, _cldate, _discount_label, _money, _num, _object, _opening_labels,
    _position_svg, _product_caption, _rev_display, _survey_dim, _value,
    _pt, finish_label,
)

CSS = """
@page { size: letter portrait; margin: 14mm 14mm 25mm; @bottom-center { content: element(quoteFooter); } }
.quote { font-size: 9.5pt; line-height: 1.35; }
.quote h1 { font-size: 24pt; line-height: 1.15; margin: 2mm 0 4mm; }
.quote h2 { font-size: 13pt; border-bottom: 1.5pt solid #075F5A; margin: 5mm 0 3mm; }
.quote h3 { margin: 0 0 2mm; font-size: 11pt; }
.quote p { margin: 1mm 0; }
.quote .q-num { font-family: 'IBM Plex Mono', monospace; font-variant-numeric: tabular-nums; }
.q-footer { position: running(quoteFooter); width: 187.9mm; border-top: 1.5pt solid #075F5A; padding-top: 2mm; font-size: 8.25pt; color: #465158; }
.q-footer-line { display: table; table-layout: fixed; width: 100%; }
.q-footer-line > span { display: table-cell; vertical-align: top; overflow-wrap: anywhere; }
.q-footer-line > span:last-child { width: 30%; text-align: right; }
.q-footer .q-legal { font: 8.25pt 'IBM Plex Sans', sans-serif; margin-top: 1mm; }
.q-legal-id { white-space: nowrap; }
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

/* v1 06 — three compositions on one contract: Esencial (compact rows),
   Proyecto (grouped, larger drawings, hero band), Alternativas (comparison). */
.quote h1 { font-size: 18pt; line-height: 1.2; margin: 4mm 0 3mm; }
.q-head { align-items: flex-start; padding: 0 0 3mm; }
.q-folio { display: flex; flex-direction: column; align-items: flex-end; gap: 0.5mm; min-width: 50mm; }
.q-number { font-size: 15pt; font-weight: 600; }
.q-draft { border: 0.75pt dashed #B25E09; color: #7A3D05; padding: 2mm 3mm; margin: 0 0 3mm; font-size: 9pt; }
.q-intro p, .q-closing p { margin: 0 0 2mm; }
.q-hero { display: flex; gap: 8mm; align-items: center; border-top: 0.75pt solid #CDD5D6; border-bottom: 0.75pt solid #CDD5D6; padding: 4mm 0; margin: 4mm 0; break-inside: avoid; }
.q-hero-drawing { width: 80mm; flex: 0 0 80mm; }
.q-hero-drawing svg { width: 100%; max-height: 62mm; }
.q-hero-facts p { margin: 0 0 2mm; }
.q-figure { width: var(--q-figure, 60mm); flex: 0 0 var(--q-figure, 60mm); }
.q-index { display: inline-block; min-width: 6mm; color: #465158; font-weight: 500; }
.q-group { font-size: 10.5pt; margin: 5mm 0 1mm; color: #465158; }
.q-esencial .q-position { padding: 2mm 0; }
.q-esencial .q-figure svg { max-height: 34mm; }
.q-esencial .q-spec { font-size: 8.75pt; }
.q-esencial .q-details { break-before: auto; }
.q-esencial .q-close, .q-alternativas .q-close { break-before: auto; }
.q-position--compact h3 { font-size: 10pt; }
.q-proyecto .q-details { break-before: page; }
.q-options { break-inside: auto; }
.q-compare { break-inside: avoid; }
.q-options .q-figure svg { max-height: 34mm; }
.q-options .q-spec dl { columns: 2; column-gap: 6mm; }
.q-compare { width: 100%; margin: 2mm 0; }
.q-compare td, .q-compare th { padding: 2mm 1mm; border-bottom: 0.5pt solid #CDD5D6; }
.q-compare .q-main td { font-weight: 600; }
.q-schedule { width: 100%; margin-top: 3mm; }
.q-schedule caption { text-align: left; font-weight: 600; padding-bottom: 1mm; }
.q-terms-block { break-inside: avoid; }
.q-terms-block p { margin: 0 0 2.5mm; }
.q-notes { border-left: 1.5pt solid #075F5A; padding-left: 3mm; margin-top: 3mm; }
.q-link { font: 8.25pt 'IBM Plex Sans', sans-serif; }
/* Dirección final 04 — editorial base: 14 mm margins, body 10 pt, secondary
   data never below 9.5 pt. Layout and page breaks adapt; type does not shrink. */
.quote { font-size: 10pt; line-height: 1.4; }
.quote dt, .q-label, .quote th, .q-legend, .q-footer, .q-footer .q-legal, .q-overview .q-dims,
.q-plan, .q-drawing-measures, .q-link, .q-signature span, .q-head .brand-sub { font-size: 9.5pt; }
.q-esencial .q-spec, .q-compact .q-spec, .q-position-price, .q-overview, .q-extra, .q-folio,
.q-draft, .q-dense .q-spec, .q-dense .q-position-price, .q-dense .q-overview { font-size: 9.5pt; }
.q-dense .q-position h3 { font-size: 10pt; }
.q-details, .q-close, .q-proyecto .q-details { break-before: auto; }
.quote th.q-num { font-family: 'IBM Plex Sans', sans-serif; }
.q-kv { margin: 0 0 1mm; }
.q-kv dt { display: inline; margin-right: 1.5mm; }
.q-kv dd { display: inline; margin: 0; }
.q-client .q-total { font-size: 16pt; margin: 0 0 2mm; }
.q-client .q-client-name { margin: 0 0 2mm; }
.q-esencial .q-spec dl { columns: 2; column-gap: 6mm; }
.q-esencial .q-spec .q-spec-row { break-inside: avoid; }
.q-terms-block .q-terms-list { columns: 2; column-gap: 8mm; }
.q-terms-block .q-terms-list p { break-inside: avoid; }
.q-hero-types { margin: 0; padding: 0; list-style: none; }
.q-hero-types li { margin: 0 0 1mm; }
.q-accept h2 { margin-top: 4mm; }
.q-online { margin-top: 2mm; }
.q-online img { width: 24mm; height: 24mm; }
"""


def stylesheet(snapshot: dict) -> str:
    org = snapshot.get("organization") or {}
    prefs = document_preferences(org.get("document_preferences"))
    width = {"LETTER": "187.9mm", "OFICIO": "188mm", "A4": "182mm"}[prefs["paper"]]
    return CSS.replace("187.9mm", width).replace("letter portrait", PAPERS[prefs["paper"]]).replace("#075F5A", ACCENTS[prefs["accent"]])


def known(value: object) -> str:
    if value is None or value == "" or value == "—" or value in ("Sin dato", "Falta completar"):
        return ""
    return _value(value)


def spec_row(label: str, value: str, *, numeric: bool = False) -> str:
    if not value:
        return ""
    return f'<div class="q-spec-row"><dt>{escape(label)} · </dt><dd class="{"q-num" if numeric else ""}">{escape(value)}</dd></div>'


def field_specs(position: dict, *, authoritative_thermal: bool = False) -> str:
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
        single = len(roots) == 1 and len(bays) == 1
        for field_index, bay in enumerate(bays, 1):
            label = ", ".join(_opening_labels(bay)) or "Fijo"
            field_label = "Apertura" if single else f"Campo {module_index}.{field_index}"
            if isinstance(modules, list) and len(modules) > 1:
                field_label = f"Módulo {module_index} · {field_label}"
            rows.append(spec_row(field_label, label))
            bounds = next((datum for datum in drawing.bays if datum.bay_id == bay.get("id")), None)
            if bounds is not None and not single:
                rows.append(spec_row("Medidas del campo", f"{_survey_dim(bounds.width_mm)} × {_survey_dim(bounds.height_mm)} mm", numeric=True))
            product = bay.get("glass_product")
            if isinstance(product, dict):
                glass = GlassProduct.model_validate_json(json.dumps(product, default=str))
                description = format_glass_notation(glass.composition)
                if glass.synthetic:
                    description += " · DEMO"
                rows.append(spec_row("Vidrio", description))
                # New emissions use the reviewed, scoped evidence in their
                # sealed thermal annex. Preserve historical snapshots' layout.
                if glass.properties.ug is not None and not authoritative_thermal:
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
    return f'<div class="q-plan"><p>Planta del conjunto · elevación desarrollada · datos del motor de esta revisión</p>{svg}{dimensions}</div>'


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
        rows += f'<tr><td>Base de la ventana</td><td></td><td></td><td class="q-num">{escape(_money(base, currency))}</td></tr>'
    for item in items:
        unit = {"EA": "un.", "M": "m", "M2": "m²", "KG": "kg", "WINDOW": "ventanas"}.get(str(item.get("unit")), "")
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


TEMPLATES = ("ESENCIAL", "PROYECTO", "ALTERNATIVAS")
TEMPLATE_LABELS = {"ESENCIAL": "Esencial", "PROYECTO": "Proyecto", "ALTERNATIVAS": "Alternativas"}
BLOCKS = ("intro", "client", "hero", "summary", "positions", "alternatives",
          "commercial", "terms", "services", "acceptance", "closing")
# Positions and the commercial summary (totals, payment, validity) carry the
# offer itself: they can be restyled but never hidden.
REQUIRED_BLOCKS = {"positions", "commercial"}
DEFAULT_ORDER = {
    "ESENCIAL": ("intro", "client", "positions", "commercial", "terms", "services", "acceptance", "closing"),
    "PROYECTO": ("intro", "client", "hero", "summary", "positions", "commercial", "terms", "services", "acceptance", "closing"),
    "ALTERNATIVAS": ("intro", "client", "alternatives", "positions", "commercial", "terms", "services", "acceptance", "closing"),
}
MAX_TEXT = 2000


def resolve_layout(snapshot: dict, requested: str | None = None) -> dict:
    """Company design (document preferences) overridden by this work's draft
    composition, both sealed in the snapshot. Unknown keys are ignored."""
    org = snapshot.get("organization") or {}
    prefs = document_preferences(org.get("document_preferences"))
    project = snapshot.get("project") or {}
    company = prefs.get("quotation_layout") if isinstance(prefs.get("quotation_layout"), dict) else {}
    local = project.get("document_layout") if isinstance(project.get("document_layout"), dict) else {}
    merged = {**company, **local}
    # Sealed revisions issued before templates existed keep the composition
    # closest to the one they were issued with.
    legacy = not declared(org.get("document_preferences"), "quotation_template") and not merged.get("template")
    template = requested if requested in TEMPLATES else merged.get("template")
    if template not in TEMPLATES:
        # document_preferences fills today's default, so a sealed set that
        # never declared a template must not read it as a choice.
        if legacy:
            template = "PROYECTO"
        else:
            template = prefs["quotation_template"] if prefs.get("quotation_template") in TEMPLATES else "ESENCIAL"
    order = [block for block in merged.get("order") or [] if block in BLOCKS]
    order += [block for block in DEFAULT_ORDER[template] if block not in order]
    required = set(REQUIRED_BLOCKS)
    order = [block for block in order if block in DEFAULT_ORDER[template] or block in merged.get("order", [])]
    if snapshot.get("alternatives"):
        # Alternatives sealed in this revision are part of the offer the
        # customer chooses from: every template shows them, after the
        # windows unless the layout places them elsewhere, and they are
        # never hidden.
        required.add("alternatives")
        if "alternatives" not in order:
            order.insert(order.index("positions") + 1 if "positions" in order else len(order), "alternatives")
    hidden = {block for block in merged.get("hidden") or [] if block in BLOCKS and block not in required}
    texts = merged.get("texts") if isinstance(merged.get("texts"), dict) else {}
    return {
        "template": template,
        "order": order,
        "hidden": hidden,
        "texts": {key: str(texts.get(key) or "")[:MAX_TEXT] for key in ("intro", "closing", "notes")},
        "drawing_size": merged.get("drawing_size") if merged.get("drawing_size") in ("S", "M", "L") else "M",
        "unit_prices": merged.get("unit_prices", True) is not False,
        "acceptance": acceptance_mode(org.get("document_preferences"), prefs),
    }


def acceptance_mode(raw: object, prefs: dict) -> str:
    """NONE | PORTAL | SIGNATURE. A sealed preference set from before the
    policy existed keeps the signature block it was issued with."""
    if not declared(raw, "acceptance_mode"):
        return "SIGNATURE"
    return prefs["acceptance_mode"]


def _paragraphs(text: str) -> str:
    return "".join(f"<p>{escape(part.strip())}</p>" for part in text.split("\n\n") if part.strip())


def _short_link(url: str) -> str:
    """Display a link without letting a long token cross the margin."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return parsed.netloc or url[:40]


def render(snapshot: dict, *, portal_url: str | None = None, layout_name: str | None = None) -> str:
    project = _object(snapshot.get("project"), "invalid_frozen_revision_snapshot")
    positions = snapshot.get("positions")
    if not isinstance(positions, list):
        raise DocumentaryError("invalid_frozen_revision_snapshot")
    layout = resolve_layout(snapshot, layout_name)
    template = layout["template"]
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
        line_values[str(position["position_index"])] = quotation_line(
            quantity=int(position["quantity"]), net=_num(position["price_net"]), currency=currency,
            original_unit=_num(detail["unit_price"]) if detail.get("unit_price") is not None else None,
            discount=_num(position.get("discount_pct") or "0"))
    revision = str(snapshot.get("revision") or "")
    if not revision.startswith("REV-"):
        revision = "REV-" + revision
    draft = bool(snapshot.get("draft"))
    number = "Borrador" if draft else (known(project.get("commercial_label"))
                                       or f'COT-{known(project.get("code"))}-{revision}')
    date = _cldate(snapshot.get("sealed_at"))
    valid = _cldate(project["quotation_valid_until"]) if project.get("quotation_valid_until") else ""
    # The legal line spans the full width: company name and RUT never break
    # inside themselves; the company's free legal text may wrap.
    legal_parts = [f'<span class="q-legal-id">{escape(value)}</span>' for value in [
        known(org.get("name")), "RUT " + known(org["tax_id"]) if known(org.get("tax_id")) else ""] if value]
    if known(prefs.get("legal_footer")):
        legal_parts.append(f'<span>{escape(known(prefs.get("legal_footer")))}</span>')
    footer = (f'<footer class="q-footer"><div class="q-footer-line"><span>Cotización {escape(number)} · '
              f'Revisión {escape(_rev_display(revision))}</span><span class="q-num">Página <span class="pg"></span></span></div>'
              f'<div class="q-legal">{" · ".join(legal_parts)}</div></footer>')
    drawing_width = {"S": 46, "M": 60, "L": 78}[layout["drawing_size"]]
    if template == "ESENCIAL":
        drawing_width = {"S": 34, "M": 42, "L": 56}[layout["drawing_size"]]
    body = f'<main class="quote q-{template.lower()}" style="--q-figure:{drawing_width}mm">{footer}'

    # Header: compact identity row; the offer starts on the first page.
    issuer = " · ".join(known(org.get(field)) for field in ("tax_id", "brand_address", "brand_phone", "brand_email") if known(org.get(field)))
    body += ('<header class="q-head">' + _brand_block({**org, "brand_schema": 1})
             + f'<div class="q-folio"><span class="q-label">Cotización</span><strong class="q-number">{escape(number)}</strong>'
             f'<span>Revisión {escape(_rev_display(revision))} · {escape(date)}</span></div></header>')
    if issuer:
        body += f'<p class="q-issuer">{escape(issuer)}</p>'
    if draft:
        body += '<p class="q-draft">Borrador · no emitido. El número se asigna al preparar la versión para emitir.</p>'
    body += f'<h1>{escape(known(project.get("name")) or "Propuesta para su obra")}</h1>'

    def block_intro() -> str:
        text = layout["texts"]["intro"]
        return f'<section class="q-intro">{_paragraphs(text)}</section>' if text else ""

    def kv(label: str, value: str) -> str:
        return f'<div class="q-kv"><dt>{escape(label)}</dt><dd>{escape(value)}</dd></div>' if value else ""

    def block_client() -> str:
        client = ''.join(kv(label, known(project.get(field))) for label, field in [
            ("RUT", "client_rut"), ("Dirección", "client_address"), ("Comuna", "client_comuna"),
            ("Contacto", "client_email"), ("Teléfono", "client_phone"), ("Obra", "delivery_address")])
        # Conditions are printed once, in their own block; the offer column
        # carries only the scope, the total and the validity.
        count = sum(int(item["quantity"]) for item in positions)
        offer = kv("Alcance", f'{len(positions)} {"tipo" if len(positions) == 1 else "tipos"} de ventana · {count} {"unidad" if count == 1 else "unidades"}') if positions else ""
        if project.get("total_price_gross") is not None:
            offer += (f'<p class="q-label">Total con impuesto · {escape(currency)}</p>'
                      f'<p class="q-total">{escape(_money(project["total_price_gross"], currency))}</p>')
        offer += kv("Vigente hasta", valid)
        client_name = known(project.get("client_name"))
        name_html = f'<p class="q-client-name">{escape(client_name)}</p>' if client_name else ""
        return (f'<div class="q-client"><div><p class="q-label">Para</p>'
                f'{name_html}'
                f'<dl>{client}</dl></div><div><p class="q-label">Propuesta</p>{offer}</div></div>')

    def block_hero() -> str:
        if len(positions) < 2:
            return ""
        hero = positions[representative_index([(_num(item["width_mm"]), _num(item["height_mm"])) for item in positions])]
        kinds: dict[str, int] = {}
        for item in positions:
            caption = _product_caption(item)
            kinds[caption] = kinds.get(caption, 0) + int(item["quantity"])
        types = "".join(f'<li>{escape(caption)} · <span class="q-num">{amount}</span> un.</li>' for caption, amount in kinds.items())
        return (f'<section class="q-hero"><div class="q-hero-drawing">{_position_svg(hero, commercial=True, dimensions=True, dimension_font_divisor=Decimal("16"), include_sliding_plan=False)}</div>'
                f'<div class="q-hero-facts"><span class="q-label">Tipos de ventana en la obra</span><ul class="q-hero-types">{types}</ul></div></section>')

    def block_summary() -> str:
        if not positions:
            return ""
        out = ('<h2>Resumen</h2><table class="q-overview"><colgroup>'
               + ''.join(f'<col style="width:{width}%">' for width in (6, 30, 20, 18, 6, 20))
               + '</colgroup><thead><tr><th>N.º</th><th>Ubicación</th><th>Tipo</th><th>Medida</th><th>Cant.</th><th class="q-num">Total neto</th></tr></thead><tbody>')
        for position in positions:
            value = line_values.get(str(position["position_index"]))
            out += (f'<tr><td class="q-num">{escape(str(position["position_index"]))}</td><td>{escape(known(position.get("location_tag")))}</td>'
                    f'<td>{escape(_product_caption(position))}</td><td class="q-num">{escape(_survey_dim(position.get("width_mm")))} × {escape(_survey_dim(position.get("height_mm")))} mm</td>'
                    f'<td class="q-num">{escape(str(position["quantity"]))}</td><td class="q-num">{escape(_money(value.net, currency)) if value else ""}</td></tr>')
        return out + '</tbody></table>'

    def position_specs(position: dict) -> str:
        specs = spec_row("Sistema", known(position.get("system_name")))
        specs += spec_row("Medida", f'{_survey_dim(position["width_mm"])} × {_survey_dim(position["height_mm"])} mm', numeric=True)
        finish = position.get("resolved_finish") or {}
        if finish:
            approximate = any((finish.get(face) or {}).get("approximate") for face in ("interior", "exterior"))
            specs += spec_row("Acabado", finish_label(position.get("color_interior"), position.get("color_exterior"), finish) + (" · tono aproximado" if approximate else ""))
        else:
            raw = position.get("color_interior")
            specs += spec_row("Color", {"WHITE": "Blanco", "FOILED": "Foliado"}.get(str(raw), ""))
        specs += field_specs(position, authoritative_thermal="thermal" in snapshot)
        for item in position.get("commercial_hardware") or []:
            specs += spec_row("Manilla", " · ".join(known(item.get(field)) for field in ("handle_name", "handle_color") if known(item.get(field))))
            specs += spec_row("Opciones", "; ".join(item.get("options") or []))
        specs += spec_row("Cantidad", str(position["quantity"]) + " un.", numeric=True)
        return specs

    def position_price(position: dict) -> str:
        value = line_values.get(str(position["position_index"]))
        if not value:
            return ""
        discount = _num(position.get("discount_pct") or "0")
        out = '<div class="q-position-price">'
        if discount:
            out += f'<span>Incluye descuento del {escape(_discount_label(discount))}</span>'
        if layout["unit_prices"]:
            out += f'<span>Unitario neto <strong class="q-num">{escape(_money(value.unit_net, currency))}</strong></span>'
        out += f'<span>Total <strong class="q-num">{escape(_money(value.net, currency))}</strong></span></div>'
        if value.adjustment:
            out += f'<p class="q-legend">Cantidad × unitario + ajuste de moneda <span class="q-num">{escape(_money(value.adjustment, currency))}</span> = total emitido.</p>'
        return out

    def position_card(position: dict, *, compact: bool) -> str:
        detail = details.get(str(position["position_index"]), {})
        title = known(position.get("location_tag")) or _product_caption(position)
        figure = _position_svg(position, commercial=True, dimensions=True,
                               dimension_font_divisor=Decimal("14" if compact else "12"), include_sliding_plan=False)
        extras = extras_table(detail.get("sublines") or [], currency, prices=result.get("document_extra_prices", "ITEMIZED") == "ITEMIZED", base=detail.get("base_net"))
        return (f'<article class="q-position{" q-position--compact" if compact else ""}"><h3><span class="q-index">{escape(str(position["position_index"]))}</span> {escape(title)}</h3>'
                f'<div class="q-position-body"><div class="q-figure">{figure}{plan_figure(position)}{sliding_specs(position)}</div>'
                f'<div class="q-spec"><dl>{position_specs(position)}</dl>{position_price(position)}</div></div>{extras}</article>')

    def block_positions() -> str:
        out = '<section class="q-details"><h2>Ventanas y puertas</h2>'
        out += '<p class="q-legend">Vista interior. Línea continua: abre hacia usted; discontinua: se aleja; flecha: corredera.</p>'
        if template == "PROYECTO":
            groups: dict[str, list] = {}
            for position in positions:
                placement = position.get("placement") if isinstance(position.get("placement"), dict) else {}
                key = " · ".join(value for value in (known(placement.get("floor")), known(placement.get("room"))) if value)
                groups.setdefault(key, []).append(position)
            for key, items in groups.items():
                if key and len(groups) > 1:
                    out += f'<h3 class="q-group">{escape(key)}</h3>'
                out += "".join(position_card(item, compact=False) for item in items)
        else:
            out += "".join(position_card(item, compact=True) for item in positions)
        return out + '</section>'

    def block_alternatives() -> str:
        alternatives = snapshot.get("alternatives") or []
        if not alternatives:
            return ""
        rows = [(f"Propuesta principal · Revisión {_rev_display(revision)}", project.get("total_price_gross"), currency, positions, True)]
        rows += [(f"Alternativa · Revisión {_rev_display(alt['revision'])}", alt["project"].get("total_price_gross"),
                  str(alt["project"].get("currency") or currency), alt["positions"], False) for alt in alternatives]
        out = ('<section class="q-options"><h2>Opciones para su obra</h2><table class="q-compare"><thead><tr><th>Opción</th>'
               '<th>Sistemas</th><th class="q-num">Ventanas</th><th class="q-num">Total con impuesto</th></tr></thead><tbody>')
        for title, total, money_currency, items, main in rows:
            systems = ", ".join(sorted({known(item.get("system_name")) for item in items if known(item.get("system_name"))})) or "—"
            out += (f'<tr class="{"q-main" if main else ""}"><td>{escape(title)}</td><td>{escape(systems)}</td>'
                    f'<td class="q-num">{sum(int(item["quantity"]) for item in items)}</td>'
                    f'<td class="q-num">{escape(_money(total, money_currency)) if total is not None else ""}</td></tr>')
        out += '</tbody></table><p class="q-legend">Las alternativas no se suman al total de esta propuesta. Usted elige una.</p>'
        for alternative in alternatives:
            alt_currency = str(alternative["project"]["currency"])
            out += (f'<h3>Alternativa · Revisión {escape(_rev_display(alternative["revision"]))}</h3>'
                    '<p><strong>No incluida en el total de esta propuesta.</strong> Corresponde a una revisión '
                    'emitida anterior; se presenta para comparar.</p>')
            for option in alternative["positions"]:
                out += (f'<article class="q-position q-position--compact"><h3>{escape(known(option.get("location_tag")) or _product_caption(option))}</h3>'
                        f'<div class="q-position-body"><div class="q-figure">{_position_svg(option, commercial=True, dimensions=True, dimension_font_divisor=Decimal("14"), include_sliding_plan=False)}</div>'
                        f'<div class="q-spec"><dl>{spec_row("Sistema", known(option.get("system_name")))}{field_specs(option)}{spec_row("Cantidad", str(option["quantity"]))}</dl>'
                        f'<div class="q-position-price"><span>Total <strong class="q-num">{escape(_money(option["price_net"], alt_currency))}</strong></span></div></div></div></article>')
        return out + '</section>'

    def block_commercial() -> str:
        out = '<section class="q-close"><h2>Resumen comercial</h2><div class="q-commercial"><div>'
        if project.get("total_price_net") is not None:
            # This projection never repairs inconsistent legacy snapshots by
            # inventing original prices.
            summary = quotation_summary(list(line_values.values()), _num(project["total_price_net"])) if len(line_values) == len(positions) else None
            rows = ''
            if summary and summary.before_discount is not None:
                rows += (f'<tr><td>Neto antes de descuento</td><td class="q-num">{escape(_money(summary.before_discount, currency))}</td></tr>'
                         f'<tr><td>Descuento</td><td class="q-num">{escape(_money(summary.discount, currency))}</td></tr>')
            rows += f'<tr><td>Neto</td><td class="q-num">{escape(_money(project["total_price_net"], currency))}</td></tr>'
            pricing = snapshot.get("pricing") or {}
            tax_rate = (pricing.get("input_snapshot") or {}).get("rules", {}).get("tax_rate_pct")
            if tax_rate is None:
                tax_rate = pricing.get("request", {}).get("tax_rate_pct")
            tax_label = "Impuesto" if tax_rate is None else "IVA " + _discount_label(tax_rate)
            rows += (f'<tr><td>{escape(tax_label)}</td><td class="q-num">{escape(_money(project["total_price_tax"], currency))}</td></tr>'
                     f'<tr class="q-final"><td>Total · {escape(currency)}</td><td class="q-num">{escape(_money(project["total_price_gross"], currency))}</td></tr>')
            out += f'<table class="q-totals"><colgroup><col style="width:55%"><col style="width:45%"></colgroup><tbody>{rows}</tbody></table>'
            schedule = terms.get("payment_schedule") or []
            if schedule:
                amounts = payment_amounts(_num(project["total_price_gross"]), [_num(item["share"]) for item in schedule], currency)
                out += '<table class="q-schedule"><caption>Calendario de pagos</caption><tbody>'
                for item, amount in zip(schedule, amounts, strict=True):
                    due = (_cldate(item["due_on"]) if item.get("due_on") else
                           "Al aprobar" if item.get("due_event") == "APPROVAL" else
                           "Contra entrega completa" if item.get("due_event") == "DELIVERY" else "")
                    out += (f'<tr><td>{escape(item["label"])} · <span class="q-num">{escape(_discount_label(item["share"]))}</span>'
                            f'{"<br>" + escape(due) if due else ""}</td><td class="q-num">{escape(_money(amount, currency))}</td></tr>')
                out += '</tbody></table>'
        out += '</div><div class="q-terms">'
        for label, value in [("Forma de pago", project.get("payment_terms"))]:
            if known(value):
                out += f'<p><strong>{escape(label)}</strong><br>{escape(known(value))}</p>'
        return out + '</div></div></section>'

    def block_terms() -> str:
        out = ""
        for label, field in [("Plazo de entrega", "delivery_text"), ("Instalación", "installation_text"), ("Exclusiones", "exclusions"), ("Garantía", "warranty"), ("Jurisdicción", "jurisdiction")]:
            if known(terms.get(field)):
                out += f'<p><strong>{escape(label)}</strong><br>{escape(known(terms[field]))}</p>'
        if known(project.get("notes_commercial")):
            out += f'<p><strong>Condiciones</strong><br>{escape(known(project["notes_commercial"]))}</p>'
        if layout["texts"]["notes"]:
            out += f'<div class="q-notes">{_paragraphs(layout["texts"]["notes"])}</div>'
        return f'<section class="q-terms-block"><h2>Condiciones</h2><div class="q-terms-list">{out}</div></section>' if out else ""

    def block_services() -> str:
        return extras_table(result.get("services") or [], currency, prices=result.get("document_extra_prices", "ITEMIZED") == "ITEMIZED",
                            caption="Servicios del proyecto incluidos en el neto")

    def block_acceptance() -> str:
        """Acceptance only by policy (or an explicit request); without it the
        printed link lets the customer review this same revision online."""
        mode = layout["acceptance"]
        if draft or (mode == "NONE" and not portal_url):
            return ""
        title = "Consulta en línea" if mode == "NONE" else "Aceptación"
        out = f'<section class="q-accept"><h2>{title}</h2>'
        if mode == "SIGNATURE":
            out += (f'<p>Al firmar acepta las especificaciones, condiciones y total de la cotización {escape(number)}.</p>'
                    '<div class="q-signature"><div><span>Nombre y RUT</span></div><div><span>Firma</span></div><div><span>Fecha</span></div></div>')
        if portal_url:
            import segno
            uri = segno.make(portal_url, micro=False, error="m").svg_data_uri(border=4, scale=8)
            heading = "Vea esta cotización en línea" if mode == "NONE" else "Revise y acepte en línea"
            out += (f'<div class="q-online"><a href="{escape(portal_url, quote=True)}"><img src="{uri}" alt="Código QR de esta cotización"></a><div><strong>{heading}</strong>'
                    f'<p>Escanee el código o abra el enlace que le enviamos. Corresponde a esta misma revisión.</p>'
                    f'<a class="q-link" href="{escape(portal_url, quote=True)}">{escape(_short_link(portal_url))}</a></div></div>')
        return out + '</section>'

    def block_closing() -> str:
        text = layout["texts"]["closing"]
        return f'<section class="q-closing">{_paragraphs(text)}</section>' if text else ""

    builders = {
        "intro": block_intro, "client": block_client, "hero": block_hero, "summary": block_summary,
        "positions": block_positions, "alternatives": block_alternatives, "commercial": block_commercial,
        "terms": block_terms, "services": block_services, "acceptance": block_acceptance, "closing": block_closing,
    }
    for block in layout["order"]:
        if block in layout["hidden"]:
            continue
        body += f'<div class="q-block" data-block="{block}">{builders[block]()}</div>'
    body += thermal_annex(snapshot.get("thermal"))
    body += '</main>'
    return body


def thermal_annex(report: dict | None) -> str:
    """Only independently authoritative values from this revision's seal."""
    if not report or not (report.get("inputs") or {}).get("include_doc01"):
        return ""
    assessment = report.get("assessment") or {}
    html = '<section class="q-details"><h2>Anexo técnico · ventanas</h2>'
    html += '<p>Valores con informe vigente revisado al emitir esta revisión. Este cálculo no constituye certificación del edificio.</p>'
    valid = []
    for position in assessment.get("positions") or []:
        metric = position.get("thermal") or {}
        if metric.get("state") != "KNOWN" or metric.get("uw") is None:
            continue
        valid.append(position)
        trace = metric.get("trace") or {}
        html += f'<article class="q-position"><h3>Ventana {int(position["position_index"])} · {escape(position.get("location_tag") or "Sin ubicación")}</h3><dl>'
        html += spec_row("Uw", str(_num(metric["uw"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)).replace(".", ",") + " W/m²K", numeric=True)
        for label, field in (("Clase de aire a 100 Pa", "air_class"), ("Clase de agua", "water_class"), ("Clase de viento", "wind_class")):
            if metric.get(field) is not None:
                html += spec_row(label, str(metric[field]), numeric=True)
        html += '</dl><p>Uw = (ΣAg·Ug + Af·Uf + Σlg·Ψg) / (Ag + Af) · ISO 10077-1, método de áreas.</p>'
        seen = set()
        certificates = [trace.get("frame_report"), trace.get("performance_report")]
        for pane in trace.get("panes") or []:
            if pane.get("solar_factor") is not None:
                html += spec_row("Factor solar g", str(_num(pane["solar_factor"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)).replace(".", ","), numeric=True)
            certificates.extend([pane.get("glass_report"), pane.get("spacer_report")])
        for source in certificates:
            if not source or source["id"] in seen:
                continue
            seen.add(source["id"])
            html += f'<p>{escape(source["source_document"])} · {escape(source["laboratory"])} · {escape(_cldate(source["report_date"]))} · {escape(source["standard"])} · {escape(source["source_page"])}</p>'
            html += f'<p>{escape(source["applicability"])}</p>'
        html += '</article>'
    if not valid:
        html += '<p>No se adjuntan valores térmicos: faltan datos e informes de las ventanas. Complétalos en una nueva revisión.</p>'
    html += f'<p>{escape(assessment.get("scope") or "")}</p>'
    html += f'<p>Normativa de referencia: {escape(assessment.get("source_label") or "OGUC 4.1.10")}</p></section>'
    return html
