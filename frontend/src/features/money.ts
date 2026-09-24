/** Shared es-CL presentation helpers — UI mirrors the document formatter
 * (thousands "." + integer CLP) so a quote reads the same on screen and PDF. */

export function formatMoney(value: string | null | undefined, currency: string): string {
  if (value === null || value === undefined || value === "") return "—";
  return new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency,
    maximumFractionDigits: currency === "CLP" ? 0 : 2,
  }).format(Number(value));
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("es-CL", { dateStyle: "medium" }).format(new Date(value));
}
