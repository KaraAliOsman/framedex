import { describe, expect, it } from "vitest";
import fixtures from "../../../../engine/tests/fixtures/scene3d.json";
import type { DesignOptions, ResolvedFinish } from "../../api/generated/models";
import type { OpeningLeafFact } from "./physicalOpenings";
import type { ProductJson } from "./productEditing";
import { buildScene3D, type Vec3 } from "./Product3DScene";
import { resolveMembers, withFinishMembers } from "./members";
import {
  moduleLeafPoses,
  transformPosePoint,
  explodeLayer,
  explodeDistance,
  solidCenter,
  MOTION_SECONDS,
} from "./poses3d";
import { cameraShot, poseMatrix } from "./studioRig3d";
import * as THREE from "three";

function prepared(fixture: (typeof fixtures)[number]) {
  const product = fixture.product as ProductJson;
  let members = resolveMembers(fixture.options as unknown as DesignOptions);
  if (fixture.finish)
    members = withFinishMembers(members, fixture.finish as unknown as ResolvedFinish);
  const scene = buildScene3D(
    product,
    members,
    null,
    fixture.openingFacts as unknown as Record<string, OpeningLeafFact[]>,
  );
  return { product, scene, module: scene.modules[0]! };
}
const closeTo = (actual: Vec3, expected: Vec3) =>
  actual.forEach((v, i) => expect(v).toBeCloseTo(expected[i]!, 6));

describe("motor-authorized rigid 3D projection", () => {
  for (const fixture of fixtures)
    it(fixture.name, () => {
      const { product, scene, module } = prepared(fixture);
      const height = Number(product.assembly.modules[0]!.height_mm),
        width = Number(product.assembly.modules[0]!.width_mm);
      const states = Object.fromEntries(
        module.leaves.map((leaf) => [leaf.leafId, { amount: 1, mode: "open" as const }]),
      );
      const poses = moduleLeafPoses(module, states);
      for (const leaf of module.leaves) {
        if (!leaf.fact) {
          expect(leaf.kind).toBe("slide");
          const pose = poses[leaf.leafId]!;
          expect(pose.rotationX).toBe(0);
          expect(pose.rotationY).toBe(0);
          expect(pose.translation[0]).toBe(leaf.dir * leaf.travel);
          for (const solid of module.solids.filter((s) => s.leafId === leaf.leafId)) {
            const center = transformPosePoint(solidCenter(solid), pose);
            expect(center[0]).toBeGreaterThanOrEqual(0);
            expect(center[0]).toBeLessThanOrEqual(width);
            expect(center[1]).toBeGreaterThanOrEqual(0);
            expect(center[1]).toBeLessThanOrEqual(height);
          }
          continue;
        }
        const f = leaf.fact!,
          a = f.advanced,
          pose = poses[leaf.leafId]!;
        const plane = leaf.pivotDepth!;
        const start: Vec3 = [Number(f.x_mm), 0, plane],
          end: Vec3 = [Number(f.x_mm) + Number(f.width_mm), 0, plane];
        if (a && ["FOLD", "PIVOT_V"].includes(f.opening.movement)) {
          for (const [index, point] of [start, end].entries())
            closeTo(transformPosePoint(point, pose), [
              Number(a.open_plan[index]!.x_mm),
              0,
              Number(a.open_plan[index]!.depth_mm),
            ]);
        }
        if (
          ["SLIDE", "LIFT_SLIDE", "PARALLEL_SLIDE", "VERTICAL_SLIDE"].includes(f.opening.movement)
        ) {
          const bottom = height - Number(f.y_mm) - Number(f.height_mm);
          const points: Vec3[] = [
            [start[0], bottom, plane],
            [end[0], bottom + Number(f.height_mm), plane],
          ];
          for (const p of points.map((point) => transformPosePoint(point, pose))) {
            expect(p[0]).toBeGreaterThanOrEqual(-0.01);
            expect(p[0]).toBeLessThanOrEqual(width + 0.01);
            expect(p[1]).toBeGreaterThanOrEqual(-0.01);
            expect(p[1]).toBeLessThanOrEqual(height + 0.01);
          }
          if (a && f.opening.movement !== "VERTICAL_SLIDE") {
            closeTo(transformPosePoint(start, pose), [
              Number(a.open_plan[0].x_mm),
              Number(a.lift_mm ?? 0),
              Number(a.open_plan[0].depth_mm),
            ]);
          }
        }
        // Rotation preserves the hinge/pivot and every pairwise distance.
        if (pose.rotationX || pose.rotationY) {
          closeTo(
            transformPosePoint(pose.pivot, pose),
            pose.pivot.map((v, i) => v + pose.translation[i]!) as Vec3,
          );
        }
        for (const amount of [0, 0.25, 0.5, 0.75, 1]) {
          const states = Object.fromEntries(
            module.leaves.map((l) => [l.leafId, { amount, mode: "open" as const }]),
          );
          const p = moduleLeafPoses(module, states)[leaf.leafId]!;
          const a = transformPosePoint(start, p),
            b = transformPosePoint(end, p);
          expect(Math.hypot(...a.map((v, i) => v - b[i]!))).toBeCloseTo(Number(f.width_mm), 6);
          const projected = new THREE.Vector3(...end).applyMatrix4(poseMatrix(p));
          closeTo([projected.x, projected.y, projected.z], b);
        }
        const hardware = module.solids.filter(
          (s) => s.leafId === leaf.leafId && s.surface === "handle",
        );
        if (!f.handle) expect(hardware).toHaveLength(0);
        else {
          const x = Number(f.x_mm) + Number(f.handle.x_mm),
            y = height - Number(f.y_mm) - Number(f.handle.y_mm);
          expect(
            hardware.some((s) => {
              const c = solidCenter(s);
              return Math.abs(c[0] - x) < 0.01 && Math.abs(c[1] - y) < 0.01;
            }),
          ).toBe(true);
          if (f.opening.hinge_side === "LEFT")
            expect(x).toBeGreaterThan(Number(f.x_mm) + Number(f.width_mm) / 2);
          if (f.opening.hinge_side === "RIGHT")
            expect(x).toBeLessThan(Number(f.x_mm) + Number(f.width_mm) / 2);
        }
      }
      expect(scene.diagnostics).toEqual([]);
    });
  it("separates glass/bead/sash only along depth, with ordered axial layers", () => {
    const { module } = prepared(fixtures.find((f) => f.name === "DEMO_HST/A")!);
    const layers = new Set(module.solids.map(explodeLayer));
    expect([...layers].sort()).toEqual([0, 1, 2, 3]);
    for (const solid of module.solids) {
      const p = solidCenter(solid),
        offset = explodeLayer(solid) * explodeDistance(module.depth);
      const q: Vec3 = [p[0], p[1], p[2] + offset];
      expect(q.slice(0, 2)).toEqual(p.slice(0, 2));
      expect(q[2] - p[2]).toBe(offset);
    }
  });
  it("operates a passage leaf while the other folding leaves remain closed", () => {
    const { module } = prepared(fixtures.find((f) => f.name === "DEMO_PLEGABLE/3+0-PASO")!);
    const leaf = module.leaves.find((l) => l.fact?.advanced?.pass_through)!;
    const poses = moduleLeafPoses(module, { [leaf.leafId]: { amount: 1, mode: "pass" } });
    const f = leaf.fact!,
      a = f.advanced!;
    const points: Vec3[] = [
      [Number(f.x_mm), 0, Number(a.plane_offset_mm)],
      [Number(f.x_mm) + Number(f.width_mm), 0, Number(a.plane_offset_mm)],
    ];
    points.forEach((p, i) =>
      closeTo(transformPosePoint(p, poses[leaf.leafId]!), [
        Number(a.pass_open_plan![i]!.x_mm),
        0,
        Number(a.pass_open_plan![i]!.depth_mm),
      ]),
    );
    for (const other of module.leaves.filter((l) => l !== leaf))
      expect(poses[other.leafId]!.rotationY).toBe(0);
  });
  it("has matching interior/exterior cameras and bounded motion duration", () => {
    const { scene } = prepared(fixtures[0]!);
    const inside = cameraShot(scene, "interior", 1.5),
      outside = cameraShot(scene, "exterior", 1.5);
    expect(inside.position[2]).toBe(-outside.position[2]);
    expect(inside.target).toEqual(outside.target);
    expect(inside.fov).toBe(outside.fov);
    expect(MOTION_SECONDS).toBeLessThanOrEqual(0.28);
  });
  it("clears the HST/PSK mechanism before translating along its rail", () => {
    for (const name of ["DEMO_HST/A", "DEMO_PSK/XO"]) {
      const { module } = prepared(fixtures.find((f) => f.name === name)!);
      const leaf = module.leaves[0]!,
        authority = leaf.fact!.advanced!;
      const pose = moduleLeafPoses(module, { [leaf.leafId]: { amount: 0.25, mode: "open" } })[
        leaf.leafId
      ]!;
      expect(pose.translation[0]).toBe(0);
      expect(pose.translation[1]).toBe(Number(authority.lift_mm ?? 0));
      expect(pose.translation[2]).toBe(Number(authority.parallel_offset_mm ?? 0));
    }
  });
  it("matches the horizontal pivot's declared top/bottom depth polygon", () => {
    const { module, product } = prepared(fixtures.find((f) => f.name.startsWith("DEMO_PIVOT_H/"))!);
    const leaf = module.leaves[0]!,
      f = leaf.fact!,
      a = f.advanced!;
    const pose = moduleLeafPoses(module, { [leaf.leafId]: { amount: 1, mode: "open" } })[
      leaf.leafId
    ]!;
    const height = Number(product.assembly.modules[0]!.height_mm);
    const top = transformPosePoint(
      [Number(f.x_mm), height - Number(f.y_mm), Number(a.plane_offset_mm)],
      pose,
    );
    const bottom = transformPosePoint(
      [Number(f.x_mm), height - Number(f.y_mm) - Number(f.height_mm), Number(a.plane_offset_mm)],
      pose,
    );
    expect(top[2]).toBeCloseTo(Number(a.open_plan_polygon![0]!.depth_mm), 6);
    expect(bottom[2]).toBeCloseTo(Number(a.open_plan_polygon![2]!.depth_mm), 6);
  });
});
