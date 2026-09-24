// frontend/src/features/commands/CommandPalette.test.tsx
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useMemo, useState } from "react";
import { afterEach, expect, it, vi } from "vitest";

import { t } from "../../i18n/es-CL";
import { CommandPalette } from "./CommandPalette";
import { useRegisterCommands } from "./registry";
import type { ResolvedCommand } from "./types";

const searchMock = vi.fn(
  async (): Promise<{
    status: number;
    data: { results: import("../../api/generated/models").SearchResult[] };
  }> => ({ status: 200, data: { results: [] } }),
);
vi.mock("../../api/generated/dekopen", async (importOriginal) => {
  const original = await importOriginal<typeof import("../../api/generated/dekopen")>();
  return { ...original, globalSearch: () => searchMock() };
});

afterEach(cleanup);

function Harness({
  commands,
  organizationId = null,
}: {
  commands: ResolvedCommand[];
  organizationId?: string | null;
}) {
  const surface = useMemo(() => ({ commands }), [commands]);
  useRegisterCommands(surface);
  const [navigated, setNavigated] = useState("");
  return (
    <>
      <CommandPalette
        navItems={[{ to: "/projects", label: "Proyectos" }]}
        onNavigate={setNavigated}
        organizationId={organizationId}
      />
      <output data-testid="navigated">{navigated}</output>
    </>
  );
}

function openPalette() {
  fireEvent.keyDown(window, { key: "k", ctrlKey: true });
  return screen.getByRole("dialog");
}

it("opens with Ctrl+K, filters by keyword, and runs navigation", () => {
  const run = vi.fn();
  render(
    <Harness commands={[{ id: "x.run", title: "Igualar anchos", keywords: ["repartir"], run }]} />,
  );
  const dialog = openPalette();
  expect(dialog.getAttribute("aria-label")).toBe(t("cmd.palette"));

  // Filters command titles and nav labels.
  const input = screen.getByPlaceholderText(t("cmd.placeholder"));
  fireEvent.change(input, { target: { value: "repartir" } });
  expect(screen.getByRole("option", { name: /Igualar anchos/ })).toBeTruthy();
  expect(screen.queryByRole("option", { name: /Proyectos/ })).toBeNull();

  fireEvent.change(input, { target: { value: "proyectos" } });
  fireEvent.click(screen.getByRole("option", { name: /Ir a Proyectos/ }));
  expect(screen.getByTestId("navigated").textContent).toBe("/projects");
  // Closed after running.
  expect(screen.queryByRole("dialog")).toBeNull();

  // Runs a param-free command.
  openPalette();
  fireEvent.click(screen.getByRole("option", { name: /Igualar anchos/ }));
  expect(run).toHaveBeenCalledWith({});
});

it("collects a number parameter before running", () => {
  const run = vi.fn();
  render(
    <Harness
      commands={[
        {
          id: "x.angle",
          title: "Definir ángulo",
          keywords: ["union"],
          params: [{ kind: "number", id: "angle", label: "Ángulo", unit: "°" }],
          run,
        },
      ]}
    />,
  );
  openPalette();
  // Accent-insensitive query still matches "ángulo".
  fireEvent.change(screen.getByPlaceholderText(t("cmd.placeholder")), {
    target: { value: "angulo" },
  });
  fireEvent.click(screen.getByRole("option", { name: /Definir ángulo/ }));
  // Param step: same input becomes the numeric entry.
  const input = screen.getByPlaceholderText("Ángulo");
  fireEvent.change(input, { target: { value: "15.5" } });
  fireEvent.keyDown(input, { key: "Enter" });
  expect(run).toHaveBeenCalledWith({ angle: "15.5" });
  expect(screen.queryByRole("dialog")).toBeNull();
});

it("collects a choice parameter through the option list", () => {
  const run = vi.fn();
  render(
    <Harness
      commands={[
        {
          id: "x.opening",
          title: "Cambiar apertura",
          params: [
            {
              kind: "choice",
              id: "opening",
              label: "Apertura",
              options: [
                { value: "FIXED", label: "Fijo" },
                { value: "TURN_LEFT", label: "Abatible izquierda" },
              ],
            },
          ],
          run,
        },
      ]}
    />,
  );
  openPalette();
  fireEvent.click(screen.getByRole("option", { name: /Cambiar apertura/ }));
  fireEvent.click(screen.getByRole("option", { name: "Abatible izquierda" }));
  expect(run).toHaveBeenCalledWith({ opening: "TURN_LEFT" });
});

it("keeps a rejected number entry open and submits the normalized value", () => {
  const run = vi.fn();
  render(
    <Harness
      commands={[
        {
          id: "x.width",
          title: "Definir ancho",
          params: [
            {
              kind: "number",
              id: "width",
              label: "Ancho",
              validate: (raw) => {
                const value = Number(raw);
                return Number.isFinite(value) && value > 0 ? value.toFixed(2) : null;
              },
            },
          ],
          run,
        },
      ]}
    />,
  );
  openPalette();
  fireEvent.click(screen.getByRole("option", { name: /Definir ancho/ }));
  const input = screen.getByPlaceholderText("Ancho");

  // Invalid input keeps the step open and runs nothing.
  fireEvent.change(input, { target: { value: "abc" } });
  fireEvent.keyDown(input, { key: "Enter" });
  expect(run).not.toHaveBeenCalled();
  expect(screen.getByText(t("cmd.invalidValue"))).toBeTruthy();

  // A valid entry runs with the normalized string and closes.
  fireEvent.change(input, { target: { value: "750" } });
  fireEvent.keyDown(input, { key: "Enter" });
  expect(run).toHaveBeenCalledWith({ width: "750.00" });
  expect(screen.queryByRole("dialog")).toBeNull();
});

it("Enter selects the highlighted choice option, not a top-level item", () => {
  const run = vi.fn();
  const navSpy = vi.fn();
  render(
    <Harness
      commands={[
        { id: "x.decoy", title: "Añadir unidad", run: vi.fn() },
        {
          id: "x.opening",
          title: "Cambiar apertura",
          params: [
            {
              kind: "choice",
              id: "opening",
              label: "Apertura",
              options: [
                { value: "FIXED", label: "Fijo" },
                { value: "TURN_LEFT", label: "Abatible izquierda" },
              ],
            },
          ],
          run,
        },
      ]}
    />,
  );
  void navSpy;
  openPalette();
  fireEvent.click(screen.getByRole("option", { name: /Cambiar apertura/ }));
  const input = screen.getByPlaceholderText("Apertura");
  fireEvent.keyDown(input, { key: "ArrowDown" });
  fireEvent.keyDown(input, { key: "Enter" });
  expect(run).toHaveBeenCalledWith({ opening: "TURN_LEFT" });
  expect(screen.queryByRole("dialog")).toBeNull();
});

it("Escape inside a parameter step abandons it and clears the typed query", () => {
  const run = vi.fn();
  render(
    <Harness
      commands={[
        {
          id: "x.width",
          title: "Definir ancho",
          params: [{ kind: "number", id: "width", label: "Ancho", validate: () => "1.00" }],
          run,
        },
      ]}
    />,
  );
  openPalette();
  fireEvent.click(screen.getByRole("option", { name: /Definir ancho/ }));
  const input = screen.getByPlaceholderText("Ancho");
  fireEvent.change(input, { target: { value: "999" } });
  fireEvent.keyDown(window, { key: "Escape" });
  // Parameter step abandoned, query cleared — the full command list is back.
  const back = screen.getByPlaceholderText(t("cmd.placeholder")) as HTMLInputElement;
  expect(back.value).toBe("");
  expect(run).not.toHaveBeenCalled();
  fireEvent.keyDown(window, { key: "Escape" });
  expect(screen.queryByRole("dialog")).toBeNull();
});

it("closes on Escape and arrows move the cursor", () => {
  render(<Harness commands={[{ id: "x.a", title: "Primero", run: vi.fn() }]} />);
  openPalette();
  const input = screen.getByPlaceholderText(t("cmd.placeholder"));
  fireEvent.keyDown(input, { key: "ArrowDown" });
  fireEvent.keyDown(input, { key: "Enter" });
  // Cursor 1 → the nav item ran rather than the command.
  expect(screen.getByTestId("navigated").textContent).toBe("/projects");

  openPalette();
  fireEvent.keyDown(window, { key: "Escape" });
  expect(screen.queryByRole("dialog")).toBeNull();
});

it("merges global search results into the list and navigates to their path", async () => {
  searchMock.mockResolvedValueOnce({
    status: 200,
    data: {
      results: [
        {
          group: "projects",
          id: "p1",
          title: "PRJ-1 · Hotel Sur",
          subtitle: "Inmobiliaria",
          path: "/projects/p1",
        },
      ],
    },
  });
  vi.useFakeTimers({ shouldAdvanceTime: true });
  try {
    render(<Harness commands={[]} organizationId="org-1" />);
    openPalette();
    fireEvent.change(screen.getByPlaceholderText(t("cmd.placeholder")), {
      target: { value: "hotel" },
    });
    await vi.advanceTimersByTimeAsync(300);
    const option = await screen.findByRole("option", { name: /Hotel Sur/ });
    fireEvent.click(option);
    expect(screen.getByTestId("navigated").textContent).toBe("/projects/p1");
    expect(searchMock).toHaveBeenCalled();
  } finally {
    vi.useRealTimers();
  }
});
