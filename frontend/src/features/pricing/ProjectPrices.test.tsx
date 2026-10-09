import { StrictMode } from "react";
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { apiMutator, ApiError } from "../../api/apiMutator";
import { CommercialPricingPage } from "./PricingPage";

const identity = vi.hoisted(() => ({ id: "tenant-a", role: "OWNER" }));
vi.mock("../../auth/AuthSessionProvider", () => ({
  useAuthSession: () => ({ me: { active_organization: identity, user: { id: "requester" } } }),
}));
vi.mock("../../api/apiMutator", () => ({
  apiMutator: vi.fn(),
  ApiError: class extends Error {
    payload: unknown;
    constructor(_status: number, payload: unknown) {
      super("API");
      this.payload = payload;
    }
  },
}));
vi.mock("../../api/generated/dekopen", () => ({
  projectsList: vi.fn().mockResolvedValue({
    status: 200,
    data: {
      items: [
        { id: "project-a", code: "P-001", name: "Casa", client_name: "Cliente", status: "DRAFT" },
        { id: "project-b", code: "P-002", name: "Casa B", status: "DRAFT" },
      ],
    },
  }),
}));

const options = {
  fx: [
    {
      id: "fx-a",
      base_currency: "USD",
      quote_currency: "CLP",
      observed_rate: "900.12345678",
      observed_date: "2026-10-09",
      effective_date: "2026-10-09",
      source: "Banco Central",
    },
  ],
  commercial_lists: [],
  band: {
    minimum_margin_pct: "0.25",
    default_margin_pct: "0.35",
    maximum_margin_pct: "0.60",
    discount_approval_pct: "0.10",
  },
};
const reading = (
  value: string,
): {
  current: string | null;
  proposed: string;
  delta: string | null;
  delta_pct: string | null;
  delta_pp: string | null;
} => ({
  current: null,
  proposed: value,
  delta: null,
  delta_pct: null,
  delta_pp: null,
});
function operation(overrides: Record<string, unknown> = {}) {
  return {
    id: null,
    project_id: "project-a",
    project_code: "P-001",
    project_name: "Casa",
    revision_code: "REV-A",
    state: "PREVIEW",
    currency: "CLP",
    costs_visible: true,
    project_net: "1000",
    project_tax: "190",
    project_gross: "1190",
    total_cost: "650",
    requested_by: "requester",
    requested_by_email: "estimador@taller.cl",
    created_at: "2026-10-09T12:00:00Z",
    reason: "Primera cotización",
    lines: [],
    services: [],
    workspace: {
      comparison: {
        net: reading("1000"),
        tax: reading("190"),
        total: reading("1190"),
        cost: reading("650"),
        margin: reading("0.35"),
      },
      cascade: {
        cost: "650",
        profit: "350",
        margin: "0.35",
        list_net: "1053",
        net: "1000",
        tax: "190",
        gross: "1190",
        closes: true,
        steps: [
          { key: "profile", amount: "300" },
          { key: "glass", amount: "300" },
          { key: "labor", amount: "50" },
          { key: "profit_at_list", amount: "403" },
          { key: "discount", amount: "-53" },
          { key: "tax", amount: "190" },
        ],
      },
      positions: [
        {
          position_index: 1,
          location: "Living",
          typology: "FIXED",
          width_mm: "1200",
          height_mm: "1400",
          quantity: 3,
          unit_cost: "216.6667",
          unit_price: "350.8772",
          line_net: "1000",
          margin: "0.35",
          delta: null,
          warnings: [],
        },
      ],
      band: { minimum: "0.25", target: "0.35", maximum: "0.60" },
      requested_margin: "0.35",
      policy: { requires_approval: false, cause_text: [] as string[] },
      sources: ["Lista de costos vigente desde 2026-10-01"],
      demo: false,
      rounding: "Se redondea una vez por línea.",
      current_revision: null,
      explanation: { available: false, reason: "Sin dato: aún no hay precio aplicado." },
    },
    ...overrides,
  };
}
function deferred() {
  let resolve!: (value: unknown) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}
let history: ReturnType<typeof operation>[];
let workspace: (body: Record<string, unknown>) => Promise<unknown>;
const calls = (suffix: string) =>
  vi.mocked(apiMutator).mock.calls.filter(([path]) => String(path).endsWith(suffix));
function page(bound = true, strict = false) {
  const ui = bound ? (
    <MemoryRouter initialEntries={["/projects/project-a/pricing"]}>
      <Routes>
        <Route path="/projects/:id/pricing" element={<CommercialPricingPage />} />
      </Routes>
    </MemoryRouter>
  ) : (
    <MemoryRouter>
      <CommercialPricingPage />
    </MemoryRouter>
  );
  return strict ? <StrictMode>{ui}</StrictMode> : ui;
}
beforeEach(() => {
  identity.id = "tenant-a";
  identity.role = "OWNER";
  history = [];
  workspace = async () => operation();
  vi.mocked(apiMutator)
    .mockReset()
    .mockImplementation(async (path, init) => {
      const route = String(path);
      const body = init.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : {};
      if (route.endsWith("options/")) return { data: options };
      if (route.endsWith("operations/")) return { data: history };
      if (route.endsWith("workspace/")) return { data: await workspace(body) };
      if (route.endsWith("preview/")) {
        const result = operation({
          id: "operation-a",
          state: identity.role === "ESTIMATOR" ? "PENDING" : "PREVIEW",
        });
        history = [result];
        return { data: result };
      }
      if (route.includes("/apply/")) {
        const result = operation({
          id: "operation-a",
          state: body.reject ? "REJECTED" : "APPLIED",
          reason: body.reason,
        });
        history = [result];
        return { data: result };
      }
      if (route.includes("/withdraw/")) {
        const result = operation({ id: "operation-a", state: "WITHDRAWN" });
        history = [result];
        return { data: result };
      }
      if (route.endsWith("acknowledge/")) return { data: { items: [] } };
      throw new Error(`Unexpected route ${route}`);
    });
});
afterEach(cleanup);

it.each(["WORKSHOP_MANAGER", "OPERATOR", "INSTALLER"])(
  "denies commercial workspace to %s without requests",
  (role) => {
    identity.role = role;
    render(page());
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(apiMutator).not.toHaveBeenCalled();
  },
);
it("mounts selling evidence and authorized FX for estimator without confidential administration", async () => {
  identity.role = "ESTIMATOR";
  render(page());
  await screen.findByRole("heading", { name: "Actual y propuesto" });
  expect(calls("options/")).toHaveLength(1);
  expect(vi.mocked(apiMutator).mock.calls.some(([url]) => String(url).includes("admin/"))).toBe(
    false,
  );
  expect(screen.queryByText("Utilidad de la obra:")).not.toBeInTheDocument();
  expect(screen.queryByText("Costo unitario")).not.toBeInTheDocument();
  expect(screen.getByText(/Margen solicitado: 35/)).toBeInTheDocument();
  fireEvent.click(screen.getByText("Moneda y autoridades"));
  fireEvent.change(screen.getByLabelText("Fecha de costos"), { target: { value: "2026-10-09" } });
  expect(screen.getByRole("option", { name: /USD → CLP.*900.*09-10-2026/ })).toBeInTheDocument();
});
it("shows authority unit and line for quantity three without deriving a unit from the line", async () => {
  render(page());
  await screen.findByText("3 unidades");
  const table = screen.getByLabelText("Tabla de posiciones");
  expect(within(table).getByText("$351")).toBeInTheDocument();
  expect(within(table).getByText("$1.000")).toBeInTheDocument();
  expect(table).toHaveTextContent("1 200 × 1 400 mm");
  expect(within(table).getAllByRole("button", { name: "¿De dónde sale?" }).length).toBeGreaterThan(
    0,
  );
});
it("reads actual margin difference in percentage points", async () => {
  const value = operation();
  value.workspace.comparison.margin = {
    current: "0.35",
    proposed: "0.20",
    delta: "-0.15",
    delta_pct: "-0.428571",
    delta_pp: "-15",
  };
  workspace = async () => value;
  render(page());
  expect(await screen.findByText("−15,0 pp")).toBeInTheDocument();
});
it("keeps a positioned missing-cost failure and a resolver link without a zero-price substitute", async () => {
  workspace = async () => {
    throw new ApiError(422, { error: { detail: "Vano 4 · falta costo vigente del vidrio." } });
  };
  render(page());
  await screen.findByRole("alert");
  expect(screen.getByRole("alert")).toHaveTextContent("Vano 4");
  expect(screen.getByRole("link", { name: "Completar costos y autoridades" })).toHaveAttribute(
    "href",
    "/pricing/cost-lists",
  );
  expect(screen.queryByText("$0")).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Aplicar" })).toBeDisabled();
});
it.each([false, true])(
  "late projection A cannot publish or release B (failure=%s)",
  async (failure) => {
    const a = deferred(),
      b = deferred();
    let count = 0;
    workspace = () => (++count === 1 ? a.promise : b.promise);
    render(page());
    await waitFor(() => expect(calls("workspace/")).toHaveLength(1));
    fireEvent.change(screen.getByLabelText("Descuento (%)"), { target: { value: "7" } });
    await waitFor(() => expect(calls("workspace/")).toHaveLength(2));
    await act(async () => {
      if (failure) a.reject(new Error("late A"));
      else a.resolve(operation({ project_net: "111" }));
    });
    expect(screen.getByRole("button", { name: "Aplicar" })).toBeDisabled();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    await act(async () => b.resolve(operation()));
    expect(await screen.findByRole("heading", { name: "Actual y propuesto" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Aplicar" })).toBeEnabled();
  },
);
it("projection B stays authoritative when A finishes later", async () => {
  const a = deferred(),
    b = deferred();
  let count = 0;
  workspace = () => (++count === 1 ? a.promise : b.promise);
  render(page());
  await waitFor(() => expect(calls("workspace/")).toHaveLength(1));
  fireEvent.change(screen.getByLabelText("Descuento (%)"), { target: { value: "5" } });
  await waitFor(() => expect(calls("workspace/")).toHaveLength(2));
  await act(async () => b.resolve(operation()));
  await screen.findByRole("heading", { name: "Actual y propuesto" });
  await act(async () => a.resolve(operation({ workspace: undefined })));
  expect(screen.getByRole("heading", { name: "Actual y propuesto" })).toBeInTheDocument();
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});
it("strict remount retains current signals and aborts requests on tenant replacement", async () => {
  const outstanding = deferred();
  workspace = () => outstanding.promise;
  const view = render(page(true, true));
  await waitFor(() => expect(calls("workspace/")).toHaveLength(1));
  const old = vi.mocked(apiMutator).mock.calls.at(-1)?.[1].signal;
  expect(old?.aborted).toBe(false);
  identity.id = "tenant-b";
  view.rerender(page(true, true));
  expect(old?.aborted).toBe(true);
  await waitFor(() =>
    expect(apiMutator).toHaveBeenLastCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({ "X-Organization-ID": "tenant-b" }),
      }),
    ),
  );
});
it.each([false, true])(
  "unmounted projection success/failure cannot publish (failure=%s)",
  async (failure) => {
    const task = deferred();
    workspace = () => task.promise;
    const view = render(page());
    await waitFor(() => expect(calls("workspace/")).toHaveLength(1));
    view.unmount();
    await act(async () => {
      if (failure) task.reject(new Error("gone"));
      else task.resolve(operation());
    });
    expect(view.container).toBeEmptyDOMElement();
  },
);
it.each([
  "Margen solicitado (%)",
  "Descuento (%)",
  "Modo de precio",
  "Segmento",
  "Moneda",
  "Fecha de costos",
  "Tipo de cambio registrado",
])("material control %s voids owner attestation", async (label) => {
  render(page());
  await screen.findByRole("heading", { name: "Actual y propuesto" });
  const confirmation = screen.getByLabelText("Confirmo las condiciones comerciales");
  fireEvent.click(confirmation);
  expect(confirmation).toBeChecked();
  if (["Moneda", "Fecha de costos", "Tipo de cambio registrado"].includes(label))
    fireEvent.click(screen.getByText("Moneda y autoridades"));
  const values: Record<string, string> = {
    "Margen solicitado (%)": "20",
    "Descuento (%)": "5",
    "Modo de precio": "COMMERCIAL_LIST_WITH_DISCOUNTS",
    Segmento: "ARCHITECT",
    Moneda: "USD",
    "Fecha de costos": "2026-10-09",
    "Tipo de cambio registrado": "fx-a",
  };
  if (
    label === "Fecha de costos" &&
    (screen.getByLabelText(label) as HTMLInputElement).value === values[label]
  )
    values[label] = "2026-10-10";
  fireEvent.change(screen.getByLabelText(label), { target: { value: values[label] } });
  expect(confirmation).not.toBeChecked();
});
it("editing only the reason keeps owner attestation", async () => {
  render(page());
  await screen.findByRole("heading", { name: "Actual y propuesto" });
  const checkbox = screen.getByLabelText("Confirmo las condiciones comerciales");
  fireEvent.click(checkbox);
  fireEvent.change(screen.getByLabelText("Motivo"), {
    target: { value: "Acuerdo comercial documentado" },
  });
  expect(checkbox).toBeChecked();
});
it("previews live margin without history writes and submits a pending request explicitly", async () => {
  identity.role = "ESTIMATOR";
  workspace = async (body) => {
    const value = operation({ costs_visible: false });
    if (body.target_margin === "0.2000")
      value.workspace.policy = {
        requires_approval: true,
        cause_text: ["El margen queda bajo el mínimo de la organización."],
      };
    return value;
  };
  render(page());
  await screen.findByRole("heading", { name: "Actual y propuesto" });
  fireEvent.change(screen.getByLabelText("Margen solicitado (%)"), { target: { value: "20" } });
  const submit = await screen.findByRole("button", { name: "Solicitar aprobación" });
  await waitFor(() => expect(submit).toBeEnabled());
  expect(calls("preview/")).toHaveLength(0);
  fireEvent.click(submit);
  await screen.findByText(/Solicitud enviada al dueño/);
  expect(calls("preview/")).toHaveLength(1);
  expect(calls("apply/")).toHaveLength(0);
  fireEvent.click(screen.getByRole("button", { name: "Retirar solicitud" }));
  await screen.findByText("Solicitud retirada.");
  expect(calls("withdraw/")).toHaveLength(1);
});
it.each([false, true])(
  "owner decides pending request with a required comment (reject=%s)",
  async (reject) => {
    history = [operation({ id: "operation-a", state: "PENDING" })];
    render(page(false));
    fireEvent.click(await screen.findByRole("button", { name: "Revisar solicitud" }));
    const action = screen.getByRole("button", { name: reject ? "Rechazar" : "Aprobar y aplicar" });
    expect(action).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Comentario de la decisión"), {
      target: { value: "Decisión justificada" },
    });
    fireEvent.click(action);
    await waitFor(() => expect(calls("apply/")).toHaveLength(1));
    expect(JSON.parse(String(calls("apply/")[0]?.[1].body))).toMatchObject({
      reason: "Decisión justificada",
      reject,
    });
  },
);
it("requester can read and acknowledge a decision that resulted in issue", async () => {
  identity.role = "ESTIMATOR";
  history = [
    operation({
      id: "operation-a",
      state: "APPLIED",
      resulted_in_issue: true,
      notification_unread: true,
    }),
  ];
  render(page(false));
  await screen.findByText("Resultó en emisión");
  expect(screen.getByText("Decisión nueva")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Ver detalle" }));
  fireEvent.click(screen.getByRole("button", { name: "Marcar decisión como leída" }));
  await screen.findByText("Decisión marcada como leída.");
  expect(calls("acknowledge/")).toHaveLength(1);
});
