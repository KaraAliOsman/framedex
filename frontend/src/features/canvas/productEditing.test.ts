import { describe, expect, it } from "vitest";

import { createBowFromInputs } from "./AssemblyEditor";
import {
  addAdjacentUnit,
  equalizeCouplingAngles,
  equalizeModuleWidths,
  isProductModel,
  isSingleUnit,
  removeUnit,
  scaleModuleWidths,
  makeBowProduct,
  moduleGlassSku,
  moduleOpening,
  modulePanelSku,
  moveModuleDivision,
  resizeModuleSeam,
  setModulePanel,
  setAllCouplingAngles,
  setCouplerSku,
  setModuleGlass,
  setCouplerSkuAll,
  setCouplingAngle,
  setModuleCount,
  setModuleOpening,
  setModuleWidth,
  setAllModuleHeights,
  splitModuleBay,
  totalModuleWidth,
  wrapTreeAsProduct,
} from "./productEditing";
import type { CanvasDesignInputs } from "./canvasStore";

function bow(): ReturnType<typeof makeBowProduct> {
  return makeBowProduct({
    moduleCount: 3,
    widthMm: 2100,
    heightMm: 1400,
    angleDeg: 15,
  });
}

describe("makeBowProduct", () => {
  it("builds modules + couplings that sum to the nominal width", () => {
    const product = bow();
    expect(product.version).toBe("product-v2");
    expect(product.assembly.modules.map((m) => m.id)).toEqual(["m1", "m2", "m3"]);
    expect(product.assembly.couplings.map((c) => c.id)).toEqual(["c1", "c2"]);
    expect(totalModuleWidth(product)).toBeCloseTo(2100, 5);
    expect(isProductModel(product)).toBe(true);
    expect(isProductModel({ version: "product-v1" })).toBe(false);
  });
});

describe("addAdjacentUnit", () => {
  it("appends a unit inheriting the edge module and outermost joint", () => {
    const base = setCouplerSkuAll(bow(), "ACOPLE-60");
    const grown = addAdjacentUnit(base, "right");
    expect(grown.assembly.modules.map((m) => m.id)).toEqual(["m1", "m2", "m3", "m4"]);
    expect(grown.assembly.couplings.map((c) => c.id)).toEqual(["c1", "c2", "c3"]);
    const added = grown.assembly.modules.at(-1)!;
    expect(added.width_mm).toBe(base.assembly.modules.at(-1)!.width_mm);
    expect(added.height_mm).toBe(base.assembly.modules.at(-1)!.height_mm);
    expect(grown.assembly.couplings.at(-1)!.angle_deg).toBe("15.0");
    expect(grown.assembly.couplings.at(-1)!.coupler_profile_sku).toBe("ACOPLE-60");
  });

  it("prepends on the left and starts straight when no joint exists", () => {
    const single = wrapTreeAsProduct(
      { id: "g1", type: "BAY", opening_type: "FIXED" },
      "1000.00",
      "1200.00",
    );
    expect(isSingleUnit(single)).toBe(true);
    const grown = addAdjacentUnit(single, "left");
    expect(grown.assembly.modules.map((m) => m.id)).toEqual(["m2", "m1"]);
    expect(grown.assembly.couplings).toEqual([
      { id: "c1", angle_deg: "0.0", coupler_profile_sku: null },
    ]);
    expect(isSingleUnit(grown)).toBe(false);
    // the inherited unit is a deep copy, not a shared tree reference
    expect(grown.assembly.modules[0]!.tree).not.toBe(grown.assembly.modules[1]!.tree);
  });
});

describe("removeUnit", () => {
  it("drops an edge module with its one adjacent coupling", () => {
    const removed = removeUnit(bow(), "m1");
    expect(removed.assembly.modules.map((m) => m.id)).toEqual(["m2", "m3"]);
    expect(removed.assembly.couplings.map((c) => c.id)).toEqual(["c2"]);
  });

  it("heals interior removals by merging the deflection so orientation survives", () => {
    const bent = setAllCouplingAngles(bow(), "10.0");
    const removed = removeUnit(bent, "m2");
    expect(removed.assembly.modules.map((m) => m.id)).toEqual(["m1", "m3"]);
    // heading of m3 was 0 + 10 + 10 — the merged joint preserves it
    expect(removed.assembly.couplings).toHaveLength(1);
    expect(removed.assembly.couplings[0]!.angle_deg).toBe("20.0");
  });

  it("refuses to remove the last module or an unknown id", () => {
    const single = wrapTreeAsProduct(
      { id: "g1", type: "BAY", opening_type: "FIXED" },
      "1000.00",
      "1200.00",
    );
    expect(removeUnit(single, "m1")).toBe(single);
    expect(removeUnit(bow(), "nope")).toEqual(bow());
  });
});

describe("splitModuleBay", () => {
  it("splits the primary bay at the center with the given mullion", () => {
    const split = splitModuleBay(bow(), "m2", { type: "SPLIT_V", mullionSku: "MULL-60" });
    const tree = split.assembly.modules[1]!.tree;
    expect(tree.type).toBe("SPLIT_V");
    expect(tree.split_offset_mm).toBe("350.00");
    expect(tree.mullion_profile_sku).toBe("MULL-60");
    expect(tree.children).toHaveLength(2);
  });

  it("generates unique node ids across repeated splits", () => {
    const once = splitModuleBay(bow(), "m2", { type: "SPLIT_V", mullionSku: "MULL-60" });
    const twice = splitModuleBay(once, "m2", { type: "SPLIT_H", mullionSku: "MULL-60" });
    expect(twice).not.toBe(once);
  });

  it("refuses door bays and missing mullions", () => {
    const door = setModuleOpening(bow(), "m2", "DOOR_ENTRY");
    expect(splitModuleBay(door, "m2", { type: "SPLIT_V", mullionSku: "MULL-60" })).toBe(door);
    expect(splitModuleBay(bow(), "m2", { type: "SPLIT_V", mullionSku: "" })).toEqual(bow());
  });

  it("splits at a pointer-chosen offset instead of the center", () => {
    const split = splitModuleBay(bow(), "m2", {
      type: "SPLIT_V",
      mullionSku: "MULL-60",
      offsetMm: "215.00",
    });
    expect(split.assembly.modules[1]!.tree.split_offset_mm).toBe("215.00");
  });
});

describe("moveModuleDivision", () => {
  it("moves the divider to a new offset", () => {
    const split = splitModuleBay(bow(), "m2", { type: "SPLIT_V", mullionSku: "MULL-60" });
    const divisionId = split.assembly.modules[1]!.tree.id;
    const moved = moveModuleDivision(split, "m2", divisionId, "420.00");
    expect(moved.assembly.modules[1]!.tree.split_offset_mm).toBe("420.00");
  });

  it("returns the same product for unknown ids or bays", () => {
    const product = bow();
    expect(moveModuleDivision(product, "m2", "m2-g1", "100.00")).toBe(product);
    expect(moveModuleDivision(product, "nope", "anything", "100.00")).toBe(product);
  });
});

describe("resizeModuleSeam", () => {
  it("grows the left module while shrinking the right — total holds", () => {
    const resized = resizeModuleSeam(bow(), 0, 120);
    const [m1, m2] = resized.assembly.modules;
    expect(Number(m1!.width_mm)).toBeCloseTo(820, 5);
    expect(Number(m2!.width_mm)).toBeCloseTo(580, 5);
    expect(totalModuleWidth(resized)).toBeCloseTo(2100, 5);
  });

  it("refuses drags that cross the minimum module width", () => {
    const product = bow();
    // each module is 700mm — a -560mm drag would leave 140mm on the left
    expect(resizeModuleSeam(product, 0, -560)).toBe(product);
    expect(resizeModuleSeam(product, 0, 560)).toBe(product);
    expect(resizeModuleSeam(product, 9, 10)).toBe(product);
  });
});

describe("setModuleCount", () => {
  it("grows by copying the last module and coupling", () => {
    const grown = setModuleCount(setCouplerSkuAll(bow(), "ACOPLE-60"), 4);
    expect(grown.assembly.modules).toHaveLength(4);
    expect(grown.assembly.couplings).toHaveLength(3);
    expect(grown.assembly.couplings[2]?.coupler_profile_sku).toBe("ACOPLE-60");
    expect(grown.assembly.couplings[2]?.angle_deg).toBe("15.0");
  });

  it("shrinks by trimming the tail", () => {
    const shrunk = setModuleCount(bow(), 2);
    expect(shrunk.assembly.modules.map((m) => m.id)).toEqual(["m1", "m2"]);
    expect(shrunk.assembly.couplings.map((c) => c.id)).toEqual(["c1"]);
  });
});

describe("equalizeModuleWidths", () => {
  it("preserves the total width with the last module absorbing rounding", () => {
    const uneven = setModuleWidth(bow(), "m1", "900.00");
    const total = totalModuleWidth(uneven);
    const equalized = equalizeModuleWidths(uneven);
    expect(totalModuleWidth(equalized)).toBeCloseTo(total, 5);
    const widths = equalized.assembly.modules.map((m) => Number(m.width_mm));
    expect(widths[0]).toBeCloseTo(766.67, 2);
    expect(widths[2]).toBeCloseTo(766.66, 2);
  });
});

describe("scaleModuleWidths", () => {
  it("scales so widths sum back to the requested total exactly", () => {
    const scaled = scaleModuleWidths(bow(), "2000.00");
    const widths = scaled.assembly.modules.map((module) => Number(module.width_mm));
    expect(widths.reduce((sum, width) => sum + width, 0)).toBeCloseTo(2000, 9);
    // proportional shares — largest-remainder allocation keeps the 0.00 mm sum
    expect(widths[0]).toBeCloseTo(666.67, 2);
    expect(widths[2]).toBeCloseTo(666.66, 2);
  });

  it("never produces zero-width modules on tiny totals", () => {
    const scaled = scaleModuleWidths(bow(), "0.05");
    const widths = scaled.assembly.modules.map((module) => Number(module.width_mm));
    expect(widths.reduce((sum, width) => sum + width, 0)).toBeCloseTo(0.05, 9);
    expect(widths.every((width) => width >= 0.01)).toBe(true);
    // unequal proportions still honor the positive floor for every module
    const skewed = scaleModuleWidths(
      {
        ...bow(),
        assembly: {
          ...bow().assembly,
          modules: bow().assembly.modules.map((module, index) => ({
            ...module,
            width_mm: index === 0 ? "10.00" : index === 1 ? "100.00" : "190.00",
          })),
        },
      },
      "0.03",
    );
    expect(skewed.assembly.modules.every((module) => Number(module.width_mm) >= 0.01)).toBe(true);
  });

  it("rejects totals too small to keep every module positive", () => {
    const product = bow();
    expect(scaleModuleWidths(product, "0")).toBe(product);
    expect(scaleModuleWidths(product, "abc")).toBe(product);
    expect(scaleModuleWidths(product, "0.02")).toBe(product);
  });
});

describe("module commands", () => {
  it("sets opening type on every bay of the module tree", () => {
    const opened = setModuleOpening(bow(), "m2", "TILT_TURN_LEFT");
    expect(moduleOpening(opened.assembly.modules[1]!)).toBe("TILT_TURN_LEFT");
    expect(moduleOpening(opened.assembly.modules[0]!)).toBe("FIXED");
  });

  it("sets angle and sku on the matching coupling only", () => {
    const next = setCouplerSku(setCouplingAngle(bow(), "c2", "22.0"), "c2", "SK-9");
    expect(next.assembly.couplings[1]?.angle_deg).toBe("22.0");
    expect(next.assembly.couplings[1]?.coupler_profile_sku).toBe("SK-9");
    expect(next.assembly.couplings[0]?.coupler_profile_sku).toBeNull();
  });

  it("equalizes all coupling angles to the first", () => {
    const next = equalizeCouplingAngles(setCouplingAngle(bow(), "c1", "18.5"));
    expect(next.assembly.couplings.map((c) => c.angle_deg)).toEqual(["18.5", "18.5"]);
  });

  it("sets a shared height across modules", () => {
    const next = setAllModuleHeights(bow(), "1250.00");
    expect(next.assembly.modules.every((module) => module.height_mm === "1250.00")).toBe(true);
  });

  it("sets the commercial glass sku on the matching module only", () => {
    const glazed = setModuleGlass(bow(), "m2", "GLASS-A");
    expect(moduleGlassSku(glazed.assembly.modules[1]!)).toBe("GLASS-A");
    expect(moduleGlassSku(glazed.assembly.modules[0]!)).toBeNull();
  });

  it("assigns a panel sku to the matching module only", () => {
    const paneled = setModulePanel(bow(), "m2", "PANEL-70");
    expect(modulePanelSku(paneled.assembly.modules[1]!)).toBe("PANEL-70");
    expect(modulePanelSku(paneled.assembly.modules[0]!)).toBeNull();
  });

  it("clears the panel sku when the module leaves DOOR_ENTRY", () => {
    const doored = setModuleOpening(setModulePanel(bow(), "m2", "PANEL-70"), "m2", "DOOR_ENTRY");
    const fixed = setModuleOpening(doored, "m2", "FIXED");
    expect(modulePanelSku(doored.assembly.modules[1]!)).toBe("PANEL-70");
    expect(modulePanelSku(fixed.assembly.modules[1]!)).toBeNull();
  });
});

describe("createBowFromInputs", () => {
  it("derives a 3-module bow from classic inputs", () => {
    const inputs: CanvasDesignInputs = {
      systemId: "s",
      nominalWidthMm: "2400.00",
      nominalHeightMm: "1500.00",
      color: "WHITE",
      parametricTree: { id: "b", type: "BAY", opening_type: "FIXED" },
      product: null,
    };
    const product = createBowFromInputs(inputs, "4.00", "4");
    expect(product.assembly.modules).toHaveLength(3);
    expect(totalModuleWidth(product)).toBeCloseTo(2400, 5);
  });

  it("carries the selected glass sku into every module", () => {
    const inputs: CanvasDesignInputs = {
      systemId: "s",
      nominalWidthMm: "2400.00",
      nominalHeightMm: "1500.00",
      color: "WHITE",
      parametricTree: { id: "b", type: "BAY", opening_type: "FIXED" },
      product: null,
    };
    const product = createBowFromInputs(inputs, "4.00", "4", "GLASS-A");
    expect(product.assembly.modules.every((module) => moduleGlassSku(module) === "GLASS-A")).toBe(
      true,
    );
  });
});
