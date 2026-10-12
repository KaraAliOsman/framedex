import { describe, expect, it } from "vitest";
import { parseMoneyInput } from "./money";

describe("typed es-CL money", () => {
  it.each(["1.50", "1.5", "1.0.0", "1,5,0", "-100", "+100", "1e3"])(
    "rejects ambiguous or unsupported input %s",
    (input) => expect(parseMoneyInput(input)).toBeNull(),
  );
  it.each([
    ["1.500.000", "1500000"],
    ["1.500.000,50", "1500000.5"],
    ["100,50", "100.5"],
    ["2 400", "2400"],
    ["9007199254740993,50", "9007199254740993.5"],
  ])("preserves the typed amount %s", (input, result) => {
    expect(parseMoneyInput(input)).toBe(result);
  });
  it("requires the currency's declared precision", () => {
    expect(parseMoneyInput("12,5", 0)).toBeNull();
    expect(parseMoneyInput("12,50", 2)).toBe("12.5");
    expect(parseMoneyInput("12,500", 2)).toBeNull();
  });
});
