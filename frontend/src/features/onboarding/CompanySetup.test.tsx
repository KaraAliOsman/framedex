import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import { CompanySetup } from "./CompanySetup";

vi.mock("../settings/AdminSections", () => ({
  CompanyCard: ({ canEdit, onSaved }: { canEdit: boolean; onSaved: () => void }) =>
    canEdit ? <button onClick={onSaved}>Guardar identidad</button> : <p>Identidad de lectura</p>,
}));
vi.mock("../projects/DocumentSettings", () => ({
  DocumentSettings: ({ section, onSaved }: { section: string; onSaved: () => void }) => (
    <button onClick={onSaved}>Guardar {section}</button>
  ),
}));
vi.mock("../pricing/PricingPage", () => ({ PricingRulesSettings: () => <p>Reglas del dueño</p> }));
afterEach(cleanup);

test("a company setup cannot advance to first project before each section is saved and confirmed", () => {
  const complete = vi.fn();
  render(
    <MemoryRouter>
      <CompanySetup orgId="a" owner onComplete={complete} />
    </MemoryRouter>,
  );
  expect(screen.getByRole("button", { name: "Confirmar y continuar" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Guardar identidad" }));
  fireEvent.click(screen.getByRole("button", { name: "Confirmar y continuar" }));
  expect(screen.getByRole("button", { name: "Confirmar y continuar" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Guardar commercial" }));
  fireEvent.click(screen.getByRole("button", { name: "Confirmar y continuar" }));
  expect(screen.getByRole("button", { name: "Crear primer proyecto" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Guardar documents" }));
  fireEvent.click(screen.getByRole("button", { name: "Crear primer proyecto" }));
  expect(complete).toHaveBeenCalledOnce();
});

test("an estimator explicitly continues with existing identity without legal or pricing writes", () => {
  render(
    <MemoryRouter>
      <CompanySetup orgId="a" owner={false} onComplete={vi.fn()} />
    </MemoryRouter>,
  );
  expect(screen.queryByRole("button", { name: "Guardar identidad" })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Continuar con mi acceso" }));
  fireEvent.click(screen.getByRole("button", { name: "Confirmar y continuar" }));
  expect(screen.getByRole("button", { name: "Guardar commercial" })).toBeInTheDocument();
  expect(screen.queryByText("Reglas del dueño")).not.toBeInTheDocument();
});
