import type { ProjectResponse, StageEnum } from "../../api/generated/models";
import type { StatusTone } from "../../ui/StatusBadge";

export const workStages: Record<StageEnum, string> = {
  QUOTING: "Cotizando",
  SENT: "Enviada",
  ACCEPTED: "Aceptada",
  WORKSHOP: "En taller",
  INSTALLED: "Instalada",
  TO_COLLECT: "Por cobrar",
  CLOSED: "Cerrada",
  CANCELLED: "Cancelada",
};
export const workStageTone: Record<StageEnum, StatusTone> = {
  QUOTING: "warning",
  SENT: "neutral",
  ACCEPTED: "success",
  WORKSHOP: "info",
  INSTALLED: "success",
  TO_COLLECT: "person",
  CLOSED: "neutral",
  CANCELLED: "neutral",
};
export const legacyStatuses: Record<string, string> = {
  DRAFT: "Borrador",
  QUOTED: "Cotizada",
  APPROVED: "Aprobada",
  IN_PRODUCTION: "En producción",
  COMPLETED: "Terminada",
  CANCELLED: "Cancelada",
};

export function pageOffset(value: string | null): number {
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) && parsed > 0 ? Math.floor(parsed / 50) * 50 : 0;
}

export function filterWorks(
  items: ProjectResponse[],
  search: string,
  status: string,
  sort: string,
) {
  const needle = search.trim().toLocaleLowerCase("es-CL");
  return items
    .filter(
      (item) =>
        (!status || item.status === status) &&
        `${item.code} ${item.name} ${item.client_name}`.toLocaleLowerCase("es-CL").includes(needle),
    )
    .sort(
      (a, b) =>
        (sort === "name"
          ? (a.name || a.code).localeCompare(b.name || b.code, "es-CL")
          : b.updated_at.localeCompare(a.updated_at)) || a.id.localeCompare(b.id),
    );
}

/** Issued selection wins; an unpriced successor never inherits its amount. */
export function workAmount(item: ProjectResponse) {
  if (
    item.progress?.quoted_total !== null &&
    item.progress?.quoted_total !== undefined &&
    item.progress.currency
  )
    return {
      value: item.progress.quoted_total,
      currency: item.progress.currency,
      origin: "Total de la cotización vigente",
    };
  if (item.pricing_current)
    return {
      value: item.total_price_gross,
      currency: item.currency,
      origin: "Precio aplicado de esta revisión",
    };
  return null;
}
