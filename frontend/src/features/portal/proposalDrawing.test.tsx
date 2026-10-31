import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";
import type { PortalPosition } from "../../api/generated/models";
import { ProposalDrawing } from "./proposalDrawing";

afterEach(cleanup);

const position = {
  position_index: 1,
  location_tag: "Living",
  width_mm: "1200",
  height_mm: "1000",
  parametric_tree: null,
  opening_leaves: [],
  opening_measurements: [],
} as unknown as PortalPosition;

test("the client sees the 3D view when the workshop's plan includes it", () => {
  render(<ProposalDrawing position={position} />);
  expect(screen.getByRole("button", { name: "3D" })).toBeVisible();
});

test("a Taller's client reads the drawing without the 3D view", () => {
  render(<ProposalDrawing position={position} threeD={false} />);
  expect(screen.queryByRole("button", { name: "3D" })).toBeNull();
  expect(screen.getByRole("button", { name: "Técnica" })).toBeVisible();
});
