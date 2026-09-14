"""Frozen-authority PDF producers for DOC-01, DOC-03 through DOC-07."""

from __future__ import annotations

from decimal import Decimal
from html import escape
from typing import NoReturn

from documents.repository import DocumentaryError

_PDF_MEDIA = "application/pdf"
_CSS = """
@page { size: letter portrait; margin: 14mm 12mm 18mm; @bottom-left { content: string(bom-identity); font: 7pt monospace; color: #64748b; } @bottom-right { content: "Página " counter(page) " de " counter(pages); font: 8pt sans-serif; color: #64748b; } }
* { box-sizing: border-box; } body { color: #172033; font: 9.5pt Arial, sans-serif; margin: 0; } main { string-set: bom-identity attr(data-bom); } h1 { font-size: 23pt; margin: 0 0 4mm; letter-spacing: -0.5pt; } h2 { font-size: 13pt; margin: 7mm 0 2mm; border-bottom: 1px solid #bcc6d6; padding-bottom: 1.5mm; } h3 { font-size: 10pt; margin: 4mm 0 1.5mm; } p { margin: 1.5mm 0; } .masthead { display: flex; justify-content: space-between; border-bottom: 3px solid #163b66; padding-bottom: 4mm; margin-bottom: 6mm; } .brand { color: #163b66; font-weight: 800; letter-spacing: 1px; } .meta { text-align: right; color: #475569; } .hero { background: #eef3f8; border-left: 4px solid #163b66; padding: 5mm; margin: 4mm 0 7mm; } .total { font-size: 18pt; font-weight: 800; color: #163b66; } table { width: 100%; border-collapse: collapse; margin: 2mm 0 4mm; table-layout: fixed; } th { background: #e7edf4; color: #1e293b; font-size: 8pt; text-transform: uppercase; letter-spacing: .25pt; } th, td { border: 1px solid #cbd5e1; padding: 1.8mm; vertical-align: top; overflow-wrap: anywhere; } .workshop h1 { font-size: 18pt; } .workshop th { background: #20262f; color: #ffffff; } .dimension { font-size: 12pt; font-weight: 800; } .hash { font: 7.5pt monospace; overflow-wrap: anywhere; } .break-avoid { break-inside: avoid; } .blank { display: inline-block; width: 5mm; height: 5mm; border: 1.2px solid #111827; vertical-align: middle; } .confidential { color: #991b1b; font-weight: 800; } .muted { color: #64748b; } .signature { height: 18mm; border-bottom: 1px solid #334155; margin-top: 8mm; }
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


def _deny_url_fetch(url: str, *args: object, **kwargs: object) -> NoReturn:
    raise DocumentaryError(f"External PDF resource forbidden: {url}")


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


def _revision_header(snapshot: dict[str, object], title: str, workshop: bool = False) -> tuple[str, str]:
    project = _object(snapshot.get("project"), "invalid_frozen_revision_snapshot")
    bom_hash = _value(snapshot.get("bom_hash"))
    class_name = "workshop" if workshop else ""
    header = (
        f'<div class="masthead"><div><div class="brand">DEKOPEN</div>'
        f"<h1>{escape(title)}</h1></div><div class=\"meta\">"
        f"<strong>{escape(_value(project.get('code')))}</strong><br>"
        f"Revisión {escape(_value(snapshot.get('revision')))}<br>"
        f"{escape(_value(snapshot.get('sealed_at')))}</div></div>"
    )
    return f'<main class="{class_name}" data-bom="{escape(bom_hash)}">{header}', bom_hash


def _doc01(snapshot: dict[str, object]) -> str:
    project = _object(snapshot.get("project"), "invalid_frozen_revision_snapshot")
    positions = [_object(item, "invalid_frozen_position")
                 for item in _array(snapshot.get("positions"), "invalid_frozen_revision_snapshot")]
    opening_rows = []
    for position in positions:
        specs = _glass_specs(position.get("parametric_tree"))
        opening_rows.append([
            position.get("position_index"), position.get("location_tag"),
            f"{_value(position.get('width_mm'))} × {_value(position.get('height_mm'))}",
            position.get("quantity"), ", ".join(specs) or "Panel declarado",
            f"{_value(position.get('color_interior'))} / {_value(position.get('color_exterior'))}",
        ])
    body, _ = _revision_header(snapshot, "Cotización comercial")
    body += (
        '<section class="hero"><p>Preparado para</p>'
        f"<h2>{escape(_value(project.get('client_name')))}</h2>"
        f"<p>{escape(_value(project.get('delivery_address')))}</p>"
        f'<p class="total">Total: {escape(_value(project.get("currency")))} '
        f'{escape(_value(project.get("total_price_gross")))}</p></section>'
        "<h2>Solución propuesta</h2>"
        + _table(["Pos.", "Ubicación", "Dimensiones mm", "Cant.", "Relleno", "Acabado"], opening_rows)
        + "<h2>Resumen comercial</h2>"
        + _table(["Neto", "Impuesto", "Total"], [[
            project.get("total_price_net"), project.get("total_price_tax"),
            project.get("total_price_gross"),
        ]], ["", "", "dimension"])
        + f"<h2>Condiciones</h2><p><strong>Pago:</strong> {escape(_value(project.get('payment_terms')))}</p>"
        + f"<p><strong>Oferta válida hasta:</strong> {escape(_value(project.get('quotation_valid_until')))}</p>"
        + f"<p>{escape(_value(project.get('notes_commercial')))}</p>"
        + "<div class=\"signature\"></div><p class=\"muted\">Aceptación del cliente</p></main>"
    )
    return body


def _doc03(snapshot: dict[str, object]) -> str:
    if snapshot.get("production_allowed") is not True:
        raise DocumentaryError("production_document_blocked")
    if snapshot.get("documentary_complete") is not True:
        raise DocumentaryError("manufacturing_document_incomplete")
    facts = [_object(item, "invalid_manufacturing_fact")
             for item in _array(snapshot.get("manufacturing"), "invalid_frozen_revision_snapshot")]
    body, _ = _revision_header(snapshot, "Orden de trabajo de taller", workshop=True)
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
                ["Miembro físico", "Rol / slot", "SKU taller", "Corte mm", "Ángulos", "Referencia X/Y"],
                [[
                    member.get("member_id"),
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
                ["Refuerzo", "Miembro padre", "SKU acero", "Corte mm", "Ángulos"],
                [[item.get("reinforcement_id"), item.get("parent_member_id"),
                  item.get("workshop_sku"), item.get("cut_length_mm"),
                  f"{_value(item.get('angle_left'))}° / {_value(item.get('angle_right'))}°"]
                 for item in reinforcements], ["hash", "hash", "", "dimension", ""]
            )
        if infills:
            body += _table(
                ["Relleno", "Vano / hoja", "Especificación", "Dimensiones mm", "Retención"],
                [[item.get("infill_id"), f"{_value(item.get('bay_id'))} / {_value(item.get('leaf_id'))}",
                  item.get("composition"),
                  f"{_value(_object(item.get('rect'), 'invalid_infill_rect').get('width_mm'))} × "
                  f"{_value(_object(item.get('rect'), 'invalid_infill_rect').get('height_mm'))}",
                  "Junquillos identificados en matriz"] for item in infills],
                ["hash", "", "", "dimension", ""],
            )
        if handles:
            body += _table(
                ["Manilla", "Vano / hoja", "Miembro host", "Punto X/Y mm", "Referencia vertical"],
                [[item.get("handle_id"), f"{_value(item.get('bay_id'))} / {_value(item.get('leaf_id'))}",
                  item.get("host_member_id"),
                  f"{_value(_object(item.get('point'), 'invalid_handle_point').get('x_mm'))} / "
                  f"{_value(_object(item.get('point'), 'invalid_handle_point').get('y_mm'))}",
                  item.get("vertical_reference")] for item in handles], ["hash", "", "hash", "dimension", ""]
            )
        body += "</section>"
    return body + "</main>"


def _doc05(snapshot: dict[str, object]) -> str:
    if snapshot.get("production_allowed") is not True:
        raise DocumentaryError("production_document_blocked")
    if snapshot.get("documentary_complete") is not True:
        raise DocumentaryError("manufacturing_document_incomplete")
    purchase = _object(snapshot.get("purchase_requirements"), "invalid_purchase_projection")
    groups = [_object(item, "invalid_stock_group")
              for item in _array(purchase.get("stock_groups"), "invalid_purchase_projection")]
    body, _ = _revision_header(snapshot, "Plan de corte 1D", workshop=True)
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
                    [[cut.get("sequence"), cut.get("piece_id"), cut.get("source_position_id"),
                      f"{_value(cut.get('bay_id'))} / {_value(cut.get('leaf_id'))}",
                      cut.get("workshop_sku"), cut.get("length_mm"),
                      f"{_value(cut.get('angle_left'))}° / {_value(cut.get('angle_right'))}°"]
                     for cut in cuts], ["", "hash", "", "", "", "dimension", ""]
                )
            )
    return body + "</main>"


def _doc06(snapshot: dict[str, object]) -> str:
    inspector = [_object(item, "invalid_inspector_evidence")
                 for item in _array(snapshot.get("inspector"), "invalid_frozen_revision_snapshot")]
    body, _ = _revision_header(snapshot, "Checklist de control final", workshop=True)
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
    body, _ = _revision_header(snapshot, "Informe ejecutivo de costos y margen")
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
    body, _ = _revision_header(pseudo_revision, "Pedido de perfiles", workshop=True)
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
    content = HTML(string=html, url_fetcher=_deny_url_fetch).write_pdf(
        pdf_identifier=pdf_identifier,
    )
    if not isinstance(content, bytes) or not content.startswith(b"%PDF-"):
        raise DocumentaryError("pdf_generation_failed")
    return content, _PDF_MEDIA
