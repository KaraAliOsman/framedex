import { beforeEach, describe, expect, it } from "vitest";
import { useCanvasStore } from "./canvasStore";
import {
  changeOpening,
  exactMm,
  intentBays,
  moveDivision,
  requestTree,
  singleBayTemplate,
  splitBay,
  type IntentNode,
  type SplitType,
} from "./intentEditing";
import { requestFromInputs } from "./useEngineCalculation";

const bay: IntentNode = {
  id: "bay-a",
  type: "BAY",
  opening_type: "FIXED",
  glass_thickness_mm: "24.00",
  glass_spec: "4-16-4",
  glass_article_sku: "GLASS-A",
};

function divided(type: SplitType = "SPLIT_V"): IntentNode {
  return splitBay(
    bay,
    bay.id,
    { type, offsetMm: "500,25", mullionSku: "CATALOG-MULLION" },
    { split: "split-a", secondBay: "bay-b" },
  );
}

beforeEach(() => useCanvasStore.getState().reset());

describe("rectangular intent", () => {
  it("moves only an existing division with the exact requested distance", () => {
    const tree = divided();
    const before = JSON.stringify(tree);
    const moved = moveDivision(tree, "split-a", "450,75");
    expect(moved.split_offset_mm).toBe("450.75");
    expect(moved.children).toEqual(tree.children);
    expect(moved.mullion_profile_sku).toBe(tree.mullion_profile_sku);
    expect(JSON.stringify(tree)).toBe(before);
    expect(() => moveDivision(tree, "bay-a", "100")).toThrow("division_unavailable");
    expect(() => moveDivision(tree, "split-a", "100.001")).toThrow("invalid_dimension");
  });
  it.each(["SPLIT_V", "SPLIT_H"] as const)(
    "copies the human centerline for %s without deriving child dimensions",
    (type) => {
      const source = JSON.stringify(bay);
      const tree = divided(type);

      expect(tree.type).toBe(type);
      expect(tree.split_offset_mm).toBe("500.25");
      expect(tree.mullion_profile_sku).toBe("CATALOG-MULLION");
      expect(intentBays(tree).map((node) => node.id)).toEqual(["bay-a", "bay-b"]);
      expect(
        intentBays(tree).every(
          (node) => node.width_mm === undefined && node.height_mm === undefined,
        ),
      ).toBe(true);
      expect(JSON.stringify(bay)).toBe(source);
    },
  );

  it("edits only the selected nested bay and preserves explicit materials", () => {
    const tree = divided();
    const changed = changeOpening(tree, "bay-b", "TILT_TURN_RIGHT");

    expect(changed.children?.[0]).toBe(tree.children?.[0]);
    expect(changed.children?.[1]).toMatchObject({
      id: "bay-b",
      opening_type: "TILT_TURN_RIGHT",
      glass_article_sku: "GLASS-A",
    });
    expect(tree.children?.[1]?.opening_type).toBe("FIXED");
  });

  it("preserves explicit hardware so engine can validate compatibility", () => {
    const source: IntentNode = {
      ...bay,
      opening_type: "TURN_LEFT",
      hardware_set_sku: "KIT-A",
    };
    expect(changeOpening(source, source.id, "TURN_RIGHT")).toMatchObject({
      hardware_set_sku: "KIT-A",
      opening_type: "TURN_RIGHT",
    });
  });

  it("permits a wrapped top-level door but rejects nested doors", () => {
    const root: IntentNode = { id: "root", type: "ROOT", children: [bay] };
    expect(changeOpening(root, bay.id, "DOOR_ENTRY").children?.[0]?.opening_type).toBe(
      "DOOR_ENTRY",
    );
    expect(() => changeOpening(divided(), "bay-b", "DOOR_ENTRY")).toThrow();
    expect(() =>
      splitBay(
        { ...bay, opening_type: "DOOR_ENTRY" },
        bay.id,
        { type: "SPLIT_V", offsetMm: "500", mullionSku: "POST" },
        { split: "split-a", secondBay: "bay-b" },
      ),
    ).toThrow();
  });

  it("replaces the layout only through an explicit single-bay template", () => {
    const result = singleBayTemplate(divided(), "bay-b", "AWNING");
    expect(result).toMatchObject({
      id: "bay-b",
      type: "BAY",
      opening_type: "AWNING",
      glass_article_sku: "GLASS-A",
    });
    expect(result.children).toBeUndefined();
  });

  it("does not silently round or accept invalid dimensions", () => {
    expect(exactMm("001200,25")).toBe("1200.25");
    for (const value of ["0", "-1", "1.005", "1e3", "NaN", "1.000,25"]) {
      expect(() => exactMm(value)).toThrow();
    }
  });

  it("rejects missing selection and colliding generated identities", () => {
    expect(() => changeOpening(bay, "missing", "FIXED")).toThrow();
    expect(() =>
      splitBay(
        bay,
        bay.id,
        { type: "SPLIT_H", offsetMm: "500", mullionSku: "POST" },
        { split: bay.id, secondBay: "new" },
      ),
    ).toThrow();
  });

  it("removes duplicate top-level dimensions without changing the input", () => {
    const root: IntentNode = {
      id: "root",
      type: "ROOT",
      width_mm: "1000.00",
      height_mm: "1000.00",
      children: [{ ...bay, width_mm: "1000.00", height_mm: "1000.00" }],
    };
    const normalized = requestTree(root);

    expect(normalized.width_mm).toBeUndefined();
    expect(normalized.children?.[0]?.width_mm).toBeUndefined();
    expect(root.width_mm).toBe("1000.00");
    expect(root.children?.[0]?.width_mm).toBe("1000.00");
  });

  it("retains the existing EngineCalculateRequest shape for position.design", () => {
    const inputs = {
      ...useCanvasStore.getState().inputs,
      systemId: "system-a",
      parametricTree: divided(),
    };
    expect(requestFromInputs(inputs)).toEqual({
      system_id: "system-a",
      nominal_width_mm: "1000.00",
      nominal_height_mm: "1000.00",
      color: "WHITE",
      parametric_tree: inputs.parametricTree,
    });
  });

  it("rejects a stale calculation after reset, even with identical values", () => {
    const base = useCanvasStore.getState().inputs;
    useCanvasStore.getState().reset();

    expect(
      useCanvasStore.getState().acceptIntent(base, { ...base, nominalWidthMm: "1200.00" }, "g1"),
    ).toBe(false);
    expect(useCanvasStore.getState().inputs.nominalWidthMm).toBe("1000.00");
  });
});
