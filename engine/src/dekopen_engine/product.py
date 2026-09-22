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

from dekopen_engine.geometry import calculate_geometry
from dekopen_engine.models import (
    BayOpeningType,
    EffectiveProfileArticle,
    EngineModel,
    EngineResult,
    NodeType,
    ParametricNode,
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


class CouplingDef(EngineModel):
    """Angled joint between two adjacent modules.

    `angle_deg` is the signed deflection of the front chain at the joint:
    positive turns the next module counterclockwise (plan view). Zero is a
    coplanar coupling.
    """

    id: str
    angle_deg: Decimal
    coupler_profile_sku: str | None = None


class ProductModule(EngineModel):
    id: str
    width_mm: Decimal = Field(gt=0)
    height_mm: Decimal = Field(gt=0)
    tree: ParametricNode


class CoupledAssembly(EngineModel):
    modules: list[ProductModule] = Field(min_length=1)
    couplings: list[CouplingDef] = Field(default_factory=list)


class ProductModel(EngineModel):
    version: Literal["product-v2"]
    assembly: CoupledAssembly


class PlanPoint(EngineModel):
    x_mm: Decimal
    y_mm: Decimal


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

    front: list[PlanPoint] = [PlanPoint(x_mm=Decimal(0), y_mm=Decimal(0))]
    normals: list[PlanPoint] = []
    plan_modules: list[PlanModule] = []
    plan_couplings: list[PlanCoupling] = []
    all_points: list[PlanPoint] = []

    for index, module in enumerate(modules):
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
        plan_modules.append(
            PlanModule(
                module_id=module.id,
                corners=[start, end, back_end, back_start],
            )
        )
        all_points.extend([start, end, back_start, back_end])

        if index < len(modules) - 1 and index < len(couplings):
            coupling = couplings[index]
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
                            "first": modules[i].id,
                            "second": modules[j].id,
                        },
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
            piece.model_copy(update={"bay_id": bay(piece.bay_id)})
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

    if len(couplings) != len(modules) - 1:
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
            result = calculate_geometry(
                _top_with_module_dims(module), params, is_foiled=is_foiled
            )
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
    for index, coupling in enumerate(couplings[: len(modules) - 1]):
        left = modules[index]
        right = modules[index + 1]
        sku = coupling.coupler_profile_sku
        article = coupler_articles.get(sku) if sku is not None else None
        if sku is None:
            issues.append(
                ProductIssue(
                    code=IssueCode.COUPLER_PROFILE_MISSING.value,
                    severity=Severity.WARNING,
                    target=f"coupling:{coupling.id}",
                )
            )
            continue
        if article is None:
            issues.append(
                ProductIssue(
                    code=IssueCode.COUPLER_PROFILE_UNKNOWN.value,
                    severity=Severity.WARNING,
                    target=f"coupling:{coupling.id}",
                    params={"sku": sku},
                )
            )
            continue
        if left.height_mm != right.height_mm:
            issues.append(
                ProductIssue(
                    code=IssueCode.COUPLER_HEIGHT_MISMATCH.value,
                    severity=Severity.WARNING,
                    target=f"coupling:{coupling.id}",
                    params={
                        "left_mm": str(left.height_mm),
                        "right_mm": str(right.height_mm),
                    },
                )
            )
            continue
        height = left.height_mm
        coupler_cuts.append(
            ProfileCut(
                sku=article.sku,
                role=ProfileRole.COUPLER,
                material=article.material,
                length_mm=height,
                angle_left=Decimal("90"),
                angle_right=Decimal("90"),
                qty=1,
                bay_id=coupling.id,
            )
        )
        if article.reinforcement_sku:
            coupler_reinforcements.append(
                ReinforcementPiece(
                    parent_profile_sku=article.sku,
                    reinforcement_sku=article.reinforcement_sku,
                    role=ProfileRole.COUPLER,
                    length_mm=height,
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
