"""Private immutable reception sheet, using the shared document grammar."""

import base64
from html import escape

from documents.renderers import _CSS, _MITER, _brand_block, _cldate, _position_svg, _url_fetcher
from documents.preferences import ACCENTS, PAPERS, document_preferences


def render_field_act(payload, signature):
    from weasyprint import HTML

    ctx = payload["context"]
    prefs = document_preferences((ctx.get("organization") or {}).get("document_preferences"))
    css = _CSS.replace("letter portrait", PAPERS[prefs["paper"]]).replace("#075F5A", ACCENTS[prefs["accent"]])

    def text(value):
        return escape(str(value or "Sin dato"))

    checks = {(c["position_id"], c["unit_index"]): c for c in payload["checks"]}
    labels = {
        "installed": "Instalada",
        "levelled": "Nivelada",
        "sealed": "Sellada",
        "adjusted": "Regulada",
        "clean": "Limpia",
    }
    units = []
    for unit in ctx["units"]:
        design = unit["design"]
        drawing = _position_svg(
            {
                "parametric_tree": design["parametric_tree"],
                "width_mm": design["nominal_width_mm"],
                "height_mm": design["nominal_height_mm"],
            },
            dimensions=True,
        )
        evidence = checks.get((unit["position_id"], unit["unit_index"])) or {}
        checked = " · ".join(
            f"{label}: {'Sí' if evidence.get('checks', {}).get(key) else 'No acreditada'}"
            for key, label in labels.items()
        )
        if payload["kind"] == "SERVICE":
            checked = text(evidence.get("note"))
        photo = evidence.get("photo") or {}
        demo = "DEMO · catálogo sintético" if unit["is_demo"] else ""
        units.append(
            f'<section class="field-position"><h2>P{unit["position_index"]:02d} · U{unit["unit_index"]:02d} · {text(unit["location_tag"])}</h2><p>{text(unit["order_code"])} · {demo}</p><div class="field-elevation">{drawing}</div><p class="muted">Vista interior · cotas en mm</p><p>{checked}</p><p class="muted">Foto contextual conservada en el registro privado · huella {text(photo.get("file_sha256", "")[:12])}</p></section>'
        )
    incidents = "".join(
        f"<p>{text(c['code'])} · {text(c['description'])}</p>" for c in payload["incidents"]
    )
    cells = [
        ("Proyecto", ctx["project_code"]),
        ("Acta", payload["act_code"]),
        ("Revisión", ctx["revision_code"]),
        ("Fecha", _cldate(payload["issued_at"])),
        ("Huella de revisión", (ctx["snapshot_sha256"] or "Sin dato")[:12]),
    ]
    titleblock = '<div class="titleblock">' + "".join(
        f'<div class="tb-cell"><span class="tb-label">{label}</span><span class="tb-value">{text(value)}</span></div>'
        for label, value in cells
    )
    titleblock += '<div class="tb-cell"><span class="tb-label">Página</span><span class="tb-value"><span class="pg"></span></span></div></div>'
    title = (
        "Acta de servicio en obra" if payload["kind"] == "SERVICE" else "Acta de recepción en obra"
    )
    html = f"""<!doctype html><html lang="es-CL"><head><meta charset="utf-8"><style>{css}
    .field-elevation {{ width: 92mm; margin: 3mm 0; }}
    .field-elevation svg {{ width: 100%; height: 52mm; }}
    .field-position {{ break-inside: avoid; border-bottom: 0.3mm solid #CAD3D6; padding-bottom: 3mm; }}
    </style></head><body><main>{titleblock}
    <div class="masthead">{_MITER}{_brand_block(ctx.get("organization"))}<div class="meta"><strong>{text(payload["act_code"])}</strong><br>{text(_cldate(payload["issued_at"]))}</div></div>
    <div class="rule-stack"></div><h1>{title}</h1>
    <p>{text(ctx["project_code"])} · {text(ctx["project_name"])} · {text(ctx["revision_code"])}</p>
    <p><strong>Obra:</strong> {text(ctx["address"])} · {text(payload["visit_code"])}</p>
    {"".join(units)}<h2>Recepción del cliente</h2>
    <p>Usted acredita únicamente las unidades indicadas, con sus observaciones e incidencias conservadas. Esta acta no cierra las incidencias ni acredita otras unidades de la orden.</p>
    <p>{text(payload["receiver_name"])} · RUT {text(payload["receiver_rut"])}</p>
    <img alt="Firma de recepción" width="240" src="data:image/png;base64,{base64.b64encode(signature).decode("ascii")}">
    <h2>Observaciones e incidencias</h2><p>{text(payload["observations"])}</p>{incidents or "<p>Sin incidencias declaradas en esta visita.</p>"}
    <p class="muted">Documento inmutable. La evidencia permanece en el registro privado de terreno.</p></main></body></html>"""
    return HTML(string=html, url_fetcher=_url_fetcher).write_pdf(pdf_identifier=payload["act_code"])
