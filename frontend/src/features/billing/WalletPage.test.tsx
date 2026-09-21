import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { walletRetrieve } from "../../api/generated/dekopen";
import { WalletPage } from "./WalletPage";

const identity = vi.hoisted(() => ({ id: "tenant-a", role: "OWNER" }));
vi.mock("../../auth/AuthSessionProvider", () => ({
  useAuthSession: () => ({ me: { active_organization: identity } }),
}));
vi.mock("../../api/generated/dekopen", () => ({ walletRetrieve: vi.fn() }));

beforeEach(() => {
  identity.role = "OWNER";
  vi.clearAllMocks();
});
afterEach(cleanup);

it("shows zero balance with continuing manual operation", async () => {
  vi.mocked(walletRetrieve).mockResolvedValue({
    status: 200,
    headers: new Headers(),
    data: {
      plan: "STARTER",
      balance: 0,
      trial_ends_at: null,
      billing_cycle: "annual",
      ai_available: false,
      ledger: [],
    },
  });
  render(<WalletPage />);
  expect(await screen.findByText(/Las funciones manuales siguen disponibles/)).toBeInTheDocument();
  expect(screen.getByText("0")).toBeInTheDocument();
  expect(walletRetrieve).toHaveBeenCalledWith(
    expect.objectContaining({ headers: { "X-Organization-ID": "tenant-a" } }),
  );
});

it("does not request OWNER data for another role", () => {
  identity.role = "ESTIMATOR";
  render(<WalletPage />);
  expect(screen.getByRole("alert")).toHaveTextContent("Solo el propietario");
  expect(walletRetrieve).not.toHaveBeenCalled();
});

it("displays a recovery action after an API failure", async () => {
  vi.mocked(walletRetrieve).mockRejectedValue(new Error("network"));
  render(<WalletPage />);
  expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo actualizar");
  expect(screen.getByRole("button", { name: "Actualizar" })).toBeEnabled();
});
