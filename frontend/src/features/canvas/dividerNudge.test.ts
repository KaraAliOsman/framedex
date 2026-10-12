import { expect, it } from "vitest";
import { dividerNudge } from "./dividerNudge";

it("nudges a repeating engine offset without truncating its authority", () => {
  expect(dividerNudge("733.3333333333333333333333333", 1)).toBe("734.3333333333333333333333333");
  expect(dividerNudge("733.3333333333333333333333333", -10)).toBe("723.3333333333333333333333333");
  expect(dividerNudge("700", 10)).toBe("710.00");
  expect(dividerNudge("0.50", -1)).toBeNull();
});
