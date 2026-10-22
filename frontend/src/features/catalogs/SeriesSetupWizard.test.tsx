import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import * as api from "../../api/generated/dekopen";
import type { SetupProgress } from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { ConfirmProvider } from "../../ui";
import { SeriesSetupWizard } from "./SeriesSetupWizard";
import { sheetFixture } from "./seriesSheet.test.fixtures";

vi.mock("../../api/generated/dekopen", () => ({
  catalogSeriesSheet: vi.fn(),
  catalogSeriesSetupProgress: vi.fn(),
  catalogSeriesSaveSetupProgress: vi.fn(),
}));
vi.mock("./CatalogImportsPanel", () => ({
  CatalogImportsPanel: ({
    setup,
  }: {
    setup: { onImport: (id: string) => void; onDirtyChange: (dirty: boolean) => void };
  }) => (
    <>
      <input aria-label="Borrador del manual" onChange={() => setup.onDirtyChange(true)} />
      <button
        onClick={() => {
          setup.onImport("manual-1");
          setup.onImport("manual-2");
        }}
      >
        Elegir dos referencias
      </button>
    </>
  ),
}));
vi.mock("./SupplierPriceImport", () => ({
  SupplierPriceImport: () => <input aria-label="Borrador de precios" />,
}));
vi.mock("./SeriesTrial", () => ({
  SeriesTrial: ({ onVerified }: { onVerified: () => void }) => (
    <button onClick={onVerified}>Verificar ensayo</button>
  ),
}));
const ok = <T,>(data: T) => ({ status: 200 as const, data, headers: new Headers() });
let progress: SetupProgress;
afterEach(cleanup);
beforeEach(() => {
  vi.resetAllMocks();
  progress = { step: 1, revision: 1, state: {} };
  vi.mocked(api.catalogSeriesSheet).mockResolvedValue(ok(sheetFixture()));
  vi.mocked(api.catalogSeriesSetupProgress).mockImplementation(async () => ok(progress));
  vi.mocked(api.catalogSeriesSaveSetupProgress).mockImplementation(async (_id, data) => {
    progress = { step: data.step, state: data.state, revision: data.revision + 1 };
    return ok(progress);
  });
});
function mount(
  owner = true,
  client = new QueryClient({ defaultOptions: { queries: { retry: false } } }),
) {
  const close = vi.fn();
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <ConfirmProvider>
          <Routes>
            <Route
              path="/"
              element={
                <SeriesSetupWizard orgId="org" systemId="system" isOwner={owner} onClose={close} />
              }
            />
            <Route path="/projects" element={<p>Obra nueva</p>} />
          </Routes>
        </ConfirmProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
  return close;
}
async function step(label: string) {
  fireEvent.click(await screen.findByRole("button", { name: label }));
  await waitFor(() =>
    expect(screen.getByRole("button", { name: label })).toHaveAttribute("aria-current", "step"),
  );
}
it("serializes writes with the previous returned revision and preserves a manual draft between steps", async () => {
  mount();
  await step("Paso 2: Manual");
  const draft = await screen.findByRole("textbox", { name: "Borrador del manual" });
  fireEvent.change(draft, { target: { value: "cita sin publicar" } });
  fireEvent.click(screen.getByRole("button", { name: "Elegir dos referencias" }));
  await waitFor(() => expect(api.catalogSeriesSaveSetupProgress).toHaveBeenCalledTimes(3));
  await waitFor(() => expect(screen.queryByText("Guardando progreso…")).not.toBeInTheDocument());
  const requests = vi.mocked(api.catalogSeriesSaveSetupProgress).mock.calls;
  expect(requests.map((call) => call[1].revision)).toEqual([1, 2, 3]);
  expect(requests[2]![1].state.manual_import_id).toBe("manual-2");
  expect(requests[2]![2]).toMatchObject({ headers: { "X-Organization-ID": "org" } });
  await step("Paso 3: Precios");
  expect(draft).toBeInTheDocument();
  expect(draft).not.toBeVisible();
  await step("Paso 2: Manual");
  expect(draft).toHaveValue("cita sin publicar");
});
it("does not overwrite another screen after a stale revision and recovers explicitly", async () => {
  mount();
  await screen.findByText("Tu serie, paso a paso");
  vi.mocked(api.catalogSeriesSaveSetupProgress).mockRejectedValueOnce(new ApiError(409, {}));
  fireEvent.click(screen.getByRole("button", { name: "Paso 2: Manual" }));
  await screen.findByRole("alert");
  expect(screen.getByRole("button", { name: "Paso 3: Precios" })).toBeDisabled();
  expect(api.catalogSeriesSaveSetupProgress).toHaveBeenCalledTimes(1);
  progress = { step: 4, revision: 12, state: { prices_file_name: "guardado.xlsx" } };
  fireEvent.click(screen.getByRole("button", { name: "Recuperar alta guardada" }));
  await screen.findByRole("button", { name: "Verificar ensayo" });
  await step("Paso 3: Precios");
  expect(api.catalogSeriesSaveSetupProgress).toHaveBeenLastCalledWith(
    "system",
    expect.objectContaining({ revision: 12, state: { prices_file_name: "guardado.xlsx" } }),
    expect.any(Object),
  );
});
it("waits for the current saved step when reopening with a stale query cache", async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  mount(true, client);
  await screen.findByText("Tu serie, paso a paso");
  cleanup();
  progress = { step: 4, revision: 8, state: {} };
  mount(true, client);
  await screen.findByRole("button", { name: "Verificar ensayo" });
  expect(screen.getByRole("button", { name: "Paso 4: Ventana de prueba" })).toHaveAttribute(
    "aria-current",
    "step",
  );
});

it("recovers the saved step without mounting purchase costs for a workshop manager", async () => {
  progress = { step: 3, revision: 8, state: {} };
  mount(false);
  await screen.findByText(/El dueño del taller puede cargar la lista/);
  expect(screen.queryByRole("textbox", { name: "Borrador de precios" })).not.toBeInTheDocument();
  expect(api.catalogSeriesSaveSetupProgress).not.toHaveBeenCalled();
});
it("uses actual quote capability and never turns visiting the final step into verification", async () => {
  const sheet = sheetFixture();
  sheet.usage.levels = [
    {
      level: "QUOTABLE",
      ok: false,
      pending: [
        {
          field: "prices",
          rule: "missing",
          origin: null,
          action: "Agrega tu lista de compra.",
          required_for: ["QUOTABLE"],
          resource: "systems",
          row_id: null,
        },
      ],
    },
  ];
  vi.mocked(api.catalogSeriesSheet).mockResolvedValue(ok(sheet));
  mount();
  await step("Paso 5: Primera cotización");
  expect(screen.getByRole("button", { name: "Crear mi primera cotización" })).toBeDisabled();
  expect(screen.getByText("Agrega tu lista de compra.")).toBeVisible();
  expect(progress.step).toBe(5);
  expect(sheet.usage.verified).toBe(false);
});
it("refreshes verification revision while retaining the other steps' unpublished draft", async () => {
  mount();
  await step("Paso 2: Manual");
  const draft = screen.getByRole("textbox", { name: "Borrador del manual" });
  fireEvent.change(draft, { target: { value: "por revisar" } });
  await step("Paso 4: Ventana de prueba");
  progress = { ...progress, step: 5, revision: progress.revision + 1 };
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "Verificar ensayo" }));
  });
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Paso 5: Primera cotización" })).toHaveAttribute(
      "aria-current",
      "step",
    ),
  );
  await step("Paso 2: Manual");
  expect(draft).toHaveValue("por revisar");
});
