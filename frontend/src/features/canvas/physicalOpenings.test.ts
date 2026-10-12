import { describe, expect, it } from "vitest";
import { choiceMatches, choicePatch, type OpeningChoice } from "./physicalOpenings";
import {
  applyBaySpec,
  changeOpening,
  intentBays,
  singleBayTemplate,
  type IntentNode,
} from "./intentEditing";

const choice: OpeningChoice = {
  id: "turn-right-outward",
  label: "Abatible hacia afuera — bisagras a la derecha",
  use: "WINDOW",
  source: "Ficha sintética de ensayo",
  opening: {
    movement: "TURN",
    hinge_side: "RIGHT",
    direction: "OUTWARD",
    leaf_role: "SINGLE",
    fixed_in_sash: false,
  },
};
const physical: IntentNode = { id: "physical", type: "BAY", ...choicePatch(choice) };

describe("physical opening identity across serialization and edits", () => {
  it("marks a reopened choice regardless of JSON key order and distinguishes direction/use", () => {
    const reopened = {
      ...physical,
      opening: {
        fixed_in_sash: false,
        leaf_role: "SINGLE",
        direction: "OUTWARD",
        hinge_side: "RIGHT",
        movement: "TURN",
      },
    } as IntentNode;
    expect(choiceMatches(reopened, choice)).toBe(true);
    expect(choiceMatches({ ...reopened, opening_use: "DOOR" }, choice)).toBe(false);
    expect(
      choiceMatches({ ...reopened, opening: { ...choice.opening, direction: "INWARD" } }, choice),
    ).toBe(false);
  });
  it("keeps a recipient's physical opening when copying only glass and hardware", () => {
    const source: IntentNode = {
      id: "source",
      type: "BAY",
      opening_type: "FIXED",
      glass_article_sku: "SOURCE-GLASS",
    };
    const tree: IntentNode = {
      id: "split",
      type: "SPLIT_V",
      split_offset_mm: "500",
      mullion_profile_sku: "MULLION",
      children: [source, physical],
    };
    const target = intentBays(applyBaySpec(tree, "source", "physical"))[1]!;
    expect(target.opening).toEqual(choice.opening);
    expect(target.opening_use).toBe("WINDOW");
    expect(target.glass_article_sku).toBe("SOURCE-GLASS");
  });
  it("clears the physical contract on an explicit legacy template replacement", () => {
    const target = singleBayTemplate(physical, physical.id, "FIXED");
    expect(target.opening_type).toBe("FIXED");
    expect(target.opening).toBeNull();
    expect(target.hinged_layout).toBeNull();
    expect(changeOpening(physical, physical.id, "TURN_LEFT").opening).toBeNull();
  });
});
