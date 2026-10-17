import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ConfirmProvider } from "../../ui/ConfirmDialog";
import * as api from "../../api/generated/dekopen";
import { CatalogImportsPanel } from "./CatalogImportsPanel";

vi.mock("../../api/generated/dekopen", () => ({
  catalogImportsList: vi.fn(),
  catalogTemplateSchema: vi.fn(),
  catalogImportsCreate: vi.fn(),
  catalogImportReview: vi.fn(),
  catalogImportPublish: vi.fn(),
  catalogImportUndo: vi.fn(),
  catalogImportTimeline: vi.fn(),
}));
const entry = {
  id: "import-1",
  file_name: "ficha.pdf",
  kind: "PDF",
  status: "REVIEW_READY",
  system_id: null,
  candidates: [
    {
      key: "ai0",
      sheet: "Sistemas",
      row: 1,
      method: "AI",
      confidence: "LOW",
      values: { system_code: "SERIE", depth_mm: null },
      fields: {
        system_code: { ref: "Página 1", quote: "Serie SERIE", confidence: "HIGH" },
        depth_mm: { ref: "Página 1", quote: "Tabla borrosa", confidence: "LOW", proposed: "60" },
      },
      errors: [],
    },
  ],
  warnings: [],
  result: [],
  error_code: null,
  created_at: "2026-10-05T12:00:00Z",
  updated_at: "2026-10-05T12:00:00Z",
};
async function openReview() {
  render(
    <ConfirmProvider>
      <CatalogImportsPanel orgId="org" systems={[]} canWrite onConfirmed={() => {}} />
    </ConfirmProvider>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Importar catálogo" }));
  fireEvent.click(await screen.findByRole("button", { name: "Revisar fuente y cambios" }));
  await screen.findByText("Fuente del proveedor");
}
describe("CatalogImportsPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.catalogImportTimeline).mockResolvedValue({
      status: 200,
      data: { items: [] },
    } as never);
    vi.mocked(api.catalogImportsList).mockResolvedValue({
      status: 200,
      data: { imports: [entry] },
    } as never);
    vi.mocked(api.catalogTemplateSchema).mockResolvedValue({
      status: 200,
      data: {
        version: 1,
        sheets: [
          {
            name: "Sistemas",
            columns: [
              { key: "system_code", label: "Código de serie", kind: "text", required: true },
              { key: "depth_mm", label: "Profundidad", kind: "positive", required: true },
            ],
          },
        ],
      },
    } as never);
    vi.mocked(api.catalogImportReview).mockResolvedValue({
      status: 200,
      data: {
        review_token: "sha256:review",
        errors: [],
        changes: [
          {
            key: "ai0",
            sheet: "Sistemas",
            action: "create",
            before: null,
            after: { depth_mm: "60.00" },
          },
        ],
      },
    } as never);
    vi.mocked(api.catalogImportPublish).mockResolvedValue({
      status: 200,
      data: { import: { ...entry, status: "CONFIRMED" }, created: [{ row_id: "new" }], errors: [] },
    } as never);
  });
  it("keeps uncertain readings empty and requires a diff plus human review before publication", async () => {
    await openReview();
    expect(screen.getByLabelText(/^Profundidad/)).toHaveValue("");
    expect(screen.getByText("Tabla borrosa")).toBeVisible();
    expect(screen.getByText(/Lectura dudosa: 60/)).toBeVisible();
    expect(api.catalogImportPublish).not.toHaveBeenCalled();
    expect(screen.getByLabelText("Incluir fila 1")).not.toBeChecked();
    expect(screen.getByRole("button", { name: "Comparar cambios" })).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/^Profundidad/), { target: { value: "60.00" } });
    fireEvent.click(screen.getByLabelText("Incluir fila 1"));
    fireEvent.click(screen.getByRole("button", { name: "Comparar cambios" }));
    const publish = await screen.findByRole("button", { name: "Publicar catálogo revisado" });
    expect(publish).toBeDisabled();
    fireEvent.click(screen.getByLabelText(/Revisé la fuente/));
    fireEvent.click(publish);
    await waitFor(() => expect(api.catalogImportPublish).toHaveBeenCalledTimes(1));
    expect(vi.mocked(api.catalogImportPublish).mock.calls[0]?.[1]).toMatchObject({
      review_token: "sha256:review",
      reviewed: true,
      items: [{ key: "ai0", values: { depth_mm: "60.00" } }],
    });
  });
  it("invalidates the reviewed diff when a field changes", async () => {
    await openReview();
    fireEvent.click(screen.getByLabelText("Incluir fila 1"));
    fireEvent.click(screen.getByRole("button", { name: "Comparar cambios" }));
    await screen.findByRole("button", { name: "Publicar catálogo revisado" });
    fireEvent.click(screen.getByLabelText(/Revisé la fuente/));
    fireEvent.change(screen.getByLabelText(/^Profundidad/), { target: { value: "70.00" } });
    expect(
      screen.queryByRole("button", { name: "Publicar catálogo revisado" }),
    ).not.toBeInTheDocument();
    expect(api.catalogImportPublish).not.toHaveBeenCalled();
  });
});
