import type { GlassSpecChoice } from "../../api/generated/models";
import type { IntentNode } from "../canvas/intentEditing";

export type GlassPly = {
  thickness_mm: string;
  type:
    | "FLOAT"
    | "TEMPERED"
    | "HEAT_STRENGTHENED"
    | "LOW_E"
    | "SOLAR"
    | "REFLECTIVE"
    | "MIRROR"
    | "SATIN"
    | "PRINTED";
  color: "CLEAR" | "BRONZE" | "GREY" | "GREEN";
  coating_face: number | null;
  supplier_sku: string | null;
};
export type Interlayer = {
  thickness_mm: string | null;
  type: "PVB" | "ACOUSTIC_PVB";
  density_kg_m3: string | null;
  source: string | null;
};
export type Pane = { kind: "PANE"; plies: GlassPly[]; interlayers: Interlayer[] };
export type Chamber = {
  kind: "CHAMBER";
  width_mm: string;
  spacer: "ALUMINIUM" | "WARM_EDGE" | null;
  gas: "AIR" | "ARGON" | null;
  sealant: string | null;
};
export type SupplierDatum = { value: string; source: string };
export type GlassProduct = {
  authority_id?: string | null;
  name: string;
  composition: { layers: (Pane | Chamber)[] };
  source: string;
  synthetic: boolean;
  properties: {
    ug?: SupplierDatum | null;
    solar_factor?: SupplierDatum | null;
    light_transmittance?: SupplierDatum | null;
    weight_kg_m2?: SupplierDatum | null;
    safety_class?: { value: "A" | "B" | "C"; source: string } | null;
  };
  limits: {
    source?: string | null;
    min_width_mm?: string | null;
    max_width_mm?: string | null;
    min_height_mm?: string | null;
    max_height_mm?: string | null;
    max_area_m2?: string | null;
    max_aspect_ratio?: string | null;
  };
  billing: {
    source?: string | null;
    minimum_area_m2?: string;
    tempering_sku?: string | null;
    polishing_sku?: string | null;
    drilling_sku?: string | null;
    bars_per_m_sku?: string | null;
    bars_per_crossing_sku?: string | null;
  };
};
export type GlassProcessing = {
  polished_edges: ("TOP" | "BOTTOM" | "LEFT" | "RIGHT")[];
  holes: number;
  bars_vertical: number;
  bars_horizontal: number;
};
export const NO_PROCESSING: GlassProcessing = {
  polished_edges: [],
  holes: 0,
  bars_vertical: 0,
  bars_horizontal: 0,
};
export const newPly = (): GlassPly => ({
  thickness_mm: "4",
  type: "FLOAT",
  color: "CLEAR",
  coating_face: null,
  supplier_sku: null,
});
export const newPane = (): Pane => ({ kind: "PANE", plies: [newPly()], interlayers: [] });
export function asGlassProduct(value: unknown): GlassProduct | null {
  if (!value || typeof value !== "object" || !("composition" in value) || !("name" in value))
    return null;
  return value as GlassProduct;
}
/** Assign the catalog authority and its derived bead thickness atomically. */
export function glassChoicePatch(choice: GlassSpecChoice): Partial<IntentNode> {
  return {
    glass_article_sku: choice.sku,
    glass_spec: choice.spec,
    glass_thickness_mm: choice.total_thickness_mm ?? null,
    glass_product: asGlassProduct(choice.product),
  };
}
