/** Member surface palette: one place that maps a catalog material to how a
 * fenestration member is drawn — restrained, matte, engineering-drawing
 * treatments. Geometry (face widths) always comes from the catalog; only the
 * surface treatment lives here. */
import type { FinishColor } from "../../api/generated/models";
import { finishColorCss } from "./finishColors";

export interface MemberSurface {
  /** member body fill */
  fill: string;
  /** inner shadow / rebate line */
  edge: string;
  /** thin highlight line that reads as an extrusion edge */
  highlight: string;
  /** Interior detail drawn inside wide-enough members:
   *  - "chamber": the soft inner rebate line of a multi-chamber PVC profile;
   *  - "thermal": the insulated break strip that splits an aluminium profile
   *    into its interior/exterior halves;
   *  - "none": flat fill (fallback materials, non-profile surfaces). */
  detail: "chamber" | "thermal" | "none";
  /** Wood-effect finish: the drawing overlays a grain that runs along each
   * member (presentation only, never a manufacturer pattern claim). */
  grain?: boolean;
  /** A photo texture (company sample or catalog map) at physical scale. */
  texture?: { href: string; tileMm: number; grain: "ALONG" | "ACROSS" | "NONE" };
}

const SURFACES: Record<string, MemberSurface> = {
  PVC: {
    fill: "var(--member-pvc-fill)",
    edge: "var(--member-pvc-edge)",
    highlight: "var(--member-pvc-highlight)",
    detail: "chamber",
  },
  /** Foil-laminated PVC — still a multi-chamber polymer profile under
   * the film; only the skin reads wood. */
  PVC_FOIL: {
    fill: "var(--member-foil-fill)",
    edge: "var(--member-foil-edge)",
    highlight: "var(--member-foil-highlight)",
    detail: "chamber",
  },
  ALUMINIUM: {
    fill: "var(--member-aluminium-fill)",
    edge: "var(--member-aluminium-edge)",
    highlight: "var(--member-aluminium-highlight)",
    detail: "thermal",
  },
  ALUMINIUM_ANTHRACITE: {
    fill: "var(--member-anthracite-fill)",
    edge: "var(--member-anthracite-edge)",
    highlight: "var(--member-anthracite-highlight)",
    detail: "thermal",
  },
};

const DEFAULT_SURFACE = { ...SURFACES.PVC!, detail: "none" as const };

export function memberSurface(
  material: string | null | undefined,
  finish?: FinishColor,
): MemberSurface {
  const surface = SURFACES[material ?? ""] ?? DEFAULT_SURFACE;
  if (!finish) return surface;
  const presentation = (
    finish as FinishColor & {
      presentation?: { tileMm: number; grain: "ALONG" | "ACROSS" | "NONE" };
    }
  ).presentation;
  const texture = finish.texture_path
    ? {
        href: finish.texture_path,
        tileMm: presentation?.tileMm ?? 300,
        grain: presentation?.grain ?? "ALONG",
      }
    : undefined;
  return {
    ...surface,
    fill: finishColorCss(finish),
    detail: "none",
    grain: !texture && (finish.kind === "FOIL" || finish.kind === "WOOD_EFFECT"),
    ...(texture ? { texture } : {}),
  };
}
