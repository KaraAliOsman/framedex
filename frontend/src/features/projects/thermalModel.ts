import type { ThermalInput, PositionDesign } from "../../api/generated/models";

export type ThermalSource = {
  id: string;
  source_document: string;
  source_url: string;
  source_page: string;
  laboratory: string;
  laboratory_registration: string;
  report_date: string;
  valid_until: string;
  standard: string;
  applicability: string;
  reviewed_at?: string;
  reviewer_label?: string;
};
export type ThermalMetric = {
  state: "KNOWN" | "UNKNOWN";
  uw: string | null;
  missing: string[];
  air_class: number | null;
  water_class: string | null;
  wind_class: string | null;
  trace: null | {
    formula: string;
    method: string;
    area_m2: string;
    ag_m2: string;
    af_m2: string;
    lg_m: string;
    uf: string | null;
    frame_report: ThermalSource | null;
    performance_report: ThermalSource | null;
    panes: {
      bay_id: string;
      ug: string | null;
      solar_factor: string | null;
      psi_g: string | null;
      glass_report: ThermalSource | null;
      spacer_report: ThermalSource | null;
    }[];
  };
};
export type ThermalPosition = {
  position_id: string;
  position_index: number;
  location_tag: string;
  quantity: number;
  window_area_m2: string | null;
  thermal: ThermalMetric;
  verdict: "PASS" | "FAIL" | "UNKNOWN";
  causes: string[];
  group: string | null;
  minimum_air_class: number | null;
  maximum_percentage: string | null;
  actual_percentage: string | null;
  maximum_uw: string | null;
};
export type ThermalAssessment = {
  verdict: "PASS" | "FAIL" | "UNKNOWN";
  causes: string[];
  positions: ThermalPosition[];
  ogt: boolean | null;
  rules_version: string;
  source_url: string;
  source_label: string;
  scope: string;
};
export type ThermalReportData = {
  inputs: ThermalInput;
  updated_at: string | null;
  sealed: boolean;
  assessment: ThermalAssessment;
};
export type ThermalCandidate = {
  system_id: string;
  system_name: string;
  glass_sku: string;
  product: unknown;
  design: PositionDesign;
  delta_net: string;
  price: { net: string; currency: string; source: string };
  before_price: { net: string };
  assessment: ThermalPosition;
};
export const thermalVerdict = {
  PASS: "Cumple",
  FAIL: "No cumple",
  UNKNOWN: "Sin datos suficientes",
};
export const orientationLabel: Record<string, string> = {
  N: "Norte",
  E: "Oriente",
  W: "Poniente",
  S: "Sur",
  OGT: "Orientación global teórica",
  ROOF: "Techumbre",
};
