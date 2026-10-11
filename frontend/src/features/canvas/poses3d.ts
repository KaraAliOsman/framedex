import type { LeafMotion, ModuleScene, Solid3D, Vec3 } from "./Product3DScene";

/** Presentation only. Rigid transforms consume evaluated/sealed motor facts;
 * their floating-point projection never feeds dimensions or fabrication. */
export type LeafPoseMode = "open" | "tilt" | "pass";
export type LeafPoseState = { amount: number; mode: LeafPoseMode };
export type Pose3D = { pivot: Vec3; translation: Vec3; rotationX: number; rotationY: number };
export const MOTION_SECONDS = 0.24;
const RAD = Math.PI / 180;
const closed = (): Pose3D => ({
  pivot: [0, 0, 0],
  translation: [0, 0, 0],
  rotationX: 0,
  rotationY: 0,
});
const amount = (state?: LeafPoseState) => Math.max(0, Math.min(1, state?.amount ?? 0));

export function transformPosePoint(point: Vec3, pose: Pose3D): Vec3 {
  const [x, y, z] = point.map((v, i) => v - pose.pivot[i]!) as Vec3;
  const cx = Math.cos(pose.rotationX),
    sx = Math.sin(pose.rotationX);
  const cy = Math.cos(pose.rotationY),
    sy = Math.sin(pose.rotationY);
  const ry = y * cx - z * sx,
    rz = y * sx + z * cx;
  return [
    x * cy + rz * sy + pose.pivot[0] + pose.translation[0],
    ry + pose.pivot[1] + pose.translation[1],
    -x * sy + rz * cy + pose.pivot[2] + pose.translation[2],
  ];
}

function leafPose(motion: LeafMotion, state?: LeafPoseState): Pose3D {
  const t = amount(state),
    result = closed();
  if (!t) return result;
  const f = motion.fact,
    a = f?.advanced;
  const z = motion.pivotDepth ?? 0;
  if (a?.pass_open_plan && state?.mode === "pass") {
    const [start, end] = a.pass_open_plan;
    const x = Number(f!.x_mm),
      width = Number(f!.width_mm);
    const hingeAtLeft = Number(start.x_mm) === x && Number(start.depth_mm) === z;
    result.pivot = [hingeAtLeft ? x : x + width, 0, z];
    result.rotationY =
      -Math.atan2(
        Number(end.depth_mm) - Number(start.depth_mm),
        Number(end.x_mm) - Number(start.x_mm),
      ) * t;
    return result;
  }
  if (a && f?.opening.movement === "PIVOT_V") {
    result.pivot = [Number(a.pivot_x_mm), 0, z];
    result.rotationY =
      -Number(a.opening_angle_deg) * RAD * t * (f.opening.direction === "INWARD" ? 1 : -1);
  } else if (a && f?.opening.movement === "PIVOT_H") {
    result.pivot = [0, motion.moduleHeight! - Number(a.pivot_y_mm), z];
    result.rotationX =
      -Number(a.opening_angle_deg) * RAD * t * (f.opening.direction === "INWARD" ? 1 : -1);
  } else if (motion.kind === "vertical_slide") {
    result.translation[1] = (a?.travel === "UP" ? 1 : -1) * motion.travel * t;
  } else if (motion.kind === "slide") {
    if (a && f?.opening.movement === "PARALLEL_SLIDE" && state?.mode === "tilt") {
      result.pivot = [0, motion.tiltPivot ?? 0, z];
      result.rotationX = 10 * RAD * t * (f.opening.direction === "INWARD" ? 1 : -1);
    } else {
      // Lift/parallel clearance precedes the rail translation, and reverses
      // in the physical order on closing. Each stage follows one axis.
      const guided =
        f?.opening.movement === "LIFT_SLIDE" || f?.opening.movement === "PARALLEL_SLIDE";
      const clearance = guided ? Math.min(1, t * 4) : t;
      const sliding = guided ? Math.max(0, (t - 0.25) / 0.75) : t;
      result.translation[0] = motion.dir * motion.travel * sliding;
      result.translation[1] = Number(a?.lift_mm ?? 0) * clearance;
      result.translation[2] =
        Number(a?.parallel_offset_mm ?? 0) *
        clearance *
        (f?.opening.direction === "OUTWARD" ? -1 : 1);
    }
  } else if (motion.kind === "tilt" || (motion.kind === "tilt_turn" && state?.mode === "tilt")) {
    result.pivot = [0, motion.kind === "tilt_turn" ? (motion.tiltPivot ?? 0) : motion.pivot, z];
    result.rotationX =
      10 *
      RAD *
      t *
      (motion.kind === "tilt_turn" ? (f?.opening.direction === "OUTWARD" ? -1 : 1) : motion.dir);
  } else if (motion.kind !== "fold") {
    result.pivot = [motion.pivot, 0, z];
    result.rotationY = 32 * RAD * t * motion.dir;
  }
  return result;
}

/** Folding groups form rigid chains, not independently interpolated vertices.
 * Angles interpolate; gaps close along the carrier. At t=1 every endpoint
 * matches the motor's open plan while each leaf keeps its original length. */
export function moduleLeafPoses(
  module: ModuleScene,
  states: Record<string, LeafPoseState>,
): Record<string, Pose3D> {
  const poses = Object.fromEntries(
    module.leaves.map((leaf) => [leaf.leafId, leafPose(leaf, states[leaf.leafId])]),
  );
  const groups = new Map<string, LeafMotion[]>();
  for (const leaf of module.leaves) {
    const a = leaf.fact?.advanced;
    if (leaf.kind !== "fold" || !a?.fold_group || states[leaf.leafId]?.mode === "pass") continue;
    const key = `${leaf.fact!.bay_id}/${a.fold_group}`;
    groups.set(key, [...(groups.get(key) ?? []), leaf]);
  }
  for (const group of groups.values()) {
    group.sort((l, r) => l.fact!.advanced!.fold_index! - r.fact!.advanced!.fold_index!);
    const first = group[0]!,
      right = first.fact!.advanced!.stack_side === "RIGHT";
    const t = amount(states[first.leafId]);
    const anchorIndex = right ? 1 : 0,
      freeIndex = right ? 0 : 1;
    let anchor = first.fact!.advanced!.closed_plan[anchorIndex];
    let x = Number(anchor.x_mm),
      z = Number(anchor.depth_mm);
    for (let index = 0; index < group.length; index++) {
      const motion = group[index]!,
        f = motion.fact!,
        a = f.advanced!;
      const [s, e] = a.open_plan;
      const angle =
        Math.atan2(Number(e.depth_mm) - Number(s.depth_mm), Number(e.x_mm) - Number(s.x_mm)) * t;
      const width = Number(f.width_mm);
      const dx = width * Math.cos(angle),
        dz = width * Math.sin(angle);
      const startX = right ? x - dx : x,
        startZ = right ? z - dz : z;
      poses[motion.leafId] = {
        pivot: [Number(f.x_mm), 0, Number(a.plane_offset_mm)],
        rotationX: 0,
        rotationY: angle === 0 ? 0 : -angle,
        translation: [startX - Number(f.x_mm), 0, startZ - Number(a.plane_offset_mm)],
      };
      x = right ? startX : x + dx;
      z = right ? startZ : z + dz;
      const next = group[index + 1]?.fact?.advanced;
      if (next) {
        anchor = next.closed_plan[anchorIndex];
        x += (Number(anchor.x_mm) - Number(a.closed_plan[freeIndex].x_mm)) * (1 - t);
        z += (Number(anchor.depth_mm) - Number(a.closed_plan[freeIndex].depth_mm)) * (1 - t);
      }
    }
  }
  return poses;
}

/** Ordered axial layers; no horizontal or vertical displacement in despiece. */
export function explodeLayer(solid: Solid3D): number {
  if (["glass", "panel", "spacer"].includes(solid.surface)) return 3;
  if (["bead", "gasket"].includes(solid.surface)) return 2;
  return solid.leafId ? 1 : 0;
}
export function explodeDistance(depth: number): number {
  return Math.max(60, depth * 0.8);
}

export function solidCenter(solid: Solid3D): Vec3 {
  if (solid.kind === "box") return solid.center;
  if (solid.kind === "profile")
    return solid.axis === "x"
      ? [(solid.a0 + solid.a1) / 2, solid.u0, solid.v0]
      : [solid.u0, (solid.a0 + solid.a1) / 2, solid.v0];
  const xs = solid.outline.map((p) => p[0]),
    ys = solid.outline.map((p) => p[1]);
  const x = (Math.min(...xs) + Math.max(...xs)) / 2,
    y = (Math.min(...ys) + Math.max(...ys)) / 2;
  return solid.kind === "prism"
    ? [x, (solid.y0 + solid.y1) / 2, y]
    : [x, y, solid.z0 + solid.depth / 2];
}
