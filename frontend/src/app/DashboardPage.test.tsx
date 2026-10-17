import { fireEvent, render, screen, within, cleanup } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { analyticsToday } from "../api/generated/dekopen";
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
vi.mock("../api/generated/dekopen", () => ({ analyticsToday: vi.fn() }));
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
function show(actions = Array.from({ length: 51 }, (_, index) => item(index + 1))) {
  vi.mocked(analyticsToday).mockResolvedValue({
    status: 200,
    data: {
      today: "2026-10-09",
      actions,
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
beforeEach(() => vi.clearAllMocks());
afterEach(cleanup);
it("keeps exact entity and phase/currency links, and preserves ordered actions across pages", async () => {
  show();
  const queue = await screen.findByRole("list", { name: "Acciones pendientes" });
  expect(within(queue).getAllByRole("listitem")).toHaveLength(50);
  expect(within(queue).getAllByRole("link", { name: "Abrir entrega" })[0]).toHaveAttribute(
    "href",
    "/production?order=order-1",
  );
  expect(screen.getByRole("link", { name: /En producción/ })).toHaveAttribute(
    "href",
    "/quotes?phase=IN_PRODUCTION&currency=USD",
  );
  fireEvent.click(screen.getByRole("button", { name: "Siguiente" }));
  expect(within(queue).getByRole("heading", { name: "Completa la entrega 51" })).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Anterior" }));
  expect(within(queue).getByRole("heading", { name: "Completa la entrega 1" })).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Atención pendiente" }));
  expect(await screen.findByRole("link", { name: "Ver todo mi trabajo" })).toHaveAttribute(
    "href",
    "/dashboard",
  );
  expect(vi.mocked(analyticsToday).mock.calls.length).toBeLessThanOrEqual(2);
});
it("uses one quiet empty state without zero KPI tiles", async () => {
  show([]);
  expect(await screen.findByRole("heading", { name: "Todo al día" })).toBeVisible();
  expect(screen.queryByRole("list", { name: "Acciones pendientes" })).not.toBeInTheDocument();
});
