import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import { companyUsers, organizationPlan } from "../../api/generated/dekopen";
import { ConfirmProvider } from "../../ui";
import { UsersCard } from "./AdminSections";

vi.mock("../../api/generated/dekopen", async (original) => ({
  ...(await original<object>()),
  companyUsers: vi.fn(),
  organizationPlan: vi.fn(),
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const owner = {
  id: "m1",
  email: "dueno@taller.test",
  role: "OWNER",
  is_active: true,
  updated_at: "2026-10-31T00:00:00Z",
};

function show(plan: Record<string, unknown>, items: unknown[] = [owner]) {
  vi.mocked(companyUsers).mockResolvedValue({
    status: 200,
    data: { items, invitations: [] },
  } as never);
  vi.mocked(organizationPlan).mockResolvedValue({
    status: 200,
    data: {
      pending_invitations: 0,
      ai: false,
      solo: items.length === 1,
      active_members: items.length,
      ...plan,
    },
  } as never);
  render(
    <MemoryRouter>
      <QueryClientProvider
        client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
      >
        <ConfirmProvider>
          <UsersCard orgId="organization" canEdit />
        </ConfirmProvider>
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

test("a Taller is one person: no roles, no invitation, a way to grow", async () => {
  show({ code: "STARTER", seats: 1, seats_left: 0, roles: ["OWNER"], features: [] });
  expect(await screen.findByRole("heading", { name: "Equipo" })).toBeVisible();
  expect(screen.getByText(/Trabajas solo y ves todo/)).toBeVisible();
  expect(screen.getByText("Plan Taller · 1 de 1 persona")).toBeVisible();
  expect(screen.queryByRole("button", { name: "Invitar y enviar correo" })).toBeNull();
  expect(screen.queryByText("Rol de ingreso")).toBeNull();
  expect(screen.getByRole("link", { name: "Ver planes" })).toHaveAttribute(
    "href",
    "/settings/billing",
  );
});

test("Pro invites by what the person will do, never by role", async () => {
  show({
    code: "PRO",
    seats: 3,
    seats_left: 2,
    roles: ["OWNER", "ESTIMATOR", "WORKSHOP_MANAGER"],
    features: ["client_3d", "purchasing", "cnc"],
  });
  expect(await screen.findByRole("group", { name: "¿Qué hará?" })).toBeVisible();
  expect(screen.getByRole("radio", { name: "Oficina: cotiza, vende y cobra." })).toBeChecked();
  expect(screen.getByRole("radio", { name: "Taller: produce, compra y despacha." })).toBeVisible();
  expect(screen.queryByRole("radio", { name: /Operario/ })).toBeNull();
  expect(screen.queryByText("Rol de ingreso")).toBeNull();
});

test("a full plan says how to make room instead of offering an invitation", async () => {
  show(
    {
      code: "PRO",
      seats: 3,
      seats_left: 0,
      roles: ["OWNER", "ESTIMATOR", "WORKSHOP_MANAGER"],
      features: ["client_3d", "purchasing", "cnc"],
    },
    [
      owner,
      { ...owner, id: "m2", email: "a@t.test", role: "ESTIMATOR" },
      { ...owner, id: "m3", email: "b@t.test", role: "WORKSHOP_MANAGER" },
    ],
  );
  expect(await screen.findByText(/Tu plan ya ocupa sus 3 personas/)).toBeVisible();
  expect(screen.queryByRole("button", { name: "Invitar y enviar correo" })).toBeNull();
  expect(screen.getAllByRole("combobox", { name: "Hace" })[1]).toHaveDisplayValue("Oficina");
});

test("Empresa keeps every role", async () => {
  show({
    code: "BUSINESS",
    seats: null,
    seats_left: null,
    roles: ["OWNER", "ESTIMATOR", "WORKSHOP_MANAGER", "OPERATOR", "INSTALLER"],
    features: ["client_3d", "purchasing", "cnc", "roles", "subagents", "stations", "field"],
  });
  expect(await screen.findByRole("heading", { name: "Usuarios y roles" })).toBeVisible();
  expect(screen.getByRole("combobox", { name: "Rol de ingreso" })).toHaveTextContent("Operario");
  expect(screen.getByText("Plan Empresa · 1 persona · sin límite")).toBeVisible();
});

test("a team that moved down to Taller keeps its people and gets no new seat", async () => {
  show({ code: "STARTER", seats: 1, seats_left: 0, roles: ["OWNER"], features: [] }, [
    owner,
    { ...owner, id: "m2", email: "a@t.test", role: "ESTIMATOR" },
  ]);
  expect(await screen.findByText(/Tu plan ya ocupa su única persona/)).toBeVisible();
  expect(screen.queryByText(/Trabajas solo/)).toBeNull();
  expect(screen.getAllByRole("combobox", { name: "Hace" })[1]).toHaveDisplayValue("Oficina");
});
