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

/** Business date — DD-MM-AAAA pinned to the business timezone so a sealed-at
 * timestamp never renders a different day than the document carries. */
export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const day = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (day) return `${day[3]}-${day[2]}-${day[1]}`;
  const stamp = new Date(value);
  if (Number.isNaN(stamp.getTime())) return value;
  return stamp.toLocaleDateString("es-CL", { timeZone: "America/Santiago" });
}
