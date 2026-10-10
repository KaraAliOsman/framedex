"""Strict authorization for newly generated CNC interchange.

Historical neutral documents retain their validation contract in operations.py.
This gate never converts absence into capability, nor plan Y into tool Y.
"""

from __future__ import annotations

from decimal import Decimal
import hashlib
import json

from .operations import (
    MachineProfile, ManufacturingOperation, MemberFace, OperationValidation,
    validate_operations,
)


def authorize_member_operations(
    ops: list[ManufacturingOperation], machine: MachineProfile, *,
    authority: dict[str, object], member_length_mm: Decimal | None,
    section: dict[str, object] | None, member_label: str,
    profile_sku: str | None = None,
) -> list[OperationValidation]:
    """All missing physical prerequisites block, including a declared empty set.

The neutral adapter is a reviewed interchange, never executable vendor code.
End machining addresses an entire end plane. Face work needs a transverse
tool coordinate, which current point/longitudinal declarations do not supply.
"""
    lengths = {op.host: member_length_mm for op in ops} if member_length_mm is not None else {}
    results = validate_operations(ops, machine, member_lengths_mm=lengths)
    output = [item.model_copy(update={"level": "BLOCK"})
              if item.level == "WARN" else item for item in results if item.level != "PASS"]
    by_tool = {tool.tool_id: tool for tool in machine.tools}
    for op in ops:
        def block(code: str, **detail: str) -> None:
            output.append(OperationValidation(operation_id=op.operation_id, level="BLOCK",
                code=code, detail={"host": member_label, "kind": op.kind.value,
                                   "machine": machine.machine_id, **detail}))

        for field in ("supported_kinds", "supported_faces", "coordinate_systems", "axes"):
            if not authority.get(field):
                block("machine_authority_missing", field=field)
        if authority.get("machine_type") not in ("END_MILLER", "MACHINING_CENTER", "SAW", "DECLARED"):
            block("machine_authority_missing", field="machine_type")
        if not str(authority.get("authority_source") or "").strip():
            block("machine_authority_missing", field="authority_source")
        if authority.get("clamps_declared") is not True:
            block("machine_authority_missing", field="clamps_declared")
        if machine.max_member_length_mm is None:
            block("machine_authority_missing", field="max_member_length_mm")
        if machine.safe_margin_mm is None:
            block("machine_authority_missing", field="safe_margin_mm")
        axes = authority.get("axes")
        if not isinstance(axes, list) or "X" not in axes:
            block("machine_axis_missing", axis="X")
        if machine.units != "mm" or machine.encoding != "utf-8":
            block("machine_format_unsupported")
        if machine.postprocessor_id != "neutral-ops-v1" or machine.postprocessor_version != "1":
            block("postprocessor_undeclared")
        if machine.controller_family != "NEUTRAL":
            block("postprocessor_controller_unsupported", controller_family=machine.controller_family or "")
        if member_length_mm is None or member_length_mm <= 0:
            block("member_length_undeclared")
        if op.u_mm is None:
            block("member_coordinate_undeclared")
        elif member_length_mm is not None and not Decimal(0) <= op.u_mm <= member_length_mm:
            block("member_coordinate_outside", u_mm=str(op.u_mm))
        if op.reference not in ("member_start", "member_end"):
            block("member_datum_undeclared")
        if ((op.face == MemberFace.START_EDGE and (op.u_mm != 0 or op.reference != "member_start"))
            or (op.face == MemberFace.END_EDGE and (op.u_mm != member_length_mm or op.reference != "member_end"))):
            block("end_datum_inconsistent")
        if op.face is None:
            block("face_undeclared")
        if not section or not section.get("polygon"):
            block("section_undeclared")
        else:
            if not section.get("orientation_declared") or not section.get("origin_declared"):
                block("section_orientation_undeclared")
            # Drawing orientation is for rendering only. Loading authority is a
            # separate reviewed setup, bound to the exact sealed section.
            setups = authority.get("profile_setups")
            setup = next((s for s in setups if isinstance(s, dict) and s.get("profile_sku") == profile_sku), None) if isinstance(setups, list) else None
            if not setup or setup.get("section_fingerprint") != section_fingerprint(section):
                block("profile_setup_undeclared", profile_sku=profile_sku or "Sin dato")
            elif (setup.get("loading_orientation") not in ("EXTERIOR_UP", "EXTERIOR_DOWN", "EXTERIOR_LEFT", "EXTERIOR_RIGHT")
                  or setup.get("axial_datum") != "MEMBER_START" or not str(setup.get("source") or "").strip()):
                block("profile_loading_undeclared", profile_sku=profile_sku or "Sin dato")
        if op.face not in (MemberFace.START_EDGE, MemberFace.END_EDGE):
            # x/y are assembly plan coordinates. u is a longitudinal coordinate;
            # none of these specifies a tool's transverse point on the section.
            block("transverse_coordinate_undeclared")
        tool = by_tool.get(op.tool_id or "")
        if tool is None:
            block("no_compatible_tool", tool_id=op.tool_id or "Sin dato")
        else:
            sources = authority.get("tool_sources")
            if not isinstance(sources, dict) or not sources.get(tool.tool_id):
                block("tool_source_undeclared", tool_id=tool.tool_id)
            if tool.compatible_kinds is None:
                block("tool_capability_undeclared", tool_id=tool.tool_id)
            if tool.diameter_mm is None or tool.working_length_mm is None or tool.max_depth_mm is None:
                block("tool_geometry_undeclared", tool_id=tool.tool_id)
            if op.depth_mm is not None and tool.working_length_mm is not None and op.depth_mm > tool.working_length_mm:
                block("tool_working_length_exceeded", tool_id=tool.tool_id)
        if op.depth_mm is None:
            block("depth_undeclared")
        elif op.depth_mm <= 0 or (member_length_mm is not None and op.depth_mm > member_length_mm):
            block("depth_invalid")
        for zone in machine.clamp_zones:
            start = end = op.u_mm
            if op.u_mm is not None and op.depth_mm is not None:
                if op.face == MemberFace.START_EDGE:
                    end = op.u_mm + op.depth_mm
                elif op.face == MemberFace.END_EDGE:
                    start = op.u_mm - op.depth_mm
            if start is not None and end is not None and start <= zone.end_mm and end >= zone.start_mm:
                if not any(item.operation_id == op.operation_id and item.code == "clamp_conflict" for item in output):
                    block("clamp_conflict", clamp_label=zone.label,
                          clamp_zone=f"{zone.start_mm}–{zone.end_mm}")
        if not any(item.operation_id == op.operation_id for item in output):
            output.append(OperationValidation(operation_id=op.operation_id, level="PASS", code="ok",
                detail={"host": member_label}))
    return output


def section_fingerprint(section: dict[str, object]) -> str:
    """Bind a reviewed loading setup to immutable declared geometry."""
    return hashlib.sha256(json.dumps(section, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def member_preview(*, ops: list[ManufacturingOperation], length_mm: Decimal | None,
                   section: dict[str, object] | None) -> dict[str, object]:
    """Longitudinal positions use u from START, even when work targets END.

This fixes the old length-u projection. No missing coordinate is inferred
from a face, reference, plan coordinate or viewport size.
"""
    marks = [{"operation_id": op.operation_id,
              "x_mm": str(op.u_mm) if op.u_mm is not None else None,
              "face": op.face.value if op.face else None,
              "section_coverage": "END_PLANE" if op.face in (MemberFace.START_EDGE, MemberFace.END_EDGE) else None}
             for op in ops]
    return {"datum": "member_start", "length_mm": str(length_mm) if length_mm is not None else None,
            "section": section, "section_fingerprint": section_fingerprint(section) if section else None, "marks": marks}


def program_diff(previous: dict[str, object] | None, proposed: dict[str, object]) -> dict[str, object]:
    """Compare sealed physical content. Absence of history is explicit."""
    before = previous or {}
    def operations(document: dict[str, object]) -> dict[str, dict[str, object]]:
        value = document.get("operations")
        return {str(op["operation_id"]): op for op in value if isinstance(op, dict)} if isinstance(value, list) else {}
    old = operations(before)
    new = operations(proposed)
    return {"has_previous": previous is not None,
            "added": [new[key] for key in sorted(new.keys()-old.keys())],
            "removed": [old[key] for key in sorted(old.keys()-new.keys())],
            "changed": [{"before": old[key], "after": new[key]} for key in sorted(old.keys()&new.keys()) if old[key] != new[key]],
            "authority_changes": [{"field": field, "before": before.get(field), "after": proposed.get(field)}
                                  for field in ("machine", "preview", "identity", "declared_intent_gaps")
                                  if before.get(field) != proposed.get(field)]}
