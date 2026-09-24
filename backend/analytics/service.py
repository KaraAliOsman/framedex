"""Operational analytics: read-only aggregates over the live platform tables.

Every query is org-scoped; the numbers describe what the connected workflow
is actually doing — the same orders, stock, and documents the rest of the
product writes. Nothing here invents data."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from django.db import transaction

from documents.repository import documentary_backend, one, rows


def _counts_by(sql: str, org_id: UUID) -> dict[str, int]:
    return {
        str(row["status"]): int(row["n"])
        for row in rows(sql, [str(org_id)])
    }


def operational_summary(*, org_id: UUID) -> dict[str, Any]:
    """One org's live operating picture: funnel, throughput, stock, output."""
    with transaction.atomic(), documentary_backend():
        return _summary(org_id)


def _summary(org_id: UUID) -> dict[str, Any]:
    work_orders = _counts_by(
        """
        SELECT status::text AS status, count(*) AS n FROM public.orders
        WHERE org_id = %s AND order_type = 'WORKSHOP_OT' GROUP BY status
        """,
        org_id,
    )
    supplier_orders = _counts_by(
        """
        SELECT status::text AS status, count(*) AS n FROM public.orders
        WHERE org_id = %s AND order_type <> 'WORKSHOP_OT' GROUP BY status
        """,
        org_id,
    )
    throughput = one(
        """
        SELECT
            count(*) FILTER (WHERE event = 'WO_DISPATCHED') AS dispatched_30d,
            count(*) FILTER (WHERE event = 'WO_INSTALLED') AS installed_30d,
            count(*) FILTER (WHERE event = 'WO_COMPLETED') AS completed_30d
        FROM public.production_step_events
        WHERE org_id = %s AND created_at >= now() - interval '30 days'
        """,
        [str(org_id)],
    )
    # §8 explicit domain workflows, surfaced as counts: approved-but-unreleased
    # versions, work orders flagging material shortage, sealed packing awaiting
    # a dispatch note, and catalogs missing fabrication authority.
    prep = one(
        """
        SELECT
            (SELECT count(*) FROM public.project_versions v
             WHERE v.org_id = %s AND v.production_allowed
               AND NOT EXISTS (
                   SELECT 1 FROM public.orders o
                   WHERE o.org_id = v.org_id AND o.project_version_id = v.id
                     AND o.order_type = 'WORKSHOP_OT')) AS versions_ready,
            (SELECT count(*) FROM public.orders o
             WHERE o.org_id = %s AND o.order_type = 'WORKSHOP_OT'
               AND o.status NOT IN ('CANCELLED', 'INSTALLED')
               AND (COALESCE((o.payload_json->'prep'->>'shortages')::int, 0) > 0
                    OR EXISTS (
                        SELECT 1 FROM jsonb_array_elements(
                            COALESCE(o.payload_json->'optimization'->'stock_reservations',
                                     '[]'::jsonb)) r
                        WHERE COALESCE((r->>'short')::numeric, 0) > 0)))
                AS work_orders_shortage,
            (SELECT count(*) FROM public.orders o
             WHERE o.org_id = %s AND o.order_type = 'WORKSHOP_OT'
               AND o.status = 'COMPLETED' AND o.payload_json ? 'packing'
               AND NOT EXISTS (
                   SELECT 1 FROM public.dispatch_notes dn
                   WHERE dn.org_id = o.org_id AND dn.work_order_id = o.id))
                AS dispatch_ready,
            (SELECT count(*) FROM public.profile_systems s
             WHERE s.org_id = %s
               AND (s.rebate_depth_mm IS NULL
                    OR s.end_milling_overlap_mm IS NULL)) AS catalog_gaps
        """,
        [str(org_id)] * 4,
    )
    lead = one(
        """
        SELECT
            avg(extract(epoch FROM (d.created_at - o.created_at)) / 3600.0)
                AS release_to_dispatch_hours
        FROM public.production_step_events d
        JOIN public.orders o ON o.id = d.order_id AND o.org_id = d.org_id
        WHERE d.org_id = %s AND d.event = 'WO_DISPATCHED'
        """,
        [str(org_id)],
    )
    inventory = {
        "items": int(
            one(
                "SELECT count(*) AS n FROM public.inventory_items WHERE org_id = %s",
                [str(org_id)],
            )["n"]
        ),
        "offcuts": int(
            one(
                "SELECT count(*) AS n FROM public.offcut_inventory WHERE org_id = %s",
                [str(org_id)],
            )["n"]
        ),
    }
    deliveries = one(
        """
        SELECT
            count(*) FILTER (WHERE scheduled_date = local_today
                AND status IN ('SCHEDULED','ON_ROUTE','FAILED')) AS today,
            count(*) FILTER (WHERE scheduled_date < local_today
                AND status IN ('SCHEDULED','ON_ROUTE','FAILED')) AS overdue
        FROM public.deliveries,
            LATERAL (
                SELECT (CURRENT_TIMESTAMP AT TIME ZONE org.timezone)::date AS local_today
                FROM public.tenancy_organizations AS org
                WHERE org.id = %s
            ) AS zone
        WHERE org_id = %s
        """,
        [str(org_id), str(org_id)],
    )
    documents = {
        str(row["document_type"]): int(row["n"])
        for row in rows(
            """
            SELECT document_type, count(*) AS n FROM public.document_artifacts
            WHERE org_id = %s GROUP BY document_type ORDER BY document_type
            """,
            [str(org_id)],
        )
    }
    projects = one(
        """
        SELECT
            (SELECT count(*) FROM public.projects WHERE org_id = %s) AS projects,
            (SELECT count(*) FROM public.project_positions WHERE org_id = %s)
                AS positions,
            (SELECT count(*) FROM public.project_versions
             WHERE org_id = %s) AS sealed_versions
        """,
        [str(org_id), str(org_id), str(org_id)],
    )
    recent = [
        {
            "event": str(row["event"]),
            "order_code": str(row["order_code"]),
            "at": row["created_at"].isoformat(),
        }
        for row in rows(
            """
            SELECT e.event, o.order_code, e.created_at
            FROM public.production_step_events e
            JOIN public.orders o ON o.id = e.order_id AND o.org_id = e.org_id
            WHERE e.org_id = %s
            ORDER BY e.created_at DESC LIMIT 10
            """,
            [str(org_id)],
        )
    ]
    lag_hours = lead.get("release_to_dispatch_hours")
    return {
        "schema": "operational_summary_v1",
        "work_orders": work_orders,
        "supplier_orders": supplier_orders,
        "throughput_30d": {k: int(v or 0) for k, v in throughput.items()},
        "avg_release_to_dispatch_hours": (
            round(float(lag_hours), 1) if lag_hours is not None else None
        ),
        "inventory": inventory,
        "prep": {k: int(v or 0) for k, v in prep.items()},
        "deliveries": {k: int(v or 0) for k, v in deliveries.items()},
        "documents": documents,
        "projects": {k: int(v or 0) for k, v in projects.items()},
        "recent_events": recent,
    }
