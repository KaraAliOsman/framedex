"""Read-only outcome facts from already computed, current engine authorities."""

from decimal import Decimal


def engine_accepted(envelope: dict) -> bool:
    result = envelope.get("result") or {}
    return (envelope.get("http_status") == 200
            and result.get("status") in {"VALID", "MANUFACTURING_INCOMPLETE"}
            and not any(i.get("severity") == "error" for i in result.get("issues") or []))


def priced_winner(project: dict, operations: list[dict]) -> str | None:
    """Never rank draft zeroes or a preview/reset/superseded operation."""
    authority = project.get("current_pricing_operation_id")
    if not project.get("pricing_current") or not authority:
        return None
    positions = {p["position_index"]: p for p in project.get("positions") or []}
    operation = next((o for o in operations if o.get("id") == authority), None)
    if operation is not None:
        if (operation.get("state") != "APPLIED" or operation.get("project_id") != project.get("id")
                or operation.get("revision_code") != project.get("current_revision")):
            return None
        lines = operation.get("lines") or []
    else:
        # The estimator's operation list only exposes their own previews.
        # Project GET still exposes applied position prices, gated by its
        # current APPLIED authority (including the reset/revision check).
        if any(p.get("price_net") is None for p in positions.values()):
            return None
        lines = [{"position_index": index, "line_net": p["price_net"]} for index, p in positions.items()]
    if not lines or len(lines) != len(positions) or {line["position_index"] for line in lines} != set(positions):
        return None
    winner = max(lines, key=lambda line: (Decimal(str(line["line_net"])), -line["position_index"]))
    return positions[winner["position_index"]]["id"]


def frame_bar_count(payload: dict) -> int | None:
    """Count physical bars with frame profile cuts, excluding steel/other roles."""
    bars = (payload.get("optimization") or {}).get("bars")
    if not isinstance(bars, dict) or bars.get("unplaced"):
        return None
    plan = bars.get("workshop_cut_plan")
    if not isinstance(plan, list):
        return None
    if any(c.get("source_kind") == "PROFILE" and not c.get("role")
           for bar in plan for c in bar.get("cuts") or []):
        return None
    return sum(any(c.get("source_kind") == "PROFILE" and c.get("role") == "FRAME"
                   for c in bar.get("cuts") or []) for bar in plan)
