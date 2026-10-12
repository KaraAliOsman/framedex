/** Presentation only. Values arrive from the engine; no engineering formula lives here. */
export type DecimalValue = string | number | bigint | null | undefined;
export const THIN_SPACE = "\u2009";

/** Exact sorting of engine decimals; never quantizes the underlying value. */
export function compareDecimal(a: string, b: string): number {
  const [ai = "0", af = ""] = a.replace(/^[+-]/, "").split(".");
  const [bi = "0", bf = ""] = b.replace(/^[+-]/, "").split(".");
  const digits = Math.max(af.length, bf.length);
  const av = BigInt(ai + af.padEnd(digits, "0")) * (a.startsWith("-") ? -1n : 1n);
  const bv = BigInt(bi + bf.padEnd(digits, "0")) * (b.startsWith("-") ? -1n : 1n);
  return av < bv ? -1 : av > bv ? 1 : 0;
}

function canonical(value: DecimalValue): string | null {
  if (value === null || value === undefined || value === "") return null;
  const text = String(value).trim();
  if (/^[+-]?\d+(?:\.\d+)?$/.test(text)) return text.replace(/^\+/, "");
  return null;
}

/** Backend Decimal -> editable/payload text, never localized or rounded. */
export function decimalInputValue(value: DecimalValue): string {
  const text = canonical(value);
  if (text === null) return "";
  const negative = text.startsWith("-");
  const [whole = "0", fraction = ""] = text.replace(/^-/, "").split(".");
  const integer = BigInt(whole).toString();
  const tail = fraction.replace(/0+$/, "");
  const magnitude = `${integer}${tail ? `.${tail}` : ""}`;
  return `${negative && magnitude !== "0" ? "-" : ""}${magnitude}`;
}

/** Decimal ROUND_HALF_UP, including negative ties and carry beyond Number.MAX_SAFE_INTEGER. */
export function quantize(value: DecimalValue, digits: number): string | null {
  if (!Number.isInteger(digits) || digits < 0 || digits > 12)
    throw new RangeError("Precisión inválida");
  const text = canonical(value);
  if (text === null) return null;
  const negative = text.startsWith("-");
  const [integer = "0", fraction = ""] = text.replace(/^-/, "").split(".");
  const kept = fraction.slice(0, digits).padEnd(digits, "0");
  let units = BigInt(integer + kept);
  if ((fraction[digits] ?? "0") >= "5") units += 1n;
  const magnitude = units.toString().padStart(digits + 1, "0");
  const sign = negative && units !== 0n ? "-" : "";
  return `${sign}${digits ? `${magnitude.slice(0, -digits)}.${magnitude.slice(-digits)}` : magnitude}`;
}

export function formatDecimal(value: DecimalValue, digits = 0, separator = THIN_SPACE): string {
  const rounded = quantize(value, digits);
  if (rounded === null) return "Sin dato";
  const [integer = "0", fraction] = rounded.replace(/^-/, "").split(".");
  const grouped = integer.replace(/\B(?=(\d{3})+(?!\d))/g, separator);
  return `${rounded.startsWith("-") ? "−" : ""}${grouped}${fraction ? `,${fraction}` : ""}`;
}

/** User input -> Decimal-safe string. Comma is decimal; three-digit dots are grouping. */
export function parseDecimalInput(candidate: string, precision = 2): string | null {
  const text = candidate.trim().replace(/[\s\u2009\u00a0]/g, "");
  if (!text) return null;
  const grouped = /^[+-]?\d{1,3}(?:\.\d{3})+(?:,\d+)?$/.test(text);
  const normalized = grouped ? text.replaceAll(".", "").replace(",", ".") : text.replace(",", ".");
  const match = /^([+-]?)(\d+)(?:\.(\d+))?$/.exec(normalized);
  if (!match || (match[3]?.length ?? 0) > precision) return null;
  const integer = BigInt(match[2]!).toString();
  const fraction = match[3]?.replace(/0+$/, "");
  const magnitude = `${integer}${fraction ? `.${fraction}` : ""}`;
  return `${match[1] === "-" && magnitude !== "0" ? "-" : ""}${magnitude}`;
}

export function formatMoney(value: DecimalValue, currency = "CLP"): string {
  if (canonical(value) === null) return "Sin dato";
  const digits = currency === "CLP" ? 0 : currency === "UF" ? 4 : 2;
  const prefix = currency === "CLP" ? "$" : currency === "USD" ? "US$ " : `${currency} `;
  return `${prefix}${formatDecimal(value, digits, ".")}`;
}

export function formatPercent(value: DecimalValue, kind: "fraction" | "points"): string {
  let text = canonical(value);
  if (text === null) return "Sin dato";
  if (kind === "fraction") {
    const negative = text.startsWith("-");
    const [integer = "0", fraction = ""] = text.replace(/^-/, "").split(".");
    const extended = fraction.padEnd(2, "0");
    text = `${negative ? "-" : ""}${integer}${extended.slice(0, 2)}${extended.length > 2 ? `.${extended.slice(2)}` : ""}`;
  }
  return `${formatDecimal(text, 1)} %`;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "Sin dato";
  const day = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (day) {
    const check = new Date(`${value}T12:00:00Z`);
    if (!Number.isNaN(check.getTime()) && check.toISOString().slice(0, 10) === value)
      return `${day[3]}-${day[2]}-${day[1]}`;
    return "Sin dato";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Sin dato";
  const parts = new Intl.DateTimeFormat("es-CL", {
    timeZone: "America/Santiago",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).formatToParts(date);
  const get = (type: string) => parts.find((part) => part.type === type)?.value;
  return `${get("day")}-${get("month")}-${get("year")}`;
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value || Number.isNaN(new Date(value).getTime())) return "Sin dato";
  const time = new Intl.DateTimeFormat("es-CL", {
    timeZone: "America/Santiago",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).format(new Date(value));
  return `${formatDate(value)} ${time}`;
}

export function formatRelativeTimestamp(value: string, now = Date.now()): string {
  const difference = new Date(value).getTime() - now;
  if (!Number.isFinite(difference)) return "Sin dato";
  const unit =
    Math.abs(difference) < 3600000 ? "minute" : Math.abs(difference) < 86400000 ? "hour" : "day";
  const divisor = unit === "minute" ? 60000 : unit === "hour" ? 3600000 : 86400000;
  return new Intl.RelativeTimeFormat("es-CL", { numeric: "auto" }).format(
    Math.round(difference / divisor),
    unit,
  );
}
