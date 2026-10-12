import { describe, expect, it, vi } from "vitest";
import type { DesignOperation } from "../../api/generated/models";
import type { CommandContext } from "../commands/types";
import { resolveCommands } from "../commands/registry";
import { ASSEMBLY_COMMANDS } from "./assemblyCommands";
import { applyOperationEffects, productFingerprint } from "./designOps";
import { bayOperations, slidingOperation } from "./operationIntents";
import { makeBowProduct } from "./productEditing";

function product() {
  return makeBowProduct({ moduleCount: 1, widthMm: 1200, heightMm: 1400, angleDeg: 0 });
}

describe("live operation effects", () => {
  it("applies the exact server graph and refuses intent-only operations", () => {
    const before = product();
    const after = structuredClone(before);
    after.assembly.modules[0]!.width_mm = "1700.00";
    const intent: DesignOperation = {
      op: "set_module_width",
      module: before.assembly.modules[0]!.id,
      width_mm: "1700",
    };
    expect(() => applyOperationEffects(before, [intent])).toThrow("operation_effect_required");
    const effect = { ...intent, base_sig: productFingerprint(before), result: after };
    expect(applyOperationEffects(before, [effect])).toBe(after);
    expect(before.assembly.modules[0]!.width_mm).toBe("1200.00");
    const changed = structuredClone(before);
    changed.assembly.modules[0]!.tree.glass_article_sku = "ANOTHER";
    expect(() => applyOperationEffects(changed, [effect])).toThrow("proposal_stale");
  });

  it("refuses a broken effect sequence atomically", () => {
    const before = product();
    const after = structuredClone(before);
    const effect: DesignOperation = {
      op: "set_height",
      height_mm: "1400",
      base_sig: productFingerprint(before),
      result: after,
    };
    expect(() =>
      applyOperationEffects(before, [effect, { ...effect, base_sig: "outdated" }]),
    ).toThrow("proposal_stale");
    expect(before).toEqual(product());
  });

  it("routes palette commands to simulation without local geometry arithmetic", () => {
    const before = product();
    const simulate = vi.fn();
    const commit = vi.fn();
    const context: CommandContext = {
      product: before,
      selection: before.assembly.modules[0]!.id,
      disabled: false,
      catalog: {
        glassThicknesses: [],
        glassSkus: [],
        couplerSkus: [],
        panelSkus: [],
        mullionSkus: {},
      },
      simulate,
      commit,
      select: vi.fn(),
    };
    const command = resolveCommands(context, ASSEMBLY_COMMANDS).find(
      (row) => row.id === "module.set-width",
    )!;
    command.run({ width: "1700" });
    expect(simulate).toHaveBeenCalledWith(
      [{ op: "set_module_width", module: before.assembly.modules[0]!.id, width_mm: "1700.00" }],
      expect.anything(),
      { width: "1700" },
    );
    expect(commit).not.toHaveBeenCalled();
    expect(ASSEMBLY_COMMANDS.filter((spec) => spec.apply).every((spec) => spec.operation)).toBe(
      true,
    );
  });

  it("emits the generated glass and sliding intent contracts without derived thickness", () => {
    expect(
      bayOperations("m", "b", { glass_article_sku: "REAL-GLASS", glass_thickness_mm: "24" }),
    ).toEqual([{ op: "set_glass", module: "m", bay: "b", sku: "REAL-GLASS" }]);
    expect(
      slidingOperation("m", "b", {
        tracks: 2,
        panels: [
          { slot: "1", kind: "MOVING", track: 0 },
          { slot: "2", kind: "MOVING", track: 1 },
        ],
      }),
    ).toEqual({
      op: "set_sliding_layout",
      module: "m",
      bay: "b",
      tracks: 2,
      panels: "XX",
      panel_tracks: [0, 1],
      panel_travel: ["RIGHT", "LEFT"],
    });
  });
});
