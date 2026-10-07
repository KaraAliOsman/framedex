import { fmtMm, formatMoney } from "../../format";

export type ExtraSelection = {
  code: string;
  decision?: "ACCEPT" | "DISMISS";
  bay_id?: string | null;
  leaf_id?: string | null;
  sides?: ("TOP" | "RIGHT" | "BOTTOM" | "LEFT")[] | null;
  overhang_left_mm?: string;
  overhang_right_mm?: string;
  zone?: string | null;
};

export type ExtraDefinition = {
  code: string;
  name: string;
  scope: "POSITION" | "PROJECT";
  kind: "PROFILE" | "SCREEN" | "FITTING" | "SERVICE";
  basis:
    "SILL" | "SIDES" | "WINDOW" | "LEAF" | "AREA" | "PERIMETER" | "PER_POSITION" | "FIXED" | "ZONE";
  unit: "M" | "M2" | "EA";
  currency: "CLP" | "USD";
  cost_rate?: string;
  selling_rate: string;
  source: string;
  synthetic: boolean;
  profile_role?: string | null;
  sku?: string | null;
  default_sides?: ExtraSelection["sides"];
  default_overhang_mm?: string;
  suggestion?: "NONE" | "WINDOW" | "MOVING_LEAF" | "OPENING_GAP";
  allowed_movements?: string[];
  replaces_handle?: boolean;
  installation?: boolean;
  zones?: Record<string, { cost_rate?: string; selling_rate: string }>;
};

export type ExtraAuthority = { schema_version: 1; definitions: ExtraDefinition[]; source: string };
export type ExtraPolicy = {
  schema_version: 1;
  services: ExtraDefinition[];
  position_defaults: ExtraSelection[];
  document_prices: "ITEMIZED" | "GROUPED";
};
export type ExtraLine = {
  rounding?: string;
  code: string;
  name: string;
  quantity: string;
  unit: string;
  selling_rate?: string;
  unit_price?: string;
  amount?: string;
  net?: string;
  source?: string;
  synthetic?: boolean;
  width_mm?: string | null;
  height_mm?: string | null;
};
export type ExtraSuggestion = {
  selection: ExtraSelection;
  name: string;
  cause: string;
  source: string;
};

export const extraBasisLabels: Record<string, string> = {
  SILL: "Ancho y vuelos",
  SIDES: "Largos por lado",
  WINDOW: "Por vano",
  LEAF: "Por hoja",
  AREA: "Por m²",
  PERIMETER: "Por perímetro",
  PER_POSITION: "Por posición",
  FIXED: "Fijo",
  ZONE: "Por zona",
};
export const sideLabels = {
  TOP: "Superior",
  RIGHT: "Derecho",
  BOTTOM: "Inferior",
  LEFT: "Izquierdo",
} as const;
export const extraUnit = (unit: string) => ({ M: "m", M2: "m²", EA: "un." })[unit] ?? "Sin dato";
export const extraQuantity = (value: string) => fmtMm(value);
export const extraTariff = (value: string | undefined, currency = "CLP") =>
  value === undefined ? "Sin dato" : formatMoney(value, currency);
export const hasRounding = (value: string | undefined) =>
  Boolean(value && !/^[-+]?0(?:\.0*)?$/.test(value));

export function extraDescription(item: ExtraDefinition): string {
  return `${item.name} · ${extraBasisLabels[item.basis]} · costo ${extraTariff(item.cost_rate, item.currency)}/${extraUnit(item.unit)} · venta ${extraTariff(item.selling_rate, item.currency)}/${extraUnit(item.unit)} · ${item.source}${item.synthetic ? " · DEMO" : ""}`;
}

export function extraImportSummary(value: unknown): string[] {
  if (!value || typeof value !== "object") return [];
  const record = value as Partial<ExtraAuthority & ExtraPolicy>;
  const lines = definitions(record.definitions ?? record.services).map(extraDescription);
  if (record.document_prices)
    lines.push(record.document_prices === "ITEMIZED" ? "Sublíneas con precio" : "Precio agrupado");
  if (record.position_defaults)
    lines.push(`${record.position_defaults.length} extras en la plantilla de posiciones nuevas`);
  return lines;
}

export function definitions(value: unknown): ExtraDefinition[] {
  return Array.isArray(value)
    ? value.filter((item): item is ExtraDefinition =>
        Boolean(
          item &&
          typeof item === "object" &&
          typeof item.code === "string" &&
          typeof item.name === "string" &&
          typeof item.basis === "string",
        ),
      )
    : [];
}
export function extraLines(value: unknown): ExtraLine[] {
  return Array.isArray(value)
    ? value.filter((item): item is ExtraLine =>
        Boolean(
          item &&
          typeof item === "object" &&
          typeof item.name === "string" &&
          typeof item.quantity === "string",
        ),
      )
    : [];
}
