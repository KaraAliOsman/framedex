import type { TranslationKey } from "../../i18n/es-CL";
import type { IntentNode, Opening } from "./intentEditing";
import {
  makeArchModule,
  makeBowProduct,
  makeTrapezoidModule,
  totalModuleWidth,
  wrapTreeAsProduct,
  type ProductJson,
} from "./productEditing";

function starterTree(opening: Opening): IntentNode {
  return { id: crypto.randomUUID(), type: "BAY", opening_type: opening };
}

export interface StarterDefinition {
  key: string;
  titleKey: TranslationKey;
  hintKey: TranslationKey;
  build(widthMm: number, heightMm: number): ProductJson;
}

/** Coupled pair of two independent bays joined by a coupler. */
function coupledModules(
  first: IntentNode,
  second: IntentNode,
  firstShare: number,
  widthMm: number,
  heightMm: number,
): ProductJson {
  return {
    version: "product-v2",
    assembly: {
      modules: [
        {
          id: crypto.randomUUID(),
          width_mm: (widthMm * firstShare).toFixed(2),
          height_mm: heightMm.toFixed(2),
          tree: first,
        },
        {
          id: crypto.randomUUID(),
          width_mm: (widthMm * (1 - firstShare)).toFixed(2),
          height_mm: heightMm.toFixed(2),
          tree: second,
        },
      ],
      couplings: [{ id: crypto.randomUUID(), angle_deg: "0.0", coupler_profile_sku: null }],
    },
  };
}

function splitBay(
  direction: "SPLIT_V" | "SPLIT_H",
  children: IntentNode[],
  widthMm: number,
  heightMm: number,
): ProductJson {
  return wrapTreeAsProduct(
    {
      id: crypto.randomUUID(),
      type: direction,
      split_offset_mm: (direction === "SPLIT_V" ? widthMm / 2 : heightMm / 2).toFixed(2),
      mullion_profile_sku: null,
      children,
    },
    widthMm.toFixed(2),
    heightMm.toFixed(2),
  );
}

/** Design library: creation recipes that produce a compositional product.
 * They are not product types — everything they build is editable on canvas. */
export const STARTER_DEFINITIONS: StarterDefinition[] = [
  {
    key: "fixed",
    titleKey: "assembly.starter.fixed",
    hintKey: "assembly.starter.fixedHint",
    build: (w, h) => wrapTreeAsProduct(starterTree("FIXED"), w.toFixed(2), h.toFixed(2)),
  },
  {
    key: "sash",
    titleKey: "assembly.starter.sash",
    hintKey: "assembly.starter.sashHint",
    build: (w, h) => wrapTreeAsProduct(starterTree("TILT_TURN_LEFT"), w.toFixed(2), h.toFixed(2)),
  },
  {
    key: "twoSash",
    titleKey: "assembly.starter.twoSash",
    hintKey: "assembly.starter.twoSashHint",
    build: (w, h) =>
      splitBay("SPLIT_V", [starterTree("TILT_TURN_LEFT"), starterTree("TILT_TURN_RIGHT")], w, h),
  },
  {
    key: "sliding2",
    titleKey: "assembly.starter.sliding2",
    hintKey: "assembly.starter.sliding2Hint",
    build: (w, h) => wrapTreeAsProduct(starterTree("SLIDING_2L"), w.toFixed(2), h.toFixed(2)),
  },
  {
    key: "sliding3",
    titleKey: "assembly.starter.sliding3",
    hintKey: "assembly.starter.sliding3Hint",
    build: (w, h) => wrapTreeAsProduct(starterTree("SLIDING_3L"), w.toFixed(2), h.toFixed(2)),
  },
  {
    key: "awning",
    titleKey: "assembly.starter.awning",
    hintKey: "assembly.starter.awningHint",
    build: (w, h) => wrapTreeAsProduct(starterTree("AWNING"), w.toFixed(2), h.toFixed(2)),
  },
  {
    key: "awningBand",
    titleKey: "assembly.starter.awningBand",
    hintKey: "assembly.starter.awningBandHint",
    build: (w, h) => splitBay("SPLIT_H", [starterTree("FIXED"), starterTree("AWNING")], w, h),
  },
  {
    key: "coupled",
    titleKey: "assembly.starter.coupled",
    hintKey: "assembly.starter.coupledHint",
    build: (w, h) => coupledModules(starterTree("TILT_TURN_LEFT"), starterTree("FIXED"), 0.5, w, h),
  },
  {
    key: "doorSide",
    titleKey: "assembly.starter.doorSide",
    hintKey: "assembly.starter.doorSideHint",
    build: (w, h) => coupledModules(starterTree("DOOR_ENTRY"), starterTree("FIXED"), 0.4, w, h),
  },
  {
    key: "slidingFixed",
    titleKey: "assembly.starter.slidingFixed",
    hintKey: "assembly.starter.slidingFixedHint",
    build: (w, h) => coupledModules(starterTree("SLIDING_2L"), starterTree("FIXED"), 0.55, w, h),
  },
  {
    key: "bow3",
    titleKey: "assembly.starter.bow3",
    hintKey: "assembly.starter.bow3Hint",
    build: (w, h) => makeBowProduct({ moduleCount: 3, widthMm: w, heightMm: h, angleDeg: 15 }),
  },
  {
    key: "bow5",
    titleKey: "assembly.starter.bow5",
    hintKey: "assembly.starter.bow5Hint",
    build: (w, h) => makeBowProduct({ moduleCount: 5, widthMm: w, heightMm: h, angleDeg: 15 }),
  },
  {
    key: "trapezoid",
    titleKey: "assembly.starter.trapezoid",
    hintKey: "assembly.starter.trapezoidHint",
    build: (w, h) => ({
      version: "product-v2" as const,
      assembly: {
        modules: [
          makeTrapezoidModule(
            "m1",
            w.toFixed(2),
            h.toFixed(2),
            Math.round(w * 0.15),
            Math.round(w * 0.15),
            starterTree("FIXED"),
          ),
        ],
        couplings: [],
      },
    }),
  },
  {
    key: "arch",
    titleKey: "assembly.starter.arch",
    hintKey: "assembly.starter.archHint",
    build: (w, h) => ({
      version: "product-v2" as const,
      assembly: {
        modules: [
          makeArchModule(
            "m1",
            w.toFixed(2),
            h.toFixed(2),
            Math.round(w * 0.2),
            starterTree("FIXED"),
          ),
        ],
        couplings: [],
      },
    }),
  },
];

export type StarterKey = (typeof STARTER_DEFINITIONS)[number]["key"];

/** Nominal canvas the library cards preview at — templates render their own
 * proportions (bow reads wider, door reads taller). */
export function starterNominalSize(key: string): { widthMm: number; heightMm: number } {
  switch (key) {
    case "bow3":
      return { widthMm: 2400, heightMm: 1400 };
    case "bow5":
      return { widthMm: 3000, heightMm: 1400 };
    case "doorSide":
      return { widthMm: 1600, heightMm: 2200 };
    case "trapezoid":
      return { widthMm: 2400, heightMm: 1400 };
    case "arch":
      return { widthMm: 1800, heightMm: 1600 };
    case "sliding2":
    case "slidingFixed":
      return { widthMm: 1800, heightMm: 1400 };
    case "sliding3":
      return { widthMm: 2400, heightMm: 1400 };
    case "awning":
    case "awningBand":
      return { widthMm: 1200, heightMm: 800 };
    case "twoSash":
      return { widthMm: 1400, heightMm: 1400 };
    default:
      return { widthMm: 1200, heightMm: 1400 };
  }
}

/** Size a new build inherits from whatever is already on canvas. */
export function starterContextSize(current: ProductJson | null): {
  widthMm: number;
  heightMm: number;
} {
  return {
    widthMm: current ? totalModuleWidth(current) : 1500,
    heightMm: current
      ? Math.max(...current.assembly.modules.map((module) => Number(module.height_mm)))
      : 1200,
  };
}
