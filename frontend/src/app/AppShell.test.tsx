import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import * as client from "../api/generated/dekopen";
import { AppShell } from "./AppShell";

vi.mock("../auth/AuthSessionProvider", () => ({
  useAuthSession: () => ({
    status: "ready",
    session: { user: { id: "user-1" } },
    me: {
      user: { id: "user-1", email: "owner@example.test" },
      active_organization: { id: "org-1", name: "Taller", role: "OWNER" },
      memberships: [{ organization_id: "org-1", organization_name: "Taller", role: "OWNER" }],
    },
    memberships: [],
    signOut: vi.fn(),
    selectOrganization: vi.fn(),
  }),
}));
vi.mock("../api/generated/dekopen");

function capabilities(granted: boolean) {
  return {
    status: 200,
    headers: new Headers(),
    data: {
      ai_entitlement: { granted, origin: granted ? "plan" : "none" },
      capabilities: [],
      plans: [],
      extras: [],
      role: "OWNER",
    },
  } as never;
}

function mount() {
  const queries = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queries}>
      <MemoryRouter initialEntries={["/projects"]}>
        <AppShell>
          <p>Trabajo manual</p>
        </AppShell>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.resetAllMocks();
  for (const value of Object.values(client)) {
    if (typeof value === "function" && "mockResolvedValue" in value)
      (value as unknown as { mockResolvedValue: (v: unknown) => void }).mockResolvedValue({
        status: 200,
        headers: new Headers(),
        data: {},
      });
  }
});
afterEach(cleanup);

it("mounts no assistant, character or AI polling in the manual plan", async () => {
  vi.mocked(client.capabilitiesRetrieve).mockResolvedValue(capabilities(false));
  mount();
  await waitFor(() => expect(client.capabilitiesRetrieve).toHaveBeenCalled());
  expect(screen.getByText("Trabajo manual")).toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /Asistente/ })).not.toBeInTheDocument();
  expect(screen.queryByRole("dialog", { name: "Asistente" })).not.toBeInTheDocument();
  expect(client.aiPresenceGet).not.toHaveBeenCalled();
  expect(client.aiThreadTimeline).not.toHaveBeenCalled();
  expect(client.aiAgent).not.toHaveBeenCalled();
});

it("offers the assistant only once the server confirms the AI core", async () => {
  vi.mocked(client.capabilitiesRetrieve).mockResolvedValue(capabilities(true));
  mount();
  expect(await screen.findByRole("button", { name: /Asistente/ })).toBeInTheDocument();
  // Showing the entry point opens nothing and calls no model.
  expect(screen.queryByRole("dialog", { name: "Asistente" })).not.toBeInTheDocument();
  expect(client.aiAgent).not.toHaveBeenCalled();
});
