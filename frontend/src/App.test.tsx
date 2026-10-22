import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";

import { AppRoutes, DEV_ONLY_ROUTE_PATHS, visibleDevOnlyRoutePaths } from "./App";
import { AuthSessionContext, type AuthSessionContextValue } from "./auth/AuthSessionProvider";
import { ConfirmProvider } from "./ui";
// Compile the real lazy destination during test setup. The route assertion
// verifies navigation/rendering, independently of concurrent Vite transforms.
import "./features/projects/ProjectPages";
vi.mock("./api/generated/dekopen", () => ({
  projectsList: vi.fn().mockResolvedValue({ status: 200, data: { items: [] } }),
  analyticsToday: vi.fn().mockResolvedValue({
    status: 200,
    data: { today: "2026-10-09", actions: [], pipeline: [], source: "Compromisos" },
  }),
}));

function authValue(status: AuthSessionContextValue["status"]): AuthSessionContextValue {
  return {
    status,
    session:
      status === "anonymous"
        ? null
        : ({ user: { id: "route-test-user" } } as AuthSessionContextValue["session"]),
    me:
      status === "ready"
        ? {
            user: { id: "10000000-0000-0000-0000-000000000001", email: "" },
            aal: "aal1",
            active_organization: {
              id: "20000000-0000-0000-0000-000000000001",
              name: "Taller A",
              role: "ESTIMATOR",
            },
            memberships: [],
          }
        : null,
    memberships:
      status === "organization_required"
        ? [
            {
              organization_id: "20000000-0000-0000-0000-000000000001",
              organization_name: "Taller A",
              role: "ESTIMATOR",
            },
          ]
        : [],
    error: null,
    requestMagicLink: vi.fn().mockResolvedValue(undefined),
    selectOrganization: vi.fn().mockResolvedValue(undefined),
    refreshContext: vi.fn().mockResolvedValue(undefined),
    signOut: vi.fn().mockResolvedValue(undefined),
  };
}

function renderRoute(path: string, auth: AuthSessionContextValue) {
  return render(
    <AuthSessionContext.Provider value={auth}>
      <QueryClientProvider
        client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
      >
        <ConfirmProvider>
          <MemoryRouter initialEntries={[path]}>
            <AppRoutes />
          </MemoryRouter>
        </ConfirmProvider>
      </QueryClientProvider>
    </AuthSessionContext.Provider>,
  );
}

describe("SHOT-04 application routes", () => {
  it("shows anonymous visitors the public landing with an entry to login", async () => {
    renderRoute("/", authValue("anonymous"));
    expect(await screen.findByRole("heading", { name: /ventana que diseñas/ })).toBeInTheDocument();
    for (const link of screen.getAllByRole("link", { name: "Entrar" })) {
      expect(link).toHaveAttribute("href", "/login");
    }
  });

  it("opens the real project list from the authenticated shell", async () => {
    renderRoute("/dashboard", authValue("ready"));
    expect(await screen.findByTestId("app-shell")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Obras" })).toHaveAttribute("href", "/projects");
    fireEvent.click(screen.getByRole("link", { name: "Obras" }));
    expect(await screen.findByRole("heading", { name: "Obras", level: 1 })).toBeInTheDocument();
  });

  it("lets an operator explicitly open their role-scoped Today queue", async () => {
    const auth = authValue("ready");
    auth.me!.active_organization!.role = "OPERATOR";
    renderRoute("/dashboard", auth);
    expect(await screen.findByRole("heading", { name: "Pendientes" })).toBeVisible();
    expect(screen.queryByRole("link", { name: "Precios" })).not.toBeInTheDocument();
  });

  it("routes an OWNER requiring aal2 to the MFA flow", async () => {
    renderRoute("/dashboard", authValue("mfa_required"));
    expect(await screen.findByTestId("mfa-page")).toBeInTheDocument();
  });

  it("routes multi-membership sessions to explicit organization selection", async () => {
    const auth = authValue("organization_required");
    renderRoute("/dashboard", auth);
    const selector = await screen.findByTestId("organization-selector");
    fireEvent.click(screen.getByRole("button", { name: /Taller A/ }));
    await waitFor(() => expect(auth.selectOrganization).toHaveBeenCalledOnce());
    expect(selector).toBeInTheDocument();
  });

  it("keeps a single light theme without a theme switch (constitution 2026-10)", async () => {
    window.localStorage.setItem("dekopen.theme", "dark");
    renderRoute("/dashboard", authValue("ready"));
    expect(await screen.findByTestId("app-shell")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Cambiar tema" })).not.toBeInTheDocument();
    expect(document.documentElement.dataset.theme).not.toBe("dark");
  });

  it("keeps dev-only routes out of production routing", () => {
    expect(DEV_ONLY_ROUTE_PATHS).toContain("/projects/demo/positions/g1/edit");
    expect(visibleDevOnlyRoutePaths({ DEV: false })).toEqual([]);
    expect(visibleDevOnlyRoutePaths({ DEV: true })).toEqual(DEV_ONLY_ROUTE_PATHS);
  });
});
