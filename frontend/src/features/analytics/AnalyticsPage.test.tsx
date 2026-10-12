import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  analyticsDecisionWorkspace,
  analyticsActualReport,
  analyticsActualReportPreview,
  analyticsActualReportSave,
} from "../../api/generated/dekopen";
import { AnalyticsPage } from "./AnalyticsPage";
import { CostClosure } from "./CostClosure";
import type { ActualOrder } from "./types";

const identity = vi.hoisted(() => ({ id: "tenant-a", role: "OWNER" }));
vi.mock("../../auth/AuthSessionProvider", () => ({
  useAuthSession: () => ({ me: { active_organization: identity } }),
}));
vi.mock("../../api/generated/dekopen", () => ({
  analyticsDecisionWorkspace: vi.fn(),
  analyticsActualReport: vi.fn(),
  analyticsActualReportPreview: vi.fn(),
  analyticsActualReportSave: vi.fn(),
}));
const metric = {
  key: "conversion",
  label: "Conversión",
  group: "sales",
  value: "0.25",
  unit: "fraction",
  currency: null,
  reason: null,
  formula: "Aprobadas ÷ emitidas de la cohorte",
  source: "emissions.sql",
  definition: "/analytics?definition=conversion",
  missing: 0,
  details: [
    {
      code: "P-001",
      label: "Revisión A elegida",
      href: "/projects/one",
      value: "1",
      unit: "count",
      currency: null,
      reason: null,
    },
  ],
};
const workspace = {
  start: "2026-10-01",
  end: "2026-10-31",
  as_of: "2026-10-13T12:00:00Z",
  metrics: [metric],
  works: [],
  source: "SQL por organización",
  empty: false,
};
function show(path = "/analytics?view=sales") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AnalyticsPage />
    </MemoryRouter>,
  );
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
  vi.clearAllMocks();
  identity.role = "OWNER";
  vi.mocked(analyticsDecisionWorkspace).mockResolvedValue({ data: workspace } as never);
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("denies cost readers outside the authorized roles before any request", () => {
  identity.role = "ESTIMATOR";
  show();
  expect(screen.getByText(/El dueño y el jefe de taller pueden leer/)).toBeTruthy();
  expect(analyticsDecisionWorkspace).not.toHaveBeenCalled();
});

it("F6 opens the focused metric with definition and exact source destination", async () => {
  show();
  const value = await screen.findByRole("button", { name: "Conversión: ver fuente" });
  value.focus();
  fireEvent.keyDown(window, { key: "F6" });
  const dialog = await screen.findByRole("dialog", { name: "Conversión" });
  expect(within(dialog).getByText("Aprobadas ÷ emitidas de la cohorte")).toBeTruthy();
  expect(within(dialog).getByRole("link", { name: "P-001" }).getAttribute("href")).toBe(
    "/projects/one",
  );
  expect(within(dialog).getByText("25,0 %")).toBeTruthy();
  fireEvent.keyDown(document, { key: "Escape" });
  await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
  expect(document.activeElement).toBe(value);
});

it("keeps missing data and its cause visible, without a zero", async () => {
  vi.mocked(analyticsDecisionWorkspace).mockResolvedValue({
    data: {
      ...workspace,
      metrics: [{ ...metric, value: null, reason: "Falta la decisión", missing: 1 }],
    },
  } as never);
  show();
  expect(await screen.findByText("Sin datos suficientes")).toBeTruthy();
  expect(screen.getByText("Falta la decisión")).toBeTruthy();
  expect(screen.queryByText("0,0 %")).toBeNull();
});

it("retains the period when a retry follows a failed read", async () => {
  vi.mocked(analyticsDecisionWorkspace).mockRejectedValueOnce(new Error("transport"));
  show();
  await screen.findByText(/No pudimos calcular la analítica/);
  fireEvent.click(screen.getByRole("button", { name: /Reintentar/ }));
  await screen.findByRole("button", { name: "Conversión: ver fuente" });
  expect(analyticsDecisionWorkspace).toHaveBeenCalledTimes(2);
});

it("shows one action when the selected cohort has no evidence", async () => {
  vi.mocked(analyticsDecisionWorkspace).mockResolvedValue({
    data: { ...workspace, empty: true, metrics: [] },
  } as never);
  show();
  expect(await screen.findByRole("link", { name: "Abrir proyectos" })).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Conversión: ver fuente" })).toBeNull();
});

it("keeps the applied period when the initial request arrives later", async () => {
  let resolveInitial!: (response: never) => void;
  vi.mocked(analyticsDecisionWorkspace).mockImplementationOnce(
    () =>
      new Promise((resolve) => {
        resolveInitial = resolve;
      }),
  );
  vi.mocked(analyticsDecisionWorkspace).mockResolvedValueOnce({
    data: { ...workspace, start: "2020-01-01", end: "2020-01-31", empty: true, metrics: [] },
  } as never);
  show();
  fireEvent.change(screen.getByLabelText("Desde"), { target: { value: "2020-01-01" } });
  fireEvent.change(screen.getByLabelText("Hasta"), { target: { value: "2020-01-31" } });
  fireEvent.submit(screen.getByLabelText("Desde").closest("form")!);
  await screen.findByRole("link", { name: "Abrir proyectos" });
  resolveInitial({ data: workspace } as never);
  await waitFor(() =>
    expect((screen.getByLabelText("Desde") as HTMLInputElement).value).toBe("2020-01-01"),
  );
  expect(screen.queryByRole("button", { name: "Conversión: ver fuente" })).toBeNull();
});

it("requires preview and a second human click to register the immutable cost revision", async () => {
  const order: ActualOrder = {
    id: "order",
    code: "OT-001",
    project_id: "one",
    status: "COMPLETED",
    currency: "CLP",
    revision: 0,
    source_fingerprint: "a".repeat(64),
    source: "Libro de taller",
    reason: "",
    closed: false,
    materials: [
      {
        id: "m",
        sku: "MARCO",
        name: "Marco",
        unit: "M",
        kind: "CONSUMPTION",
        quantity: "42",
        unit_cost: null,
        waste_quantity: null,
      },
    ],
    labor: [{ id: "s", label: "Corte", status: "DONE", hours: null, hourly_rate: null }],
    produced: [],
    other_cost: null,
    reusable_credit: null,
    bars: {},
    result: {
      cost: null,
      materials: null,
      waste: null,
      labor: null,
      other: null,
      credit: null,
      causes: ["Faltan tarifas"],
      lines: [],
    },
  };
  vi.mocked(analyticsActualReport).mockResolvedValue({ data: order } as never);
  vi.mocked(analyticsActualReportPreview).mockResolvedValue({
    data: {
      ...order,
      result: { ...order.result, cost: "500", causes: [] },
      previous_result: order.result,
    },
  } as never);
  vi.mocked(analyticsActualReportSave).mockResolvedValue({
    data: { ...order, revision: 1 },
  } as never);
  const saved = vi.fn();
  render(<CostClosure orderId="order" onClose={vi.fn()} onSaved={saved} />);
  const source = await screen.findByLabelText("Fuente de las tarifas, horas y mediciones");
  fireEvent.change(source, { target: { value: "Libro de taller" } });
  fireEvent.change(screen.getByLabelText("Motivo de este registro"), {
    target: { value: "Cierre verificado" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Revisar registro de costos" }));
  await screen.findByText("Revisa la nueva evidencia");
  expect(analyticsActualReportSave).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Registrar revisión de costos" }));
  await waitFor(() => expect(saved).toHaveBeenCalledOnce());
  expect(analyticsActualReportSave).toHaveBeenCalledWith(
    "order",
    expect.objectContaining({
      confirmed: true,
      expected_revision: 0,
      source_fingerprint: "a".repeat(64),
    }),
  );
});

it("blocks historical orders without a sealed currency before displaying or recording costs", async () => {
  vi.mocked(analyticsActualReport).mockResolvedValue({
    data: {
      id: "order",
      code: "OT-001",
      project_id: "one",
      status: "COMPLETED",
      currency: null,
      revision: 0,
      source_fingerprint: "a".repeat(64),
      source: "",
      reason: "",
      closed: false,
      materials: [],
      labor: [],
      produced: [],
      other_cost: null,
      reusable_credit: null,
      bars: {},
      result: { cost: null, causes: ["Falta moneda"], lines: [] },
    },
  } as never);
  render(
    <MemoryRouter>
      <CostClosure orderId="order" onClose={vi.fn()} onSaved={vi.fn()} />
    </MemoryRouter>,
  );
  const origin = await screen.findByRole("link", { name: "Abrir revisión de la obra" });
  expect(origin.getAttribute("href")).toBe("/projects/one?section=quote");
  expect(screen.queryByRole("button", { name: "Revisar registro de costos" })).toBeNull();
  expect(analyticsActualReportPreview).not.toHaveBeenCalled();
  expect(analyticsActualReportSave).not.toHaveBeenCalled();
});
