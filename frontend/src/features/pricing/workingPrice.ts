import type { ProjectResponse } from "../../api/generated/models";

/** Select server money only. A cached project total is not a draft price. */
export function projectPrice(project: ProjectResponse) {
  if (project.pricing_current)
    return {
      net: project.total_price_net,
      tax: project.total_price_tax,
      gross: project.total_price_gross,
      currency: project.currency,
      ready: true,
      working: false,
    };
  const price = project.status === "DRAFT" ? project.working_price : null;
  if (!price || price.state === "BLOCKED" || price.project_gross == null) return null;
  return {
    net: price.project_net,
    tax: price.project_tax,
    gross: price.project_gross,
    currency: price.currency,
    ready: price.state === "READY",
    working: true,
  };
}

export function priceReady(project: ProjectResponse): boolean {
  return projectPrice(project)?.ready === true;
}
