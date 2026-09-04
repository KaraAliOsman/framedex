import { describe, expect, it } from "vitest";

import { normalizeDimensionCandidate, snapOuterDimension } from "./snapping";

describe("SHOT-05 outer-dimension snapping", () => {
  it("snaps to the nearest 50 mm at the inclusive twelve-pixel boundary", () => {
    expect(snapOuterDimension("1038", "1", true)).toEqual({
      valueMm: "1050.00",
      mode: "50mm",
      showGuide: true,
    });
  });

  it("falls back to 10 mm immediately outside the screen-space radius", () => {
    expect(snapOuterDimension("1037.99", "1", true)).toEqual({
      valueMm: "1040.00",
      mode: "10mm",
      showGuide: false,
    });
  });

  it("uses ROUND_HALF_UP for both the 50 mm and 10 mm tie cases", () => {
    expect(snapOuterDimension("1025", "0.4", true).valueMm).toBe("1050.00");
    expect(snapOuterDimension("1035", "1", true).valueMm).toBe("1040.00");
  });

  it("quantizes Snap OFF candidates to 0.01 mm with ROUND_HALF_UP", () => {
    expect(snapOuterDimension("1000.005", "1", false)).toEqual({
      valueMm: "1000.01",
      mode: "0.01mm",
      showGuide: false,
    });
  });

  it("keeps the magnetic radius fixed in pixels as viewport scale changes", () => {
    expect(snapOuterDimension("1042", "1.5", true).mode).toBe("50mm");
    expect(snapOuterDimension("1042", "1.51", true).mode).toBe("10mm");
  });

  it("normalizes only positive decimal strings representable by the API field", () => {
    expect(normalizeDimensionCandidate("1000")).toBe("1000.00");
    expect(normalizeDimensionCandidate("1000.5")).toBe("1000.50");
    expect(normalizeDimensionCandidate("0.01")).toBe("0.01");
    expect(normalizeDimensionCandidate("99999999.99")).toBe("99999999.99");
    expect(normalizeDimensionCandidate("0")).toBeNull();
    expect(normalizeDimensionCandidate("1000.001")).toBeNull();
    expect(normalizeDimensionCandidate("100000000.00")).toBeNull();
    expect(normalizeDimensionCandidate("Infinity")).toBeNull();
  });
});
