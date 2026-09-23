import type { DesignOptions } from "../../api/generated/models";

/** Drawing hierarchy resolved from the catalog: member face widths and the
 * system's rebate/overlap geometry. Everything optional — the demo/DOM paths
 * without options fall back to sane PVC-60 proportions so the drawing still
 * reads as a real window. */

export interface MemberSpec {
  sku: string | null;
  material: "PVC" | "ALUMINIUM" | string;
  faceWidthMm: number;
}

export interface MemberGeometry {
  frame: MemberSpec;
  sash: MemberSpec;
  mullionV: MemberSpec | null;
  mullionH: MemberSpec | null;
  threshold: MemberSpec | null;
  /** bead sightline width by glass thickness (mm). */
  beadFor(glassThicknessMm: string | null): number;
  couplerFor(sku: string | null): MemberSpec | null;
  rebateMm: number;
  sashOverlapMm: number;
}

const FALLBACK = {
  frame: 60,
  sash: 72,
  mullion: 70,
  threshold: 30,
  bead: 18,
  rebate: 20,
  sashOverlap: 8,
} as const;

function member(
  options: DesignOptions | undefined,
  role: string,
  fallbackWidth: number,
): MemberSpec {
  const profile = options?.profiles.find((item) => item.role === role);
  const faceWidth = profile ? Number(profile.face_width_mm) : NaN;
  return {
    sku: profile?.sku ?? null,
    material: profile?.material ?? "PVC",
    faceWidthMm: profile && Number.isFinite(faceWidth) && faceWidth > 0 ? faceWidth : fallbackWidth,
  };
}

export function resolveMembers(options: DesignOptions | undefined): MemberGeometry {
  const couplers = new Map<string, MemberSpec>();
  for (const item of options?.coupler_profiles ?? []) {
    const faceWidth = Number(item.face_width_mm);
    couplers.set(item.sku, {
      sku: item.sku,
      material: item.material,
      faceWidthMm: Number.isFinite(faceWidth) && faceWidth > 0 ? faceWidth : FALLBACK.mullion,
    });
  }
  const beads = new Map<string, number>();
  for (const bead of options?.glazing_beads ?? []) {
    const width = Number(bead.bead_width_mm);
    if (Number.isFinite(width) && width > 0) beads.set(bead.glass_thickness_mm, width);
  }
  const rebate = Number(options?.rebate_depth_mm);
  const sashOverlap = Number(options?.sash_overlap_mm);
  return {
    frame: member(options, "FRAME", FALLBACK.frame),
    sash: member(options, "SASH", FALLBACK.sash),
    mullionV: options?.profiles.some((item) => item.role === "MULLION_V")
      ? member(options, "MULLION_V", FALLBACK.mullion)
      : null,
    mullionH: options?.profiles.some((item) => item.role === "MULLION_H")
      ? member(options, "MULLION_H", FALLBACK.mullion)
      : null,
    threshold: options?.profiles.some((item) => item.role === "THRESHOLD")
      ? member(options, "THRESHOLD", FALLBACK.threshold)
      : null,
    beadFor(glassThicknessMm) {
      if (glassThicknessMm !== null && beads.has(glassThicknessMm))
        return beads.get(glassThicknessMm)!;
      const first = beads.values().next().value;
      return first ?? FALLBACK.bead;
    },
    couplerFor(sku) {
      return (sku ? couplers.get(sku) : undefined) ?? couplers.values().next().value ?? null;
    },
    rebateMm: Number.isFinite(rebate) && rebate > 0 ? rebate : FALLBACK.rebate,
    sashOverlapMm:
      Number.isFinite(sashOverlap) && sashOverlap >= 0 ? sashOverlap : FALLBACK.sashOverlap,
  };
}
