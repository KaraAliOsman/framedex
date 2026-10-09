import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { resolveMembers } from "./members";
import { SectionView } from "./SectionView";

describe("horizontal section authority", () => {
  it("keeps drawing proportions without presenting the fallback as a measured depth", () => {
    const { container } = render(
      <SectionView bay={null} members={resolveMembers(undefined)} widthMm={2400} />,
    );
    expect(screen.getByText(/Profundidad del marco: Sin dato/)).toBeTruthy();
    expect(screen.getByText(/trazo aproximado/)).toBeTruthy();
    expect(container.querySelector(".section-member--approx")).not.toBeNull();
    expect(container.querySelector(".section-dim")).toBeNull();
    expect(container.querySelector("svg text")).toBeNull();
  });

  it("preserves the declared fractional depth independently of drawing crop and scale", () => {
    const members = resolveMembers(undefined);
    members.frame.section = {
      source: "POLYGON",
      depth_mm: "60.25",
      polygon: [
        { x_mm: "0", y_mm: "0" },
        { x_mm: "60", y_mm: "0" },
        { x_mm: "60", y_mm: "60.25" },
        { x_mm: "0", y_mm: "60.25" },
      ],
    };
    const { rerender, container } = render(
      <SectionView bay={null} members={members} widthMm={600} />,
    );
    expect(screen.getByText("60,25 mm")).toBeTruthy();
    rerender(<SectionView bay={null} members={members} widthMm={2400} />);
    expect(screen.getByText("60,25 mm")).toBeTruthy();
    expect(container.querySelector(".section-member--approx")).toBeNull();
    expect(container.querySelector(".section-dim")).not.toBeNull();
  });
});
