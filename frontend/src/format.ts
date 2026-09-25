/** Revision codes are storage identifiers ("REV-A"); the UI reads them as
 * document language («Revisión A»). Anything outside the pattern renders
 * unchanged — never invent a friendlier name for an unknown code. */
export function formatRevision(code: string | null | undefined): string {
  if (!code) return "—";
  const match = /^REV-([A-Z]+)$/.exec(code);
  return match ? `Revisión ${match[1]}` : code;
}

const BUSINESS_TZ = "America/Santiago";

/** Operator-facing timestamp: business timezone and minute precision — the
 * browser's locale + raw seconds never leak into the product (review m3).
 * Unparseable input renders unchanged rather than as "Invalid Date". */
export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const stamp = new Date(value);
  if (Number.isNaN(stamp.getTime())) return value;
  return stamp.toLocaleString("es-CL", {
    timeZone: BUSINESS_TZ,
    dateStyle: "short",
    timeStyle: "short",
  });
}
