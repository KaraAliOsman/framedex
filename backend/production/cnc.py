"""CNC workspace: org-declared machines and tools, per-member program
generation, machine-neutral validation, and program staleness.

Authority model: machines and tools are org-declared manufacturing
authority (write through ``documentary_backend`` after API role checks).
Programs are generated artifacts — immutable rows that flip
CURRENT → SUPERSEDED when a replan changes their input fingerprint, so an
operator never runs stale output without the flag being visible.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from uuid import UUID

from django.db import transaction

from dekopen_engine.cnc_authorization import authorize_member_operations, member_preview, program_diff
from dekopen_engine.cutting import CutBar
from dekopen_engine.operations import (
    ClampZone,
    CoordinateSystem,
    MachineProfile,
    MemberFace,
    NeutralOpsPostProcessor,
    OperationKind,
    Tool,
    ToolKind,
    member_meta_map,
    member_program,
    operations_from_plan,
)
from documents.repository import (
    DocumentaryError,
    documentary_backend,
    one,
    rows,
    write,
)
from documents.renderers import (
    _cut_key,
    _cut_member_map,
    _piece_labels,
)
from production.service import (
    _decoded,
    _operations_fact_units,
    _ops_source_fingerprint,
    _raw_fact_units,
    _sealed_hardware_operations,
)


_TOOL_KINDS = {kind.value for kind in ToolKind}
_OP_KINDS = {kind.value for kind in OperationKind}
_FACES = {face.value for face in MemberFace}
_COORDS = {coord.value for coord in CoordinateSystem}


def _dec(value: object) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        number = Decimal(str(value))
        if not number.is_finite():
            raise ValueError("nonfinite")
        return number
    except (InvalidOperation, ValueError):
        raise DocumentaryError("cnc_numeric_invalid")


def _string_list(value: object, *, allowed: set[str], code: str) -> list[str] | None:
    """Preserve absence and explicit empty declarations without granting capability."""
    if value is None:
        return None
    if not isinstance(value, list) or any(
        not isinstance(item, str) or item not in allowed for item in value
    ):
        raise DocumentaryError(code)
    return value


def _public_tool(row: dict[str, object]) -> dict[str, object]:
    public = {
        "id": str(row["id"]),
        "code": row["code"],
        "name": row["name"],
        "kind": row["kind"],
        "diameter_mm": str(row["diameter_mm"]) if row["diameter_mm"] is not None else None,
        "working_length_mm": str(row["working_length_mm"]) if row["working_length_mm"] is not None else None,
        "max_depth_mm": str(row["max_depth_mm"]) if row["max_depth_mm"] is not None else None,
        "compatible_kinds": row.get("compatible_kinds"),
        "active": row["active"],
        "authority_source": row.get("authority_source", ""),
    }
    return {**public, "authority_revision": _authority_revision(public)}


def _authority_revision(public: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(public, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _check_authority_review(data: dict[str, object], public: dict[str, object]) -> None:
    if data.get("expected_revision") is not None and data["expected_revision"] != public["authority_revision"]:
        raise DocumentaryError("cnc_authority_stale")


def _jsonb_value(value: object) -> object:
    # rows() returns jsonb columns as raw text; decode before domain use.
    return json.loads(value) if isinstance(value, str) else value


def _jsonb_list(value: object) -> list[object]:
    decoded = _jsonb_value(value)
    return decoded if isinstance(decoded, list) else []


def _public_machine(row: dict[str, object]) -> dict[str, object]:
    public = {
        "id": str(row["id"]),
        "code": row["code"],
        "name": row["name"],
        "machine_type": row.get("machine_type", ""),
        "profile_setups": _jsonb_list(row.get("profile_setups")),
        "axes": row.get("axes"),
        "clamps_declared": row.get("clamps_declared", False),
        "manufacturer": row["manufacturer"],
        "model": row["model"],
        "controller_family": row["controller_family"],
        "coordinate_systems": row["coordinate_systems"],
        "supported_kinds": row["supported_kinds"],
        "supported_faces": row["supported_faces"],
        "max_member_length_mm": str(row["max_member_length_mm"]) if row["max_member_length_mm"] is not None else None,
        "safe_margin_mm": str(row["safe_margin_mm"]) if row["safe_margin_mm"] is not None else None,
        "clamp_zones": _jsonb_value(row["clamp_zones"]),
        "tool_ids": [str(tool_id) for tool_id in row["tool_ids"]],
        "postprocessor_id": row["postprocessor_id"],
        "postprocessor_version": row["postprocessor_version"],
        "units": row["units"],
        "encoding": row["encoding"],
        "active": row["active"],
        "authority_source": row.get("authority_source", ""),
    }
    return {**public, "authority_revision": _authority_revision(public)}


def list_tools(*, org_id: UUID) -> list[dict[str, object]]:
    return [
        _public_tool(row)
        for row in rows(
            """
            SELECT id, code, name, kind, diameter_mm, working_length_mm,
                   max_depth_mm, compatible_kinds, active, authority_source
            FROM public.cnc_tools WHERE org_id = %s ORDER BY code
            """,
            [str(org_id)],
        )
    ]


def create_tool(*, org_id: UUID, actor_id: UUID, data: dict[str, object]) -> dict[str, object]:
    code = str(data.get("code") or "").strip()
    name = str(data.get("name") or "").strip()
    kind = str(data.get("kind") or "")
    if not code or not name or kind not in _TOOL_KINDS:
        raise DocumentaryError("cnc_tool_invalid")
    compatible = _string_list(
        data.get("compatible_kinds"), allowed=_OP_KINDS, code="cnc_tool_kind_invalid"
    )
    with documentary_backend():
        created = one(
            """
            INSERT INTO public.cnc_tools
                (org_id, code, name, kind, diameter_mm, working_length_mm,
                 max_depth_mm, compatible_kinds, authority_source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, code, name, kind, diameter_mm, working_length_mm,
                      max_depth_mm, compatible_kinds, active, authority_source
            """,
            [
                str(org_id),
                code,
                name,
                kind,
                _dec(data.get("diameter_mm")),
                _dec(data.get("working_length_mm")),
                _dec(data.get("max_depth_mm")),
                compatible,
                str(data.get("authority_source") or "").strip(),
            ],
            "cnc_tool_invalid",
        )
    return _public_tool(created)


@transaction.atomic
def update_tool(
    *, org_id: UUID, tool_id: UUID, data: dict[str, object]
) -> dict[str, object]:
    with documentary_backend():
        current = one(
            """
            SELECT id, code, name, kind, diameter_mm, working_length_mm,
                   max_depth_mm, compatible_kinds, active, authority_source
            FROM public.cnc_tools WHERE id = %s AND org_id = %s FOR UPDATE
            """,
            [str(tool_id), str(org_id)],
            "cnc_tool_not_found",
        )
    public = _public_tool(current)
    _check_authority_review(data, public)
    merged = {**public, **data}
    kind = str(merged["kind"])
    if kind not in _TOOL_KINDS:
        raise DocumentaryError("cnc_tool_invalid")
    compatible = _string_list(
        merged.get("compatible_kinds"), allowed=_OP_KINDS, code="cnc_tool_kind_invalid"
    )
    with documentary_backend():
        updated = one(
            """
            UPDATE public.cnc_tools SET
                code = %s, name = %s, kind = %s, diameter_mm = %s,
                working_length_mm = %s, max_depth_mm = %s,
                compatible_kinds = %s, active = %s, authority_source = %s
            WHERE id = %s AND org_id = %s
            RETURNING id, code, name, kind, diameter_mm, working_length_mm,
                      max_depth_mm, compatible_kinds, active, authority_source
            """,
            [
                str(merged["code"]).strip(),
                str(merged["name"]).strip(),
                kind,
                _dec(merged.get("diameter_mm")),
                _dec(merged.get("working_length_mm")),
                _dec(merged.get("max_depth_mm")),
                compatible,
                bool(merged["active"]),
                str(merged.get("authority_source") or "").strip(),
                str(tool_id),
                str(org_id),
            ],
            "cnc_tool_not_found",
        )
    return _public_tool(updated)


def list_machines(*, org_id: UUID) -> list[dict[str, object]]:
    return [
        _public_machine(row)
        for row in rows(
            """
            SELECT id, code, name, manufacturer, model, controller_family,
                   coordinate_systems, supported_kinds, supported_faces,
                   max_member_length_mm, safe_margin_mm, clamp_zones, tool_ids,
                   postprocessor_id, postprocessor_version, units, encoding, active, axes, clamps_declared, authority_source, machine_type, profile_setups
            FROM public.cnc_machines WHERE org_id = %s ORDER BY code
            """,
            [str(org_id)],
        )
    ]


def _clamp_zones(value: object) -> list[dict[str, object]]:
    value = _jsonb_value(value)
    if value is None:
        return []
    if not isinstance(value, list):
        raise DocumentaryError("cnc_clamp_zones_invalid")
    zones: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, dict):
            raise DocumentaryError("cnc_clamp_zones_invalid")
        start = _dec(item.get("start_mm"))
        end = _dec(item.get("end_mm"))
        if start is None or end is None or start < 0 or end <= start:
            raise DocumentaryError("cnc_clamp_zones_invalid")
        zones.append(
            {
                "start_mm": str(start),
                "end_mm": str(end),
                "label": str(item.get("label") or "")[:120],
            }
        )
    return zones


def _tool_ids(value: object, *, org_id: UUID) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise DocumentaryError("cnc_tool_ids_invalid")
    ids = [str(item) for item in value]
    if not ids:
        return []
    # Every magazine entry must resolve to an org tool — a phantom tool id
    # would make validation report the wrong blocker.
    found = rows(
        """
        SELECT id::text FROM public.cnc_tools
        WHERE org_id = %s AND id = ANY(%s::uuid[])
        """,
        [str(org_id), ids],
    )
    if {row["id"] for row in found} != set(ids):
        raise DocumentaryError("cnc_tool_not_in_org")
    return ids


def _machine_type(value):
    value = str(value or "")
    if value not in ("", "END_MILLER", "MACHINING_CENTER", "SAW", "DECLARED"):
        raise DocumentaryError("cnc_machine_invalid")
    return value


def _profile_setups(value):
    value = _jsonb_value(value)
    if value is None:
        return []
    if not isinstance(value, list):
        raise DocumentaryError("cnc_profile_setup_invalid")
    skus = set()
    for entry in value:
        if not isinstance(entry, dict) or set(entry) != {"profile_sku", "section_fingerprint", "loading_orientation", "axial_datum", "source"}:
            raise DocumentaryError("cnc_profile_setup_invalid")
        if not all(isinstance(v, str) and v.strip() for v in entry.values()):
            raise DocumentaryError("cnc_profile_setup_invalid")
        if (entry["profile_sku"] in skus or entry["loading_orientation"] not in ("EXTERIOR_UP", "EXTERIOR_DOWN", "EXTERIOR_LEFT", "EXTERIOR_RIGHT")
            or entry["axial_datum"] != "MEMBER_START" or len(entry["section_fingerprint"]) != 64
            or any(c not in "0123456789abcdef" for c in entry["section_fingerprint"])):
            raise DocumentaryError("cnc_profile_setup_invalid")
        skus.add(entry["profile_sku"])
    return value


def create_machine(
    *, org_id: UUID, actor_id: UUID, data: dict[str, object]
) -> dict[str, object]:
    code = str(data.get("code") or "").strip()
    name = str(data.get("name") or "").strip()
    if not code or not name:
        raise DocumentaryError("cnc_machine_invalid")
    supported_kinds = _string_list(
        data.get("supported_kinds"), allowed=_OP_KINDS, code="cnc_machine_kind_invalid"
    )
    supported_faces = _string_list(
        data.get("supported_faces"), allowed=_FACES, code="cnc_machine_face_invalid"
    )
    coordinates = _string_list(
        data.get("coordinate_systems"), allowed=_COORDS, code="cnc_machine_coord_invalid"
    )
    coordinates = coordinates if coordinates is not None else []
    with documentary_backend():
        created = one(
            """
            INSERT INTO public.cnc_machines
                (org_id, code, name, manufacturer, model, controller_family,
                 coordinate_systems, supported_kinds, supported_faces,
                 max_member_length_mm, safe_margin_mm, clamp_zones, tool_ids,
                 postprocessor_id, postprocessor_version, units, encoding, axes, clamps_declared, authority_source, machine_type, profile_setups)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::uuid[], %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            RETURNING id, code, name, manufacturer, model, controller_family,
                      coordinate_systems, supported_kinds, supported_faces,
                      max_member_length_mm, safe_margin_mm, clamp_zones, tool_ids,
                      postprocessor_id, postprocessor_version, units, encoding, active, axes, clamps_declared, authority_source, machine_type, profile_setups
            """,
            [
                str(org_id),
                code,
                name,
                str(data.get("manufacturer") or "")[:120],
                str(data.get("model") or "")[:120],
                str(data.get("controller_family") or "")[:80],
                coordinates,
                supported_kinds,
                supported_faces,
                _dec(data.get("max_member_length_mm")),
                _dec(data.get("safe_margin_mm")),
                json.dumps(_clamp_zones(data.get("clamp_zones"))),
                _tool_ids(data.get("tool_ids"), org_id=org_id),
                str(data.get("postprocessor_id") or "")[:80],
                str(data.get("postprocessor_version") or "")[:40],
                str(data.get("units") or "mm")[:20],
                str(data.get("encoding") or "utf-8")[:40],
                _string_list(data.get("axes"), allowed={"X", "Y", "Z", "A", "B", "C"}, code="cnc_machine_axis_invalid"),
                bool(data.get("clamps_declared", False)),
                str(data.get("authority_source") or "").strip(),
                _machine_type(data.get("machine_type")),
                json.dumps(_profile_setups(data.get("profile_setups"))),
            ],
            "cnc_machine_invalid",
        )
    return _public_machine(created)


@transaction.atomic
def update_machine(
    *, org_id: UUID, machine_id: UUID, data: dict[str, object]
) -> dict[str, object]:
    with documentary_backend():
        current = _public_machine(
            one(
                """
                SELECT id, code, name, manufacturer, model, controller_family,
                       coordinate_systems, supported_kinds, supported_faces,
                       max_member_length_mm, safe_margin_mm, clamp_zones, tool_ids,
                       postprocessor_id, postprocessor_version, units, encoding, active, axes, clamps_declared, authority_source, machine_type, profile_setups
                FROM public.cnc_machines WHERE id = %s AND org_id = %s FOR UPDATE
                """,
                [str(machine_id), str(org_id)],
                "cnc_machine_not_found",
            )
        )
    _check_authority_review(data, current)
    merged = {**current, **data}
    supported_kinds = _string_list(
        merged.get("supported_kinds"), allowed=_OP_KINDS, code="cnc_machine_kind_invalid"
    )
    supported_faces = _string_list(
        merged.get("supported_faces"), allowed=_FACES, code="cnc_machine_face_invalid"
    )
    coordinates = _string_list(
        merged.get("coordinate_systems"),
        allowed=_COORDS,
        code="cnc_machine_coord_invalid",
    )
    with documentary_backend():
        updated = one(
            """
            UPDATE public.cnc_machines SET
                code = %s, name = %s, manufacturer = %s, model = %s,
                controller_family = %s, coordinate_systems = %s,
                supported_kinds = %s, supported_faces = %s,
                max_member_length_mm = %s, safe_margin_mm = %s,
                clamp_zones = %s::jsonb, tool_ids = %s::uuid[],
                postprocessor_id = %s, postprocessor_version = %s,
                units = %s, encoding = %s, active = %s, updated_at = %s,
                axes = %s, clamps_declared = %s, authority_source = %s, machine_type = %s, profile_setups = %s::jsonb
            WHERE id = %s AND org_id = %s
            RETURNING id, code, name, manufacturer, model, controller_family,
                      coordinate_systems, supported_kinds, supported_faces,
                      max_member_length_mm, safe_margin_mm, clamp_zones, tool_ids,
                      postprocessor_id, postprocessor_version, units, encoding, active, axes, clamps_declared, authority_source, machine_type, profile_setups
            """,
            [
                str(merged["code"]).strip(),
                str(merged["name"]).strip(),
                str(merged.get("manufacturer") or "")[:120],
                str(merged.get("model") or "")[:120],
                str(merged.get("controller_family") or "")[:80],
                coordinates,
                supported_kinds,
                supported_faces,
                _dec(merged.get("max_member_length_mm")),
                _dec(merged.get("safe_margin_mm")),
                json.dumps(_clamp_zones(merged.get("clamp_zones"))),
                _tool_ids(merged.get("tool_ids"), org_id=org_id),
                str(merged.get("postprocessor_id") or "")[:80],
                str(merged.get("postprocessor_version") or "")[:40],
                str(merged.get("units") or "mm")[:20],
                str(merged.get("encoding") or "utf-8")[:40],
                bool(merged.get("active", True)),
                datetime.now(timezone.utc),
                _string_list(merged.get("axes"), allowed={"X", "Y", "Z", "A", "B", "C"}, code="cnc_machine_axis_invalid"),
                bool(merged.get("clamps_declared", False)),
                str(merged.get("authority_source") or "").strip(),
                _machine_type(merged.get("machine_type")),
                json.dumps(_profile_setups(merged.get("profile_setups"))),
                str(machine_id),
                str(org_id),
            ],
            "cnc_machine_not_found",
        )
    return _public_machine(updated)


def _machine_profile(
    machine_row: dict[str, object], tools_by_id: dict[str, dict[str, object]]
) -> MachineProfile:
    machine_row["profile_setups"] = _jsonb_list(machine_row.get("profile_setups"))
    machine_row["tool_sources"] = {str(tool["code"]): tool.get("authority_source", "")
        for tool_id in machine_row.get("tool_ids") or []
        if (tool := tools_by_id.get(str(tool_id))) is not None and tool.get("active", True)}
    magazine: list[Tool] = []
    for tool_id in machine_row["tool_ids"] or []:
        tool = tools_by_id.get(str(tool_id))
        if tool is None or not tool.get("active", True):
            continue
        magazine.append(
            Tool(
                tool_id=str(tool["code"]),
                kind=ToolKind(str(tool["kind"])),
                name=str(tool["name"]),
                diameter_mm=_dec(tool.get("diameter_mm")),
                working_length_mm=_dec(tool.get("working_length_mm")),
                max_depth_mm=_dec(tool.get("max_depth_mm")),
                compatible_kinds=(
                    [OperationKind(kind) for kind in tool["compatible_kinds"]]
                    if tool.get("compatible_kinds") is not None
                    else None
                ),
            )
        )
    return MachineProfile(
        machine_id=str(machine_row["code"]),
        name=str(machine_row["name"]),
        controller_family=str(machine_row["controller_family"]),
        coordinate_systems=[
            CoordinateSystem(value) for value in machine_row["coordinate_systems"] or []
        ],
        tools=magazine,
        supported_kinds=(
            [OperationKind(kind) for kind in machine_row["supported_kinds"]]
            if machine_row.get("supported_kinds") is not None
            else None
        ),
        supported_faces=(
            [MemberFace(face) for face in machine_row["supported_faces"]]
            if machine_row.get("supported_faces") is not None
            else None
        ),
        max_member_length_mm=_dec(machine_row.get("max_member_length_mm")),
        safe_margin_mm=_dec(machine_row.get("safe_margin_mm")),
        clamp_zones=[
            ClampZone(
                start_mm=Decimal(str(zone["start_mm"])),
                end_mm=Decimal(str(zone["end_mm"])),
                label=str(zone.get("label") or ""),
            )
            for zone in _jsonb_list(machine_row.get("clamp_zones"))
            if isinstance(zone, dict)
        ],
        postprocessor_id=str(machine_row["postprocessor_id"]),
        postprocessor_version=str(machine_row["postprocessor_version"]),
        units=str(machine_row["units"]),
        encoding=str(machine_row["encoding"]),
    )


def _order_ops(*, org_id: UUID, order_id: UUID) -> dict[str, object]:
    """Load the order's sealed plan + facts and derive the canonical ops —
    the same derivation the ops export runs, so readiness and programs can
    never disagree with what the shop already sees."""
    order = one(
        """
        SELECT id, order_code, status::text, payload_json, project_version_id,
               project_id
        FROM public.orders
        WHERE id = %s AND org_id = %s AND order_type = 'WORKSHOP_OT'
        """,
        [str(order_id), str(org_id)],
        "work_order_not_found",
    )
    payload = _decoded(order["payload_json"])
    if str(order["status"]) == "CANCELLED":
        raise DocumentaryError("work_order_cancelled")
    optimization = payload.get("optimization")
    if not isinstance(optimization, dict) or not optimization:
        raise DocumentaryError("operations_requires_optimization")
    if optimization.get("invalidated"):
        raise DocumentaryError("plan_invalidated")
    with documentary_backend():
        version_row = one(
            """
            SELECT snapshot_json, revision_code, project_id
            FROM public.project_versions WHERE id = %s AND org_id = %s
            """,
            [str(order["project_version_id"]), str(org_id)],
            "work_order_missing_version",
        )
    version_snapshot = _decoded(version_row["snapshot_json"])
    position_id = str(payload.get("position_id") or "") or None
    fact_units = _operations_fact_units(version_snapshot, position_id)
    bars = [
        CutBar.model_validate_json(json.dumps(bar))
        for bar in (optimization.get("bars") or {}).get("workshop_cut_plan") or []
    ]
    ops_issues: list[dict[str, object]] = []
    ops = operations_from_plan(
        bars=bars, fact_units=fact_units, issues=ops_issues
    )
    ops.extend(_sealed_hardware_operations(version_snapshot, position_id, fact_units, ops_issues))
    from production.cnc_coverage import declared_gaps, sealed_sections
    gaps = declared_gaps(version_snapshot, position_id, fact_units, ops, ops_issues)
    sections = sealed_sections(version_snapshot, position_id, fact_units)
    labels = _piece_labels(version_snapshot)
    member_labels = {
        str(member_id): code for member_id, code in labels.get("member", {}).items()
    }
    member_labels.update(
        {str(rid): code for rid, code in labels.get("reinforcement", {}).items()}
    )
    cut_map = _cut_member_map(version_snapshot, labels)
    for bar in (optimization.get("bars") or {}).get("workshop_cut_plan") or []:
        if isinstance(bar, dict):
            for cut in bar.get("cuts") or []:
                if isinstance(cut, dict) and cut.get("piece_id"):
                    member_labels.setdefault(
                        str(cut["piece_id"]),
                        str(cut_map.get(_cut_key(cut), "")),
                    )
    member_lengths = {
        member.member_id: member.cut_length_mm
        for unit in fact_units
        for member in unit.members
    }
    manufacturing = _raw_fact_units(version_snapshot, position_id)
    input_fingerprint = hashlib.sha256(json.dumps({
        "source": _ops_source_fingerprint(optimization, manufacturing),
        "sections": sections, "gaps": gaps, "authorization": "cnc-strict-v1",
    }, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    project_code = ""
    if order.get("project_id"):
        # project_manual_read excludes floor roles — the operator's CNC
        # file must still carry the project code it was cut for.
        with documentary_backend():
            project = rows(
                "SELECT code FROM public.projects WHERE id = %s AND org_id = %s",
                [str(order["project_id"]), str(org_id)],
            )
        project_code = str(project[0]["code"]) if project else ""
    return {
        "order": order,
        "payload": payload,
        "optimization": optimization,
        "ops": ops,
        "ops_issues": ops_issues,
        "declared_gaps": gaps,
        "sections": sections,
        "fact_units": fact_units,
        "member_labels": member_labels,
        "member_lengths": member_lengths,
        "input_fingerprint": input_fingerprint,
        "identity": {
            "order_code": str(order["order_code"]),
            "project_code": project_code,
            "revision_code": str(version_row.get("revision_code") or ""),
            "position_id": position_id or "",
            "plan_seed": str(
                (optimization.get("bars") or {}).get("plan_seed") or ""
            ),
        },
    }


def _tools_by_id(*, org_id: UUID) -> dict[str, dict[str, object]]:
    return {
        str(row["id"]): row
        for row in rows(
            """
            SELECT id::text, code, name, kind, diameter_mm, working_length_mm,
                   max_depth_mm, compatible_kinds, active, authority_source
            FROM public.cnc_tools WHERE org_id = %s
            """,
            [str(org_id)],
        )
    }


def cnc_readiness(
    *, org_id: UUID, order_id: UUID, machine_id: UUID | None = None
) -> dict[str, object]:
    """Per-member machining readiness against the org's real machines:
    every member that carries MEMBER ops gets a verdict + named blockers."""
    bundle = _order_ops(org_id=org_id, order_id=order_id)
    machines = rows(
        """
        SELECT id, code, name, manufacturer, model, controller_family,
               coordinate_systems, supported_kinds, supported_faces,
               max_member_length_mm, safe_margin_mm, clamp_zones, tool_ids,
               postprocessor_id, postprocessor_version, units, encoding, active, axes, clamps_declared, authority_source, machine_type, profile_setups
        FROM public.cnc_machines
        WHERE org_id = %s AND active
        """ + (" AND id = %s" if machine_id else "") + " ORDER BY code",
        [str(org_id)] + ([str(machine_id)] if machine_id else []),
    )
    tools_by_id = _tools_by_id(org_id=org_id)
    member_ops: dict[str, list] = {}
    for op in bundle["ops"]:
        if op.host_kind == "MEMBER":
            member_ops.setdefault(op.host, []).append(op)
    member_ids = sorted(member_meta_map(bundle["fact_units"]))
    machine_rows = machines
    machine_profiles = [
        _machine_profile(row, tools_by_id) for row in machine_rows
    ]
    member_meta = member_meta_map(bundle["fact_units"])
    members: list[dict[str, object]] = []
    for member_id in member_ids:
        label = bundle["member_labels"].get(member_id) or "Pieza sin dirección"
        meta = member_meta.get(member_id) or {}
        ops = member_ops.get(member_id, [])
        machine_results: list[dict[str, object]] = []
        for profile, machine_row in zip(machine_profiles, machine_rows):
            validations = authorize_member_operations(
                ops, profile, authority=machine_row,
                member_length_mm=bundle["member_lengths"].get(member_id),
                section=bundle["sections"].get(member_id), member_label=label,
                profile_sku=meta.get("workshop_sku"),
            )
            blockers = [item for item in validations if item.level == "BLOCK"]
            warnings = [item for item in validations if item.level == "WARN"]
            machine_results.append(
                {
                    "machine_id": str(machine_row["id"]),
                    "machine_code": machine_row["code"],
                    "machine_name": machine_row["name"],
                    "verdict": (
                        "BLOCK"
                        if blockers
                        else ("WARN" if warnings or bundle["declared_gaps"] else "PASS")
                    ),
                    "blockers": [item.model_dump(mode="json") for item in blockers],
                    "warnings": [item.model_dump(mode="json") for item in warnings],
                    "declared_unemitted": bundle["declared_gaps"],
                    "output_kind": "NEUTRAL_INTERCHANGE",
                }
            )
        members.append(
            {
                "member_id": member_id,
                "member_label": label,
                "workshop_sku": meta.get("workshop_sku"),
                "role": meta.get("role"),
                "bay_id": meta.get("bay_id"),
                "leaf_id": meta.get("leaf_id"),
                "position_index": meta.get("position_index"),
                "length_mm": str(bundle["member_lengths"].get(member_id) or ""),
                "operation_count": len(ops),
                "kinds": sorted({op.kind.value for op in ops}),
                "machines": machine_results,
                "preview": member_preview(ops=ops, length_mm=bundle["member_lengths"].get(member_id), section=bundle["sections"].get(member_id)),
                "geometry": meta,
                "operations": [
                    {
                        "operation_id": op.operation_id,
                        "kind": op.kind.value,
                        "u_mm": str(op.u_mm) if op.u_mm is not None else None,
                        "x_mm": str(op.x_mm) if op.x_mm is not None else None,
                        "y_mm": str(op.y_mm) if op.y_mm is not None else None,
                        "face": op.face.value if op.face else None,
                        "reference": op.reference,
                        "depth_mm": str(op.depth_mm) if op.depth_mm is not None else None,
                        "angle_left_deg": str(op.angle_left_deg)
                        if op.angle_left_deg is not None
                        else None,
                        "angle_right_deg": str(op.angle_right_deg)
                        if op.angle_right_deg is not None
                        else None,
                        "tool_id": op.tool_id,
                        "basis": op.basis,
                        "detail": op.detail,
                    }
                    for op in ops
                ],
            }
        )
    return {
        "order_id": str(order_id),
        "order_code": bundle["order"]["order_code"],
        "members": members,
        "issues": bundle["ops_issues"],
        "declared_unemitted": bundle["declared_gaps"],
        "identity": bundle["identity"],
        "plan_fingerprint": bundle["input_fingerprint"],
        # The op tool_ids a magazine must bind literally — without this list
        # a programmer has to guess that code "drill"/"end_mill" is required.
        "required_tool_ids": sorted(
            {op.tool_id for op in bundle["ops"] if op.tool_id}
        ),
        "machines": [_public_machine(row) for row in machine_rows],
        "programs": list_programs(org_id=org_id, order_id=order_id),
    }


def _machine_fingerprint(profile: MachineProfile, authority: dict[str, object] | None = None) -> str:
    """Content hash of the resolved machine profile — tools, limits, clamps,
    postprocessor. A machine-config change stales the programs generated
    against the previous profile, exactly like a plan change does."""
    return hashlib.sha256(
        json.dumps(
            {"profile": profile.model_dump(mode="json"), "authority": {key: (authority or {}).get(key) for key in ("active", "axes", "clamps_declared", "authority_source", "tool_sources", "machine_type", "profile_setups")}}, sort_keys=True, default=str
        ).encode("utf-8")
    ).hexdigest()


def _program_input(plan_fingerprint: str, machine_fingerprint: str) -> str:
    return f"{plan_fingerprint}+{machine_fingerprint}"


def _expected_program_input(
    *, org_id: UUID, order_id: UUID, machine_id: str | None,
) -> str | None:
    """The fingerprint a CURRENT program for this machine would carry today:
    sealed plan inputs + the machine profile as it exists now. None when the
    plan or the machine can't be resolved (everything then reads stale)."""
    if not machine_id:
        return None
    try:
        bundle = _order_ops(org_id=org_id, order_id=order_id)
        machine_row = rows(
            """
            SELECT id, code, name, manufacturer, model, controller_family,
                   coordinate_systems, supported_kinds, supported_faces,
                   max_member_length_mm, safe_margin_mm, clamp_zones, tool_ids,
                   postprocessor_id, postprocessor_version, units, encoding,
                   active, axes, clamps_declared, authority_source, machine_type, profile_setups
            FROM public.cnc_machines WHERE id = %s AND org_id = %s
            """,
            [str(machine_id), str(org_id)],
        )
    except DocumentaryError:
        return None
    if not machine_row or not machine_row[0].get("active"):
        return None
    machine_fp = _machine_fingerprint(
        _machine_profile(machine_row[0], _tools_by_id(org_id=org_id)), machine_row[0]
    )
    return _program_input(str(bundle["input_fingerprint"]), machine_fp)


def _program_no(*, order_code: str, member_label: str, machine_code: str, seq: int) -> str:
    label = "".join(ch for ch in member_label if ch.isalnum())[:12] or "M"
    return f"{order_code}-{label}-{machine_code}-{seq:02d}"


def preview_program(*, org_id: UUID, order_id: UUID, machine_id: UUID,
                    member_id: str) -> dict[str, object]:
    bundle = _order_ops(org_id=org_id, order_id=order_id)
    machine = one("SELECT * FROM public.cnc_machines WHERE id=%s AND org_id=%s AND active",
                  [str(machine_id), str(org_id)], "cnc_machine_not_found")
    profile = _machine_profile(machine, _tools_by_id(org_id=org_id))
    ops = [op for op in bundle["ops"] if op.host_kind == "MEMBER" and op.host == member_id]
    if not ops:
        raise DocumentaryError("cnc_member_no_ops")
    label = bundle["member_labels"].get(member_id) or "Pieza sin dirección"
    validation = authorize_member_operations(ops, profile, authority=machine,
        member_length_mm=bundle["member_lengths"].get(member_id),
        section=bundle["sections"].get(member_id), member_label=label,
        profile_sku=(member_meta_map(bundle["fact_units"]).get(member_id) or {}).get("workshop_sku"))
    blockers = [item.model_dump(mode="json") for item in validation if item.level == "BLOCK"]
    document = member_program(bundle["ops"], member_id=member_id, member_label=label,
        machine=profile, identity=bundle["identity"], validations=validation, issues=bundle["ops_issues"])
    document["machine"] = {**profile.model_dump(mode="json"), "authority_source": machine.get("authority_source"),
        "clamps_declared": machine.get("clamps_declared"), "axes": machine.get("axes"),
        "machine_type": machine.get("machine_type"), "profile_setups": _profile_setups(machine.get("profile_setups")),
        "tool_sources": machine.get("tool_sources")}
    document["preview"] = member_preview(ops=ops, length_mm=bundle["member_lengths"].get(member_id),
        section=bundle["sections"].get(member_id))
    document["declared_intent_gaps"] = bundle["declared_gaps"]
    document["verdict"] = "BLOCK" if blockers else "WARN" if bundle["declared_gaps"] else "PASS"
    prior = rows("SELECT id,program_no,files::text FROM public.cnc_programs WHERE org_id=%s AND work_order_id=%s AND machine_id=%s AND member_id=%s ORDER BY created_at DESC,id DESC LIMIT 1",
                 [str(org_id), str(order_id), str(machine_id), member_id])
    previous = None
    if prior:
        raw = _decoded(prior[0]["files"]).get("operations.json")
        previous = json.loads(raw) if isinstance(raw, str) else None
    review = hashlib.sha256(json.dumps({"proposed": document,
        "input": _program_input(str(bundle["input_fingerprint"]), _machine_fingerprint(profile, machine)),
        "previous_id": str(prior[0]["id"]) if prior else None,
        "status": str(bundle["order"]["status"])}, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return {"review_fingerprint": review, "verdict": "BLOCK" if blockers else "WARN" if bundle["declared_gaps"] else "PASS",
            "blockers": blockers, "member_label": label, "machine_code": machine["code"],
            "preview": document["preview"], "document": document,
            "diff": program_diff(previous, document), "declared_unemitted": bundle["declared_gaps"],
            "previous_id": str(prior[0]["id"]) if prior else None,
            "previous_no": prior[0]["program_no"] if prior else None,
            "output_kind": "NEUTRAL_INTERCHANGE"}


def generate_program(*, org_id: UUID, order_id: UUID, machine_id: UUID, member_id: str,
                     actor_id: UUID, expected_preview: str = "", confirmed: bool = False) -> dict[str, object]:
    with transaction.atomic(), documentary_backend():
        locked_order = one("SELECT id,status FROM public.orders WHERE id=%s AND org_id=%s AND order_type='WORKSHOP_OT' FOR UPDATE",
            [str(order_id), str(org_id)], "work_order_not_found")
        if str(locked_order["status"]) == "CANCELLED":
            raise DocumentaryError("work_order_cancelled")
        one("SELECT id FROM public.cnc_machines WHERE id=%s AND org_id=%s FOR UPDATE",
            [str(machine_id), str(org_id)], "cnc_machine_not_found")
        rows("SELECT id FROM public.cnc_tools WHERE org_id=%s ORDER BY id FOR SHARE", [str(org_id)])
        return _generate_program(org_id=org_id, order_id=order_id, machine_id=machine_id,
            member_id=member_id, actor_id=actor_id, expected_preview=expected_preview, confirmed=confirmed)


def _generate_program(
    *, org_id: UUID, order_id: UUID, machine_id: UUID, member_id: str,
    actor_id: UUID, expected_preview: str, confirmed: bool,
) -> dict[str, object]:
    if confirmed and expected_preview:
        previous = rows("SELECT id,program_no,verdict,fingerprint,operation_count,member_label,created_at,files::text,input_fingerprint,status FROM public.cnc_programs WHERE org_id=%s AND work_order_id=%s AND machine_id=%s AND member_id=%s AND review_fingerprint=%s",
            [str(org_id),str(order_id),str(machine_id),member_id,expected_preview])
        if previous:
            row = previous[0]
            if row["status"] != "CURRENT" or row["input_fingerprint"] != _expected_program_input(org_id=org_id,order_id=order_id,machine_id=str(machine_id)):
                raise DocumentaryError("cnc_preview_stale")
            return {**row, "id":str(row["id"]),"files":_decoded(row["files"]),"machine_code":one("SELECT code FROM public.cnc_machines WHERE id=%s AND org_id=%s",[str(machine_id),str(org_id)],"cnc_machine_not_found")["code"]}
    reviewed = preview_program(org_id=org_id, order_id=order_id, machine_id=machine_id, member_id=member_id)
    if not confirmed or not expected_preview:
        raise DocumentaryError("cnc_preview_required")
    if expected_preview != reviewed["review_fingerprint"]:
        raise DocumentaryError("cnc_preview_stale")
    if reviewed["verdict"] == "BLOCK":
        raise DocumentaryError("cnc_program_blocked", detail="No se puede generar: completa las autoridades señaladas en la vista previa.", extra={"blockers": reviewed["blockers"]})
    bundle = _order_ops(org_id=org_id, order_id=order_id)
    if str(bundle["order"]["status"]) == "CANCELLED":
        raise DocumentaryError("work_order_cancelled")
    tools_by_id = _tools_by_id(org_id=org_id)
    machine_row = one(
        """
        SELECT id, code, name, manufacturer, model, controller_family,
               coordinate_systems, supported_kinds, supported_faces,
               max_member_length_mm, safe_margin_mm, clamp_zones, tool_ids,
               postprocessor_id, postprocessor_version, units, encoding, active, axes, clamps_declared, authority_source, machine_type, profile_setups
        FROM public.cnc_machines
        WHERE id = %s AND org_id = %s AND active
        """,
        [str(machine_id), str(org_id)],
        "cnc_machine_not_found",
    )
    profile = _machine_profile(machine_row, tools_by_id)
    document = dict(reviewed["document"])
    document["verdict"] = reviewed["verdict"]
    from dekopen_engine.operations import ops_fingerprint
    document["fingerprint"] = ops_fingerprint(document)
    seq_row = one(
        """
        SELECT COUNT(*) + 1 AS seq FROM public.cnc_programs
        WHERE org_id = %s AND work_order_id = %s AND machine_id = %s AND member_id = %s
        """,
        [str(org_id), str(order_id), str(machine_id), member_id],
        "cnc_program_invalid",
    )
    program_no = _program_no(
        order_code=str(bundle["order"]["order_code"]),
        member_label=str(document["identity"]["member_label"]),
        machine_code=str(machine_row["code"]),
        seq=int(seq_row["seq"]),
    )
    files = NeutralOpsPostProcessor().render({
        **document, "schema": "dekopen_ops_v1", "output_kind": "NEUTRAL_INTERCHANGE",
        "order_code": bundle["identity"]["order_code"],
        "project_code": bundle["identity"]["project_code"],
        "revision_code": bundle["identity"]["revision_code"],
        "plan_seed": bundle["identity"]["plan_seed"],
        "plan_fingerprint": bundle["input_fingerprint"],
        "members": {member_id: member_meta_map(bundle["fact_units"]).get(member_id)},
        "piece_labels": bundle["member_labels"],
    })
    # The stored fingerprint binds plan inputs AND the machine profile — a
    # machine-config change invalidates the program like a plan change does.
    program_input = _program_input(
        str(bundle["input_fingerprint"]), _machine_fingerprint(profile, machine_row)
    )
    # Export manifest: which files this program ships, byte-identical hashes
    # to verify them against, and who generated it — the operator can check
    # what goes to which machine without opening each file.
    files["manifest.json"] = json.dumps(
        {
            "schema": "dekopen_export_manifest_v1",
            "kind": "cnc_program",
            "output_kind": "NEUTRAL_INTERCHANGE",
            "plan_fingerprint": bundle["input_fingerprint"],
            "plan_seed": bundle["identity"]["plan_seed"],
            "preview": reviewed["preview"],
            "declared_intent_gaps": bundle["declared_gaps"],
            "program_no": program_no,
            "identity": document["identity"],
            "verdict": document["verdict"],
            "fingerprint": document["fingerprint"],
            "input_fingerprint": program_input,
            "machine": {
                "id": str(machine_row["id"]),
                "code": machine_row["code"],
                "postprocessor_id": profile.postprocessor_id,
                "postprocessor_version": profile.postprocessor_version,
            },
            "files": {
                name: {
                    "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    "bytes": len(content.encode("utf-8")),
                }
                for name, content in files.items()
            },
            "operation_count": document["operation_count"],
            "counts_by_kind": document["counts_by_kind"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": str(actor_id),
        },
        indent=2,
        sort_keys=True,
        default=str,
    ) + "\n"
    with transaction.atomic(), documentary_backend():
        write(
            """
            UPDATE public.cnc_programs SET status = 'SUPERSEDED'
            WHERE org_id = %s AND work_order_id = %s AND machine_id = %s
              AND member_id = %s AND status = 'CURRENT'
            """,
            [str(org_id), str(order_id), str(machine_id), member_id],
        )
        created = one(
            """
            INSERT INTO public.cnc_programs
                (org_id, work_order_id, machine_id, member_id, member_label,
                 program_no, operation_count, verdict, fingerprint,
                 input_fingerprint, identity, files, created_by, review_fingerprint)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s)
            RETURNING id, program_no, verdict, fingerprint, created_at
            """,
            [
                str(org_id),
                str(order_id),
                str(machine_id),
                member_id,
                document["identity"]["member_label"],
                program_no,
                int(document["operation_count"]),
                str(document["verdict"]),
                str(document["fingerprint"]),
                program_input,
                json.dumps(document["identity"]),
                json.dumps(files),
                str(actor_id),
                expected_preview,
            ],
            "cnc_program_invalid",
        )
        rows(
            """
            INSERT INTO public.production_step_events(org_id, order_id, event, actor_id, payload)
            VALUES (%s, %s, 'WO_CNC_PROGRAM', %s, %s::jsonb)
            RETURNING id
            """,
            [
                str(org_id),
                str(order_id),
                str(actor_id),
                json.dumps(
                    {
                        "program_no": created["program_no"],
                        "member_id": member_id,
                        "member_label": document["identity"]["member_label"],
                        "machine_code": machine_row["code"],
                        "operation_count": document["operation_count"],
                        "verdict": document["verdict"],
                    }
                ),
            ],
        )
    return {
        "id": str(created["id"]),
        "program_no": created["program_no"],
        "verdict": document["verdict"],
        "fingerprint": document["fingerprint"],
        "operation_count": document["operation_count"],
        "member_label": document["identity"]["member_label"],
        "machine_code": machine_row["code"],
        "files": files,
        "created_at": created["created_at"],
    }


def list_programs(*, org_id: UUID, order_id: UUID) -> list[dict[str, object]]:
    program_rows = rows(
        """
        SELECT p.id, p.program_no, p.member_id, p.member_label, p.operation_count,
               p.verdict, p.fingerprint, p.input_fingerprint, p.status,
               p.created_at, p.identity::text, p.machine_id::text, m.code AS machine_code
        FROM public.cnc_programs p
        LEFT JOIN public.cnc_machines m ON m.id = p.machine_id
        WHERE p.org_id = %s AND p.work_order_id = %s
        ORDER BY p.created_at DESC
        """,
        [str(org_id), str(order_id)],
    )
    if not program_rows:
        return []
    # Fresh staleness: a program whose inputs changed since generation is
    # reported stale even if it still reads CURRENT (lazy supersede on
    # read — operators see the truth without a background job). Inputs now
    # include the machine profile, so editing clamps/tools/postprocessor
    # also stales the file.
    try:
        bundle = _order_ops(org_id=org_id, order_id=order_id)
        current_plan_input = str(bundle["input_fingerprint"])
    except DocumentaryError:
        current_plan_input = ""
    tools_by_id = _tools_by_id(org_id=org_id)
    machine_rows = rows(
        """
        SELECT id, code, name, manufacturer, model, controller_family,
               coordinate_systems, supported_kinds, supported_faces,
               max_member_length_mm, safe_margin_mm, clamp_zones, tool_ids,
               postprocessor_id, postprocessor_version, units, encoding,
               active, axes, clamps_declared, authority_source, machine_type, profile_setups
        FROM public.cnc_machines WHERE org_id = %s
        """,
        [str(org_id)],
    )
    expected_by_machine = {
        str(row["id"]): _program_input(
            current_plan_input,
            _machine_fingerprint(_machine_profile(row, tools_by_id), row),
        )
        for row in machine_rows if row.get("active") and current_plan_input
    }
    output: list[dict[str, object]] = []
    for row in program_rows:
        stale = (
            row["input_fingerprint"]
            != expected_by_machine.get(str(row["machine_id"]), "")
            or bool(row["status"] == "SUPERSEDED")
        )
        output.append(
            {
                "id": str(row["id"]),
                "program_no": row["program_no"],
                "member_id": row["member_id"],
                "member_label": row["member_label"],
                "operation_count": row["operation_count"],
                "verdict": row["verdict"],
                "fingerprint": row["fingerprint"],
                "status": "SUPERSEDED" if stale else "CURRENT",
                "machine_code": row["machine_code"],
                "created_at": row["created_at"],
                "identity": _decoded(row.get("identity") or {}),
                "input_fingerprint": row["input_fingerprint"],
                "machine_id": str(row["machine_id"]),
                "output_kind": "NEUTRAL_INTERCHANGE",
            }
        )
    for program in output:
        successor = next((other for other in output if other["status"] == "CURRENT"
            and other["member_id"] == program["member_id"] and other["machine_id"] == program["machine_id"]), None)
        program["replacement_id"] = successor["id"] if successor and successor["id"] != program["id"] else None
        program["replacement_no"] = successor["program_no"] if successor and successor["id"] != program["id"] else None
    return output


def program_file(
    *, org_id: UUID, program_id: UUID, filename: str
) -> tuple[str, str] | None:
    program = one(
        """
        SELECT p.program_no, p.files::text, p.input_fingerprint, p.status,
               p.work_order_id::text, p.machine_id::text
        FROM public.cnc_programs p
        WHERE p.id = %s AND p.org_id = %s
        """,
        [str(program_id), str(org_id)],
        "cnc_program_not_found",
    )
    if program["status"] == "SUPERSEDED":
        raise DocumentaryError("cnc_program_superseded")
    expected_input = _expected_program_input(
        org_id=org_id,
        order_id=UUID(str(program["work_order_id"])),
        machine_id=str(program["machine_id"]),
    )
    if expected_input is None or str(program["input_fingerprint"]) != expected_input:
        raise DocumentaryError("cnc_program_superseded")
    files = _decoded(program["files"])
    content = files.get(filename)
    if not isinstance(content, str):
        return None
    return f"{program['program_no']}-{filename}", content


def cnc_workspace(*, org_id: UUID) -> dict[str, object]:
    """Org-level CNC desk: machines, tools, and every optimized order's
    machining readiness at a glance (what needs CNC / what is blocked)."""
    machine_rows = [
        _public_machine(row)
        for row in rows(
            """
            SELECT id, code, name, manufacturer, model, controller_family,
                   coordinate_systems, supported_kinds, supported_faces,
                   max_member_length_mm, safe_margin_mm, clamp_zones, tool_ids,
                   postprocessor_id, postprocessor_version, units, encoding, active, axes, clamps_declared, authority_source, machine_type, profile_setups
            FROM public.cnc_machines WHERE org_id = %s ORDER BY code
            """,
            [str(org_id)],
        )
    ]
    orders = rows(
        """
        SELECT id::text, order_code, status::text, payload_json::text
        FROM public.orders
        WHERE org_id = %s AND order_type = 'WORKSHOP_OT'
        ORDER BY created_at DESC
        """,
        [str(org_id)],
    )
    order_rows: list[dict[str, object]] = []
    for order in orders:
        payload = _decoded(order["payload_json"])
        optimization = payload.get("optimization") or {}
        needs_machining = False
        if isinstance(optimization, dict) and not optimization.get("invalidated"):
            # An optimized order carries MEMBER ops when facts declare
            # machining (handles, end-milling) — full derive happens in
            # readiness; the desk lists orders that could need machining.
            needs_machining = bool(optimization.get("bars") or payload.get("materials"))
        programs = list_programs(org_id=org_id, order_id=UUID(str(order["id"]))) if needs_machining else []
        if needs_machining:
            order_rows.append(
                {
                    "order_id": order["id"],
                    "order_code": order["order_code"],
                    "status": order["status"],
                    "programs_total": len(programs),
                    "programs_current": sum(program["status"] == "CURRENT" for program in programs),
                }
            )
    return {
        "machines": machine_rows,
        "tools": list_tools(org_id=org_id),
        "orders": order_rows,
        "history": [{**row, "id": str(row["id"]), "entity_id": str(row["entity_id"]),
                     "previous": _jsonb_value(row["previous"]), "current": _jsonb_value(row["current"])}
                    for row in rows("SELECT id,entity_id,entity_kind,action,previous,current,actor_label,created_at FROM public.cnc_authority_events WHERE org_id=%s ORDER BY created_at DESC LIMIT 100", [str(org_id)])],
    }
