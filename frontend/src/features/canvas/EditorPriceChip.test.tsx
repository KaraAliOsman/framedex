import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { EditorPriceChip } from "./EditorPriceChip";
import { useEditorPrice, type EditorPrice } from "./useEditorPrice";
import { useCanvasStore } from "./canvasStore";

vi.mock("./useEditorPrice", () => ({ useEditorPrice: vi.fn() }));

const retry = vi.fn();
const ownerPrice: EditorPrice = {
  net: "980",
  unit_net: "490",
  currency: "CLP",
  use_advanced: false,
  breakdown: {
    materials: "275.81",
    waste: "0",
    labor: "30.1234",
    installation: "12.3456",
    direct_cost: "318.279",
    exact_unit_price: "489.66",
    unit_net: "490",
    rounding: ".34",
    profit: "171.721",
    extras_cost: "0",
    extras_net: "0",
  },
  policy: {
    currency: "CLP",
    labor_rate: "30.1234",
    labor_basis: "M2",
    installation_rate: "12.3456",
    installation_basis: "WINDOW",
    margin: ".35",
    rounding_step: "10",
    waste: "0",
    tax_rate: ".19",
    use_advanced: false,
    revision: 0,
    updated_at: null,
    saved: false,
    suggested_fields: ["margin"],
  },
};

function mount(pending = false) {
  render(
    <MemoryRouter>
      <EditorPriceChip
        organizationId="org-a"
        inputs={useCanvasStore.getState().inputs}
        quantity="2"
        ready
        pending={pending}
      />
    </MemoryRouter>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Precio neto indicativo" }));
}

beforeEach(() => {
  vi.stubGlobal(
    "ResizeObserver",
    class {
      observe() {}
      unobserve() {}
      disconnect() {}
    },
  );
  vi.mocked(useEditorPrice).mockReturnValue({
    price: ownerPrice,
    calculating: false,
    error: false,
    retry,
  });
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

it("explains the unsaved simple amount, owner breakdown and suggested policy", () => {
  mount();
  expect(screen.getByText("Materiales")).toBeVisible();
  expect(screen.getByText(/Margen sobre venta: 35 %/)).toBeVisible();
  expect(screen.getByText(/guarda la ventana para actualizar el total/)).toBeVisible();
  expect(screen.getByText(/Precios de empresa sugeridos/)).toBeVisible();
  expect(screen.getByRole("link", { name: "Cómo calculo mis precios" })).toHaveAttribute(
    "href",
    "/settings/general?section=prices",
  );
  expect(screen.queryByRole("link", { name: "Revisar reglas de precio" })).toBeNull();
});

it("hides an earlier price and its private breakdown while validating another design", () => {
  mount(true);
  expect(screen.getByRole("status")).toHaveTextContent("Calculando precio");
  expect(screen.queryByText("Materiales")).toBeNull();
  expect(screen.queryByText(/980/)).toBeNull();
  expect(screen.queryByRole("link")).toBeNull();
});

it("renders sale without inventing a missing cost breakdown or policy link", () => {
  vi.mocked(useEditorPrice).mockReturnValue({
    price: { net: "980", unit_net: "490", currency: "CLP", use_advanced: false },
    calculating: false,
    error: false,
    retry,
  });
  mount();
  expect(screen.getByText(/guarda la ventana/)).toBeVisible();
  expect(screen.queryByText("Materiales")).toBeNull();
  expect(screen.queryByRole("link")).toBeNull();
});

it("recovers the live price after a read failure", () => {
  vi.mocked(useEditorPrice).mockReturnValue({
    price: undefined,
    calculating: false,
    error: true,
    retry,
  });
  mount();
  fireEvent.click(screen.getByRole("button", { name: "Reintentar precio" }));
  expect(retry).toHaveBeenCalledOnce();
  expect(screen.queryByText("Materiales")).toBeNull();
});
