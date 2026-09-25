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
  /** Wood-grain axis for foil-finished members: "u" runs grain along the
   * texture's u coordinate (long box axis, contour sidewalls), "v" along v
   * (profile extrusion run, prism run). Undefined = no grain map. */
  grain?: "u" | "v";
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
  // PVC blanco stays a desaturated polymer white — the previous warm
  // (rgb(214,211,201)) cast read as tan under the key light (review M6).
  PVC: { color: "rgb(223,225,220)", roughness: 0.55, metalness: 0.08 },
  PVC_FOIL: { color: "rgb(123,90,59)", roughness: 0.5, metalness: 0.05 },
  ALUMINIUM: { color: "rgb(143,149,154)", roughness: 0.42, metalness: 0.55 },
  // Powder-coated anthracite is near-matte — the previous metalness 0.6
  // caught the environment and washed to grey (review M7 / §05-H notes).
  ALUMINIUM_ANTHRACITE: { color: "rgb(54,58,64)", roughness: 0.55, metalness: 0.35 },
};
const MEMBER_RESPONSE_DEFAULT = { color: "rgb(223,225,220)", roughness: 0.55, metalness: 0.08 };

/** Grain follows the member's run axis: a long box's long dimension, a
 * profile's extrusion direction (v), a contour ring's perimeter (u). */
function grainAxis(solid: Solid3D): "u" | "v" {
  if (solid.kind === "box") return solid.size[0] >= solid.size[1] ? "u" : "v";
  if (solid.kind === "shape") return "u";
  return "v";
}

export function solidMaterial(solid: Solid3D, mode: MaterialMode): SolidMaterial {
  const commercial = mode === "commercial";
  switch (solid.surface) {
    case "glass":
      return {
        colorToken: "--model3d-glass",
        colorFallback: "rgb(143,184,204)",
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
        colorFallback: "rgb(185,188,192)",
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
        colorFallback: "rgb(179,173,160)",
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
        colorFallback: "rgb(46,49,52)",
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
        colorFallback: "rgb(138,145,151)",
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
        colorFallback: "rgb(169,178,184)",
        roughness: commercial ? 0.3 : 0.45,
        metalness: commercial ? 0.85 : 0.55,
        transparent: false,
        opacity: 1,
        glass: false,
        detail: true,
      };
    case "spacer":
      // IGU edge spacer — mill-finish aluminium, the thin metal line at
      // the glass border; a detail surface like the bead/track.
      return {
        colorToken: "--member-aluminium-fill",
        colorFallback: "rgb(185,189,194)",
        roughness: commercial ? 0.35 : 0.6,
        metalness: commercial ? 0.7 : 0.3,
        transparent: false,
        opacity: 1,
        glass: false,
        detail: true,
      };
    case "coupler":
      return {
        colorToken: "--model3d-coupler",
        colorFallback: "rgb(93,100,105)",
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
        colorFallback: "rgb(154,160,165)",
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
        // Foil is a wood-toned skin over PVC — grain runs along the member.
        grain: solid.material === "PVC_FOIL" ? grainAxis(solid) : undefined,
      };
    }
  }
}
