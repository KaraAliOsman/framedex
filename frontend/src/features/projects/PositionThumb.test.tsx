import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import cases from "../../../../engine/tests/fixtures/symbols/cases.json";
import type { PositionDesign } from "../../api/generated/models";
import type { OpeningLeafFact } from "../canvas/physicalOpenings";
import { PositionThumb, THUMB_MEMBERS } from "./PositionThumb";

describe("sealed portal elevation", () => {
  for (const namespaced of [true, false]) {
    it(`renders sealed opening and handle with ${namespaced ? "module" : "legacy"} bay address`, () => {
      const fixture = cases.find((entry) => entry.name === "Abatible izquierda-interior")!;
      const design: PositionDesign = {
        system_id: "",
        nominal_width_mm: "1200",
        nominal_height_mm: "1400",
        color: "WHITE",
        parametric_tree: fixture.product,
      };
      const leaf = {
        ...fixture.leaves[0],
        bay_id: namespaced ? "m1|b1" : "b1",
        leaf_id: null,
        use: "WINDOW",
        source: "Revisión emitida",
        handle: { ...fixture.leaves[0]!.handle, source: "Revisión emitida" },
      } as OpeningLeafFact;
      const { container, rerender } = render(
        <PositionThumb design={design} openingLeaves={[leaf]} />,
      );
      const symbol = container.querySelector('[data-hinge="LEFT"] [data-symbol="turn"]')!;
      expect(symbol).not.toBeNull();
      expect(symbol.hasAttribute("stroke-dasharray")).toBe(false);
      expect(container.querySelector(".handle-lever")).not.toBeNull();
      rerender(
        <PositionThumb
          design={design}
          openingLeaves={[leaf]}
          members={{ ...THUMB_MEMBERS, viewFace: "exterior" }}
        />,
      );
      expect(
        container
          .querySelector('[data-hinge="LEFT"] [data-symbol="turn"]')!
          .hasAttribute("stroke-dasharray"),
      ).toBe(true);
      expect(container.querySelector('g[transform*="scale(-1"]')).not.toBeNull();
    });
  }
});
