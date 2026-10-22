import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as api from "../../api/generated/dekopen";
import { ApiError } from "../../api/apiMutator";
import { SupplierPriceImport } from "./SupplierPriceImport";
import { SeriesPricesTable } from "./SeriesPricesTable";
import { sheetFixture } from "./seriesSheet.test.fixtures";
import { MemoryRouter } from "react-router-dom";

vi.mock("../../api/generated/dekopen", () => ({
  pricingAdminList: vi.fn(),
  pricingAdminWrite: vi.fn(),
  pricingSupplierInspect: vi.fn(),
  pricingSupplierReview: vi.fn(),
  catalogSeriesPriceHistory: vi.fn(),
  catalogSeriesSheet: vi.fn(),
}));
const ok = <T,>(data: T) => ({ status: 200 as const, data, headers: new Headers() });
const mapping = { sku: "Código", description: "Detalle", unit: "Unidad", unit_cost: "Costo" };
const inspected = {
  sheet: "Precios",
  columns: Object.values(mapping),
  suggested_mapping: mapping,
  preview: [["001", "Marco", "BARRA", "9999999999,9999"]],
  total: 500,
};
const reviewed = {
  items: [
    {
      sku: "001",
      description: "Marco",
      unit: "BAR",
      unit_cost: "9999999999.9999",
      origin: "WORKSHOP" as const,
    },
  ],
  total: 500,
  applied: false,
  review_token: "bound-token",
};
const lists = [
  {
    id: "list",
    supplier_name: "Proveedor",
    currency: "CLP",
    valid_from: "2026-10-21",
    is_active: true,
  },
  {
    id: "other",
    supplier_name: "Otro",
    currency: "USD",
    valid_from: "2026-10-22",
    is_active: true,
  },
];
afterEach(cleanup);
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(api.pricingAdminList).mockResolvedValue(ok({ items: lists }));
  vi.mocked(api.pricingSupplierInspect).mockResolvedValue(ok(inspected));
  vi.mocked(api.pricingSupplierReview).mockResolvedValue(ok(reviewed));
});
function mount() {
  const onApplied = vi.fn();
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <SupplierPriceImport orgId="org" onApplied={onApplied} />
    </QueryClientProvider>,
  );
  return onApplied;
}
async function choose() {
  fireEvent.change(screen.getByLabelText("Archivo de precios"), {
    target: { files: [new File(["csv"], "precios.csv")] },
  });
  await screen.findByText("precios.csv · hoja Precios · 500 filas");
  await screen.findByRole("option", { name: /Proveedor · CLP/ });
  fireEvent.change(screen.getByLabelText("Lista de destino"), { target: { value: "list" } });
}
async function preview() {
  await choose();
  fireEvent.click(screen.getByRole("button", { name: "Revisar todos los precios" }));
  await screen.findByRole("button", { name: "Confirmar y guardar precios" });
}
describe("mapped supplier prices", () => {
  it("inspects without writes, preserves codes and all four decimals, then applies only the reviewed token", async () => {
    const onApplied = mount();
    await preview();
    expect(api.pricingAdminWrite).not.toHaveBeenCalled();
    expect(screen.getByText("001")).toBeInTheDocument();
    expect(screen.getByText("9 999 999 999,9999 CLP")).toBeInTheDocument();
    expect(api.pricingSupplierReview).toHaveBeenLastCalledWith(
      expect.objectContaining({
        apply: false,
        mapping: JSON.stringify(mapping),
        cost_list_id: "list",
        decimal_separator: ",",
      }),
      { headers: { "X-Organization-ID": "org" } },
    );
    vi.mocked(api.pricingSupplierReview).mockResolvedValue(
      ok({ ...reviewed, applied: true, review_token: null }),
    );
    const confirm = screen.getByRole("button", { name: "Confirmar y guardar precios" });
    fireEvent.click(confirm);
    fireEvent.click(confirm);
    await screen.findByRole("heading", { name: "Precios guardados" });
    expect(api.pricingSupplierReview).toHaveBeenCalledTimes(2);
    expect(api.pricingSupplierReview).toHaveBeenLastCalledWith(
      expect.objectContaining({ apply: true, review_token: "bound-token" }),
      expect.anything(),
    );
    expect(onApplied).toHaveBeenCalledWith({
      costListId: "list",
      fileName: "precios.csv",
      total: 500,
    });
  });
  it.each(["mapping", "separator", "list", "file"])(
    "discards the previous review when %s changes",
    async (change) => {
      mount();
      await preview();
      if (change === "mapping")
        fireEvent.change(screen.getByLabelText("Código", { selector: "select" }), {
          target: { value: "Detalle" },
        });
      if (change === "separator")
        fireEvent.change(screen.getByLabelText("Separador decimal en texto"), {
          target: { value: "." },
        });
      if (change === "list")
        fireEvent.change(screen.getByLabelText("Lista de destino"), { target: { value: "other" } });
      if (change === "file")
        fireEvent.change(screen.getByLabelText("Archivo de precios"), {
          target: { files: [new File(["new"], "nueva.csv")] },
        });
      expect(
        screen.queryByRole("button", { name: "Confirmar y guardar precios" }),
      ).not.toBeInTheDocument();
      if (change === "mapping")
        expect(screen.getByRole("button", { name: "Revisar todos los precios" })).toBeDisabled();
      if (change === "file") await screen.findByText("nueva.csv · hoja Precios · 500 filas");
    },
  );
  it("keeps the mapping on server validation errors and requires a new preview after a conflict", async () => {
    mount();
    await preview();
    vi.mocked(api.pricingSupplierReview).mockRejectedValue(
      new ApiError(409, { error: { detail: "Vuelve a previsualizar." } }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Confirmar y guardar precios" }));
    await screen.findByRole("alert");
    expect(screen.getByRole("alert")).toHaveTextContent("Vuelve a previsualizar.");
    expect(screen.getByLabelText("Código", { selector: "select" })).toHaveValue("Código");
    expect(
      screen.queryByRole("button", { name: "Confirmar y guardar precios" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Revisar todos los precios" })).toBeEnabled();
  });
  it("rejects a bad replacement file without leaving the old confirmation available", async () => {
    mount();
    await preview();
    fireEvent.change(screen.getByLabelText("Archivo de precios"), {
      target: { files: [new File(["text"], "manual.pdf")] },
    });
    expect(screen.getByRole("alert")).toHaveTextContent("XLSX o CSV");
    expect(
      screen.queryByRole("button", { name: "Confirmar y guardar precios" }),
    ).not.toBeInTheDocument();
    expect(api.pricingSupplierInspect).toHaveBeenCalledTimes(1);
  });
  it("retries a failed inspection with the same selected file", async () => {
    vi.mocked(api.pricingSupplierInspect).mockRejectedValueOnce(new Error("network"));
    mount();
    const file = new File(["csv"], "precios.csv");
    fireEvent.change(screen.getByLabelText("Archivo de precios"), { target: { files: [file] } });
    fireEvent.click(await screen.findByRole("button", { name: "Volver a leer el archivo" }));
    await screen.findByText("precios.csv · hoja Precios · 500 filas");
    expect(api.pricingSupplierInspect).toHaveBeenNthCalledWith(
      2,
      { file },
      { headers: { "X-Organization-ID": "org" } },
    );
    expect(api.pricingSupplierReview).not.toHaveBeenCalled();
  });
  it("creates an empty list only on an explicit click, then selects its returned identity", async () => {
    mount();
    await choose();
    fireEvent.click(screen.getByRole("button", { name: "Crear una lista nueva" }));
    expect(api.pricingAdminWrite).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText("Proveedor"), { target: { value: "Nueva" } });
    fireEvent.change(screen.getByLabelText("Vigente desde"), { target: { value: "2026-10-22" } });
    vi.mocked(api.pricingAdminWrite).mockResolvedValue(
      ok({ items: [{ ...lists[0]!, id: "new", supplier_name: "Nueva" }] }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Crear lista" }));
    await waitFor(() => expect(screen.getByLabelText("Lista de destino")).toHaveValue("new"));
    expect(api.pricingAdminWrite).toHaveBeenCalledWith(
      "cost-lists",
      expect.objectContaining({
        values: {
          supplier_name: "Nueva",
          currency: "CLP",
          valid_from: "2026-10-22",
          is_active: true,
        },
      }),
      { headers: { "X-Organization-ID": "org" } },
    );
    expect(api.pricingSupplierReview).not.toHaveBeenCalled();
  });
  it("keeps the import action and cost-list request unavailable when the sheet denies cost access", () => {
    render(
      <QueryClientProvider client={new QueryClient()}>
        <MemoryRouter>
          <SeriesPricesTable
            orgId="org"
            sheet={sheetFixture()}
            onSaved={vi.fn()}
            onDirtyChange={vi.fn()}
          />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    expect(
      screen.queryByRole("button", { name: "Importar precios del proveedor" }),
    ).not.toBeInTheDocument();
    expect(api.pricingAdminList).not.toHaveBeenCalled();
  });
});
