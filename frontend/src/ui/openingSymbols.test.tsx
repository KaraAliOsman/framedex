import { render } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import cases from "../../../engine/tests/fixtures/symbols/cases.json";
import type { PhysicalOpening } from "../features/canvas/physicalOpenings";
import { OpeningSymbol } from "./OpeningSymbol";
import { openingSymbolLines } from "./openingSymbols";

describe("shared Python/TS DIN fixtures", () => {
  for (const fixture of cases)
    it(fixture.name, () => {
      const view = fixture.view as "interior" | "exterior";
      fixture.leaves.forEach((leaf, index) => {
        const opening = leaf.opening as PhysicalOpening;
        const rect = {
          x: Number(leaf.x_mm),
          y: Number(leaf.y_mm),
          width: Number(leaf.width_mm),
          height: Number(leaf.height_mm),
        };
        const travel = leaf.travel as "LEFT" | "RIGHT" | null;
        const lines = openingSymbolLines(opening, rect, view, travel, false);
        expect(
          lines.map((line) => ({
            ...line,
            points: line.points.map(([x, y]) => [view === "exterior" ? 1200 - x : x, y]),
          })),
        ).toEqual(
          fixture.expected[index]!.lines.map((line) => ({
            ...line,
            points: line.points.map((point) => point.map(Number)),
          })),
        );
        const { container, unmount } = render(
          <svg>
            <OpeningSymbol opening={opening} {...rect} view={view} mirror={false} travel={travel} />
          </svg>,
        );
        const paths = Array.from(container.querySelectorAll("path"));
        expect(paths).toHaveLength(lines.length);
        paths.forEach((path, at) => {
          const numbers = path
            .getAttribute("d")!
            .match(/-?\d+(?:\.\d+)?/g)!
            .map(Number);
          expect(numbers).toEqual(lines[at]!.points.flat());
          expect(path.hasAttribute("stroke-dasharray")).toBe(lines[at]!.dashed);
        });
        if (leaf.handle) {
          const x = rect.x + Number(leaf.handle.x_mm),
            y = rect.y + Number(leaf.handle.y_mm);
          expect([view === "exterior" ? 1200 - x : x, y]).toEqual(
            fixture.expected[index]!.handle!.map(Number),
          );
        }
        unmount();
      });
    });
});
