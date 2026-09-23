// frontend/src/features/canvas/assemblyCommands.test.ts
import { expect, it, vi } from "vitest";

import { assemblyCommands } from "./assemblyCommands";
import { makeBowProduct, modulePrimaryBay, type ProductJson } from "./productEditing";

function harness(
  product: ProductJson,
  selection = "",
  options: { glassThicknesses?: string[]; glassSkus?: string[]; couplerSkus?: string[] } = {},
) {
  const commit = vi.fn();
  const select = vi.fn();
  const commands = assemblyCommands({
    product,
    selection,
    commit,
    select,
    glassThicknesses: options.glassThicknesses ?? [],
    glassSkus: options.glassSkus ?? [],
    couplerSkus: options.couplerSkus ?? [],
  });
  return { commands, commit, select };
}

function byId(commands: ReturnType<typeof assemblyCommands>, id: string) {
  const command = commands.find((item) => item.id === id);
  expect(command, `expected command ${id}`).toBeTruthy();
  return command!;
}

it("always offers composition commands and selects the added unit", () => {
  const { commands, commit, select } = harness(
    makeBowProduct({ moduleCount: 2, widthMm: 1200, heightMm: 1400, angleDeg: 15 }),
  );
  byId(commands, "module.add-right").run({});
  const next = commit.mock.calls[0]![0] as ProductJson;
  expect(next.assembly.modules).toHaveLength(3);
  expect(select).toHaveBeenCalledWith("m3");
});

it("gates destructive and selection-scoped commands", () => {
  const single = makeBowProduct({ moduleCount: 1, widthMm: 900, heightMm: 1200, angleDeg: 0 });
  // Nothing selected on a single unit: no remove, no module-scoped setters.
  let { commands } = harness(single);
  expect(commands.find((item) => item.id === "module.remove")).toBeUndefined();
  expect(commands.find((item) => item.id === "module.set-width")).toBeUndefined();
  expect(commands.find((item) => item.id === "coupling.set-angle")).toBeUndefined();

  const bow = makeBowProduct({ moduleCount: 3, widthMm: 2100, heightMm: 1400, angleDeg: 20 });
  // A selected module unlocks module commands.
  ({ commands } = harness(bow, "m2", { glassThicknesses: ["4.00"], couplerSkus: ["CPL-A"] }));
  expect(byId(commands, "module.remove")).toBeTruthy();
  const widthParam = byId(commands, "module.set-width").params?.[0];
  expect(widthParam?.kind === "number" ? widthParam.defaultValue : null).toBe(
    bow.assembly.modules[1]!.width_mm,
  );
  // Coupling commands stay hidden until a coupling is selected.
  expect(commands.find((item) => item.id === "coupling.set-angle")).toBeUndefined();
  // Coupler choice is offered for couplings, not modules.
  expect(commands.find((item) => item.id === "coupling.set-coupler")).toBeUndefined();

  ({ commands } = harness(bow, "c1", { couplerSkus: ["CPL-A", "CPL-B"] }));
  expect(byId(commands, "coupling.set-angle")).toBeTruthy();
  expect(byId(commands, "coupling.set-coupler").params?.[0]).toMatchObject({
    kind: "choice",
  });
});

it("commits typed mutations with collected args", () => {
  const product = makeBowProduct({ moduleCount: 3, widthMm: 2100, heightMm: 1400, angleDeg: 10 });
  const { commands, commit } = harness(product, "m1");
  byId(commands, "module.set-width").run({ width: "750" });
  const widened = commit.mock.calls[0]![0] as ProductJson;
  expect(widened.assembly.modules[0]!.width_mm).toBe("750");

  byId(commands, "module.set-opening").run({ opening: "TURN_LEFT" });
  const opened = commit.mock.calls[1]![0] as ProductJson;
  expect(modulePrimaryBay(opened.assembly.modules[0]!)?.opening_type).toBe("TURN_LEFT");
});
