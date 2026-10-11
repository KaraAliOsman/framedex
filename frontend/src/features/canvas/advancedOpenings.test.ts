import { describe, expect, it } from "vitest";
import type { DesignOptions } from "../../api/generated/models";
import symbols from "../../../../engine/tests/fixtures/symbols/advanced.json";
import { catalogStarters } from "./designLibrary";
import { applyBaySpec, changeOpening, requestTree, splitBay } from "./intentEditing";
import {
  choiceMatches,
  choicePatch,
  openingChoices,
  type Capability,
  type PhysicalOpening,
} from "./physicalOpenings";

describe("catalog-only advanced design library", () => {
  for (const fixture of symbols.filter((item) => item.view === "interior")) {
    it(fixture.name, () => {
      const leaf = fixture.leaves.find((item) => item.advanced.kind === "MOVING")!;
      const recipe = {
        code: leaf.advanced.recipe_code,
        name: leaf.advanced.recipe_name,
        scheme: leaf.advanced.scheme,
        source: leaf.advanced.source,
        synthetic: true,
        starter_width_mm: fixture.total_width_mm,
        starter_height_mm: "2200",
      };
      const cap: Capability = {
        ...(leaf.opening as PhysicalOpening),
        use: leaf.use as "DOOR" | "WINDOW",
        hinge_sides: ["NONE"],
        hardware_kit_skus: ["TEST-KIT"],
        source: "Test source",
        handle_rule: null,
        advanced_recipes: [recipe],
      };
      const options = { opening_capabilities: [cap] } as unknown as DesignOptions;
      const choices = openingChoices(options);
      expect(choices).toHaveLength(1);
      const choice = choices[0]!;
      const node = { id: "b", type: "BAY" as const, ...choicePatch(choice) };
      expect(choiceMatches(node, choice)).toBe(true);
      expect(choicePatch(choice).sliding_layout).toBeNull();
      expect(catalogStarters(options)).toHaveLength(1);
      expect(
        catalogStarters({
          ...options,
          opening_capabilities: [{ ...cap, advanced_recipes: [] }],
        } as unknown as DesignOptions),
      ).toEqual([]);
      expect(catalogStarters()).toEqual([]);
      expect(requestTree(node).opening_recipe_code).toBe(recipe.code);
      const pasted = applyBaySpec(
        {
          id: "pair",
          type: "SPLIT_V",
          split_offset_mm: "800",
          children: [node, { id: "target", type: "BAY" }],
        },
        "b",
        "target",
      );
      expect(pasted.children?.[1]?.id).toBe("target");
      expect(pasted.children?.[1]?.opening_recipe_code).toBe(recipe.code);
      const split = splitBay(
        node,
        "b",
        { type: "SPLIT_V", offsetMm: "800", mullionSku: "POSTE" },
        { split: "s", secondBay: "b2" },
      );
      expect(split.children?.map((item) => item.opening_recipe_code)).toEqual([
        recipe.code,
        recipe.code,
      ]);
      expect(split.children?.map((item) => item.opening?.hinge_side)).toEqual(["NONE", "NONE"]);
      expect(changeOpening(node, "b", "FIXED").opening_recipe_code).toBeNull();
    });
  }
});
