import { StrictMode } from "react";
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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

const costListRow = {
  id: "9f4e5a00-0000-4000-8000-000000000001",
  supplier_name: "Proveedor Fixture",
  description: "",
  currency: "CLP",
  valid_from: "2026-09-01",
  valid_to: null,
  is_active: true,
};

function importRow(sku: string) {
  return { sku, unit: "M", unit_cost: "12.5" };
}

function importSection(): HTMLElement {
  return screen.getByRole("heading", { name: t("pricing.import") }).closest("section")!;
}
function importPreviewButton(): HTMLElement {
  return within(importSection()).getByRole("button", { name: t("pricing.previewImport") });
}
function importCalls() {
  return vi.mocked(apiMutator).mock.calls.filter((call) => String(call[0]).endsWith("import/"));
}
function adminCalls() {
  return vi.mocked(apiMutator).mock.calls.filter((call) => String(call[0]).includes("admin/"));
}
function applyCalls() {
  return importCalls().filter((call) => (call[1]?.body as FormData).get("apply") === "true");
}
function tenantCalls(organization: string) {
  return vi
    .mocked(apiMutator)
    .mock.calls.filter(
      (call) => (call[1]?.headers as Record<string, string>)["X-Organization-ID"] === organization,
    );
}
function mockImportRequests(tasks: Array<ReturnType<typeof deferred>>) {
  let index = 0;
  vi.mocked(apiMutator).mockImplementation((url) => {
    if (String(url).endsWith("import/")) {
      const task = tasks[index];
      index += 1;
      return task ? task.promise : Promise.reject(new Error("unexpected import request"));
    }
    return Promise.resolve({ data: { items: [costListRow] } });
  });
}
async function fillImportForm() {
  const section = importSection();
  await within(section).findByRole("option", { name: /Proveedor Fixture/ });
  fireEvent.change(within(section).getByLabelText(t("pricing.listId")), {
    target: { value: costListRow.id },
  });
  fireEvent.change(within(section).getByLabelText(t("pricing.file")), {
    target: { files: [new File(["SKU,Precio"], "lista.xlsx")] },
  });
  fireEvent.change(within(section).getByLabelText(t("pricing.reason")), {
    target: { value: "Carga inicial auditada" },
  });
}
function submitImport() {
  fireEvent.submit(importPreviewButton().closest("form")!);
}
function changeImportInput() {
  fireEvent.change(within(importSection()).getByLabelText(t("pricing.reason")), {
    target: { value: "Otro motivo auditado" },
  });
}
function confirmImportButton() {
  return within(importSection()).queryByRole("button", { name: t("pricing.confirmImport") });
}

it.each([false, true])(
  "stale import preview cannot publish after an input change (failure=%s)",
  async (failure) => {
    const a = deferred();
    mockImportRequests([a]);
    render(<PricingPage />);
    await fillImportForm();
    submitImport();
    expect(importPreviewButton()).toBeDisabled();
    changeImportInput();
    await settle(a, { items: [importRow("SKU-A")] }, failure);
    expect(importPreviewButton()).toBeEnabled();
    expect(within(importSection()).queryByRole("alert")).not.toBeInTheDocument();
    expect(within(importSection()).queryByText("SKU-A")).not.toBeInTheDocument();
    expect(confirmImportButton()).not.toBeInTheDocument();
  },
);

it("superseded import preview A cannot publish or release B's busy authority", async () => {
  const a = deferred(),
    b = deferred();
  mockImportRequests([a, b]);
  render(<PricingPage />);
  await fillImportForm();
  submitImport();
  submitImport();
  await settle(a, { items: [importRow("SKU-A")] });
  expect(importPreviewButton()).toBeDisabled();
  expect(within(importSection()).queryByText("SKU-A")).not.toBeInTheDocument();
  await settle(b, { items: [importRow("SKU-B")] });
  expect(within(importSection()).getByText("SKU-B")).toBeInTheDocument();
  expect(importPreviewButton()).toBeEnabled();
});

it.each([false, true])(
  "import preview B failure is published and late A cannot replace or clear it (late failure=%s)",
  async (lateFailure) => {
    const a = deferred(),
      b = deferred();
    mockImportRequests([a, b]);
    render(<PricingPage />);
    await fillImportForm();
    submitImport();
    submitImport();
    expect(importPreviewButton()).toBeDisabled();
    await settle(b, null, true);
    expect(within(importSection()).getByRole("alert")).toHaveTextContent(t("pricing.importError"));
    expect(importPreviewButton()).toBeEnabled();
    await settle(a, { items: [importRow("SKU-A")] }, lateFailure);
    expect(within(importSection()).getByRole("alert")).toHaveTextContent(t("pricing.importError"));
    expect(within(importSection()).queryByText("SKU-A")).not.toBeInTheDocument();
    expect(confirmImportButton()).not.toBeInTheDocument();
    expect(importPreviewButton()).toBeEnabled();
  },
);

it("import preview B remains authoritative after late A completes", async () => {
  const a = deferred(),
    b = deferred(),
    applied = deferred();
  mockImportRequests([a, b, applied]);
  render(<PricingPage />);
  await fillImportForm();
  submitImport();
  submitImport();
  await settle(b, { items: [importRow("SKU-B")] });
  expect(within(importSection()).getByText("SKU-B")).toBeInTheDocument();
  await settle(a, { items: [importRow("SKU-A")] });
  expect(within(importSection()).getByText("SKU-B")).toBeInTheDocument();
  expect(within(importSection()).queryByText("SKU-A")).not.toBeInTheDocument();
  fireEvent.click(confirmImportButton()!);
  expect(applyCalls()).toHaveLength(1);
  expect((applyCalls()[0]?.[1]?.body as FormData).get("apply")).toBe("true");
  await settle(applied, { items: [] });
});

it.each([false, true])(
  "stale durable apply releases busy, reloads once and never restores pending (failure=%s)",
  async (failure) => {
    const previewTask = deferred(),
      applyTask = deferred();
    mockImportRequests([previewTask, applyTask]);
    render(<PricingPage />);
    await fillImportForm();
    submitImport();
    await settle(previewTask, { items: [importRow("SKU-P")] });
    const confirm = within(importSection()).getByRole("button", {
      name: t("pricing.confirmImport"),
    });
    act(() => {
      confirm.click();
      confirm.click();
    });
    expect(importPreviewButton()).toBeDisabled();
    expect(within(importSection()).queryByText("SKU-P")).not.toBeInTheDocument();
    expect(confirmImportButton()).not.toBeInTheDocument();
    expect(applyCalls()).toHaveLength(1);
    expect((applyCalls()[0]?.[1]?.body as FormData).get("apply")).toBe("true");
    changeImportInput();
    expect(importPreviewButton()).toBeDisabled();
    await settle(applyTask, { items: [importRow("SKU-APPLIED")] }, failure);
    expect(importPreviewButton()).toBeEnabled();
    expect(within(importSection()).queryByText("SKU-APPLIED")).not.toBeInTheDocument();
    expect(within(importSection()).queryByRole("alert")).not.toBeInTheDocument();
    expect(confirmImportButton()).not.toBeInTheDocument();
    expect(importCalls()).toHaveLength(2);
    expect(applyCalls()).toHaveLength(1);
    expect(adminCalls()).toHaveLength(2);
  },
);

it.each([false, true])(
  "unmounted import request settles without publication (failure=%s)",
  async (failure) => {
    const task = deferred();
    mockImportRequests([task]);
    const view = render(<PricingPage />);
    await fillImportForm();
    submitImport();
    expect(importCalls()).toHaveLength(1);
    view.unmount();
    await settle(task, { items: [importRow("SKU-X")] }, failure);
    expect(view.container.innerHTML).toBe("");
    expect(importCalls()).toHaveLength(1);
  },
);

it.each([false, true])(
  "tenant replacement aborts an outstanding import apply and suppresses its reload (failure=%s)",
  async (failure) => {
    const previewTask = deferred(),
      applyTask = deferred();
    mockImportRequests([previewTask, applyTask]);
    const view = render(
      <StrictMode>
        <PricingPage />
      </StrictMode>,
    );
    await fillImportForm();
    submitImport();
    await settle(previewTask, { items: [importRow("SKU-T")] });
    fireEvent.click(confirmImportButton()!);
    const signal = applyCalls()[0]?.[1]?.signal;
    identity.id = "tenant-b";
    view.rerender(
      <StrictMode>
        <PricingPage />
      </StrictMode>,
    );
    expect(signal?.aborted).toBe(true);
    await waitFor(() => expect(tenantCalls("tenant-b").length).toBeGreaterThan(0));
    const oldTenantCalls = tenantCalls("tenant-a").length;
    await settle(applyTask, { items: [importRow("SKU-T")] }, failure);
    expect(tenantCalls("tenant-a")).toHaveLength(oldTenantCalls);
    expect(importCalls()).toHaveLength(2);
    expect(within(importSection()).queryByText("SKU-T")).not.toBeInTheDocument();
    expect(within(importSection()).queryByRole("alert")).not.toBeInTheDocument();
    view.unmount();
  },
);
