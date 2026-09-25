import { useState } from "react";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { createMemoryRouter, Link, RouterProvider } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import { t } from "../i18n/es-CL";
import { UnsavedChangesGuard } from "./UnsavedChangesGuard";

afterEach(() => vi.restoreAllMocks());

function Editor(): JSX.Element {
  const [dirty, setDirty] = useState(false);
  return (
    <>
      <UnsavedChangesGuard dirty={dirty} message="Descartar cambios" />
      <input aria-label="Nombre" onChange={() => setDirty(true)} />
      <Link to="/projects">Volver</Link>
    </>
  );
}

it.each(["link", "back"] as const)(
  "preserves edits when %s navigation is cancelled",
  async (mode) => {
    const router = createMemoryRouter(
      [
        { path: "/edit", element: <Editor /> },
        { path: "/projects", element: <h1>Proyectos</h1> },
      ],
      { initialEntries: ["/projects", "/edit"], initialIndex: 1 },
    );
    render(<RouterProvider router={router} />);
    fireEvent.change(screen.getByLabelText("Nombre"), { target: { value: "Trabajo pendiente" } });
    if (mode === "link") fireEvent.click(screen.getByText("Volver"));
    else
      await act(async () => {
        await router.navigate(-1);
      });
    const dialog = await screen.findByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: t("ui.cancel") }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(screen.getByLabelText("Nombre")).toHaveValue("Trabajo pendiente");
    expect(router.state.location.pathname).toBe("/edit");
    fireEvent.click(screen.getByText("Volver"));
    const confirmDialog = await screen.findByRole("dialog");
    fireEvent.click(within(confirmDialog).getByRole("button", { name: t("ui.confirm") }));
    await screen.findByRole("heading", { name: "Proyectos" });
    expect(router.state.location.pathname).toBe("/projects");
  },
);
