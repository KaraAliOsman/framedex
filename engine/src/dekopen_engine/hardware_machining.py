"""Machine-neutral projection of sealed hardware declarations, with exact gaps."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from dekopen_engine.manufacturing import ManufacturingFactsV1
from dekopen_engine.models import HardwareItem, ProfileRole
from dekopen_engine.operations import (
    CoordinateSystem, ManufacturingOperation, MemberFace, OperationKind, _op_id, _num,
)


def hardware_operations(*, items: Sequence[HardwareItem], fact_units: Sequence[ManufacturingFactsV1],
                        issues: list[dict[str, object]]) -> list[ManufacturingOperation]:
    operations = []
    for kit in items:
        if kit.resolution is None:
            continue
        for component in kit.contents:
            for declaration in component.machining:
                missing = []
                if not declaration.positions_mm:
                    missing.append("coordenadas")
                if declaration.host_scope is None:
                    missing.append("ámbito de la pieza anfitriona")
                if declaration.face is None:
                    missing.append("cara")
                if declaration.tool_id is None:
                    missing.append("herramienta")
                if declaration.depth_mm is None:
                    missing.append("profundidad")
                if declaration.covered_quantity != component.qty:
                    missing.append("cobertura de la cantidad resuelta")
                targets = []
                for unit in fact_units:
                    leaf = next((leaf for leaf in unit.leaves if leaf.bay_id == kit.bay_id and leaf.leaf_id == kit.leaf_id), None)
                    if leaf is None:
                        continue
                    side: str = declaration.host_side
                    if side in ("HINGE", "CLOSING"):
                        hinge = leaf.opening.hinge_side.value if leaf.opening is not None else leaf.door_handedness
                        if hinge is None:
                            missing.append("lado de bisagras")
                            continue
                        side = hinge if side == "HINGE" else {"LEFT": "RIGHT", "RIGHT": "LEFT", "TOP": "BOTTOM", "BOTTOM": "TOP"}.get(hinge, "")
                    hosts = [member for member in unit.members if member.identity.physical_member_slot == side and (
                        member.identity.assembly == "OUTER_FRAME" and member.identity.role is ProfileRole.FRAME
                        if declaration.host_scope == "OUTER_FRAME" else
                        member.bay_id == kit.bay_id and member.leaf_id == kit.leaf_id
                        and member.identity.assembly == leaf.assembly
                        and member.identity.role in (ProfileRole.SASH, ProfileRole.SLIDING_SASH, ProfileRole.DOOR_SASH))]
                    if len(hosts) != 1:
                        missing.append("pieza anfitriona inequívoca")
                        continue
                    host = hosts[0]
                    dx, dy = host.end.x_mm-host.start.x_mm, host.end.y_mm-host.start.y_mm
                    span = abs(dx)+abs(dy)
                    if host.sagitta_mm is not None or (dx != 0 and dy != 0) or span <= 0:
                        missing.append("referencia recta de la pieza")
                    if any(u > span for u in declaration.positions_mm):
                        missing.append("coordenadas dentro de la pieza")
                    targets.append((host, dx, dy))
                if not targets:
                    missing.append("hoja física sellada")
                if missing:
                    issues.append({"code": "declared_intent_not_emitted", "kind": declaration.kind,
                        "component_sku": component.sku, "component_name": component.name,
                        "declaration": declaration.name, "bay_id": kit.bay_id, "leaf_id": kit.leaf_id,
                        "source": declaration.source,
                        "detail": "Declarada no emitida: faltan " + ", ".join(sorted(set(missing))) + "."})
                    continue
                assert declaration.face is not None
                for host, dx, dy in targets:
                    for u in declaration.positions_mm:
                        x = host.start.x_mm + (u if dx > 0 else -u if dx < 0 else Decimal(0))
                        y = host.start.y_mm + (u if dy > 0 else -u if dy < 0 else Decimal(0))
                        basis = f"hardware:{kit.kit_sku}:{component.sku}:{declaration.code}:{declaration.source}"
                        operations.append(ManufacturingOperation(
                            operation_id=_op_id(host.member_id, declaration.kind, basis, _num(u),
                                declaration.face, declaration.tool_id, _num(declaration.depth_mm)),
                            kind=OperationKind(declaration.kind), host_kind="MEMBER", host=host.member_id,
                            coordinate_system=CoordinateSystem.MEMBER_PLAN, x_mm=x, y_mm=y, u_mm=u,
                            reference="member_start", face=MemberFace(declaration.face),
                            depth_mm=declaration.depth_mm, tool_id=declaration.tool_id,
                            basis=basis, detail={"component": component.name, "source": declaration.source}))
    return operations
