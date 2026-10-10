"""Printable physical cut/remnant labels; reads never allocate stock or codes."""

from html import escape
from uuid import UUID

from django.db import transaction

from documents.preferences import document_preferences
from documents.repository import DocumentaryError, decoded, documentary_backend, one, rows
from documents.renderers import _CSS, _COLOR_ES, _url_fetcher
from production.cut_documents import angle, mm
from production.cut_manifest import grouped_cuts
from production.pieces import addressed_plan, add_remnant_codes, entity_address, physical_labels
from production.service import _optimization_fingerprint


def label_data(*, org_id: UUID, order_id: UUID, grouped: bool = False) -> dict:
    with transaction.atomic(), documentary_backend():
        order = one("SELECT id,order_code,payload_json,project_version_id FROM public.orders "
                    "WHERE id=%s AND org_id=%s AND order_type='WORKSHOP_OT'",
                    [str(order_id), str(org_id)], "work_order_not_found")
        payload = decoded(order["payload_json"])
        optimization = payload.get("optimization") or {}
        if not optimization or not optimization.get("bars"):
            raise DocumentaryError("cut_pack_requires_optimization")
        if optimization.get("invalidated"):
            raise DocumentaryError("plan_invalidated")
        snapshot = decoded(one("SELECT snapshot_json FROM public.project_versions WHERE id=%s AND org_id=%s",
                               [str(order["project_version_id"]),str(org_id)], "version_not_found")["snapshot_json"])
        preferences = document_preferences(one("SELECT document_preferences FROM public.tenancy_organizations WHERE id=%s",
                                           [str(org_id)], "organization_not_found")["document_preferences"])
        route = rows("SELECT sequence,code,label FROM public.production_steps WHERE order_id=%s AND org_id=%s ORDER BY sequence",
                     [str(order_id), str(org_id)])
        cut_steps = [step["sequence"] for step in route if step["code"] in ("CUT", "CUT_STEEL")]
        following = next((step["label"] for step in route if cut_steps and step["sequence"] > max(cut_steps)),
                         "Sin dato · consulta la ruta de la OT")
        fingerprint = _optimization_fingerprint(optimization)
        display = add_remnant_codes(addressed_plan(snapshot, optimization, order_id=order_id),org_id)
        labels = physical_labels(display,snapshot=snapshot,order_code=order["order_code"],
                                 fingerprint=fingerprint,next_station=following, route=route)
        if grouped:
            ranks = {piece["stable_id"]: rank for rank,piece in enumerate(
                piece for group in grouped_cuts(display) for piece in group["pieces"])}
            labels.sort(key=lambda label: ranks.get(label["stable_id"], len(ranks)))
        import segno

        for entry in [*((display.get("remnants") or {}).get("produced_bars") or []),
                      *((display.get("remnants") or {}).get("produced_sheets") or [])]:
            if not entry.get("id") or not entry.get("code"):
                continue  # A historical plan cannot invent an RT address on read.
            address = entity_address("/inventory",remnant=entry["id"],code=entry["code"])
            labels.append({"code":entry["code"],"stable_id":entry["id"],"qr_payload":address,
                "qr_svg":segno.make(address,error="m").svg_inline(border=4,scale=4,omitsize=True),
                "order_code":order["order_code"],"role_label":"Retazo", "length_mm":entry.get("remainder_mm"),
                "width_mm":entry.get("width_mm"),"height_mm":entry.get("height_mm"),
                "color":optimization.get("color"),"fingerprint":fingerprint[:16],
                "next_station":entry.get("rack_location") or "Sin dato · declara destino",
                "stock_notice":"Alta en stock al completar corte"})
    return {"order_code":order["order_code"],"fingerprint":fingerprint,"paper":preferences["piece_label_paper"],
            "is_demo": bool(snapshot.get("is_demo") or any(pos.get("is_demo") for pos in snapshot.get("positions") or [])),
            "labels":labels}


def labels_html(data: dict, *, paper: str | None = None) -> str:
    selected = paper or data["paper"]
    if selected not in ("LETTER", "A4", "ROLL_100_50"):
        raise DocumentaryError("piece_label_paper_invalid")
    roll = selected == "ROLL_100_50"
    size = "100mm 50mm" if roll else "letter portrait" if selected == "LETTER" else "A4 portrait"
    css = f"""
@page {{ size: {size}; margin: {"0" if roll else "3mm"}; }}
body {{ margin: 0; font-size: 8pt; }}
.physical-grid {{ display: block; }}
.physical-row {{ display: table; table-layout: fixed; border-spacing: 3mm;
 margin: -1.5mm; break-inside: avoid; }}
.physical-label {{ box-sizing: border-box; width: 100mm; height: 50mm;
 padding: 2.5mm; border: 0.3pt solid #465158; display: table-cell; vertical-align: top;
 font: 8pt 'IBM Plex Sans'; line-height: 1.2; }}
.physical-label h2 {{ font: 14pt/1.15 'IBM Plex Mono'; margin: 0 0 1mm; padding: 0; border: 0; color: #161C1F; }}
.physical-label p {{ margin: 0 0 0.8mm; font-size: 8pt; overflow-wrap: anywhere; }}
.label-qr {{ float: right; width: 24mm; height: 24mm; margin: 0 0 1mm 2mm; }}
.label-qr svg {{ display: block; width: 24mm; height: 24mm; }}
.label-measure,.label-address,.label-fingerprint {{ font: 8pt 'IBM Plex Mono'; font-variant-numeric: tabular-nums; }}
.label-measure {{ font-size: 11pt; }}
.label-fingerprint {{ clear: both; border-top: 0.3pt solid #CDD5D6; padding-top: 0.6mm; }}
.physical-roll {{ display: block; break-after: page; break-inside: avoid; border: 0; }}
"""
    body = '<main class="physical-grid">'
    labels = data["labels"]
    for offset in range(0,len(labels),1 if roll else 2):
        if not roll:
            body += '<div class="physical-row">'
        for label in labels[offset:offset+(1 if roll else 2)]:
            measure = (mm(label["length_mm"])+" mm" if label.get("length_mm") is not None else
                       mm(label.get("width_mm"))+" × "+mm(label.get("height_mm"))+" mm")
            location = ' · '.join(str(value) for value in (label.get("position"),
                        (f"Unidad {label['unit_index']}" if label.get("unit_index") is not None else None),
                        label.get("bay_code"),label.get("leaf_code")) if value)
            body += f'<article class="physical-label{ " physical-roll" if roll else ""}"><h2>{escape(label["code"])}</h2>'
            body += f'<div class="label-qr">{label["qr_svg"]}</div><p class="label-address">{escape(label["order_code"])}</p>'
            body += f'<p>{escape(location or label.get("stock_notice") or "Sin dato · consulta la OT")}</p>'
            body += f'<p>{escape(label.get("role_label") or "Sin dato · función histórica")}</p><p class="label-measure">{escape(measure)}</p>'
            if label.get("length_mm") is not None and label.get("role_label") != "Retazo":
                body += f'<p class="label-address">Izq. {angle(label.get("angle_left"))} · Der. {angle(label.get("angle_right"))}</p>'
            body += f'<p>{escape(_COLOR_ES.get(str(label.get("color")),str(label.get("color") or "Sin dato")))}</p>'
            body += f'<p>Siguiente: {escape(label["next_station"])}</p>'
            if data.get("is_demo"):
                body += '<p>DEMO · Catálogo sintético, sin certificación.</p>'
            body += f'<p class="label-fingerprint">Huella {escape(label["fingerprint"])}</p></article>'
        if not roll:
            body += '</div>'
    body += '</main>'
    return '<!doctype html><html lang="es-CL"><head><meta charset="utf-8"><style>'+_CSS+css+'</style></head><body>'+body+'</body></html>'


def render_piece_labels(*, org_id: UUID, order_id: UUID, grouped: bool = False,
                        paper: str | None = None) -> tuple[bytes,str]:
    from weasyprint import HTML

    data = label_data(org_id=org_id,order_id=order_id,grouped=grouped)
    content = HTML(string=labels_html(data,paper=paper),url_fetcher=_url_fetcher).write_pdf()
    return content,f"{data['order_code']}-etiquetas-piezas.pdf"
