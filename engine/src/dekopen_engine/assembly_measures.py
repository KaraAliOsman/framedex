"""Exact assembly dimensions and developed/projected drawing placements."""

from decimal import Decimal, ROUND_HALF_UP, localcontext
from typing import TYPE_CHECKING

from dekopen_engine.models import EngineModel, EffectiveProfileArticle, PlanPoint

if TYPE_CHECKING:
    from dekopen_engine.product import CoupledAssembly, PlanGeometry, ElevationLayout

D = Decimal


class AssemblyModuleMeasure(EngineModel):
    module_id: str
    width_mm: Decimal
    height_mm: Decimal
    developed_x_mm: Decimal
    sill_mm: Decimal
    projected_x_mm: Decimal
    projected_width_mm: Decimal


class AssemblyMeasure(EngineModel):
    developed_width_mm: Decimal
    front_width_mm: Decimal
    projection_mm: Decimal
    height_mm: Decimal
    coupling_width_mm: Decimal
    modules: list[AssemblyModuleMeasure]
    source: str


def developed_layout(assembly: "CoupledAssembly", measures: AssemblyMeasure | None) -> "ElevationLayout":
    """Apply engine placements to the shared elevation, including net gaps."""
    from dekopen_engine.product import elevation_layout, _resolved_pairs, _resolve_stack_roots, _stack_parents
    layout = elevation_layout(assembly)
    if measures is None:
        return layout
    by_id = {item.module_id: item for item in measures.modules}
    for member in layout.members:
        fact = by_id[member.module_id]
        member.x_mm, member.sill_mm = fact.developed_x_mm, fact.sill_mm
    pairs = _resolved_pairs(assembly.modules, assembly.couplings)
    roots = _resolve_stack_roots(assembly.modules, pairs)
    columns = [module.id for module in assembly.modules if module.id not in roots]
    members = {member.module_id: member for member in layout.members}
    def column_top(root: str) -> Decimal:
        return max(member.sill_mm + member.height_mm for member in layout.members
                   if roots.get(member.module_id, member.module_id) == root)
    for index, joint in enumerate(layout.column_joints):
        left, right = members[columns[index]], members[columns[index + 1]]
        joint.x_mm = (left.x_mm + left.width_mm + right.x_mm) / D(2)
        joint.top_mm = min(column_top(left.module_id), column_top(right.module_id))
    parents = _stack_parents(pairs)
    for stack_joint in layout.stack_joints:
        pair = next(pair for coupling, pair in pairs if coupling.id == stack_joint.coupling_id)
        child = next(module for module in pair if parents.get(module) in pair)
        upper, lower = members[child], members[parents[child]]
        stack_joint.x_mm = upper.x_mm
        stack_joint.y_mm = (upper.sill_mm + lower.sill_mm + lower.height_mm) / D(2)
    return layout


def assembly_measures(assembly: "CoupledAssembly", plan: "PlanGeometry",
                      articles: dict[str, EffectiveProfileArticle]) -> AssemblyMeasure | None:
    """No authority is inferred from an SKU, saw angle, or face width.

    Historical joints without this optional authority retain their original
    evaluation bytes. New measurements use only sourced front-axis widths.
    The chord joins the first and last front endpoints; projection is the
    maximum perpendicular excursion of the front chain from that chord.
    """
    from dekopen_engine.product import ConnectionKind, _resolved_pairs, _resolve_stack_roots, _stack_parents, elevation_layout
    if not assembly.couplings:
        return None
    rules = {}
    for joint in assembly.couplings:
        article = articles.get(joint.coupler_profile_sku or "")
        if article is None or article.coupling_rule is None:
            return None
        rules[joint.id] = article.coupling_rule
    layout = elevation_layout(assembly)
    pairs = _resolved_pairs(assembly.modules, assembly.couplings)
    roots = _resolve_stack_roots(assembly.modules, pairs)
    parents = _stack_parents(pairs)
    stack_gaps = {}
    for joint, pair in pairs:
        if joint.kind is ConnectionKind.STACKED:
            child = next((module for module in pair if parents.get(module) in pair), None)
            if child is not None:
                stack_gaps[child] = rules[joint.id].development_mm
    def stack_shift(module_id: str) -> Decimal:
        shift = D(0)
        while module_id in parents:
            shift += stack_gaps.get(module_id, D(0))
            module_id = parents[module_id]
        return shift
    inline = [(joint, pair) for joint, pair in pairs if joint.kind is ConnectionKind.INLINE]
    # A joint contributes once, to the space before its right-hand column.
    root_order = [module.id for module in assembly.modules if module.id not in roots]
    gaps = {root: D(0) for root in root_order}
    for joint, pair in inline:
        endpoints = [roots.get(module, module) for module in pair]
        right = max(endpoints, key=root_order.index)
        gaps[right] += rules[joint.id].development_mm
    shifts = {}
    shift = D(0)
    for root in root_order:
        shift += gaps[root]
        shifts[root] = shift
    footprints = {module.module_id: module.corners for module in plan.modules}
    first, last = plan.front_chain[0], plan.front_chain[-1]
    with localcontext() as context:
        context.prec = 50
        dx, dy = last.x_mm-first.x_mm, last.y_mm-first.y_mm
        chord = (dx*dx+dy*dy).sqrt()
        if chord == 0:
            return None
        def q(value: Decimal) -> Decimal:
            return value.quantize(D("0.01"), rounding=ROUND_HALF_UP)
        def along(point: PlanPoint) -> Decimal:
            return ((point.x_mm-first.x_mm)*dx+(point.y_mm-first.y_mm)*dy)/chord
        projected = {key: (along(points[0]), along(points[1])) for key, points in footprints.items()}
        projection = max(abs((p.x_mm-first.x_mm)*dy-(p.y_mm-first.y_mm)*dx)/chord for p in plan.front_chain)
        by_id = {module.id: module for module in assembly.modules}
        members = [AssemblyModuleMeasure(module_id=member.module_id,
            width_mm=by_id[member.module_id].width_mm, height_mm=member.height_mm,
            developed_x_mm=member.x_mm+shifts[roots.get(member.module_id, member.module_id)],
            sill_mm=member.sill_mm+stack_shift(member.module_id), projected_x_mm=q(min(projected[member.module_id])),
            projected_width_mm=q(abs(projected[member.module_id][1]-projected[member.module_id][0])))
            for member in layout.members]
        joint_width = sum(gaps.values(), D(0))
        width = max(member.developed_x_mm+member.width_mm for member in members)-min(member.developed_x_mm for member in members)
        height = max(member.sill_mm+member.height_mm for member in members)-min(member.sill_mm for member in members)
        return AssemblyMeasure(developed_width_mm=q(width), front_width_mm=q(chord),
            projection_mm=q(projection), height_mm=q(height), coupling_width_mm=q(joint_width), modules=members,
            source="Motor geométrico; suma desarrollada con acoples declarados; cuerda y salida perpendicular de la cadena frontal.")
