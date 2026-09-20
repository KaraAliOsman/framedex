import { renderHook, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { engineLayout } from "../../api/generated/dekopen";
import { useCanvasStore } from "./canvasStore";
import { useEngineLayout } from "./useEngineLayout";

vi.mock("../../api/generated/dekopen", () => ({ engineLayout: vi.fn() }));

it("hides the previous organization's layout while new authority is unresolved", async () => {
  useCanvasStore.getState().setSystemId("shared-system");
  const inputs = useCanvasStore.getState().inputs;
  const node = {
    node_id: "bay",
    width_mm: "1200",
    height_mm: "1000",
    child_weights: [],
    vertical: { half: "600", one_third: "400", two_thirds: "800" },
    horizontal: { half: "500", one_third: "333.33", two_thirds: "666.67" },
  };
  vi.mocked(engineLayout)
    .mockResolvedValueOnce({
      status: 200,
      headers: new Headers(),
      data: {
        calculation_hash: `sha256:${"0".repeat(64)}`,
        nodes: [node],
      },
    })
    .mockImplementationOnce(() => new Promise(() => {}));
  const { result, rerender } = renderHook(({ org }) => useEngineLayout(inputs, org), {
    initialProps: { org: "org-a" },
  });
  await waitFor(() => expect(result.current).toEqual([node]));
  rerender({ org: "org-b" });
  expect(result.current).toEqual([]);
});
