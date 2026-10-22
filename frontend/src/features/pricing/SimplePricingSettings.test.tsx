import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import {
  pricingSimplePolicy,
  pricingSaveSimplePolicy,
  pricingSimplePolicyExample,
} from "../../api/generated/dekopen";
import type { SimplePolicyResponse } from "../../api/generated/models";
import { SimplePricingSettings } from "./SimplePricingSettings";

vi.mock("../../api/generated/dekopen", () => ({
  pricingSimplePolicy: vi.fn(),
  pricingSaveSimplePolicy: vi.fn(),
  pricingSimplePolicyExample: vi.fn(),
}));
vi.mock("./PricingPage", () => ({ PricingRulesSettings: () => <p>Reglas avanzadas</p> }));
const policy: SimplePolicyResponse = {
  currency: "CLP",
  labor_rate: "15000.1234",
  labor_basis: "M2",
  installation_rate: "10000",
  installation_basis: "WINDOW",
  margin: ".3535",
  rounding_step: "1000",
  waste: ".08",
  tax_rate: ".19",
  use_advanced: false,
  revision: 3,
  saved: true,
  suggested_fields: [],
  updated_at: "2026-10-22T12:00:00Z",
};
function mount(owner = true) {
  vi.mocked(pricingSimplePolicy).mockResolvedValue({
    status: 200,
    headers: new Headers(),
    data: policy,
  });
  vi.mocked(pricingSimplePolicyExample).mockResolvedValue({
    status: 200,
    headers: new Headers(),
    data: {
      position_id: null,
      position_index: null,
      currency: "CLP",
      breakdown: null,
      project_net: null,
      project_tax: null,
      project_gross: null,
      assumptions: {},
      detail: "Crea una ventana para ver el precio con tus materiales.",
    },
  });
  return render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <MemoryRouter>
        <SimplePricingSettings orgId="org" owner={owner} />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});

it("keeps decimal input exact and sends one reviewed policy revision", async () => {
  mount();
  const margin = await screen.findByRole("textbox", { name: "Margen sobre venta" });
  expect(margin).toHaveValue("35,35");
  expect(screen.getByRole("textbox", { name: "Mano de obra" })).toHaveValue("15000,1234");
  fireEvent.change(margin, { target: { value: "42,75" } });
  vi.mocked(pricingSaveSimplePolicy).mockResolvedValue({
    status: 200,
    headers: new Headers(),
    data: { ...policy, margin: ".4275", revision: 4 },
  });
  fireEvent.click(screen.getByRole("button", { name: "Guardar mis precios" }));
  await screen.findByText(/Precios guardados/);
  expect(pricingSaveSimplePolicy).toHaveBeenCalledWith(
    {
      values: {
        currency: "CLP",
        labor_rate: "15000.1234",
        labor_basis: "M2",
        installation_rate: "10000",
        installation_basis: "WINDOW",
        margin: "0.4275",
        rounding_step: "1000",
        waste: "0.08",
        tax_rate: "0.19",
        use_advanced: false,
      },
      expected_revision: 3,
      reason: "Configuración de precios de mi empresa",
    },
    expect.anything(),
  );
});

it("does not save invalid margin or silently replace a conflict draft", async () => {
  mount();
  const margin = await screen.findByRole("textbox", { name: "Margen sobre venta" });
  fireEvent.change(margin, { target: { value: "100" } });
  expect(screen.getByRole("button", { name: "Guardar mis precios" })).toBeDisabled();
  fireEvent.change(margin, { target: { value: "48,25" } });
  vi.mocked(pricingSaveSimplePolicy).mockResolvedValue({
    status: 409,
    headers: new Headers(),
    data: {
      error: {
        code: "stale_workshop_policy",
        detail: "Tus precios cambiaron. Recarga para compararlos.",
      },
    },
  });
  fireEvent.click(screen.getByRole("button", { name: "Guardar mis precios" }));
  await screen.findByText("Tus precios cambiaron. Recarga para compararlos.");
  expect(margin).toHaveValue("48,25");
  expect(screen.getByRole("button", { name: "Recargar configuración" })).toBeVisible();
});

it("hides advanced rules until their toggle is saved", async () => {
  mount();
  const toggle = await screen.findByRole("switch", { name: "Usar precios avanzados" });
  expect(screen.queryByText("Reglas avanzadas")).not.toBeInTheDocument();
  fireEvent.click(toggle);
  expect(screen.queryByText("Reglas avanzadas")).not.toBeInTheDocument();
  vi.mocked(pricingSaveSimplePolicy).mockResolvedValue({
    status: 200,
    headers: new Headers(),
    data: { ...policy, use_advanced: true, revision: 4 },
  });
  fireEvent.click(screen.getByRole("button", { name: "Guardar mis precios" }));
  await screen.findByText("Reglas avanzadas");
});

it("never requests private prices for an estimator", () => {
  mount(false);
  expect(screen.getByText(/El dueño configura los costos/)).toBeVisible();
  expect(pricingSimplePolicy).not.toHaveBeenCalled();
});

it("replaces a pending example and never shows its late response", async () => {
  mount();
  const margin = await screen.findByRole("textbox", { name: "Margen sobre venta" });
  let finish: ((value: Awaited<ReturnType<typeof pricingSimplePolicyExample>>) => void) | undefined;
  vi.mocked(pricingSimplePolicyExample).mockImplementationOnce(
    () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  );
  await waitFor(() => expect(pricingSimplePolicyExample).toHaveBeenCalledTimes(1));
  fireEvent.change(margin, { target: { value: "40" } });
  await screen.findByText("Crea una ventana para ver el precio con tus materiales.");
  finish?.({
    status: 200,
    headers: new Headers(),
    data: {
      position_id: null,
      position_index: null,
      currency: "CLP",
      breakdown: null,
      project_net: null,
      project_tax: null,
      project_gross: null,
      assumptions: {},
      detail: "Respuesta anterior",
    },
  });
  await waitFor(() => expect(screen.queryByText("Respuesta anterior")).not.toBeInTheDocument());
});
