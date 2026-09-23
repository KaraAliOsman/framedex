import { describe, expect, it } from "vitest";

import { applyDesignOp, applyDesignOps, describeDesignOp } from "./designOps";
import { makeBowProduct, totalModuleWidth } from "./productEditing";

function bow(modules = 3) {
  return makeBowProduct({ moduleCount: modules, widthMm: 2100, heightMm: 1400, angleDeg: 15 });
}

describe("applyDesignOps", () => {
  it("applies a module count change", () => {
    const next = applyDesignOps(bow(3), [{ op: "set_module_count", count: 5 }]);
    expect(next.assembly.modules).toHaveLength(5);
    expect(next.assembly.couplings).toHaveLength(4);
  });

  it("scales the total width", () => {
    const next = applyDesignOps(bow(2), [{ op: "set_total_width", width_mm: "2400" }]);
    expect(totalModuleWidth(next)).toBeCloseTo(2400, 1);
  });

  it("sets an opening on a module by index", () => {
    const next = applyDesignOps(bow(2), [{ op: "set_opening", module: 1, opening: "SLIDING_2L" }]);
    const tree = next.assembly.modules[1]!.tree;
    const child = tree.children?.[0] ?? tree;
    expect(child.opening_type).toBe("SLIDING_2L");
  });

  it("sets coupling angles per index", () => {
    const next = applyDesignOps(bow(3), [
      { op: "set_coupling_angle", coupling: 0, angle_deg: "30" },
      { op: "set_coupling_angle", coupling: 1, angle_deg: "30" },
    ]);
    expect(next.assembly.couplings[0]!.angle_deg).toBe("30");
    expect(next.assembly.couplings[1]!.angle_deg).toBe("30");
  });

  it("drops ops against missing indices instead of corrupting the product", () => {
    const product = bow(2);
    const next = applyDesignOps(product, [
      { op: "set_opening", module: 7, opening: "FIXED" },
      { op: "set_coupling_angle", coupling: 9, angle_deg: "10" },
    ]);
    expect(next).toBe(product);
  });

  it("never mutates on an unknown op", () => {
    const product = bow(2);
    expect(applyDesignOp(product, { op: "delete_all" })).toBe(product);
  });

  it("adds a unit on the left", () => {
    const next = applyDesignOps(bow(2), [{ op: "add_unit", side: "left" }]);
    expect(next.assembly.modules).toHaveLength(3);
    expect(next.assembly.couplings).toHaveLength(2);
  });
});

describe("describeDesignOp", () => {
  it("renders human es-CL labels", () => {
    expect(describeDesignOp({ op: "set_module_count", count: 3 })).toBe("3 módulos");
    expect(describeDesignOp({ op: "equalize_widths" })).toBe("anchos iguales");
    expect(describeDesignOp({ op: "set_total_width", width_mm: "2400" })).toContain("2400");
    expect(describeDesignOp({ op: "set_opening", module: 0, opening: "DOOR_ENTRY" })).toBe(
      "módulo 1: puerta",
    );
  });
});
