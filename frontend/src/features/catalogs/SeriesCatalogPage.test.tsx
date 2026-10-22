import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as api from "../../api/generated/dekopen";
import type { SystemResponse } from "../../api/generated/models";
import { catalogGroups, SeriesCatalogPage } from "./SeriesCatalogPage";
import { sheetFixture } from "./seriesSheet.test.fixtures";

const identity = vi.hoisted(() => ({ role: "OWNER" }));
vi.mock("../../auth/AuthSessionProvider", () => ({
  useAuthSession: () => ({
    status: "ready",
    session: { user: { id: "owner" } },
    me: { active_organization: { id: "org", role: identity.role } },
  }),
}));
vi.mock("../../api/generated/dekopen", () => ({
  catalogSystemList: vi.fn(),
  catalogFamilyTemplates: vi.fn(),
  catalogSeriesCreate: vi.fn(),
  catalogReferenceSeries: vi.fn(),
}));
vi.mock("./SeriesSheetView", () => ({
  SeriesSheetView: ({ systemId }: { systemId: string }) => <h1>Ficha {systemId}</h1>,
}));
vi.mock("./SeriesTrialDialog", () => ({ SeriesTrialDialog: () => null }));
vi.mock("./CatalogPage", () => ({ CatalogPage: () => <h1>Ajustes del catálogo</h1> }));
const ok = <T,>(data: T) => ({ status: 200 as const, data, headers: new Headers() });
const system = (extra: Partial<SystemResponse> = {}): SystemResponse => ({
  ...sheetFixture().tabs.rules,
  usage: sheetFixture().usage,
  ...extra,
});
afterEach(cleanup);
beforeEach(() => {
  vi.resetAllMocks();
  identity.role = "OWNER";
});

function mount(rows = [system()], initial = "/catalogs/systems") {
  vi.mocked(api.catalogSystemList).mockImplementation(async (params) =>
    ok({ items: rows.filter((row) => row.is_demo === params?.is_demo) }),
  );
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <MemoryRouter initialEntries={[initial]}>
        <SeriesCatalogPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("catalog home", () => {
  it("groups manufacturer spelling and sorts versions without merging different series", () => {
    const groups = catalogGroups([
      system({ manufacturer: " Proline ", version: 1 }),
      system({ manufacturer: "PROLINE", version: 2, id: "new" }),
      system({ manufacturer: "Proline", code: "OTHER", id: "other" }),
    ]);
    expect(groups).toHaveLength(1);
    expect(groups[0]!.series).toHaveLength(2);
    expect(groups[0]!.series[0]!.map((item) => item.version)).toEqual([2, 1]);
  });

  it("excludes examples and old versions from the count and leaves examples collapsed", async () => {
    mount([
      system({ name: "Actual", version: 2, manufacturer: "Proline" }),
      system({ id: "old", version: 1, name: "Antigua", manufacturer: "Proline" }),
      system({ id: "demo", is_demo: true, name: "Ejemplo sintético" }),
    ]);
    await screen.findByText("1 serie de tu taller");
    expect(screen.getByText("Actual")).toBeInTheDocument();
    expect(screen.queryByText("Antigua")).not.toBeInTheDocument();
    expect(document.querySelector("details")).not.toHaveAttribute("open");
    expect(api.catalogSystemList).toHaveBeenCalledTimes(1);
    expect(api.catalogSystemList).toHaveBeenCalledWith(
      { summary: true, is_demo: false, owned_only: true },
      expect.objectContaining({ headers: { "X-Organization-ID": "org" } }),
    );
    fireEvent.click(screen.getByText("Ejemplos", { exact: true }));
    await screen.findByText("Ejemplo sintético");
    expect(api.catalogSystemList).toHaveBeenCalledWith(
      { summary: true, is_demo: true },
      expect.any(Object),
    );
    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "proline" } });
    expect(screen.getByText("Actual")).toBeInTheDocument();
    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "no existe" } });
    expect(screen.getByText("Ninguna serie coincide")).toBeInTheDocument();
  });

  it("creates a real versioned template and opens the returned series", async () => {
    mount([]);
    vi.mocked(api.catalogFamilyTemplates).mockResolvedValue(
      ok({
        items: [
          {
            id: "pvc",
            version: 7,
            name: "PVC practicable",
            source_ref: "Plantilla",
            origin: "SUGGESTED",
            notes: [],
            system: {},
            profile_defaults: {},
            reinforcement_defaults: null,
            hardware_defaults: {},
            glazing_defaults: {},
            prices: [],
          },
        ],
      }),
    );
    const created = { ...sheetFixture(), id: "created" };
    vi.mocked(api.catalogSeriesCreate).mockResolvedValue({
      status: 201,
      data: created,
      headers: new Headers(),
    });
    fireEvent.click(screen.getByRole("button", { name: "Agregar serie" }));
    fireEvent.click(screen.getByRole("button", { name: "Desde una plantilla" }));
    await screen.findByRole("option", { name: "PVC practicable" });
    fireEvent.change(screen.getByLabelText("Nombre de la serie"), {
      target: { value: "Mi serie" },
    });
    fireEvent.change(screen.getByLabelText("Código"), { target: { value: "MI-SERIE" } });
    fireEvent.change(screen.getByLabelText("Fabricante"), { target: { value: "Mi fabricante" } });
    fireEvent.click(screen.getByRole("button", { name: "Crear serie" }));
    await screen.findByRole("heading", { name: "Ficha created" });
    expect(api.catalogSeriesCreate).toHaveBeenCalledWith(
      {
        template_id: "pvc",
        template_version: 7,
        name: "Mi serie",
        code: "MI-SERIE",
        manufacturer: "Mi fabricante",
      },
      { headers: { "X-Organization-ID": "org" } },
    );
  });

  it("preserves old import links in the advanced catalog", async () => {
    mount([], "/catalogs/systems?import=existing");
    await screen.findByRole("heading", { name: "Ajustes del catálogo" });
    expect(api.catalogSystemList).not.toHaveBeenCalled();
  });

  it("allows an estimator to open a sheet while hiding creation", async () => {
    identity.role = "ESTIMATOR";
    mount();
    await screen.findByText("1 serie de tu taller");
    expect(screen.queryByRole("button", { name: "Agregar serie" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /PRO6004 sintética/ }));
    await screen.findByRole("heading", { name: "Ficha system" });
  });

  it("denies a role outside technical catalog access without fetching its data", () => {
    identity.role = "INSTALLER";
    mount();
    expect(screen.getByText("Tu rol no permite abrir el catálogo.")).toBeInTheDocument();
    expect(api.catalogSystemList).not.toHaveBeenCalled();
  });
});
