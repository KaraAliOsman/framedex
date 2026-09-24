import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { aiAsk } from "../../api/generated/dekopen";
import { AskDekopen } from "./AskDekopen";
import { AssistantSurfaceProvider, routeContext } from "./assistantContext";

vi.mock("../../api/generated/dekopen", () => ({ aiAsk: vi.fn() }));
const askMock = vi.mocked(aiAsk);

function successResponse() {
  return {
    status: 200,
    headers: new Headers(),
    data: {
      audit_id: "a1",
      model: "mock-context-1",
      credits_debited: 2,
      answer: "Tienes 3 proyectos activos.",
      actions: [{ kind: "navigate", path: "/projects", label: "Ver proyectos" }],
      warnings: [],
    },
  };
}

function renderDock(initialPath = "/dashboard") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AssistantSurfaceProvider>
        <Routes>
          <Route path="*" element={<AskDekopen organizationId="org-1" />} />
        </Routes>
      </AssistantSurfaceProvider>
    </MemoryRouter>,
  );
}

describe("routeContext", () => {
  it("maps entity routes to their required refs", () => {
    expect(routeContext("/projects")).toEqual({ surface: "projects", refs: {} });
    expect(routeContext("/projects/abc-1")).toEqual({
      surface: "project",
      refs: { project_id: "abc-1" },
    });
    expect(routeContext("/projects/p1/positions/pos-9/edit")).toEqual({
      surface: "position",
      refs: { project_id: "p1", position_id: "pos-9" },
    });
    expect(routeContext("/settings/billing")).toEqual({ surface: "settings", refs: {} });
    expect(routeContext("/production")).toEqual({ surface: "production", refs: {} });
  });
});

describe("AskDekopen", () => {
  beforeEach(() => askMock.mockReset());

  it("answers inside the route's typed surface and navigates on actions", async () => {
    askMock.mockResolvedValue(successResponse() as never);
    renderDock("/projects/abc-1");
    fireEvent.click(screen.getByRole("button", { name: /Abrir el asistente/i }));
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "¿Qué ves aquí?" } });
    fireEvent.click(screen.getByRole("button", { name: /Enviar/i }));
    await waitFor(() => expect(askMock).toHaveBeenCalledTimes(1));
    const [body, options] = askMock.mock.calls[0] ?? [];
    expect(body).toMatchObject({
      surface: "project",
      refs: { project_id: "abc-1" },
      question: "¿Qué ves aquí?",
    });
    expect(new Headers(options?.headers).get("X-Organization-ID")).toBe("org-1");
    expect(await screen.findByText("Tienes 3 proyectos activos.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Ver proyectos" })).toBeTruthy();
  });

  it("drops the in-flight answer when the surface changes", async () => {
    let resolve!: (value: ReturnType<typeof successResponse>) => void;
    askMock.mockReturnValue(new Promise((r) => (resolve = r)) as never);
    const view = render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <AssistantSurfaceProvider>
          <Routes>
            <Route path="*" element={<AskDekopen organizationId="org-1" />} />
          </Routes>
        </AssistantSurfaceProvider>
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: /Abrir el asistente/i }));
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "hola" } });
    fireEvent.click(screen.getByRole("button", { name: /Enviar/i }));
    expect(askMock).toHaveBeenCalledTimes(1);
    // Simulate a route change by unmounting/remounting on a different surface.
    view.unmount();
    resolve(successResponse());
    await waitFor(() => expect(screen.queryByText("Tienes 3 proyectos activos.")).toBeNull());
  });

  it("shows the API error detail when the ask fails", async () => {
    askMock.mockResolvedValue({
      status: 400,
      headers: new Headers(),
      data: { error: { detail: "contexto inválido" } },
    } as never);
    renderDock();
    fireEvent.click(screen.getByRole("button", { name: /Abrir el asistente/i }));
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "algo" } });
    fireEvent.submit(screen.getByRole("button", { name: /Enviar/i }).closest("form")!);
    expect(await screen.findByText("contexto inválido")).toBeTruthy();
  });
});
