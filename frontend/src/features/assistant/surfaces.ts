import { domainLabels } from "../../i18n/domainLabels";

/** Keep the provider's wording and grounded numbers; translate known API
 * enums when a response quotes them. Hyphenated catalog SKUs stay intact. */
export function assistantText(value: string | undefined): string {
  return (value ?? "").replace(
    /(?<![\w-])[A-Z]+(?:_[A-Z0-9]+)+(?![\w-])/g,
    (word) => domainLabels[word] ?? word,
  );
}

/** One surface dictionary — dock, workspace, and the route map all read from
 * here so a new surface name never drifts into three spellings. The values
 * are the Spanish domain words the UI shows next to state chips and headers. */
export const SURFACE_LABELS: Record<string, string> = {
  // Job/workflow surfaces
  morning_brief: "resumen del día",
  purchase_plan: "plan de compras",
  production_plan: "plan de producción",
  quotation_complete: "completar cotización",
  project_from_documents: "proyecto desde documentos",
  catalog_compiler: "compilador de catálogo",
  customer_comms: "comunicación al cliente",
  // Route surfaces
  dashboard: "panel",
  projects: "proyectos",
  project: "proyecto",
  position: "vano",
  quotation: "cotización",
  catalog: "catálogo",
  production: "producción",
  work_order: "orden de trabajo",
  clients: "clientes",
  client: "cliente",
  purchasing: "compras",
  settings: "configuración",
  assistant: "asistente",
  jobs: "trabajos",
  onboarding: "inicio guiado",
  // Read-only engine tools share this dictionary with restored transcripts.
  calculate_position: "cálculo del vano",
  validate_position: "validación del vano",
  price_position: "venta del vano",
  price_project: "precios del proyecto",
  explain_price_delta: "diferencia de precio",
  list_catalog_options: "opciones del catálogo",
  get_blockers: "impedimentos del motor",
  simulate_ops: "simulación del diseño",
  preview_project_operations: "simulación del proyecto",
};
