import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { projectsList, projectsRetrieve } from "../../api/generated/dekopen";
import { apiFetchBlob } from "../../api/apiMutator";
import { DocumentPreview } from "./AdminSections";

vi.mock("../../api/generated/dekopen", async (original) => ({
  ...(await original<object>()),
  projectsList: vi.fn(),
  projectsRetrieve: vi.fn(),
}));
vi.mock("../../api/apiMutator", async (original) => ({
  ...(await original<object>()),
  apiFetchBlob: vi.fn(),
}));

const legacy = {
  id: "historical",
  revision_code: "REV-A",
  authority_version: "LEGACY",
  snapshot_sha256: "a".repeat(64),
};
beforeEach(() => {
  vi.mocked(projectsList).mockResolvedValue({
    status: 200,
    data: { items: [{ id: "project", code: "P-000001", name: "Obra", status: "QUOTED" }] },
  } as never);
  vi.mocked(apiFetchBlob).mockResolvedValue({ blob: new Blob(["%PDF-fixture"]) } as never);
  vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:reviewed-reference");
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.clearAllMocks();
});
function show(versions: unknown[]) {
  vi.mocked(projectsRetrieve).mockResolvedValue({ status: 200, data: { versions } } as never);
  render(
    <MemoryRouter>
      <QueryClientProvider
        client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
      >
        <DocumentPreview orgId="organization" branding={{}} />
      </QueryClientProvider>
    </MemoryRouter>,
  );
}
test("an old hashed revision explains its limit without sending an unsupported PDF request", async () => {
  show([legacy]);
  expect(await screen.findByText(/Esta revisión histórica no tiene la trazabilidad/)).toBeVisible();
  expect(apiFetchBlob).not.toHaveBeenCalled();
  expect(screen.getByRole("link", { name: "Abrir cotización de la obra" })).toHaveAttribute(
    "href",
    "/projects/project?section=quote",
  );
});
test("a supported sealed revision is selected ahead of the historical reference", async () => {
  show([
    legacy,
    { ...legacy, id: "supported", revision_code: "REV-B", authority_version: "SHOT10_V1" },
  ]);
  await waitFor(() => expect(screen.getByTitle("PDF real de referencia")).toBeVisible());
  expect(screen.getByLabelText("Revisión de referencia")).toHaveValue("supported");
  expect(apiFetchBlob).toHaveBeenCalledWith(
    expect.any(String),
    expect.objectContaining({ body: JSON.stringify({ version_id: "supported", branding: {} }) }),
  );
});
