"""Compositional product model: assemblies of modules joined by couplings.

A DEKOPEN product is a `CoupledAssembly`: one or more `ProductModule`s
(rectangular parametric units reusing the proven per-module geometry)
joined by `CouplingDef`s — angled posts between adjacent module frames.
A single-unit window is the degenerate assembly: one module, no couplings.

`evaluate_product` separates two questions the UI must keep apart:

- Is the geometry constructible? (plan polygon, angle accumulation)
- Is the manufacturing definition complete? (module geometry evaluates,
  every coupling has a resolvable coupler profile, heights match)

The result status is INVALID / MANUFACTURING_INCOMPLETE / VALID. The engine
never invents catalog data: an unresolved coupler SKU is reported, never
faked.
"""

from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Literal

from pydantic import Field

from dekopen_engine.contour import (
    Contour,
    contour_area,
    contour_points,
    edge_length as contour_edge_length,
    ensure_ccw,
    interior_angle,
    offset_contour,
    validate_contour,
)
from dekopen_engine.geometry import (
    calculate_geometry,
    joint_adjustment_per_end,
    reinforcement_cut_length,
    resolve_bead_rule,
)
from dekopen_engine.glass import derive_net_glass_thickness
from dekopen_engine.models import (
    BayOpeningType,
    EffectiveProfileArticle,
    EngineModel,
    EngineResult,
    GlassPiece,
    NodeType,
    ParametricNode,
    PlanPoint,
    ProfileCut,
    ProfileRole,
    ReinforcementPiece,
    SystemParams,
)
from dekopen_engine.trig import cos_degrees, sin_degrees

QUANTUM_MM = Decimal("0.01")
_MAX_HEADING_DEG = Decimal("170")


class ProductStatus(str, Enum):
    VALID = "VALID"
    MANUFACTURING_INCOMPLETE = "MANUFACTURING_INCOMPLETE"
    INVALID = "INVALID"


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


class IssueCode(str, Enum):
    COUPLINGS_COUNT_MISMATCH = "couplings_count_mismatch"
    ASSEMBLY_FOLDS_BACK = "assembly_folds_back"
    PLAN_SELF_INTERSECTION = "plan_self_intersection"
    MODULE_GEOMETRY_FAILED = "module_geometry_failed"
    COUPLER_PROFILE_MISSING = "coupler_profile_missing"
    COUPLER_PROFILE_UNKNOWN = "coupler_profile_unknown"
    COUPLER_HEIGHT_MISMATCH = "coupler_height_mismatch"
    COUPLER_REINFORCEMENT_NONPOSITIVE = "coupler_reinforcement_nonpositive"
    CONTOUR_INVALID = "contour_invalid"
    CONTOUR_SPLITS_UNSUPPORTED = "contour_splits_unsupported"
    CONTOUR_OPENING_UNSUPPORTED = "contour_opening_unsupported"
    CONTOUR_PANEL_UNSUPPORTED = "contour_panel_unsupported"
    MEMBER_BENDING_REQUIRED = "member_bending_required"
    COUPLER_WIDTH_MISMATCH = "coupler_width_mismatch"
    COUPLER_MODULE_UNKNOWN = "coupler_module_unknown"
    COUPLER_EDGE_INVALID = "coupler_edge_invalid"
    COUPLER_EDGE_CONFLICT = "coupler_edge_conflict"
    CONNECTION_TYPE_UNSUPPORTED = "connection_type_unsupported"


class ConnectionKind(str, Enum):
    """Structural class of a module-to-module joint (mandate §6)."""

    INLINE = "INLINE"  # vertical post between same-height neighbors (any plan angle)
    STACKED = "STACKED"  # horizontal member — module on top of module
    TEE = "TEE"  # member landing mid-edge (declared; evaluated as unsupported)
    CORNER = "CORNER"  # framed corner assembly (declared; evaluated as unsupported)


class EdgeSide(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


class CouplingDef(EngineModel):
    """Joint between two modules of an assembly.

    `angle_deg` is the signed deflection of the front chain at the joint:
    positive turns the next module counterclockwise (plan view). Zero is a
    coplanar coupling.

    `modules`/`edges` name the two endpoints explicitly — `modules[i]`'s
    `edges[i]` side joins `modules[j]`'s `edges[j]` side. When absent the
    coupling keeps the legacy positional binding: modules[i] right to
    modules[i+1] left, in declaration order.
    """

    id: str
    angle_deg: Decimal = Decimal("0")
    coupler_profile_sku: str | None = None
    kind: ConnectionKind = ConnectionKind.INLINE
    modules: list[str] | None = None
    edges: list[EdgeSide] | None = None


class ProductModule(EngineModel):
    id: str
    # Nominal bounding rectangle — still drives plan-view layout and module
    # pitch. For contour modules these equal the contour bounding box.
    width_mm: Decimal = Field(gt=0)
    height_mm: Decimal = Field(gt=0)
    # Non-rectangular outer shape (elevation, module-local mm). When set the
    # module evaluates through the contour path: frame members follow edges,
    # miters are corner interior / 2, and the fill region is the inward
    # offset. `tree` must then be a single BAY leaf carrying the region spec.
    contour: Contour | None = None
    tree: ParametricNode


class CoupledAssembly(EngineModel):
    modules: list[ProductModule] = Field(min_length=1)
    couplings: list[CouplingDef] = Field(default_factory=list)


class ProductModel(EngineModel):
    version: Literal["product-v2"]
    assembly: CoupledAssembly


class PlanModule(EngineModel):
    module_id: str
    # front-left, front-right, back-right, back-left
    corners: list[PlanPoint]


class PlanCoupling(EngineModel):
    coupling_id: str
    polygon: list[PlanPoint]


class PlanGeometry(EngineModel):
    front_chain: list[PlanPoint]
    modules: list[PlanModule]
    couplings: list[PlanCoupling]
    min_x_mm: Decimal
    min_y_mm: Decimal
    width_mm: Decimal
    height_mm: Decimal


class ProductIssue(EngineModel):
    code: str
    severity: Severity
    target: str
    params: dict[str, str] = Field(default_factory=dict)


class ModuleEvaluation(EngineModel):
    module_id: str
    issues: list[ProductIssue] = Field(default_factory=list)
    result: EngineResult | None = None


class ProductEvaluation(EngineModel):
    status: ProductStatus
    issues: list[ProductIssue] = Field(default_factory=list)
    plan: PlanGeometry | None = None
    modules: list[ModuleEvaluation] = Field(default_factory=list)
    bom: EngineResult | None = None


def _q(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM_MM, rounding=ROUND_HALF_UP)


def _seg_intersects(
    a1: PlanPoint, a2: PlanPoint, b1: PlanPoint, b2: PlanPoint
) -> bool:
    def orient(p: PlanPoint, q: PlanPoint, r: PlanPoint) -> Decimal:
        return (q.x_mm - p.x_mm) * (r.y_mm - p.y_mm) - (q.y_mm - p.y_mm) * (
            r.x_mm - p.x_mm
        )

    o1 = orient(a1, a2, b1)
    o2 = orient(a1, a2, b2)
    o3 = orient(b1, b2, a1)
    o4 = orient(b1, b2, a2)
    return (o1 * o2 < 0) and (o3 * o4 < 0)


def _polygons_overlap(
    a: list[PlanPoint], b: list[PlanPoint], *, interior_only: bool = False
) -> bool:
    """SAT overlap test for convex polygons.

    Exact for our module rectangles and coupler wedges: any separating axis
    (an edge normal of either polygon) means disjoint; otherwise the polygons
    intersect — including containment and edge-touch, which both collide
    physically. With `interior_only`, touching at a vertex or edge does not
    count: only positive-area overlap is reported (adjacent modules always
    share their joint boundary, so only interior penetration is a collision).
    """

    def span(points: list[PlanPoint], nx: Decimal, ny: Decimal) -> tuple[Decimal, Decimal]:
        values = [p.x_mm * nx + p.y_mm * ny for p in points]
        return min(values), max(values)

    for poly in (a, b):
        count = len(poly)
        for i in range(count):
            edge = poly[(i + 1) % count]
            ex = edge.x_mm - poly[i].x_mm
            ey = edge.y_mm - poly[i].y_mm
            lo_a, hi_a = span(a, -ey, ex)
            lo_b, hi_b = span(b, -ey, ex)
            if interior_only:
                if hi_a <= lo_b or hi_b <= lo_a:
                    return False
            elif hi_a < lo_b or hi_b < lo_a:
                return False
    return True


def _plan_geometry(
    assembly: CoupledAssembly, depth_mm: Decimal
) -> tuple[PlanGeometry, list[ProductIssue]]:
    """Project the assembly into a top-view polygon.

    Module i runs from front-chain point F_i to F_{i+1} along heading
    theta_i; theta_0 = 0 and theta_{i+1} = theta_i + coupling[i].angle_deg.
    The back edge of every module is offset by `depth_mm` along its local
    normal; the gap between two module rectangles at a joint is the coupler
    wedge polygon.
    """
    issues: list[ProductIssue] = []
    modules = assembly.modules
    couplings = assembly.couplings

    headings: list[Decimal] = [Decimal(0)]
    for coupling in couplings:
        heading = headings[-1] + coupling.angle_deg
        if abs(heading) > _MAX_HEADING_DEG:
            issues.append(
                ProductIssue(
                    code=IssueCode.ASSEMBLY_FOLDS_BACK.value,
                    severity=Severity.ERROR,
                    target=f"coupling:{coupling.id}",
                    params={"heading_deg": str(_q(heading))},
                )
            )
        headings.append(heading)
    while len(headings) < len(modules):
        headings.append(headings[-1])

    # Modules joined by a STACKED coupling project onto their lower partner's
    # plan footprint (same front slot, same depth) — they are not a new chain
    # segment. Anchor = the endpoint whose TOP edge is the contact (lower),
    # resolved transitively for towers; cycles degrade to "no anchor".
    stack_parent: dict[str, str] = {}
    coupling_pairs: set[frozenset[str]] = set()
    for index, coupling in enumerate(couplings):
        pair = coupling.modules
        if pair is None and index < len(modules) - 1:
            pair = [modules[index].id, modules[index + 1].id]
        if pair is not None and len(pair) == 2:
            coupling_pairs.add(frozenset(pair))
        if coupling.kind is not ConnectionKind.STACKED:
            continue
        edges = coupling.edges or [EdgeSide.TOP, EdgeSide.BOTTOM]
        if pair is not None and len(pair) == 2 and len(edges) == 2:
            top_index = (
                0
                if edges[0] is EdgeSide.TOP
                else (1 if edges[1] is EdgeSide.TOP else None)
            )
            if top_index is not None:
                stack_parent[pair[1 - top_index]] = pair[top_index]

    def _anchor(module_id: str) -> str | None:
        seen: set[str] = set()
        current = module_id
        while current in stack_parent and current not in seen:
            seen.add(current)
            current = stack_parent[current]
        return None if current in stack_parent else current

    front: list[PlanPoint] = [PlanPoint(x_mm=Decimal(0), y_mm=Decimal(0))]
    normals: list[PlanPoint] = []
    plan_modules: list[PlanModule] = []
    plan_couplings: list[PlanCoupling] = []
    all_points: list[PlanPoint] = []
    corners_by_module: dict[str, list[PlanPoint]] = {}
    stack_root: dict[str, str] = {}
    front_module_ids: list[str] = []

    for index, module in enumerate(modules):
        anchor = _anchor(module.id) if module.id in stack_parent else None
        if anchor is not None and anchor in corners_by_module:
            corners = corners_by_module[anchor]
            plan_modules.append(PlanModule(module_id=module.id, corners=corners))
            stack_root[module.id] = anchor
            continue
        front_module_ids.append(module.id)
        theta = headings[index]
        cos_t = cos_degrees(theta)
        sin_t = sin_degrees(theta)
        end_x = front[-1].x_mm + module.width_mm * cos_t
        end_y = front[-1].y_mm + module.width_mm * sin_t
        front.append(PlanPoint(x_mm=end_x, y_mm=end_y))
        normal = PlanPoint(x_mm=-sin_t, y_mm=cos_t)
        normals.append(normal)

        start = front[-2]
        end = front[-1]
        back_start = PlanPoint(
            x_mm=start.x_mm - depth_mm * normal.x_mm,
            y_mm=start.y_mm - depth_mm * normal.y_mm,
        )
        back_end = PlanPoint(
            x_mm=end.x_mm - depth_mm * normal.x_mm,
            y_mm=end.y_mm - depth_mm * normal.y_mm,
        )
        corners = [start, end, back_end, back_start]
        corners_by_module[module.id] = corners
        plan_modules.append(
            PlanModule(
                module_id=module.id,
                corners=corners,
            )
        )
        all_points.extend([start, end, back_start, back_end])

        if index < len(modules) - 1 and index < len(couplings):
            coupling = couplings[index]
            adjacent = coupling.modules is None or coupling.modules == [
                modules[index].id,
                modules[index + 1].id,
            ]
            if coupling.kind is ConnectionKind.INLINE and adjacent:
                next_theta = headings[index + 1]
                next_normal = PlanPoint(
                    x_mm=-sin_degrees(next_theta), y_mm=cos_degrees(next_theta)
                )
                joint = end
                back_left = PlanPoint(
                    x_mm=joint.x_mm - depth_mm * next_normal.x_mm,
                    y_mm=joint.y_mm - depth_mm * next_normal.y_mm,
                )
                plan_couplings.append(
                    PlanCoupling(
                        coupling_id=coupling.id,
                        polygon=[joint, back_end, back_left],
                    )
                )
                all_points.extend([back_left])

    # Non-adjacent front segments must not cross.
    for i in range(len(front) - 1):
        for j in range(i + 2, len(front) - 1):
            if _seg_intersects(front[i], front[i + 1], front[j], front[j + 1]):
                issues.append(
                    ProductIssue(
                        code=IssueCode.PLAN_SELF_INTERSECTION.value,
                        severity=Severity.ERROR,
                        target="assembly",
                        params={
                            "first": front_module_ids[i],
                            "second": front_module_ids[j],
                        },
                    )
                )

    # Depth polygons must not collide either: front chains can stay disjoint
    # while two module rectangles or a coupler wedge overlap in depth.
    # Modules stacked on one anchor share the footprint by design — excluded,
    # and coupling-declared endpoint pairs legitimately share a boundary.
    def _co_stacked(id_a: str, id_b: str) -> bool:
        return (
            id_a in stack_root
            and id_b in stack_root
            and stack_root[id_a] == stack_root[id_b]
        ) or stack_root.get(id_a) == id_b or stack_root.get(id_b) == id_a

    rects = [(module.module_id, module.corners) for module in plan_modules]
    for i, (id_a, poly_a) in enumerate(rects):
        for j in range(i + 1, len(rects)):
            id_b, poly_b = rects[j]
            if _co_stacked(id_a, id_b):
                continue
            # Adjacent chain slots touch; coupling-declared columns touch —
            # including anchored siblings stacked over declared partners.
            root_a, root_b = stack_root.get(id_a, id_a), stack_root.get(id_b, id_b)
            expected_contact = (
                j == i + 1 or frozenset({root_a, root_b}) in coupling_pairs
            )
            if _polygons_overlap(poly_a, poly_b, interior_only=expected_contact):
                issues.append(
                    ProductIssue(
                        code=IssueCode.PLAN_SELF_INTERSECTION.value,
                        severity=Severity.ERROR,
                        target=f"module:{id_b}",
                        params={"other": id_a},
                    )
                )
    for index, plan_coupling in enumerate(plan_couplings):
        for j, (id_b, poly_b) in enumerate(rects):
            if j in (index, index + 1):
                continue
            if _polygons_overlap(plan_coupling.polygon, poly_b):
                issues.append(
                    ProductIssue(
                        code=IssueCode.PLAN_SELF_INTERSECTION.value,
                        severity=Severity.ERROR,
                        target=f"module:{id_b}",
                        params={"other": f"coupling:{plan_coupling.coupling_id}"},
                    )
                )

    quantized = [PlanPoint(x_mm=_q(p.x_mm), y_mm=_q(p.y_mm)) for p in all_points]
    min_x = min(p.x_mm for p in quantized)
    min_y = min(p.y_mm for p in quantized)
    max_x = max(p.x_mm for p in quantized)
    max_y = max(p.y_mm for p in quantized)
    plan = PlanGeometry(
        front_chain=[
            PlanPoint(x_mm=_q(p.x_mm), y_mm=_q(p.y_mm)) for p in front
        ],
        modules=[
            PlanModule(
                module_id=m.module_id,
                corners=[
                    PlanPoint(x_mm=_q(c.x_mm), y_mm=_q(c.y_mm))
                    for c in m.corners
                ],
            )
            for m in plan_modules
        ],
        couplings=[
            PlanCoupling(
                coupling_id=c.coupling_id,
                polygon=[
                    PlanPoint(x_mm=_q(p.x_mm), y_mm=_q(p.y_mm))
                    for p in c.polygon
                ],
            )
            for c in plan_couplings
        ],
        min_x_mm=min_x,
        min_y_mm=min_y,
        width_mm=max_x - min_x,
        height_mm=max_y - min_y,
    )
    return plan, issues


def _top_with_module_dims(module: ProductModule) -> ParametricNode:
    tree = module.tree
    if tree.width_mm is not None and tree.width_mm != module.width_mm:
        raise ValueError(f"{module.id}: tree width conflicts with module width")
    if tree.height_mm is not None and tree.height_mm != module.height_mm:
        raise ValueError(f"{module.id}: tree height conflicts with module height")
    return tree.model_copy(
        update={"width_mm": module.width_mm, "height_mm": module.height_mm}
    )


def _prefix_result(module_id: str, result: EngineResult) -> EngineResult:
    prefix = f"{module_id}|"

    def bay(bay_id: str | None) -> str | None:
        return f"{prefix}{bay_id}" if bay_id is not None else None

    def leaf(leaf_id: str | None) -> str | None:
        return f"{prefix}{leaf_id}" if leaf_id is not None else None

    return EngineResult(
        profile_cuts=[
            cut.model_copy(
                update={"bay_id": bay(cut.bay_id), "leaf_id": leaf(cut.leaf_id)}
            )
            for cut in result.profile_cuts
        ],
        reinforcements=[
            piece.model_copy(
                update={
                    "bay_id": bay(piece.bay_id),
                    "leaf_id": leaf(piece.leaf_id),
                }
            )
            for piece in result.reinforcements
        ],
        glasses=[
            piece.model_copy(
                update={
                    "bay_id": bay(piece.bay_id),
                    "leaf_id": leaf(piece.leaf_id),
                }
            )
            for piece in result.glasses
        ],
        panels=[
            piece.model_copy(
                update={"bay_id": bay(piece.bay_id), "leaf_id": leaf(piece.leaf_id)}
            )
            for piece in result.panels
        ],
        hardware_items=[
            item.model_copy(
                update={
                    "bay_id": bay(item.bay_id),
                    "leaf_id": leaf(item.leaf_id),
                }
            )
            for item in result.hardware_items
        ],
        leaf_weights=[
            weight.model_copy(
                update={
                    "bay_id": bay(weight.bay_id),
                    "leaf_id": leaf(weight.leaf_id),
                }
            )
            for weight in result.leaf_weights
        ],
    )


def _single_region_leaf(tree: ParametricNode) -> ParametricNode | None:
    """The region spec of a contour module: a bare BAY or ROOT wrapping one."""
    top = tree.children[0] if tree.type is NodeType.ROOT and len(tree.children) == 1 else tree
    return top if top.type is NodeType.BAY and not top.children else None


_ANGLE_Q = Decimal("0.1")


def _qa(value: Decimal) -> Decimal:
    """Canonical cut-angle quantum — serializer accepts angles at 0.1° only."""
    return value.quantize(_ANGLE_Q, rounding=ROUND_HALF_UP)


def _is_axis_rect(contour: Contour) -> bool:
    """Four straight axis-aligned edges — the classic glass rectangle."""
    if len(contour.vertices) != 4 or any(contour.bulges):
        return False
    n = 4
    return all(
        contour.vertices[i].x_mm == contour.vertices[(i + 1) % n].x_mm
        or contour.vertices[i].y_mm == contour.vertices[(i + 1) % n].y_mm
        for i in range(n)
    )


def _evaluate_contour_module(
    module: ProductModule,
    params: SystemParams,
    *,
    is_foiled: bool,
) -> tuple[EngineResult | None, list[ProductIssue]]:
    """Evaluate a non-rectangular module: frame follows the contour, one
    inward-offset fill region per module.

    Trapezoid/arch/triangle modules get real member lengths and miter cuts
    (corner interior / 2 — the welded-rect 45° rule generalized), an exact
    glass polygon, and bead cuts per edge. Anything the kernel cannot build
    honestly (split trees, operable leaves, panels, bends without a bending
    authority) is reported, never approximated into a rectangle.
    """
    issues: list[ProductIssue] = []
    target = f"module:{module.id}"
    assert module.contour is not None
    contour = ensure_ccw(module.contour)

    problems = validate_contour(contour)
    if problems:
        issues.append(
            ProductIssue(
                code=IssueCode.CONTOUR_INVALID.value,
                severity=Severity.ERROR,
                target=target,
                params={"reason": "; ".join(problems)},
            )
        )
        return None, issues

    leaf = _single_region_leaf(module.tree)
    if leaf is None:
        issues.append(
            ProductIssue(
                code=IssueCode.CONTOUR_SPLITS_UNSUPPORTED.value,
                severity=Severity.ERROR,
                target=target,
            )
        )
        return None, issues

    opening = leaf.opening_type or BayOpeningType.FIXED
    if opening is not BayOpeningType.FIXED:
        issues.append(
            ProductIssue(
                code=IssueCode.CONTOUR_OPENING_UNSUPPORTED.value,
                severity=Severity.WARNING,
                target=target,
                params={"opening": opening.value},
            )
        )
        # The frame is still buildable; the operable leaf is not (v1).
        # Emit frame + infill as a fixed region so BOM stays honest about
        # what exists, while the warning keeps the module incomplete.
    if leaf.panel_article_sku is not None:
        issues.append(
            ProductIssue(
                code=IssueCode.CONTOUR_PANEL_UNSUPPORTED.value,
                severity=Severity.WARNING,
                target=target,
                params={"sku": leaf.panel_article_sku},
            )
        )

    frame = params.effective_profile_articles[ProfileRole.FRAME]
    per_end = joint_adjustment_per_end(params, frame)
    n = len(contour.vertices)

    profile_cuts: list[ProfileCut] = []
    reinforcements: list[ReinforcementPiece] = []
    glasses: list[GlassPiece] = []

    for i in range(n):
        bulge = contour.bulges[i]
        length = contour_edge_length(contour, i) + 2 * per_end
        sagitta = bulge if bulge else None
        profile_cuts.append(
            ProfileCut(
                sku=frame.sku,
                role=ProfileRole.FRAME,
                material=frame.material,
                length_mm=_q(length),
                angle_left=_qa(interior_angle(contour, i) / 2),
                angle_right=_qa(interior_angle(contour, (i + 1) % n) / 2),
                qty=1,
                bay_id=leaf.id,
                sagitta_mm=_q(sagitta) if sagitta is not None else None,
            )
        )
        if sagitta is not None:
            issues.append(
                ProductIssue(
                    code=IssueCode.MEMBER_BENDING_REQUIRED.value,
                    severity=Severity.WARNING,
                    target=target,
                    params={"edge": str(i), "sagitta_mm": str(_q(sagitta))},
                )
            )
        if frame.reinforcement_sku is not None:
            reinforcements.append(
                ReinforcementPiece(
                    parent_profile_sku=frame.sku,
                    reinforcement_sku=frame.reinforcement_sku,
                    role=ProfileRole.FRAME,
                    length_mm=_q(reinforcement_cut_length(length, frame, 2)),
                    qty=1,
                    bay_id=leaf.id,
                    sagitta_mm=_q(sagitta) if sagitta is not None else None,
                )
            )

    clearance_mm = params.glass_clearance_foil_mm if is_foiled else params.glass_clearance_white_mm
    # Inward offset that lands exactly on the rect-path pocket math:
    # pocket = finished - 2*face + 2*rebate - 2*clearance.
    inset = frame.face_width_mm - params.rebate_depth_mm + clearance_mm
    try:
        fill = offset_contour(contour, inset)
    except ValueError as error:
        issues.append(
            ProductIssue(
                code=IssueCode.CONTOUR_INVALID.value,
                severity=Severity.ERROR,
                target=target,
                params={"reason": str(error)},
            )
        )
        return None, issues

    fill_area_mm2 = contour_area(fill.vertices, fill.bulges)
    # A collapsed offset inverts the pocket (negative shoelace area) or
    # self-intersects — both are structural failures, not a small glass.
    if fill_area_mm2 <= 0 or validate_contour(fill):
        issues.append(
            ProductIssue(
                code=IssueCode.CONTOUR_INVALID.value,
                severity=Severity.ERROR,
                target=target,
                params={"reason": "frame inset collapsed the glass pocket"},
            )
        )
        return None, issues

    if leaf.glass_thickness_mm is None or leaf.glass_spec is None:
        raise ValueError(f"contour region {leaf.id} requires glass_thickness_mm and glass_spec")

    thickness_net = derive_net_glass_thickness(leaf.glass_spec, leaf.glass_thickness_mm)
    area_m2 = (fill_area_mm2 / Decimal("1000000")).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP
    )
    weight_kg = (fill_area_mm2 / Decimal("1000000") * thickness_net * Decimal("2.50")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    xs = [v.x_mm for v in fill.vertices]
    ys = [v.y_mm for v in fill.vertices]
    glasses.append(
        GlassPiece(
            bay_id=leaf.id,
            width_mm=_q(max(xs) - min(xs)),
            height_mm=_q(max(ys) - min(ys)),
            area_m2=area_m2,
            weight_kg=weight_kg,
            thickness_net_mm=thickness_net.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            glass_spec=leaf.glass_spec,
            article_sku=leaf.glass_article_sku,
            # An axis-aligned rect fill is the classic rectangle — `shape`
            # stays None so production sheet-nests it like any other pane.
            shape=None if _is_axis_rect(fill) else contour_points(fill),
        )
    )

    # Glazing beads run the fill boundary, one cut per edge.
    rule = resolve_bead_rule(leaf.glass_thickness_mm, params)
    fill_n = len(fill.vertices)
    for i in range(fill_n):
        bulge = fill.bulges[i]
        profile_cuts.append(
            ProfileCut(
                sku=rule.bead_article.sku,
                role=ProfileRole.GLAZING_BEAD,
                material=rule.bead_article.material,
                length_mm=_q(contour_edge_length(fill, i) + rule.cut_add_mm),
                angle_left=_qa(interior_angle(fill, i) / 2),
                angle_right=_qa(interior_angle(fill, (i + 1) % fill_n) / 2),
                qty=1,
                bay_id=leaf.id,
                sagitta_mm=_q(bulge) if bulge else None,
            )
        )
        if bulge:
            issues.append(
                ProductIssue(
                    code=IssueCode.MEMBER_BENDING_REQUIRED.value,
                    severity=Severity.WARNING,
                    target=target,
                    params={"edge": f"bead-{i}", "sagitta_mm": str(_q(bulge))},
                )
            )

    return (
        EngineResult(
            profile_cuts=profile_cuts,
            reinforcements=reinforcements,
            glasses=glasses,
        ),
        issues,
    )


def evaluate_product(
    product: ProductModel,
    params: SystemParams,
    *,
    coupler_articles: dict[str, EffectiveProfileArticle] | None = None,
    is_foiled: bool = False,
) -> ProductEvaluation:
    """Evaluate an assembly: plan geometry, per-module geometry, couplers, BOM."""
    assembly = product.assembly
    modules = assembly.modules
    couplings = assembly.couplings
    issues: list[ProductIssue] = []

    if len({module.id for module in modules}) != len(modules) or len(
        {coupling.id for coupling in couplings}
    ) != len(couplings):
        raise ValueError("module and coupling ids must be unique")

    # The modules-1 chain count only constrains positional couplings — their
    # endpoints ARE the chain slots. Explicit-endpoint couplings declare a
    # structured graph (stacked towers, TEE joins) where any count is legal.
    positional = [c for c in couplings if c.modules is None]
    if positional and len(couplings) != len(modules) - 1:
        issues.append(
            ProductIssue(
                code=IssueCode.COUPLINGS_COUNT_MISMATCH.value,
                severity=Severity.ERROR,
                target="assembly",
                params={
                    "modules": str(len(modules)),
                    "couplings": str(len(couplings)),
                },
            )
        )

    plan, plan_issues = _plan_geometry(assembly, params.depth_mm)
    issues.extend(plan_issues)

    module_evals: list[ModuleEvaluation] = []
    aggregated: list[EngineResult] = []
    for module in modules:
        module_issues: list[ProductIssue] = []
        result: EngineResult | None = None
        try:
            if module.contour is not None:
                result, contour_issues = _evaluate_contour_module(
                    module, params, is_foiled=is_foiled
                )
                module_issues.extend(contour_issues)
            else:
                result = calculate_geometry(
                    _top_with_module_dims(module), params, is_foiled=is_foiled
                )
            if result is not None:
                aggregated.append(_prefix_result(module.id, result))
        except (ValueError, KeyError, NotImplementedError) as error:
            module_issues.append(
                ProductIssue(
                    code=IssueCode.MODULE_GEOMETRY_FAILED.value,
                    severity=Severity.WARNING,
                    target=f"module:{module.id}",
                    params={"reason": str(error)},
                )
            )
        module_evals.append(
            ModuleEvaluation(
                module_id=module.id, issues=module_issues, result=result
            )
        )
        issues.extend(module_issues)

    coupler_cuts: list[ProfileCut] = []
    coupler_reinforcements: list[ReinforcementPiece] = []
    coupler_articles = coupler_articles or {}
    module_by_id = {module.id: module for module in modules}
    claimed_edges: set[tuple[str, EdgeSide]] = set()
    for index, coupling in enumerate(couplings):
        target = f"coupling:{coupling.id}"
        if coupling.kind in (ConnectionKind.TEE, ConnectionKind.CORNER):
            # Declared in the model, honestly not yet manufacturable — a T or
            # framed-corner joint needs machining consequences we don't have.
            issues.append(
                ProductIssue(
                    code=IssueCode.CONNECTION_TYPE_UNSUPPORTED.value,
                    severity=Severity.WARNING,
                    target=target,
                    params={"kind": coupling.kind.value},
                )
            )
            continue
        # Endpoint resolution: explicit ids win; absent endpoints keep the
        # legacy positional binding (module i right to module i+1 left).
        if coupling.modules is not None:
            first = module_by_id.get(coupling.modules[0])
            second = (
                module_by_id.get(coupling.modules[1])
                if len(coupling.modules) > 1
                else None
            )
        elif index < len(modules) - 1:
            first, second = modules[index], modules[index + 1]
        else:
            first = second = None
        if first is None or second is None or first.id == second.id:
            issues.append(
                ProductIssue(
                    code=IssueCode.COUPLER_MODULE_UNKNOWN.value,
                    severity=Severity.WARNING,
                    target=target,
                )
            )
            continue
        edges = coupling.edges
        if edges is None:
            edges = (
                [EdgeSide.RIGHT, EdgeSide.LEFT]
                if coupling.kind is ConnectionKind.INLINE
                else [EdgeSide.TOP, EdgeSide.BOTTOM]
            )
        if len(edges) != 2:
            issues.append(
                ProductIssue(
                    code=IssueCode.COUPLER_EDGE_INVALID.value,
                    severity=Severity.WARNING,
                    target=target,
                )
            )
            continue
        sides = set(edges)
        valid = (
            sides <= {EdgeSide.LEFT, EdgeSide.RIGHT}
            if coupling.kind is ConnectionKind.INLINE
            else sides <= {EdgeSide.TOP, EdgeSide.BOTTOM}
        )
        if not valid or len(sides) != 2:
            issues.append(
                ProductIssue(
                    code=IssueCode.COUPLER_EDGE_INVALID.value,
                    severity=Severity.WARNING,
                    target=target,
                    params={"kind": coupling.kind.value},
                )
            )
            continue
        pair_claims = {(first.id, edges[0]), (second.id, edges[1])}
        if claimed_edges & pair_claims:
            issues.append(
                ProductIssue(
                    code=IssueCode.COUPLER_EDGE_CONFLICT.value,
                    severity=Severity.WARNING,
                    target=target,
                )
            )
            continue
        claimed_edges |= pair_claims
        sku = coupling.coupler_profile_sku
        article = coupler_articles.get(sku) if sku is not None else None
        if sku is None:
            issues.append(
                ProductIssue(
                    code=IssueCode.COUPLER_PROFILE_MISSING.value,
                    severity=Severity.WARNING,
                    target=target,
                )
            )
            continue
        if article is None:
            issues.append(
                ProductIssue(
                    code=IssueCode.COUPLER_PROFILE_UNKNOWN.value,
                    severity=Severity.WARNING,
                    target=target,
                    params={"sku": sku},
                )
            )
            continue
        if coupling.kind is ConnectionKind.INLINE:
            if first.height_mm != second.height_mm:
                issues.append(
                    ProductIssue(
                        code=IssueCode.COUPLER_HEIGHT_MISMATCH.value,
                        severity=Severity.WARNING,
                        target=target,
                        params={
                            "left_mm": str(first.height_mm),
                            "right_mm": str(second.height_mm),
                        },
                    )
                )
                continue
            span = first.height_mm
        else:
            if first.width_mm != second.width_mm:
                issues.append(
                    ProductIssue(
                        code=IssueCode.COUPLER_WIDTH_MISMATCH.value,
                        severity=Severity.WARNING,
                        target=target,
                        params={
                            "below_mm": str(first.width_mm),
                            "above_mm": str(second.width_mm),
                        },
                    )
                )
                continue
            span = first.width_mm
        coupler_cuts.append(
            ProfileCut(
                sku=article.sku,
                role=ProfileRole.COUPLER,
                material=article.material,
                length_mm=span,
                angle_left=Decimal("90.0"),
                angle_right=Decimal("90.0"),
                qty=1,
                bay_id=coupling.id,
            )
        )
        if article.reinforcement_sku:
            steel_length = reinforcement_cut_length(span, article, 0)
            if steel_length <= Decimal("0"):
                issues.append(
                    ProductIssue(
                        code=IssueCode.COUPLER_REINFORCEMENT_NONPOSITIVE.value,
                        severity=Severity.WARNING,
                        target=target,
                        params={"sku": article.sku},
                    )
                )
            else:
                coupler_reinforcements.append(
                    ReinforcementPiece(
                        parent_profile_sku=article.sku,
                        reinforcement_sku=article.reinforcement_sku,
                        role=ProfileRole.COUPLER,
                        length_mm=steel_length,
                        qty=1,
                        bay_id=coupling.id,
                    )
                )

    bom: EngineResult | None = None
    if aggregated or coupler_cuts:
        bom = EngineResult(
            profile_cuts=[
                cut for r in aggregated for cut in r.profile_cuts
            ]
            + coupler_cuts,
            reinforcements=[
                piece for r in aggregated for piece in r.reinforcements
            ]
            + coupler_reinforcements,
            glasses=[piece for r in aggregated for piece in r.glasses],
            panels=[piece for r in aggregated for piece in r.panels],
            hardware_items=[
                item for r in aggregated for item in r.hardware_items
            ],
            leaf_weights=[
                weight for r in aggregated for weight in r.leaf_weights
            ],
        )

    if any(issue.severity is Severity.ERROR for issue in issues):
        status = ProductStatus.INVALID
    elif issues:
        status = ProductStatus.MANUFACTURING_INCOMPLETE
    else:
        status = ProductStatus.VALID

    return ProductEvaluation(
        status=status,
        issues=issues,
        plan=plan,
        modules=module_evals,
        bom=bom,
    )


# --- Typed commands -------------------------------------------------------
# The only way the UI (and later the agent) mutates a product. Each command
# returns a new ProductModel; undo/redo is a stack of before/after states.


def _bay_node(
    opening: BayOpeningType,
    node_id: str,
    *,
    glass_thickness_mm: Decimal,
    glass_spec: str,
) -> ParametricNode:
    return ParametricNode(
        id=node_id,
        type=NodeType.BAY,
        opening_type=opening,
        glass_thickness_mm=glass_thickness_mm,
        glass_spec=glass_spec,
    )


def make_single_unit(
    *,
    width_mm: Decimal,
    height_mm: Decimal,
    opening: BayOpeningType = BayOpeningType.FIXED,
    glass_thickness_mm: Decimal,
    glass_spec: str,
) -> ProductModel:
    return ProductModel(
        version="product-v2",
        assembly=CoupledAssembly(
            modules=[
                ProductModule(
                    id="m1",
                    width_mm=width_mm,
                    height_mm=height_mm,
                    tree=_bay_node(
                        opening,
                        "m1",
                        glass_thickness_mm=glass_thickness_mm,
                        glass_spec=glass_spec,
                    ),
                )
            ],
            couplings=[],
        ),
    )


def make_bow_assembly(
    *,
    module_count: int,
    width_mm: Decimal,
    height_mm: Decimal,
    angle_deg: Decimal,
    opening: BayOpeningType = BayOpeningType.FIXED,
    glass_thickness_mm: Decimal,
    glass_spec: str,
) -> ProductModel:
    if module_count < 2:
        raise ValueError("A bow assembly requires at least two modules")
    share = (width_mm / module_count).quantize(QUANTUM_MM, rounding=ROUND_HALF_UP)
    modules = [
        ProductModule(
            id=f"m{index}",
            width_mm=share,
            height_mm=height_mm,
            tree=_bay_node(
                opening,
                f"m{index}",
                glass_thickness_mm=glass_thickness_mm,
                glass_spec=glass_spec,
            ),
        )
        for index in range(1, module_count)
    ]
    modules.append(
        ProductModule(
            id=f"m{module_count}",
            width_mm=width_mm - share * (module_count - 1),
            height_mm=height_mm,
            tree=_bay_node(
                opening,
                f"m{module_count}",
                glass_thickness_mm=glass_thickness_mm,
                glass_spec=glass_spec,
            ),
        )
    )
    couplings = [
        CouplingDef(id=f"c{index}", angle_deg=angle_deg)
        for index in range(1, module_count)
    ]
    return ProductModel(
        version="product-v2",
        assembly=CoupledAssembly(modules=modules, couplings=couplings),
    )


def _replace_module(
    product: ProductModel, module_id: str, module: ProductModule
) -> ProductModel:
    modules = [
        module if existing.id == module_id else existing
        for existing in product.assembly.modules
    ]
    return product.model_copy(
        update={"assembly": product.assembly.model_copy(update={"modules": modules})}
    )


def _replace_coupling(
    product: ProductModel, coupling_id: str, coupling: CouplingDef
) -> ProductModel:
    couplings = [
        coupling if existing.id == coupling_id else existing
        for existing in product.assembly.couplings
    ]
    return product.model_copy(
        update={
            "assembly": product.assembly.model_copy(
                update={"couplings": couplings}
            )
        }
    )


def set_module_count(product: ProductModel, module_count: int) -> ProductModel:
    modules = product.assembly.modules
    couplings = product.assembly.couplings
    current = len(modules)
    if module_count < 1:
        raise ValueError("An assembly requires at least one module")
    if module_count == current:
        return product
    if module_count < current:
        return product.model_copy(
            update={
                "assembly": CoupledAssembly(
                    modules=modules[:module_count],
                    couplings=couplings[: module_count - 1],
                )
            }
        )
    last = modules[-1]
    new_modules = list(modules)
    new_couplings = list(couplings)
    default_angle = couplings[-1].angle_deg if couplings else Decimal("15")
    for index in range(current + 1, module_count + 1):
        new_couplings.append(
            CouplingDef(
                id=f"c{index - 1}",
                angle_deg=default_angle,
                coupler_profile_sku=couplings[-1].coupler_profile_sku
                if couplings
                else None,
            )
        )
        new_modules.append(
            ProductModule(
                id=f"m{index}",
                width_mm=last.width_mm,
                height_mm=last.height_mm,
                tree=last.tree,
            )
        )
    return product.model_copy(
        update={
            "assembly": CoupledAssembly(
                modules=new_modules, couplings=new_couplings
            )
        }
    )


def set_module_width(
    product: ProductModel, module_id: str, width_mm: Decimal
) -> ProductModel:
    module = next(m for m in product.assembly.modules if m.id == module_id)
    return _replace_module(
        product, module_id, module.model_copy(update={"width_mm": width_mm})
    )


def set_module_height(
    product: ProductModel, module_id: str, height_mm: Decimal
) -> ProductModel:
    module = next(m for m in product.assembly.modules if m.id == module_id)
    return _replace_module(
        product, module_id, module.model_copy(update={"height_mm": height_mm})
    )


def equalize_module_widths(product: ProductModel) -> ProductModel:
    modules = product.assembly.modules
    total = sum((m.width_mm for m in modules), Decimal("0"))
    share = (total / len(modules)).quantize(QUANTUM_MM, rounding=ROUND_HALF_UP)
    new_modules = [
        m.model_copy(update={"width_mm": share}) for m in modules[:-1]
    ]
    new_modules.append(
        modules[-1].model_copy(
            update={"width_mm": total - share * (len(modules) - 1)}
        )
    )
    return product.model_copy(
        update={
            "assembly": product.assembly.model_copy(
                update={"modules": new_modules}
            )
        }
    )


def set_coupling_angle(
    product: ProductModel, coupling_id: str, angle_deg: Decimal
) -> ProductModel:
    coupling = next(
        c for c in product.assembly.couplings if c.id == coupling_id
    )
    return _replace_coupling(
        product, coupling_id, coupling.model_copy(update={"angle_deg": angle_deg})
    )


def equalize_coupling_angles(
    product: ProductModel, angle_deg: Decimal | None = None
) -> ProductModel:
    couplings = product.assembly.couplings
    if not couplings:
        return product
    angle = angle_deg if angle_deg is not None else couplings[0].angle_deg
    return product.model_copy(
        update={
            "assembly": product.assembly.model_copy(
                update={
                    "couplings": [
                        c.model_copy(update={"angle_deg": angle})
                        for c in couplings
                    ]
                }
            )
        }
    )


def set_coupler_sku(
    product: ProductModel, coupling_id: str, sku: str | None
) -> ProductModel:
    coupling = next(
        c for c in product.assembly.couplings if c.id == coupling_id
    )
    return _replace_coupling(
        product,
        coupling_id,
        coupling.model_copy(update={"coupler_profile_sku": sku}),
    )


def _with_opening(node: ParametricNode, opening: BayOpeningType) -> ParametricNode:
    if node.type is NodeType.BAY:
        return node.model_copy(update={"opening_type": opening})
    return node.model_copy(
        update={
            "children": [_with_opening(child, opening) for child in node.children]
        }
    )


def set_module_opening(
    product: ProductModel, module_id: str, opening: BayOpeningType
) -> ProductModel:
    module = next(m for m in product.assembly.modules if m.id == module_id)
    tree = module.tree
    if tree.type is NodeType.ROOT and len(tree.children) == 1:
        tree = tree.model_copy(
            update={"children": [_with_opening(tree.children[0], opening)]}
        )
    else:
        tree = _with_opening(tree, opening)
    return _replace_module(
        product, module_id, module.model_copy(update={"tree": tree})
    )


def set_module_tree(
    product: ProductModel, module_id: str, tree: ParametricNode
) -> ProductModel:
    module = next(m for m in product.assembly.modules if m.id == module_id)
    return _replace_module(
        product, module_id, module.model_copy(update={"tree": tree})
    )


# --- Queries --------------------------------------------------------------


def module_ids(product: ProductModel) -> list[str]:
    return [m.id for m in product.assembly.modules]


def coupling_ids(product: ProductModel) -> list[str]:
    return [c.id for c in product.assembly.couplings]


def nominal_width_mm(product: ProductModel) -> Decimal:
    return sum((m.width_mm for m in product.assembly.modules), Decimal("0"))


def nominal_height_mm(product: ProductModel) -> Decimal:
    return max(m.height_mm for m in product.assembly.modules)
