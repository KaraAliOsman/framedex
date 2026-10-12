import { describe, expect, it } from "vitest";
import {
  formatDate,
  formatDateTime,
  formatDecimal,
  formatMoney,
  formatPercent,
  parseDecimalInput,
  quantize,
  decimalInputValue,
} from "./decimal";

describe("Decimal presentation", () => {
  it.each([
    ["2400", "2400"],
    ["2 400", "2400"],
    ["2.400", "2400"],
    ["1249,5", "1249.5"],
    ["-2.400,50", "-2400.5"],
  ])("normalizes %s without float", (input, expected) => {
    expect(parseDecimalInput(input)).toBe(expected);
  });
  it.each(["1.2.3", "1,2,3", "123,456", "NaN", "", "1e9"])(
    "rejects ambiguous or excess precision: %s",
    (input) => expect(parseDecimalInput(input)).toBeNull(),
  );
  it("matches engine HALF_UP including carry and negative ties", () => {
    expect(quantize("100.005", 2)).toBe("100.01");
    expect(quantize("-1.005", 2)).toBe("-1.01");
    expect(quantize("999.995", 2)).toBe("1000.00");
    expect(quantize("-0.001", 2)).toBe("0.00");
    expect(formatMoney("9007199254740993.5", "CLP")).toBe("$9.007.199.254.740.994");
  });
  it("covers zero, negative, billion, null and currencies", () => {
    expect(formatMoney("0", "CLP")).toBe("$0");
    expect(formatMoney("-1435471.5", "CLP")).toBe("$−1.435.472");
    expect(formatMoney("1000000000", "CLP")).toBe("$1.000.000.000");
    expect(formatMoney("1234.5", "USD")).toBe("US$ 1.234,50");
    expect(formatMoney("38.4521", "UF")).toBe("UF 38,4521");
    expect(formatMoney(null)).toBe("Sin dato");
    expect(formatDecimal(undefined)).toBe("Sin dato");
    expect(formatDecimal("2400")).toBe("2\u2009400");
  });
  it("requires explicit percentage authority", () => {
    expect(formatPercent("0.325", "fraction")).toBe("32,5 %");
    expect(formatPercent("32.5", "points")).toBe("32,5 %");
    expect(formatPercent("0", "fraction")).toBe("0,0 %");
  });
  it("pins civil dates and instants to Santiago", () => {
    expect(formatDate("2026-10-04")).toBe("04-10-2026");
    expect(formatDateTime("2026-10-05T02:00:00Z")).toBe("04-10-2026 23:00");
    expect(formatDate("2026-02-31")).toBe("Sin dato");
  });
  it("keeps payload decimals unlocalized and exact", () => {
    expect(decimalInputValue("1050.0000")).toBe("1050");
    expect(decimalInputValue("900.300")).toBe("900.3");
    expect(decimalInputValue("1000.3500")).toBe("1000.35");
    expect(decimalInputValue(null)).toBe("");
  });
});
