// frontend/src/features/commands/CommandPalette.test.tsx
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useMemo, useState } from "react";
import { afterEach, expect, it, vi } from "vitest";

import { t } from "../../i18n/es-CL";
import { CommandPalette } from "./CommandPalette";
import { useRegisterCommands } from "./registry";
import type { CommandDefinition } from "./types";

afterEach(cleanup);

function Harness({ commands }: { commands: CommandDefinition[] }) {
  const surface = useMemo(() => ({ commands }), [commands]);
  useRegisterCommands(surface);
  const [navigated, setNavigated] = useState("");
  return (
    <>
      <CommandPalette
        navItems={[{ to: "/projects", label: "Proyectos" }]}
        onNavigate={setNavigated}
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
