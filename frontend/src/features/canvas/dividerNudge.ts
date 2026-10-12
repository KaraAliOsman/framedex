/** Adjust a declared divider offset by whole millimetres, preserving every
 * decimal digit supplied by the engine (equal bays can have long fractions).
 * This changes human intent; the registered operation validates the result. */
export function dividerNudge(offset: string, step: number): string | null {
  const match = /^(\d+)(?:\.(\d+))?$/.exec(offset);
  if (!match || !Number.isInteger(step)) return null;
  const fraction = match[2] ?? "";
  const digits = Math.max(2, fraction.length);
  const factor = 10n ** BigInt(digits);
  const value =
    BigInt(match[1]!) * factor + BigInt(fraction.padEnd(digits, "0")) + BigInt(step) * factor;
  if (value <= 0n) return null;
  const text = value.toString().padStart(digits + 1, "0");
  return `${text.slice(0, -digits)}.${text.slice(-digits)}`;
}
