import type { IntentNode, Opening } from "./intentEditing";
import { intentBays } from "./intentEditing";

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
): IntentNode {
  return {
    id,
    type: "BAY",
    opening_type: opening,
    glass_thickness_mm: glassThicknessMm,
    glass_spec: glassSpec,
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
}): ProductJson {
  const {
    moduleCount,
    widthMm,
    heightMm,
    angleDeg,
    opening = "FIXED",
    glassThicknessMm = "4.00",
    glassSpec = "4",
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
      tree: makeBayTree(`m${index}`, opening, glassThicknessMm, glassSpec),
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
  if (!Number.isFinite(totalCents) || totalCents <= 0 || currentCents <= 0) return product;
  const widths = modules.map((module) =>
    Math.round((Number(module.width_mm) * 100 * totalCents) / currentCents),
  );
  // The last module absorbs the rounding remainder so the widths always sum
  // back to the requested total (0.00 mm tolerance).
  const last = totalCents - widths.slice(0, -1).reduce((sum, width) => sum + width, 0);
  const nextModules = modules.map((module, index) => ({
    ...module,
    width_mm: ((index === modules.length - 1 ? last : widths[index]!) / 100).toFixed(2),
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
    if (node.type === "BAY") return { ...node, opening_type: opening };
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
