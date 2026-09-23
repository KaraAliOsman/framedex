import type { IntentNode, Opening, SlidingLayout, SplitType } from "./intentEditing";
import { SLIDING_PRESETS } from "./intentEditing";
import { intentBays, moveDivision, splitBay, walkIntent } from "./intentEditing";
import type { MemberGeometry } from "./members";
import { FALLBACK_MEMBERS, resolveMembers } from "./members";

/** Compositional product model (product-v2) — modules joined by couplings.
 *
 * Mirrors dekopen_engine.product: a ProductJson is the JSON form of the
 * engine's ProductModel. Every mutator returns a NEW object so edits can be
 * recorded as undo history entries and validated by the engine afterwards.
 */

export type CouplingJson = {
  id: string;
  angle_deg: string;
  coupler_profile_sku: string | null;
  /** Structural class of the joint — absent means the inline chain default. */
  kind?: "INLINE" | "STACKED" | "TEE" | "CORNER";
  /** Explicit endpoints: modules[i]'s edges[i] side meets modules[j]'s
   * edges[j] side. Absent = legacy positional binding (i right, i+1 left). */
  modules?: [string, string];
  edges?: ["left" | "right" | "top" | "bottom", "left" | "right" | "top" | "bottom"];
};

/** Closed elevation outline of a module — mirrors dekopen_engine.contour.
 * vertices[i] → vertices[i+1] is edge i; bulges[i] is its signed sagitta
 * (positive bulges right of the directed edge = outward on a CCW loop).
 * Module-local mm, y-up, CCW; the canvas flips y when drawing. */
export type ContourJson = {
  vertices: { x_mm: string; y_mm: string }[];
  bulges: (string | null)[];
};

export type ProductModuleJson = {
  id: string;
  width_mm: string;
  height_mm: string;
  tree: IntentNode;
  /** Present only on non-rectangular modules; width/height stay the bbox. */
  contour?: ContourJson;
};

export type ProductJson = {
  version: "product-v2";
  assembly: {
    modules: ProductModuleJson[];
    couplings: CouplingJson[];
  };
};

export function isProductModel(value: unknown): value is ProductJson {
  return (
    typeof value === "object" &&
    value !== null &&
    (value as { version?: unknown }).version === "product-v2" &&
    typeof (value as { assembly?: { modules?: unknown } }).assembly === "object" &&
    Array.isArray((value as { assembly: { modules?: unknown } }).assembly.modules)
  );
}

export function makeTrapezoidModule(
  id: string,
  widthMm: string,
  heightMm: string,
  offsetLeftMm: number,
  offsetRightMm: number,
  tree: IntentNode,
): ProductModuleJson {
  const w = Number(widthMm);
  const h = Number(heightMm);
  return {
    id,
    width_mm: widthMm,
    height_mm: heightMm,
    contour: {
      vertices: [
        { x_mm: "0", y_mm: "0" },
        { x_mm: w.toFixed(2), y_mm: "0" },
        { x_mm: (w - offsetRightMm).toFixed(2), y_mm: h.toFixed(2) },
        { x_mm: offsetLeftMm.toFixed(2), y_mm: h.toFixed(2) },
      ],
      bulges: [null, null, null, null],
    },
    tree,
  };
}

export function makeArchModule(
  id: string,
  widthMm: string,
  heightMm: string,
  riseMm: number,
  tree: IntentNode,
): ProductModuleJson {
  const w = Number(widthMm);
  const h = Number(heightMm);
  return {
    id,
    width_mm: widthMm,
    height_mm: heightMm,
    contour: {
      vertices: [
        { x_mm: "0", y_mm: "0" },
        { x_mm: w.toFixed(2), y_mm: "0" },
        { x_mm: w.toFixed(2), y_mm: h.toFixed(2) },
        { x_mm: "0", y_mm: h.toFixed(2) },
      ],
      bulges: [null, null, riseMm.toFixed(2), null],
    },
    tree,
  };
}

export function makeBayTree(
  id: string,
  opening: Opening,
  glassThicknessMm: string,
  glassSpec: string,
  glassArticleSku: string | null = null,
): IntentNode {
  return {
    id,
    type: "BAY",
    opening_type: opening,
    glass_thickness_mm: glassThicknessMm,
    glass_spec: glassSpec,
    glass_article_sku: glassArticleSku,
  };
}

export function makeBowProduct(options: {
  moduleCount: number;
  widthMm: number;
  heightMm: number;
  angleDeg: number;
  opening?: Opening;
  glassThicknessMm?: string;
  glassSpec?: string;
  glassArticleSku?: string | null;
}): ProductJson {
  const {
    moduleCount,
    widthMm,
    heightMm,
    angleDeg,
    opening = "FIXED",
    glassThicknessMm = "4.00",
    glassSpec = "4",
    glassArticleSku = null,
  } = options;
  const share = Math.floor((widthMm / moduleCount) * 100) / 100;
  const modules: ProductModuleJson[] = [];
  const couplings: CouplingJson[] = [];
  let remaining = widthMm;
  for (let index = 1; index <= moduleCount; index += 1) {
    const width = index === moduleCount ? remaining : share;
    remaining -= width;
    modules.push({
      id: `m${index}`,
      width_mm: width.toFixed(2),
      height_mm: heightMm.toFixed(2),
      tree: makeBayTree(`m${index}`, opening, glassThicknessMm, glassSpec, glassArticleSku),
    });
    if (index > 1) {
      couplings.push({
        id: `c${index - 1}`,
        angle_deg: angleDeg.toFixed(1),
        coupler_profile_sku: null,
      });
    }
  }
  return { version: "product-v2", assembly: { modules, couplings } };
}

export function totalModuleWidth(product: ProductJson): number {
  return product.assembly.modules.reduce((total, module) => total + Number(module.width_mm), 0);
}

/** The nominal front-elevation envelope — mirrors the engine's
 * `elevation_envelope` exactly: stacked members project into their root
 * column, so width sums across columns only and height is the tallest
 * column's stacked sum. Nominal dims are a contract between this request
 * body and the server's validation — keep the resolution rules identical. */
interface ResolvedPair {
  coupling: ProductJson["assembly"]["couplings"][number];
  pair: readonly [string, string];
}

export interface StackResolution {
  /** Every coupling with its resolved module pair (explicit ids, else the
   * positional index→index+1 binding). */
  pairs: ResolvedPair[];
  /** Stacked member id → the partner it hangs over. */
  stackParent: Map<string, string>;
  /** Stacked member id → its root column id. */
  stackRoot: Map<string, string>;
}

/** Resolved stack graph of an assembly — shared by the envelope, the front
 * layout and any consumer that must agree with the engine's rules. */
export function resolveStacks(product: ProductJson): StackResolution {
  const modules = product.assembly.modules;
  const pairs = product.assembly.couplings.flatMap((coupling, index) => {
    const pair =
      coupling.modules ??
      (index < modules.length - 1 && modules[index] && modules[index + 1]
        ? ([modules[index]!.id, modules[index + 1]!.id] as const)
        : undefined);
    return pair !== undefined && pair.length === 2 ? [{ coupling, pair }] : [];
  });
  const stackParent = new Map<string, string>();
  for (const { coupling, pair } of pairs) {
    if (coupling.kind !== "STACKED") continue;
    const edges = coupling.edges ?? ["top", "bottom"];
    if (edges.length !== 2) continue;
    const topIndex = edges[0] === "top" ? 0 : edges[1] === "top" ? 1 : -1;
    if (topIndex === 0 || topIndex === 1) {
      stackParent.set(pair[(1 - topIndex) as 0 | 1]!, pair[topIndex as 0 | 1]!);
    }
  }
  const moduleIds = new Set(modules.map((module) => module.id));
  const stackRoot = new Map<string, string>();
  for (const member of stackParent.keys()) {
    const seen = new Set<string>();
    let current = member;
    while (stackParent.has(current) && !seen.has(current)) {
      seen.add(current);
      current = stackParent.get(current) as string;
    }
    const anchor = stackParent.has(current) ? undefined : current;
    if (anchor !== undefined && moduleIds.has(anchor)) stackRoot.set(member, anchor);
  }
  return { pairs, stackParent, stackRoot };
}

export function elevationEnvelopeMm(product: ProductJson): { width: number; height: number } {
  const modules = product.assembly.modules;
  const { stackRoot } = resolveStacks(product);
  let width = 0;
  const columns = new Map<string, number>();
  for (const module of modules) {
    const root = stackRoot.get(module.id) ?? module.id;
    if (!stackRoot.has(module.id)) width += Number(module.width_mm);
    columns.set(root, (columns.get(root) ?? 0) + Number(module.height_mm));
  }
  return { width, height: columns.size > 0 ? Math.max(...columns.values()) : 0 };
}

function replaceModule(
  product: ProductJson,
  moduleId: string,
  module: ProductModuleJson,
): ProductJson {
  return {
    ...product,
    assembly: {
      ...product.assembly,
      modules: product.assembly.modules.map((existing) =>
        existing.id === moduleId ? module : existing,
      ),
    },
  };
}

function replaceCoupling(
  product: ProductJson,
  couplingId: string,
  coupling: CouplingJson,
): ProductJson {
  return {
    ...product,
    assembly: {
      ...product.assembly,
      couplings: product.assembly.couplings.map((existing) =>
        existing.id === couplingId ? coupling : existing,
      ),
    },
  };
}

/** Next free module/coupling id — survives removals without collisions. */
export function nextModuleId(product: ProductJson): string {
  const used = new Set(product.assembly.modules.map((module) => module.id));
  let index = product.assembly.modules.length + 1;
  while (used.has(`m${index}`)) index += 1;
  return `m${index}`;
}

export function nextCouplingId(product: ProductJson): string {
  const used = new Set(product.assembly.couplings.map((coupling) => coupling.id));
  let index = product.assembly.couplings.length + 1;
  while (used.has(`c${index}`)) index += 1;
  return `c${index}`;
}

function cloneTree(node: IntentNode): IntentNode {
  return { ...node, children: node.children?.map(cloneTree) };
}

/** Direct-composition grow: attach a compatible unit on the left/right edge.
 *
 * Inherits the edge module's height and bay structure (same opening, glass,
 * panel), a reasonable default width, and a coupling whose angle/coupler
 * inherit the outermost existing joint — or straight (0°) for the first one.
 */
export function addAdjacentUnit(
  product: ProductJson,
  side: "left" | "right",
  defaults: { widthMm?: string } = {},
): ProductJson {
  const { modules, couplings } = product.assembly;
  const edge = side === "right" ? modules.at(-1) : modules[0];
  if (!edge) return product;
  const outerCoupling = side === "right" ? couplings.at(-1) : couplings[0];
  const module: ProductModuleJson = {
    id: nextModuleId(product),
    width_mm: defaults.widthMm ?? edge.width_mm,
    height_mm: edge.height_mm,
    tree: cloneTree(edge.tree),
  };
  const coupling: CouplingJson = {
    id: nextCouplingId(product),
    angle_deg: outerCoupling?.angle_deg ?? "0.0",
    coupler_profile_sku: outerCoupling?.coupler_profile_sku ?? null,
  };
  return {
    ...product,
    assembly:
      side === "right"
        ? { modules: [...modules, module], couplings: [...couplings, coupling] }
        : { modules: [module, ...modules], couplings: [coupling, ...couplings] },
  };
}

/** Remove a unit and heal the chain: when an interior module leaves, its two
 * neighboring modules re-join with a merged deflection (c_left + c_right) so
 * downstream modules keep their absolute orientation. */
export function removeUnit(product: ProductJson, moduleId: string): ProductJson {
  const { modules, couplings } = product.assembly;
  const index = modules.findIndex((module) => module.id === moduleId);
  if (index === -1 || modules.length === 1) return product;
  const nextModules = modules.filter((_, position) => position !== index);
  const nextCouplings = couplings.filter(
    (_, position) => position !== index && position !== index - 1,
  );
  if (index > 0 && index < modules.length - 1) {
    const merged = Number(couplings[index - 1]!.angle_deg) + Number(couplings[index]!.angle_deg);
    nextCouplings.splice(index - 1, 0, {
      ...couplings[index - 1]!,
      angle_deg: merged.toFixed(1),
    });
  }
  return {
    ...product,
    assembly: { modules: nextModules, couplings: nextCouplings },
  };
}

/** Wrap a classic parametric tree as a degenerate one-module product so the
 * compositional editor can edit legacy positions without a mode switch. */
export function wrapTreeAsProduct(
  tree: IntentNode,
  widthMm: string,
  heightMm: string,
): ProductJson {
  return {
    version: "product-v2",
    assembly: {
      modules: [{ id: "m1", width_mm: widthMm, height_mm: heightMm, tree }],
      couplings: [],
    },
  };
}

/** True when the product is a single uncoupled unit — i.e. it can persist in
 * the classic design shape (which keeps the documentary/quotation path).
 * A contoured module stays on the product-v2 path: the classic shape has
 * nowhere to carry its outline. */
export function isSingleUnit(product: ProductJson): boolean {
  return (
    product.assembly.modules.length === 1 &&
    product.assembly.couplings.length === 0 &&
    !product.assembly.modules[0]!.contour
  );
}

/** Set the same deflection on every joint — "Distribuir arco" with an exact value. */
export function setAllCouplingAngles(product: ProductJson, angleDeg: string): ProductJson {
  return {
    ...product,
    assembly: {
      ...product.assembly,
      couplings: product.assembly.couplings.map((coupling) => ({
        ...coupling,
        angle_deg: angleDeg,
      })),
    },
  };
}

export function setModuleCount(product: ProductJson, moduleCount: number): ProductJson {
  const { modules, couplings } = product.assembly;
  const current = modules.length;
  if (moduleCount < 1 || moduleCount === current) return product;
  if (moduleCount < current) {
    return {
      ...product,
      assembly: {
        modules: modules.slice(0, moduleCount),
        couplings: couplings.slice(0, moduleCount - 1),
      },
    };
  }
  const last = modules.at(-1);
  if (!last) return product;
  const lastCoupling = couplings.at(-1);
  const lastAngle = lastCoupling?.angle_deg ?? "15.0";
  const lastSku = lastCoupling?.coupler_profile_sku ?? null;
  const nextModules = [...modules];
  const nextCouplings = [...couplings];
  for (let index = current + 1; index <= moduleCount; index += 1) {
    const growing: ProductJson = {
      ...product,
      assembly: { modules: nextModules, couplings: nextCouplings },
    };
    nextCouplings.push({
      id: nextCouplingId(growing),
      angle_deg: lastAngle,
      coupler_profile_sku: lastSku,
    });
    nextModules.push({ ...last, id: nextModuleId(growing) });
  }
  return {
    ...product,
    assembly: { modules: nextModules, couplings: nextCouplings },
  };
}

/** Rescale a contour to a new bounding box — x and y scale independently.
 * An arc cannot stay circular under unequal scaling, so each edge's sagitta
 * rescales by the perpendicular component of the scale to its chord: the
 * rebuilt arc keeps the intended rise relative to the new outline (an arch
 * keeps its flecha; a bowed side wall keeps its lateral bow). */
export function scaledContour(
  contour: ContourJson,
  widthMm: string,
  heightMm: string,
): ContourJson {
  const xs = contour.vertices.map((v) => Number(v.x_mm));
  const ys = contour.vertices.map((v) => Number(v.y_mm));
  const bw = Math.max(...xs) - Math.min(...xs);
  const bh = Math.max(...ys) - Math.min(...ys);
  const sx = Number(widthMm) / (bw || 1);
  const sy = Number(heightMm) / (bh || 1);
  const minX = Math.min(...xs);
  const minY = Math.min(...ys);
  const n = contour.vertices.length;
  return {
    vertices: contour.vertices.map((v) => ({
      x_mm: ((Number(v.x_mm) - minX) * sx).toFixed(2),
      y_mm: ((Number(v.y_mm) - minY) * sy).toFixed(2),
    })),
    bulges: contour.bulges.map((b, i) => {
      if (b === null || b === undefined) return null;
      const a = contour.vertices[i]!;
      const c = contour.vertices[(i + 1) % n]!;
      const dx = Number(c.x_mm) - Number(a.x_mm);
      const dy = Number(c.y_mm) - Number(a.y_mm);
      const len = Math.hypot(dx, dy) || 1;
      // unit normal of the chord, scaled: |(-dy,dx)/len ⊙ (sx,sy)|
      const factor = Math.hypot((-dy / len) * sx, (dx / len) * sy);
      return (Number(b) * factor).toFixed(2);
    }),
  };
}

export function setModuleWidth(
  product: ProductJson,
  moduleId: string,
  widthMm: string,
): ProductJson {
  const module = product.assembly.modules.find((item) => item.id === moduleId);
  if (!module) return product;
  return replaceModule(product, moduleId, {
    ...module,
    width_mm: widthMm,
    ...(module.contour
      ? { contour: scaledContour(module.contour, widthMm, module.height_mm) }
      : {}),
  });
}

/** Minimum width a module may be dragged to — below this the geometry is
 * meaningless for any catalog (engine minimums sit higher, ~400mm). */
export const MIN_MODULE_WIDTH_MM = 150;

/** Drag a column seam: the left column's root grows by `deltaMm`, the right
 * column's root shrinks by the same amount, so the overall width is
 * preserved — stacked members keep their own declared widths. Both sides
 * are clamped to MIN_MODULE_WIDTH_MM; returns the unchanged product when the
 * seam doesn't exist or would cross a minimum. */
export function resizeModuleSeam(
  product: ProductJson,
  seamIndex: number,
  deltaMm: number,
): ProductJson {
  const modules = product.assembly.modules;
  const { stackRoot } = resolveStacks(product);
  const columns = modules.filter((module) => !stackRoot.has(module.id));
  const left = columns[seamIndex];
  const right = columns[seamIndex + 1];
  if (!left || !right || !Number.isFinite(deltaMm)) return product;
  const leftMm = Number(left.width_mm) + deltaMm;
  const rightMm = Number(right.width_mm) - deltaMm;
  if (leftMm < MIN_MODULE_WIDTH_MM || rightMm < MIN_MODULE_WIDTH_MM) return product;
  const nextModules = modules.map((module) =>
    module.id === left.id
      ? {
          ...module,
          width_mm: leftMm.toFixed(2),
          ...(module.contour
            ? { contour: scaledContour(module.contour, leftMm.toFixed(2), module.height_mm) }
            : {}),
        }
      : module.id === right.id
        ? {
            ...module,
            width_mm: rightMm.toFixed(2),
            ...(module.contour
              ? { contour: scaledContour(module.contour, rightMm.toFixed(2), module.height_mm) }
              : {}),
          }
        : module,
  );
  return { ...product, assembly: { ...product.assembly, modules: nextModules } };
}

/** Drag an interior divider (mullion/travesaño) to a new offset. */
export function moveModuleDivision(
  product: ProductJson,
  moduleId: string,
  divisionId: string,
  offsetMm: string,
): ProductJson {
  const module = product.assembly.modules.find((item) => item.id === moduleId);
  if (!module) return product;
  try {
    const tree = moveDivision(
      module.tree.type === "ROOT" ? (module.tree.children?.[0] ?? module.tree) : module.tree,
      divisionId,
      offsetMm,
    );
    return replaceModule(product, moduleId, {
      ...module,
      tree: module.tree.type === "ROOT" ? { ...module.tree, children: [tree] } : tree,
    });
  } catch {
    return product;
  }
}

/** Indices of the two top corners (y ≈ maxY, ordered left→right) of a
 * contour whose upper bound is a straight or arched chord — trapezoid and
 * arch starters both qualify. Null for degenerate or free-form outlines. */
export function contourTopCorners(
  contour: ContourJson,
): { leftIndex: number; rightIndex: number } | null {
  const ys = contour.vertices.map((v) => Number(v.y_mm));
  const maxY = Math.max(...ys);
  const top = ys.flatMap((y, index) => (Math.abs(y - maxY) < 0.51 ? [index] : []));
  if (top.length !== 2) return null;
  const [first, second] = top as [number, number];
  return Number(contour.vertices[first]!.x_mm) <= Number(contour.vertices[second]!.x_mm)
    ? { leftIndex: first, rightIndex: second }
    : { leftIndex: second, rightIndex: first };
}

export function setContourVertex(
  product: ProductJson,
  moduleId: string,
  vertexIndex: number,
  xMm: string,
  yMm: string,
): ProductJson {
  const module = product.assembly.modules.find((item) => item.id === moduleId);
  if (!module?.contour) return product;
  const vertices = module.contour.vertices.map((vertex, index) =>
    index === vertexIndex ? { x_mm: xMm, y_mm: yMm } : vertex,
  );
  return replaceModule(product, moduleId, {
    ...module,
    contour: { ...module.contour, vertices },
  });
}

export function setContourBulge(
  product: ProductJson,
  moduleId: string,
  edgeIndex: number,
  sagittaMm: string | null,
): ProductJson {
  const module = product.assembly.modules.find((item) => item.id === moduleId);
  if (!module?.contour) return product;
  const bulges = module.contour.bulges.map((bulge, index) =>
    index === edgeIndex ? sagittaMm : bulge,
  );
  return replaceModule(product, moduleId, {
    ...module,
    contour: { ...module.contour, bulges },
  });
}

export function setAllModuleHeights(product: ProductJson, heightMm: string): ProductJson {
  return {
    ...product,
    assembly: {
      ...product.assembly,
      modules: product.assembly.modules.map((module) => ({
        ...module,
        height_mm: heightMm,
        ...(module.contour
          ? { contour: scaledContour(module.contour, module.width_mm, heightMm) }
          : {}),
      })),
    },
  };
}

export function equalizeModuleWidths(product: ProductJson): ProductJson {
  const modules = product.assembly.modules;
  const total = totalModuleWidth(product);
  const share = Math.round((total / modules.length) * 100) / 100;
  const nextModules = modules.map((module, index) => {
    const widthMm =
      index === modules.length - 1
        ? (total - share * (modules.length - 1)).toFixed(2)
        : share.toFixed(2);
    return {
      ...module,
      width_mm: widthMm,
      ...(module.contour
        ? { contour: scaledContour(module.contour, widthMm, module.height_mm) }
        : {}),
    };
  });
  return { ...product, assembly: { ...product.assembly, modules: nextModules } };
}

export function scaleModuleWidths(product: ProductJson, totalMm: string): ProductJson {
  const modules = product.assembly.modules;
  const totalCents = Math.round(Number(totalMm) * 100);
  const currentCents = Math.round(totalModuleWidth(product) * 100);
  // Every module must stay ≥0.01 mm or the product fails engine validation.
  if (!Number.isFinite(totalCents) || totalCents < modules.length || currentCents <= 0)
    return product;
  // Integer-hundredth allocation: 1 cent baseline each, remaining cents
  // distributed proportionally by largest remainder so shares never hit zero.
  const extra = totalCents - modules.length;
  const currentTotal = totalModuleWidth(product);
  const exact = modules.map((module) => (Number(module.width_mm) * extra) / currentTotal);
  const shares = exact.map(Math.floor);
  let remainder = extra - shares.reduce((sum, share) => sum + share, 0);
  const order = modules
    .map((_, index) => index)
    .sort((a, b) => exact[b]! - shares[b]! - (exact[a]! - shares[a]!));
  for (const index of order) {
    if (remainder <= 0) break;
    shares[index]! += 1;
    remainder -= 1;
  }
  const nextModules = modules.map((module, index) => {
    const widthMm = ((1 + shares[index]!) / 100).toFixed(2);
    return {
      ...module,
      width_mm: widthMm,
      ...(module.contour
        ? { contour: scaledContour(module.contour, widthMm, module.height_mm) }
        : {}),
    };
  });
  return { ...product, assembly: { ...product.assembly, modules: nextModules } };
}

export function setCouplingAngle(
  product: ProductJson,
  couplingId: string,
  angleDeg: string,
): ProductJson {
  const coupling = product.assembly.couplings.find((item) => item.id === couplingId);
  if (!coupling) return product;
  return replaceCoupling(product, couplingId, {
    ...coupling,
    angle_deg: angleDeg,
  });
}

export function equalizeCouplingAngles(product: ProductJson): ProductJson {
  const couplings = product.assembly.couplings;
  const angle = couplings.at(0)?.angle_deg;
  if (angle === undefined) return product;
  return {
    ...product,
    assembly: {
      ...product.assembly,
      couplings: couplings.map((coupling) => ({
        ...coupling,
        angle_deg: angle,
      })),
    },
  };
}

export function setCouplerSku(
  product: ProductJson,
  couplingId: string,
  sku: string | null,
): ProductJson {
  const coupling = product.assembly.couplings.find((item) => item.id === couplingId);
  if (!coupling) return product;
  return replaceCoupling(product, couplingId, {
    ...coupling,
    coupler_profile_sku: sku,
  });
}

export function setCouplerSkuAll(product: ProductJson, sku: string | null): ProductJson {
  return {
    ...product,
    assembly: {
      ...product.assembly,
      couplings: product.assembly.couplings.map((coupling) => ({
        ...coupling,
        coupler_profile_sku: sku,
      })),
    },
  };
}

export function setModuleOpening(
  product: ProductJson,
  moduleId: string,
  opening: Opening,
): ProductJson {
  const module = product.assembly.modules.find((item) => item.id === moduleId);
  if (!module) return product;
  function withOpening(node: IntentNode): IntentNode {
    if (node.type === "BAY") {
      // Panels are only an engine input for DOOR_ENTRY; a stale panel sku on a
      // non-door bay would linger invisibly after switching back.
      const cleared =
        opening === "DOOR_ENTRY"
          ? { ...node, opening_type: opening }
          : { ...node, opening_type: opening, panel_article_sku: null };
      // The opening picker selects presets — a stale declared layout would
      // keep winning over the new preset. "SLIDING" alone needs a layout to
      // evaluate, so it seeds the 2-leaf topology the user then edits.
      return {
        ...cleared,
        sliding_layout: opening === "SLIDING" ? structuredClone(SLIDING_PRESETS.SLIDING_2L!) : null,
      };
    }
    return { ...node, children: node.children?.map(withOpening) };
  }
  const singleChild = module.tree.children?.at(0);
  const tree =
    module.tree.type === "ROOT" && singleChild && module.tree.children?.length === 1
      ? { ...module.tree, children: [withOpening(singleChild)] }
      : withOpening(module.tree);
  return replaceModule(product, moduleId, { ...module, tree });
}

/** Author the primary bay's sliding topology (mandate §12). Any manual
 * layout edit makes the bay layout-driven (`opening_type: "SLIDING"` —
 * presets resolve without a declared layout). */
export function setModuleSlidingLayout(
  product: ProductJson,
  moduleId: string,
  layout: SlidingLayout,
): ProductJson {
  const module = product.assembly.modules.find((item) => item.id === moduleId);
  if (!module) return product;
  function withLayout(node: IntentNode): IntentNode {
    if (node.type === "BAY") {
      return { ...node, opening_type: "SLIDING", sliding_layout: layout };
    }
    return { ...node, children: node.children?.map(withLayout) };
  }
  const singleChild = module.tree.children?.at(0);
  const tree =
    module.tree.type === "ROOT" && singleChild && module.tree.children?.length === 1
      ? { ...module.tree, children: [withLayout(singleChild)] }
      : withLayout(module.tree);
  return replaceModule(product, moduleId, { ...module, tree });
}

/** First bay of a module tree — anchor for material edits. */
export function modulePrimaryBay(module: ProductModuleJson): IntentNode | null {
  const child = module.tree.children?.at(0);
  const bays = intentBays(module.tree.type === "ROOT" && child ? child : module.tree);
  return bays[0] ?? null;
}

export function moduleOpening(module: ProductModuleJson): Opening {
  const bay = modulePrimaryBay(module);
  return bay?.opening_type ?? "FIXED";
}

/** Commercial glass SKU on every bay of a module — pricing authority. */
export function setModuleGlass(
  product: ProductJson,
  moduleId: string,
  glassArticleSku: string | null,
): ProductJson {
  const module = product.assembly.modules.find((item) => item.id === moduleId);
  if (!module) return product;
  function withGlass(node: IntentNode): IntentNode {
    if (node.type === "BAY") return { ...node, glass_article_sku: glassArticleSku };
    return { ...node, children: node.children?.map(withGlass) };
  }
  return replaceModule(product, moduleId, { ...module, tree: withGlass(module.tree) });
}

export function moduleGlassSku(module: ProductModuleJson): string | null {
  return modulePrimaryBay(module)?.glass_article_sku ?? null;
}

/** Glazing thickness on every bay of a module (bead slot + monolithic spec
 * fallback). An existing glass composition is preserved — the thickness is
 * the physical slot, the spec the pane recipe. */
export function setModuleGlassThickness(
  product: ProductJson,
  moduleId: string,
  glassThicknessMm: string | null,
): ProductJson {
  const module = product.assembly.modules.find((item) => item.id === moduleId);
  if (!module) return product;
  function withThickness(node: IntentNode): IntentNode {
    if (node.type === "BAY") {
      return {
        ...node,
        glass_thickness_mm: glassThicknessMm,
        glass_spec: node.glass_spec ?? glassThicknessMm,
      };
    }
    return { ...node, children: node.children?.map(withThickness) };
  }
  return replaceModule(product, moduleId, { ...module, tree: withThickness(module.tree) });
}

export function moduleGlassThicknessMm(module: ProductModuleJson): string | null {
  return modulePrimaryBay(module)?.glass_thickness_mm ?? null;
}

/** Catalog panel article for door modules (DOOR_ENTRY infill authority). */
export function setModulePanel(
  product: ProductJson,
  moduleId: string,
  panelArticleSku: string | null,
): ProductJson {
  const module = product.assembly.modules.find((item) => item.id === moduleId);
  if (!module) return product;
  function withPanel(node: IntentNode): IntentNode {
    if (node.type === "BAY") return { ...node, panel_article_sku: panelArticleSku };
    return { ...node, children: node.children?.map(withPanel) };
  }
  return replaceModule(product, moduleId, { ...module, tree: withPanel(module.tree) });
}

export function modulePanelSku(module: ProductModuleJson): string | null {
  return modulePrimaryBay(module)?.panel_article_sku ?? null;
}

/** A bay's region extent along an axis — the span its local split_offset_mm
 * must stay inside, derived exactly like the engine walks the tree: the top
 * node fills the frame-clear rectangle (module span minus both frame faces)
 * and every same-axis ancestor consumes half its mullion face on each side
 * of the split centerline. The top node's own split_offset_mm is measured
 * from the module edge (local origin 0); deeper nodes measure from their
 * own region origin, so only the root step folds in raw module mm.
 * `isTopBay` tells callers the bay IS the tree top — a new split there
 * becomes the root and needs a module-relative offset. */
function baySpanOnAxis(
  root: IntentNode,
  bayId: string,
  vertical: boolean,
  moduleSpanMm: number,
  members: MemberGeometry,
): { spanMm: number; isTopBay: boolean } | null {
  const pathTo = (node: IntentNode): { node: IntentNode; index: number }[] | null => {
    if (node.id === bayId) return [];
    for (const [index, child] of (node.children ?? []).entries()) {
      const rest = pathTo(child);
      if (rest !== null) return [{ node, index }, ...rest];
    }
    return null;
  };
  const path = pathTo(root);
  if (!path) return null;
  const frameFace = members.frame.faceWidthMm;
  const mullionHalf =
    (vertical
      ? (members.mullionV?.faceWidthMm ?? FALLBACK_MEMBERS.mullion)
      : (members.mullionH?.faceWidthMm ?? FALLBACK_MEMBERS.mullion)) / 2;
  let lo = frameFace;
  let hi = Math.max(moduleSpanMm - frameFace, frameFace);
  for (const { node, index } of path) {
    if (node.type !== "SPLIT_V" && node.type !== "SPLIT_H") continue;
    if ((node.type === "SPLIT_V") !== vertical) continue;
    const offset = Number(node.split_offset_mm);
    if (!Number.isFinite(offset) || offset <= 0) continue;
    const centerline = node === root ? offset : lo + offset;
    if (index === 0) hi = Math.min(hi, centerline - mullionHalf);
    else lo = Math.max(lo, centerline + mullionHalf);
  }
  return { spanMm: Math.max(hi - lo, 0), isTopBay: path.length === 0 };
}

/** "Dividir" — split a module's bay region with a catalog mullion.
 *
 * The default split centers inside the TARGET bay's own span (bay-local
 * offsets measure from the bay's region origin, not the module edge), so a
 * click anywhere — front view, object tree, plan — produces a valid nested
 * split. Returns the unchanged product when the module or split is invalid
 * (door bays can't split).
 */
export function splitModuleBay(
  product: ProductJson,
  moduleId: string,
  division: { type: SplitType; mullionSku: string; offsetMm?: string; bayId?: string },
  members?: MemberGeometry,
): ProductJson {
  const module = product.assembly.modules.find((item) => item.id === moduleId);
  if (!module || !division.mullionSku.trim()) return product;
  const root =
    module.tree.type === "ROOT" ? (module.tree.children?.[0] ?? module.tree) : module.tree;
  const bay = division.bayId
    ? (intentBays(root).find((item) => item.id === division.bayId) ?? null)
    : modulePrimaryBay(module);
  if (!bay || moduleOpening(module) === "DOOR_ENTRY") return product;
  const size = division.type === "SPLIT_V" ? Number(module.width_mm) : Number(module.height_mm);
  if (!Number.isFinite(size) || size <= 0) return product;
  const region = baySpanOnAxis(
    root,
    bay.id,
    division.type === "SPLIT_V",
    size,
    members ?? resolveMembers(undefined),
  );
  if (region === null || region.spanMm <= 0) return product;
  // The top bay's split becomes the new root — its offset is module-relative.
  // Deeper bays store bay-local offsets, so centering halves the bay's own span.
  const offset = division.offsetMm ?? (region.isTopBay ? size / 2 : region.spanMm / 2).toFixed(2);
  const used = new Set(walkIntent(module.tree).map((node) => node.id));
  const freeId = (base: string): string => {
    let index = 1;
    while (used.has(`${base}${index}`)) index += 1;
    return `${base}${index}`;
  };
  try {
    const tree = splitBay(
      module.tree.type === "ROOT" ? (module.tree.children?.[0] ?? module.tree) : module.tree,
      bay.id,
      { type: division.type, offsetMm: offset, mullionSku: division.mullionSku },
      {
        split: freeId(`${module.id}-s${division.type === "SPLIT_V" ? "v" : "h"}`),
        secondBay: freeId(`${bay.id}-b`),
      },
    );
    return replaceModule(product, moduleId, { ...module, tree });
  } catch {
    return product;
  }
}
