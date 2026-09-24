import { describe, expect, it } from "vitest";

import type { DesignOptions, PlanGeometry } from "../../api/generated/models";
import type { ProductJson } from "./productEditing";
import { makeBowProduct, wrapTreeAsProduct } from "./productEditing";
import type { IntentNode } from "./intentEditing";
import { resolveMembers } from "./members";
import { buildScene3D, type BoxSolid, type ShapeSolid } from "./Product3DScene";

const members = resolveMembers(undefined);

function optionsWithMullion(): DesignOptions {
  return {
    profiles: [
      {
        role: "MULLION_V",
        sku: "MV-1",
        material: "PVC",
        face_width_mm: "70.00",
        section: null,
      },
      {
        role: "FRAME",
        sku: "FR-1",
        material: "PVC",
        face_width_mm: "60.00",
        section: null,
      },
    ],
  } as DesignOptions;
}

function splitModule(offsetMm = 450): IntentNode {
  return {
    id: "split",
    type: "SPLIT_V",
    split_offset_mm: offsetMm.toFixed(2),
    children: [
      { id: "b1", type: "BAY", opening_type: "FIXED", glass_thickness_mm: "4.00" },
      { id: "b2", type: "BAY", opening_type: "TURN_LEFT", glass_thickness_mm: "4.00" },
    ],
  };
}

describe("buildScene3D", () => {
  it("builds a frame ring plus a glass leaf for a fixed module", () => {
    const product = makeBowProduct({ moduleCount: 1, widthMm: 900, heightMm: 1400, angleDeg: 0 });
    const scene = buildScene3D(product, members);
    expect(scene.modules).toHaveLength(1);
    const module = scene.modules[0]!;
    const frame = module.solids.filter((solid) => solid.surface === "frame") as BoxSolid[];
    expect(frame).toHaveLength(4);
    expect(frame.every((solid) => solid.owner === module.moduleId)).toBe(true);
    const glass = module.solids.filter((solid) => solid.surface === "glass") as BoxSolid[];
    expect(glass).toHaveLength(1);
    // leaf solids own the composite selection id the canvas uses
    expect(glass[0]!.owner).toMatch(/^m1\//);
    expect(module.position).toEqual([0, 0, 0]);
    expect(module.rotationY).toBe(0);
    expect(scene.radius).toBeGreaterThan(0);
  });

  it("emits a divider bar and per-leaf solids for a split module", () => {
    const base = makeBowProduct({ moduleCount: 1, widthMm: 900, heightMm: 1400, angleDeg: 0 });
    const module = { ...base.assembly.modules[0]!, tree: splitModule() };
    const product = {
      ...base,
      assembly: { modules: [module], couplings: [] },
    } as ProductJson;
    const scene = buildScene3D(product, resolveMembers(optionsWithMullion()));
    const solids = scene.modules[0]!.solids;
    const mullions = solids.filter((solid) => solid.surface === "mullion") as BoxSolid[];
    expect(mullions).toHaveLength(1);
    expect(mullions[0]!.size[0]).toBeCloseTo(70, 5);
    // fixed leaf → glass only; operable leaf → sash ring + glass
    const sash = solids.filter((solid) => solid.surface === "sash");
    expect(sash).toHaveLength(4);
    const glass = solids.filter((solid) => solid.surface === "glass");
    expect(glass).toHaveLength(2);
  });

  it("places modules along their plan headings", () => {
    const product = makeBowProduct({ moduleCount: 2, widthMm: 1400, heightMm: 1400, angleDeg: 15 });
    const plan: PlanGeometry = {
      front_chain: [],
      couplings: [],
      min_x_mm: "0",
      min_y_mm: "0",
      width_mm: "1400",
      height_mm: "60",
      modules: [
        {
          module_id: "m1",
          corners: [
            { x_mm: "0", y_mm: "0" },
            { x_mm: "700", y_mm: "0" },
            { x_mm: "700", y_mm: "-60" },
            { x_mm: "0", y_mm: "-60" },
          ],
        },
        {
          module_id: "m2",
          corners: [
            { x_mm: "700", y_mm: "0" },
            { x_mm: "1376.09", y_mm: "181.16" },
            { x_mm: "1360.57", y_mm: "239.12" },
            { x_mm: "684.48", y_mm: "57.96" },
          ],
        },
      ],
    };
    const scene = buildScene3D(product, members, plan);
    const [first, second] = scene.modules;
    expect(first!.position[0]).toBeCloseTo(0, 5);
    expect(first!.position[1]).toBeCloseTo(0, 5);
    expect(first!.position[2]).toBeCloseTo(0, 5);
    expect(first!.rotationY).toBeCloseTo(0, 5);
    expect(second!.position[0]).toBeCloseTo(700, 5);
    expect(second!.position[1]).toBeCloseTo(0, 5);
    expect(second!.position[2]).toBeCloseTo(0, 5);
    expect(second!.rotationY).toBeCloseTo((15 * Math.PI) / 180, 3);
    // module depth comes from the plan back edge, not a constant
    const depth = Math.hypot(684.48 - 700, 57.96 - 0);
    const box = second!.solids.find((solid) => solid.kind === "box") as BoxSolid;
    expect(box.size[2]).toBeCloseTo(depth, 0);
  });

  it("extrudes the real contour outline for shaped modules", () => {
    const base = makeBowProduct({ moduleCount: 1, widthMm: 1200, heightMm: 1400, angleDeg: 0 });
    const module = {
      ...base.assembly.modules[0]!,
      contour: {
        vertices: [
          { x_mm: "0", y_mm: "0" },
          { x_mm: "1200", y_mm: "0" },
          { x_mm: "1200", y_mm: "1400" },
          { x_mm: "0", y_mm: "900" },
        ],
        bulges: [null, null, null, null],
      },
    };
    const product = { ...base, assembly: { modules: [module], couplings: [] } } as ProductJson;
    const scene = buildScene3D(product, members);
    const shape = scene.modules[0]!.solids.find((solid) => solid.kind === "shape") as ShapeSolid;
    expect(shape).toBeDefined();
    expect(shape.outline).toHaveLength(4);
    expect(shape.holes).toHaveLength(1);
    expect(shape.owner).toBe(module.id);
  });

  it("renders frameless modules as pane + declared supports", () => {
    const base = makeBowProduct({ moduleCount: 1, widthMm: 900, heightMm: 1200, angleDeg: 0 });
    const module = {
      ...base.assembly.modules[0]!,
      frameless: {
        supports: [
          { kind: "CHANNEL" as const, edge: "bottom" as const, article_sku: "CH-1", qty: 1 },
        ],
        fittings: [],
      },
    };
    const product = { ...base, assembly: { modules: [module], couplings: [] } } as ProductJson;
    const scene = buildScene3D(product, members);
    const solids = scene.modules[0]!.solids;
    expect(solids.filter((solid) => solid.surface === "glass")).toHaveLength(1);
    expect(solids.filter((solid) => solid.surface === "support")).toHaveLength(1);
    expect(solids.some((solid) => solid.surface === "frame")).toBe(false);
  });

  it("emits a stack coupler bar at the member's sill line", () => {
    const door = makeBowProduct({ moduleCount: 1, widthMm: 900, heightMm: 2100, angleDeg: 0 });
    const transom = wrapTreeAsProduct(
      makeBowProduct({ moduleCount: 1, widthMm: 900, heightMm: 400, angleDeg: 0 }).assembly
        .modules[0]!.tree,
      "900.00",
      "400.00",
    ).assembly.modules[0]!;
    const product = {
      ...door,
      assembly: {
        modules: [door.assembly.modules[0]!, { ...transom, id: "t1" }],
        couplings: [
          {
            id: "c1",
            modules: [door.assembly.modules[0]!.id, "t1"],
            edges: ["top", "bottom"],
            kind: "STACKED" as const,
            coupler_profile_sku: null,
            angle_deg: "0.00",
          },
        ],
      },
    } as ProductJson;
    const scene = buildScene3D(product, members);
    const coupler = scene.couplers.find((solid) => solid.owner === "c1") as BoxSolid;
    expect(coupler).toBeDefined();
    expect(coupler.kind).toBe("box");
    // the member's sill sits at the door top — the coupler bar centres on it
    expect(coupler.center[1]).toBeCloseTo(2100, 0);
  });
});
