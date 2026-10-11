import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import fixtures from "../../../../engine/tests/fixtures/symbols/advanced.json";
import { AdvancedPlanPane } from "./AdvancedPlanPane";
import type { OpeningLeafFact } from "./physicalOpenings";

describe("engine-sourced advanced plan", () => {
  it("keeps a horizontal pivot's exact polygon", () => {
    const fixture = fixtures.find((item) => item.name === "DEMO_PIVOT_H/EJE-30/interior")!;
    const leaves = fixture.leaves as unknown as OpeningLeafFact[];
    const { container } = render(<AdvancedPlanPane facts={{ m: leaves }} onHide={() => {}} />);
    const points = leaves[0]!.advanced!.open_plan_polygon!;
    expect(container.querySelector('path[d$="Z"]')?.getAttribute("d")).toBe(
      points
        .map((point, index) => `${index ? "L" : "M"}${point.x_mm} ${point.depth_mm}`)
        .join(" ") + " Z",
    );
  });
  it("shows independent access rotation without opening the folding packet", () => {
    const fixture = fixtures.find((item) => item.name === "DEMO_PLEGABLE/3+0-PASO/interior")!;
    const leaves = fixture.leaves as unknown as OpeningLeafFact[];
    const { container } = render(<AdvancedPlanPane facts={{ m: leaves }} onHide={() => {}} />);
    fireEvent.click(screen.getByRole("button", { name: "Ver hoja de paso" }));
    const data = leaves[2]!.advanced!;
    expect(container.querySelectorAll(".advanced-plan-open")[2]?.getAttribute("d")).toBe(
      data
        .pass_open_plan!.map(
          (point, index) => `${index ? "L" : "M"}${point.x_mm} ${point.depth_mm}`,
        )
        .join(" "),
    );
    expect(container.querySelectorAll(".advanced-plan-open")[0]?.getAttribute("d")).toBe(
      leaves[0]!
        .advanced!.closed_plan.map(
          (point, index) => `${index ? "L" : "M"}${point.x_mm} ${point.depth_mm}`,
        )
        .join(" "),
    );
  });
  it("preserves other bays' travel and horizontal pivot polygons in passage mode", () => {
    const source = (name: string, bay: string) =>
      (fixtures.find((item) => item.name === name)!.leaves as unknown as OpeningLeafFact[]).map(
        (leaf) => ({ ...leaf, bay_id: bay }),
      );
    const fold = source("DEMO_PLEGABLE/3+0-PASO/interior", "fold");
    const hst = source("DEMO_HST/A/interior", "hst");
    const pivot = source("DEMO_PIVOT_H/EJE-30/interior", "pivot");
    const { container } = render(
      <AdvancedPlanPane facts={{ m: [...fold, ...hst, ...pivot] }} onHide={() => {}} />,
    );
    const figures = container.querySelectorAll("figure");
    const preserved = [...figures].slice(1).map((figure) => figure.innerHTML);
    fireEvent.click(screen.getByRole("button", { name: "Ver hoja de paso" }));
    expect([...figures].slice(1).map((figure) => figure.innerHTML)).toEqual(preserved);
    expect(figures[0]!.querySelectorAll(".advanced-plan-open")[0]?.getAttribute("d")).toBe(
      fold[0]!
        .advanced!.closed_plan.map(
          (point, index) => `${index ? "L" : "M"}${point.x_mm} ${point.depth_mm}`,
        )
        .join(" "),
    );
  });
});
