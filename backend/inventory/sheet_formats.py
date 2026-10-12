"""Source-backed sheet supply declarations, without stock movements.

Each declaration is an immutable inventory variant. Existing cut plans keep
their sealed dimensions; a new declaration affects only a human re-optimize.
"""

from decimal import Decimal
from uuid import UUID

from django.db import transaction

from dekopen_engine.documentary_canonical import documentary_sha256_v1
from documents.repository import DocumentaryError, decoded, documentary_backend, one, rows
from pricing.repository import json_text


def list_formats(*, org_id: UUID) -> dict:
    options = rows(
        """SELECT DISTINCT m.technical_sku AS sku, 'GLASS' AS kind,
                  m.technical_sku AS name, s.is_demo
           FROM public.glass_purchase_mappings m
           JOIN public.profile_systems s ON s.id=m.system_id
           WHERE m.org_id=%s OR (m.org_id IS NULL AND s.is_global)
           UNION
           SELECT a.sku, 'PANEL', a.name, s.is_demo
           FROM public.infill_articles a
           JOIN public.profile_systems s ON s.id=a.system_id
           WHERE a.is_active AND (a.org_id=%s OR (a.org_id IS NULL AND s.is_global))
           ORDER BY kind, sku""", [str(org_id), str(org_id)],
    )
    items = rows(
        """SELECT id,sku,name,category,attributes FROM public.inventory_items
           WHERE org_id=%s AND attributes ? 'sheet_width_mm'
             AND attributes ? 'sheet_height_mm' ORDER BY sku,variant_key""", [str(org_id)],
    )
    return {"options": options, "items": [{
        "id": str(item["id"]), "sku": item["sku"], "name": item["name"],
        "kind": item["category"],
        "technical_sku": decoded(item["attributes"]).get("glass_sku") or item["sku"],
        "width_mm": str(decoded(item["attributes"])["sheet_width_mm"]),
        "height_mm": str(decoded(item["attributes"])["sheet_height_mm"]),
        "edge_trim_mm": str(decoded(item["attributes"]).get("sheet_edge_trim_mm") or "0"),
        "supplier": decoded(item["attributes"]).get("supplier_name"),
        "source": decoded(item["attributes"]).get("sheet_source"),
        "is_demo": bool(decoded(item["attributes"]).get("sheet_is_demo")),
    } for item in items]}


def declare_format(*, org_id: UUID, data: dict) -> tuple[dict, bool]:
    option = next((item for item in list_formats(org_id=org_id)["options"]
                   if item["sku"] == data["technical_sku"] and item["kind"] == data["kind"]), None)
    if option is None:
        raise DocumentaryError("sheet_substrate_not_found", detail="Selecciona un vidrio o panel visible en tu catálogo.")
    if data["edge_trim_mm"] * 2 >= min(data["width_mm"], data["height_mm"]):
        raise DocumentaryError("sheet_usable_size_invalid", detail="El despunte debe dejar ancho y alto útiles positivos.")
    # A panel is matched by its physical article; glass by declared substrate.
    sku = data["technical_sku"] if data["kind"] == "PANEL" else data["sku"]
    attributes = {
        "sheet_width_mm": str(data["width_mm"]), "sheet_height_mm": str(data["height_mm"]),
        "sheet_edge_trim_mm": str(data["edge_trim_mm"]),
        "supplier_name": data["supplier"], "sheet_source": data["source"],
        "sheet_is_demo": option["is_demo"], "purchasing_sku": data["sku"],
    }
    if data["kind"] == "GLASS":
        attributes["glass_sku"] = data["technical_sku"]
    variant = "FORMAT:" + documentary_sha256_v1(attributes)
    with transaction.atomic(), documentary_backend():
        # The existing stock ledger addresses sheet supply by commercial SKU.
        # Serialize declarations so this identity cannot describe incompatible
        # dimensions/substrates; another physical format needs its own SKU.
        rows("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", [f"sheet-format:{org_id}:{sku}"])
        existing = rows(
            """SELECT attributes FROM public.inventory_items WHERE org_id=%s AND sku=%s
               AND attributes ? 'sheet_width_mm' AND attributes ? 'sheet_height_mm'""",
            [str(org_id), sku],
        )
        for item in existing:
            previous = decoded(item["attributes"])
            if (Decimal(str(previous["sheet_width_mm"])) != data["width_mm"]
                    or Decimal(str(previous["sheet_height_mm"])) != data["height_mm"]
                    or Decimal(str(previous.get("sheet_edge_trim_mm") or "0")) != data["edge_trim_mm"]
                    or previous.get("glass_sku") != attributes.get("glass_sku")):
                raise DocumentaryError("sheet_supply_identity_conflict", detail=
                    "Ese código de compra ya identifica otro formato o vidrio. Declara un código de compra distinto para este suministro.")
        inserted = rows(
            """INSERT INTO public.inventory_items(org_id,sku,name,category,unit,variant_key,attributes)
               VALUES (%s,%s,%s,%s,'M2',%s,%s::jsonb)
               ON CONFLICT (org_id,sku,variant_key) DO NOTHING RETURNING id""",
            [str(org_id), sku, data["supplier"], data["kind"], variant, json_text(attributes)],
        )
        item = one("SELECT id FROM public.inventory_items WHERE org_id=%s AND sku=%s AND variant_key=%s",
                   [str(org_id), sku, variant], "sheet_format_not_found")
    return {"id": str(item["id"])}, bool(inserted)
