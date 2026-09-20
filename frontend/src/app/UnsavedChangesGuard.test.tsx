import { useState } from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, Link, RouterProvider } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
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
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
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
    await waitFor(() => expect(confirm).toHaveBeenCalledOnce());
    expect(screen.getByLabelText("Nombre")).toHaveValue("Trabajo pendiente");
    expect(router.state.location.pathname).toBe("/edit");
    confirm.mockReturnValue(true);
    fireEvent.click(screen.getByText("Volver"));
    await screen.findByRole("heading", { name: "Proyectos" });
    expect(router.state.location.pathname).toBe("/projects");
  },
);
