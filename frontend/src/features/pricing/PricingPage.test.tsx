import { StrictMode } from "react";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { apiMutator } from "../../api/apiMutator";
import { t } from "../../i18n/es-CL";
import { CommercialPricingPage, PricingPage } from "./PricingPage";

const identity = vi.hoisted(() => ({ id: "tenant-a", role: "OWNER" }));
vi.mock("../../auth/AuthSessionProvider", () => ({
  useAuthSession: () => ({ me: { active_organization: identity } }),
}));
vi.mock("../../api/apiMutator", () => ({ apiMutator: vi.fn(), ApiError: class extends Error {} }));

beforeEach(() => {
  identity.id = "tenant-a";
  identity.role = "OWNER";
  vi.mocked(apiMutator)
    .mockReset()
    .mockResolvedValue({ data: { items: [] } });
});
afterEach(cleanup);

it.each(["ESTIMATOR", "WORKSHOP_MANAGER", "INSTALLER"])(
  "denies S09 to %s without fetching costs",
  (role) => {
    identity.role = role;
    render(<PricingPage />);
    expect(screen.getByRole("alert")).toHaveTextContent(t("pricing.ownerOnly"));
    expect(apiMutator).not.toHaveBeenCalled();
  },
);

it("keeps the current request alive after StrictMode cleanup and aborts on tenant switch", async () => {
  const view = render(
    <StrictMode>
      <PricingPage />
    </StrictMode>,
  );
  await waitFor(() => expect(apiMutator).toHaveBeenCalledTimes(2));
  const previous = vi.mocked(apiMutator).mock.calls[1]?.[1].signal;
  expect(previous?.aborted).toBe(false);
  identity.id = "tenant-b";
  view.rerender(
    <StrictMode>
      <PricingPage />
    </StrictMode>,
  );
  expect(previous?.aborted).toBe(true);
  await waitFor(() =>
    expect(apiMutator).toHaveBeenLastCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({ "X-Organization-ID": "tenant-b" }),
      }),
    ),
  );
});

it("lets an estimator calculate without requesting confidential administration", async () => {
  identity.role = "ESTIMATOR";
  render(<CommercialPricingPage />);
  expect(screen.getByText(t("pricing.calculate"))).toBeInTheDocument();
  expect(apiMutator).not.toHaveBeenCalled();
  expect(screen.queryByText(t("pricing.cost"))).not.toBeInTheDocument();
});

it("does not apply a late preview after its financial input changes", async () => {
  identity.role = "ESTIMATOR";
  let resolve: (value: unknown) => void = () => undefined;
  vi.mocked(apiMutator).mockImplementation(
    () =>
      new Promise((done) => {
        resolve = done;
      }),
  );
  render(<CommercialPricingPage />);
  const submit = screen.getByRole("button", { name: t("pricing.preview") });
  fireEvent.submit(submit.closest("form")!);
  fireEvent.change(screen.getByLabelText(t("pricing.discount")), { target: { value: "0.05" } });
  await act(async () =>
    resolve({ data: { id: "stale", state: "PREVIEW", currency: "CLP", project_net: "1000" } }),
  );
  expect(screen.queryByRole("button", { name: t("pricing.apply") })).not.toBeInTheDocument();
});

it("allows an owner to review and reject a saved pending request", async () => {
  const pending = {
    id: "operation-a",
    project_id: "project-a",
    discount_pct: "0.15",
    state: "PENDING",
    currency: "CLP",
    project_net: "850",
    project_tax: "162",
    project_gross: "1012",
  };
  vi.mocked(apiMutator)
    .mockResolvedValueOnce({ data: [pending] })
    .mockResolvedValueOnce({ data: { ...pending, state: "REJECTED" } });
  render(<CommercialPricingPage />);
  fireEvent.click(screen.getByRole("button", { name: t("pricing.reload") }));
  fireEvent.click(await screen.findByRole("button", { name: t("pricing.review") }));
  fireEvent.change(screen.getByLabelText(t("pricing.reason")), {
    target: { value: "Descuento no autorizado" },
  });
  fireEvent.click(screen.getByRole("button", { name: t("pricing.reject") }));
  await waitFor(() =>
    expect(apiMutator).toHaveBeenCalledWith(
      "/api/v1/pricing/operations/operation-a/apply/",
      expect.objectContaining({
        body: JSON.stringify({ reason: "Descuento no autorizado", confirmed: false, reject: true }),
      }),
    ),
  );
});
