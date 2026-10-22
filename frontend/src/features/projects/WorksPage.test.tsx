import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { engineSystems, projectsWorks } from "../../api/generated/dekopen";
import type { WorkIndexItem, WorksResponse } from "../../api/generated/models";
import { LegacyQuotesRedirect } from "../quotations/LegacyQuotesRedirect";
import { WorksPage } from "./WorksPage";

const auth = vi.hoisted(() => ({ role: "OWNER", orgId: "org-a", userId: "user-a" }));
vi.mock("../../auth/AuthSessionProvider", () => ({
  useAuthSession: () => ({
    session: { user: { id: auth.userId } },
    me: { active_organization: { id: auth.orgId, name: "Taller de prueba", role: auth.role } },
  }),
}));
vi.mock("../../api/generated/dekopen", async (original) => ({
  ...(await original<typeof import("../../api/generated/dekopen")>()),
  engineSystems: vi.fn(),
  projectsWorks: vi.fn(),
}));
function response<T>(data: T) {
  return { status: 200 as const, data, headers: new Headers() };
}
const item: WorkIndexItem = {
  id: "work-a",
  code: "P-000001",
  name: "Casa Pérez",
  client_name: "Cliente de prueba",
  status: "QUOTED",
  current_revision: "REV-A",
  updated_at: "2026-10-22T12:00:00Z",
  total_price_net: "0.00",
  total_price_tax: "0.00",
  total_price_gross: "0.00",
  currency: "CLP",
  pricing_current: false,
  current_pricing_operation_id: null,
  position_count: 1,
  progress: {
    stage: "QUOTING",
    reason: "Todavía sin envío",
    quoted_total: "1190.00",
    currency: "CLP",
  },
  quotation: null,
};
function index(overrides: Partial<WorksResponse> = {}): WorksResponse {
  return {
    items: [item],
    total: 1,
    matching: 1,
    counts: { QUOTING: 1 },
    offset: 0,
    limit: 50,
    ...overrides,
  };
}
const clients: QueryClient[] = [];
function mount(
  path = "/projects",
  client = new QueryClient({ defaultOptions: { queries: { retry: false } } }),
) {
  clients.push(client);
  const router = createMemoryRouter(
    [
      { path: "/projects", element: <WorksPage /> },
      { path: "/quotes", element: <LegacyQuotesRedirect /> },
      { path: "/projects/:id", element: <p>Detalle de obra</p> },
    ],
    { initialEntries: [path] },
  );
  const view = render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return { router, client, ...view };
}
beforeEach(() => {
  vi.clearAllMocks();
  Object.assign(auth, { role: "OWNER", orgId: "org-a", userId: "user-a" });
  vi.mocked(engineSystems).mockResolvedValue(response({ systems: [] }));
  vi.mocked(projectsWorks).mockResolvedValue(response(index()));
});
afterEach(() => {
  cleanup();
  for (const client of clients.splice(0)) client.clear();
});

it("redirects legacy quotes with every filter, exact offset and hash", async () => {
  const { router } = mount(
    "/quotes?q=REV-A&attention=viewed&phase=QUOTED&currency=UF&offset=51#lista",
  );
  await screen.findByRole("link", { name: /Casa Pérez/ });
  expect(router.state.location.pathname).toBe("/projects");
  expect(router.state.location.hash).toBe("#lista");
  expect(Object.fromEntries(new URLSearchParams(router.state.location.search))).toEqual({
    q: "REV-A",
    attention: "viewed",
    phase: "QUOTED",
    currency: "UF",
    offset: "51",
    view: "quotes",
  });
  expect(projectsWorks).toHaveBeenLastCalledWith(
    expect.objectContaining({ q: "REV-A", view: "quotes", offset: 51, limit: 50 }),
    expect.objectContaining({
      signal: expect.any(AbortSignal),
      headers: { "X-Organization-ID": "org-a" },
    }),
  );
});

it("uses server counts and arbitrary offsets instead of filtering one page", async () => {
  vi.mocked(projectsWorks).mockResolvedValue(
    response(index({ total: 501, matching: 800, counts: { QUOTING: 501, SENT: 299 }, offset: 51 })),
  );
  const { router } = mount("/projects?stage=QUOTING&offset=51");
  await screen.findByRole("button", { name: "Todas · 800" });
  expect(screen.getByRole("button", { name: "Enviada · 299" })).toBeInTheDocument();
  expect(screen.getByText("52–101 de 501 obras")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Siguiente" }));
  await waitFor(() =>
    expect(new URLSearchParams(router.state.location.search).get("offset")).toBe("101"),
  );
  fireEvent.click(await screen.findByRole("button", { name: "Enviada · 299" }));
  await waitFor(() =>
    expect(new URLSearchParams(router.state.location.search).has("offset")).toBe(false),
  );
});

it("keeps the search focused, hides old rows and aborts superseded requests", async () => {
  mount();
  await screen.findByRole("link", { name: /Casa Pérez/ });
  vi.mocked(projectsWorks).mockImplementationOnce(() => new Promise(() => undefined));
  const input = screen.getByRole("searchbox", { name: "Buscar obra o cliente" });
  input.focus();
  fireEvent.change(input, { target: { value: "terra" } });
  await screen.findByRole("status", { name: "Actualizando obras" });
  expect(input).toHaveFocus();
  expect(input).toHaveValue("terra");
  expect(screen.queryByRole("link", { name: /Casa Pérez/ })).not.toBeInTheDocument();
  const oldSignal = vi.mocked(projectsWorks).mock.calls.at(-1)![1]!.signal!;
  fireEvent.change(input, { target: { value: "terraza" } });
  await waitFor(() => expect(oldSignal.aborted).toBe(true));
  await screen.findByRole("link", { name: /Casa Pérez/ });
  expect(input).toHaveFocus();
});

it("returns from commercial filters to all works without retaining hidden filters", async () => {
  const { router } = mount(
    "/projects?view=quotes&attention=unshared&phase=QUOTED&currency=CLP&sort=updated&offset=50",
  );
  await screen.findByLabelText("Mostrar");
  fireEvent.change(screen.getByLabelText("Mostrar"), { target: { value: "" } });
  await waitFor(() => expect(router.state.location.search).toBe(""));
  expect(screen.queryByLabelText("Seguimiento")).not.toBeInTheDocument();
});

it("shows commercial evidence and links directly to its quotation", async () => {
  vi.mocked(projectsWorks).mockResolvedValue(
    response(
      index({
        items: [
          {
            ...item,
            quotation: {
              project_id: item.id,
              project_code: item.code,
              project_name: item.name,
              client_name: item.client_name,
              revision_code: "REV-A",
              state: "response",
              phase: "QUOTED",
              valid_until: "2026-10-30",
              view_count: 2,
              last_viewed_at: "2026-10-22T12:00:00Z",
              response_note: "Revisar entrega",
              total: "1190.00",
              currency: "CLP",
              source: "Revisión emitida vigente",
              href: "/projects/work-a?section=quote",
            },
          },
        ],
      }),
    ),
  );
  mount("/projects?view=quotes");
  expect(await screen.findByRole("link", { name: /Revisar entrega/ })).toHaveAttribute(
    "href",
    "/projects/work-a?section=quote",
  );
  expect(screen.getByText("Respuesta por revisar")).toBeInTheDocument();
  expect(screen.getByText("2 vistas", { exact: false })).toBeInTheDocument();
  expect(screen.getByText("Vigencia")).toBeInTheDocument();
});

it("does not reuse the previous organization's works while the new query loads", async () => {
  const first = mount();
  await screen.findByRole("link", { name: /Casa Pérez/ });
  first.unmount();
  auth.orgId = "org-b";
  vi.mocked(projectsWorks).mockImplementationOnce(() => new Promise(() => undefined));
  mount("/projects", first.client);
  expect(screen.queryByText("Casa Pérez")).not.toBeInTheDocument();
  await screen.findByRole("status", { name: "Cargando obras" });
});

it.each(["OPERATOR", "INSTALLER"])("keeps %s outside Works", async (role) => {
  auth.role = role;
  mount();
  await screen.findByRole("alert");
  expect(projectsWorks).not.toHaveBeenCalled();
});
it("keeps workshop access without commercial controls or creation", async () => {
  auth.role = "WORKSHOP_MANAGER";
  mount();
  await screen.findByRole("link", { name: /Casa Pérez/ });
  expect(screen.queryByLabelText("Mostrar")).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Nueva cotización" })).not.toBeInTheDocument();
});
