import { fireEvent, render, screen, within, cleanup } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { analyticsToday, catalogSystemList, projectsCreate } from "../api/generated/dekopen";
import type { PreparedQuotations } from "../api/generated/models";
import { DashboardPage } from "./DashboardPage";
import { AttentionBell } from "./AttentionBell";

vi.mock("../auth/AuthSessionProvider", () => ({
  useAuthSession: () => ({
    me: {
      user: { id: "estimator" },
      active_organization: { id: "org", name: "Obra DEMO", role: "OWNER" },
    },
  }),
}));
vi.mock("../api/generated/dekopen", () => ({
  analyticsToday: vi.fn(),
  catalogSystemList: vi.fn(),
  projectsCreate: vi.fn(),
}));
const item = (index: number) => ({
  key: `due:${index}`,
  kind: "delivery",
  entity_code: `OT-${index}`,
  entity_name: "Obra Prat",
  title: `Completa la entrega ${index}`,
  reason: "Entrega comprometida hoy",
  verb: "Abrir entrega",
  href: `/production?order=order-${index}`,
  due_on: "2026-10-09",
  blocking: false,
  consequence: "today",
  amount: null,
  currency: null,
  balance_total: null,
  balance_collected: null,
  source: "Agenda real",
  operation_id: null,
});
function show(
  actions = Array.from({ length: 51 }, (_, index) => item(index + 1)),
  prepared: PreparedQuotations = { count: 0, items: [] },
) {
  vi.mocked(analyticsToday).mockResolvedValue({
    status: 200,
    data: {
      today: "2026-10-09",
      actions,
      prepared,
      pipeline: [
        {
          phase: "IN_PRODUCTION",
          currency: "USD",
          amount: "120.005",
          count: 1,
          unknown_count: 0,
          href: "/quotes?phase=IN_PRODUCTION&currency=USD",
          source: "Totales emitidos",
        },
      ],
      source: "Motor",
    },
  } as never);
  return render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <MemoryRouter>
        <DashboardPage />
        <AttentionBell />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(catalogSystemList).mockResolvedValue({
    status: 200,
    data: { items: [{ id: "serie" }] },
  } as never);
});
afterEach(cleanup);
it("keeps exact entity and phase/currency links, and preserves ordered actions across pages", async () => {
  show();
  const queue = await screen.findByRole("list", { name: "Acciones pendientes" });
  expect(within(queue).getAllByRole("listitem")).toHaveLength(50);
  expect(within(queue).getAllByRole("link", { name: "Abrir entrega" })[0]).toHaveAttribute(
    "href",
    "/production?order=order-1",
  );
  fireEvent.click(screen.getByText("Venta por etapa", { selector: "summary" }));
  expect(screen.getByRole("link", { name: /En producción/ })).toHaveAttribute(
    "href",
    "/quotes?phase=IN_PRODUCTION&currency=USD",
  );
  fireEvent.click(screen.getByRole("button", { name: "Siguiente" }));
  expect(within(queue).getByRole("heading", { name: "Completa la entrega 51" })).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Anterior" }));
  expect(within(queue).getByRole("heading", { name: "Completa la entrega 1" })).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Atención pendiente" }));
  expect(await screen.findByRole("link", { name: "Ver todos los pendientes" })).toHaveAttribute(
    "href",
    "/dashboard",
  );
  expect(vi.mocked(analyticsToday).mock.calls.length).toBeLessThanOrEqual(2);
});
it("uses one quiet empty state without zero KPI tiles", async () => {
  show([]);
  expect(await screen.findByRole("heading", { name: "Todo al día" })).toBeVisible();
  expect(screen.queryByRole("list", { name: "Acciones pendientes" })).not.toBeInTheDocument();
  expect(screen.queryByRole("region", { name: "Resumen de hoy" })).not.toBeInTheDocument();
  expect(screen.queryByText(/DEKOPEN preparó/)).not.toBeInTheDocument();
});

it("sends a workshop without its own series to the first-use guide", async () => {
  vi.mocked(catalogSystemList).mockResolvedValue({ status: 200, data: { items: [] } } as never);
  show([]);
  expect(await screen.findByRole("heading", { name: "Prepara tu taller" })).toBeVisible();
  expect(screen.getByRole("link", { name: "Empezar" })).toHaveAttribute("href", "/onboarding");
  expect(catalogSystemList).toHaveBeenCalledWith(
    { summary: true, is_demo: false, owned_only: true },
    expect.objectContaining({ headers: { "X-Organization-ID": "org" } }),
  );
});

it("opens the prepared drafts without applying or sending anything", async () => {
  show([], {
    count: 1,
    items: [{ project_id: "draft", name: "Casa Pérez", code: "P-000001", href: "/projects/draft" }],
  });
  expect(await screen.findByRole("heading", { name: "DEKOPEN preparó 1 cosa" })).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Revisar" }));
  const dialog = screen.getByRole("dialog", { name: "Cotizaciones preparadas" });
  expect(within(dialog).getByRole("link", { name: /Casa Pérez/ })).toHaveAttribute(
    "href",
    "/projects/draft",
  );
  expect(vi.mocked(projectsCreate)).not.toHaveBeenCalled();
});

it("starts one draft from the explicit click and reports a denied creation", async () => {
  show([]);
  await screen.findByRole("heading", { name: "Todo al día" });
  vi.mocked(projectsCreate).mockResolvedValue({ status: 403, data: {} } as never);
  fireEvent.click(screen.getByRole("button", { name: "Nueva cotización" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Tu rol no puede crear cotizaciones");
  expect(projectsCreate).toHaveBeenCalledWith(
    { name: expect.stringMatching(/^Cotización del /), client_name: "" },
    { headers: { "X-Organization-ID": "org" } },
  );
});
