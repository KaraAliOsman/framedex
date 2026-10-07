import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { mountingPreview, mountingRules } from "../../api/generated/dekopen";
import type { MountingPreviewResponse } from "../../api/generated/models";
import golden from "../../../../engine/tests/golden_mounting.json";
import { useCanvasStore } from "../canvas/canvasStore";
import { wrapTreeAsProduct } from "../canvas/productEditing";
import type { MountingEvidence } from "./mountingModel";
import { MountingInspector } from "./MountingInspector";

vi.mock("../../api/generated/dekopen", () => ({
  mountingPreview: vi.fn(),
  mountingRules: vi.fn(),
}));
vi.mock("../../auth/AuthSessionProvider", () => ({
  useAuthSession: () => ({ me: { active_organization: { id: "org-a" } } }),
}));

const evidence = {
  ...golden.IN_OPENING,
  survey: { ...golden.IN_OPENING.survey, module_id: "m1", independent_extras: [] },
} as MountingEvidence;
const initial = wrapTreeAsProduct(
  { id: "g1", type: "BAY", opening_type: "FIXED", glass_article_sku: "GLASS-BASE" },
  "1500",
  "1200",
);
const result = {
  status: 200 as const,
  headers: new Headers(),
  data: {
    design: {
      system_id: "series-a",
      color: "WHITE",
      nominal_width_mm: "1500",
      nominal_height_mm: "1200",
      parametric_tree: initial,
    },
    measurements: [evidence],
  } as MountingPreviewResponse,
};

function Harness() {
  const product = useCanvasStore((store) => store.inputs.product)!;
  return (
    <MountingInspector
      product={product}
      module={product.assembly.modules[0]!}
      busy={false}
      onChanged={vi.fn()}
    />
  );
}
function mount() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <MemoryRouter>
      <QueryClientProvider client={client}>
        <Harness />
      </QueryClientProvider>
    </MemoryRouter>,
  );
}
function changeGlazing() {
  const store = useCanvasStore.getState();
  const product = store.inputs.product!;
  const next = {
    ...product,
    assembly: {
      ...product.assembly,
      modules: product.assembly.modules.map((module) => ({
        ...module,
        tree: { ...module.tree, glass_article_sku: "NEW-GLASS" },
      })),
    },
  };
  act(() => store.commitInputs({ ...store.inputs, product: next }));
  return next;
}
beforeEach(() => {
  vi.clearAllMocks();
  useCanvasStore.getState().reset();
  const store = useCanvasStore.getState();
  store.loadDesign({
    ...store.inputs,
    systemId: "series-a",
    product: initial,
    mounting: [evidence],
  });
  vi.mocked(mountingRules).mockResolvedValue({
    status: 200,
    headers: new Headers(),
    data: { items: [{ revision: 1, rule: golden.IN_OPENING.rule }] },
  });
});
afterEach(cleanup);

it("rejects a delayed preview after a newer glazing edit without replacing it", async () => {
  let finish!: (value: typeof result) => void;
  vi.mocked(mountingPreview).mockImplementation(
    () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  );
  mount();
  fireEvent.click(await screen.findByRole("button", { name: "Calcular fabricación" }));
  await waitFor(() => expect(mountingPreview).toHaveBeenCalledOnce());
  const changed = changeGlazing();
  await act(async () => {
    finish(result);
  });
  expect(screen.queryByRole("button", { name: "Aplicar fabricación" })).not.toBeInTheDocument();
  expect(screen.getByRole("alert")).toHaveTextContent("El diseño cambió");
  expect(useCanvasStore.getState().inputs.product).toEqual(changed);
});

it("invalidates a ready proposal when the design changes before Apply", async () => {
  vi.mocked(mountingPreview).mockResolvedValue(result);
  mount();
  fireEvent.click(await screen.findByRole("button", { name: "Calcular fabricación" }));
  await screen.findByRole("button", { name: "Aplicar fabricación" });
  const changed = changeGlazing();
  expect(screen.queryByRole("button", { name: "Aplicar fabricación" })).not.toBeInTheDocument();
  expect(useCanvasStore.getState().inputs.product).toEqual(changed);
});

it("discards a pending preview when the user opts into a newer rule", async () => {
  let finish!: (value: typeof result) => void;
  vi.mocked(mountingRules).mockResolvedValue({
    status: 200,
    headers: new Headers(),
    data: { items: [{ revision: 2, rule: golden.IN_OPENING.rule }] },
  });
  vi.mocked(mountingPreview).mockImplementation(
    () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  );
  mount();
  await screen.findByRole("button", { name: "Usar regla actual" });
  fireEvent.click(screen.getByRole("button", { name: "Calcular fabricación" }));
  await waitFor(() => expect(mountingPreview).toHaveBeenCalledOnce());
  fireEvent.click(screen.getByRole("button", { name: "Usar regla actual" }));
  await act(async () => {
    finish(result);
  });
  expect(screen.queryByRole("button", { name: "Aplicar fabricación" })).not.toBeInTheDocument();
  expect(useCanvasStore.getState().inputs.mounting).toEqual([evidence]);
  expect(screen.getByRole("button", { name: "Calcular fabricación" })).toBeEnabled();
});
