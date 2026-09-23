import { expect, it, vi } from "vitest";

import { resolveCommands } from "../commands/registry";
import type { CommandContext } from "../commands/types";
import { assemblyCommands } from "./assemblyCommands";
import { makeBowProduct, modulePrimaryBay, type ProductJson } from "./productEditing";

function harness(
  product: ProductJson,
  selection: string | null = null,
  options: {
    glassThicknesses?: string[];
    glassSkus?: string[];
    couplerSkus?: string[];
    panelSkus?: string[];
    mullionSkus?: Partial<Record<"SPLIT_V" | "SPLIT_H", string>>;
    canUndo?: boolean;
    canRedo?: boolean;
  } = {},
) {
  const commit = vi.fn();
  const select = vi.fn();
  const setTool = vi.fn();
  const undo = vi.fn();
  const redo = vi.fn();
  const ctx: CommandContext = {
    product,
    selection,
    catalog: {
      glassThicknesses: options.glassThicknesses ?? [],
      glassSkus: options.glassSkus ?? [],
      couplerSkus: options.couplerSkus ?? [],
      panelSkus: options.panelSkus ?? [],
      mullionSkus: options.mullionSkus ?? {},
    },
    disabled: false,
    commit,
    select,
    setTool,
    undo,
    redo,
    canUndo: options.canUndo,
    canRedo: options.canRedo,
  };
  const commands = resolveCommands(ctx, assemblyCommands(ctx));
  return { commands, commit, select, setTool, undo, redo };
}

function byId(commands: ReturnType<typeof harness>["commands"], id: string) {
  const command = commands.find((item) => item.id === id);
  expect(command, `expected command ${id}`).toBeTruthy();
  return command!;
}

it("always offers composition commands", () => {
  const { commands, commit } = harness(
    makeBowProduct({ moduleCount: 2, widthMm: 1200, heightMm: 1400, angleDeg: 15 }),
  );
  byId(commands, "product.add-right").run({});
  const next = commit.mock.calls[0]![0] as ProductJson;
  expect(next.assembly.modules).toHaveLength(3);
});

it("gates destructive and selection-scoped commands", () => {
  const single = makeBowProduct({ moduleCount: 1, widthMm: 900, heightMm: 1200, angleDeg: 0 });
  // Nothing selected on a single unit: no remove, no module-scoped setters.
  let { commands } = harness(single);
  expect(commands.find((item) => item.id === "module.remove")).toBeUndefined();
  // Equalizing a single unit can never change the product — don't offer it.
  expect(commands.find((item) => item.id === "product.equalize-widths")).toBeUndefined();
  expect(commands.find((item) => item.id === "module.set-width")).toBeUndefined();
  expect(commands.find((item) => item.id === "coupling.set-angle")).toBeUndefined();
  // A straight assembly offers no straighten/clear-angle.
  expect(commands.find((item) => item.id === "product.straighten")).toBeUndefined();

  const bow = makeBowProduct({ moduleCount: 3, widthMm: 2100, heightMm: 1400, angleDeg: 20 });
  // A selected module unlocks module commands.
  ({ commands } = harness(bow, "m2", { glassThicknesses: ["4.00"], couplerSkus: ["CPL-A"] }));
  expect(byId(commands, "module.remove")).toBeTruthy();
  expect(byId(commands, "product.equalize-widths")).toBeTruthy();
  expect(byId(commands, "product.equalize-angles")).toBeTruthy();
  const widthParam = byId(commands, "module.set-width").params?.[0];
  expect(widthParam?.kind === "number" ? widthParam.defaultValue : null).toBe(
    bow.assembly.modules[1]!.width_mm,
  );
  // Coupling commands stay hidden until a coupling is selected.
  expect(commands.find((item) => item.id === "coupling.set-angle")).toBeUndefined();
  expect(commands.find((item) => item.id === "coupling.set-coupler")).toBeUndefined();

  ({ commands } = harness(bow, "c1", { couplerSkus: ["CPL-A", "CPL-B"] }));
  expect(byId(commands, "coupling.set-angle")).toBeTruthy();
  expect(byId(commands, "coupling.set-coupler").params?.[0]).toMatchObject({ kind: "choice" });
  // Nonzero angles on a bow offer straighten.
  expect(byId(commands, "product.straighten")).toBeTruthy();
});

it("commits typed mutations with collected args", () => {
  const product = makeBowProduct({ moduleCount: 3, widthMm: 2100, heightMm: 1400, angleDeg: 10 });
  const { commands, commit } = harness(product, "m1");
  byId(commands, "module.set-width").run({ width: "750" });
  const widened = commit.mock.calls[0]![0] as ProductJson;
  expect(widened.assembly.modules[0]!.width_mm).toBe("750.00");

  byId(commands, "module.set-opening").run({ opening: "TURN_LEFT" });
  const opened = commit.mock.calls[1]![0] as ProductJson;
  expect(modulePrimaryBay(opened.assembly.modules[0]!)?.opening_type).toBe("TURN_LEFT");
});

it("applies wire angles at the inclusive ±90° bound the contract accepts", async () => {
  const { applyDesignOps } = await import("./designOps");
  const product = makeBowProduct({ moduleCount: 3, widthMm: 2100, heightMm: 1400, angleDeg: 10 });
  const next = applyDesignOps(product, [
    { op: "set_coupling_angle", coupling: 0, angle_deg: "90" },
    { op: "set_coupling_angle", coupling: 1, angle_deg: "-90" },
  ]);
  expect(next.assembly.couplings[0]!.angle_deg).toBe("90.0");
  expect(next.assembly.couplings[1]!.angle_deg).toBe("-90.0");
});

it("refuses to mint a thirteenth module — cap is shared with the contract", async () => {
  const { applyDesignOps } = await import("./designOps");
  const full = makeBowProduct({ moduleCount: 12, widthMm: 8400, heightMm: 1400, angleDeg: 0 });
  const { commands, commit } = harness(full);
  expect(commands.find((item) => item.id === "product.add-right")).toBeUndefined();
  expect(commands.find((item) => item.id === "product.add-left")).toBeUndefined();
  // Even a direct wire dispatch cannot exceed the bound.
  const next = applyDesignOps(full, [{ op: "add_unit", side: "right" }]);
  expect(next.assembly.modules).toHaveLength(12);
  // …and neither can set_module_count through the same registry.
  expect(
    applyDesignOps(full, [{ op: "set_module_count", count: 13 }]).assembly.modules,
  ).toHaveLength(12);
  expect(commit).not.toHaveBeenCalled();
});

it("dispatches AI wire ops through the same command apply as the palette", async () => {
  const { applyDesignOps } = await import("./designOps");
  const product = makeBowProduct({ moduleCount: 3, widthMm: 2100, heightMm: 1400, angleDeg: 10 });
  // The wire path decodes module index 0 → its id and calls the same spec
  // `apply` a palette run commits.
  const viaOp = applyDesignOps(product, [{ op: "set_module_width", module: 0, width_mm: "750" }]);
  const { commands, commit } = harness(product, "m1");
  byId(commands, "module.set-width").run({ width: "750" });
  const viaPalette = commit.mock.calls[0]![0] as ProductJson;
  expect(viaOp).toEqual(viaPalette);
});

it("arms the divide tools and drives history without a product mutation", () => {
  const product = makeBowProduct({ moduleCount: 1, widthMm: 900, heightMm: 1200, angleDeg: 0 });
  const { commands, setTool, undo, commit } = harness(product, null, {
    mullionSkus: { SPLIT_V: "MULL-V", SPLIT_H: "MULL-H" },
    canUndo: true,
  });
  byId(commands, "tool.split-vertical").run({});
  expect(setTool).toHaveBeenCalledWith("split_v");
  byId(commands, "edit.undo").run({});
  expect(undo).toHaveBeenCalled();
  expect(commit).not.toHaveBeenCalled();
  // No undo available → no undo row.
  const { commands: fresh } = harness(product, null, { canUndo: false });
  expect(fresh.find((item) => item.id === "edit.undo")).toBeUndefined();
});

it("hides every command while editing is disabled", () => {
  const product = makeBowProduct({ moduleCount: 2, widthMm: 1200, heightMm: 1400, angleDeg: 15 });
  const commit = vi.fn();
  const ctx: CommandContext = {
    product,
    selection: null,
    catalog: {
      glassThicknesses: [],
      glassSkus: [],
      couplerSkus: [],
      panelSkus: [],
      mullionSkus: {},
    },
    disabled: true,
    commit,
    select: vi.fn(),
  };
  expect(assemblyCommands(ctx)).toHaveLength(0);
});
