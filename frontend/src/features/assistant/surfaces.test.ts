import { expect, it } from "vitest";
import { assistantText } from "./surfaces";

it("translates API opening names while preserving catalog identifiers and grounded numbers", () => {
  expect(
    assistantText(
      "TURN_LEFT y TILT_TURN_RIGHT; vidrio DEMO_60-GLASS-SAFE; 1\u2009600 × 1\u2009100 mm",
    ),
  ).toBe(
    "Abatible izquierda y Oscilobatiente derecha; vidrio DEMO_60-GLASS-SAFE; 1\u2009600 × 1\u2009100 mm",
  );
  expect(assistantText("KIT-TURN_LEFT / UNKNOWN_OPERATION")).toBe(
    "KIT-TURN_LEFT / UNKNOWN_OPERATION",
  );
});
