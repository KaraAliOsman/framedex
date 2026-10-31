import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { DelegateStep } from "./DelegateStep";
import { describeInterface } from "./InterfaceStep";

describe("assistant interface and delegation receipts", () => {
  it("describes a presentation change in plain words", () => {
    expect(
      describeInterface({ text_size: "large", density: "workshop", project_tab: "quote" }),
    ).toEqual(["Densidad de taller", "Texto grande", "Las obras se abren en cotización"]);
    expect(describeInterface({ reduce_motion: false, rail_collapsed: true })).toEqual([
      "Movimiento normal",
      "Barra lateral plegada",
    ]);
  });

  it("lists proposed parallel tasks until they are approved", () => {
    render(
      <QueryClientProvider client={new QueryClient()}>
        <MemoryRouter>
          <DelegateStep
            organizationId="org-a"
            step={{
              kind: "delegate",
              label: "Dos obras en paralelo",
              tasks: [
                { goal: "Cotiza la obra A", label: "Obra A" },
                { goal: "Cotiza la obra B", label: "Obra B" },
              ],
            }}
          />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    expect(
      screen.getByRole("region", { name: "Propuesta de asistentes en paralelo" }),
    ).toBeVisible();
    expect(screen.getByText("Obra A")).toBeVisible();
    expect(screen.getByText(/con tus mismos permisos/)).toBeVisible();
  });
});
