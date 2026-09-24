import { describe, expect, it } from "vitest";

import { contourPathD, insetContourPoints, pointsPathD } from "./contourGeometry";
import {
  contourTopCorners,
  isSingleUnit,
  makeArchModule,
  makeTrapezoidModule,
  scaledContour,
  setContourBulge,
  setContourVertex,
  setModuleWidth,
  type ContourJson,
  type ProductJson,
} from "./productEditing";

const trapezoid = makeTrapezoidModule("m1", "2400.00", "1400.00", 200, 300, {
  id: "b1",
  type: "BAY",
  opening_type: "FIXED",
});
const arch = makeArchModule("m1", "2400.00", "1400.00", 300, {
  id: "b1",
  type: "BAY",
  opening_type: "FIXED",
});
const product = (module: typeof trapezoid): ProductJson => ({
  version: "product-v2",
  assembly: { modules: [module], couplings: [] },
});

describe("contourPathD", () => {
  it("flips y into screen space and closes", () => {
    const d = contourPathD(trapezoid.contour!, 1400);
    expect(d).toContain("M 0.00 1400.00");
    expect(d).toContain("L 2400.00 1400.00");
    expect(d).toContain("L 2100.00 0.00");
    expect(d).toContain("L 200.00 0.00");
    expect(d).toContain("Z");
    expect(d).not.toContain("A ");
  });

  it("emits an SVG arc command for a bulged edge", () => {
    const d = contourPathD(arch.contour!, 1400);
    expect(d).toMatch(/A 2550\.00 2550\.00 0 0 0 0\.00 0\.00/);
  });
});

describe("insetContourPoints", () => {
  it("reproduces the inset rectangle on an axis-aligned contour", () => {
    const rect: ContourJson = {
      vertices: [
        { x_mm: "0.00", y_mm: "0.00" },
        { x_mm: "1200.00", y_mm: "0.00" },
        { x_mm: "1200.00", y_mm: "800.00" },
        { x_mm: "0.00", y_mm: "800.00" },
      ],
      bulges: [null, null, null, null],
    };
    const points = insetContourPoints(rect, 45);
    const xs = points.map((p) => p.x);
    const ys = points.map((p) => p.y);
    expect(Math.min(...xs)).toBeCloseTo(45, 1);
    expect(Math.max(...xs)).toBeCloseTo(1155, 1);
    expect(Math.min(...ys)).toBeCloseTo(45, 1);
    expect(Math.max(...ys)).toBeCloseTo(755, 1);
  });

  it("samples the inset arch along its own crown", () => {
    // The outline's apex sits rise above the springline; the inset crown
    // reaches ~apex−distance, never below the chord.
    const points = insetContourPoints(arch.contour!, 45);
    const maxY = Math.max(...points.map((p) => p.y));
    expect(points.length).toBeGreaterThan(8);
    expect(maxY).toBeGreaterThan(1600);
    expect(maxY).toBeLessThan(1700);
  });
});

describe("pointsPathD", () => {
  it("draws a closed polyline through flipped points", () => {
    const d = pointsPathD(
      [
        { x: 45, y: 45 },
        { x: 1155, y: 45 },
        { x: 1155, y: 755 },
      ],
      800,
    );
    expect(d).toBe("M 45.00 755.00 L 1155.00 755.00 L 1155.00 45.00 Z");
  });
});

describe("contour editing", () => {
  it("finds the top corners ordered left→right", () => {
    expect(contourTopCorners(trapezoid.contour!)).toEqual({ leftIndex: 3, rightIndex: 2 });
  });

  it("rescales a contour to a new bounding box", () => {
    const scaled = scaledContour(trapezoid.contour!, "1200.00", "700.00");
    expect(scaled.vertices[2]!.x_mm).toBe("1050.00");
    expect(scaled.vertices[2]!.y_mm).toBe("700.00");
    const scaledArch = scaledContour(arch.contour!, "1200.00", "700.00");
    expect(scaledArch.bulges[2]).toBe("150.00");
  });

  it("keeps an arch's rise under width-only scaling (no y squash)", () => {
    // Horizontal chord: the rise scales with y, so a width-only resize
    // preserves the flecha instead of falsely squashing it.
    const wider = scaledContour(arch.contour!, "4800.00", "1400.00");
    expect(wider.bulges[2]).toBe("300.00");
    // A bowed side wall (vertical chord) scales its sagitta with x instead.
    const sideBow: ContourJson = {
      vertices: [
        { x_mm: "0", y_mm: "0" },
        { x_mm: "1200", y_mm: "0" },
        { x_mm: "1200", y_mm: "1500" },
        { x_mm: "0", y_mm: "1500" },
      ],
      bulges: [null, "100.00", null, null],
    };
    const stretched = scaledContour(sideBow, "2400.00", "1500.00");
    expect(stretched.bulges[1]).toBe("200.00");
  });

  it("scales the contour when the module width commits", () => {
    const next = setModuleWidth(product(trapezoid), "m1", "1200.00");
    expect(next.assembly.modules[0]!.contour!.vertices[2]!.x_mm).toBe("1050.00");
  });

  it("moves a single vertex", () => {
    const next = setContourVertex(product(trapezoid), "m1", 3, "400.00", "1400.00");
    expect(next.assembly.modules[0]!.contour!.vertices[3]).toEqual({
      x_mm: "400.00",
      y_mm: "1400.00",
    });
  });

  it("edits an edge rise", () => {
    const next = setContourBulge(product(arch), "m1", 2, "500.00");
    expect(next.assembly.modules[0]!.contour!.bulges[2]).toBe("500.00");
  });

  it("keeps contoured units on the product-v2 persistence path", () => {
    expect(isSingleUnit(product(trapezoid))).toBe(false);
  });
});
