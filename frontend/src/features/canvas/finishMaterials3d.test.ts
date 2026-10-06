import { describe, expect, it } from "vitest";
import * as THREE from "three";
import goldens from "../../../../engine/tests/golden_finishes.json";
import type { ResolvedFinish } from "../../api/generated/models";
import { chartFinish, finishColorCss } from "./finishColors";
import { disposeFinishMaterials, finishGeometryMaterials } from "./finishMaterials3d";
import { withFinishMembers, resolveMembers } from "./members";
import { bayHardwareColor } from "./finishHardware";

const finish = goldens["pvc-nogal-exterior"].bom.finish as ResolvedFinish;

describe("declared finishes in commercial render", () => {
  it("keeps the catalog linear channels on room/street faces and exposes PVC base on edges", () => {
    const geometry = new THREE.BoxGeometry(100, 100, 60);
    const materials = finishGeometryMaterials(geometry, finish);
    expect(materials[1]!.color.toArray()).toEqual(finish.interior.linear_rgb.map(Number));
    expect(materials[2]!.color.toArray()).toEqual(finish.exterior.linear_rgb.map(Number));
    expect(materials[0]!.color.toArray()).toEqual(finish.base!.linear_rgb.map(Number));
    expect(materials.every((material) => material.emissive.getHex() === 0)).toBe(true);
    expect(new Set(geometry.groups.map((group) => group.materialIndex))).toEqual(
      new Set([0, 1, 2]),
    );
    for (const group of geometry.groups) {
      const vertex = geometry.index!.getX(group.start);
      const z = geometry.getAttribute("normal").getZ(vertex);
      expect(group.materialIndex).toBe(z > 0.5 ? 1 : z < -0.5 ? 2 : 0);
    }
    disposeFinishMaterials(materials);
    geometry.dispose();
  });
  it("uses the same swatch as the emitted face and never fabricates grain", () => {
    expect(finishColorCss(finish.exterior)).toBe(
      "color(srgb 0.3803921568627451 0.23921568627450981 0.11764705882352941)",
    );
    const materials = finishGeometryMaterials(new THREE.BoxGeometry(1, 1, 1), finish);
    expect(materials.every((material) => material.map === null)).toBe(true);
    disposeFinishMaterials(materials);
    const interior = withFinishMembers(resolveMembers(undefined), finish, "interior");
    const exterior = withFinishMembers(resolveMembers(undefined), finish, "exterior");
    expect(interior.frame.faceFinish).toEqual(finish.interior);
    expect(exterior.frame.faceFinish).toEqual(finish.exterior);
  });
  it("refuses unknown pairs and obtains hardware paint only from declared samples", () => {
    const chart = {
      schema_version: 1,
      material: "PVC",
      colors: [finish.interior, finish.exterior],
      combinations: [finish.combination],
      source: "Fuente de ensayo",
    };
    expect(chartFinish(chart, "CREAM_WALNUT")).toBeNull();
    const members = withFinishMembers(resolveMembers(undefined), finish, "interior");
    const bay = {
      id: "vano",
      type: "BAY" as const,
      hardware_selection: { color_code: "BLACK", option_codes: [] },
    };
    expect(bayHardwareColor(members, bay)?.code).toBe("BLACK");
    expect(
      bayHardwareColor(members, {
        ...bay,
        hardware_selection: { color_code: "BRONZE", option_codes: [] },
      }),
    ).toBeUndefined();
  });
});
