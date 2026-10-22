export type CatalogReading = {
  value?: unknown;
  reading?: number;
  ref?: string;
  quote?: string;
  literal?: string;
  confidence?: string;
};

export type CatalogEvidence = {
  ref?: string;
  quote?: string;
  literal?: string;
  confidence?: string;
  proposed?: unknown;
  comparison?: string;
  readings?: CatalogReading[];
};

export type CatalogReviewRow = {
  key: string;
  sheet: string;
  row: number;
  method: string;
  confidence: string;
  include: boolean;
  values: Record<string, unknown>;
  fields: Record<string, CatalogEvidence>;
  errors: Array<{ field: string; message: string }>;
  warnings: string[];
  double_read?: { identity_unique?: boolean; review_fields?: string[] };
};

export function doubleReadFields(row: CatalogReviewRow): string[] {
  return Object.entries(row.fields)
    .filter(([, evidence]) => evidence.comparison === "REVIEW")
    .map(([field]) => field);
}

export function unresolvedReadFields(row: CatalogReviewRow): string[] {
  return doubleReadFields(row).filter((key) => row.values[key] == null || row.values[key] === "");
}

export function hasDoubleReading(row: CatalogReviewRow): boolean {
  return Object.values(row.fields).some((field) => field.readings?.length === 2);
}

export function reviewRowLabel(row: CatalogReviewRow): string {
  const value = row.values.sku ?? row.values.system_code ?? row.values.code;
  return typeof value === "string" && value ? value : `Fila ${row.row}`;
}

export function readingText(value: unknown): string {
  if (value == null || value === "") return "No declarado";
  if (typeof value === "boolean") return value ? "Sí" : "No";
  return String(value);
}
