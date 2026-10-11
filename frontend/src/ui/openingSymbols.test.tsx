import { render } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import cases from "../../../engine/tests/fixtures/symbols/cases.json";
import advanced from "../../../engine/tests/fixtures/symbols/advanced.json";
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

describe("advanced catalog fixtures shared with Python", () => {
  for (const fixture of advanced)
    it(fixture.name, () => {
      const view = fixture.view as "interior" | "exterior";
      fixture.leaves.forEach((leaf, index) => {
        const data = leaf.advanced;
        const rect = {
          x: Number(leaf.x_mm),
          y: Number(leaf.y_mm),
          width: Number(leaf.width_mm),
          height: Number(leaf.height_mm),
        };
        const lines = openingSymbolLines(
          leaf.opening as PhysicalOpening,
          rect,
          view,
          data.travel as "LEFT" | "RIGHT" | "UP" | "DOWN" | null,
          false,
          {
            x: data.pivot_x_mm === null ? null : Number(data.pivot_x_mm),
            y: data.pivot_y_mm === null ? null : Number(data.pivot_y_mm),
            closingSide: leaf.handle?.side,
          },
        );
        // SVG projects Decimal thirds onto binary screen coordinates. Compare
        // at 0.01 mm (0.00 mm difference); exact authority is verified by the
        // Python/PDF fixtures before any Number conversion.
        expect(
          lines.map((line) => ({
            ...line,
            points: line.points.map(([x, y]) => [
              (view === "exterior" ? Number(fixture.total_width_mm) - x : x).toFixed(2),
              y.toFixed(2),
            ]),
          })),
        ).toEqual(
          fixture.expected[index]!.lines.map((line) => ({
            ...line,
            points: line.points.map((point) => point.map((value) => Number(value).toFixed(2))),
          })),
        );
      });
    });
});
