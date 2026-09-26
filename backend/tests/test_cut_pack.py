"""§10 cut pack — printable workshop pack bound to the live optimization."""

import json

import pytest

from documents.repository import DocumentaryError
from production.cut_pack import render_cut_pack


def _order(payload):
    return {
        "id": "order-1",
        "order_code": "OT-7",
        "status": "RELEASED",
        "project_version_id": "ver-1",
        "payload_json": json.dumps(payload),
    }


def _version():
    return {
        "snapshot_json": json.dumps({
            "manufacturing": [
                {
                    "members": [{"member_id": "mem-1", "bay_id": "bay-1"}],
                    "reinforcements": [],
                    "infills": [{"infill_id": "inf-1", "bay_id": "bay-1"}],
                    "handles": [],
                    "leaves": [{"leaf_id": "leaf-1", "bay_id": "bay-1"}],
                }
            ],
            "positions": [{"id": "pos-1", "position_index": 1}],
        })
    }


_OPTIMIZATION = {
    "color": "BLANCO",
    "units": 1,
    "strategy": "AUTO",
    "bars": {
        "metrics": {
            "bars": 1,
            "cuts": 2,
            "process_waste_mm": "120",
            "reusable_remnant_mm": "800",
        },
        "workshop_cut_plan": [
            {
                "bar_index": 1,
                "commercial_sku": "DEKO-MARCO-60",
                "material": "PVC",
                "stock_length_mm": "6000",
                "head_trim_mm": "20",
                "tail_trim_mm": "20",
                "kerf_mm": "5",
                "remainder_mm": "800",
                "remainder_reusable": True,
                "yield_pct": "86.67",
                "source": "NEW",
                "cuts": [
                    {
                        "sequence": 1,
                        "piece_id": "mem-1",
                        "workshop_sku": "DEMO_60",
                        "length_mm": "2500",
                        "angle_left": "45",
                        "angle_right": "45",
                        "source_position_id": "pos-1",
                        "bay_id": "bay-1",
                        "leaf_id": "leaf-1",
                    },
                    {
                        "sequence": 2,
                        "piece_id": "hashpiece",
                        "workshop_sku": "DEMO_60",
                        "length_mm": "2655",
                        "angle_left": "45",
                        "angle_right": "45",
                        "source_position_id": "pos-1",
                        "bay_id": "bay-1",
                        "leaf_id": None,
                    },
                ],
            }
        ],
    },
    "sheets": [
        {
            "sheet_index": 1,
            "purchasing_sku": "DVH-4/12/4",
            "sheet_width_mm": "2600",
            "sheet_height_mm": "1600",
            "yield_pct": "71.5",
            "placements": [
                {
                    "piece_id": "inf-1",
                    "x_mm": "0",
                    "y_mm": "0",
                    "width_mm": "1400",
                    "height_mm": "1300",
                    "rotated": False,
                    "bay_id": "bay-1",
                    "leaf_id": None,
                }
            ],
            "produced_remnants": [
                {"x_mm": "1400", "y_mm": "0", "width_mm": "1200", "height_mm": "1600"}
            ],
        }
    ],
    "unnested": [],
}


def _install_db(monkeypatch, order_payload):
    import contextlib

    def fake_one(sql_text, params, code="not_found"):
        lowered = " ".join(sql_text.lower().split())
        if "public.orders" in lowered:
            return _order(order_payload)
        if "project_versions" in lowered:
            return _version()
        raise AssertionError(lowered)

    monkeypatch.setattr("production.cut_pack.one", fake_one)
    monkeypatch.setattr(
        "production.cut_pack.documentary_backend", contextlib.nullcontext
    )
    monkeypatch.setattr(
        "production.cut_pack.transaction.atomic", contextlib.nullcontext
    )


def test_cut_pack_renders_pdf(monkeypatch) -> None:
    _install_db(monkeypatch, {"optimization": _OPTIMIZATION})
    content, name = render_cut_pack(org_id="org", order_id="order-1")
    assert content.startswith(b"%PDF-")
    assert name == "OT-7-pack-corte.pdf"


def test_cut_pack_requires_optimization(monkeypatch) -> None:
    _install_db(monkeypatch, {})
    with pytest.raises(DocumentaryError, match="cut_pack_requires_optimization"):
        render_cut_pack(org_id="org", order_id="order-1")


def test_cut_pack_refuses_invalidated_plan(monkeypatch) -> None:
    payload = {"optimization": {**_OPTIMIZATION, "invalidated": True}}
    _install_db(monkeypatch, payload)
    with pytest.raises(DocumentaryError, match="plan_invalidated"):
        render_cut_pack(org_id="org", order_id="order-1")
