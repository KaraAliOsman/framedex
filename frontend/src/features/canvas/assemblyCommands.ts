import { parseLocaleNumber } from "../../format";
import type { DesignOperationRequest } from "../../api/generated/models";
import { asGlassProduct, glassChoicePatch } from "../glass/glassModel";
import { t } from "../../i18n/es-CL";
import type {
  CommandArgs,
  CommandContext,
  CommandSpec,
  DesignOp,
  DesignOpState,
} from "../commands/types";
import type { IntentNode, Opening } from "./intentEditing";
import { baySpec, findNode, parentSplitOf, updateBay } from "./intentEditing";
import { choicePatch, physicalNodeLabel, structuredOpeningPatch } from "./physicalOpenings";
import { OPENING_OPTIONS } from "./openings";
import { runCommand } from "../commands/registry";
import { unlinkCoupling, usedEdges } from "./assemblyGraph";
import {
  addAdjacentUnit,
  addStackedUnit,
  allowedCouplingKinds,
  canRemoveModuleDivision,
  copyBaySpec,
  duplicateModule,
  equalizeCouplingAngles,
  equalizeModuleWidths,
  insertModuleBetween,
  moduleGlassThicknessMm,
  moduleNeighbors,
  modulePrimaryBay,
  modulePanelSku,
  removeModuleBay,
  removeModuleDivision,
  removeUnit,
  scaleModuleWidths,
  setAllCouplingAngles,
  setAllModuleHeights,
  setCouplerSku,
  setCouplingAngle,
  setCouplingKind,
  setModuleCount,
  setModuleGlass,
  setModuleGlassThickness,
  setModuleOpening,
  setModulePanel,
  setModuleTree,
  setModuleWidth,
  swapModules,
  type ProductJson,
  type ProductModuleJson,
} from "./productEditing";

/** Same presentation rules as the canvas DraftFields: positive dimensions
 * commit at 0.01mm, joint angles stay strictly inside ±90° at 0.1°, module
 * counts are positive integers bounded by the product contract. */
const MAX_MM = 30000;

function normalizeMm(raw: string): string | null {
  const value = parseLocaleNumber(raw);
  if (value === null || value <= 0 || value > MAX_MM) return null;
  return value.toFixed(2);
}

function normalizeAngle(raw: string): string | null {
  const value = parseLocaleNumber(raw);
  if (value === null || Math.abs(value) >= 90) return null;
  return value.toFixed(1);
}

function normalizeCount(raw: string): string | null {
  const value = parseLocaleNumber(raw);
  if (value === null || !Number.isInteger(value) || value < 1 || value > 12) return null;
  return String(value);
}

function selectedModule(ctx: CommandContext): ProductModuleJson | null {
  return ctx.product.assembly.modules.find((module) => module.id === ctx.selection) ?? null;
}

/** Module the selection lives in — the module row itself, or the module
 * owning a selected bay/split/handle. Module-level commands (duplicate,
 * reorder, width) act on it so a selected paño doesn't orphan them. */
function selectedModuleScope(ctx: CommandContext): ProductModuleJson | null {
  return selectedModule(ctx) ?? selectedTreeNode(ctx)?.module ?? null;
}

function selectedCoupling(ctx: CommandContext) {
  return ctx.product.assembly.couplings.find((coupling) => coupling.id === ctx.selection) ?? null;
}

/** Composite selection "moduleId/nodeId" → owning module + tree node.
 * Mullions, transoms and bays all live behind this address form. */
function selectedTreeNode(
  ctx: CommandContext,
): { module: ProductModuleJson; node: IntentNode } | null {
  const separator = ctx.selection?.indexOf("/") ?? -1;
  if (!ctx.selection || separator === -1) return null;
  const moduleId = ctx.selection.slice(0, separator);
  const nodeId = ctx.selection.slice(separator + 1);
  const module = ctx.product.assembly.modules.find((item) => item.id === moduleId) ?? null;
  const node = module ? findNode(module.tree, nodeId) : null;
  return module && node ? { module, node } : null;
}

function selectedSplit(ctx: CommandContext) {
  const target = selectedTreeNode(ctx);
  return target && (target.node.type === "SPLIT_V" || target.node.type === "SPLIT_H")
    ? target
    : null;
}

function selectedBayTarget(ctx: CommandContext) {
  const target = selectedTreeNode(ctx);
  return target && target.node.type === "BAY" ? target : null;
}

/** Target resolution: explicit args (palette params, AI wire args) win over
 * the live selection — same stable id space either way. */
function moduleTarget(ctx: CommandContext, args: CommandArgs): ProductModuleJson | null {
  const id = args.module ?? selectedModuleScope(ctx)?.id ?? null;
  return id ? (ctx.product.assembly.modules.find((module) => module.id === id) ?? null) : null;
}

function couplingTarget(ctx: CommandContext, args: CommandArgs) {
  const id = args.coupling ?? selectedCoupling(ctx)?.id ?? null;
  return id ? (ctx.product.assembly.couplings.find((item) => item.id === id) ?? null) : null;
}

function bayTarget(ctx: CommandContext, args: CommandArgs) {
  if (args.module && args.bay) {
    const module = ctx.product.assembly.modules.find((item) => item.id === args.module) ?? null;
    const node = module ? findNode(module.tree, args.bay) : null;
    return module && node?.type === "BAY" ? { module, node } : null;
  }
  return selectedBayTarget(ctx);
}

function splitTarget(ctx: CommandContext, args: CommandArgs) {
  if (args.module && args.division) {
    const module = ctx.product.assembly.modules.find((item) => item.id === args.module) ?? null;
    const node = module ? findNode(module.tree, args.division) : null;
    return module && node && (node.type === "SPLIT_V" || node.type === "SPLIT_H")
      ? { module, node }
      : null;
  }
  return selectedSplit(ctx);
}

/** The module a new member's id was minted from — post-commit selection
 * helper for structural run commands (duplicate, stack, insert). */
function createdModule(before: ProductJson, after: ProductJson): string | null {
  return (
    after.assembly.modules.find(
      (module) => !before.assembly.modules.some((item) => item.id === module.id),
    )?.id ?? null
  );
}

/** Wire `module`/`coupling` address → entity id. A string is a stable domain
 * ref — the module's own id, a synthetic `added_m{n}`/`added_c{n}` minted by
 * an earlier structural op in the same sequence, or the `m{n}`/`c{n}`
 * positional fallback — a number stays a legacy index. */
/** Positional addresses (a bare number or `m{n}`/`c{n}`) name the sequence
 * author's ORIGINAL ordering — the backend validator resolves them against
 * the immutable summary list, so the client resolves them against the
 * sequence-start product in state.origin. A member removed mid-sequence is
 * no longer addressable by position on either side. */
function moduleAt(product: ProductJson, address: unknown, state?: DesignOpState): string | null {
  const positional = state?.origin ?? product;
  const live = (id: string | undefined): string | null =>
    id && product.assembly.modules.some((module) => module.id === id) ? id : null;
  if (typeof address === "number") {
    return live(positional.assembly.modules[address]?.id);
  }
  if (typeof address !== "string") return null;
  const direct = product.assembly.modules.find((module) => module.id === address);
  if (direct) return direct.id;
  const added = /^added_m(\d+)$/.exec(address);
  if (added) return state?.addedModules[Number(added[1]) - 1] ?? null;
  const index = /^m(\d+)$/.exec(address);
  if (index) return live(positional.assembly.modules[Number(index[1]) - 1]?.id);
  return null;
}

function couplingAt(product: ProductJson, address: unknown, state?: DesignOpState): string | null {
  const positional = state?.origin ?? product;
  const live = (id: string | undefined): string | null =>
    id && product.assembly.couplings.some((coupling) => coupling.id === id) ? id : null;
  if (typeof address === "number") {
    return live(positional.assembly.couplings[address]?.id);
  }
  if (typeof address !== "string") return null;
  const direct = product.assembly.couplings.find((coupling) => coupling.id === address);
  if (direct) return direct.id;
  const added = /^added_c(\d+)$/.exec(address);
  if (added) return state?.addedCouplings[Number(added[1]) - 1] ?? null;
  const index = /^c(\d+)$/.exec(address);
  if (index) return live(positional.assembly.couplings[Number(index[1]) - 1]?.id);
  return null;
}

function text(value: unknown): string | null {
  return typeof value === "string" && value.length ? value : null;
}

/** Human position label for a wire address — '2' for the second module,
 * 'nueva 1' for a unit an earlier op in the sequence just created. */
function targetLabel(address: unknown, entities: { id: string }[]): string {
  if (typeof address === "number") return String(address + 1);
  if (typeof address !== "string") return "?";
  const added = /^added_[mc](\d+)$/.exec(address);
  if (added?.[1]) return `nueva ${added[1]}`;
  const index = entities.findIndex((entity) => entity.id === address);
  if (index >= 0) return String(index + 1);
  const positional = /^[mc](\d+)$/.exec(address);
  return positional?.[1] ?? "?";
}

/** Wire `module` address (ref or legacy index) → args `{module: <id>,
 * target: "<n>"}`: the id drives `apply`, the position stays for human
 * descriptions. */
function decodeModule(
  op: DesignOp,
  product: ProductJson,
  state?: DesignOpState,
  extra: CommandArgs = {},
): CommandArgs | null {
  const id = moduleAt(product, op.module, state);
  return id
    ? { module: id, target: targetLabel(op.module, product.assembly.modules), ...extra }
    : null;
}

function decodeCoupling(
  op: DesignOp,
  product: ProductJson,
  state?: DesignOpState,
  extra: CommandArgs = {},
): CommandArgs | null {
  const id = couplingAt(product, op.coupling, state);
  return id
    ? {
        coupling: id,
        target: targetLabel(op.coupling, product.assembly.couplings),
        ...extra,
      }
    : null;
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
    applicable: (ctx) =>
      selectedModuleScope(ctx) !== null && ctx.product.assembly.modules.length > 1,
    apply: (ctx, args) => {
      const id = args.module ?? selectedModule(ctx)?.id;
      return id && ctx.product.assembly.modules.length > 1
        ? removeUnit(ctx.product, id)
        : ctx.product;
    },
    postCommit: (ctx, before, next, args) => {
      const removedId = args.module ?? ctx.selection;
      const index = before.assembly.modules.findIndex((item) => item.id === removedId);
      ctx.select(
        next.assembly.modules[Math.min(Math.max(index, 0), next.assembly.modules.length - 1)]?.id ??
          null,
      );
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
        defaultValue: selectedModuleScope(ctx)?.width_mm,
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
      decode: (op, product, state) => {
        const width = text(op.width_mm);
        return width ? decodeModule(op, product, state, { width }) : null;
      },
    },
  },
  {
    id: "module.set-opening",
    title: "cmd.setOpening",
    keywords: ["apertura", "hoja", "fijo", "oscilobatiente", "puerta", "corredera"],
    applicable: (ctx) => selectedModule(ctx) !== null,
    params: (ctx) => [
      {
        kind: "choice",
        id: "opening",
        label: t("cmd.openingLabel"),
        options: ctx.catalog.openingChoices?.length
          ? ctx.catalog.openingChoices.map((choice) => ({
              value: JSON.stringify(choicePatch(choice)),
              label: choice.label,
            }))
          : OPENING_OPTIONS.filter(
              ([value]) =>
                !ctx.catalog.compatibleOpenings?.length ||
                ctx.catalog.compatibleOpenings.includes(value),
            ).map(([value, key]) => ({ value, label: t(key) })),
      },
    ],
    apply: (ctx, args) => {
      const id = args.module ?? selectedModule(ctx)?.id;
      if (id && args.opening?.startsWith("{")) {
        const module = ctx.product.assembly.modules.find((item) => item.id === id);
        const bay = module ? modulePrimaryBay(module) : null;
        try {
          const patch = structuredOpeningPatch(JSON.parse(args.opening));
          return module && bay && patch
            ? setModuleTree(ctx.product, id, updateBay(module.tree, bay.id, patch))
            : ctx.product;
        } catch {
          return ctx.product;
        }
      }
      return id && args.opening
        ? setModuleOpening(ctx.product, id, args.opening as Opening)
        : ctx.product;
    },
    describe: (args) => {
      try {
        const patch = structuredOpeningPatch(JSON.parse(args.opening ?? ""));
        if (patch?.opening)
          return `${moduleLabel(args)}: ${physicalNodeLabel({ ...patch, id: "opening-proposal", type: "BAY" })}`;
      } catch {
        /* Legacy transport has a human label below. */
      }
      return `${moduleLabel(args)}: ${OPENING_LABELS[args.opening as Opening] ?? "Apertura sin dato"}`;
    },
    ai: {
      op: "set_opening",
      decode: (op, product, state) => {
        const physical = structuredOpeningPatch(op);
        const opening = physical ? JSON.stringify(physical) : text(op.opening);
        return opening ? decodeModule(op, product, state, { opening }) : null;
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
        options: ctx.catalog.glassSkus.map((value) => ({
          value,
          label:
            asGlassProduct(ctx.catalog.glassSpecs?.find((choice) => choice.sku === value)?.product)
              ?.name ??
            ctx.catalog.glassSpecs?.find((choice) => choice.sku === value)?.spec ??
            value,
        })),
      },
    ],
    apply: (ctx, args) => {
      const id = args.module ?? selectedModule(ctx)?.id;
      const choice = ctx.catalog.glassSpecs?.find((item) => item.sku === args.glass);
      return id
        ? setModuleGlass(
            ctx.product,
            id,
            args.glass ?? null,
            choice?.spec,
            choice ? glassChoicePatch(choice) : undefined,
          )
        : ctx.product;
    },
    describe: (args) => `${moduleLabel(args)}: vidrio ${args.glass ?? "?"}`,
    ai: {
      op: "set_glass",
      decode: (op, product, state) => {
        const sku = text(op.sku);
        return sku ? decodeModule(op, product, state, { glass: sku }) : null;
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
      decode: (op, product, state) =>
        decodeModule(op, product, state, { thickness: text(op.mm) ?? "" }),
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
      decode: (op, product, state) =>
        decodeModule(op, product, state, { panel: op.sku === null ? "" : (text(op.sku) ?? "") }),
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
      decode: (op, product, state) => {
        const angle = text(op.angle_deg);
        return angle ? decodeCoupling(op, product, state, { angle }) : null;
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
    id: "module.duplicate",
    title: "cmd.duplicateModule",
    keywords: ["duplicar", "copiar", "clonar", "unidad", "vano"],
    shortcut: "mod+d",
    applicable: (ctx) => selectedModuleScope(ctx) !== null,
    apply: (ctx, args) => {
      const module = moduleTarget(ctx, args);
      return module ? duplicateModule(ctx.product, module.id) : ctx.product;
    },
    postCommit: (ctx, before, next) => {
      const created = createdModule(before, next);
      if (created) ctx.select(created);
    },
    describe: () => "duplicar unidad",
    ai: { op: "duplicate_module", decode: decodeModule },
  },
  {
    id: "module.move-left",
    title: "cmd.moveModuleLeft",
    keywords: ["mover", "izquierda", "reordenar", "orden", "intercambiar"],
    applicable: (ctx) =>
      selectedModuleScope(ctx) !== null &&
      moduleNeighbors(ctx.product, selectedModuleScope(ctx)!.id).left !== null,
    apply: (ctx) => {
      const module = selectedModuleScope(ctx);
      const left = module ? moduleNeighbors(ctx.product, module.id).left : null;
      return module && left ? swapModules(ctx.product, module.id, left) : ctx.product;
    },
    describe: () => "intercambiar con la unidad de la izquierda",
  },
  {
    id: "module.move-right",
    title: "cmd.moveModuleRight",
    keywords: ["mover", "derecha", "reordenar", "orden", "intercambiar"],
    applicable: (ctx) =>
      selectedModuleScope(ctx) !== null &&
      moduleNeighbors(ctx.product, selectedModuleScope(ctx)!.id).right !== null,
    apply: (ctx) => {
      const module = selectedModuleScope(ctx);
      const right = module ? moduleNeighbors(ctx.product, module.id).right : null;
      return module && right ? swapModules(ctx.product, module.id, right) : ctx.product;
    },
    describe: () => "intercambiar con la unidad de la derecha",
  },
  {
    id: "module.stack-above",
    title: "cmd.stackAbove",
    keywords: ["apilar", "encima", "montante", "transom", "stacked", "superior"],
    applicable: (ctx) => {
      const module = selectedModuleScope(ctx);
      return (
        module !== null &&
        !module.contour &&
        !module.frameless &&
        !usedEdges(ctx.product, module.id).has("top")
      );
    },
    apply: (ctx, args) => {
      const module = moduleTarget(ctx, args);
      return module ? addStackedUnit(ctx.product, module.id) : ctx.product;
    },
    postCommit: (ctx, before, next) => {
      const created = createdModule(before, next);
      if (created) ctx.select(created);
    },
    describe: () => "unidad apilada encima",
    ai: { op: "add_stacked_unit", decode: decodeModule },
  },
  {
    id: "module.copy-spec",
    title: "cmd.copySpec",
    keywords: ["copiar", "especificación", "propiedades", "formato"],
    shortcut: "mod+shift+c",
    applicable: (ctx) => selectedModuleScope(ctx) !== null && ctx.writeSpecClipboard !== undefined,
    run: (ctx) => {
      const module = selectedModuleScope(ctx);
      if (module) ctx.writeSpecClipboard?.({ kind: "module", tree: module.tree });
    },
  },
  {
    id: "module.apply-spec",
    title: "cmd.applySpec",
    keywords: ["aplicar", "pegar", "especificación", "propiedades", "formato"],
    shortcut: "mod+shift+v",
    applicable: (ctx) => selectedModuleScope(ctx) !== null && ctx.specClipboard?.kind === "module",
    apply: (ctx) => {
      const module = selectedModuleScope(ctx);
      const clipboard = ctx.specClipboard;
      return module && clipboard?.kind === "module"
        ? setModuleTree(ctx.product, module.id, structuredClone(clipboard.tree))
        : ctx.product;
    },
    describe: () => "aplicar estructura copiada",
  },
  {
    id: "bay.copy-spec",
    title: "cmd.copyBaySpec",
    keywords: ["copiar", "especificación", "vano", "apertura", "vidrio", "hoja"],
    shortcut: "mod+shift+c",
    applicable: (ctx) => selectedBayTarget(ctx) !== null && ctx.writeSpecClipboard !== undefined,
    run: (ctx) => {
      const target = selectedBayTarget(ctx);
      if (target) ctx.writeSpecClipboard?.({ kind: "bay", spec: baySpec(target.node) });
    },
  },
  {
    id: "bay.apply-spec",
    title: "cmd.applyBaySpec",
    keywords: ["aplicar", "pegar", "especificación", "vano", "apertura", "vidrio"],
    shortcut: "mod+shift+v",
    applicable: (ctx) => selectedBayTarget(ctx) !== null && ctx.specClipboard?.kind === "bay",
    apply: (ctx) => {
      const target = selectedBayTarget(ctx);
      const clipboard = ctx.specClipboard;
      return target && clipboard?.kind === "bay"
        ? copyBaySpec(ctx.product, target.module.id, target.node.id, clipboard.spec)
        : ctx.product;
    },
    describe: () => "aplicar especificación de vano",
  },
  {
    id: "coupling.insert-module",
    title: "cmd.insertModule",
    // No "dividir" keyword: this inserts a whole new unit — under a divide
    // search it impersonates the in-place bay split (designer report P1-7).
    keywords: ["insertar", "unidad", "entre", "agregar"],
    applicable: (ctx) => {
      const coupling = selectedCoupling(ctx);
      return coupling !== null && (coupling.kind ?? "INLINE") === "INLINE";
    },
    apply: (ctx, args) => {
      const coupling = couplingTarget(ctx, args);
      return coupling ? insertModuleBetween(ctx.product, coupling.id) : ctx.product;
    },
    postCommit: (ctx, before, next) => {
      const created = createdModule(before, next);
      if (created) ctx.select(created);
    },
    describe: () => "insertar unidad en la unión",
    ai: { op: "insert_module", decode: decodeCoupling },
  },
  {
    id: "coupling.disconnect",
    title: "cmd.disconnectCoupling",
    keywords: ["desconectar", "quitar unión", "separar", "acoplamiento"],
    applicable: (ctx) => selectedCoupling(ctx) !== null,
    apply: (ctx, args) => {
      const coupling = couplingTarget(ctx, args);
      return coupling ? unlinkCoupling(ctx.product, coupling.id) : ctx.product;
    },
    postCommit: (ctx, _before, next) => {
      if (
        ctx.selection &&
        !next.assembly.couplings.some((coupling) => coupling.id === ctx.selection)
      ) {
        ctx.select(null);
      }
    },
    describe: () => "desconectar unión",
    ai: { op: "remove_coupling", decode: decodeCoupling },
  },
  {
    id: "coupling.set-kind",
    title: "cmd.couplingKind",
    keywords: ["tipo", "unión", "inline", "stacked", "tee", "corner", "esquina", "codo"],
    applicable: (ctx) => {
      const coupling = selectedCoupling(ctx);
      return coupling !== null && allowedCouplingKinds(ctx.product, coupling.id).length > 1;
    },
    params: (ctx) => {
      const coupling = selectedCoupling(ctx);
      const kinds = coupling ? allowedCouplingKinds(ctx.product, coupling.id) : [];
      return [
        {
          kind: "choice",
          id: "kind",
          label: t("cmd.couplingKindLabel"),
          options: kinds.map((value) => ({
            value,
            label: t(
              (
                {
                  INLINE: "assembly.kindInline",
                  STACKED: "assembly.kindStacked",
                  TEE: "assembly.kindTee",
                  CORNER: "assembly.kindCorner",
                } as const
              )[value],
            ),
          })),
        },
      ];
    },
    apply: (ctx, args) => {
      const coupling = couplingTarget(ctx, args);
      const kind = args.kind;
      return coupling && kind
        ? setCouplingKind(ctx.product, coupling.id, kind as "STACKED" | "TEE" | "CORNER" | "INLINE")
        : ctx.product;
    },
    describe: (args) => `unión ${args.target ?? "?"}: ${args.kind ?? "?"}`,
    ai: {
      op: "set_coupling_kind",
      decode: (op, product, state) => {
        const kind = text(op.kind);
        return kind ? decodeCoupling(op, product, state, { kind }) : null;
      },
    },
  },
  {
    id: "bay.remove",
    title: "cmd.removeBay",
    keywords: ["quitar", "eliminar", "vano", "hoja"],
    applicable: (ctx) => {
      const target = selectedBayTarget(ctx);
      return target !== null && parentSplitOf(target.module.tree, target.node.id) !== null;
    },
    apply: (ctx, args) => {
      const target = bayTarget(ctx, args);
      return target ? removeModuleBay(ctx.product, target.module.id, target.node.id) : ctx.product;
    },
    postCommit: (ctx, _before, _next, args) => {
      const target = bayTarget(ctx, args);
      if (!target) return;
      const parent = parentSplitOf(target.module.tree, target.node.id);
      const sibling = (parent?.children ?? []).find((child) => child.id !== target.node.id)?.id;
      ctx.select(sibling ? `${target.module.id}/${sibling}` : target.module.id);
    },
    describe: () => "quitar vano",
  },
  {
    id: "split.remove",
    title: "cmd.removeSplit",
    keywords: ["quitar", "eliminar", "división", "montante", "travesaño", "mullion", "transom"],
    applicable: (ctx) => {
      const target = selectedSplit(ctx);
      return (
        target !== null && canRemoveModuleDivision(ctx.product, target.module.id, target.node.id)
      );
    },
    apply: (ctx, args) => {
      const target = splitTarget(ctx, args);
      return target
        ? removeModuleDivision(ctx.product, target.module.id, target.node.id)
        : ctx.product;
    },
    postCommit: (ctx, _before, _next, args) => {
      const target = splitTarget(ctx, args);
      if (!target) return;
      const kept = target.node.children?.[0]?.id;
      ctx.select(kept ? `${target.module.id}/${kept}` : target.module.id);
    },
    describe: () => "quitar división",
  },
  {
    id: "edit.remove",
    title: "cmd.removeSelection",
    keywords: ["eliminar", "quitar", "borrar"],
    shortcut: "del",
    mutates: true,
    applicable: (ctx) =>
      (selectedModule(ctx) !== null && ctx.product.assembly.modules.length > 1) ||
      selectedCoupling(ctx) !== null ||
      selectedSplit(ctx) !== null ||
      (selectedBayTarget(ctx) !== null &&
        parentSplitOf(selectedBayTarget(ctx)!.module.tree, selectedBayTarget(ctx)!.node.id) !==
          null),
    run: (ctx) => {
      const dispatch = (specId: string, args: CommandArgs): void => {
        const spec = ASSEMBLY_COMMANDS.find((item) => item.id === specId);
        if (spec) runCommand(ctx, spec, args);
      };
      const split = selectedSplit(ctx);
      if (split) {
        dispatch("split.remove", { module: split.module.id, division: split.node.id });
        return;
      }
      const coupling = selectedCoupling(ctx);
      if (coupling) {
        dispatch("coupling.disconnect", { coupling: coupling.id });
        return;
      }
      const bay = selectedBayTarget(ctx);
      if (bay && parentSplitOf(bay.module.tree, bay.node.id)) {
        dispatch("bay.remove", { module: bay.module.id, bay: bay.node.id });
        return;
      }
      const module = selectedModule(ctx);
      if (module && ctx.product.assembly.modules.length > 1) {
        dispatch("module.remove", { module: module.id });
      }
    },
    describe: () => "eliminar selección",
  },
  {
    id: "edit.deselect",
    title: "cmd.deselect",
    keywords: ["deseleccionar", "cancelar", "escape"],
    shortcut: "esc",
    applicable: (ctx) => ctx.selection !== null && ctx.selection !== "",
    run: (ctx) => ctx.select(null),
    describe: () => "deseleccionar",
  },
  {
    id: "edit.repeat",
    title: "cmd.repeatLast",
    keywords: ["repetir", "último", "otra vez"],
    shortcut: "mod+shift+d",
    mutates: true,
    applicable: (ctx) =>
      ctx.lastMutation !== null &&
      ctx.lastMutation !== undefined &&
      ASSEMBLY_COMMANDS.some(
        (spec) => spec.id === ctx.lastMutation?.specId && (spec.applicable?.(ctx) ?? true),
      ),
    run: (ctx) => {
      const spec = ASSEMBLY_COMMANDS.find((item) => item.id === ctx.lastMutation?.specId);
      if (spec && ctx.lastMutation) runCommand(ctx, spec, ctx.lastMutation.args);
    },
  },
  {
    id: "edit.undo",
    title: "cmd.undo",
    keywords: ["deshacer", "volver"],
    shortcut: "mod+z",
    mutates: true,
    applicable: (ctx) => ctx.canUndo === true,
    run: (ctx) => ctx.undo?.(),
  },
  {
    id: "edit.redo",
    title: "cmd.redo",
    keywords: ["rehacer", "adelante"],
    shortcut: ["mod+shift+z", "mod+y"],
    mutates: true,
    applicable: (ctx) => ctx.canRedo === true,
    run: (ctx) => ctx.redo?.(),
  },
  {
    id: "tool.select",
    title: "cmd.selectTool",
    keywords: ["seleccionar", "cursor", "herramienta"],
    shortcut: "v",
    run: (ctx) => ctx.setTool?.("select"),
  },
  {
    id: "tool.split-vertical",
    title: "cmd.splitVertical",
    keywords: ["dividir", "partir", "vertical", "montante", "mullion"],
    shortcut: "m",
    applicable: (ctx) => ctx.catalog.mullionSkus.SPLIT_V !== undefined,
    run: (ctx) => ctx.setTool?.("split_v"),
  },
  {
    id: "tool.split-horizontal",
    title: "cmd.splitHorizontal",
    keywords: ["dividir", "partir", "horizontal", "travesaño", "transom"],
    shortcut: "t",
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

/** Human controls emit the same discriminated intent that the AI proposes.
 * Legacy pure handlers remain readers for historical stored proposals. */
export function commandOperations(
  spec: CommandSpec,
  ctx: CommandContext,
  args: CommandArgs,
): DesignOperationRequest[] | null {
  const module = moduleTarget(ctx, args);
  const coupling = couplingTarget(ctx, args);
  const name = spec.ai?.op;
  let intent: Record<string, unknown> | null = null;
  if (name === "add_unit") intent = { op: name, side: spec.id.endsWith("left") ? "left" : "right" };
  else if (name === "set_module_count") intent = { op: name, count: Number(args.count) };
  else if (name === "set_height") intent = { op: name, height_mm: normalizeMm(args.height ?? "") };
  else if (name === "set_total_width")
    intent = { op: name, width_mm: normalizeMm(args.width ?? "") };
  else if (name === "set_module_width" && module)
    intent = { op: name, module: module.id, width_mm: normalizeMm(args.width ?? "") };
  else if (name === "set_opening" && module && args.opening) {
    const patch = args.opening.startsWith("{")
      ? structuredOpeningPatch(JSON.parse(args.opening))
      : null;
    intent = patch?.opening
      ? {
          op: name,
          module: module.id,
          bay: modulePrimaryBay(module)?.id,
          opening: patch.opening,
          opening_use: patch.opening_use,
          hinged_layout: patch.hinged_layout,
          sliding_layout: patch.sliding_layout,
        }
      : { op: name, module: module.id, opening: args.opening };
  } else if (name === "set_glass" && module)
    intent = { op: name, module: module.id, sku: args.glass };
  else if (name === "set_glass_thickness" && module)
    intent = { op: name, module: module.id, mm: args.thickness };
  else if (name === "set_panel" && module)
    intent = { op: name, module: module.id, sku: args.panel || null };
  else if (["equalize_widths", "equalize_angles"].includes(name ?? "")) intent = { op: name };
  else if (["duplicate_module", "add_stacked_unit", "remove_unit"].includes(name ?? "") && module)
    intent = { op: name, module: module.id };
  else if (["insert_module", "remove_coupling"].includes(name ?? "") && coupling)
    intent = { op: name, coupling: coupling.id };
  else if (name === "set_coupling_angle" && coupling)
    intent = { op: name, coupling: coupling.id, angle_deg: normalizeAngle(args.angle ?? "") };
  else if (name === "set_coupling_kind" && coupling)
    intent = { op: name, coupling: coupling.id, kind: args.kind };
  else if (spec.id === "module.clear-panel" && module)
    intent = { op: "set_panel", module: module.id, sku: null };
  else if (spec.id === "split.remove") {
    const target = splitTarget(ctx, args);
    if (target)
      intent = { op: "remove_divider", module: target.module.id, divider: target.node.id };
  } else if (spec.id === "bay.remove") {
    const target = bayTarget(ctx, args);
    const parent = target ? parentSplitOf(target.module.tree, target.node.id) : null;
    const sibling = parent?.children?.find((child) => child.id !== target?.node.id);
    if (target && parent && sibling)
      intent = {
        op: "remove_divider",
        module: target.module.id,
        divider: parent.id,
        keep_bay: sibling.id,
      };
  } else if (spec.id === "product.straighten") {
    return ctx.product.assembly.couplings.map((item) => ({
      op: "set_coupling_angle",
      coupling: item.id,
      angle_deg: "0",
    }));
  } else if (spec.id === "coupling.clear-angle" && coupling)
    intent = { op: "set_coupling_angle", coupling: coupling.id, angle_deg: "0" };
  return intent ? [intent as unknown as DesignOperationRequest] : null;
}

for (const spec of ASSEMBLY_COMMANDS) {
  if (
    spec.ai ||
    [
      "module.clear-panel",
      "split.remove",
      "bay.remove",
      "product.straighten",
      "coupling.clear-angle",
    ].includes(spec.id)
  ) {
    spec.operation = (ctx, args) => commandOperations(spec, ctx, args);
  }
}

/** Commands the surface offers right now (selection/product-sensitive). */
export function assemblyCommands(ctx: CommandContext): CommandSpec[] {
  if (ctx.disabled) return [];
  const domain = ASSEMBLY_COMMANDS.filter((spec) => spec.applicable?.(ctx) ?? true);
  return ctx.focusAssistant ? [...domain, UI_ASK_ASSISTANT] : domain;
}
