import { create } from "zustand";
import type { AnnotationRequest, InspectorDiff } from "../../api/generated/models";
import { intentBays, type IntentNode } from "./intentEditing";
import type { ProductJson } from "./productEditing";

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
  color: "WHITE" | "FOILED";
  parametricTree: IntentNode;
  /** Compositional product (product-v2). null = classic single unit. */
  product: ProductJson | null;
};

const HISTORY_LIMIT = 100;

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
  annotations: AnnotationRequest[];
  previewDiff: InspectorDiff | null;
  setAnnotations(annotations: AnnotationRequest[]): void;
  setPreviewDiff(diff: InspectorDiff | null): void;
  inputs: CanvasDesignInputs;
  draftDimension: DraftDimension;
  selection: string;
  selectBay(id: string): void;
  loadDesign(inputs: CanvasDesignInputs): void;
  acceptIntent(expected: CanvasDesignInputs, next: CanvasDesignInputs, selection: string): boolean;
  /** Typed design commands: record history, then apply. */
  commitInputs(next: CanvasDesignInputs): void;
  past: CanvasDesignInputs[];
  future: CanvasDesignInputs[];
  undo(): void;
  redo(): void;
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
    product: null,
  };
}

const INITIAL_VIEWPORT: ViewportState = {
  scale: 1,
  offsetX: 0,
  offsetY: 0,
};

export const useCanvasStore = create<CanvasState>((set) => ({
  annotations: [],
  previewDiff: null,
  setAnnotations(annotations) {
    set({ annotations, previewDiff: null });
  },
  setPreviewDiff(previewDiff) {
    set({ previewDiff });
  },
  inputs: initialInputs(),
  draftDimension: null,
  selection: "g1",
  selectBay(id) {
    set((state) => {
      if (
        state.inputs.product !== null &&
        state.inputs.product.assembly.modules.some((m) => m.id === id)
      )
        return { selection: id };
      return intentBays(state.inputs.parametricTree).some((bay) => bay.id === id)
        ? { selection: id }
        : state;
    });
  },
  loadDesign(inputs) {
    set({
      inputs,
      selection:
        inputs.product !== null
          ? (inputs.product.assembly.modules[0]?.id ?? "")
          : (intentBays(inputs.parametricTree)[0]?.id ?? ""),
      annotations: [],
      previewDiff: null,
      draftDimension: null,
      viewport: INITIAL_VIEWPORT,
      past: [],
      future: [],
    });
  },
  acceptIntent(expected, next, selection) {
    let accepted = false;
    set((state) => {
      if (
        state.inputs !== expected ||
        !intentBays(next.parametricTree).some((bay) => bay.id === selection)
      )
        return state;
      accepted = true;
      return {
        inputs: next,
        selection,
        draftDimension: null,
        previewDiff: null,
        past: [...state.past.slice(-(HISTORY_LIMIT - 1)), state.inputs],
        future: [],
      };
    });
    return accepted;
  },
  commitInputs(next) {
    set((state) => ({
      inputs: next,
      past: [...state.past.slice(-(HISTORY_LIMIT - 1)), state.inputs],
      future: [],
      draftDimension: null,
      previewDiff: null,
    }));
  },
  past: [],
  future: [],
  undo() {
    set((state) => {
      const previous = state.past[state.past.length - 1];
      if (previous === undefined) return state;
      return {
        inputs: previous,
        past: state.past.slice(0, -1),
        future: [...state.future, state.inputs],
        draftDimension: null,
      };
    });
  },
  redo() {
    set((state) => {
      const next = state.future[state.future.length - 1];
      if (next === undefined) return state;
      return {
        inputs: next,
        past: [...state.past, state.inputs],
        future: state.future.slice(0, -1),
        draftDimension: null,
      };
    });
  },
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
      past: [...state.past.slice(-(HISTORY_LIMIT - 1)), state.inputs],
      future: [],
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
      annotations: [],
      previewDiff: null,
      inputs: initialInputs(),
      draftDimension: null,
      selection: "g1",
      viewport: INITIAL_VIEWPORT,
      snapEnabled: true,
      past: [],
      future: [],
    });
  },
}));
