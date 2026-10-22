import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import { COPILOT_DELEGATE_EVENT } from "./copilotBridge";
import { CopilotWindow, clampGeometry } from "./CopilotWindow";

vi.mock("../../api/generated/dekopen", () => ({
  aiAgent: vi.fn(),
  aiJobApprove: vi.fn(),
  aiJobCancel: vi.fn(),
  aiJobMessageCreate: vi.fn(),
  aiJobOutcomeCreate: vi.fn(),
  aiJobRetrieve: vi.fn(),
  aiJobRetry: vi.fn(),
  aiThreadTimeline: vi.fn(async () => ({ status: 200, data: { items: [], next_cursor: null } })),
  aiThreadsList: vi.fn(async () => ({ status: 200, data: { items: [], next_cursor: null } })),
  aiThreadsCreate: vi.fn(),
  aiThreadUpdate: vi.fn(),
  aiAttachmentsUpload: vi.fn(),
  aiAttachmentGet: vi.fn(),
}));

function mount(openRequested = 1) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <button type="button">Invocador</button>
        <CopilotWindow organizationId="org-1" userId="user-1" openRequested={openRequested} />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  window.sessionStorage.clear();
  window.localStorage.clear();
  Object.defineProperty(window, "innerWidth", { configurable: true, value: 1440 });
  Object.defineProperty(window, "innerHeight", { configurable: true, value: 900 });
});
afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
});

it("docks as a full-height side panel by default, without drag or resize", () => {
  mount();
  const dialog = screen.getByRole("dialog", { name: "Asistente" });
  expect(dialog).toHaveClass("is-docked");
  expect(dialog.style.width).toBe("");
  expect(
    screen.queryByRole("button", { name: "Mover o cambiar tamaño con el teclado" }),
  ).not.toBeInTheDocument();
});

it("opens as a non-modal dialog that leaves the page interactive", () => {
  vi.stubEnv("VITE_AGENTE_PANEL_LATERAL", "false");
  mount();
  const dialog = screen.getByRole("dialog", { name: "Asistente" });
  expect(dialog).toHaveAttribute("aria-modal", "false");
  // No scrim and no focus trap: the manual page stays reachable.
  expect(screen.getByRole("button", { name: "Invocador" })).toBeEnabled();
  expect(dialog.style.width).toBe("420px");
  expect(dialog.style.height).toBe("600px");
});

it("starts closed without an explicit request", () => {
  mount(0);
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});

it("shows the three policies only in Trabajo and keeps the choice", () => {
  mount();
  expect(
    screen.queryByRole("radiogroup", { name: "Autonomía del trabajo" }),
  ).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("radio", { name: "Encargar" }));
  const policies = screen.getByRole("radiogroup", { name: "Autonomía del trabajo" });
  expect(policies).toBeInTheDocument();
  expect(screen.getByRole("radio", { name: "Con aprobación" })).toHaveAttribute(
    "aria-checked",
    "true",
  );
  fireEvent.click(screen.getByRole("radio", { name: "Omitir todo" }));
  expect(screen.getByRole("radio", { name: "Omitir todo" })).toHaveAttribute(
    "aria-checked",
    "true",
  );
  expect(window.localStorage.getItem("dekopen.copilot.v1.autonomy.user-1.org-1")).toBe("draft");
});

it("minimizes and restores without losing the draft", () => {
  mount();
  const composer = screen.getByRole("textbox", { name: /Qué necesitas/ });
  fireEvent.change(composer, { target: { value: "Agrega una corredera" } });
  fireEvent.click(screen.getByRole("button", { name: "Minimizar el asistente" }));
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Restaurar el asistente" }));
  expect(screen.getByRole("textbox", { name: /Qué necesitas/ })).toHaveValue(
    "Agrega una corredera",
  );
});

it("adjusts position from the keyboard and saves with Enter", () => {
  vi.stubEnv("VITE_AGENTE_PANEL_LATERAL", "false");
  mount();
  const dialog = screen.getByRole("dialog");
  fireEvent.click(screen.getByRole("button", { name: "Mover o cambiar tamaño con el teclado" }));
  const before = Number.parseFloat(dialog.style.left);
  fireEvent.keyDown(dialog, { key: "ArrowLeft" });
  fireEvent.keyDown(dialog, { key: "ArrowDown", shiftKey: true });
  fireEvent.keyDown(dialog, { key: "Enter" });
  expect(Number.parseFloat(dialog.style.left)).toBe(before - 16);
  const saved = JSON.parse(
    window.localStorage.getItem("dekopen.pref.v1.copilot-geometry.user-1.org-1")!,
  );
  expect(saved.height).toBe(616);
});

it("closes with Escape and keeps the conversation for the session", () => {
  mount();
  fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" });
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  const session = JSON.parse(
    window.sessionStorage.getItem("dekopen.copilot.v1.session.user-1.org-1")!,
  );
  expect(session.open).toBe(false);
});

it("opens from a manual delegation with the request prefilled, never sent", async () => {
  const { aiAgent } = await import("../../api/generated/dekopen");
  mount(0);
  act(() => {
    window.dispatchEvent(
      new CustomEvent(COPILOT_DELEGATE_EVENT, {
        detail: {
          mode: "work",
          text: "Divide esta ventana en dos hojas",
          refs: { position_id: "p-1" },
        },
      }),
    );
  });
  await waitFor(() =>
    expect(screen.getByRole("textbox", { name: /Qué necesitas/ })).toHaveValue(
      "Divide esta ventana en dos hojas",
    ),
  );
  expect(screen.getByRole("radio", { name: "Encargar" })).toHaveAttribute("aria-checked", "true");
  expect(aiAgent).not.toHaveBeenCalled();
});

it("keeps the window inside the viewport", () => {
  expect(
    clampGeometry({ x: -50, y: 2000, width: 5000, height: 100 }, { width: 1024, height: 700 }),
  ).toEqual({
    x: 16,
    y: 264,
    width: 992,
    height: 420,
  });
});
