import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import {
  productionWorkCenters,
  productionWorkCentersCreate,
  catalogProcessProfileList,
} from "../../api/generated/dekopen";
import { ConfirmProvider } from "../../ui";
import { ProductionSettings } from "./ProductionSettings";

vi.mock("../../api/generated/dekopen", () => ({
  productionWorkCenters: vi.fn(),
  productionWorkCentersCreate: vi.fn(),
  catalogProcessProfileList: vi.fn(),
}));
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});

it("creates a station and edits its existing code without changing identity", async () => {
  const center = {
    id: "station",
    code: "CUT-01",
    name: "Corte",
    kind: "CUT",
    display_order: 1,
    active: true,
  };
  vi.mocked(productionWorkCenters).mockResolvedValue({
    status: 200,
    headers: new Headers(),
    data: { centers: [center] },
  });
  vi.mocked(catalogProcessProfileList).mockResolvedValue({
    status: 200,
    headers: new Headers(),
    data: { items: [] },
  });
  vi.mocked(productionWorkCentersCreate).mockResolvedValue({
    status: 200,
    headers: new Headers(),
    data: center,
  });
  render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <MemoryRouter>
        <ConfirmProvider>
          <ProductionSettings orgId="org" canEdit />
        </ConfirmProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
  fireEvent.click(await screen.findByRole("button", { name: "Editar estación" }));
  expect(screen.getByLabelText("Código de estación")).toHaveAttribute("readonly");
  fireEvent.change(screen.getByLabelText("Nombre"), { target: { value: "Corte norte" } });
  fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
  fireEvent.click(await screen.findByRole("button", { name: "Confirmar" }));
  await waitFor(() =>
    expect(productionWorkCentersCreate).toHaveBeenCalledWith(
      { code: "CUT-01", name: "Corte norte", kind: "CUT", display_order: 1 },
      expect.anything(),
    ),
  );
  await screen.findByText("Estación guardada.");
  expect(screen.getByLabelText("Código de estación")).not.toHaveAttribute("readonly");
  fireEvent.change(screen.getByLabelText("Código de estación"), { target: { value: "CUT-02" } });
  fireEvent.change(screen.getByLabelText("Nombre"), { target: { value: "Corte sur" } });
  fireEvent.click(screen.getByRole("button", { name: "Guardar estación" }));
  fireEvent.click(await screen.findByRole("button", { name: "Confirmar" }));
  await waitFor(() =>
    expect(productionWorkCentersCreate).toHaveBeenLastCalledWith(
      { code: "CUT-02", name: "Corte sur", kind: "CUT", display_order: 1 },
      expect.anything(),
    ),
  );
  expect(productionWorkCentersCreate).toHaveBeenCalledTimes(2);
});
