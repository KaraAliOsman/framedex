import type { ModuleScene, Vec3 } from "./Product3DScene";

/** A sealed site opening for one module, as the engine derived it: the
 * measured vano and, per side, the mounting rule's adjustment (overlap minus
 * clearance, frame and extension) and clearance. The view only places these
 * values; it never derives a new measure from them. */
export interface MountedOpening {
  moduleId?: string | null;
  moduleIndex: number;
  widthMm: string;
  heightMm: string;
  ruleName: string;
  synthetic: boolean;
  sides?: Record<"left" | "right" | "top" | "bottom", MountedSide> | null;
  warnings?: string[];
}

export interface MountedSide {
  adjustment_mm: string;
  clearance_mm: string;
}

export interface WallBox {
  center: Vec3;
  size: Vec3;
}

/** Masonry around the measured vano, in the module's local frame (x right,
 * y up from the sill, z through the frame depth). The frame spans
 * [0, width] × [0, height]; each vano edge sits at the frame edge moved by
 * that side's engine adjustment, so a clearance shows as a gap and an
 * overlap tucks the frame behind the reveal. Without sealed sides the vano
 * is centred on the frame — the caller labels that as approximate. */
export function mountedWallBoxes(
  module: Pick<ModuleScene, "depth">,
  frame: { width: number; height: number },
  opening: MountedOpening,
): WallBox[] {
  const vanoWidth = Number(opening.widthMm),
    vanoHeight = Number(opening.heightMm);
  if (!(vanoWidth > 0 && vanoHeight > 0 && frame.width > 0 && frame.height > 0)) return [];
  const sides = opening.sides;
  const left = sides ? Number(sides.left.adjustment_mm) : (vanoWidth - frame.width) / -2;
  const bottom = sides ? Number(sides.bottom.adjustment_mm) : (vanoHeight - frame.height) / -2;
  const x0 = left,
    x1 = x0 + vanoWidth,
    y0 = bottom,
    y1 = y0 + vanoHeight;
  if (![x0, x1, y0, y1].every(Number.isFinite)) return [];
  const border = Math.max(250, Math.max(vanoWidth, vanoHeight) * 0.25);
  const depth = Math.max(module.depth + 140, 200);
  const z = module.depth / 2;
  const height = y1 - y0 + border * 2;
  return [
    { center: [x0 - border / 2, (y0 + y1) / 2, z], size: [border, height, depth] },
    { center: [x1 + border / 2, (y0 + y1) / 2, z], size: [border, height, depth] },
    { center: [(x0 + x1) / 2, y1 + border / 2, z], size: [x1 - x0, border, depth] },
    { center: [(x0 + x1) / 2, y0 - border / 2, z], size: [x1 - x0, border, depth] },
  ];
}

/** Openings matched to scene modules: by sealed module id, else by order. */
export function openingsByModule(
  moduleIds: string[],
  openings: MountedOpening[],
): Record<string, MountedOpening> {
  const matched: Record<string, MountedOpening> = {};
  for (const opening of openings) {
    const id =
      opening.moduleId && moduleIds.includes(opening.moduleId)
        ? opening.moduleId
        : moduleIds[opening.moduleIndex - 1];
    if (id && !matched[id]) matched[id] = opening;
  }
  return matched;
}
