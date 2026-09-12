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

function deferred() {
  let resolve!: (value: unknown) => void;
  let reject!: (reason: Error) => void;
  const promise = new Promise<unknown>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}
function result(id: string, state = "PREVIEW") {
  return {
    id,
    project_id: `project-${id}`,
    discount_pct: "0.05",
    state,
    currency: "CLP",
    project_net: id === "B" ? "200" : "100",
    project_tax: "19",
    project_gross: "119",
  };
}
function previewButton() {
  return screen.getByRole("button", { name: t("pricing.preview") });
}
function submitPreview() {
  fireEvent.submit(previewButton().closest("form")!);
}
function changeFinancialInput() {
  fireEvent.change(screen.getByLabelText(t("pricing.discount")), { target: { value: "0.07" } });
}
async function settle(task: ReturnType<typeof deferred>, value: unknown, failure = false) {
  await act(async () => {
    if (failure) task.reject(new Error("controlled failure"));
    else task.resolve({ data: value });
  });
}

it.each([false, true])(
  "invalidated preview success/failure cannot publish or finish a newer request (failure=%s)",
  async (failure) => {
    const a = deferred(),
      b = deferred();
    vi.mocked(apiMutator)
      .mockImplementationOnce(() => a.promise)
      .mockImplementationOnce(() => b.promise);
    render(<CommercialPricingPage />);
    submitPreview();
    changeFinancialInput();
    expect(previewButton()).toBeEnabled();
    submitPreview();
    await settle(a, result("A"), failure);
    expect(previewButton()).toBeDisabled();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.queryByText("Proyecto: project-A")).not.toBeInTheDocument();
    await settle(b, result("B"));
    expect(screen.getByText("Proyecto: project-B")).toBeInTheDocument();
    expect(previewButton()).toBeEnabled();
  },
);

it("preview B alone wins when B completes before A", async () => {
  const a = deferred(),
    b = deferred();
  vi.mocked(apiMutator)
    .mockImplementationOnce(() => a.promise)
    .mockImplementationOnce(() => b.promise);
  render(<CommercialPricingPage />);
  submitPreview();
  changeFinancialInput();
  submitPreview();
  await settle(b, result("B"));
  await settle(a, result("A"));
  expect(screen.getByText("Proyecto: project-B")).toBeInTheDocument();
  expect(screen.queryByText("Proyecto: project-A")).not.toBeInTheDocument();
  expect(previewButton()).toBeEnabled();
});

it("current preview failure remains visible and releases its busy authority", async () => {
  const task = deferred();
  vi.mocked(apiMutator).mockImplementationOnce(() => task.promise);
  render(<CommercialPricingPage />);
  submitPreview();
  expect(previewButton()).toBeDisabled();
  await settle(task, null, true);
  expect(screen.getByRole("alert")).toHaveTextContent(t("pricing.calculateError"));
  expect(previewButton()).toBeEnabled();
});

it.each(["apply", "reject"] as const)(
  "stale %s cannot replace a newer preview; reload reflects the persisted mutation",
  async (action) => {
    const mutation = deferred(),
      next = deferred();
    const original = result("A", action === "reject" ? "PENDING" : "PREVIEW");
    const persisted = result("A", action === "reject" ? "REJECTED" : "APPLIED");
    vi.mocked(apiMutator)
      .mockResolvedValueOnce({ data: original })
      .mockImplementationOnce(() => mutation.promise)
      .mockImplementationOnce(() => next.promise)
      .mockResolvedValueOnce({ data: [persisted] });
    render(<CommercialPricingPage />);
    submitPreview();
    await screen.findByText("Proyecto: project-A");
    fireEvent.change(screen.getByLabelText(t("pricing.reason")), { target: { value: "Reviewed" } });
    fireEvent.click(
      screen.getByRole("button", {
        name: t(action === "reject" ? "pricing.reject" : "pricing.apply"),
      }),
    );
    changeFinancialInput();
    submitPreview();
    await settle(mutation, persisted);
    expect(previewButton()).toBeDisabled();
    expect(screen.queryByText("Proyecto: project-A")).not.toBeInTheDocument();
    await settle(next, result("B"));
    expect(screen.getByText("Proyecto: project-B")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: t("pricing.reload") }));
    await screen.findByRole("button", { name: t("pricing.review") });
    expect(
      screen.getByText(t(action === "reject" ? "pricing.rejected" : "pricing.applied")),
    ).toBeInTheDocument();
    expect(screen.getByText("Proyecto: project-B")).toBeInTheDocument();
  },
);

it.each(["apply", "reject"] as const)(
  "stale %s failure cannot publish error or release newer busy",
  async (action) => {
    const mutation = deferred(),
      next = deferred();
    vi.mocked(apiMutator)
      .mockResolvedValueOnce({ data: result("A", action === "reject" ? "PENDING" : "PREVIEW") })
      .mockImplementationOnce(() => mutation.promise)
      .mockImplementationOnce(() => next.promise);
    render(<CommercialPricingPage />);
    submitPreview();
    await screen.findByText("Proyecto: project-A");
    fireEvent.change(screen.getByLabelText(t("pricing.reason")), { target: { value: "Reviewed" } });
    fireEvent.click(
      screen.getByRole("button", {
        name: t(action === "reject" ? "pricing.reject" : "pricing.apply"),
      }),
    );
    changeFinancialInput();
    submitPreview();
    await settle(mutation, null, true);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(previewButton()).toBeDisabled();
    await settle(next, result("B"));
  },
);

it.each([false, true])(
  "reload A cannot publish or finish reload B (failure=%s)",
  async (failure) => {
    const a = deferred(),
      b = deferred();
    vi.mocked(apiMutator)
      .mockImplementationOnce(() => a.promise)
      .mockImplementationOnce(() => b.promise);
    render(<CommercialPricingPage />);
    fireEvent.click(screen.getByRole("button", { name: t("pricing.reload") }));
    changeFinancialInput();
    fireEvent.click(screen.getByRole("button", { name: t("pricing.reload") }));
    await settle(a, [result("A")], failure);
    expect(previewButton()).toBeDisabled();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.queryByText("100 CLP")).not.toBeInTheDocument();
    await settle(b, [result("B")]);
    expect(screen.getByText("200 CLP")).toBeInTheDocument();
    expect(previewButton()).toBeEnabled();
  },
);

it("reload B remains authoritative after late reload A", async () => {
  const a = deferred(),
    b = deferred();
  vi.mocked(apiMutator)
    .mockImplementationOnce(() => a.promise)
    .mockImplementationOnce(() => b.promise);
  render(<CommercialPricingPage />);
  fireEvent.click(screen.getByRole("button", { name: t("pricing.reload") }));
  changeFinancialInput();
  fireEvent.click(screen.getByRole("button", { name: t("pricing.reload") }));
  await settle(b, [result("B")]);
  await settle(a, [result("A")]);
  expect(screen.getByText("200 CLP")).toBeInTheDocument();
  expect(screen.queryByText("100 CLP")).not.toBeInTheDocument();
});

it.each([false, true])(
  "StrictMode tenant replacement rejects late preview publication (failure=%s)",
  async (failure) => {
    const a = deferred(),
      b = deferred();
    vi.mocked(apiMutator)
      .mockImplementationOnce(() => a.promise)
      .mockImplementationOnce(() => b.promise);
    const view = render(
      <StrictMode>
        <CommercialPricingPage />
      </StrictMode>,
    );
    submitPreview();
    const signal = vi.mocked(apiMutator).mock.calls[0]?.[1].signal;
    identity.id = "tenant-b";
    view.rerender(
      <StrictMode>
        <CommercialPricingPage />
      </StrictMode>,
    );
    expect(signal?.aborted).toBe(true);
    submitPreview();
    await settle(a, result("A"), failure);
    expect(previewButton()).toBeDisabled();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    await settle(b, result("B"));
    expect(screen.getByText("Proyecto: project-B")).toBeInTheDocument();
    expect(previewButton()).toBeEnabled();
    view.unmount();
  },
);

it("unmount settles a rejected request without unhandled publication", async () => {
  const task = deferred();
  vi.mocked(apiMutator).mockImplementationOnce(() => task.promise);
  const view = render(<CommercialPricingPage />);
  submitPreview();
  view.unmount();
  await settle(task, null, true);
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});

it.each(["reload", "apply", "reject"] as const)(
  "current %s failure is shown and releases busy",
  async (action) => {
    const task = deferred();
    if (action !== "reload")
      vi.mocked(apiMutator).mockResolvedValueOnce({
        data: result("A", action === "reject" ? "PENDING" : "PREVIEW"),
      });
    vi.mocked(apiMutator).mockImplementationOnce(() => task.promise);
    render(<CommercialPricingPage />);
    if (action !== "reload") {
      submitPreview();
      await screen.findByText("Proyecto: project-A");
      fireEvent.change(screen.getByLabelText(t("pricing.reason")), {
        target: { value: "Reviewed" },
      });
    }
    fireEvent.click(
      screen.getByRole("button", {
        name: t(
          action === "reload"
            ? "pricing.reload"
            : action === "reject"
              ? "pricing.reject"
              : "pricing.apply",
        ),
      }),
    );
    expect(previewButton()).toBeDisabled();
    await settle(task, null, true);
    expect(screen.getByRole("alert")).toHaveTextContent(
      t(action === "reload" ? "pricing.loadError" : "pricing.applyError"),
    );
    expect(previewButton()).toBeEnabled();
  },
);

it.each(["apply", "reject"] as const)(
  "late %s success cannot replace preview B that already completed",
  async (action) => {
    const task = deferred();
    vi.mocked(apiMutator)
      .mockResolvedValueOnce({ data: result("A", action === "reject" ? "PENDING" : "PREVIEW") })
      .mockImplementationOnce(() => task.promise)
      .mockResolvedValueOnce({ data: result("B") });
    render(<CommercialPricingPage />);
    submitPreview();
    await screen.findByText("Proyecto: project-A");
    fireEvent.change(screen.getByLabelText(t("pricing.reason")), { target: { value: "Reviewed" } });
    fireEvent.click(
      screen.getByRole("button", {
        name: t(action === "reject" ? "pricing.reject" : "pricing.apply"),
      }),
    );
    changeFinancialInput();
    submitPreview();
    await screen.findByText("Proyecto: project-B");
    await settle(task, result("A", action === "reject" ? "REJECTED" : "APPLIED"));
    expect(screen.getByText("Proyecto: project-B")).toBeInTheDocument();
    expect(screen.queryByText("Proyecto: project-A")).not.toBeInTheDocument();
    expect(previewButton()).toBeEnabled();
  },
);
