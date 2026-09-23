import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import {
  engineSystems,
  projectDesignOptions,
  projectImportConfirm,
  projectImportsList,
} from "../../api/generated/dekopen";
import { t } from "../../i18n/es-CL";
import { ProjectImportsPanel } from "./ProjectImportsPanel";

vi.mock("../../api/generated/dekopen", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../api/generated/dekopen")>();
  return {
    ...actual,
    engineSystems: vi.fn(),
    projectDesignOptions: vi.fn(),
    projectImportsList: vi.fn(),
    projectImportsCreate: vi.fn(),
    projectImportConfirm: vi.fn(),
  };
});

const IMPORT = {
  id: "imp-1",
  file_name: "cotizacion-providencia.pdf",
  kind: "PDF",
  status: "REVIEW_READY",
  candidates: [
    {
      key: "r1",
      label: "V-101",
      width_mm: "1200",
      height_mm: "1100",
      quantity: 2,
      opening_type: "TURN_RIGHT",
      confidence: "HIGH",
      warnings: [],
      source_text: "V-101 1200x1100",
    },
    {
      key: "r2",
      label: null,
      width_mm: "800",
      height_mm: "600",
      quantity: 1,
      opening_type: null,
      confidence: "REVIEW_REQUIRED",
      warnings: ["fila_ambigua"],
      source_text: "800 x 600 ???",
    },
  ],
  warnings: [],
  result: [],
  error_code: null,
  created_at: "2026-09-20T10:00:00Z",
  updated_at: "2026-09-20T10:00:05Z",
};

function renderPanel() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ProjectImportsPanel projectId="p-1" orgId="org-a" canWrite={true} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.mocked(projectImportsList).mockResolvedValue({
    status: 200,
    data: { imports: [IMPORT] },
  } as never);
  vi.mocked(engineSystems).mockResolvedValue({
    status: 200,
    data: { systems: [{ id: "sys-1", code: "DEMO_60", name: "Demo 60" }] },
  } as never);
  vi.mocked(projectDesignOptions).mockResolvedValue({
    status: 200,
    data: {
      glass_skus: ["4-12-4 Float Incoloro"],
      glass_specs: [{ sku: "4-12-4 Float Incoloro", spec: "4-12-4" }],
      glazing_thicknesses: ["20.00"],
    },
  } as never);
  vi.mocked(projectImportConfirm).mockResolvedValue({
    status: 200,
    data: {
      import: { ...IMPORT, status: "CONFIRMED" },
      created: [{ position_id: "pos-1", key: "r1", label: "V-101" }],
      errors: [],
    },
  } as never);
});

afterEach(() => {
  cleanup();
});

it("expands to list imports and confirms marked candidates into positions", async () => {
  renderPanel();
  expect(vi.mocked(projectImportsList)).not.toHaveBeenCalled();

  fireEvent.click(screen.getByRole("button", { name: t("projects.importsTitle") }));
  await screen.findByText("cotizacion-providencia.pdf");
  expect(vi.mocked(projectImportsList)).toHaveBeenCalledTimes(1);
  expect(screen.getByText(t("projects.importsStatusReviewReady"))).toBeTruthy();

  fireEvent.click(screen.getByRole("button", { name: t("projects.importsReview") }));
  await screen.findByText(t("projects.importsConfirm"));

  // HIGH confidence is pre-checked; REVIEW_REQUIRED stays unchecked.
  const checks = screen.getAllByRole("checkbox");
  expect(checks).toHaveLength(2);

  // Wait for the system + glass picks to resolve before confirming.
  await waitFor(() => expect(screen.getByDisplayValue("Demo 60")).toBeTruthy());

  fireEvent.click(screen.getByRole("button", { name: t("projects.importsConfirm") }));
  await waitFor(() => expect(vi.mocked(projectImportConfirm)).toHaveBeenCalledTimes(1));
  const call = vi.mocked(projectImportConfirm).mock.calls[0]!;
  const items = (call[2] as { items: { key: string }[] }).items;
  expect(items).toHaveLength(1);
  expect(items[0]).toMatchObject({
    key: "r1",
    system_id: "sys-1",
    glass_article_sku: "4-12-4 Float Incoloro",
  });
  // No glass_spec on the wire — the purchase mapping resolves it server-side.
  expect(items[0]).not.toHaveProperty("glass_spec");
  await screen.findByText(t("projects.importsConfirmed").replace("{count}", "1"));
});
