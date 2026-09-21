import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { billingRetrieve } from "../../api/generated/dekopen";
import { BillingPage } from "./BillingPage";

const identity = vi.hoisted(() => ({ id: "tenant-a", role: "OWNER" }));
vi.mock("../../auth/AuthSessionProvider", () => ({
  useAuthSession: () => ({ me: { active_organization: identity } }),
}));
vi.mock("../../api/generated/dekopen", () => ({ billingRetrieve: vi.fn() }));

beforeEach(() => {
  identity.role = "OWNER";
  vi.clearAllMocks();
});
afterEach(cleanup);

it("shows a pending asynchronous payment without inventing a fiscal receipt", async () => {
  vi.mocked(billingRetrieve).mockResolvedValue({
    status: 200,
    headers: new Headers(),
    data: {
      plan: "STARTER",
      trial_ends_at: null,
      subscription: null,
      payments: [
        {
          id: "payment-a",
          amount: "43857",
          currency: "CLP",
          status: "pending",
          tax_doc_type: null,
          tax_doc_folio: null,
          created_at: "2026-09-20T12:00:00Z",
        },
      ],
    },
  });
  render(<BillingPage />);
  expect(await screen.findByText("CLP 43857")).toBeInTheDocument();
  expect(screen.getByText("Pendiente de confirmación")).toBeInTheDocument();
  expect(screen.queryByText("Pagado")).not.toBeInTheDocument();
  expect(screen.getByText("No disponible")).toBeInTheDocument();
  expect(billingRetrieve).toHaveBeenCalledWith(
    expect.objectContaining({ headers: { "X-Organization-ID": "tenant-a" } }),
  );
});

it("does not request payment history for an estimator", () => {
  identity.role = "ESTIMATOR";
  render(<BillingPage />);
  expect(screen.getByRole("alert")).toHaveTextContent("Solo el propietario");
  expect(billingRetrieve).not.toHaveBeenCalled();
});
