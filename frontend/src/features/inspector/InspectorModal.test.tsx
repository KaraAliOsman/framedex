import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { engineCalculate, engineInspect, engineOptimizeCut } from "../../api/generated/dekopen";
import type {
  AnnotationRequest,
  EngineInspectResponse,
  InspectorDiff,
} from "../../api/generated/models";
import { useCanvasStore } from "../canvas/canvasStore";
import { InspectorModal } from "./InspectorModal";
import { previewDrainDraft, workshopReadiness } from "./inspectorDraft";

vi.mock("../../api/generated/dekopen", () => ({
  engineCalculate: vi.fn(),
  engineInspect: vi.fn(),
  engineOptimizeCut: vi.fn(),
}));
const hash = `sha256:${"a".repeat(64)}`;
const target = { bay_id: "g1", leaf_id: null };
const original: AnnotationRequest[] = [
  {
    ...target,
    bottom_drain_holes_mm: ["100", "900"],
    continuous_width_mm: "1000",
    finish_class: "WHITE",
    has_coupler: false,
  },
];
const diff: InspectorDiff = {
  diff_id: "synthetic-r07",
  rule_id: "R07",
  target,
  preconditions: { opening_width_mm: "1000.00", bottom_drain_holes_mm: ["100.00", "900.00"] },
  operations: [
    {
      kind: "ADD_BOTTOM_DRAIN_HOLE",
      target,
      old_value: ["100", "900"],
      new_value: ["100", "500", "900"],
    },
  ],
};
function inspection(fixed: boolean, red = false): EngineInspectResponse {
  return {
    status: red ? "RED" : fixed ? "GREEN" : "YELLOW",
    production_allowed: !red,
    source_calculation_hash: hash,
    evaluations: [],
    findings: fixed
      ? []
      : [
          {
            rule_id: "R07",
            severity: "YELLOW",
            title: "Falta un desagüe",
            diagnosis: "Dos posiciones declaradas",
            risk: "Acumulación de agua",
            recommendation: "Añadir el centro",
            fixability: "AUTO_FIXABLE",
            ...target,
            fix: diff,
          },
        ],
  };
}
function mount(): QueryClient {
  const cache = new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: Infinity } },
  });
  render(
    <QueryClientProvider client={cache}>
      <InspectorModal
        open
        onClose={vi.fn()}
        organizationId="org"
        inputs={useCanvasStore.getState().inputs}
        calculationHash={hash}
      />
    </QueryClientProvider>,
  );
  return cache;
}
async function preview(): Promise<void> {
  fireEvent.click(await screen.findByRole("button", { name: "Ver corrección propuesta" }));
  expect(screen.getByText("Antes: 100, 900 mm")).toBeVisible();
  expect(screen.getByText("Después: 100, 500, 900 mm")).toBeVisible();
  expect(useCanvasStore.getState().annotations).toEqual(original);
  expect(engineCalculate).not.toHaveBeenCalled();
}
beforeEach(() => {
  vi.resetAllMocks();
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", {
    configurable: true,
    value() {
      this.setAttribute("open", "");
    },
  });
  Object.defineProperty(HTMLDialogElement.prototype, "close", {
    configurable: true,
    value() {
      this.removeAttribute("open");
    },
  });
  useCanvasStore.getState().reset();
  useCanvasStore.getState().setSystemId("system");
  useCanvasStore.getState().setAnnotations(structuredClone(original));
  vi.mocked(engineInspect).mockImplementation(async (request) => ({
    status: 200,
    headers: new Headers(),
    data: inspection(request.annotations?.[0]?.bottom_drain_holes_mm?.length === 3),
  }));
  vi.mocked(engineOptimizeCut).mockResolvedValue({
    status: 200,
    headers: new Headers(),
    data: { source_calculation_hash: hash, purchase_list: [], workshop_cut_plan: [] },
  });
  vi.mocked(engineCalculate).mockResolvedValue({
    status: 200,
    headers: new Headers(),
    data: {
      calculation_hash: hash,
      profile_cuts: [],
      reinforcements: [],
      glasses: [],
      panels: [],
      hardware_items: [],
      leaf_weights: [],
    },
  });
});
describe("SHOT-07 transactional modal", () => {
  it("previews without mutation, applies calculate then inspect, commits once and recomputes green", async () => {
    mount();
    await preview();
    fireEvent.click(screen.getByRole("button", { name: "Aplicar corrección" }));
    await screen.findByText("VERDE · Sin infracciones");
    expect(useCanvasStore.getState().annotations[0]?.bottom_drain_holes_mm).toEqual([
      "100",
      "500",
      "900",
    ]);
    expect(useCanvasStore.getState().previewDiff).toBeNull();
    expect(engineCalculate).toHaveBeenCalledTimes(1);
    expect(vi.mocked(engineCalculate).mock.invocationCallOrder[0]).toBeLessThan(
      vi.mocked(engineInspect).mock.invocationCallOrder[1] ?? 0,
    );
    expect(screen.queryByRole("button", { name: "Aplicar corrección" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Aprobar para Taller" })).toBeEnabled();
  });
  it.each(["RED", "YELLOW", "GREEN"] as const)(
    "recomputes RED to %s from the new response",
    async (status) => {
      vi.mocked(engineInspect).mockImplementation(async (request) => ({
        status: 200,
        headers: new Headers(),
        data:
          request.annotations?.[0]?.bottom_drain_holes_mm?.length === 3
            ? { ...inspection(true), status, production_allowed: status !== "RED" }
            : inspection(false, true),
      }));
      mount();
      await preview();
      fireEvent.click(screen.getByRole("button", { name: "Aplicar corrección" }));
      await waitFor(() => expect(useCanvasStore.getState().previewDiff).toBeNull());
      expect(document.querySelector(".inspector-semaphore")).toHaveAttribute("data-status", status);
      expect(
        screen.getByRole("button", { name: "Aprobar para Taller" }).hasAttribute("disabled"),
      ).toBe(status === "RED");
    },
  );
  it.each(["calculate", "inspect"])(
    "rolls back every local field on %s failure",
    async (failure) => {
      mount();
      await preview();
      const before = structuredClone({
        inputs: useCanvasStore.getState().inputs,
        annotations: useCanvasStore.getState().annotations,
        preview: useCanvasStore.getState().previewDiff,
      });
      if (failure === "calculate")
        vi.mocked(engineCalculate).mockRejectedValueOnce(new Error("traceback internal"));
      else vi.mocked(engineInspect).mockRejectedValueOnce(new Error("SELECT secret"));
      fireEvent.click(screen.getByRole("button", { name: "Aplicar corrección" }));
      expect(await screen.findByRole("alert")).toHaveTextContent("El diseño anterior se conserva");
      expect(screen.getByRole("alert")).not.toHaveTextContent(/traceback|SELECT/);
      expect(screen.getByRole("button", { name: "Aprobar para Taller" })).toBeDisabled();
      expect({
        inputs: useCanvasStore.getState().inputs,
        annotations: useCanvasStore.getState().annotations,
        preview: useCanvasStore.getState().previewDiff,
      }).toEqual(before);
    },
  );
  it("rejects a response after the design changes and keeps approval disabled during requests", async () => {
    let release!: () => void;
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    const normal = vi.mocked(engineCalculate).getMockImplementation()!;
    vi.mocked(engineCalculate).mockImplementation(async (...args) => {
      await gate;
      return normal(...args);
    });
    mount();
    await preview();
    fireEvent.click(screen.getByRole("button", { name: "Aplicar corrección" }));
    expect(screen.getByRole("button", { name: "Aprobar para Taller" })).toBeDisabled();
    act(() => useCanvasStore.getState().acceptDimension("width", "1100.00"));
    await act(async () => {
      release();
      await gate;
    });
    await screen.findByRole("alert");
    expect(useCanvasStore.getState().annotations).toEqual(original);
    expect(useCanvasStore.getState().inputs.nominalWidthMm).toBe("1100.00");
  });
  it("does not approve a GREEN inspector when BFD fails", async () => {
    vi.mocked(engineInspect).mockResolvedValue({
      status: 200,
      headers: new Headers(),
      data: inspection(true),
    });
    vi.mocked(engineOptimizeCut).mockRejectedValue(new Error("missing stock"));
    mount();
    await screen.findByText("VERDE · Sin infracciones");
    expect(screen.getByRole("button", { name: "Aprobar para Taller" })).toBeDisabled();
  });
});
describe("typed drain draft", () => {
  it("accepts equivalent decimal strings without changing the original", () => {
    expect(previewDrainDraft(original, diff, "01000.000")[0]?.bottom_drain_holes_mm).toEqual([
      "100",
      "500",
      "900",
    ]);
    expect(original[0]?.bottom_drain_holes_mm).toEqual(["100", "900"]);
  });
  it("rejects repeated application, stale width, different target and duplicate coordinates", () => {
    const applied = previewDrainDraft(original, diff, "1000");
    expect(() => previewDrainDraft(applied, diff, "1000")).toThrow();
    expect(() => previewDrainDraft(original, diff, "1000.01")).toThrow();
    expect(() => previewDrainDraft([], diff, "1000")).toThrow();
    const duplicate = structuredClone(diff);
    duplicate.operations[0]!.new_value = ["100", "900", "900.00"];
    expect(() => previewDrainDraft(original, duplicate, "1000")).toThrow();
  });
  it.each([
    [undefined, true, true],
    [true, false, true],
    [true, true, false],
    [false, true, true],
  ])("fails closed for missing or stale readiness %s/%s/%s", (allowed, optimized, current) => {
    expect(workshopReadiness(allowed, optimized, current)).toBe(false);
  });
});
