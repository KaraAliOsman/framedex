import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import * as api from "../api/generated/dekopen";
import { CreateWorkshop } from "./CreateWorkshop";

const auth = vi.hoisted(() => ({
  selectOrganization: vi.fn(),
  signOut: vi.fn(),
}));
vi.mock("./AuthSessionProvider", () => ({
  useAuthSession: () => ({
    status: "no_membership",
    session: { user: { id: "nuevo", email: "nuevo@taller.test" } },
    ...auth,
  }),
}));
vi.mock("../api/generated/dekopen", () => ({ workshopCreate: vi.fn() }));
afterEach(cleanup);
beforeEach(() => vi.resetAllMocks());

test("a new person names their workshop and enters it as its owner", async () => {
  vi.mocked(api.workshopCreate).mockResolvedValue({
    status: 200,
    data: { organization_id: "org-nuevo" },
    headers: new Headers(),
  });
  render(<CreateWorkshop />);
  expect(screen.getByText("nuevo@taller.test")).toBeInTheDocument();
  expect(screen.getByText("Chile")).toBeInTheDocument();
  expect(screen.getByText("19 %")).toBeInTheDocument();
  const submit = screen.getByRole("button", { name: "Crear mi taller" });
  fireEvent.change(screen.getByLabelText("Nombre del taller"), { target: { value: " x " } });
  expect(submit).toBeDisabled();
  fireEvent.change(screen.getByLabelText("Nombre del taller"), {
    target: { value: "  Ventanas del Sur  " },
  });
  fireEvent.click(submit);
  await waitFor(() => expect(auth.selectOrganization).toHaveBeenCalledWith("org-nuevo"));
  expect(api.workshopCreate).toHaveBeenCalledWith({ name: "Ventanas del Sur" });
});

test("a refused creation explains itself and keeps the person on the form", async () => {
  vi.mocked(api.workshopCreate).mockRejectedValue(new Error("network"));
  render(<CreateWorkshop />);
  fireEvent.change(screen.getByLabelText("Nombre del taller"), {
    target: { value: "Ventanas del Sur" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Crear mi taller" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo crear el taller");
  expect(auth.selectOrganization).not.toHaveBeenCalled();
});
