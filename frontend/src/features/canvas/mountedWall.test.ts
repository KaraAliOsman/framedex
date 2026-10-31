import { describe, expect, it } from "vitest";

import { mountedWallBoxes, openingsByModule, type MountedOpening } from "./mountedWall";

const side = (adjustment_mm: string, clearance_mm = "10.00") => ({ adjustment_mm, clearance_mm });
const opening = (over: Partial<MountedOpening> = {}): MountedOpening => ({
  moduleId: "m1",
  moduleIndex: 1,
  widthMm: "1220.00",
  heightMm: "1020.00",
  ruleName: "En vano · Proline",
  synthetic: false,
  sides: {
    left: side("-10.00"),
    right: side("-10.00"),
    top: side("-10.00"),
    bottom: side("-10.00"),
  },
  ...over,
});

function edges(boxes: ReturnType<typeof mountedWallBoxes>) {
  const [left, right, top, bottom] = boxes;
  return {
    x0: left!.center[0] + left!.size[0] / 2,
    x1: right!.center[0] - right!.size[0] / 2,
    y1: top!.center[1] - top!.size[1] / 2,
    y0: bottom!.center[1] + bottom!.size[1] / 2,
  };
}

describe("mounted wall", () => {
  it("opens the wall exactly at the measured vano around the frame", () => {
    const boxes = mountedWallBoxes({ depth: 60 }, { width: 1200, height: 1000 }, opening());
    expect(boxes).toHaveLength(4);
    expect(edges(boxes)).toEqual({ x0: -10, x1: 1210, y0: -10, y1: 1010 });
  });

  it("tucks the frame behind the reveal when the rule overlaps", () => {
    const boxes = mountedWallBoxes(
      { depth: 60 },
      { width: 1200, height: 1000 },
      opening({
        widthMm: "1160.00",
        heightMm: "960.00",
        sides: {
          left: side("20.00", "0.00"),
          right: side("20.00", "0.00"),
          top: side("20.00", "0.00"),
          bottom: side("20.00", "0.00"),
        },
      }),
    );
    expect(edges(boxes)).toEqual({ x0: 20, x1: 1180, y0: 20, y1: 980 });
  });

  it("centres an older sealed vano without sides and refuses an invalid one", () => {
    const centred = mountedWallBoxes(
      { depth: 60 },
      { width: 1200, height: 1000 },
      opening({ sides: null }),
    );
    expect(edges(centred)).toEqual({ x0: -10, x1: 1210, y0: -10, y1: 1010 });
    expect(
      mountedWallBoxes({ depth: 60 }, { width: 1200, height: 1000 }, opening({ widthMm: "" })),
    ).toEqual([]);
  });

  it("matches sealed module ids first and falls back to order", () => {
    const byId = openingsByModule(["a", "b"], [opening({ moduleId: "b", moduleIndex: 1 })]);
    expect(Object.keys(byId)).toEqual(["b"]);
    const byOrder = openingsByModule(["a", "b"], [opening({ moduleId: null, moduleIndex: 2 })]);
    expect(Object.keys(byOrder)).toEqual(["b"]);
  });
});
