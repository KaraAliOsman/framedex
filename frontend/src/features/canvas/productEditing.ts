import type { IntentNode, Opening, SplitType } from "./intentEditing";
import { intentBays, moveDivision, splitBay, walkIntent } from "./intentEditing";

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
};

export type ProductModuleJson = {
  id: string;
  width_mm: string;
  height_mm: string;
  tree: IntentNode;
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

export function maxModuleHeight(product: ProductJson): number {
  return Math.max(...product.assembly.modules.map((module) => Number(module.height_mm)));
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
 * the classic design shape (which keeps the documentary/quotation path). */
export function isSingleUnit(product: ProductJson): boolean {
  return product.assembly.modules.length === 1 && product.assembly.couplings.length === 0;
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
    nextCouplings.push({
      id: `c${index - 1}`,
      angle_deg: lastAngle,
      coupler_profile_sku: lastSku,
    });
    nextModules.push({ ...last, id: `m${index}` });
  }
  return {
    ...product,
    assembly: { modules: nextModules, couplings: nextCouplings },
  };
}

export function setModuleWidth(
  product: ProductJson,
  moduleId: string,
  widthMm: string,
): ProductJson {
  const module = product.assembly.modules.find((item) => item.id === moduleId);
  if (!module) return product;
  return replaceModule(product, moduleId, { ...module, width_mm: widthMm });
}

/** Minimum width a module may be dragged to — below this the geometry is
 * meaningless for any catalog (engine minimums sit higher, ~400mm). */
export const MIN_MODULE_WIDTH_MM = 150;

/** Drag a module seam: the left module grows by `deltaMm`, the right module
 * shrinks by the same amount, so the overall width is preserved. Both sides
 * are clamped to MIN_MODULE_WIDTH_MM; returns the unchanged product when the
 * seam doesn't exist or would cross a minimum. */
export function resizeModuleSeam(
  product: ProductJson,
  seamIndex: number,
  deltaMm: number,
): ProductJson {
  const modules = product.assembly.modules;
  const left = modules[seamIndex];
  const right = modules[seamIndex + 1];
  if (!left || !right || !Number.isFinite(deltaMm)) return product;
  const leftMm = Number(left.width_mm) + deltaMm;
  const rightMm = Number(right.width_mm) - deltaMm;
  if (leftMm < MIN_MODULE_WIDTH_MM || rightMm < MIN_MODULE_WIDTH_MM) return product;
  const nextModules = modules.map((module, index) =>
    index === seamIndex
      ? { ...module, width_mm: leftMm.toFixed(2) }
      : index === seamIndex + 1
        ? { ...module, width_mm: rightMm.toFixed(2) }
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

export function setAllModuleHeights(product: ProductJson, heightMm: string): ProductJson {
  return {
    ...product,
    assembly: {
      ...product.assembly,
      modules: product.assembly.modules.map((module) => ({
        ...module,
        height_mm: heightMm,
      })),
    },
  };
}

export function equalizeModuleWidths(product: ProductJson): ProductJson {
  const modules = product.assembly.modules;
  const total = totalModuleWidth(product);
  const share = Math.round((total / modules.length) * 100) / 100;
  const nextModules = modules.map((module, index) => ({
    ...module,
    width_mm:
      index === modules.length - 1
        ? (total - share * (modules.length - 1)).toFixed(2)
        : share.toFixed(2),
  }));
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
  const nextModules = modules.map((module, index) => ({
    ...module,
    width_mm: ((1 + shares[index]!) / 100).toFixed(2),
  }));
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

export function setModuleTree(
  product: ProductJson,
  moduleId: string,
  tree: IntentNode,
): ProductJson {
  const module = product.assembly.modules.find((item) => item.id === moduleId);
  if (!module) return product;
  return replaceModule(product, moduleId, { ...module, tree });
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
      return opening === "DOOR_ENTRY"
        ? { ...node, opening_type: opening }
        : { ...node, opening_type: opening, panel_article_sku: null };
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

/** "Dividir" — split a module's bay region with a catalog mullion.
 *
 * The default split is centered (width / 2 for vertical, height / 2 for
 * horizontal) so a single click produces two equal regions; the user can
 * refine the divider afterwards. Returns the unchanged product when the
 * module or split is invalid (door bays can't split).
 */
export function splitModuleBay(
  product: ProductJson,
  moduleId: string,
  division: { type: SplitType; mullionSku: string; offsetMm?: string; bayId?: string },
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
  const offset = division.offsetMm ?? (size / 2).toFixed(2);
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
