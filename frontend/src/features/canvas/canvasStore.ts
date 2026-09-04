import { create } from "zustand";

export type DimensionAxis = "width" | "height";

export type FixedParametricTree = {
  id: "g1";
  type: "BAY";
  opening_type: "FIXED";
  glass_thickness_mm: "4.00";
  glass_spec: "4 Float Incoloro";
};

export type CanvasDesignInputs = {
  systemId: string | null;
  nominalWidthMm: string;
  nominalHeightMm: string;
  color: "WHITE";
  parametricTree: FixedParametricTree;
};

type DraftDimension = {
  axis: DimensionAxis;
  value: string;
} | null;

type ViewportState = {
  scale: number;
  offsetX: number;
  offsetY: number;
};

type CanvasState = {
  inputs: CanvasDesignInputs;
  draftDimension: DraftDimension;
  selection: "g1";
  viewport: ViewportState;
  snapEnabled: boolean;
  setSystemId(systemId: string): void;
  setDraftDimension(draft: DraftDimension): void;
  acceptDimension(axis: DimensionAxis, value: string): void;
  setViewport(viewport: ViewportState): void;
  toggleSnap(): void;
  reset(): void;
};

const G1_TREE: FixedParametricTree = Object.freeze({
  id: "g1",
  type: "BAY",
  opening_type: "FIXED",
  glass_thickness_mm: "4.00",
  glass_spec: "4 Float Incoloro",
});

function initialInputs(): CanvasDesignInputs {
  return {
    systemId: null,
    nominalWidthMm: "1000.00",
    nominalHeightMm: "1000.00",
    color: "WHITE",
    parametricTree: G1_TREE,
  };
}

const INITIAL_VIEWPORT: ViewportState = {
  scale: 1,
  offsetX: 0,
  offsetY: 0,
};

export const useCanvasStore = create<CanvasState>((set) => ({
  inputs: initialInputs(),
  draftDimension: null,
  selection: "g1",
  viewport: INITIAL_VIEWPORT,
  snapEnabled: true,
  setSystemId(systemId) {
    set((state) => ({ inputs: { ...state.inputs, systemId } }));
  },
  setDraftDimension(draftDimension) {
    set({ draftDimension });
  },
  acceptDimension(axis, value) {
    set((state) => ({
      inputs: {
        ...state.inputs,
        ...(axis === "width" ? { nominalWidthMm: value } : { nominalHeightMm: value }),
      },
      draftDimension: null,
    }));
  },
  setViewport(viewport) {
    set({ viewport });
  },
  toggleSnap() {
    set((state) => ({ snapEnabled: !state.snapEnabled }));
  },
  reset() {
    set({
      inputs: initialInputs(),
      draftDimension: null,
      selection: "g1",
      viewport: INITIAL_VIEWPORT,
      snapEnabled: true,
    });
  },
}));
