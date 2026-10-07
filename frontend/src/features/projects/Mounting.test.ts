import { beforeEach, expect, it } from "vitest";
import golden from "../../../../engine/tests/golden_mounting.json";
import { useCanvasStore } from "../canvas/canvasStore";
import { wrapTreeAsProduct } from "../canvas/productEditing";
import { mountingGeometryChanged, type MountingEvidence } from "./mountingModel";

const evidence: MountingEvidence = {
  ...golden.IN_OPENING,
  survey: { ...golden.IN_OPENING.survey, module_id: "m1" },
} as MountingEvidence;

beforeEach(() => useCanvasStore.getState().reset());

it("blocks changed fabrication while preserving exact equivalent decimals", () => {
  const product = wrapTreeAsProduct(
    { id: "g1", type: "BAY", opening_type: "FIXED" },
    "1500.00",
    "1200.00",
  );
  expect(mountingGeometryChanged(product, [evidence])).toBe(false);
  expect(
    mountingGeometryChanged(
      {
        ...product,
        assembly: {
          ...product.assembly,
          modules: product.assembly.modules.map((m) => ({ ...m, width_mm: "1500.01" })),
        },
      },
      [evidence],
    ),
  ).toBe(true);
});

it("removes gone-frame evidence atomically and restores it through undo", () => {
  const product = wrapTreeAsProduct(
    { id: "g1", type: "BAY", opening_type: "FIXED" },
    "1500",
    "1200",
  );
  const store = useCanvasStore.getState();
  store.loadDesign({ ...store.inputs, systemId: "series-a", product, mounting: [evidence] });
  store.commitInputs({
    ...useCanvasStore.getState().inputs,
    product: {
      ...product,
      assembly: {
        ...product.assembly,
        modules: [{ ...product.assembly.modules[0]!, id: "replacement" }],
      },
    },
  });
  expect(useCanvasStore.getState().inputs.mounting).toEqual([]);
  store.undo();
  expect(useCanvasStore.getState().inputs.mounting).toEqual([evidence]);
  store.redo();
  expect(useCanvasStore.getState().inputs.mounting).toEqual([]);
});

it("requires a new series mounting authority after changing the system", () => {
  const store = useCanvasStore.getState();
  store.loadDesign({ ...store.inputs, systemId: "series-a", mounting: [evidence] });
  store.setSystemId("series-a");
  expect(useCanvasStore.getState().inputs.mounting).toEqual([evidence]);
  store.setSystemId("series-b");
  expect(useCanvasStore.getState().inputs.mounting).toEqual([]);
});

it("records independent accessory edits with the same undo transaction as the product", () => {
  const product = wrapTreeAsProduct(
    {
      id: "g1",
      type: "BAY",
      opening_type: "FIXED",
      extras: [{ code: "FRAME_EXTENSION", sides: ["LEFT"] }],
    },
    "1500",
    "1200",
  );
  const attributed = { ...evidence, survey: { ...evidence.survey, independent_extras: [] } };
  const store = useCanvasStore.getState();
  store.loadDesign({ ...store.inputs, product, mounting: [attributed] });
  store.commitInputs({
    ...useCanvasStore.getState().inputs,
    product: {
      ...product,
      assembly: {
        ...product.assembly,
        modules: product.assembly.modules.map((module) => ({
          ...module,
          tree: { ...module.tree, extras: [...module.tree.extras!, { code: "SCREEN_FIXED" }] },
        })),
      },
    },
  });
  expect(useCanvasStore.getState().inputs.mounting?.[0]?.survey.independent_extras).toEqual([
    { code: "SCREEN_FIXED" },
  ]);
  store.undo();
  expect(useCanvasStore.getState().inputs.mounting?.[0]?.survey.independent_extras).toEqual([]);
  store.redo();
  expect(useCanvasStore.getState().inputs.mounting?.[0]?.survey.independent_extras).toEqual([
    { code: "SCREEN_FIXED" },
  ]);
});
