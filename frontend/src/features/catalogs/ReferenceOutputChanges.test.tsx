import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { ReferenceOutputChanges } from "./ReferenceOutputChanges";

afterEach(cleanup);
it("exposes angle-only, component-only, added and removed physical changes exactly", () => {
  render(
    <ReferenceOutputChanges
      before={{
        profile_cuts: [{ angle_left: "45.00" }],
        hardware_items: [{ sku: "001", qty: 2 }],
        panels: [{ width_mm: "1234.56" }],
      }}
      after={{
        profile_cuts: [{ angle_left: "90.00" }],
        hardware_items: [{ sku: "002", qty: 3 }],
        glasses: [{ width_mm: "1234.57" }],
      }}
    />,
  );
  expect(screen.getByText("Perfiles · 1 · Ángulo izquierdo · °")).toBeInTheDocument();
  expect(screen.getByText("45")).toBeInTheDocument();
  expect(screen.getByText("90")).toBeInTheDocument();
  expect(screen.getByText("Herrajes · 1 · Cantidad")).toBeInTheDocument();
  expect(screen.getByText("001")).toBeInTheDocument();
  expect(screen.getByText("002")).toBeInTheDocument();
  expect(screen.getByText(/1\s234,56/)).toBeInTheDocument();
  expect(screen.getByText(/1\s234,57/)).toBeInTheDocument();
});
