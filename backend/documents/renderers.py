"""Frozen-authority PDF producers for DOC-01, DOC-03 through DOC-07."""

from __future__ import annotations

from decimal import Decimal
from html import escape
from pathlib import Path

from documents.repository import DocumentaryError

_PDF_MEDIA = "application/pdf"
_FONTS_DIR = Path(__file__).resolve().parent / "fonts"

# DEKOPEN document language — teal/graphite tokens from the visual-identity
# study: #075F5A teal-800, #0B7770 teal-700, #E6F4F2 teal-50, graphite ramp
# #161C1F..#FCFDFC, Plex Sans + Plex Mono, hairline rules instead of tinted
# boxes, ISO-7200-style title block in the bottom margin.
_TEAL_800 = "#075F5A"
_TEAL_700 = "#0B7770"
_TEAL_50 = "#E6F4F2"
_G_950 = "#161C1F"
_G_800 = "#252D31"
_G_700 = "#465158"
_G_500 = "#727D82"
_G_300 = "#CDD5D6"
_G_50 = "#F5F7F6"
_PAPER = "#FCFDFC"
_MARK = "#E56A32"
_DANGER = "#991B1B"


def _font_face(family: str, weight: int, filename: str) -> str:
    uri = (_FONTS_DIR / filename).as_uri()
    return (
        "@font-face {"
        f" font-family: '{family}'; font-style: normal; font-weight: {weight};"
        f" src: url('{uri}') format('truetype');"
        " }"
    )


_FONTS = "".join(
    [
        _font_face("IBM Plex Sans", 400, "IBMPlexSans-400.ttf"),
        _font_face("IBM Plex Sans", 500, "IBMPlexSans-500.ttf"),
        _font_face("IBM Plex Sans", 600, "IBMPlexSans-600.ttf"),
        _font_face("IBM Plex Sans", 700, "IBMPlexSans-700.ttf"),
        _font_face("IBM Plex Mono", 400, "IBMPlexMono-400.ttf"),
        _font_face("IBM Plex Mono", 500, "IBMPlexMono-500.ttf"),
    ]
)

_CSS = _FONTS + """
@page { size: letter portrait; margin: 13mm 12mm 22mm; @bottom-center { content: element(titleblock); } }
* { box-sizing: border-box; } body { color: #161C1F; font: 9.5pt 'IBM Plex Sans', sans-serif; margin: 0; }
.titleblock { position: running(titleblock); display: table; width: 100%; border-collapse: collapse; border-top: 1.5pt solid #075F5A; font-family: 'IBM Plex Mono', monospace; }
.titleblock .tb-cell { display: table-cell; border-left: 0.5pt solid #CDD5D6; border-bottom: 0.5pt solid #CDD5D6; padding: 1.2mm 2mm; vertical-align: top; }
.titleblock .tb-cell:first-child { border-left: none; padding-left: 0; }
.titleblock .tb-wide { width: 34%; }
.tb-label { display: block; font: 6.5pt 'IBM Plex Sans', sans-serif; text-transform: uppercase; letter-spacing: 0.5pt; color: #727D82; margin-bottom: 0.6mm; }
.tb-value { display: block; font: 8pt 'IBM Plex Mono', monospace; color: #252D31; overflow-wrap: anywhere; }
.pg::after { content: counter(page) " / " counter(pages); }
h1 { font-size: 16pt; font-weight: 600; margin: 0 0 4mm; letter-spacing: -0.2pt; color: #161C1F; }
h2 { font-size: 11pt; font-weight: 600; margin: 5mm 0 2mm; border-bottom: 0.75pt solid #465158; padding-bottom: 1.2mm; color: #161C1F; }
h3 { font-size: 9.5pt; font-weight: 600; margin: 4mm 0 1.5mm; color: #252D31; } p { margin: 1.5mm 0; }
.masthead { position: relative; display: flex; justify-content: space-between; padding-bottom: 4mm; margin-bottom: 1.6mm; }
.brand { color: #075F5A; font-weight: 600; font-size: 12pt; letter-spacing: 2.4pt; }
.brand .mark { display: inline-block; width: 2.4mm; height: 2.4mm; background: #E56A32; margin-left: 1.6mm; }
.meta { text-align: right; color: #727D82; font: 8pt 'IBM Plex Mono', monospace; padding-right: 9mm; }
.meta strong { color: #252D31; font-weight: 500; }
.rule-stack { border-top: 1.5pt solid #075F5A; border-bottom: 0.5pt solid #CDD5D6; height: 1.2mm; margin-bottom: 6mm; }
.miter { position: absolute; top: 0; right: 0; width: 8mm; height: 8mm; }
.hero { position: relative; background: #E6F4F2; border-left: 3px solid #0B7770; padding: 4mm 5mm; margin: 3mm 0 5mm; }
.hero p { color: #465158; } .total { font-size: 14pt; font-weight: 600; color: #075F5A; }
table { width: 100%; border-collapse: collapse; margin: 2mm 0 3mm; table-layout: fixed; }
thead { border-top: 0.9pt solid #465158; }
th { color: #465158; font: 6.5pt 'IBM Plex Sans', sans-serif; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5pt; text-align: left; border-bottom: 0.9pt solid #465158; padding: 1.4mm 1.8mm; }
td { border-bottom: 0.5pt solid #CDD5D6; padding: 1.6mm 1.8mm; vertical-align: top; overflow-wrap: anywhere; }
tbody tr:last-child td { border-bottom: 0.9pt solid #465158; }
.workshop h1 { font-size: 14pt; } .workshop th { background: #252D31; color: #FCFDFC; }
.dimension { font: 11pt 'IBM Plex Mono', monospace; font-weight: 500; color: #161C1F; }
.hash { font: 6.5pt 'IBM Plex Mono', monospace; color: #465158; overflow-wrap: anywhere; }
.break-avoid { break-inside: avoid; } .blank { display: inline-block; width: 5mm; height: 5mm; border: 1px solid #252D31; vertical-align: middle; }
.confidential { color: #991B1B; font-weight: 600; font-size: 6.5pt; text-transform: uppercase; letter-spacing: 0.8pt; }
.muted { color: #727D82; } .signature { height: 15mm; border-bottom: 0.5pt solid #465158; margin-top: 6mm; }
.signoff { break-inside: avoid; }
svg:not(.miter) { max-width: 100%; height: auto; display: block; } svg text { font-family: 'IBM Plex Mono', monospace; }
.figures { display: flex; flex-wrap: wrap; gap: 4mm; margin: 2mm 0 4mm; }
.figures figure { margin: 0; width: 58mm; break-inside: avoid; }
.figures figcaption { color: #4A5559; font-size: 7pt; line-height: 1.45; margin-top: 1mm; }
.figures .figpos { color: #161C1F; font-weight: 600; }
.figures .figdim { font-family: 'IBM Plex Mono', monospace; font-size: 7.5pt; }
"""


def _object(value: object, code: str) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise DocumentaryError(code)
    return value


def _array(value: object, code: str) -> list[object]:
    if not isinstance(value, list):
        raise DocumentaryError(code)
    return value


def _value(value: object) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Sí" if value else "No"
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (str, int)):
        return str(value)
    if isinstance(value, float):
        raise DocumentaryError("pdf_float_authority_forbidden")
    raise DocumentaryError("pdf_value_not_scalar")


def _cell(value: object, class_name: str = "") -> str:
    css = f' class="{escape(class_name)}"' if class_name else ""
    return f"<td{css}>{escape(_value(value))}</td>"


def _row(values: list[object], classes: list[str] | None = None) -> str:
    styles = classes or [""] * len(values)
    return "<tr>" + "".join(_cell(value, styles[index]) for index, value in enumerate(values)) + "</tr>"


def _table(headers: list[str], rows: list[list[object]], classes: list[str] | None = None) -> str:
    head = "<tr>" + "".join(f"<th>{escape(header)}</th>" for header in headers) + "</tr>"
    return "<table><thead>" + head + "</thead><tbody>" + "".join(
        _row(row, classes) for row in rows
    ) + "</tbody></table>"


def _url_fetcher(url: str, *args: object, **kwargs: object) -> object:
    """Frozen-authority fetcher: only the bundled Plex TTFs may load.

    Every other URL — remote or local — is denied so emitted documents can
    never exfiltrate or depend on network state.
    """
    if url.startswith("file://"):
        target = Path(url.removeprefix("file://")).resolve()
        if target.parent == _FONTS_DIR and target.suffix == ".ttf":
            from weasyprint import URLFetcher

            return URLFetcher(allowed_protocols={"file"}).fetch(url)
    raise DocumentaryError(f"External PDF resource forbidden: {url}")


_MITER = (
    '<svg class="miter" width="8mm" height="8mm" viewBox="0 0 32 32" '
    'xmlns="http://www.w3.org/2000/svg">'
    f'<path d="M0,0 L32,0 L32,32 Z" fill="{_PAPER}" stroke="{_TEAL_800}" '
    'stroke-width="2"/></svg>'
)


_SVG_INSET = Decimal("0.06")


def _num(value: object) -> Decimal:
    if isinstance(value, bool):
        raise DocumentaryError("svg_dimension_invalid")
    if isinstance(value, (Decimal, int)):
        return Decimal(value)
    if isinstance(value, str):
        try:
            return Decimal(value)
        except ArithmeticError:
            raise DocumentaryError("svg_dimension_invalid") from None
    raise DocumentaryError("svg_dimension_invalid")


def _pt(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _svg_elements(node: dict[str, object], x: Decimal, y: Decimal,
                  width: Decimal, height: Decimal, out: list[str],
                  marker: str) -> None:
    node_type = str(node.get("type"))
    children = node.get("children")
    if children is None:
        children = []
    if not isinstance(children, list):
        raise DocumentaryError("invalid_frozen_parametric_tree")
    if node_type == "ROOT":
        if len(children) != 1 or not isinstance(children[0], dict):
            raise DocumentaryError("invalid_frozen_parametric_tree")
        _svg_elements(children[0], x, y, width, height, out, marker)
        return
    if node_type in ("SPLIT_V", "SPLIT_H"):
        offset = node.get("split_offset_mm")
        if offset is None or len(children) != 2:
            raise DocumentaryError("invalid_frozen_parametric_tree")
        split = _num(offset)
        first, second = children
        if not isinstance(first, dict) or not isinstance(second, dict):
            raise DocumentaryError("invalid_frozen_parametric_tree")
        if node_type == "SPLIT_V":
            out.append(
                f'<line x1="{_pt(x + split)}" y1="{_pt(y)}" x2="{_pt(x + split)}" '
                f'y2="{_pt(y + height)}" stroke="#465158" stroke-width="'
                f'{_pt(height / Decimal("60"))}"/>'
            )
            _svg_elements(first, x, y, split, height, out, marker)
            _svg_elements(second, x + split, y, width - split, height, out, marker)
        else:
            out.append(
                f'<line x1="{_pt(x)}" y1="{_pt(y + split)}" x2="{_pt(x + width)}" '
                f'y2="{_pt(y + split)}" stroke="#465158" stroke-width="'
                f'{_pt(width / Decimal("60"))}"/>'
            )
            _svg_elements(first, x, y, width, split, out, marker)
            _svg_elements(second, x, y + split, width, height - split, out, marker)
        return
    if node_type != "BAY":
        raise DocumentaryError("invalid_frozen_parametric_tree")
    inset_x = width * _SVG_INSET
    inset_y = height * _SVG_INSET
    ix, iy = x + inset_x, y + inset_y
    iw, ih = width - inset_x * 2, height - inset_y * 2
    stroke = _pt(min(width, height) / Decimal("120"))
    out.append(
        f'<rect x="{_pt(x)}" y="{_pt(y)}" width="{_pt(width)}" height="{_pt(height)}" '
        'fill="none" stroke="#075F5A" stroke-width="' + _pt(min(width, height) / Decimal("40"))
        + '"/>'
    )
    out.append(
        f'<rect x="{_pt(ix)}" y="{_pt(iy)}" width="{_pt(iw)}" height="{_pt(ih)}" '
        f'fill="#E6F4F2" stroke="#075F5A" stroke-width="{stroke}"/>'
    )
    opening = node.get("opening_type")
    mx, my = ix + iw / 2, iy + ih / 2
    if opening in ("TURN_LEFT", "TILT_TURN_LEFT"):
        out.append(
            f'<polygon points="{_pt(ix)},{_pt(iy)} {_pt(ix)},{_pt(iy + ih)} '
            f'{_pt(ix + iw)},{_pt(my)}" fill="none" stroke="#075F5A" '
            f'stroke-width="{stroke}"/>'
        )
    elif opening in ("TURN_RIGHT", "TILT_TURN_RIGHT"):
        out.append(
            f'<polygon points="{_pt(ix + iw)},{_pt(iy)} {_pt(ix + iw)},{_pt(iy + ih)} '
            f'{_pt(ix)},{_pt(my)}" fill="none" stroke="#075F5A" '
            f'stroke-width="{stroke}"/>'
        )
    if opening in ("TILT_TURN_LEFT", "TILT_TURN_RIGHT"):
        out.append(
            f'<polygon points="{_pt(ix)},{_pt(iy + ih)} {_pt(ix + iw)},{_pt(iy + ih)} '
            f'{_pt(mx)},{_pt(iy)}" fill="none" stroke="#075F5A" stroke-width="{stroke}"/>'
        )
    elif opening == "AWNING":
        out.append(
            f'<polygon points="{_pt(ix)},{_pt(iy)} {_pt(ix + iw)},{_pt(iy)} '
            f'{_pt(mx)},{_pt(iy + ih)}" fill="none" stroke="#075F5A" '
            f'stroke-width="{stroke}"/>'
        )
    elif opening in ("SLIDING_2L", "SLIDING_3L", "SLIDING_4L"):
        leaf_count = {"SLIDING_2L": 2, "SLIDING_3L": 3, "SLIDING_4L": 4}[str(opening)]
        leaf_w = iw / leaf_count
        for index in range(leaf_count):
            lx = ix + leaf_w * index
            out.append(
                f'<rect x="{_pt(lx)}" y="{_pt(iy)}" width="{_pt(leaf_w)}" '
                f'height="{_pt(ih)}" fill="none" stroke="#075F5A" '
                f'stroke-width="{stroke}"/>'
            )
            out.append(
                f'<line x1="{_pt(lx + leaf_w / 4)}" y1="{_pt(my)}" '
                f'x2="{_pt(lx + leaf_w * 3 / 4)}" y2="{_pt(my)}" stroke="#075F5A" '
                f'stroke-width="{stroke}" marker-end="url(#{marker})"/>'
            )
    elif opening in ("DOOR_ENTRY", "DOOR_DOUBLE"):
        out.append(
            f'<line x1="{_pt(ix)}" y1="{_pt(iy + ih)}" x2="{_pt(ix + iw)}" '
            f'y2="{_pt(iy + ih)}" stroke="#E56A32" stroke-width="{stroke}"/>'
        )
        if opening == "DOOR_DOUBLE":
            out.append(
                f'<line x1="{_pt(mx)}" y1="{_pt(iy)}" x2="{_pt(mx)}" '
                f'y2="{_pt(iy + ih)}" stroke="#075F5A" stroke-width="{stroke}"/>'
            )


def _position_svg(position: dict[str, object]) -> str:
    tree = _object(position.get("parametric_tree"), "invalid_frozen_parametric_tree")
    marker = f"arrow-{_value(position.get('position_index'))}"
    elements: list[str] = [
        f'<defs><marker id="{marker}" markerWidth="8" markerHeight="8" refX="6" refY="3" '
        'orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#075F5A" '
        'stroke-width="1"/></marker></defs>'
    ]
    if tree.get("version") == "product-v2":
        # Assemblies draw every module's front view side by side; couplings
        # become an orange joint line with the plan deflection annotated.
        assembly = _object(tree.get("assembly"), "invalid_frozen_parametric_tree")
        modules = [
            _object(module, "invalid_frozen_parametric_tree")
            for module in _array(assembly.get("modules"), "invalid_frozen_parametric_tree")
        ]
        couplings = [
            _object(coupling, "invalid_frozen_parametric_tree")
            for coupling in _array(
                assembly.get("couplings", []), "invalid_frozen_parametric_tree"
            )
        ]
        width = Decimal("0")
        height = Decimal("0")
        for index, module in enumerate(modules):
            module_width = _num(module.get("width_mm"))
            module_height = _num(module.get("height_mm"))
            if module_width <= 0 or module_height <= 0:
                raise DocumentaryError("svg_dimension_invalid")
            if index > 0:
                joint_width = module_width / Decimal("60")
                elements.append(
                    f'<line x1="{_pt(width)}" y1="0" x2="{_pt(width)}" '
                    f'y2="{_pt(module_height)}" stroke="#E56A32" '
                    f'stroke-width="{_pt(joint_width)}"/>'
                )
                if index - 1 < len(couplings):
                    angle = couplings[index - 1].get("angle_deg")
                    if angle is not None:
                        elements.append(
                            f'<text x="{_pt(width)}" y="{_pt(module_height / Decimal("18"))}" '
                            f'font-size="{_pt(module_height / Decimal("16"))}" '
                            f'fill="#E56A32" text-anchor="middle">'
                            f'{escape(_value(angle))}°</text>'
                        )
            _svg_elements(
                _object(module.get("tree"), "invalid_frozen_parametric_tree"),
                width, Decimal("0"), module_width, module_height, elements, marker,
            )
            elements.append(
                f'<text x="{_pt(width + module_width / Decimal("30"))}" '
                f'y="{_pt(module_height - module_height / Decimal("30"))}" '
                f'font-size="{_pt(module_height / Decimal("18"))}" '
                f'fill="#727D82">{escape(_value(module.get("id")))}</text>'
            )
            width += module_width
            height = max(height, module_height)
    else:
        width = _num(position.get("width_mm"))
        height = _num(position.get("height_mm"))
        if width <= 0 or height <= 0:
            raise DocumentaryError("svg_dimension_invalid")
        _svg_elements(tree, Decimal("0"), Decimal("0"), width, height, elements, marker)
    return (
        f'<svg viewBox="0 0 {_pt(width)} {_pt(height)}" '
        'xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="Vano {_value(position.get("position_index"))}">'
        + "".join(elements) + "</svg>"
    )


def _glass_specs(node: object) -> list[str]:
    if not isinstance(node, dict):
        raise DocumentaryError("invalid_frozen_parametric_tree")
    result = []
    if node.get("glass_spec") is not None:
        result.append(_value(node["glass_spec"]))
    children = node.get("children", [])
    if not isinstance(children, list):
        raise DocumentaryError("invalid_frozen_parametric_tree")
    for child in children:
        result.extend(_glass_specs(child))
    return result


def _position_glass_specs(position: dict[str, object]) -> list[str]:
    tree = _object(position.get("parametric_tree"), "invalid_frozen_parametric_tree")
    if tree.get("version") == "product-v2":
        assembly = _object(tree.get("assembly"), "invalid_frozen_parametric_tree")
        specs: list[str] = []
        for module in _array(assembly.get("modules"), "invalid_frozen_parametric_tree"):
            specs.extend(
                _glass_specs(
                    _object(module, "invalid_frozen_parametric_tree").get("tree")
                )
            )
        return specs
    return _glass_specs(tree)


def _revision_header(
    snapshot: dict[str, object], title: str, doc_code: str, workshop: bool = False
) -> tuple[str, str]:
    project = _object(snapshot.get("project"), "invalid_frozen_revision_snapshot")
    bom_hash = _value(snapshot.get("bom_hash"))
    class_name = "workshop" if workshop else ""
    sealed_at = _value(snapshot.get("sealed_at"))
    revision = _value(snapshot.get("revision"))
    project_code = _value(project.get("code"))
    titleblock = (
        '<div class="titleblock">'
        f'<div class="tb-cell"><span class="tb-label">Proyecto</span>'
        f'<span class="tb-value">{escape(project_code)}</span></div>'
        f'<div class="tb-cell"><span class="tb-label">Documento</span>'
        f'<span class="tb-value">{escape(doc_code)}</span></div>'
        f'<div class="tb-cell"><span class="tb-label">Rev.</span>'
        f'<span class="tb-value">{escape(revision)}</span></div>'
        f'<div class="tb-cell"><span class="tb-label">Fecha</span>'
        f'<span class="tb-value">{escape(sealed_at[:10])}</span></div>'
        f'<div class="tb-cell tb-wide"><span class="tb-label">Huella BOM</span>'
        f'<span class="tb-value">{escape(bom_hash)}</span></div>'
        '<div class="tb-cell"><span class="tb-label">Página</span>'
        '<span class="tb-value"><span class="pg"></span></span></div>'
        "</div>"
    )
    header = (
        f'<div class="masthead">{_MITER}<div><div class="brand">DEKOPEN'
        '<span class="mark"></span></div></div>'
        '<div class="meta">'
        f"<strong>{escape(project_code)}</strong><br>"
        f"{escape(doc_code)} · Rev. {escape(revision)}<br>"
        f"{escape(sealed_at)}</div></div>"
        '<div class="rule-stack"></div>'
        f"<h1>{escape(title)}</h1>"
    )
    return f'<main class="{class_name}">{titleblock}{header}', bom_hash


def _doc01(snapshot: dict[str, object]) -> str:
    project = _object(snapshot.get("project"), "invalid_frozen_revision_snapshot")
    positions = [_object(item, "invalid_frozen_position")
                 for item in _array(snapshot.get("positions"), "invalid_frozen_revision_snapshot")]
    opening_rows = []
    for position in positions:
        specs = _position_glass_specs(position)
        opening_rows.append([
            position.get("position_index"), position.get("location_tag"),
            f"{_value(position.get('width_mm'))} × {_value(position.get('height_mm'))}",
            position.get("quantity"), ", ".join(specs) or "Panel declarado",
            f"{_value(position.get('color_interior'))} / {_value(position.get('color_exterior'))}",
        ])
    body, _ = _revision_header(snapshot, "Cotización comercial", "DOC-01")
    body += (
        '<section class="hero"><p>Preparado para</p>'
        f"<h2>{escape(_value(project.get('client_name')))}</h2>"
        f"<p>{escape(_value(project.get('delivery_address')))}</p>"
        f'<p class="total">Total: {escape(_value(project.get("currency")))} '
        f'{escape(_value(project.get("total_price_gross")))}</p></section>'
        "<h2>Solución propuesta</h2>"
        + _table(["Pos.", "Ubicación", "Dimensiones mm", "Cant.", "Relleno", "Acabado"], opening_rows)
    )
    body += '<h2>Vistas de vanos</h2><div class="figures">'
    for position in positions:
        body += (
            f'<figure>{_position_svg(position)}'
            f'<figcaption><span class="figpos">Pos. '
            f'{escape(_value(position.get("position_index")))}</span> · '
            f'{escape(_value(position.get("location_tag")))}<br/>'
            f'<span class="figdim">{escape(_value(position.get("width_mm")))} × '
            f'{escape(_value(position.get("height_mm")))} mm</span> · Cant. '
            f'{escape(_value(position.get("quantity")))}</figcaption></figure>'
        )
    body += "</div>"
    body += (
        "<h2>Resumen comercial</h2>"
        + _table(["Neto", "Impuesto", "Total"], [[
            project.get("total_price_net"), project.get("total_price_tax"),
            project.get("total_price_gross"),
        ]], ["", "", "dimension"])
        + f"<h2>Condiciones</h2><p><strong>Pago:</strong> {escape(_value(project.get('payment_terms')))}</p>"
        + f"<p><strong>Oferta válida hasta:</strong> {escape(_value(project.get('quotation_valid_until')))}</p>"
        + f"<p>{escape(_value(project.get('notes_commercial')))}</p>"
        + "<div class=\"signoff\"><div class=\"signature\"></div><p class=\"muted\">Aceptación del cliente</p></div></main>"
    )
    return body


def _doc03(snapshot: dict[str, object]) -> str:
    if snapshot.get("production_allowed") is not True:
        raise DocumentaryError("production_document_blocked")
    if snapshot.get("documentary_complete") is not True:
        raise DocumentaryError("manufacturing_document_incomplete")
    facts = [_object(item, "invalid_manufacturing_fact")
             for item in _array(snapshot.get("manufacturing"), "invalid_frozen_revision_snapshot")]
    positions_list = [
        _object(item, "invalid_frozen_position")
        for item in _array(snapshot.get("positions"), "invalid_frozen_revision_snapshot")
    ]
    positions_by_index = {item.get("position_index"): item for item in positions_list}
    annotated_positions: set[object] = set()
    labels = _piece_labels(snapshot)
    body, _ = _revision_header(snapshot, "Orden de trabajo de taller", "DOC-03", workshop=True)
    for fact in facts:
        members = [_object(item, "invalid_manufacturing_member")
                   for item in _array(fact.get("members"), "invalid_manufacturing_fact")]
        reinforcements = [_object(item, "invalid_reinforcement_fact")
                          for item in _array(fact.get("reinforcements"), "invalid_manufacturing_fact")]
        handles = [_object(item, "invalid_handle_fact")
                   for item in _array(fact.get("handles"), "invalid_manufacturing_fact")]
        infills = [_object(item, "invalid_infill_fact")
                   for item in _array(fact.get("infills"), "invalid_manufacturing_fact")]
        body += (
            f'<section class="break-avoid"><h2>Posición {escape(_value(fact.get("position_index")))} · '
            f'Repetición {escape(_value(fact.get("repetition_index")))}</h2>'
            f'<p class="dimension">{escape(_value(fact.get("nominal_width_mm")))} × '
            f'{escape(_value(fact.get("nominal_height_mm")))} mm</p>'
            + _table(
                ["Pieza", "Rol / slot", "SKU taller", "Corte mm", "Ángulos", "Referencia X/Y"],
                [[
                    labels["member"].get(member.get("member_id"), member.get("member_id")),
                    f"{_value(_object(member.get('identity'), 'invalid_member_identity').get('role'))} / "
                    f"{_value(_object(member.get('identity'), 'invalid_member_identity').get('physical_member_slot'))}",
                    member.get("workshop_sku"), member.get("cut_length_mm"),
                    f"{_value(member.get('angle_left'))}° / {_value(member.get('angle_right'))}°",
                    f"({_value(_object(member.get('start'), 'invalid_member_point').get('x_mm'))}, "
                    f"{_value(_object(member.get('start'), 'invalid_member_point').get('y_mm'))}) → "
                    f"({_value(_object(member.get('end'), 'invalid_member_point').get('x_mm'))}, "
                    f"{_value(_object(member.get('end'), 'invalid_member_point').get('y_mm'))})",
                ] for member in members], ["hash", "", "", "dimension", "", ""]
            )
        )
        if reinforcements:
            body += _table(
                ["Refuerzo", "Pieza padre", "SKU acero", "Corte mm", "Ángulos"],
                [[labels["reinforcement"].get(item.get("reinforcement_id"), item.get("reinforcement_id")),
                  labels["member"].get(item.get("parent_member_id"), item.get("parent_member_id")),
                  item.get("workshop_sku"), item.get("cut_length_mm"),
                  f"{_value(item.get('angle_left'))}° / {_value(item.get('angle_right'))}°"]
                 for item in reinforcements], ["hash", "hash", "", "dimension", ""]
            )
        if infills:
            body += _table(
                ["Relleno", "Vano / hoja", "Especificación", "Dimensiones mm", "Retención"],
                [[labels["infill"].get(item.get("infill_id"), item.get("infill_id")),
                  _location(labels, item.get("bay_id"), item.get("leaf_id")),
                  item.get("composition"),
                  f"{_value(_object(item.get('rect'), 'invalid_infill_rect').get('width_mm'))} × "
                  f"{_value(_object(item.get('rect'), 'invalid_infill_rect').get('height_mm'))}",
                  "Junquillos identificados en matriz"] for item in infills],
                ["hash", "", "", "dimension", ""],
            )
        if handles:
            body += _table(
                ["Manilla", "Vano / hoja", "Pieza host", "Punto X/Y mm",
                 "Altura solicitada mm", "Referencia vertical"],
                [[labels["handle"].get(item.get("handle_id"), item.get("handle_id")),
                  _location(labels, item.get("bay_id"), item.get("leaf_id")),
                  labels["member"].get(item.get("host_member_id"), item.get("host_member_id")),
                  f"{_value(_object(item.get('point'), 'invalid_handle_point').get('x_mm'))} / "
                  f"{_value(_object(item.get('point'), 'invalid_handle_point').get('y_mm'))}",
                  item.get("requested_height_mm"),
                  item.get("vertical_reference")] for item in handles],
                ["hash", "", "hash", "dimension", "dimension", ""]
            )
        if fact.get("position_index") not in annotated_positions:
            annotated_positions.add(fact.get("position_index"))
            position = positions_by_index.get(fact.get("position_index"))
            if position is None:
                raise DocumentaryError("invalid_frozen_revision_snapshot")
            body += (
                f'<div class="break-avoid" style="text-align:center">'
                f'<div style="display:inline-block;max-width:100mm">'
                f'{_position_svg(_object(position, "invalid_frozen_position"))}</div></div>'
            )
            annotations = [
                _object(item, "invalid_workshop_annotations")
                for item in _array(
                    position.get("workshop_annotations"), "invalid_workshop_annotations"
                )
            ]
            if annotations:
                body += "<h3>Anotaciones de taller congeladas</h3>" + _table(
                    ["Vano", "Hoja", "Desagüe inferior mm", "Cierres perímetro mm",
                     "Ancho continuo mm", "Acabado", "Coplador"],
                    [[
                        item.get("bay_id"), item.get("leaf_id"),
                        ", ".join(_value(number) for number in _array(
                            item.get("bottom_drain_holes_mm"), "invalid_workshop_annotations"
                        )) if item.get("bottom_drain_holes_mm") is not None else "—",
                        ", ".join(_value(number) for number in _array(
                            item.get("closing_points_perimeter_mm"),
                            "invalid_workshop_annotations",
                        )) if item.get("closing_points_perimeter_mm") is not None else "—",
                        item.get("continuous_width_mm"), item.get("finish_class"),
                        item.get("has_coupler"),
                    ] for item in annotations],
                    ["", "", "dimension", "dimension", "dimension", "", ""],
                )
        relationships = [
            _object(item, "invalid_assembly_relationship")
            for item in _array(fact.get("relationships"), "invalid_manufacturing_fact")
        ]
        if relationships:
            endpoints = {
                **labels["member"],
                **labels["reinforcement"],
                **labels["infill"],
                **labels["leaf_fact"],
            }
            body += "<h3>Matriz de ensamble</h3>" + _table(
                ["Relación", "Pieza origen", "Pieza destino"],
                [[item.get("relationship"),
                  endpoints.get(item.get("source_id"), item.get("source_id")),
                  endpoints.get(item.get("target_id"), item.get("target_id"))]
                 for item in relationships],
                ["", "hash", "hash"],
            )
        body += "</section>"
    return body + "</main>"


def _piece_labels(
    snapshot: dict[str, object],
) -> dict[str, dict[object, str]]:
    """Sequential workshop-facing piece codes (M-01, R-01, I-01, MAN-01) plus
    location codes (P-01, V-01, H-01) so emitted documents never print raw
    engineering ids. The frozen snapshot keeps the full identities."""
    member: dict[object, str] = {}
    reinforcement: dict[object, str] = {}
    infill: dict[object, str] = {}
    handle: dict[object, str] = {}
    bay: dict[object, str] = {}
    leaf: dict[object, str] = {}
    leaf_fact: dict[object, str] = {}
    for fact in _array(snapshot.get("manufacturing"), "invalid_frozen_revision_snapshot"):
        for item in _array(fact.get("members"), "invalid_manufacturing_fact"):
            member.setdefault(item.get("member_id"), f"M-{len(member) + 1:02d}")
            if item.get("bay_id") is not None:
                bay.setdefault(item.get("bay_id"), f"V-{len(bay) + 1:02d}")
        for item in _array(fact.get("reinforcements"), "invalid_manufacturing_fact"):
            reinforcement.setdefault(item.get("reinforcement_id"), f"R-{len(reinforcement) + 1:02d}")
        for item in _array(fact.get("infills"), "invalid_manufacturing_fact"):
            infill.setdefault(item.get("infill_id"), f"I-{len(infill) + 1:02d}")
        for item in _array(fact.get("handles"), "invalid_manufacturing_fact"):
            handle.setdefault(item.get("handle_id"), f"MAN-{len(handle) + 1:02d}")
        for item in [
            *_array(fact.get("infills"), "invalid_manufacturing_fact"),
            *_array(fact.get("handles"), "invalid_manufacturing_fact"),
        ]:
            if item.get("bay_id") is not None:
                bay.setdefault(item.get("bay_id"), f"V-{len(bay) + 1:02d}")
            if item.get("leaf_id") is not None:
                leaf.setdefault(item.get("leaf_id"), f"H-{len(leaf) + 1:02d}")
        for item in fact.get("leaves") if isinstance(fact.get("leaves"), list) else []:
            leaf_id = item.get("leaf_id")
            bay_id = item.get("bay_id")
            if leaf_id is not None:
                leaf.setdefault(leaf_id, f"H-{len(leaf) + 1:02d}")
                leaf_fact[item.get("leaf_fact_id")] = leaf[leaf_id]
            elif bay_id is not None:
                bay.setdefault(bay_id, f"V-{len(bay) + 1:02d}")
                leaf_fact[item.get("leaf_fact_id")] = bay[bay_id]
    position: dict[object, str] = {}
    for item in _array(snapshot.get("positions"), "invalid_frozen_revision_snapshot"):
        position[item.get("id")] = f"P{item.get('position_index')}"
    return {
        "member": member,
        "reinforcement": reinforcement,
        "infill": infill,
        "handle": handle,
        "bay": bay,
        "leaf": leaf,
        "leaf_fact": leaf_fact,
        "position": position,
    }


def _location(labels: dict[str, dict[object, str]], bay_id: object, leaf_id: object) -> str:
    bay = labels["bay"].get(bay_id, _value(bay_id))
    if leaf_id is None:
        return str(bay)
    return f"{bay} / {labels['leaf'].get(leaf_id, _value(leaf_id))}"


def _doc05(snapshot: dict[str, object]) -> str:
    if snapshot.get("production_allowed") is not True:
        raise DocumentaryError("production_document_blocked")
    if snapshot.get("documentary_complete") is not True:
        raise DocumentaryError("manufacturing_document_incomplete")
    purchase = _object(snapshot.get("purchase_requirements"), "invalid_purchase_projection")
    groups = [_object(item, "invalid_stock_group")
              for item in _array(purchase.get("stock_groups"), "invalid_purchase_projection")]
    labels = _piece_labels(snapshot)
    body, _ = _revision_header(snapshot, "Plan de corte 1D", "DOC-05", workshop=True)
    for group in groups:
        body += (
            f"<h2>{escape(_value(group.get('purchasing_sku')))} · "
            f"{escape(_value(group.get('source_kind')))}</h2>"
            f"<p><strong>Stock físico:</strong> {escape(_value(group.get('physical_stock_identity')))} · "
            f"<strong>Largo:</strong> {escape(_value(group.get('stock_length_mm')))} mm · "
            f"<strong>Barras:</strong> {escape(_value(group.get('purchased_bar_count')))}</p>"
        )
        for bar_value in _array(group.get("bars"), "invalid_stock_group"):
            bar = _object(bar_value, "invalid_cut_bar")
            cuts = [_object(item, "invalid_cut_piece")
                    for item in _array(bar.get("cuts"), "invalid_cut_bar")]
            body += (
                f"<h3>Barra {escape(_value(bar.get('bar_index')))} · remanente "
                f"{escape(_value(bar.get('remainder_mm')))} mm</h3>"
                + _table(
                    ["Sec.", "Pieza física", "Posición", "Vano / hoja", "SKU taller", "Corte mm", "Ángulos"],
                    [[cut.get("sequence"),
                      labels["member"].get(cut.get("piece_id"),
                                           labels["reinforcement"].get(cut.get("piece_id"), cut.get("piece_id"))),
                      labels["position"].get(cut.get("source_position_id"), cut.get("source_position_id")),
                      _location(labels, cut.get("bay_id"), cut.get("leaf_id")),
                      cut.get("workshop_sku"), cut.get("length_mm"),
                      f"{_value(cut.get('angle_left'))}° / {_value(cut.get('angle_right'))}°"]
                     for cut in cuts], ["", "hash", "", "", "", "dimension", ""]
                )
            )
    return body + "</main>"


def _doc06(snapshot: dict[str, object]) -> str:
    if snapshot.get("production_allowed") is not True:
        raise DocumentaryError("production_document_blocked")
    if snapshot.get("documentary_complete") is not True:
        raise DocumentaryError("manufacturing_document_incomplete")
    inspector = [_object(item, "invalid_inspector_evidence")
                 for item in _array(snapshot.get("inspector"), "invalid_frozen_revision_snapshot")]
    body, _ = _revision_header(snapshot, "Checklist de control final", "DOC-06", workshop=True)
    tolerance = "—"
    if inspector:
        config = _object(inspector[0].get("config"), "invalid_inspector_evidence")
        tolerance = _value(_object(config.get("R10"), "invalid_inspector_evidence").get("tolerance_mm"))
    rows = [
        ["Escuadra de diagonales", f"Diferencia ≤ {tolerance} mm", "□", "________________"],
        ["Burletes y estanqueidad", "Continuidad visual y cierre", "□", "________________"],
        ["Desagües", "Libres y según diseño congelado", "□", "________________"],
        ["Herrajes", "Operación y calibración física", "□", "________________"],
        ["Vidrios / paneles", "Sin daño y correctamente retenidos", "□", "________________"],
    ]
    body += _table(["Control", "Criterio esperado", "Sin completar", "Medición / observación"], rows)
    body += (
        "<p><strong>Operador:</strong> ______________________________</p>"
        "<p><strong>Fecha de ejecución QC:</strong> __________________</p>"
        "<p><strong>Resultado físico:</strong> ☐ Pendiente &nbsp; ☐ Conforme &nbsp; ☐ No conforme</p>"
        "<div class=\"signature\"></div><p>Firma responsable QC</p></main>"
    )
    return body


def _doc07(snapshot: dict[str, object]) -> str:
    project = _object(snapshot.get("project"), "invalid_frozen_revision_snapshot")
    pricing = _object(snapshot.get("pricing"), "invalid_frozen_revision_snapshot")
    input_snapshot = _object(pricing.get("input_snapshot"), "invalid_pricing_evidence")
    costs = _array(input_snapshot.get("cost_lines"), "invalid_pricing_evidence")
    realized = _object(snapshot.get("realized_waste"), "invalid_frozen_revision_snapshot")
    body, _ = _revision_header(snapshot, "Informe ejecutivo de costos y margen", "DOC-07")
    body += '<p class="confidential">CONFIDENCIAL · SOLO PROPIETARIO</p>'
    body += _table(
        ["Posición", "Costo capturado"],
        [[_array(item, "invalid_pricing_evidence")[0], _array(item, "invalid_pricing_evidence")[1]]
         for item in costs], ["", "dimension"],
    )
    body += _table(
        ["Costo neto", "Venta neta", "Impuesto", "Venta total"],
        [[pricing.get("applied_total_cost_net"),
          project.get("total_price_net"), project.get("total_price_tax"),
          project.get("total_price_gross")]],
        ["dimension", "dimension", "", "dimension"],
    )
    status = realized.get("status")
    if status != "NOT_RECORDED" or realized.get("value") is not None:
        raise DocumentaryError("realized_waste_authority_invalid")
    body += "<h2>Merma realizada</h2><p><strong>NO REGISTRADA</strong> · valor: —</p></main>"
    return body


def _doc04(snapshot: dict[str, object]) -> str:
    order = _object(snapshot.get("order"), "invalid_order_snapshot")
    revision = _object(snapshot.get("revision"), "invalid_order_snapshot")
    if order.get("order_type") != "SUPPLIER_PROFILE_PO":
        raise DocumentaryError("document_scope_mismatch")
    lines = [_object(item, "invalid_order_line")
             for item in _array(snapshot.get("lines"), "invalid_order_snapshot")]
    pseudo_revision = {
        "project": {"code": order.get("project_code")},
        "revision": revision.get("revision_code"),
        "sealed_at": order.get("confirmed_at"),
        "bom_hash": revision.get("bom_hash"),
    }
    body, _ = _revision_header(pseudo_revision, "Pedido de perfiles", "DOC-04", workshop=True)
    body += (
        f"<p><strong>Orden:</strong> {escape(_value(order.get('order_code')))} · "
        f"<strong>Proveedor:</strong> {escape(_value(order.get('supplier_name')))}</p>"
        + _table(
            ["Requisito", "Categoría", "SKU taller", "SKU compra", "Cantidad", "Unidad"],
            [[line.get("requirement_key"), line.get("category"),
              ", ".join(_value(item) for item in _array(line.get("technical_skus"), "invalid_order_line")),
              line.get("purchasing_sku"), line.get("quantity"), line.get("unit")]
             for line in lines], ["hash", "", "", "", "dimension", ""],
        )
        + "</main>"
    )
    return body


def render_pdf_document(
    document_type: str, snapshot: dict[str, object], *, pdf_identifier: str
) -> tuple[bytes, str]:
    from weasyprint import HTML

    if document_type == "DOC-01":
        body = _doc01(snapshot)
    elif document_type == "DOC-03":
        body = _doc03(snapshot)
    elif document_type == "DOC-04":
        body = _doc04(snapshot)
    elif document_type == "DOC-05":
        body = _doc05(snapshot)
    elif document_type == "DOC-06":
        body = _doc06(snapshot)
    elif document_type == "DOC-07":
        body = _doc07(snapshot)
    else:
        raise DocumentaryError("pdf_document_type_invalid")
    html = (
        "<!doctype html><html lang=\"es-CL\"><head><meta charset=\"utf-8\">"
        f"<style>{_CSS}</style></head><body>{body}</body></html>"
    )
    content = HTML(string=html, url_fetcher=_url_fetcher).write_pdf(
        pdf_identifier=pdf_identifier,
    )
    if not isinstance(content, bytes) or not content.startswith(b"%PDF-"):
        raise DocumentaryError("pdf_generation_failed")
    return content, _PDF_MEDIA


_PAYMENT_KIND_ES = {"ANTICIPO": "Anticipo", "PARCIAL": "Abono parcial", "SALDO": "Saldo"}
_PAYMENT_METHOD_ES = {
    "TRANSFERENCIA": "Transferencia",
    "EFECTIVO": "Efectivo",
    "TARJETA": "Tarjeta",
    "CHEQUE": "Cheque",
    "FLOW": "Flow",
    "OTRO": "Otro",
}


def _receipt_body(payload: dict[str, object]) -> str:
    project = _object(payload.get("project"), "invalid_receipt_project")
    payment = _object(payload.get("payment"), "invalid_receipt_payment")
    balance = _object(payload.get("balance"), "invalid_receipt_balance")
    issued_at = _value(payload.get("issued_at"))
    receipt_code = _value(payload.get("receipt_code"))
    currency = _value(project.get("currency"))
    kind = _PAYMENT_KIND_ES.get(_value(payment.get("kind")), _value(payment.get("kind")))
    method = _PAYMENT_METHOD_ES.get(
        _value(payment.get("method")), _value(payment.get("method"))
    )
    titleblock = (
        '<div class="titleblock">'
        f'<div class="tb-cell"><span class="tb-label">Proyecto</span>'
        f'<span class="tb-value">{escape(_value(project.get("code")))}</span></div>'
        f'<div class="tb-cell"><span class="tb-label">Documento</span>'
        '<span class="tb-value">Comprobante de pago</span></div>'
        f'<div class="tb-cell"><span class="tb-label">Recibo</span>'
        f'<span class="tb-value">{escape(receipt_code)}</span></div>'
        f'<div class="tb-cell"><span class="tb-label">Fecha</span>'
        f'<span class="tb-value">{escape(issued_at[:10])}</span></div>'
        f'<div class="tb-cell tb-wide"><span class="tb-label">Operación</span>'
        f'<span class="tb-value">{escape(_value(payment.get("operation_key")))}</span></div>'
        '<div class="tb-cell"><span class="tb-label">Página</span>'
        '<span class="tb-value"><span class="pg"></span></span></div>'
        "</div>"
    )
    body = (
        f'<main>{titleblock}'
        f'<div class="masthead">{_MITER}<div><div class="brand">DEKOPEN'
        '<span class="mark"></span></div></div>'
        '<div class="meta">'
        f"<strong>{escape(receipt_code)}</strong><br>"
        f"Comprobante de pago<br>{escape(issued_at)}</div></div>"
        '<div class="rule-stack"></div>'
        "<h1>Comprobante de pago</h1>"
        '<section class="hero"><p>Recibido de</p>'
        f"<h2>{escape(_value(project.get('client_name')))}</h2>"
        f"<p>RUT: {escape(_value(project.get('client_rut')))} · "
        f"{escape(_value(project.get('delivery_address')))}</p>"
        f'<p class="total">Monto: {escape(currency)} '
        f'{escape(_value(payment.get("amount")))}</p></section>'
    )
    body += (
        "<h2>Detalle del cobro</h2>"
        + _table(
            ["Concepto", "Método", "Referencia", "Fecha de cobro"],
            [[kind, method, payment.get("reference"), _value(payment.get("recorded_at"))[:10]]],
        )
    )
    note = _value(payment.get("note"))
    if note != "—":
        body += f"<p><strong>Nota:</strong> {escape(note)}</p>"
    body += (
        "<h2>Estado del trato</h2>"
        + _table(
            ["Total cotizado", "Cobrado", "Saldo"],
            [
                [
                    f"{currency} {_value(balance.get('deal_total'))}",
                    f"{currency} {_value(balance.get('collected'))}",
                    f"{currency} {_value(balance.get('remaining'))}",
                ]
            ],
            ["", "", "dimension"],
        )
        + "<div class=\"signoff\"><div class=\"signature\"></div>"
        + "<p class=\"muted\">Recibido por</p></div></main>"
    )
    return body


def render_payment_receipt(
    payload: dict[str, object], *, pdf_identifier: str
) -> tuple[bytes, str]:
    from weasyprint import HTML

    html = (
        "<!doctype html><html lang=\"es-CL\"><head><meta charset=\"utf-8\">"
        f"<style>{_CSS}</style></head><body>{_receipt_body(payload)}</body></html>"
    )
    content = HTML(string=html, url_fetcher=_url_fetcher).write_pdf(
        pdf_identifier=pdf_identifier,
    )
    if not isinstance(content, bytes) or not content.startswith(b"%PDF-"):
        raise DocumentaryError("pdf_generation_failed")
    return content, _PDF_MEDIA


def _dispatch_note_body(payload: dict[str, object]) -> str:
    order = _object(payload.get("order"), "invalid_dispatch_note_order")
    project = _object(payload.get("project"), "invalid_dispatch_note_project")
    totals = _object(payload.get("totals"), "invalid_dispatch_note_totals")
    dispatch = _object(payload.get("dispatch"), "invalid_dispatch_note_dispatch")
    units = payload.get("units") or []
    issued_at = _value(payload.get("issued_at"))
    note_code = _value(payload.get("note_code"))
    titleblock = (
        '<div class="titleblock">'
        f'<div class="tb-cell"><span class="tb-label">Proyecto</span>'
        f'<span class="tb-value">{escape(_value(project.get("code")))}</span></div>'
        f'<div class="tb-cell"><span class="tb-label">Documento</span>'
        '<span class="tb-value">Guía de despacho</span></div>'
        f'<div class="tb-cell"><span class="tb-label">Guía</span>'
        f'<span class="tb-value">{escape(note_code)}</span></div>'
        f'<div class="tb-cell"><span class="tb-label">Fecha</span>'
        f'<span class="tb-value">{escape(issued_at[:10])}</span></div>'
        f'<div class="tb-cell tb-wide"><span class="tb-label">Orden</span>'
        f'<span class="tb-value">{escape(_value(order.get("code")))}</span></div>'
        '<div class="tb-cell"><span class="tb-label">Página</span>'
        '<span class="tb-value"><span class="pg"></span></span></div>'
        "</div>"
    )
    body = (
        f'<main>{titleblock}'
        f'<div class="masthead">{_MITER}<div><div class="brand">DEKOPEN'
        '<span class="mark"></span></div></div>'
        '<div class="meta">'
        f"<strong>{escape(note_code)}</strong><br>"
        f"Guía de despacho<br>{escape(issued_at)}</div></div>"
    )
    body += (
        '<div class="rule-stack"></div>'
        "<h1>Guía de despacho</h1>"
        '<section class="hero"><p>Destinatario</p>'
        f"<h2>{escape(_value(project.get('client_name')))}</h2>"
        f"<p>RUT: {escape(_value(project.get('client_rut')))}</p>"
        f"<p>{escape(_value(project.get('delivery_address')))}</p>"
        f'<p class="total">Unidades: {escape(_value(totals.get("units")))}</p></section>'
    )
    if units:
        body += (
            "<h2>Bultos</h2>"
            + _table(
                ["Etiqueta", "Perfiles", "Refuerzos", "Vidrios", "Paneles", "Herrajes"],
                [
                    [
                        unit.get("label_code"),
                        unit.get("profiles"),
                        unit.get("reinforcements"),
                        unit.get("glasses"),
                        unit.get("panels"),
                        unit.get("hardware"),
                    ]
                    for unit in units
                ],
                ["", "dimension", "dimension", "dimension", "dimension", "dimension"],
            )
        )
    else:
        body += (
            "<h2>Bultos</h2><p class=\"muted\">Sin manifiesto de embalaje "
            "registrado — la orden se despacha sin desglose por bulto.</p>"
        )
    note = _value(dispatch.get("note"))
    if note != "—":
        body += f"<p><strong>Nota:</strong> {escape(note)}</p>"
    body += (
        "<h2>Resumen de contenido</h2>"
        + _table(
            ["Perfiles", "Refuerzos", "Vidrios", "Paneles", "Herrajes"],
            [
                [
                    totals.get("profiles"),
                    totals.get("reinforcements"),
                    totals.get("glasses"),
                    totals.get("panels"),
                    totals.get("hardware"),
                ]
            ],
            ["dimension", "dimension", "dimension", "dimension", "dimension"],
        )
        + "<div class=\"signoff\"><div class=\"signature\"></div>"
        + "<p class=\"muted\">Despachado por / Recibido conforme</p></div></main>"
    )
    return body


def render_dispatch_note(
    payload: dict[str, object], *, pdf_identifier: str
) -> tuple[bytes, str]:
    from weasyprint import HTML

    html = (
        "<!doctype html><html lang=\"es-CL\"><head><meta charset=\"utf-8\">"
        f"<style>{_CSS}</style></head><body>{_dispatch_note_body(payload)}</body></html>"
    )
    content = HTML(string=html, url_fetcher=_url_fetcher).write_pdf(
        pdf_identifier=pdf_identifier,
    )
    if not isinstance(content, bytes) or not content.startswith(b"%PDF-"):
        raise DocumentaryError("pdf_generation_failed")
    return content, _PDF_MEDIA
