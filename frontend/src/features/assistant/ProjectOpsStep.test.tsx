import { fireEvent, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, expect, it, vi } from "vitest";

import { ApiError } from "../../api/apiMutator";
import {
  projectOperationsApply,
  projectOperationsPreview,
  projectOperationsState,
  projectOperationsUndo,
} from "../../api/generated/dekopen";
import { ProjectOpsStep } from "./ProjectOpsStep";

vi.mock("../../api/generated/dekopen", () => ({
  projectOperationsApply: vi.fn(),
  projectOperationsPreview: vi.fn(),
  projectOperationsState: vi.fn(),
  projectOperationsUndo: vi.fn(),
  projectDesignOptions: vi.fn(),
}));
const preview = {
  project_id: "project",
  before_sig: "before",
  valid: true,
  ops: [{ op: "set_quantity" as const, position_id: "position", quantity: 3 }],
  positions: [],
  simulations: [],
  diff: [
    {
      kind: "change",
      index: 1,
      before: { id: "position", position_index: 1, quantity: 1, location_tag: "Cocina" },
      after: { id: "position", position_index: 1, quantity: 3, location_tag: "Cocina" },
    },
  ],
};
function response(data: unknown) {
  return { status: 200, headers: new Headers(), data } as never;
}
function show() {
  const onSettled = vi.fn();
  render(
    <QueryClientProvider client={new QueryClient()}>
      <ProjectOpsStep
        step={{
          kind: "project_ops",
          label: "Cantidad propuesta",
          ops: preview.ops,
          simulation: preview,
        }}
        organizationId="organization"
        projectId="project"
        operationKey="ai:job:1:0"
        onSettled={onSettled}
      />
    </QueryClientProvider>,
  );
  return onSettled;
}
beforeEach(() => {
  vi.resetAllMocks();
});

it("restores applied edits read-only and can undo using their durable identity", async () => {
  vi.mocked(projectOperationsState).mockResolvedValue(
    response({ operation_id: "operation", state: "APPLIED" }),
  );
  vi.mocked(projectOperationsUndo).mockResolvedValue(
    response({ operation_id: "operation", state: "UNDONE", project: {} }),
  );
  const settled = show();
  fireEvent.click(await screen.findByRole("button", { name: "Deshacer cambios" }));
  expect(await screen.findByText("Cambios deshechos")).toBeTruthy();
  expect(projectOperationsUndo).toHaveBeenCalledWith("project", "operation", expect.anything());
  expect(projectOperationsApply).not.toHaveBeenCalled();
  expect(settled).not.toHaveBeenCalled();
});

it("keeps an undone edit settled after reopening", async () => {
  vi.mocked(projectOperationsState).mockResolvedValue(
    response({ operation_id: "operation", state: "UNDONE" }),
  );
  show();
  expect(await screen.findByText("Cambios deshechos")).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Aplicar cambios al proyecto" })).toBeNull();
  expect(projectOperationsApply).not.toHaveBeenCalled();
});

it("retries a stale proposal with a fresh server simulation and the same idempotency key", async () => {
  vi.mocked(projectOperationsState).mockResolvedValue(
    response({ operation_id: null, state: "PROPOSED" }),
  );
  vi.mocked(projectOperationsApply)
    .mockRejectedValueOnce(
      new ApiError(409, {
        error: { detail: "El proyecto cambió. Vuelve a simular la propuesta." },
      }),
    )
    .mockResolvedValueOnce(response({ operation_id: "operation", state: "APPLIED", project: {} }));
  vi.mocked(projectOperationsPreview).mockResolvedValue(
    response({ ...preview, before_sig: "fresh" }),
  );
  show();
  fireEvent.click(await screen.findByRole("button", { name: "Aplicar cambios al proyecto" }));
  fireEvent.click(await screen.findByRole("button", { name: "Reintentar simulación" }));
  const apply = await screen.findByRole("button", { name: "Aplicar cambios al proyecto" });
  await vi.waitFor(() => expect(apply).not.toBeDisabled());
  fireEvent.click(apply);
  expect(await screen.findByText("Cambios aplicados")).toBeTruthy();
  expect(projectOperationsApply).toHaveBeenLastCalledWith(
    "project",
    expect.objectContaining({ before_sig: "fresh", operation_key: "ai:job:1:0" }),
    expect.anything(),
  );
});

it("explains the required role without offering an apply action after permission loss", async () => {
  vi.mocked(projectOperationsState).mockRejectedValue(new ApiError(403, { error: {} }));
  show();
  expect(await screen.findByRole("alert")).toHaveTextContent("Solo el dueño o un estimador");
  expect(screen.getByRole("button", { name: "Aplicar cambios al proyecto" })).toBeDisabled();
  expect(projectOperationsApply).not.toHaveBeenCalled();
});
