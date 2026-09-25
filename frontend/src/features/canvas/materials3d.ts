import type { Solid3D } from "./Product3DScene";

/** Physical presentation materials (§05-C): the renderer's surface response
 * per catalog material and detail surface — two modes share one table.
 * TECHNICAL keeps the engineering-drawing look (matte, restrained);
 * COMMERCIAL steps toward PBR (metalness on aluminium/steel, lower
 * roughness, real glass transparency). A solid's `approximate` flag keeps
 * undeclared members visibly different from declared profiles. */

export type MaterialMode = "technical" | "commercial";

export interface SolidMaterial {
  colorToken: string;
  colorFallback: string;
  roughness: number;
  metalness: number;
  transparent: boolean;
  opacity: number;
  /** Glass gets depthWrite off + ior-ish clarity; others depth-write. */
  glass: boolean;
  /** Detail surfaces render as lines/dark in technical mode. */
  detail: boolean;
}

const MEMBER_TOKENS: Record<string, string> = {
  PVC: "--member-pvc-fill",
  PVC_FOIL: "--member-foil-fill",
  ALUMINIUM: "--member-aluminium-fill",
  ALUMINIUM_ANTHRACITE: "--member-anthracite-fill",
};

/** PBR-ish response per member material in commercial mode — aluminium
 * families read as coated metal, polymer as satin plastic, foil as a
 * wood-toned skin over PVC. Unknown materials stay neutral. */
const MEMBER_RESPONSE: Record<string, { color: string; roughness: number; metalness: number }> = {
  PVC: { color: "#d6d3c9", roughness: 0.55, metalness: 0.08 },
  PVC_FOIL: { color: "#7b5a3b", roughness: 0.5, metalness: 0.05 },
  ALUMINIUM: { color: "#8f959a", roughness: 0.42, metalness: 0.55 },
  ALUMINIUM_ANTHRACITE: { color: "#3f444a", roughness: 0.45, metalness: 0.6 },
};
const MEMBER_RESPONSE_DEFAULT = { color: "#d6d3c9", roughness: 0.55, metalness: 0.08 };

export function solidMaterial(solid: Solid3D, mode: MaterialMode): SolidMaterial {
  const commercial = mode === "commercial";
  switch (solid.surface) {
    case "glass":
      return {
        colorToken: "--model3d-glass",
        colorFallback: "#8fb8cc",
        roughness: commercial ? 0.06 : 0.15,
        metalness: 0,
        transparent: true,
        opacity: commercial ? 0.3 : 0.38,
        glass: true,
        detail: false,
      };
    case "panel":
      return {
        colorToken: "--member-panel-fill",
        colorFallback: "#b9bcc0",
        roughness: commercial ? 0.6 : 0.75,
        metalness: 0.05,
        transparent: false,
        opacity: 1,
        glass: false,
        detail: false,
      };
    case "bead":
      return {
        colorToken: "--member-pvc-edge",
        colorFallback: "#b3ada0",
        roughness: commercial ? 0.55 : 0.7,
        metalness: 0,
        transparent: false,
        opacity: 1,
        glass: false,
        detail: true,
      };
    case "gasket":
      return {
        colorToken: "--model3d-gasket",
        colorFallback: "#2e3134",
        roughness: 0.9,
        metalness: 0,
        transparent: false,
        opacity: 1,
        glass: false,
        detail: true,
      };
    case "track":
      return {
        colorToken: "--model3d-steel",
        colorFallback: "#8a9197",
        roughness: commercial ? 0.35 : 0.55,
        metalness: commercial ? 0.75 : 0.55,
        transparent: false,
        opacity: 1,
        glass: false,
        detail: true,
      };
    case "handle":
    case "hinge":
    case "fitting":
    case "support":
      return {
        colorToken: "--model3d-steel",
        colorFallback: "#a9b2b8",
        roughness: commercial ? 0.3 : 0.45,
        metalness: commercial ? 0.85 : 0.55,
        transparent: false,
        opacity: 1,
        glass: false,
        detail: true,
      };
    case "coupler":
      return {
        colorToken: "--model3d-coupler",
        colorFallback: "#5d6469",
        roughness: commercial ? 0.5 : 0.7,
        metalness: commercial ? 0.4 : 0.1,
        transparent: false,
        opacity: 1,
        glass: false,
        detail: false,
      };
    case "threshold":
      return {
        colorToken: "--member-aluminium-fill",
        colorFallback: "#9aa0a5",
        roughness: commercial ? 0.45 : 0.65,
        metalness: commercial ? 0.6 : 0.2,
        transparent: false,
        opacity: 1,
        glass: false,
        detail: false,
      };
    default: {
      const response = MEMBER_RESPONSE[solid.material] ?? MEMBER_RESPONSE_DEFAULT;
      return {
        colorToken: MEMBER_TOKENS[solid.material] ?? "--member-panel-fill",
        colorFallback: response.color,
        roughness: commercial ? response.roughness : 0.75,
        metalness: commercial ? response.metalness : 0.05,
        transparent: false,
        opacity: 1,
        glass: false,
        detail: false,
      };
    }
  }
}
