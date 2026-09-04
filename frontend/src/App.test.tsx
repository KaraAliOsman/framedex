import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { AppRoutes } from "./App";
import { AuthSessionContext, type AuthSessionContextValue } from "./auth/AuthSessionProvider";
import { ThemeProvider } from "./theme/ThemeProvider";

function authValue(status: AuthSessionContextValue["status"]): AuthSessionContextValue {
  return {
    status,
    session: status === "anonymous" ? null : ({} as AuthSessionContextValue["session"]),
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
      <ThemeProvider>
        <MemoryRouter initialEntries={[path]}>
          <AppRoutes />
        </MemoryRouter>
      </ThemeProvider>
    </AuthSessionContext.Provider>,
  );
}

describe("SHOT-04 application routes", () => {
  it("redirects an anonymous root session to login", async () => {
    renderRoute("/", authValue("anonymous"));
    expect(await screen.findByTestId("login-page")).toBeInTheDocument();
  });

  it("renders the navigable authenticated shell and placeholder routes", async () => {
    renderRoute("/dashboard", authValue("ready"));
    expect(screen.getByTestId("app-shell")).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("Proyectos"));
    expect(await screen.findByRole("heading", { name: "Proyectos" })).toBeInTheDocument();
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

  it("switches and persists the dual theme", () => {
    window.localStorage.setItem("dekopen.theme", "light");
    renderRoute("/dashboard", authValue("ready"));
    fireEvent.click(screen.getByRole("button", { name: "Cambiar tema" }));
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(window.localStorage.getItem("dekopen.theme")).toBe("dark");
  });
});
