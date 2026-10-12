import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { DesignOptions } from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { HardwarePanel } from "./HardwarePanel";
import type { IntentNode } from "./intentEditing";
import type { ProductModuleJson } from "./productEditing";

const preview = vi.hoisted(() => vi.fn());
vi.mock("../../api/generated/dekopen", () => ({ hardwarePreview: preview }));
const resolution = {
  class_name: "Estándar",
  width_mm: "1450",
  height_mm: "2300",
  exact_leaf_weight_kg: "96.01",
  max_leaf_weight_kg: "80",
  min_leaf_width_mm: "200",
  max_leaf_width_mm: "1500",
  min_leaf_height_mm: "400",
  max_leaf_height_mm: "2400",
  source: "Ficha fabricante · página 4",
  handle_height_mm: "1000",
  handle_minimum_mm: "100",
  handle_maximum_mm: "2200",
};
const authority = {
  handles: [
    {
      code: "STANDARD",
      name: "Estándar",
      default_color: "WHITE",
      colors: [
        { code: "WHITE", name: "Blanca" },
        { code: "BLACK", name: "Negra" },
      ],
    },
    {
      code: "KEY",
      name: "Con llave",
      default_color: "WHITE",
      colors: [{ code: "WHITE", name: "Blanca" }],
    },
  ],
  default_handle: "STANDARD",
  options: [{ code: "MICRO", name: "Microventilación", source: "Ficha" }],
};
function payload() {
  return {
    leaves: [
      {
        leaf_id: null,
        editable: true,
        message: "Hoja 96.01 kg: la clase estándar admite 80 kg.",
        recommendation_sku: "HEAVY",
        candidates: [
          {
            sku: "STANDARD",
            name: "Estándar",
            selected: true,
            compatible: false,
            resolution,
            class_authority: authority,
            contents: [
              {
                sku: "CIERRE",
                name: "Punto de cierre",
                qty: "4",
                reason: "2 + 1 por tramo",
                source: "Ficha",
                machining: [],
              },
            ],
            price_net: "10000",
            price_reason: null,
          },
          {
            sku: "HEAVY",
            name: "Pesada",
            selected: false,
            compatible: true,
            resolution: { ...resolution, class_name: "Pesada" },
            class_authority: authority,
            contents: [],
            price_net: "12500",
            delta_net: "2500",
          },
        ],
      },
    ],
    is_demo: false,
    pricing_basis: "Precio neto de herrajes por hoja",
    division: null,
  };
}
const bay = { id: "bay", type: "BAY", hardware_set_sku: "STANDARD" } as IntentNode;
const module = {
  id: "module",
  width_mm: "1500",
  height_mm: "2300",
  tree: bay,
} as ProductModuleJson;
const options = { system_id: "system", hardware_kits: [{ sku: "STANDARD" }] } as DesignOptions;
function setup(overrides: Partial<Parameters<typeof HardwarePanel>[0]> = {}) {
  const patch = vi.fn();
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <HardwarePanel
        options={options}
        module={module}
        bay={bay}
        organizationId="org"
        color="WHITE"
        busy={false}
        onPatch={patch}
        {...overrides}
      />
    </QueryClientProvider>,
  );
  return patch;
}
beforeEach(() => {
  preview.mockReset();
  preview.mockResolvedValue({ status: 200, data: payload() });
});
describe("hardware explanation and proposals", () => {
  it("shows restriction and price diff before a single typed apply", async () => {
    const patch = setup();
    await screen.findByText(/Hoja 96,0 kg/);
    fireEvent.click(screen.getByRole("button", { name: /Revisar Pesada/ }));
    expect(screen.getByRole("region", { name: "Cambio de clase propuesto" })).toHaveTextContent(
      "Δ $2.500",
    );
    expect(patch).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Aplicar clase" }));
    expect(patch).toHaveBeenCalledExactlyOnceWith({ hardware_set_sku: "HEAVY" });
  });
  it("F6 opens source and counts; sold selections are typed", async () => {
    const patch = setup();
    await screen.findByText(/Hoja 96,0 kg/);
    fireEvent.keyDown(window, { key: "F6" });
    const details = screen.getByText("Avanzado · ¿Por qué este kit?").closest("details");
    expect(details).toHaveAttribute("open");
    expect(details).toHaveTextContent("Ficha fabricante");
    fireEvent.change(screen.getByLabelText("Modelo de manilla"), { target: { value: "KEY" } });
    expect(patch).toHaveBeenLastCalledWith({
      hardware_selection: { handle_code: "KEY", color_code: "WHITE", option_codes: [] },
    });
  });
  it("passive hardware has no active selection controls", async () => {
    const data = payload();
    data.leaves[0]!.editable = false;
    preview.mockResolvedValue({ status: 200, data });
    setup();
    await screen.findByText(/Hoja 96,0 kg/);
    expect(screen.queryByLabelText("Modelo de manilla")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Revisar Pesada/ })).not.toBeInTheDocument();
  });
  it("shows unknown catalog, loading and recoverable failures", async () => {
    preview.mockRejectedValue(new ApiError(409, {}));
    setup();
    await screen.findByRole("alert");
    expect(screen.getByRole("button", { name: "Volver a resolver" })).toBeEnabled();
    preview.mockResolvedValue({ status: 200, data: payload() });
    fireEvent.click(screen.getByRole("button", { name: "Volver a resolver" }));
    await waitFor(() => expect(screen.getByText(/Hoja 96,0 kg/)).toBeInTheDocument());
  });
  it("states missing authority without a numeric default", () => {
    setup({ options: { ...options, hardware_kits: [] } });
    expect(screen.getByText(/Sin dato: esta serie/)).toBeInTheDocument();
    expect(preview).not.toHaveBeenCalled();
  });
  it("states permission failure", async () => {
    preview.mockRejectedValue(new ApiError(403, {}));
    setup();
    expect(await screen.findByText(/Tu rol no permite/)).toBeInTheDocument();
  });
  it("shows pending state while the engine resolves", () => {
    preview.mockReturnValue(new Promise(() => {}));
    setup();
    expect(
      screen.getByRole("status", { name: "Resolviendo clase y componentes" }),
    ).toHaveTextContent("Resolviendo clase");
  });
});
