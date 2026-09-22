import { describe, expect, it } from "vitest";

import { createBowFromInputs } from "./AssemblyEditor";
import {
  equalizeCouplingAngles,
  equalizeModuleWidths,
  isProductModel,
  scaleModuleWidths,
  makeBowProduct,
  moduleGlassSku,
  moduleOpening,
  modulePanelSku,
  setModulePanel,
  setCouplerSku,
  setModuleGlass,
  setCouplerSkuAll,
  setCouplingAngle,
  setModuleCount,
  setModuleOpening,
  setModuleWidth,
  setAllModuleHeights,
  totalModuleWidth,
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
    // proportional shares plus remainder on the last module
    expect(widths[0]).toBeCloseTo(666.67, 2);
    expect(widths[2]).toBeCloseTo(666.66, 2);
  });

  it("rejects non-positive totals", () => {
    const product = bow();
    expect(scaleModuleWidths(product, "0")).toBe(product);
    expect(scaleModuleWidths(product, "abc")).toBe(product);
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
