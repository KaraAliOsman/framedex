import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { projectExtraServices, projectExtraServicesSave } from "../../api/generated/dekopen";
import type { ServicesResponse } from "../../api/generated/models";
import { ProjectServicesPanel } from "./ProjectServicesPanel";
import { ExtraPriceLines } from "./ExtraPriceLines";
import { extraTariff } from "./extraModel";

vi.mock("../../api/generated/dekopen", () => ({
  projectExtraServices: vi.fn(),
  projectExtraServicesSave: vi.fn(),
}));

const freight = {
  code: "FREIGHT",
  name: "Flete",
  scope: "PROJECT",
  kind: "SERVICE",
  basis: "ZONE",
  unit: "EA",
  currency: "CLP",
  selling_rate: "12000",
  source: "Transportista revisado",
  synthetic: false,
  zones: { Valdivia: { selling_rate: "12000" } },
};
const initial: ServicesResponse = {
  definitions: [freight],
  selections: [],
  lines: [],
  updated_at: "2026-10-06T12:00:00Z",
  currency: "CLP",
  locked: false,
  reason: null,
};
const response = (data: ServicesResponse) => ({
  status: 200 as const,
  data,
  headers: new Headers(),
});
function mount(canWrite = true) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <MemoryRouter>
      <QueryClientProvider client={client}>
        <ProjectServicesPanel projectId="project-a" orgId="org-a" canWrite={canWrite} />
      </QueryClientProvider>
    </MemoryRouter>,
  );
}
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(projectExtraServices).mockResolvedValue(response(initial));
});
afterEach(cleanup);

it("saves the zone as intent and uses the returned timestamp to undo a saved selection", async () => {
  vi.mocked(projectExtraServicesSave)
    .mockResolvedValueOnce(
      response({
        ...initial,
        updated_at: "2026-10-06T12:01:00Z",
        selections: [{ code: "FREIGHT", zone: "Valdivia" }],
        lines: [
          {
            code: "FREIGHT",
            name: "Flete",
            quantity: "1",
            unit: "EA",
            amount: "12000",
            selling_rate: "12000",
          },
        ],
      }),
    )
    .mockResolvedValueOnce(response({ ...initial, updated_at: "2026-10-06T12:02:00Z" }));
  mount();
  fireEvent.click(await screen.findByRole("checkbox", { name: "Flete" }));
  fireEvent.change(screen.getByRole("combobox", { name: "Zona" }), {
    target: { value: "Valdivia" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Guardar servicios" }));
  await waitFor(() =>
    expect(projectExtraServicesSave).toHaveBeenCalledWith(
      "project-a",
      {
        selections: [{ code: "FREIGHT", zone: "Valdivia" }],
        expected_updated_at: initial.updated_at,
      },
      { headers: { "X-Organization-ID": "org-a" } },
    ),
  );
  expect(await screen.findByText("$12.000", { selector: "strong" })).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Deshacer" }));
  await waitFor(() =>
    expect(projectExtraServicesSave).toHaveBeenLastCalledWith(
      "project-a",
      {
        selections: [],
        expected_updated_at: "2026-10-06T12:01:00Z",
      },
      { headers: { "X-Organization-ID": "org-a" } },
    ),
  );
  await waitFor(() => expect(screen.getByRole("checkbox", { name: "Flete" })).not.toBeChecked());
});

it("keeps a rejected selection editable without claiming it was saved", async () => {
  vi.mocked(projectExtraServicesSave).mockRejectedValue(new Error("zone required"));
  mount();
  fireEvent.click(await screen.findByRole("checkbox", { name: "Flete" }));
  fireEvent.click(screen.getByRole("button", { name: "Guardar servicios" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("No pudimos guardar los servicios");
  expect(screen.getByRole("status")).toHaveTextContent("Cambios por guardar");
  expect(screen.queryByRole("button", { name: "Deshacer" })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Descartar cambios" }));
  expect(screen.getByRole("checkbox", { name: "Flete" })).not.toBeChecked();
});

it.each([false, true])(
  "prevents edits when read permission or the sealed revision forbids them (%s)",
  async (locked) => {
    vi.mocked(projectExtraServices).mockResolvedValue(response({ ...initial, locked }));
    mount(locked);
    expect(await screen.findByRole("checkbox", { name: "Flete" })).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Guardar servicios" })).not.toBeInTheDocument();
    expect(projectExtraServicesSave).not.toHaveBeenCalled();
  },
);

it("renders the allocated net from the engine instead of multiplying the displayed rounded tariff", () => {
  render(
    <ExtraPriceLines
      currency="CLP"
      lines={[
        {
          code: "SILL",
          name: "Vierteaguas",
          quantity: "1.56",
          unit: "M",
          unit_price: "1538",
          net: "2400",
          rounding: "0.72",
          source: "Lista verificada",
          synthetic: true,
        },
      ]}
    />,
  );
  expect(screen.getByRole("cell", { name: "$2.400" })).toBeInTheDocument();
  expect(screen.getByRole("cell", { name: "1,56 m" })).toBeInTheDocument();
  expect(screen.getByText("Lista verificada")).toBeInTheDocument();
  expect(screen.getByText("Vierteaguas · DEMO")).toBeInTheDocument();
  expect(screen.getByText("0,72 CLP")).toBeInTheDocument();
  expect(extraTariff(undefined)).toBe("Sin dato");
});
