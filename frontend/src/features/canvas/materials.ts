/** Member surface palette: one place that maps a catalog material to how a
 * fenestration member is drawn — restrained, matte, engineering-drawing
 * treatments. Geometry (face widths) always comes from the catalog; only the
 * surface treatment lives here. */

export interface MemberSurface {
  /** member body fill */
  fill: string;
  /** inner shadow / rebate line */
  edge: string;
  /** thin highlight line that reads as an extrusion edge */
  highlight: string;
}

const SURFACES: Record<string, MemberSurface> = {
  PVC: {
    fill: "var(--member-pvc-fill)",
    edge: "var(--member-pvc-edge)",
    highlight: "var(--member-pvc-highlight)",
  },
  ALUMINIUM: {
    fill: "var(--member-aluminium-fill)",
    edge: "var(--member-aluminium-edge)",
    highlight: "var(--member-aluminium-highlight)",
  },
};

const DEFAULT_SURFACE = SURFACES.PVC!;

export function memberSurface(material: string | null | undefined): MemberSurface {
  return SURFACES[material ?? ""] ?? DEFAULT_SURFACE;
}
