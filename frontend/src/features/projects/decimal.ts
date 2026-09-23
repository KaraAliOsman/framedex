/** Exact decimal arithmetic for millimetre values arriving as decimal strings.
 * Mirrors the Rational approach in `features/canvas/snapping.ts` — values keep
 * full precision; never pass through binary floats for bounds the engine will
 * re-check exactly. */

export type DecimalValue = {
  numerator: bigint;
  denominator: bigint;
};

export function parseDecimal(value: string): DecimalValue | null {
  const match = /^([+-]?)(\d+)(?:\.(\d*))?$/.exec(value.trim());
  if (match === null) return null;
  const sign = match[1] === "-" ? -1n : 1n;
  const whole = match[2];
  const fraction = match[3] ?? "";
  if (whole === undefined) return null;
  const denominator = 10n ** BigInt(fraction.length);
  return {
    numerator: sign * (BigInt(whole) * denominator + BigInt(fraction || "0")),
    denominator,
  };
}

export function addDecimal(a: DecimalValue, b: DecimalValue): DecimalValue {
  return {
    numerator: a.numerator * b.denominator + b.numerator * a.denominator,
    denominator: a.denominator * b.denominator,
  };
}

export function subtractDecimal(a: DecimalValue, b: DecimalValue): DecimalValue {
  return {
    numerator: a.numerator * b.denominator - b.numerator * a.denominator,
    denominator: a.denominator * b.denominator,
  };
}

export function compareDecimal(a: DecimalValue, b: DecimalValue): number {
  const left = a.numerator * b.denominator;
  const right = b.numerator * a.denominator;
  return left < right ? -1 : left > right ? 1 : 0;
}

/** Exact decimal presentation — denominators are powers of ten so the value
 * formats without rounding, trailing zeros trimmed. */
export function formatDecimal(value: DecimalValue): string {
  const negative = value.numerator < 0n;
  const magnitude = negative ? -value.numerator : value.numerator;
  const whole = magnitude / value.denominator;
  const fraction = magnitude % value.denominator;
  if (fraction === 0n) return `${negative ? "-" : ""}${whole}`;
  const digits = fraction.toString().padStart(value.denominator.toString().length - 1, "0");
  return `${negative ? "-" : ""}${whole}.${digits.replace(/0+$/, "")}`;
}
