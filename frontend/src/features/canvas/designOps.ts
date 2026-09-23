import type { Opening } from "./intentEditing";
import {
  addAdjacentUnit,
  equalizeCouplingAngles,
  equalizeModuleWidths,
  removeUnit,
  scaleModuleWidths,
  setAllModuleHeights,
  setCouplingAngle,
  setModuleCount,
  setModuleGlass,
  setModuleGlassThickness,
  setModuleOpening,
  setModulePanel,
  setModuleWidth,
  type ProductJson,
} from "./productEditing";

/** The validated op contract returned by POST /positions/<id>/design-assist/.
 * The server has already bounds-checked every index, enum and range against
 * the actual assembly; the client still refuses unknown ops so a newer
 * backend can never silently drive an older editor. */
export type DesignOp = { op: string } & Record<string, unknown>;

const OPENING_LABELS: Record<string, string> = {
  FIXED: "fijo",
  TURN_LEFT: "abatible izquierda",
  TURN_RIGHT: "abatible derecha",
  TILT_TURN_LEFT: "oscilobatiente izquierda",
  TILT_TURN_RIGHT: "oscilobatiente derecha",
  SLIDING_2L: "corredera 2 hojas",
  AWNING: "proyectante",
  DOOR_ENTRY: "puerta",
};

function moduleAt(product: ProductJson, index: unknown): string | null {
  if (typeof index !== "number") return null;
  return product.assembly.modules[index]?.id ?? null;
}

function couplingAt(product: ProductJson, index: unknown): string | null {
  if (typeof index !== "number") return null;
  return product.assembly.couplings[index]?.id ?? null;
}

function text(value: unknown): string | null {
  return typeof value === "string" && value.length ? value : null;
}

export function applyDesignOp(product: ProductJson, op: DesignOp): ProductJson {
  switch (op.op) {
    case "set_module_count":
      return typeof op.count === "number" ? setModuleCount(product, op.count) : product;
    case "add_unit": {
      const side = op.side === "left" ? "left" : "right";
      return addAdjacentUnit(product, side);
    }
    case "remove_unit": {
      const moduleId = moduleAt(product, op.module);
      return moduleId ? removeUnit(product, moduleId) : product;
    }
    case "set_module_width": {
      const moduleId = moduleAt(product, op.module);
      const width = text(op.width_mm);
      return moduleId && width ? setModuleWidth(product, moduleId, width) : product;
    }
    case "set_total_width": {
      const width = text(op.width_mm);
      return width ? scaleModuleWidths(product, width) : product;
    }
    case "set_height": {
      const height = text(op.height_mm);
      return height ? setAllModuleHeights(product, height) : product;
    }
    case "equalize_widths":
      return equalizeModuleWidths(product);
    case "equalize_angles":
      return equalizeCouplingAngles(product);
    case "set_coupling_angle": {
      const couplingId = couplingAt(product, op.coupling);
      const angle = text(op.angle_deg);
      return couplingId && angle ? setCouplingAngle(product, couplingId, angle) : product;
    }
    case "set_opening": {
      const moduleId = moduleAt(product, op.module);
      return moduleId && text(op.opening)
        ? setModuleOpening(product, moduleId, op.opening as Opening)
        : product;
    }
    case "set_glass_thickness": {
      const moduleId = moduleAt(product, op.module);
      return moduleId ? setModuleGlassThickness(product, moduleId, text(op.mm)) : product;
    }
    case "set_glass": {
      const moduleId = moduleAt(product, op.module);
      return moduleId ? setModuleGlass(product, moduleId, text(op.sku)) : product;
    }
    case "set_panel": {
      const moduleId = moduleAt(product, op.module);
      const sku = op.sku === null ? null : text(op.sku);
      return moduleId ? setModulePanel(product, moduleId, sku) : product;
    }
    default:
      return product;
  }
}

export function applyDesignOps(product: ProductJson, ops: DesignOp[]): ProductJson {
  return ops.reduce((current, op) => applyDesignOp(current, op), product);
}

export function describeDesignOp(op: DesignOp): string {
  const module = typeof op.module === "number" ? `módulo ${op.module + 1}` : "módulo";
  switch (op.op) {
    case "set_module_count":
      return `${op.count} módulos`;
    case "add_unit":
      return `agregar unidad ${op.side === "left" ? "a la izquierda" : "a la derecha"}`;
    case "remove_unit":
      return `quitar ${module}`;
    case "set_module_width":
      return `${module}: ancho ${op.width_mm} mm`;
    case "set_total_width":
      return `ancho total ${op.width_mm} mm`;
    case "set_height":
      return `alto ${op.height_mm} mm`;
    case "equalize_widths":
      return "anchos iguales";
    case "equalize_angles":
      return "ángulos iguales";
    case "set_coupling_angle":
      return `unión ${Number(op.coupling) + 1}: ${op.angle_deg}°`;
    case "set_opening":
      return `${module}: ${OPENING_LABELS[String(op.opening)] ?? op.opening}`;
    case "set_glass_thickness":
      return `${module}: vidrio ${op.mm} mm`;
    case "set_glass":
      return `${module}: vidrio ${op.sku}`;
    case "set_panel":
      return `${module}: panel ${op.sku ?? "ninguno"}`;
    default:
      return String(op.op);
  }
}
