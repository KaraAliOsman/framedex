/** Compatibility entry point; all presentation comes from the domain formatter. */
import { parseDecimalInput } from "../decimal";
export { formatMoney, formatDate } from "../format";
export function parseMoneyInput(text: string, precision = 2): string | null {
  if (/^[+-]/.test(text.trim())) return null;
  return parseDecimalInput(text, precision);
}
