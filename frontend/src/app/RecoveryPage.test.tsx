import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { ConnectionBoundary } from "./RecoveryPage";

afterEach(() => vi.restoreAllMocks());

test("a connection loss preserves the mounted editor and its unsaved input", () => {
  vi.spyOn(navigator, "onLine", "get").mockReturnValue(true);
  render(
    <ConnectionBoundary>
      <input aria-label="Borrador" defaultValue="Primera ventana" />
    </ConnectionBoundary>,
  );
  fireEvent.change(screen.getByLabelText("Borrador"), {
    target: { value: "Medida por confirmar" },
  });
  vi.spyOn(navigator, "onLine", "get").mockReturnValue(false);
  fireEvent(window, new Event("offline"));
  expect(screen.getByRole("heading", { name: "Sin conexión" })).toBeInTheDocument();
  expect(screen.getByLabelText("Borrador")).toHaveValue("Medida por confirmar");
  vi.spyOn(navigator, "onLine", "get").mockReturnValue(true);
  fireEvent(window, new Event("online"));
  expect(screen.queryByRole("heading", { name: "Sin conexión" })).not.toBeInTheDocument();
  expect(screen.getByLabelText("Borrador")).toBeVisible();
  expect(screen.getByLabelText("Borrador")).toHaveValue("Medida por confirmar");
});
