import { t } from "../../i18n/es-CL";
import type { CommandArgs, CommandContext, CommandSpec, DesignOp } from "../commands/types";
import type { Opening } from "./intentEditing";
import { OPENING_OPTIONS } from "./openings";
import {
  addAdjacentUnit,
  equalizeCouplingAngles,
  equalizeModuleWidths,
  moduleGlassThicknessMm,
  modulePanelSku,
  removeUnit,
  scaleModuleWidths,
  setAllCouplingAngles,
  setAllModuleHeights,
  setCouplerSku,
  setCouplingAngle,
  setModuleCount,
  setModuleGlass,
  setModuleGlassThickness,
  setModuleOpening,
  setModulePanel,
  setModuleWidth,
  type ProductJson,
  type ProductModuleJson,
} from "./productEditing";

/** Same presentation rules as the canvas DraftFields: positive dimensions
 * commit at 0.01mm, joint angles stay strictly inside ±90° at 0.1°, module
 * counts are positive integers bounded by the product contract. */
function normalizeMm(raw: string): string | null {
  const value = Number(raw.replace(",", "."));
  if (!Number.isFinite(value) || value <= 0) return null;
  return value.toFixed(2);
}

function normalizeAngle(raw: string): string | null {
  const value = Number(raw.replace(",", "."));
  if (!Number.isFinite(value) || Math.abs(value) >= 90) return null;
  return value.toFixed(1);
}

function normalizeCount(raw: string): string | null {
  const value = Number(raw.replace(",", "."));
  if (!Number.isInteger(value) || value < 1 || value > 12) return null;
  return String(value);
}

function selectedModule(ctx: CommandContext): ProductModuleJson | null {
  return ctx.product.assembly.modules.find((module) => module.id === ctx.selection) ?? null;
}

function selectedCoupling(ctx: CommandContext) {
  return ctx.product.assembly.couplings.find((coupling) => coupling.id === ctx.selection) ?? null;
}

function moduleAt(product: ProductJson, index: unknown): string | null {
  return typeof index === "number" ? (product.assembly.modules[index]?.id ?? null) : null;
}

function couplingAt(product: ProductJson, index: unknown): string | null {
  return typeof index === "number" ? (product.assembly.couplings[index]?.id ?? null) : null;
}

function text(value: unknown): string | null {
  return typeof value === "string" && value.length ? value : null;
}

/** Wire `module` index → args `{module: <id>, target: "<n>"}`: the id drives
 * `apply`, the 1-based number stays for human descriptions. */
function decodeModule(
  op: DesignOp,
  product: ProductJson,
  extra: CommandArgs = {},
): CommandArgs | null {
  const id = moduleAt(product, op.module);
  return id ? { module: id, target: String(Number(op.module) + 1), ...extra } : null;
}

function decodeCoupling(
  op: DesignOp,
  product: ProductJson,
  extra: CommandArgs = {},
): CommandArgs | null {
  const id = couplingAt(product, op.coupling);
  return id ? { coupling: id, target: String(Number(op.coupling) + 1), ...extra } : null;
}

const OPENING_LABELS: Partial<Record<Opening, string>> = {
  FIXED: "fijo",
  TURN_LEFT: "abatible izquierda",
  TURN_RIGHT: "abatible derecha",
  TILT_TURN_LEFT: "oscilobatiente izquierda",
  TILT_TURN_RIGHT: "oscilobatiente derecha",
  SLIDING_2L: "corredera 2 hojas",
  AWNING: "proyectante",
  DOOR_ENTRY: "puerta",
};

function moduleLabel(args: CommandArgs): string {
  return `módulo ${args.target ?? "?"}`;
}

/** THE command table — the single typed domain registry every surface shares.
 * Palette rows, shortcuts, context menus and AI ops all resolve to these
 * specs; `apply` is the only mutation path (one undoable commit upstream). */
export const ASSEMBLY_COMMANDS: CommandSpec[] = [
  {
    id: "product.add-right",
    title: "cmd.addUnitRight",
    keywords: ["añadir", "unidad", "vano", "hoja", "derecha", "modulo", "agregar"],
    apply: (ctx) => addAdjacentUnit(ctx.product, "right"),
    describe: () => "agregar unidad a la derecha",
    ai: { op: "add_unit", decode: (op) => (op.side === "left" ? null : { side: "right" }) },
  },
  {
    id: "product.add-left",
    title: "cmd.addUnitLeft",
    keywords: ["añadir", "unidad", "vano", "hoja", "izquierda", "modulo", "agregar"],
    apply: (ctx) => addAdjacentUnit(ctx.product, "left"),
    describe: () => "agregar unidad a la izquierda",
    ai: { op: "add_unit", decode: (op) => (op.side === "left" ? { side: "left" } : null) },
  },
  {
    id: "product.set-module-count",
    title: "cmd.setModuleCount",
    keywords: ["cantidad", "módulos", "modulos", "unidades", "número"],
    params: () => [
      { kind: "number", id: "count", label: t("cmd.moduleCountLabel"), validate: normalizeCount },
    ],
    apply: (ctx, args) => {
      const count = normalizeCount(args.count ?? "");
      return count === null ? ctx.product : setModuleCount(ctx.product, Number(count));
    },
    describe: (args) => `${args.count ?? "?"} módulos`,
    ai: {
      op: "set_module_count",
      decode: (op) =>
        typeof op.count === "number" && Number.isInteger(op.count) && op.count >= 1
          ? { count: String(op.count) }
          : null,
    },
  },
  {
    id: "module.remove",
    title: "cmd.removeUnit",
    keywords: ["eliminar", "quitar", "unidad", "vano", "hoja", "modulo"],
    applicable: (ctx) => selectedModule(ctx) !== null && ctx.product.assembly.modules.length > 1,
    apply: (ctx, args) => {
      const id = args.module ?? selectedModule(ctx)?.id;
      return id && ctx.product.assembly.modules.length > 1
        ? removeUnit(ctx.product, id)
        : ctx.product;
    },
    describe: (args) => `quitar ${moduleLabel(args)}`,
    ai: { op: "remove_unit", decode: decodeModule },
  },
  {
    id: "product.set-height",
    title: "cmd.setHeight",
    keywords: ["alto", "altura", "dimensiones"],
    params: (ctx) => [
      {
        kind: "number",
        id: "height",
        label: t("cmd.heightLabel"),
        unit: "mm",
        defaultValue: ctx.product.assembly.modules[0]?.height_mm,
        validate: normalizeMm,
      },
    ],
    apply: (ctx, args) => {
      const height = normalizeMm(args.height ?? "");
      return height === null ? ctx.product : setAllModuleHeights(ctx.product, height);
    },
    describe: (args) => `alto ${args.height ?? "?"} mm`,
    ai: {
      op: "set_height",
      decode: (op) => {
        const height = text(op.height_mm);
        return height ? { height } : null;
      },
    },
  },
  {
    id: "product.set-total-width",
    title: "cmd.setTotalWidth",
    keywords: ["ancho", "total", "dimensiones", "ancho total"],
    params: (ctx) => [
      {
        kind: "number",
        id: "width",
        label: t("cmd.totalWidthLabel"),
        unit: "mm",
        defaultValue: String(
          ctx.product.assembly.modules.reduce((sum, module) => sum + Number(module.width_mm), 0),
        ),
        validate: normalizeMm,
      },
    ],
    apply: (ctx, args) => {
      const width = normalizeMm(args.width ?? "");
      return width === null ? ctx.product : scaleModuleWidths(ctx.product, width);
    },
    describe: (args) => `ancho total ${args.width ?? "?"} mm`,
    ai: {
      op: "set_total_width",
      decode: (op) => {
        const width = text(op.width_mm);
        return width ? { width } : null;
      },
    },
  },
  {
    id: "module.set-width",
    title: "cmd.setWidth",
    keywords: ["ancho", "unidad", "dimensiones"],
    applicable: (ctx) => selectedModule(ctx) !== null,
    params: (ctx) => [
      {
        kind: "number",
        id: "width",
        label: t("cmd.widthLabel"),
        unit: "mm",
        defaultValue: selectedModule(ctx)?.width_mm,
        validate: normalizeMm,
      },
    ],
    apply: (ctx, args) => {
      const id = args.module ?? selectedModule(ctx)?.id;
      const width = normalizeMm(args.width ?? "");
      return id && width !== null ? setModuleWidth(ctx.product, id, width) : ctx.product;
    },
    describe: (args) => `${moduleLabel(args)}: ancho ${args.width ?? "?"} mm`,
    ai: {
      op: "set_module_width",
      decode: (op, product) => {
        const width = text(op.width_mm);
        return width ? decodeModule(op, product, { width }) : null;
      },
    },
  },
  {
    id: "module.set-opening",
    title: "cmd.setOpening",
    keywords: ["apertura", "hoja", "fijo", "oscilobatiente", "puerta", "corredera"],
    applicable: (ctx) => selectedModule(ctx) !== null,
    params: () => [
      {
        kind: "choice",
        id: "opening",
        label: t("cmd.openingLabel"),
        options: OPENING_OPTIONS.map(([value, key]) => ({ value, label: t(key) })),
      },
    ],
    apply: (ctx, args) => {
      const id = args.module ?? selectedModule(ctx)?.id;
      return id && args.opening
        ? setModuleOpening(ctx.product, id, args.opening as Opening)
        : ctx.product;
    },
    describe: (args) =>
      `${moduleLabel(args)}: ${OPENING_LABELS[args.opening as Opening] ?? args.opening ?? "?"}`,
    ai: {
      op: "set_opening",
      decode: (op, product) => {
        const opening = text(op.opening);
        return opening ? decodeModule(op, product, { opening }) : null;
      },
    },
  },
  {
    id: "module.set-glass",
    title: "cmd.setGlass",
    keywords: ["vidrio", "composicion", "composición", "artículo", "articulo", "dvh"],
    applicable: (ctx) => selectedModule(ctx) !== null && ctx.catalog.glassSkus.length > 0,
    params: (ctx) => [
      {
        kind: "choice",
        id: "glass",
        label: t("cmd.glassLabel"),
        options: ctx.catalog.glassSkus.map((value) => ({ value, label: value })),
      },
    ],
    apply: (ctx, args) => {
      const id = args.module ?? selectedModule(ctx)?.id;
      return id ? setModuleGlass(ctx.product, id, args.glass ?? null) : ctx.product;
    },
    describe: (args) => `${moduleLabel(args)}: vidrio ${args.glass ?? "?"}`,
    ai: {
      op: "set_glass",
      decode: (op, product) => {
        const sku = text(op.sku);
        return sku ? decodeModule(op, product, { glass: sku }) : null;
      },
    },
  },
  {
    id: "module.set-glass-thickness",
    title: "cmd.setGlassThickness",
    keywords: ["vidrio", "espesor", "dvh"],
    applicable: (ctx) => selectedModule(ctx) !== null && ctx.catalog.glassThicknesses.length > 0,
    params: (ctx) => [
      {
        kind: "choice",
        id: "thickness",
        label: t("cmd.glassThicknessLabel"),
        options: ctx.catalog.glassThicknesses.map((value) => ({
          value,
          label: `${value} mm`,
        })),
      },
    ],
    apply: (ctx, args) => {
      const id = args.module ?? selectedModule(ctx)?.id;
      return id ? setModuleGlassThickness(ctx.product, id, args.thickness ?? null) : ctx.product;
    },
    describe: (args) => `${moduleLabel(args)}: vidrio ${args.thickness ?? "?"} mm`,
    ai: {
      op: "set_glass_thickness",
      decode: (op, product) => decodeModule(op, product, { thickness: text(op.mm) ?? "" }),
    },
  },
  {
    id: "module.set-panel",
    title: "cmd.setPanel",
    keywords: ["panel", "sandwich", "tablero"],
    applicable: (ctx) => selectedModule(ctx) !== null && ctx.catalog.panelSkus.length > 0,
    params: (ctx) => [
      {
        kind: "choice",
        id: "panel",
        label: t("cmd.panelLabel"),
        options: [
          { value: "", label: t("assembly.noPanel") },
          ...ctx.catalog.panelSkus.map((value) => ({ value, label: value })),
        ],
      },
    ],
    apply: (ctx, args) => {
      const id = args.module ?? selectedModule(ctx)?.id;
      return id ? setModulePanel(ctx.product, id, args.panel || null) : ctx.product;
    },
    describe: (args) => `${moduleLabel(args)}: panel ${args.panel || "ninguno"}`,
    ai: {
      op: "set_panel",
      decode: (op, product) =>
        decodeModule(op, product, { panel: op.sku === null ? "" : (text(op.sku) ?? "") }),
    },
  },
  {
    id: "module.clear-panel",
    title: "cmd.clearPanel",
    keywords: ["panel", "quitar", "eliminar"],
    applicable: (ctx) => {
      const module = selectedModule(ctx);
      return module !== null && modulePanelSku(module) !== null;
    },
    apply: (ctx) => {
      const module = selectedModule(ctx);
      return module ? setModulePanel(ctx.product, module.id, null) : ctx.product;
    },
  },
  {
    id: "module.clear-glass-thickness",
    title: "cmd.clearGlassThickness",
    keywords: ["vidrio", "espesor", "quitar"],
    applicable: (ctx) => {
      const module = selectedModule(ctx);
      return module !== null && moduleGlassThicknessMm(module) !== null;
    },
    apply: (ctx) => {
      const module = selectedModule(ctx);
      return module ? setModuleGlassThickness(ctx.product, module.id, null) : ctx.product;
    },
  },
  {
    id: "product.equalize-widths",
    title: "cmd.equalizeWidths",
    keywords: ["igualar", "anchos", "unidades", "repartir"],
    applicable: (ctx) => ctx.product.assembly.modules.length > 1,
    apply: (ctx) => equalizeModuleWidths(ctx.product),
    describe: () => "anchos iguales",
    ai: { op: "equalize_widths", decode: () => ({}) },
  },
  {
    id: "product.equalize-angles",
    title: "cmd.equalizeAngles",
    keywords: ["igualar", "ángulos", "angulos", "acoplamiento", "bow"],
    applicable: (ctx) => ctx.product.assembly.couplings.length > 1,
    apply: (ctx) => equalizeCouplingAngles(ctx.product),
    describe: () => "ángulos iguales",
    ai: { op: "equalize_angles", decode: () => ({}) },
  },
  {
    id: "product.straighten",
    title: "cmd.straighten",
    keywords: ["recto", "enderezar", "cero", "ángulos", "planar"],
    applicable: (ctx) =>
      ctx.product.assembly.couplings.some((coupling) => coupling.angle_deg !== "0"),
    apply: (ctx) => setAllCouplingAngles(ctx.product, "0"),
    describe: () => "conjunto recto",
  },
  {
    id: "coupling.set-angle",
    title: "cmd.setAngle",
    keywords: ["ángulo", "angulo", "acoplamiento", "unión", "union", "plano"],
    applicable: (ctx) => selectedCoupling(ctx) !== null,
    params: (ctx) => [
      {
        kind: "number",
        id: "angle",
        label: t("cmd.angleLabel"),
        unit: "°",
        defaultValue: selectedCoupling(ctx)?.angle_deg,
        validate: normalizeAngle,
      },
    ],
    apply: (ctx, args) => {
      const id = args.coupling ?? selectedCoupling(ctx)?.id;
      const angle = normalizeAngle(args.angle ?? "");
      return id && angle !== null ? setCouplingAngle(ctx.product, id, angle) : ctx.product;
    },
    describe: (args) =>
      Number(args.angle ?? "0") === 0
        ? t("cmd.setAngleStraightDesc")
        : `unión ${args.target ?? "?"}: ${args.angle ?? "?"}°`,
    ai: {
      op: "set_coupling_angle",
      decode: (op, product) => {
        const angle = text(op.angle_deg);
        return angle ? decodeCoupling(op, product, { angle }) : null;
      },
    },
  },
  {
    id: "coupling.clear-angle",
    title: "cmd.clearAngle",
    keywords: ["ángulo", "angulo", "recto", "cero", "acoplamiento"],
    applicable: (ctx) => {
      const coupling = selectedCoupling(ctx);
      return coupling !== null && coupling.angle_deg !== "0";
    },
    apply: (ctx) => {
      const coupling = selectedCoupling(ctx);
      return coupling ? setCouplingAngle(ctx.product, coupling.id, "0") : ctx.product;
    },
  },
  {
    id: "coupling.set-coupler",
    title: "cmd.setCoupler",
    keywords: ["cople", "acoplador", "perfil", "acoplamiento"],
    applicable: (ctx) => selectedCoupling(ctx) !== null && ctx.catalog.couplerSkus.length > 0,
    params: (ctx) => [
      {
        kind: "choice",
        id: "coupler",
        label: t("cmd.couplerLabel"),
        options: ctx.catalog.couplerSkus.map((value) => ({ value, label: value })),
      },
    ],
    apply: (ctx, args) => {
      const id = args.coupling ?? selectedCoupling(ctx)?.id;
      return id ? setCouplerSku(ctx.product, id, args.coupler ?? null) : ctx.product;
    },
    describe: (args) => `unión ${args.target ?? "?"}: cople ${args.coupler ?? "?"}`,
  },
  {
    id: "edit.undo",
    title: "cmd.undo",
    keywords: ["deshacer", "volver"],
    applicable: (ctx) => ctx.canUndo === true,
    run: (ctx) => ctx.undo?.(),
  },
  {
    id: "edit.redo",
    title: "cmd.redo",
    keywords: ["rehacer", "adelante"],
    applicable: (ctx) => ctx.canRedo === true,
    run: (ctx) => ctx.redo?.(),
  },
  {
    id: "tool.split-vertical",
    title: "cmd.splitVertical",
    keywords: ["dividir", "partir", "vertical", "montante", "mullion"],
    applicable: (ctx) => ctx.catalog.mullionSkus.SPLIT_V !== undefined,
    run: (ctx) => ctx.setTool?.("split_v"),
  },
  {
    id: "tool.split-horizontal",
    title: "cmd.splitHorizontal",
    keywords: ["dividir", "partir", "horizontal", "travesaño", "transom"],
    applicable: (ctx) => ctx.catalog.mullionSkus.SPLIT_H !== undefined,
    run: (ctx) => ctx.setTool?.("split_h"),
  },
];

/** UI affordance on the same registry: the palette row and context-menu entry
 * that open the design assistant. Non-mutating — `run` only moves focus. */
export const UI_ASK_ASSISTANT: CommandSpec = {
  id: "ui.ask-assistant",
  title: "cmd.askDekopen",
  keywords: ["ia", "ai", "asistente", "preguntar", "dekopen", "ayuda", "help"],
  run: (ctx) => ctx.focusAssistant?.(),
};

/** Commands the surface offers right now (selection/product-sensitive). */
export function assemblyCommands(ctx: CommandContext): CommandSpec[] {
  if (ctx.disabled) return [];
  const domain = ASSEMBLY_COMMANDS.filter((spec) => spec.applicable?.(ctx) ?? true);
  return ctx.focusAssistant ? [...domain, UI_ASK_ASSISTANT] : domain;
}
