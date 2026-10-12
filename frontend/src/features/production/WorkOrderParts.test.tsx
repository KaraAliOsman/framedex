import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { WorkOrderPieces, type WorkshopPiece } from "./WorkOrderParts";
import {
  cutRoleLabel,
  opBasisLabel,
  opKindLabel,
  stationCodeLabel,
  stockKindLabel,
} from "./labels";

beforeEach(() =>
  vi.stubGlobal(
    "ResizeObserver",
    class {
      observe() {}
      disconnect() {}
    },
  ),
);
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
describe("workshop vocabulary and large sealed piece lists", () => {
  it("names known engineering facts and conceals unknown enums and policy IDs", () => {
    expect(cutRoleLabel("SASH")).toBe("Hoja");
    expect(stationCodeLabel("WELD")).toContain("Soldadura");
    expect(opKindLabel("HANDLE_PREP")).not.toContain("HANDLE_PREP");
    expect(stockKindLabel("HARDWARE_KIT")).not.toContain("HARDWARE_KIT");
    expect(opBasisLabel("handle_requirement_policy:11111111-2222-3333-4444-555555555555")).toBe(
      "Política de herraje sellada",
    );
    expect(opKindLabel("FUTURE_OPERATION")).toContain("Sin dato");
    expect(cutRoleLabel(null)).toBe("Sin dato");
  });
  it("renders fewer than 100 DOM rows for 2,000 pieces and finds a late physical label", () => {
    // Declared synthetic UI volume; these measurements do not enter production.
    const pieces: WorkshopPiece[] = Array.from({ length: 2000 }, (_, i) => ({
      id: String(i),
      code: `P01-U${String(i + 1).padStart(4, "0")}-M01`,
      position: "P01",
      unit: i + 1,
      role: "FRAME",
      sku: "DEMO-MARCO",
      length: "1000.00",
      destination: "Barra 1",
    }));
    const { container } = render(<WorkOrderPieces pieces={pieces} />);
    expect(container.querySelectorAll("tbody tr").length).toBeLessThan(100);
    expect(screen.getByRole("table")).toHaveAttribute("aria-rowcount", "2001");
    fireEvent.change(screen.getByLabelText("Filtrar piezas"), {
      target: { value: "P01-U2000-M01" },
    });
    expect(screen.getByText("P01-U2000-M01")).toBeVisible();
    expect(screen.getByRole("table")).toHaveAttribute("aria-rowcount", "2");
    expect(screen.getByText(/1\s000 mm/)).toBeVisible();
  });
});
