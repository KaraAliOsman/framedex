import { t } from "../../i18n/es-CL";
import type { CommandDefinition } from "../commands/types";
import type { Opening } from "./intentEditing";
import { OPENING_OPTIONS } from "./openings";
import {
  addAdjacentUnit,
  equalizeCouplingAngles,
  equalizeModuleWidths,
  moduleGlassThicknessMm,
  modulePanelSku,
  removeUnit,
  setAllModuleHeights,
  setCouplerSku,
  setCouplingAngle,
  setModuleGlass,
  setModuleGlassThickness,
  setModuleOpening,
  setModulePanel,
  setModuleWidth,
  type ProductJson,
} from "./productEditing";

/** Same presentation rules as the canvas DraftFields: positive dimensions
 * commit at 0.01mm, joint angles stay strictly inside ±90° at 0.1°. */
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

/** Editor commands for the Ctrl+K palette. Every definition captures the live
 * product/selection/commit; `available` is folded into the list itself — the
 * caller rebuilds it whenever those inputs change, so the palette only lists
 * commands that would actually run. Same shape an AI agent would call. */
export function assemblyCommands({
  product,
  selection,
  commit,
  select,
  glassThicknesses,
  glassSkus,
  couplerSkus,
}: {
  product: ProductJson;
  selection: string;
  commit(next: ProductJson): void;
  select(id: string | null): void;
  glassThicknesses: string[];
  glassSkus: string[];
  couplerSkus: string[];
}): CommandDefinition[] {
  const modules = product.assembly.modules;
  const couplings = product.assembly.couplings;
  const selectedModule = modules.find((module) => module.id === selection) ?? null;
  const selectedCoupling = couplings.find((coupling) => coupling.id === selection) ?? null;

  function addUnit(side: "left" | "right"): void {
    const next = addAdjacentUnit(product, side);
    commit(next);
    select(
      next.assembly.modules[side === "left" ? 0 : next.assembly.modules.length - 1]?.id ?? null,
    );
  }

  const commands: CommandDefinition[] = [
    {
      id: "module.add-right",
      title: t("cmd.addUnitRight"),
      keywords: ["añadir", "unidad", "vano", "hoja", "derecha", "modulo"],
      run: () => addUnit("right"),
    },
    {
      id: "module.add-left",
      title: t("cmd.addUnitLeft"),
      keywords: ["añadir", "unidad", "vano", "hoja", "izquierda", "modulo"],
      run: () => addUnit("left"),
    },
    {
      id: "product.set-height",
      title: t("cmd.setHeight"),
      keywords: ["alto", "altura", "dimensiones"],
      params: [
        {
          kind: "number",
          id: "height",
          label: t("cmd.heightLabel"),
          unit: "mm",
          defaultValue: modules[0]?.height_mm,
          validate: normalizeMm,
        },
      ],
      run: (args) => commit(setAllModuleHeights(product, args.height ?? "")),
    },
  ];

  if (modules.length > 1) {
    commands.push({
      id: "module.equalize-widths",
      title: t("cmd.equalizeWidths"),
      keywords: ["igualar", "anchos", "unidades", "repartir"],
      describe: () => t("cmd.equalizeWidthsDesc"),
      run: () => commit(equalizeModuleWidths(product)),
    });
  }
  if (couplings.length > 1) {
    commands.push({
      id: "product.equalize-angles",
      title: t("cmd.equalizeAngles"),
      keywords: ["igualar", "ángulos", "angulos", "acoplamiento", "bow"],
      describe: () => t("cmd.equalizeAnglesDesc"),
      run: () => commit(equalizeCouplingAngles(product)),
    });
  }

  if (selectedModule && modules.length > 1) {
    commands.push({
      id: "module.remove",
      title: t("cmd.removeUnit"),
      keywords: ["eliminar", "quitar", "unidad", "vano", "hoja", "modulo"],
      run: () => commit(removeUnit(product, selectedModule.id)),
    });
  }
  if (selectedModule) {
    commands.push(
      {
        id: "module.set-width",
        title: t("cmd.setWidth"),
        keywords: ["ancho", "unidad", "dimensiones"],
        params: [
          {
            kind: "number",
            id: "width",
            label: t("cmd.widthLabel"),
            unit: "mm",
            defaultValue: selectedModule.width_mm,
            validate: normalizeMm,
          },
        ],
        run: (args) => commit(setModuleWidth(product, selectedModule.id, args.width ?? "")),
      },
      {
        id: "module.set-opening",
        title: t("cmd.setOpening"),
        keywords: ["apertura", "hoja", "fijo", "oscilobatiente", "puerta"],
        params: [
          {
            kind: "choice",
            id: "opening",
            label: t("cmd.openingLabel"),
            options: OPENING_OPTIONS.map(([value, key]) => ({ value, label: t(key) })),
          },
        ],
        run: (args) =>
          commit(setModuleOpening(product, selectedModule.id, args.opening as Opening)),
      },
    );
    if (glassThicknesses.length > 0) {
      commands.push({
        id: "module.set-glass-thickness",
        title: t("cmd.setGlassThickness"),
        keywords: ["vidrio", "espesor", "dvh"],
        params: [
          {
            kind: "choice",
            id: "thickness",
            label: t("cmd.glassThicknessLabel"),
            options: glassThicknesses.map((value) => ({ value, label: `${value} mm` })),
          },
        ],
        run: (args) =>
          commit(setModuleGlassThickness(product, selectedModule.id, args.thickness ?? null)),
      });
    }
    if (glassSkus.length > 0) {
      commands.push({
        id: "module.set-glass",
        title: t("cmd.setGlass"),
        keywords: ["vidrio", "composicion", "composición", "artículo"],
        params: [
          {
            kind: "choice",
            id: "glass",
            label: t("cmd.glassLabel"),
            options: glassSkus.map((value) => ({ value, label: value })),
          },
        ],
        run: (args) => commit(setModuleGlass(product, selectedModule.id, args.glass ?? null)),
      });
    }
    if (modulePanelSku(selectedModule) !== null) {
      commands.push({
        id: "module.clear-panel",
        title: t("cmd.clearPanel"),
        keywords: ["panel", "quitar", "eliminar"],
        run: () => commit(setModulePanel(product, selectedModule.id, null)),
      });
    }
    if (moduleGlassThicknessMm(selectedModule) !== null) {
      commands.push({
        id: "module.clear-glass-thickness",
        title: t("cmd.clearGlassThickness"),
        keywords: ["vidrio", "espesor", "quitar"],
        run: () => commit(setModuleGlassThickness(product, selectedModule.id, null)),
      });
    }
  }
  if (selectedCoupling) {
    commands.push(
      {
        id: "coupling.set-angle",
        title: t("cmd.setAngle"),
        keywords: ["ángulo", "angulo", "acoplamiento", "unión", "plano"],
        params: [
          {
            kind: "number",
            id: "angle",
            label: t("cmd.angleLabel"),
            unit: "°",
            defaultValue: selectedCoupling.angle_deg,
            validate: normalizeAngle,
          },
        ],
        describe: (args) =>
          Number(args.angle ?? "0") === 0 ? t("cmd.setAngleStraightDesc") : t("cmd.setAngleDesc"),
        run: (args) => commit(setCouplingAngle(product, selectedCoupling.id, args.angle ?? "0")),
      },
      {
        id: "coupling.clear-angle",
        title: t("cmd.clearAngle"),
        keywords: ["ángulo", "angulo", "recto", "cero", "acoplamiento"],
        run: () => commit(setCouplingAngle(product, selectedCoupling.id, "0")),
      },
    );
    if (couplerSkus.length > 0) {
      commands.push({
        id: "coupling.set-coupler",
        title: t("cmd.setCoupler"),
        keywords: ["cople", "acoplador", "perfil", "acoplamiento"],
        params: [
          {
            kind: "choice",
            id: "coupler",
            label: t("cmd.couplerLabel"),
            options: couplerSkus.map((value) => ({ value, label: value })),
          },
        ],
        run: (args) => commit(setCouplerSku(product, selectedCoupling.id, args.coupler ?? null)),
      });
    }
  }
  return commands;
}
