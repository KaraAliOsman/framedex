import { compareDecimal } from "../../decimal";
import type { ProductJson } from "../canvas/productEditing";
import type { ExtraSelection } from "./extraModel";

export function mountingGeometryChanged(
  product: ProductJson | null,
  evidence: MountingEvidence[] = [],
): boolean {
  if (!product) return evidence.length > 0;
  return evidence.some((item) => {
    const module = product.assembly.modules.find(
      (candidate) => candidate.id === item.survey.module_id,
    );
    return (
      !module ||
      compareDecimal(module.width_mm, item.result.width.fabrication_mm) !== 0 ||
      compareDecimal(module.height_mm, item.result.height.fabrication_mm) !== 0
    );
  });
}

export type Allowance = {
  clearance_mm: string;
  frame_mm: string;
  extension_mm: string;
  overlap_mm: string;
};
export type MountingRule = {
  code: string;
  name: string;
  kind: "IN_OPENING" | "SUBFRAME" | "OVERLAP" | "RENOVATION";
  source: string;
  synthetic: boolean;
  tolerance_mm: string;
  left: Allowance;
  right: Allowance;
  top: Allowance;
  bottom: Allowance;
  extras: { code: string; sides?: ExtraSelection["sides"]; decision?: "ACCEPT" }[];
};
export type OpeningSurvey = {
  module_id: string | null;
  rule_code: string;
  rule_revision: number;
  widths_mm: string[];
  heights_mm: string[];
  wall: "" | "MASONRY" | "CONCRETE" | "PARTITION" | "WOOD";
  squareness_mm: string | null;
  plumb_mm: string | null;
  origin: "CUSTOMER" | "SITE";
  override: { width_mm: string; height_mm: string; reason: string } | null;
  independent_extras?: ExtraSelection[] | null;
};
export type AxisDerivation = {
  opening_mm: string;
  spread_mm: string;
  first: Allowance;
  second: Allowance;
  first_adjustment_mm: string;
  second_adjustment_mm: string;
  derived_mm: string;
  fabrication_mm: string;
  deviation_mm: string;
};
export type MountingEvidence = {
  survey: OpeningSurvey;
  rule: MountingRule;
  result: { width: AxisDerivation; height: AxisDerivation; warnings: string[] };
};

export function reconcileIndependentExtras(
  evidence: MountingEvidence,
  before: ExtraSelection[],
  next: ExtraSelection[],
): MountingEvidence {
  const previous = new Map(before.map((item) => [item.code, item]));
  const current = new Map(next.map((item) => [item.code, item]));
  const independent = new Map(
    (evidence.survey.independent_extras ?? before).map((item) => [item.code, item]),
  );
  let changed = false;
  for (const code of new Set([...previous.keys(), ...current.keys()])) {
    if (JSON.stringify(previous.get(code)) === JSON.stringify(current.get(code))) continue;
    changed = true;
    const selected = current.get(code);
    if (selected) independent.set(code, selected);
    else independent.delete(code);
  }
  return changed
    ? { ...evidence, survey: { ...evidence.survey, independent_extras: [...independent.values()] } }
    : evidence;
}
export type MeasurementRecord = {
  generation: number;
  state: "CUSTOMER" | "SITE" | "CONFIRMED";
  current: boolean;
  measurements: MountingEvidence[];
  reason: string;
  price_change?: PriceChange | null;
};
export type PriceChange = {
  before_net: string | null;
  after_net: string | null;
  delta_net: string | null;
  currency: string | null;
  reason: string | null;
};
export type RuleRecord = { revision: number; rule: MountingRule };
export const mountingKinds: [MountingRule["kind"], string][] = [
  ["IN_OPENING", "En vano con holgura"],
  ["SUBFRAME", "Con premarco"],
  ["OVERLAP", "Sobre vano o traslapado"],
  ["RENOVATION", "Renovación sobre marco existente"],
];
export const walls: [OpeningSurvey["wall"], string][] = [
  ["MASONRY", "Albañilería"],
  ["CONCRETE", "Hormigón"],
  ["PARTITION", "Tabique"],
  ["WOOD", "Madera"],
];
