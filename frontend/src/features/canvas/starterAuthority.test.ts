import { expect, it } from "vitest";
import type { DesignOptions } from "../../api/generated/models";
import { STARTER_DEFINITIONS } from "./designLibrary";
import { sourcedStarter } from "./starterAuthority";

it("new bow recipes resolve each declared inward opening without choosing a kit", () => {
  const options = {
    opening_capabilities: [
      {
        use: "WINDOW",
        movement: "TURN",
        direction: "INWARD",
        leaf_role: "SINGLE",
        fixed_in_sash: false,
        hinge_sides: ["LEFT", "RIGHT"],
        hardware_kit_skus: ["CLASS-A", "CLASS-B"],
        source: "Fuente con prioridad de clase",
      },
      {
        use: "WINDOW",
        movement: "FIXED",
        direction: "INWARD",
        leaf_role: "SINGLE",
        fixed_in_sash: false,
        hinge_sides: ["NONE"],
        hardware_kit_skus: [],
        source: "Fuente de fijo",
      },
    ],
  } as unknown as DesignOptions;
  const original = STARTER_DEFINITIONS.find((item) => item.key === "bow3")!.build(2400, 1200);
  const result = sourcedStarter(original, options);
  expect(result.assembly.modules.map((module) => module.tree.opening?.movement)).toEqual([
    "TURN",
    "FIXED",
    "TURN",
  ]);
  expect(result.assembly.modules[2]!.tree.opening?.hinge_side).toBe("RIGHT");
  expect(result.assembly.modules[0]!.tree.hardware_set_sku).toBeNull();
  expect(original.assembly.modules[0]!.tree.opening).toBeUndefined();
});

it("door and side-light recipe declares its inward hinge side from catalog authority", () => {
  const options = {
    opening_capabilities: [
      {
        use: "DOOR",
        movement: "TURN",
        direction: "INWARD",
        leaf_role: "SINGLE",
        fixed_in_sash: false,
        hinge_sides: ["LEFT", "RIGHT"],
        source: "Ficha puerta",
      },
      {
        use: "DOOR",
        movement: "FIXED",
        direction: "INWARD",
        leaf_role: "SINGLE",
        fixed_in_sash: false,
        hinge_sides: ["NONE"],
        source: "Ficha fijo",
      },
    ],
  } as unknown as DesignOptions;
  const original = STARTER_DEFINITIONS.find((item) => item.key === "doorSide")!.build(1600, 2200);
  const result = sourcedStarter(original, options);
  expect(result.assembly.modules[0]!.tree.opening).toMatchObject({
    movement: "TURN",
    hinge_side: "LEFT",
    direction: "INWARD",
  });
  expect(result.assembly.modules[0]!.tree.opening_use).toBe("DOOR");
  expect(result.assembly.modules[1]!.tree.opening?.movement).toBe("FIXED");
  expect(result.assembly.modules[0]!.tree.hardware_set_sku).toBeNull();
});
