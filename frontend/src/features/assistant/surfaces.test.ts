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

it("localizes restored prose without altering numbers, evidence URLs, routes or code", () => {
  expect(
    assistantText(
      "Veo 98 proyectos en el **dashboard**; $1.435.471. /dashboard?scope=TURN_LEFT https://dashboard.example/TURN_LEFT `dashboard` dashboard-G60",
    ),
  ).toBe(
    "Veo 98 proyectos en el **panel de inicio**; $1.435.471. /dashboard?scope=TURN_LEFT https://dashboard.example/TURN_LEFT `dashboard` dashboard-G60",
  );
});
