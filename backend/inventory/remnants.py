"""Remnant inventory — per-instance offcut ledger (mandate §6).

A remnant is one physical piece of leftover material: a bar drop or a sheet
offcut with exact dimensions and a producing stock identity. The optimizer
consumes AVAILABLE remnants before purchasing; a work-order plan reserves
what it claims, and completing the CUT step consumes them. Rows are never
deleted — a consumed remnant stays traceable to the order that produced it.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID
from urllib.parse import urlencode

from django.conf import settings
from django.db import transaction

from dekopen_engine.cutting import RemnantBar
from dekopen_engine.nesting import SheetRemnant
from documents.repository import DocumentaryError, documentary_backend, one, rows
from documents.preferences import document_preferences


def _remnant_row(row: dict[str, object]) -> dict[str, object]:
    return {
        "id": str(row["id"]),
        "code": row["code"],
        "kind": row["kind"],
        "stock_authority_id": (
            str(row["stock_authority_id"]) if row["stock_authority_id"] else None
        ),
        "sheet_workshop_sku": row["sheet_workshop_sku"],
        "physical_stock_identity": (
            str(row["physical_stock_identity"])
            if row["physical_stock_identity"]
            else None
        ),
        "material": row["material"],
        "color": row["color"],
        "length_mm": row["length_mm"],
        "width_mm": row["width_mm"],
        "height_mm": row["height_mm"],
        "status": row["status"],
        "origin": row["origin"],
        "origin_order_id": (
            str(row["origin_order_id"]) if row["origin_order_id"] else None
        ),
        "reserved_order_id": (
            str(row["reserved_order_id"]) if row["reserved_order_id"] else None
        ),
        "consumed_order_id": (
            str(row["consumed_order_id"]) if row["consumed_order_id"] else None
        ),
        "rack_location": row["rack_location"],
        "notes": row["notes"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


_SELECT = """
    SELECT id, private.entity_code(org_id, 'RT', id) AS code,
           kind, stock_authority_id, sheet_workshop_sku,
           physical_stock_identity, material, color,
           length_mm, width_mm, height_mm, status, origin,
           origin_order_id, reserved_order_id, consumed_order_id,
           rack_location, notes, created_at, updated_at
    FROM public.inventory_remnants
"""


def list_remnants(
    *,
    org_id: UUID,
    kind: str | None = None,
    status: str | None = None,
) -> dict[str, object]:
    clauses = ["org_id = %s"]
    parameters: list[object] = [str(org_id)]
    if kind is not None:
        if kind not in ("BAR", "SHEET"):
            raise DocumentaryError("remnant_kind_unknown")
        clauses.append("kind = %s")
        parameters.append(kind)
    if status is not None:
        if status not in ("AVAILABLE", "RESERVED", "CONSUMED", "SCRAPPED"):
            raise DocumentaryError("remnant_status_unknown")
        clauses.append("status = %s")
        parameters.append(status)
    items = rows(
        f"{_SELECT} WHERE {' AND '.join(clauses)}"
        " ORDER BY kind, status, length_mm NULLS LAST, width_mm NULLS LAST, id"
        " LIMIT 500",
        parameters,
    )
    # Resolve the work order a remnant is reserved for (or came from) into its
    # human code — the operator never sees a UUID.
    order_ids = {
        str(value)
        for r in items
        for value in (
            r["reserved_order_id"],
            r["origin_order_id"],
            r["consumed_order_id"],
        )
        if value
    }
    codes = (
        {
            str(row["id"]): str(row["order_code"])
            for row in rows(
                "SELECT id, CASE WHEN order_type='WORKSHOP_OT' THEN order_code ELSE private.entity_code(org_id, 'OC', id, order_code) END AS order_code FROM public.orders"
                " WHERE org_id = %s AND id = ANY(%s::uuid[])",
                [str(org_id), sorted(order_ids)],
            )
        }
        if order_ids
        else {}
    )
    remnants = [_remnant_row(r) for r in items]
    for entry in remnants:
        entry["reserved_order_code"] = codes.get(entry["reserved_order_id"])
        entry["origin_order_code"] = codes.get(entry["origin_order_id"])
    # Resolve the bar authority into the commercial SKU a rack worker reads —
    # a remnant with no article identity is just an anonymous drop. Sheet
    # remnants already carry sheet_workshop_sku.
    authority_ids = [
        entry["stock_authority_id"] for entry in remnants if entry["stock_authority_id"]
    ]
    skus: dict[str, dict] = {}
    if authority_ids:
        for table in ("profile_purchase_mappings", "reinforcement_articles", "catalog_color_skus"):
            color_column = "finish" if table == "catalog_color_skus" else "stock_color"
            for row in rows(
                f"SELECT id::text AS id, commercial_sku,{color_column} AS stock_color,physical_stock_identity FROM public.{table} "
                "WHERE id = ANY(%s::uuid[])",
                [authority_ids],
            ):
                skus[str(row["id"])] = row
    preferences = document_preferences(one("SELECT document_preferences FROM public.tenancy_organizations WHERE id=%s",
                                          [str(org_id)],"organization_not_found")["document_preferences"])
    limit = int(preferences["remnant_age_days"])
    for entry in remnants:
        entry["article_sku"] = (
            (skus.get(entry["stock_authority_id"]) or {}).get("commercial_sku") if entry["stock_authority_id"] else None
        )
        authority=skus.get(entry["stock_authority_id"]) or {}
        entry["color"] = entry["color"] or authority.get("stock_color")
        entry["physical_stock_identity"] = entry["physical_stock_identity"] or authority.get("physical_stock_identity")
        entry["age_days"] = max(0,(datetime.now(timezone.utc)-entry["created_at"]).days)
        entry["age_alert"] = entry["status"] == "AVAILABLE" and entry["age_days"] >= limit
    events=rows("SELECT e.*,private.entity_code(e.org_id,'RT',e.remnant_id) AS remnant_code,o.order_code "
                "FROM public.inventory_remnant_events e LEFT JOIN public.orders o ON o.id=e.order_id AND o.org_id=e.org_id "
                "WHERE e.org_id=%s ORDER BY e.created_at DESC,e.id LIMIT 100",[str(org_id)])
    return {"remnants": remnants,"age_limit_days":limit,"events":events}


def list_bar_authorities(*, org_id: UUID) -> dict[str, object]:
    """Active BAR stock authorities the operator can register a drop against —
    profiles and reinforcements merged into one pick list, same scope the
    optimizer feeds from (org rows plus global ones)."""
    profile = rows(
        """
        SELECT id::text AS id, commercial_sku,
               physical_stock_identity::text AS physical_stock_identity,
               stock_color
        FROM public.profile_purchase_mappings
        WHERE (org_id = %s OR org_id IS NULL) AND is_active
        ORDER BY commercial_sku
        """,
        [str(org_id)],
    )
    reinforcement = rows(
        """
        SELECT id::text AS id, commercial_sku,
               physical_stock_identity::text AS physical_stock_identity,
               stock_color
        FROM public.reinforcement_articles
        WHERE (org_id = %s OR org_id IS NULL) AND is_active
        ORDER BY commercial_sku
        """,
        [str(org_id)],
    )
    finished = rows(
        "SELECT id::text AS id,commercial_sku,physical_stock_identity,stock_color FROM catalog_color_skus "
        "WHERE (org_id=%s OR org_id IS NULL) AND is_active ORDER BY commercial_sku,stock_color",
        [str(org_id)])
    authorities = [
        {
            "id": row["id"],
            "commercial_sku": row["commercial_sku"],
            "physical_stock_identity": row["physical_stock_identity"],
            "stock_color": row["stock_color"],
            "source": source,
        }
        for source, found in (("PROFILE", [*profile,*finished]), ("REINFORCEMENT", reinforcement))
        for row in found
    ]
    return {"authorities": authorities}


def create_remnant(
    *,
    org_id: UUID,
    kind: str,
    stock_authority_id: UUID | None = None,
    sheet_workshop_sku: str | None = None,
    physical_stock_identity: str | None = None,
    material: str | None = None,
    color: str | None = None,
    length_mm: Decimal | None = None,
    width_mm: Decimal | None = None,
    height_mm: Decimal | None = None,
    rack_location: str | None = None,
    notes: str | None = None,
    origin: str = "MANUAL",
    origin_order_id: UUID | None = None,
) -> dict[str, object]:
    """Register one physical offcut into the pool. Manual declarations and
    produced leftovers share this write path — provenance stays honest via
    ``origin``."""
    if kind not in ("BAR", "SHEET"):
        raise DocumentaryError("remnant_kind_unknown")
    if kind == "BAR":
        if stock_authority_id is None or length_mm is None or length_mm <= 0:
            raise DocumentaryError("remnant_bar_dims_invalid")
    elif sheet_workshop_sku is None or width_mm is None or height_mm is None \
            or width_mm <= 0 or height_mm <= 0:
        raise DocumentaryError("remnant_sheet_dims_invalid")
    with transaction.atomic(), documentary_backend():
        if kind == "BAR":
            authority = _bar_identity(org_id, str(stock_authority_id))
            if (physical_stock_identity and str(physical_stock_identity) != str(authority["physical_stock_identity"])) or (
                color and color != authority["stock_color"]
            ):
                raise DocumentaryError("remnant_authority_mismatch", detail="El color o la identidad no coincide con el perfil del catálogo. Elige su suministro real.")
            physical_stock_identity = authority["physical_stock_identity"]
            color, material = authority["stock_color"], authority["material"]
            if length_mm > Decimal(str(authority["stock_length_mm"])):
                raise DocumentaryError("remnant_bar_dims_invalid", detail="El retazo supera el largo declarado de la barra. Revisa la medida y su suministro.")
        else:
            declared = rows("SELECT category,variant_key,attributes FROM inventory_items WHERE org_id=%s AND sku=%s "
                            "AND attributes ? 'sheet_width_mm' AND attributes ? 'sheet_height_mm'",
                            [str(org_id), sheet_workshop_sku])
            if len(declared) != 1:
                raise DocumentaryError("remnant_sheet_authority_missing", detail="Falta el formato y sustrato de la lámina. Decláralos en Catálogo antes de registrar su retazo.")
            declaration = declared[0]
            attributes = declaration['attributes']
            if isinstance(attributes, str):
                attributes = json.loads(attributes)
            identity = declaration['variant_key'] or None
            declared_color = attributes.get('color')
            declared_material = declaration['category']
            if (physical_stock_identity and physical_stock_identity != identity) or (
                color and color != declared_color
            ) or (material and material != declared_material):
                raise DocumentaryError('remnant_authority_mismatch', detail='El sustrato, color o identidad no coincide con la lámina declarada. Revisa su suministro.')
            if width_mm > Decimal(str(attributes['sheet_width_mm'])) or height_mm > Decimal(str(attributes['sheet_height_mm'])):
                raise DocumentaryError('remnant_sheet_dims_invalid', detail='El retazo supera el formato declarado de la lámina. Revisa sus medidas.')
            physical_stock_identity, color, material = identity, declared_color, declared_material
        created = one(
            """
            INSERT INTO public.inventory_remnants(
                org_id, kind, stock_authority_id, sheet_workshop_sku,
                physical_stock_identity, material, color,
                length_mm, width_mm, height_mm,
                origin, origin_order_id, rack_location, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            [
                str(org_id), kind,
                str(stock_authority_id) if stock_authority_id else None,
                sheet_workshop_sku,
                str(physical_stock_identity) if physical_stock_identity else None,
                material, color,
                str(length_mm) if length_mm is not None else None,
                str(width_mm) if width_mm is not None else None,
                str(height_mm) if height_mm is not None else None,
                origin,
                str(origin_order_id) if origin_order_id else None,
                rack_location, notes,
            ],
            "remnant_create_failed",
        )
        row = one(
            f"{_SELECT} WHERE id = %s AND org_id = %s",
            [str(created["id"]), str(org_id)],
            "remnant_not_found",
        )
    return _remnant_row(row)


def _bar_identity(org_id: UUID, authority_id: str) -> dict:
    found = rows(
        "SELECT m.physical_stock_identity::text,m.stock_color,a.material::text,a.commercial_length_mm AS stock_length_mm "
        "FROM profile_purchase_mappings m JOIN profile_articles a ON a.id=m.profile_article_id "
        "WHERE m.id=%s AND m.is_active AND (m.org_id=%s OR m.org_id IS NULL) "
        "UNION ALL SELECT m.physical_stock_identity::text,m.stock_color,a.material::text,a.commercial_length_mm "
        "FROM catalog_color_skus m JOIN profile_articles a ON a.id=m.profile_article_id "
        "WHERE m.id=%s AND m.is_active AND (m.org_id=%s OR m.org_id IS NULL) "
        "UNION ALL SELECT physical_stock_identity::text,stock_color,'STEEL',stock_length_mm FROM reinforcement_articles "
        "WHERE id=%s AND is_active AND (org_id=%s OR org_id IS NULL)",
        [authority_id,str(org_id),authority_id,str(org_id),authority_id,str(org_id)])
    if len(found) != 1 or found[0]["stock_length_mm"] is None:
        raise DocumentaryError("remnant_stock_authority_missing", detail="El suministro no tiene autoridad de stock vigente. Revisa su color y largo en Catálogo.")
    return found[0]


def bar_remnants_for_authorities(
    *, org_id: UUID, authority_ids: set[str],
) -> list[RemnantBar]:
    """AVAILABLE bar drops matching the plan's stock authorities — fed to the
    optimizer so on-hand material is cut before any purchase."""
    if not authority_ids:
        return []
    found = rows(
        f"{_SELECT} WHERE org_id = %s AND kind = 'BAR' AND status = 'AVAILABLE'"
        " AND stock_authority_id = ANY(%s::uuid[])",
        [str(org_id), sorted(authority_ids)],
    )
    return [
        RemnantBar(
            remnant_id=str(r["id"]),
            stock_authority_id=str(r["stock_authority_id"]),
            length_mm=Decimal(str(r["length_mm"])),
        )
        for r in found
    ]


def sheet_remnants_for_sku(*, org_id: UUID, workshop_sku: str) -> list[SheetRemnant]:
    found = rows(
        f"{_SELECT} WHERE org_id = %s AND kind = 'SHEET' AND status = 'AVAILABLE'"
        " AND sheet_workshop_sku = %s",
        [str(org_id), workshop_sku],
    )
    return [
        SheetRemnant(
            remnant_id=str(r["id"]),
            width_mm=Decimal(str(r["width_mm"])),
            height_mm=Decimal(str(r["height_mm"])),
        )
        for r in found
    ]


def reserve_remnants(
    *, org_id: UUID, remnant_ids: list[str], order_id: UUID,
) -> None:
    """Claim plan remnants inside the caller's transaction. Each row must be
    AVAILABLE — a remnant another order claimed refuses, so a physical drop
    can never be double-booked by two parallel plans."""
    if not remnant_ids:
        return
    claimed = rows(
        """
        UPDATE public.inventory_remnants
        SET status = 'RESERVED', reserved_order_id = %s, updated_at = %s
        WHERE org_id = %s AND id = ANY(%s::uuid[]) AND status = 'AVAILABLE'
        RETURNING id
        """,
        [
            str(order_id), datetime.now(timezone.utc),
            str(org_id), sorted(set(remnant_ids)),
        ],
    )
    if len(claimed) != len(set(remnant_ids)):
        raise DocumentaryError("remnant_unavailable")


def release_reservations(*, org_id: UUID, order_id: UUID) -> int:
    """Return everything this order reserved — called before re-optimizing or
    on cancellation so drops go back to the pool."""
    released = rows(
        """
        UPDATE public.inventory_remnants
        SET status = 'AVAILABLE', reserved_order_id = NULL, updated_at = %s
        WHERE org_id = %s AND reserved_order_id = %s AND status = 'RESERVED'
        RETURNING id
        """,
        [datetime.now(timezone.utc), str(org_id), str(order_id)],
    )
    return len(released)


def consume_order_remnants(*, org_id: UUID, order_id: UUID) -> int:
    """RESERVED → CONSUMED when the CUT step completes: the physical drop was
    put on the saw. Anything still reserved but not in the plan releases."""
    consumed = rows(
        """
        UPDATE public.inventory_remnants
        SET status = 'CONSUMED', consumed_order_id = %s,
            reserved_order_id = NULL, updated_at = %s
        WHERE org_id = %s AND reserved_order_id = %s AND status = 'RESERVED'
        RETURNING id
        """,
        [str(order_id), datetime.now(timezone.utc), str(org_id), str(order_id)],
    )
    return len(consumed)


def scrap_remnant(
    *, org_id: UUID, remnant_id: UUID, actor_id: UUID,
    reason: str, confirmed: bool,
) -> dict[str, object]:
    """Mark an offcut as scrap — physically too damaged/short to reuse."""
    with transaction.atomic(), documentary_backend():
        _action_reason(confirmed,reason)
        row = one(
            f"{_SELECT} WHERE id = %s AND org_id = %s FOR UPDATE",
            [str(remnant_id), str(org_id)],
            "remnant_not_found",
        )
        if row["status"] == "CONSUMED":
            raise DocumentaryError("remnant_consumed")
        if row["status"] == "RESERVED":
            raise DocumentaryError("remnant_reserved")
        rows(
            """
            UPDATE public.inventory_remnants
            SET status = 'SCRAPPED', updated_at = %s
            WHERE id = %s AND org_id = %s RETURNING id
            """,
            [datetime.now(timezone.utc), str(remnant_id), str(org_id)],
        )
        refreshed = one(
            f"{_SELECT} WHERE id = %s AND org_id = %s",
            [str(remnant_id), str(org_id)],
            "remnant_not_found",
        )
    return _remnant_row(refreshed)


def _action_reason(confirmed:bool,reason:str) -> None:
    if not confirmed or len(reason.strip())<3:
        raise DocumentaryError("inventory_confirmation_required",detail="Confirma la acción e indica un motivo para el libro de movimientos.")
    rows("SELECT set_config('dekopen.inventory_reason',%s,true)",[reason.strip()])


def move_remnant(*,org_id:UUID,remnant_id:UUID,actor_id:UUID,rack_location:str,reason:str,confirmed:bool) -> dict:
    with transaction.atomic(),documentary_backend():
        _action_reason(confirmed,reason)
        row=one(f"{_SELECT} WHERE id=%s AND org_id=%s FOR UPDATE",[str(remnant_id),str(org_id)],"remnant_not_found")
        if row['status'] in ('CONSUMED','SCRAPPED'):
            raise DocumentaryError('remnant_consumed',detail="Este retazo ya salió del stock; consulta su historia.")
        if not rack_location.strip():
            raise DocumentaryError('rack_required',detail="Indica la ubicación física de destino.")
        rows("UPDATE public.inventory_remnants SET rack_location=%s,updated_at=now() WHERE id=%s AND org_id=%s RETURNING id",
             [rack_location.strip(),str(remnant_id),str(org_id)])
        return _remnant_row(one(f"{_SELECT} WHERE id=%s AND org_id=%s",[str(remnant_id),str(org_id)],"remnant_not_found"))


def reserve_for_work_order(*,org_id:UUID,remnant_id:UUID,actor_id:UUID,order_id:UUID,confirmed:bool) -> dict:
    if not confirmed:
        raise DocumentaryError('inventory_confirmation_required',detail="Confirma la OT y revisa el plan antes de reservar.")
    from production.service import optimize_work_order
    with transaction.atomic(),documentary_backend():
        # Reuse the manufacturing optimizer and its locks; a manually chosen
        # destination never fabricates compatibility or bypasses a started cut.
        optimize_work_order(org_id=org_id,order_id=order_id,actor_id=actor_id,color="",strategy="fast")
        row=one(f"{_SELECT} WHERE id=%s AND org_id=%s",[str(remnant_id),str(org_id)],"remnant_not_found")
        if str(row['reserved_order_id']) != str(order_id) or row['status']!='RESERVED':
            raise DocumentaryError('remnant_not_selected',detail="El motor eligió otro suministro. Revisa las necesidades actuales de la OT.")
        return _remnant_row(row)


def unreserve_remnant(
    *, org_id: UUID, remnant_id: UUID, actor_id: UUID,
) -> dict[str, object]:
    """Return a RESERVED remnant to the pool — the operator decided this plan
    won't cut it after all. The reserving order's plan must stop claiming the
    drop in the same transaction: leaving the claim behind would let another
    order book the physical remnant while the first plan still lists it."""
    with transaction.atomic(), documentary_backend():
        # Lock order must match optimize_work_order's (order → remnant): taking
        # the remnant first and the order second deadlocks against a replan
        # that holds the order while claiming this remnant. The unlocked probe
        # only decides WHICH order to lock first — the authoritative state is
        # re-read under the remnant lock below.
        probe = one(
            f"{_SELECT} WHERE id = %s AND org_id = %s",
            [str(remnant_id), str(org_id)],
            "remnant_not_found",
        )
        expected_owner = (
            probe["reserved_order_id"] if probe["status"] == "RESERVED" else None
        )
        if expected_owner:
            one(
                "SELECT id FROM public.orders WHERE id = %s AND org_id = %s FOR UPDATE",
                [str(expected_owner), str(org_id)],
                "work_order_not_found",
            )
        row = one(
            f"{_SELECT} WHERE id = %s AND org_id = %s FOR UPDATE",
            [str(remnant_id), str(org_id)],
            "remnant_not_found",
        )
        if row["status"] != "RESERVED":
            raise DocumentaryError("remnant_not_reserved")
        order_id = row["reserved_order_id"]
        if str(order_id) != str(expected_owner):
            # Ownership moved between the probe and the remnant lock — the row
            # the plan now belongs to is not the one we locked first. Refuse:
            # the caller retries and locks the right owner on the next pass.
            raise DocumentaryError("remnant_reservation_moved")
        rows(
            """
            UPDATE public.inventory_remnants
            SET status = 'AVAILABLE', reserved_order_id = NULL, updated_at = %s
            WHERE id = %s AND org_id = %s RETURNING id
            """,
            [datetime.now(timezone.utc), str(remnant_id), str(org_id)],
        )
        if order_id:
            _evict_remnant_claim(
                org_id=org_id,
                order_id=UUID(str(order_id)),
                remnant_id=remnant_id,
            )
        refreshed = one(
            f"{_SELECT} WHERE id = %s AND org_id = %s",
            [str(remnant_id), str(org_id)],
            "remnant_not_found",
        )
    return _remnant_row(refreshed)


def _evict_remnant_claim(
    *, org_id: UUID, order_id: UUID, remnant_id: UUID
) -> None:
    """Rewrite the reserving order's plan so it no longer claims the released
    drop: the layout rows keep their cut positions but now need fresh stock
    (`source` → NEW, `remnant_id` cleared) and `remnants.consumed` loses the
    entry. Physical identity and plan stay consistent in one transaction."""
    row = one(
        "SELECT payload_json FROM public.orders WHERE id = %s AND org_id = %s FOR UPDATE",
        [str(order_id), str(org_id)],
        "work_order_not_found",
    )
    payload = row["payload_json"]
    if isinstance(payload, str):
        payload = json.loads(payload)
    optimization = payload.get("optimization")
    if not isinstance(optimization, dict):
        return
    # The plan claimed a physical drop that no longer exists: its layout can
    # no longer prove pieces fit real stock. Invalidate it so a consuming step
    # refuses until a fresh optimize re-reserves — and drop the machine
    # exports rendered from the old plan, whose fingerprints are now stale.
    optimization["invalidated"] = True
    # The UI names the offending drop in the alert banner — the raw id is the
    # only identity left (the remnant row is already scrapped/released).
    optimization["invalidated_by"] = str(remnant_id)
    for export_key in ("cnc_export", "dxf_export", "operations_export"):
        payload.pop(export_key, None)
    remnant_key = str(remnant_id)
    remnants = optimization.get("remnants")
    if isinstance(remnants, dict) and isinstance(remnants.get("consumed"), list):
        remnants["consumed"] = [
            entry
            for entry in remnants["consumed"]
            if str(entry.get("id")) != remnant_key
        ]
    bars = optimization.get("bars")
    if isinstance(bars, dict) and isinstance(bars.get("workshop_cut_plan"), list):
        for bar in bars["workshop_cut_plan"]:
            if isinstance(bar, dict) and str(bar.get("remnant_id")) == remnant_key:
                bar["remnant_id"] = None
                bar["source"] = "NEW"
    sheets = optimization.get("sheets")
    if isinstance(sheets, list):
        for sheet in sheets:
            if isinstance(sheet, dict) and str(sheet.get("remnant_id")) == remnant_key:
                sheet["remnant_id"] = None
                sheet["source"] = "NEW"
    rows(
        """
        UPDATE public.orders SET payload_json = %s::jsonb, updated_at = %s
        WHERE id = %s AND org_id = %s RETURNING id
        """,
        [json.dumps(payload), datetime.now(timezone.utc), str(order_id), str(org_id)],
    )


def record_produced_remnants(
    *,
    org_id: UUID,
    order_id: UUID,
    produced_bars: list[dict[str, object]],
    produced_sheets: list[dict[str, object]],
) -> int:
    """Write back the plan's usable remainders as new AVAILABLE remnants under
    the producing order — ``origin='PRODUCTION'`` keeps them traceable to the
    cut plan that made them."""
    inserted = 0
    for bar in produced_bars:
        created = rows(
            """
            INSERT INTO public.inventory_remnants(
                org_id, kind, stock_authority_id, length_mm,
                origin, origin_order_id, id, rack_location
            ) VALUES (%s, 'BAR', %s::uuid, %s, 'PRODUCTION', %s,
                      coalesce(%s::uuid, gen_random_uuid()), %s)
            ON CONFLICT (id) DO NOTHING
            RETURNING id
            """,
            [
                str(org_id), str(bar["stock_authority_id"]),
                str(bar["remainder_mm"]), str(order_id), bar.get("id"), bar.get("rack_location"),
            ],
        )
        inserted += len(created)
    for sheet in produced_sheets:
        created = rows(
            """
            INSERT INTO public.inventory_remnants(
                org_id, kind, sheet_workshop_sku, width_mm, height_mm,
                origin, origin_order_id, id, rack_location
            ) VALUES (%s, 'SHEET', %s, %s, %s, 'PRODUCTION', %s,
                      coalesce(%s::uuid, gen_random_uuid()), %s)
            ON CONFLICT (id) DO NOTHING
            RETURNING id
            """,
            [
                str(org_id), sheet["workshop_sku"],
                str(sheet["width_mm"]), str(sheet["height_mm"]),
                str(order_id), sheet.get("id"), sheet.get("rack_location"),
            ],
        )
        inserted += len(created)
    return inserted


def plan_remnant_addresses(*, org_id: UUID, order_id: UUID, plan: dict,
                           rack_location: str) -> None:
    """Reserve addresses at the human optimize click, without creating stock.

    Equal plans reuse their addresses. Changed plans retain historical codes;
    only CUT completion creates a physical AVAILABLE row with this identity.
    """
    from uuid import uuid5
    from dekopen_engine.documentary_canonical import documentary_sha256_v1

    bars = {bar["bar_index"]: bar for bar in plan["bars"].get("workshop_cut_plan") or []}
    sheets = {sheet["sheet_index"]: sheet for sheet in plan.get("sheets") or []}
    for kind, entries, homes, field in (
        ("BAR", plan.get("produced_bars") or [], bars, "bar_index"),
        ("SHEET", plan.get("produced_sheets") or [], sheets, "sheet_index"),
    ):
        for index, entry in enumerate(entries):
            identity = str(uuid5(UUID(str(order_id)), "cut-remnant:" + documentary_sha256_v1({
                "kind": kind, "index": index, "source": homes[entry[field]],
                "remnant": {key: value for key, value in entry.items() if key not in {"id", "code", "rack_location"}},
            })))
            code = one("SELECT private.assign_entity_code(%s::uuid,'RT',%s::uuid) AS code",
                       [str(org_id), identity], "remnant_code_failed")["code"]
            entry.update(id=identity, code=code, rack_location=rack_location)


def remnant_label(*, org_id: UUID, remnant_id: UUID) -> dict[str, object]:
    """Printable rack tag for one remnant — §5 barcode readiness.

    The QR payload encodes the remnant's stable identity the same way the
    cut-pack and unit labels do; a floor scanner resolves it to this row.
    Rendering (sheet vs bar dimensions) happens on the client — this returns
    the raw fields plus the pre-rendered QR SVG."""
    import segno

    row = one(
        f"{_SELECT} WHERE id = %s AND org_id = %s",
        [str(remnant_id), str(org_id)],
        "remnant_not_found",
    )
    remnant = _remnant_row(row)
    identity = remnant["sheet_workshop_sku"]
    if not identity and remnant["stock_authority_id"]:
        for table in ("profile_purchase_mappings", "reinforcement_articles", "catalog_color_skus"):
            found = rows(
                f"SELECT commercial_sku FROM public.{table} WHERE id = %s",
                [remnant["stock_authority_id"]],
            )
            if found:
                identity = str(found[0]["commercial_sku"])
                break
    if not identity:
        # An anonymous drop still gets a printable identity — material · color
        # before the raw identity UUID.
        identity = (
            " · ".join(
                part for part in (remnant.get("material"), remnant.get("color"))
                if part
            )
            or remnant["physical_stock_identity"]
            or "—"
        )
    query = urlencode({"remnant": remnant["id"], "code": remnant["code"]})
    payload = f"{settings.DEKOPEN_PUBLIC_APP_URL.rstrip('/')}/inventory?{query}"
    return {
        "remnant": remnant,
        "identity": identity,
        "qr_payload": payload,
        "qr_svg": segno.make(payload, error="m").svg_inline(border=4, scale=6, omitsize=True),
    }
