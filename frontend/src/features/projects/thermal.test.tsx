import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ThermalReadout } from "./ProjectThermalPanel";
import { ThermalDelta } from "./ThermalDelta";
import type { ThermalMetric } from "./thermalModel";

const missingCause = "DEMO: catálogo sintético, sin certificación del fabricante.";
const unknown: ThermalMetric = {
  state: "UNKNOWN",
  uw: null,
  air_class: null,
  water_class: null,
  wind_class: null,
  missing: [missingCause],
  trace: null,
};

describe("autoridad térmica visible", () => {
  beforeEach(() =>
    vi.stubGlobal(
      "ResizeObserver",
      class {
        observe() {}
        disconnect() {}
        unobserve() {}
      },
    ),
  );
  afterEach(() => vi.unstubAllGlobals());
  it("explica la ausencia de fuente al abrir la traza sin sustituirla por cero", () => {
    render(<ThermalReadout metric={unknown} />);
    fireEvent.click(screen.getByRole("button", { name: "¿De dónde sale?" }));
    expect(screen.getByText(missingCause, { exact: false })).toBeVisible();
    expect(screen.queryByText("0,00 W/m²K")).not.toBeInTheDocument();
  });
  it("no calcula ni inventa un Δ cuando falta uno de los lados", () => {
    render(
      <ThermalDelta
        simulation={{ thermal_delta: { before: unknown, after: unknown, delta_uw: null } }}
      />,
    );
    expect(screen.getByText(missingCause, { exact: false })).toBeVisible();
    expect(screen.queryByText("0,00 W/m²K")).not.toBeInTheDocument();
  });
  it("presenta la diferencia exacta emitida por el motor con formato chileno", () => {
    render(
      <ThermalDelta
        simulation={{
          thermal_delta: {
            before: { ...unknown, uw: "3.612" },
            after: { ...unknown, uw: "1.36624" },
            delta_uw: "-2.24576",
          },
        }}
      />,
    );
    expect(screen.getByText(/3,61 → 1,37 W\/m²K · Δ −2,25 W\/m²K/)).toBeVisible();
  });
});
