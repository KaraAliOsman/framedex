import { describe, expect, it } from "vitest";

import {
  alreadyJoined,
  canLink,
  chainEnd,
  connectedComponents,
  incidentCouplings,
  linkModules,
  moveModule,
  resolveCouplings,
  unlinkCoupling,
  usedEdges,
  wouldCloseCycle,
} from "./assemblyGraph";
import {
  addAdjacentUnit,
  duplicateModule,
  insertModuleBetween,
  makeBowProduct,
  makeTrapezoidModule,
  removeUnit,
  setAllCouplingAngles,
  setModuleCount,
  setModuleFrameless,
  wrapTreeAsProduct,
  type CouplingJson,
  type ProductJson,
} from "./productEditing";

function bow(modules = 3): ProductJson {
  return makeBowProduct({ moduleCount: modules, widthMm: 2100, heightMm: 1400, angleDeg: 15 });
}

/** Explicit coupling shorthand for fixture products. */
function link(
  id: string,
  modules: [string, string],
  edges: ["left" | "right" | "top" | "bottom", "left" | "right" | "top" | "bottom"],
  kind: NonNullable<CouplingJson["kind"]> = "INLINE",
  angleDeg = "0.0",
): CouplingJson {
  return { id, angle_deg: angleDeg, coupler_profile_sku: null, kind, modules, edges };
}

/** A transom stacked over a door — one column, two members. */
function stackedPair(): ProductJson {
  const base = bow(1);
  const door = base.assembly.modules[0]!;
  const transom = { ...door, id: "t1", height_mm: "400.00" };
  return {
    ...base,
    assembly: {
      modules: [door, transom],
      couplings: [link("c1", ["m1", "t1"], ["top", "bottom"], "STACKED")],
    },
  };
}

/** Two columns, each carrying one stacked member. */
function doubleStacked(): ProductJson {
  const base = bow(2);
  const [a, b] = base.assembly.modules;
  const ta = { ...a!, id: "ta", height_mm: "400.00" };
  const tb = { ...b!, id: "tb", height_mm: "400.00" };
  return {
    ...base,
    assembly: {
      modules: [a!, b!, ta, tb],
      couplings: [
        link("ca", ["m1", "m2"], ["right", "left"], "INLINE", "15.0"),
        link("cs", ["m1", "ta"], ["top", "bottom"], "STACKED"),
        link("cs2", ["m2", "tb"], ["top", "bottom"], "STACKED"),
      ],
    },
  };
}

/** L-shape: two columns meeting at a 90° corner joint. */
function cornerProduct(): ProductJson {
  const base = bow(2);
  return {
    ...base,
    assembly: {
      modules: [...base.assembly.modules],
      couplings: [link("c1", ["m1", "m2"], ["top", "top"], "CORNER", "90.0")],
    },
  };
}

/** T junction: m2 hangs on m1's top edge; m3 continues m1's right. */
function teeProduct(): ProductJson {
  const base = bow(3);
  return {
    ...base,
    assembly: {
      modules: [...base.assembly.modules],
      couplings: [
        link("c1", ["m1", "m3"], ["right", "left"], "INLINE", "10.0"),
        link("c2", ["m1", "m2"], ["top", "bottom"], "TEE"),
      ],
    },
  };
}

describe("resolveCouplings", () => {
  it("resolves positional couplings through the legacy i→i+1 binding", () => {
    const resolved = resolveCouplings(bow());
    expect(resolved.map(({ pair }) => pair)).toEqual([
      ["m1", "m2"],
      ["m2", "m3"],
    ]);
    expect(resolved.map(({ edges }) => edges)).toEqual([
      ["right", "left"],
      ["right", "left"],
    ]);
    expect(resolved.every(({ kind }) => kind === "INLINE")).toBe(true);
  });

  it("resolves explicit pairs by stable id — never by position", () => {
    const resolved = resolveCouplings(stackedPair());
    expect(resolved[0]!.pair).toEqual(["m1", "t1"]);
    expect(resolved[0]!.kind).toBe("STACKED");
    expect(resolved[0]!.edges).toEqual(["top", "bottom"]);
  });
});

describe("incidentCouplings / usedEdges / chainEnd", () => {
  it("reports every incident connection on the tee node", () => {
    const incident = incidentCouplings(teeProduct(), "m1");
    expect(incident.map(({ coupling }) => coupling.id)).toEqual(["c1", "c2"]);
    expect(usedEdges(teeProduct(), "m1")).toEqual(new Set(["right", "top"]));
  });

  it("finds the right chain end by free edge, not declaration position", () => {
    expect(chainEnd(bow(), "right")!.id).toBe("m3");
    expect(chainEnd(bow(), "left")!.id).toBe("m1");
    // m3's right edge is free even though m3 is not the declaration end
    expect(chainEnd(teeProduct(), "right")!.id).toBe("m3");
  });
});

describe("connectedComponents / cycle detection", () => {
  it("sees one component for a linked assembly", () => {
    expect(connectedComponents(bow())).toEqual([["m1", "m2", "m3"]]);
    expect(connectedComponents(stackedPair())).toEqual([["m1", "t1"]]);
  });

  it("reports a free member as its own component — the engine's disconnected case", () => {
    const base = bow(3);
    const loose = {
      ...base,
      assembly: {
        ...base.assembly,
        couplings: [link("c1", ["m1", "m2"], ["right", "left"], "INLINE", "10.0")],
      },
    };
    const components = connectedComponents(loose);
    expect(components).toHaveLength(2);
    expect(components).toContainEqual(["m3"]);
  });

  it("refuses links that would close a ring", () => {
    const product = bow();
    expect(wouldCloseCycle(product, "m1", "m3")).toBe(true);
    expect(canLink(product, "m1", "top", "m3", "top", "STACKED")).toBe(false);
    expect(linkModules(product, "m1", "top", "m3", "top", "STACKED")).toBe(product);
  });
});

describe("removeUnit", () => {
  it("resolves an L/corner joint by its declared kind and edges", () => {
    const resolved = resolveCouplings(cornerProduct());
    expect(resolved[0]!.kind).toBe("CORNER");
    expect(resolved[0]!.pair).toEqual(["m1", "m2"]);
    expect(resolved[0]!.edges).toEqual(["top", "top"]);
  });

  it("severing a corner member drops its joint without healing", () => {
    const removed = removeUnit(cornerProduct(), "m2");
    expect(removed.assembly.modules.map((m) => m.id)).toEqual(["m1"]);
    expect(removed.assembly.couplings).toHaveLength(0);
  });

  it("drops every incident connection — never leaves a dangling endpoint", () => {
    const product = teeProduct();
    const removed = removeUnit(product, "m1");
    expect(removed.assembly.modules.map((m) => m.id)).toEqual(["m2", "m3"]);
    // Both of m1's couplings are gone; nothing references m1 anymore.
    expect(removed.assembly.couplings).toHaveLength(0);
    expect(resolveCouplings(removed).flatMap(({ pair }) => [...pair])).not.toContain("m1");
  });

  it("heals only the INLINE bridge — merged deflection keeps the far heading", () => {
    const removed = removeUnit(setAllCouplingAngles(bow(), "10.0"), "m2");
    expect(removed.assembly.modules.map((m) => m.id)).toEqual(["m1", "m3"]);
    expect(removed.assembly.couplings).toEqual([
      {
        id: "c1",
        angle_deg: "20.0",
        coupler_profile_sku: null,
        kind: "INLINE",
        modules: ["m1", "m3"],
        edges: ["right", "left"],
      },
    ]);
  });

  it("removing a stacked root detaches its member — no invented re-attach", () => {
    const removed = removeUnit(stackedPair(), "m1");
    expect(removed.assembly.modules.map((m) => m.id)).toEqual(["t1"]);
    expect(removed.assembly.couplings).toHaveLength(0);
    // t1 is now a free-standing module: disconnected, visible, not silently fixed.
    expect(connectedComponents(removed)).toEqual([["t1"]]);
  });

  it("removing a stacked member leaves the column connected", () => {
    const product = doubleStacked();
    const removed = removeUnit(product, "tb");
    expect(removed.assembly.modules.map((m) => m.id)).toEqual(["m1", "m2", "ta"]);
    expect(removed.assembly.couplings.map((c) => c.id)).toEqual(["ca", "cs"]);
    expect(connectedComponents(removed)).toEqual([["m1", "m2", "ta"]]);
  });

  it("does not heal through shaped or glass-only survivors", () => {
    // m1–m2–m3 chain where m1 is a trapezoid: deleting m2 must not invent a
    // joint touching a contour edge — that coupling has no physical seam.
    const trapezoid = makeTrapezoidModule("m1", "700.00", "1400.00", 100, 100, {
      id: "g1",
      type: "BAY",
      opening_type: "FIXED",
    });
    const product: ProductJson = {
      ...bow(),
      assembly: {
        modules: [trapezoid, ...bow().assembly.modules.slice(1)],
        couplings: [
          link("c1", ["m1", "m2"], ["right", "left"], "INLINE", "10.0"),
          link("c2", ["m2", "m3"], ["right", "left"], "INLINE", "10.0"),
        ],
      },
    };
    const removed = removeUnit(product, "m2");
    expect(removed.assembly.couplings).toHaveLength(0);
    expect(connectedComponents(removed)).toHaveLength(2);
  });
});

describe("insertModuleBetween", () => {
  it("splits the joint and halves the deflection across both replacements", () => {
    const inserted = insertModuleBetween(setAllCouplingAngles(bow(), "10.0"), "c1");
    expect(inserted.assembly.modules.map((m) => m.id)).toEqual(["m1", "m4", "m2", "m3"]);
    const pairs = resolveCouplings(inserted).map(({ pair }) => pair);
    expect(pairs).toEqual([
      ["m1", "m4"],
      ["m4", "m2"],
      ["m2", "m3"],
    ]);
    const angles = inserted.assembly.couplings.map((c) => c.angle_deg);
    expect(angles).toEqual(["5.0", "5.0", "10.0"]);
  });

  it("refuses to open a stacked junction", () => {
    const product = stackedPair();
    expect(insertModuleBetween(product, "c1")).toBe(product);
  });
});

describe("duplicateModule", () => {
  it("clones onto the free right edge with a coplanar explicit joint", () => {
    const duplicated = duplicateModule(bow(), "m3");
    expect(duplicated.assembly.modules.map((m) => m.id)).toEqual(["m1", "m2", "m3", "m4"]);
    expect(duplicated.assembly.couplings.at(-1)).toEqual({
      id: "c3",
      angle_deg: "0.0",
      coupler_profile_sku: null,
      kind: "INLINE",
      modules: ["m3", "m4"],
      edges: ["right", "left"],
    });
  });

  it("attaches left when only the left edge is free", () => {
    const duplicated = duplicateModule(bow(), "m1");
    expect(duplicated.assembly.modules.map((m) => m.id)).toEqual(["m4", "m1", "m2", "m3"]);
    expect(duplicated.assembly.couplings.at(-1)!.modules).toEqual(["m4", "m1"]);
  });

  it("refuses when both side edges are taken", () => {
    const product = bow();
    expect(duplicateModule(product, "m2")).toBe(product);
  });
});

describe("addAdjacentUnit", () => {
  it("creates an explicit intended relationship at the resolved chain end", () => {
    const grown = addAdjacentUnit(bow(), "right");
    expect(grown.assembly.couplings.at(-1)).toEqual({
      id: "c3",
      angle_deg: "15.0",
      coupler_profile_sku: null,
      kind: "INLINE",
      modules: ["m3", "m4"],
      edges: ["right", "left"],
    });
  });

  it("appends at the column root even when the declaration tail is stacked", () => {
    // m2 is the front-chain end — tb hangs on it. Growing right must join
    // the column's root (full height), not the transom's free side edge.
    const grown = addAdjacentUnit(doubleStacked(), "right");
    expect(grown.assembly.couplings.at(-1)!.modules).toEqual(["m2", "m5"]);
    expect(grown.assembly.couplings.at(-1)!.kind).toBe("INLINE");
  });
});

describe("setModuleCount", () => {
  it("shrink heals couplings instead of slicing endpoints", () => {
    const product = doubleStacked();
    const shrunk = setModuleCount(product, 3);
    // declaration tail tb is removed; m2 loses its stacked member but stays joined.
    expect(shrunk.assembly.modules.map((m) => m.id)).toEqual(["m1", "m2", "ta"]);
    expect(shrunk.assembly.couplings.map((c) => c.id)).toEqual(["ca", "cs"]);
  });

  it("grows with explicit couplings", () => {
    const grown = setModuleCount(bow(), 5);
    expect(grown.assembly.couplings.at(-1)!.modules).toEqual(["m4", "m5"]);
  });
});

describe("moveModule", () => {
  it("reorders declaration without touching the resolved explicit graph", () => {
    const product = teeProduct();
    const moved = moveModule(product, "m2", 0);
    expect(moved.assembly.modules.map((m) => m.id)).toEqual(["m2", "m1", "m3"]);
    expect(resolveCouplings(moved).map(({ pair }) => pair)).toEqual([
      ["m1", "m3"],
      ["m1", "m2"],
    ]);
    expect(connectedComponents(moved)).toEqual([["m2", "m1", "m3"]]);
  });
});

describe("unlinkCoupling", () => {
  it("severs one joint and keeps every member", () => {
    const unlinked = unlinkCoupling(bow(), "c2");
    expect(unlinked.assembly.modules).toHaveLength(3);
    expect(connectedComponents(unlinked)).toEqual([["m1", "m2"], ["m3"]]);
  });
});

describe("canLink — mixed restrictions", () => {
  it("refuses occupied edges, same-module links and wrong-kind edges", () => {
    const product = bow();
    expect(canLink(product, "m1", "right", "m3", "left", "INLINE")).toBe(false);
    expect(canLink(product, "m1", "left", "m1", "right", "INLINE")).toBe(false);
    expect(canLink(product, "m1", "top", "m2", "bottom", "INLINE")).toBe(false);
    expect(canLink(product, "m1", "left", "m2", "top", "STACKED")).toBe(false);
    expect(alreadyJoined(product, "m1", "m2")).toBe(true);
  });

  it("accepts a stacked joint between free top/bottom edges across components", () => {
    // m3 is a free member; stacking it over m1 joins two components.
    const base = bow(3);
    const product: ProductJson = {
      ...base,
      assembly: {
        ...base.assembly,
        couplings: [link("c1", ["m1", "m2"], ["right", "left"], "INLINE", "10.0")],
      },
    };
    expect(canLink(product, "m1", "top", "m3", "bottom", "STACKED")).toBe(true);
    const linked = linkModules(product, "m1", "top", "m3", "bottom", "STACKED");
    expect(linked.assembly.couplings.at(-1)).toEqual({
      id: "c2",
      angle_deg: "0.0",
      coupler_profile_sku: null,
      kind: "STACKED",
      modules: ["m1", "m3"],
      edges: ["top", "bottom"],
    });
    expect(connectedComponents(linked)).toEqual([["m1", "m2", "m3"]]);
  });

  it("refuses contour endpoints — a shaped edge has no straight seam", () => {
    const trapezoid = makeTrapezoidModule("t1", "700.00", "1400.00", 100, 100, {
      id: "g1",
      type: "BAY",
      opening_type: "FIXED",
    });
    const product: ProductJson = {
      version: "product-v2",
      assembly: {
        modules: [trapezoid, bow().assembly.modules[0]!],
        couplings: [],
      },
    };
    expect(canLink(product, "t1", "right", "m1", "left", "INLINE")).toBe(false);
  });

  it("refuses frameless endpoints — a bare pane has nothing to join", () => {
    const pane = setModuleFrameless(
      wrapTreeAsProduct(
        { id: "g1", type: "BAY", opening_type: "FIXED", glass_spec: "4" },
        "1200.00",
        "2100.00",
      ),
      "m1",
      {
        supports: [{ kind: "CHANNEL", edge: "bottom", article_sku: "UCH", qty: 1 }],
        fittings: [],
      },
    );
    const product: ProductJson = {
      ...pane,
      assembly: {
        modules: [...pane.assembly.modules, bow().assembly.modules[1]!],
        couplings: [],
      },
    };
    expect(canLink(product, "m1", "right", "m2", "left", "INLINE")).toBe(false);
  });
});

describe("mutations are pure — snapshot undo stays sound", () => {
  it("removeUnit returns a new product and leaves the original untouched", () => {
    const product = bow();
    const snapshot = JSON.parse(JSON.stringify(product));
    const removed = removeUnit(product, "m2");
    expect(removed).not.toBe(product);
    expect(product).toEqual(snapshot);
    // Re-committing the snapshot restores the exact prior graph.
    expect(resolveCouplings(product).map(({ pair }) => pair)).toEqual([
      ["m1", "m2"],
      ["m2", "m3"],
    ]);
  });
});
