import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  billingChangeAbandon,
  billingChangeConfirm,
  billingChangePreview,
  billingCheckout,
  commerceRetrieve,
} from "../../api/generated/dekopen";
import { CommercePanel } from "./CommercePanel";

vi.mock("../../api/generated/dekopen", () => ({
  commerceRetrieve: vi.fn(),
  billingCheckout: vi.fn(),
  billingChangePreview: vi.fn(),
  billingChangeConfirm: vi.fn(),
  billingChangeAbandon: vi.fn(),
  billingSync: vi.fn(),
}));
const offer = {
  id: "offer-id",
  product_code: "BUSINESS",
  kind: "subscription",
  plan_tier: "BUSINESS",
  billing_cycle: "monthly",
  credits: 6000,
  amount: "145068",
  fx_source: "Explicit fixture",
  fx_observed_on: "2026-09-01",
};
const preview = {
  id: "change-id",
  kind: "upgrade",
  state: "prepared",
  effective_at: null,
  amount: "30000",
  currency: "CLP",
  product_code: "BUSINESS",
};
const result = <T,>(data: T) => ({ status: 200 as const, headers: new Headers(), data });
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(commerceRetrieve).mockResolvedValue(
    result({
      offers: [offer],
      checkouts: [],
      registration_state: "registered",
      pending_change: null,
      scheduled_changes: [],
      reconciliation_required: false,
    }),
  );
});
afterEach(cleanup);

it("recovers a pending operation after reload without repeating the mutation", async () => {
  vi.mocked(commerceRetrieve).mockResolvedValue(
    result({
      offers: [offer],
      checkouts: [],
      registration_state: "registered",
      pending_change: { ...preview, state: "uncertain" },
      scheduled_changes: [],
      reconciliation_required: false,
    }),
  );
  render(<CommercePanel orgId="org-a" subscribed onRefresh={vi.fn()} />);
  expect(
    await screen.findByRole("region", { name: "Confirmar cambio de suscripción" }),
  ).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Volver sin confirmar" })).toBeDisabled();
  expect(billingChangePreview).not.toHaveBeenCalled();
  expect(billingChangeConfirm).not.toHaveBeenCalled();
});

it("requires a second human action after Flow preview before changing a plan", async () => {
  vi.mocked(billingChangePreview).mockResolvedValue(result(preview));
  vi.mocked(billingChangeConfirm).mockResolvedValue(result({ ...preview, state: "confirmed" }));
  render(<CommercePanel orgId="org-a" subscribed onRefresh={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: "Revisar cambio" }));
  expect(await screen.findByText(/Ajuste calculado por Flow: CLP 30000/)).toBeInTheDocument();
  expect(billingChangeConfirm).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Confirmar en Flow" }));
  await waitFor(() =>
    expect(billingChangeConfirm).toHaveBeenCalledWith(
      { operation_id: "change-id" },
      { headers: { "X-Organization-ID": "org-a" } },
    ),
  );
});

it("abandons only an undispatched preview without sending a provider mutation", async () => {
  vi.mocked(billingChangePreview).mockResolvedValue(result(preview));
  vi.mocked(billingChangeAbandon).mockResolvedValue(result({ ...preview, state: "abandoned" }));
  render(<CommercePanel orgId="org-a" subscribed onRefresh={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: "Revisar cambio" }));
  fireEvent.click(await screen.findByRole("button", { name: "Volver sin confirmar" }));
  await waitFor(() => expect(billingChangeAbandon).toHaveBeenCalled());
  expect(billingChangeConfirm).not.toHaveBeenCalled();
});

it("reuses the checkout operation after a pending result and never sends a price", async () => {
  vi.mocked(billingCheckout).mockResolvedValue(
    result({
      id: "checkout-id",
      operation_key: "server-key",
      state: "pending",
      redirect_url: null,
    }),
  );
  render(<CommercePanel orgId="org-a" subscribed={false} onRefresh={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: "Contratar con Flow" }));
  await screen.findByText(/La operación se está conciliando/);
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Contratar con Flow" })).toBeEnabled(),
  );
  fireEvent.click(screen.getByRole("button", { name: "Contratar con Flow" }));
  await waitFor(() => expect(billingCheckout).toHaveBeenCalledTimes(2));
  const first = vi.mocked(billingCheckout).mock.calls[0]![0];
  const second = vi.mocked(billingCheckout).mock.calls[1]![0];
  expect(first).toEqual(second);
  expect(Object.keys(first).sort()).toEqual(["offer_id", "operation_key"]);
  expect(screen.queryByText("Pagado")).not.toBeInTheDocument();
});
