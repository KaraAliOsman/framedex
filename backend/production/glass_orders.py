"""Read-only glass orders/labels. Every size comes from the sealed BOM."""

import csv
from html import escape
from io import StringIO
from uuid import UUID
from urllib.parse import urlencode

import segno
from django.conf import settings
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.serializers import ACTIVE_ORGANIZATION_HEADER
from authentication.errors import contract_error
from dekopen_engine.models import EngineResult
from dekopen_engine.glass_orders import supplier_glass_rows
from documents.repository import documentary_backend, one, decoded, DocumentaryError
from documents.views import documentary_scope, ERRORS
from documents.renderers import _CSS, _DEMO_NOTICE_CSS, _url_fetcher, _piece_labels
from production.views import public_production_errors, _READERS
from pricing.repository import json_text


class GlassOrderRowSerializer(serializers.Serializer):
    order_code = serializers.CharField()
    position_index = serializers.IntegerField()
    location = serializers.CharField()
    piece_index = serializers.IntegerField()
    width_mm = serializers.CharField()
    height_mm = serializers.CharField()
    integer_dimensions = serializers.BooleanField()
    quantity = serializers.IntegerField()
    composition = serializers.CharField()
    article_sku = serializers.CharField(allow_null=True)
    processing = serializers.JSONField(allow_null=True)
    instructions = serializers.ListField(child=serializers.CharField())
    label_codes = serializers.ListField(child=serializers.CharField())


class GlassLabelSerializer(serializers.Serializer):
    code = serializers.CharField()
    link = serializers.CharField()
    qr_svg = serializers.CharField()
    order_code = serializers.CharField()
    position_index = serializers.IntegerField()
    location = serializers.CharField()
    width_mm = serializers.CharField()
    height_mm = serializers.CharField()
    composition = serializers.CharField()
    bom_hash = serializers.CharField()


class GlassOrderAuthoritySerializer(serializers.Serializer):
    project_code = serializers.CharField()
    revision_code = serializers.CharField()
    bom_hash = serializers.CharField()
    order_codes = serializers.ListField(child=serializers.CharField())


class GlassOrderSerializer(serializers.Serializer):
    rows = GlassOrderRowSerializer(many=True)
    labels = GlassLabelSerializer(many=True)
    authority = serializers.CharField()
    revisions = GlassOrderAuthoritySerializer(many=True)


def glass_order(*, org_id, order_ids, app_url=""):
    output, labels, revisions = [], [], {}
    with documentary_backend():
        for order_id in order_ids:
            order = one("SELECT order_code,project_version_id,payload_json::text AS payload_json "
                "FROM public.orders WHERE org_id=%s AND id=%s AND order_type='WORKSHOP_OT'",
                [org_id, order_id], "work_order_not_found")
            version = one("SELECT snapshot_json::text AS snapshot_json,bom_hash,revision_code FROM public.project_versions WHERE id=%s AND org_id=%s",
                [order["project_version_id"], org_id], "work_order_missing_version")
            snapshot, payload = decoded(version["snapshot_json"]), decoded(order["payload_json"])
            authority_key = str(order["project_version_id"])
            revision = revisions.setdefault(authority_key, {
                "project_code": snapshot["project"]["code"], "revision_code": version["revision_code"],
                "bom_hash": version["bom_hash"], "order_codes": []})
            revision["order_codes"].append(order["order_code"])
            position = next((position for position in snapshot["positions"]
                if str(position.get("position_id") or position.get("id")) == str(payload["position_id"])), None)
            if position is None:
                raise DocumentaryError("work_order_missing_version")
            authority = next((item for item in snapshot.get("bom") or [] if str(item.get("position_id")) == str(payload["position_id"])), None)
            if authority is None or int(authority["quantity"]) != int(payload["quantity"]):
                raise DocumentaryError("work_order_missing_version")
            result = EngineResult.model_validate_json(json_text(authority["engine_result"]))
            frozen_labels = _piece_labels(snapshot)["infill"]
            bound_labels = {}
            bound_links = {}
            for piece in result.glasses:
                matching = []
                for fact in snapshot.get("manufacturing") or []:
                    if str(fact.get("position_id")) != str(payload["position_id"]):
                        continue
                    for infill in fact.get("infills") or []:
                        module_id = fact.get("module_id")
                        bay_id = f"{module_id}|{infill['bay_id']}" if module_id else infill.get("bay_id")
                        leaf_id = f"{module_id}|{infill['leaf_id']}" if module_id and infill.get("leaf_id") is not None else infill.get("leaf_id")
                        if infill.get("kind") == "GLASS" and bay_id == piece.bay_id and leaf_id == piece.leaf_id:
                            code = frozen_labels.get(infill.get("infill_id"))
                            if code:
                                matching.append(code)
                                bound_links[code] = str(infill["infill_id"])
                if len(matching) == int(payload["quantity"]):
                    bound_labels[(piece.bay_id, piece.leaf_id)] = tuple(matching)
            rows = supplier_glass_rows(order_code=order["order_code"], position_index=int(position["position_index"]),
                location=position.get("location_tag") or "Sin ubicación declarada", quantity=int(payload["quantity"]),
                pieces=result.glasses, labels=bound_labels,
                synthetic=bool(position.get("is_demo") or _synthetic_recipe(position.get("parametric_tree"))))
            for row in rows:
                output.append(row.model_dump(mode="json"))
                for code in row.label_codes:
                    params = {"order": str(order_id)}
                    if code in frozen_labels.values():
                        params["piece"] = bound_links[code]
                    link = app_url.rstrip("/") + "/production?" + urlencode(params)
                    qr = segno.make(link, micro=False).svg_inline(scale=2, border=2)
                    is_demo = any(instruction.startswith("DEMO") for instruction in row.instructions)
                    labels.append({"code": code, "link": link, "qr_svg": qr, "order_code": row.order_code,
                        "position_index": row.position_index, "location": row.location,
                        "width_mm": str(row.width_mm), "height_mm": str(row.height_mm),
                        "composition": ("DEMO · " if is_demo else "") + row.composition,
                        "bom_hash": version["bom_hash"]})
    authority_by_order = {code: (revision["project_code"], revision["revision_code"])
                          for revision in revisions.values() for code in revision["order_codes"]}
    output.sort(key=lambda row: (*authority_by_order[row["order_code"]], row["position_index"], row["piece_index"]))
    labels.sort(key=lambda label: (*authority_by_order[label["order_code"]], label["position_index"], label["code"]))
    return {"rows": output, "labels": labels, "revisions": list(revisions.values()),
            "authority": "Medidas del BOM sellado; exterior a interior. No recalculadas con el catálogo vigente."}


def _synthetic_recipe(value):
    if isinstance(value, dict):
        product = value.get("glass_product")
        return bool(isinstance(product, dict) and product.get("synthetic")) or any(_synthetic_recipe(item) for item in value.values())
    return isinstance(value, list) and any(_synthetic_recipe(item) for item in value)


def glass_csv(report):
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(["OT", "Posición", "Ubicación", "Ancho corte (mm)", "Alto corte (mm)", "Cantidad",
                     "Composición exterior a interior", "Procesos", "Instrucciones", "Etiquetas"])
    for row in report["rows"]:
        values = [row["order_code"], row["position_index"], row["location"],
            _exact_size(row["width_mm"]), _exact_size(row["height_mm"]), row["quantity"], row["composition"],
            _processing_label(row["processing"]),
            " · ".join(row["instructions"]), " | ".join(row["label_codes"])]
        writer.writerow(["'" + str(value) if str(value).startswith(("=", "+", "-", "@")) else value for value in values])
    return buffer.getvalue().encode("utf-8-sig")


def _exact_size(value):
    # Decimal formatting only. Fractional cuts retain their exact authority.
    from decimal import Decimal
    number = Decimal(value)
    return format(number.to_integral_value(), "f") if number == number.to_integral_value() else format(number, "f")


def _display_size(value):
    from decimal import Decimal
    integer, dot, fraction = format(Decimal(value).normalize(), "f").partition(".")
    return format(int(integer), ",").replace(",", "\u2009") + ("," + fraction if dot else "")


def glass_pdf(report):
    from weasyprint import HTML
    fingerprints = {code: revision["bom_hash"][:12] for revision in report["revisions"] for code in revision["order_codes"]}
    table = ""
    for row in report["rows"]:
        instructions = " · ".join(value for value in row["instructions"] if not value.startswith("DEMO"))
        table += (f"<tr><td><strong>{escape(row['order_code'])}</strong>"
                  f"<p>P{row['position_index']:02d} · {escape(row['location'])}</p>"
                  f"<small class='mono'>Huella {escape(fingerprints.get(row['order_code'], 'Sin dato'))}</small></td>"
                  f"<td class='mono'>{escape(_display_size(row['width_mm']))}<br>× {escape(_display_size(row['height_mm']))}<br>mm</td>"
                  f"<td class='mono qty'>{row['quantity']}</td><td>{escape(row['composition'])}</td>"
                  f"<td>{escape(_processing_label(row['processing']))}<p class='instruction'>{escape(instructions)}</p></td></tr>")
    labels = "".join(f"<div class='glass-label'><strong class='mono'>{escape(label['code'])}</strong><p>{escape(label['order_code'])} · P{label['position_index']:02d} · {escape(label['location'])}</p>"
        f"<p class='dimension'>{escape(_display_size(label['width_mm']))} × {escape(_display_size(label['height_mm']))} mm</p>"
        f"<p>{escape(label['composition'])}</p><div class='label-foot'>{label['qr_svg']}"
        f"<small class='mono'>BOM sellado<br>{escape(label['bom_hash'][:12])}</small></div></div>" for label in report["labels"])
    demo = "<p class='demo-notice'>DEMO · catálogo sintético; no certifica seguridad ni rendimiento térmico.</p>" if any(
        value.startswith("DEMO") for row in report["rows"] for value in row["instructions"]) else ""
    authorities = "; ".join(f"{item['project_code']} · {item['revision_code']} · {item['bom_hash'][:12]}" for item in report["revisions"])
    html = f"<!doctype html><html lang='es-CL'><head><meta charset='utf-8'><style>{_CSS}{_DEMO_NOTICE_CSS}" \
        ".mono{font-family:'IBM Plex Mono',monospace;font-variant-numeric:tabular-nums}.qty{text-align:right}" \
        "tr{break-inside:avoid}small,.instruction{font-size:8pt}.instruction{color:#465158}" \
        ".glass-labels{page-break-before:always}.glass-label{display:inline-block;vertical-align:top;width:88mm;min-height:55mm;border:0.3mm solid #465158;padding:3mm;margin:2mm;break-inside:avoid}.glass-label p{margin:2mm 0}.glass-label svg{width:18mm;height:18mm}.label-foot{display:flex;align-items:center;gap:4mm}" \
        f"</style></head><body>{demo}<div class='titleblock'><div class='tb-cell tb-wide'><span class='tb-label'>Documento</span><span class='tb-value'>Pedido de vidrio</span></div><div class='tb-cell'><span class='tb-label'>Fuente</span><span class='tb-value'>BOM sellado · huella por OT</span></div><div class='tb-cell'><span class='tb-label'>Página</span><span class='tb-value pg'></span></div></div>" \
        "<main><h1>Pedido de vidrio</h1><div class='rule-stack'></div><p>Solicite cada pieza a su medida exacta. Exterior a interior.</p>" \
        f"<p>{escape(report['authority'])}</p><p class='mono instruction'>{escape(authorities)}</p>" \
        f"<table><colgroup><col style='width:25%'><col style='width:14%'><col style='width:7%'><col style='width:27%'><col style='width:27%'></colgroup><thead><tr><th>OT · posición</th><th>Corte</th><th>Cant.</th><th>Composición</th><th>Procesos · instrucciones</th></tr></thead><tbody>{table}</tbody></table>" \
        f"<section class='glass-labels'><h2>Etiquetas de vidrio</h2>{labels}</section></main></body></html>"
    return HTML(string=html, url_fetcher=_url_fetcher).write_pdf()


def _processing_label(value):
    if not value:
        return "Sin procesos adicionales"
    edges = {"TOP":"superior", "BOTTOM":"inferior", "LEFT":"izquierdo", "RIGHT":"derecho"}
    return "; ".join(part for part in (
        "Pulido: " + ", ".join(edges[edge] for edge in value["polished_edges"]) if value.get("polished_edges") else "",
        f"Perforaciones: {value['holes']}" if value.get("holes") else "",
        f"Palillaje: {value['bars_vertical']} verticales y {value['bars_horizontal']} horizontales"
            if value.get("bars_vertical") or value.get("bars_horizontal") else "") if part) or "Sin procesos adicionales"


class ProductionGlassOrderView(APIView):
    @extend_schema(operation_id="production_glass_order", parameters=[ACTIVE_ORGANIZATION_HEADER,
        OpenApiParameter("orders", OpenApiTypes.STR, required=True, description="UUID de OT separados por coma; máximo 100."),
        OpenApiParameter("export_format", OpenApiTypes.STR, enum=["JSON", "CSV", "PDF"],
                         description="Vista JSON o archivo del pedido. No afecta la negociación HTTP.")],
        responses={(200, "application/json"): GlassOrderSerializer,
                   (200, "application/pdf"): OpenApiTypes.BINARY,
                   (200, "text/csv"): OpenApiTypes.BINARY, **ERRORS}, tags=["production"])
    def get(self, request):
        try:
            ids = [UUID(value) for value in request.query_params.get("orders", "").split(",")]
        except ValueError as error:
            raise contract_error(400, "glass_orders_invalid", "Selecciona las órdenes de taller del lote.") from error
        if not ids or len(ids) > 100 or len(ids) != len(set(ids)):
            raise contract_error(400, "glass_orders_invalid", "Selecciona entre 1 y 100 órdenes distintas.")
        format_name = request.query_params.get("export_format", "JSON")
        if format_name not in ("JSON", "PDF", "CSV"):
            raise contract_error(400, "glass_orders_format", "Elige PDF, CSV o la vista del pedido.")
        with public_production_errors(), documentary_scope(request, _READERS) as (_, _, org_id):
            try:
                report = glass_order(org_id=org_id, order_ids=ids, app_url=settings.DEKOPEN_PUBLIC_APP_URL)
            except ValueError as error:
                raise contract_error(422, "glass_order_authority_missing", "Sin dato · revisa la composición y cantidad de la revisión sellada.") from error
        if format_name == "JSON":
            return Response(GlassOrderSerializer(report).data)
        body = glass_csv(report) if format_name == "CSV" else glass_pdf(report)
        response = HttpResponse(body, content_type="text/csv; charset=utf-8" if format_name == "CSV" else "application/pdf")
        response["Content-Disposition"] = f'attachment; filename="pedido-vidrio.{format_name.lower()}"'
        return response
