/** Compatibility entry point; all presentation comes from the domain formatter. */
import { parseDecimalInput } from "../decimal";
export { formatMoney, formatDate } from "../format";
export function parseMoneyInput(text: string, precision = 2): string | null {
  const input = text.trim().replace(/[\s\u2009\u00a0]/g, "");
  // Typed money uses comma fractions and correctly grouped thousands only.
  // Backend canonical values must be localized explicitly at their input edge.
  if (!/^(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d+)?$/.test(input)) return null;
  return parseDecimalInput(input, precision);
}
