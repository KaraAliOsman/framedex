export type CostResult = {
  cost: string | null;
  materials: string | null;
  waste: string | null;
  labor: string | null;
  other: string | null;
  credit: string | null;
  causes: string[];
  lines: {
    id: string;
    kind: string;
    amount: string;
    waste?: string;
    quantity?: string;
    unit_cost?: string;
    hours?: string;
    hourly_rate?: string;
  }[];
};
export type Work = {
  id: string;
  code: string;
  name: string;
  revision: string;
  currency: string;
  quoted_margin: string | null;
  real_margin: string | null;
  quoted_cost: string | null;
  real_cost: string | null;
  delta_profit: string | null;
  delta_margin: string | null;
  net: string | null;
  reason: string | null;
  demo: boolean;
  discount: string | null;
  drivers: { key: string; amount: string }[];
  orders: {
    id: string;
    code: string;
    remake: boolean;
    href: string;
    source: string;
    result: CostResult;
  }[];
};
export type ActualOrder = {
  id: string;
  code: string;
  project_id: string;
  status: string;
  currency: "CLP" | "USD" | "UF" | null;
  revision: number;
  source_fingerprint: string;
  source: string;
  reason: string;
  closed: boolean;
  materials: {
    id: string;
    sku: string;
    name: string;
    unit: string;
    kind: string;
    quantity: string;
    unit_cost: string | null;
    waste_quantity: string | null;
  }[];
  labor: {
    id: string;
    label: string;
    status: string;
    hours: string | null;
    hourly_rate: string | null;
  }[];
  produced: { id: string; code: string }[];
  other_cost: string | null;
  reusable_credit: string | null;
  bars: {
    complete?: boolean;
    input_mm?: string | null;
    productive_mm?: string | null;
    waste_mm?: string | null;
    reusable_mm?: string | null;
  };
  result: CostResult;
  previous_result?: CostResult;
};
export const driverLabels: Record<string, string> = {
  materials: "Material útil y valoración",
  waste: "Merma",
  labor: "Horas laborales",
  other: "Servicios y otros costos",
  remake: "Reposición",
};
