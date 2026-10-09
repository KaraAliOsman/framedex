import { StrictMode } from "react";
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { apiMutator } from "../../api/apiMutator";
import { t } from "../../i18n/es-CL";
import { PricingPage } from "./PricingPage";

/** Pages under test render router Links (e.g. the demo-design shortcut). */
const page = (ui: JSX.Element): JSX.Element => <MemoryRouter>{ui}</MemoryRouter>;

vi.mock("../../api/generated/dekopen", () => ({
  projectsList: vi.fn().mockResolvedValue({
    status: 200,
    data: {
      items: [
        { id: "project-a", code: "P-001", name: "Casa", client_name: "Cliente" },
        { id: "project-A", code: "P-A", name: "Casa A", client_name: "Cliente A" },
        { id: "project-B", code: "P-B", name: "Casa B", client_name: "Cliente B" },
      ],
    },
  }),
  projectsRetrieve: vi.fn().mockResolvedValue({
    status: 200,
    data: {
      id: "project-a",
      current_revision: "REV-A",
      positions: [
        {
          position_index: 1,
          location_tag: "Living",
          quantity: 2,
          design: {
            parametric_tree: { type: "BAY", opening_type: "FIXED" },
            nominal_width_mm: "1000",
            nominal_height_mm: "1000",
          },
        },
        { position_index: 2, location_tag: "Dormitorio", quantity: 1 },
      ],
    },
  }),
}));

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
    render(page(<PricingPage />));
    expect(screen.getByRole("alert")).toHaveTextContent(t("pricing.ownerOnly"));
    expect(apiMutator).not.toHaveBeenCalled();
  },
);

it("keeps the current request alive after StrictMode cleanup and aborts on tenant switch", async () => {
  const view = render(
    page(
      <StrictMode>
        <PricingPage />
      </StrictMode>,
    ),
  );
  await waitFor(() => expect(apiMutator).toHaveBeenCalledTimes(2));
  const previous = vi.mocked(apiMutator).mock.calls.at(-1)?.[1].signal;
  expect(previous?.aborted).toBe(false);
  identity.id = "tenant-b";
  view.rerender(
    page(
      <StrictMode>
        <PricingPage />
      </StrictMode>,
    ),
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

function deferred() {
  let resolve!: (value: unknown) => void;
  let reject!: (reason: Error) => void;
  const promise = new Promise<unknown>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}
async function settle(task: ReturnType<typeof deferred>, value: unknown, failure = false) {
  await act(async () => {
    if (failure) task.reject(new Error("controlled failure"));
    else task.resolve({ data: value });
  });
}

const costListRow = {
  id: "9f4e5a00-0000-4000-8000-000000000001",
  supplier_name: "Proveedor Fixture",
  description: "",
  currency: "CLP",
  valid_from: "2026-09-01",
  valid_to: null,
  is_active: true,
};

it.each([
  ["CLP", "1250", "$1.250"],
  ["USD", "12.5", "US$ 12,50"],
  [null, "12.5", "Sin dato: moneda de la autoridad"],
])("reads each cost in the currency of its authority (%s)", async (currency, value, expected) => {
  vi.mocked(apiMutator).mockImplementation((url) =>
    Promise.resolve({
      data: {
        items: String(url).endsWith("cost-items/")
          ? [{ id: "cost-row", sku: "SKU-MONEDA", cost_list_id: costListRow.id, unit_cost: value }]
          : [{ ...costListRow, currency }],
      },
    }),
  );
  render(page(<PricingPage />));
  const itemsTab = screen.getByRole("tab", { name: t("pricing.items") });
  await waitFor(() => expect(itemsTab).toBeEnabled());
  fireEvent.click(itemsTab);
  const cost = (await screen.findAllByText("SKU-MONEDA"))[0]!.closest("article")!;
  expect(within(cost).getByText(expected)).toBeInTheDocument();
});

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
    render(page(<PricingPage />));
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
  render(page(<PricingPage />));
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
    render(page(<PricingPage />));
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
  render(page(<PricingPage />));
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
    render(page(<PricingPage />));
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
    const view = render(page(<PricingPage />));
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
      page(
        <StrictMode>
          <PricingPage />
        </StrictMode>,
      ),
    );
    await fillImportForm();
    submitImport();
    await settle(previewTask, { items: [importRow("SKU-T")] });
    fireEvent.click(confirmImportButton()!);
    const signal = applyCalls()[0]?.[1]?.signal;
    identity.id = "tenant-b";
    view.rerender(
      page(
        <StrictMode>
          <PricingPage />
        </StrictMode>,
      ),
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
