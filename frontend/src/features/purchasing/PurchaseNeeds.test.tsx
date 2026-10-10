import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import { ConfirmProvider } from "../../ui";
import { PurchaseNeeds } from "./PurchaseNeeds";

afterEach(cleanup);

it("confirms only the visible reviewed purchase lines and exposes their quantities", async () => {
  const line = {
    version_id: "version",
    project_code: "P-000001",
    order_type: "SUPPLIER_PROFILE_PO",
    unit: "BAR",
    required: "2",
    reserved: "0",
    stock: "0",
    incoming: "0",
    draft: "0",
    purchase: "2.00",
    maximum: "2",
    cause: null,
    is_demo: true,
    supplier_name: "Perfiles Sur",
    supplier_eligibility_id: "supplier",
    orders: [],
  };
  const lines = [
    { ...line, requirement_id: "one", sku: "MARCO-60" },
    { ...line, requirement_id: "two", sku: "JUNQUILLO-60" },
  ];
  const request = vi
    .fn()
    .mockResolvedValue({ preview_hash: "a".repeat(64), lines, blockers: [], remnant_offers: [] });
  const created = vi.fn();
  render(
    <MemoryRouter>
      <ConfirmProvider>
        <PurchaseNeeds request={request} canWrite revision={0} onCreated={created} />
      </ConfirmProvider>
    </MemoryRouter>,
  );
  fireEvent.change(await screen.findByLabelText("Buscar material, proveedor, proyecto u OT"), {
    target: { value: "MARCO" },
  });
  fireEvent.click(screen.getByRole("button", { name: /^Comprar lo que falta$/ }));
  const dialog = await screen.findByRole("dialog");
  expect(dialog.textContent).toContain("MARCO-60: 2 barras");
  expect(dialog.textContent).not.toContain("JUNQUILLO-60");
  fireEvent.click(screen.getByRole("button", { name: "Crear órdenes revisadas" }));
  await waitFor(() => expect(created).toHaveBeenCalledOnce());
  expect(request).toHaveBeenLastCalledWith(
    "purchasing/needs/confirm/",
    "POST",
    expect.objectContaining({
      lines: [{ requirement_id: "one", quantity: "2.00", unit_price: null }],
      confirmed: true,
    }),
  );
});
