import { cleanup, render } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";

import type { PositionDesign } from "../../api/generated/models";
import { t } from "../../i18n/es-CL";
import { PositionThumb } from "./PositionThumb";

afterEach(cleanup);

function design(parametricTree: unknown): PositionDesign {
  return {
    system_id: "system-a",
    nominal_width_mm: "1800.00",
    nominal_height_mm: "1200.00",
    color: "WHITE",
    parametric_tree: parametricTree,
  } as PositionDesign;
}

it("renders a classic single-bay tree as a front-elevation thumbnail", () => {
  const { container } = render(
    <PositionThumb design={design({ id: "bay-a", type: "BAY", opening_type: "FIXED" })} />,
  );

  const svg = container.querySelector('svg[role="img"]');
  expect(svg).not.toBeNull();
  expect(svg!.getAttribute("aria-label")).toBe(t("projects.positionThumb"));
  // Frame members actually drawn — not an empty picture frame.
  expect(container.querySelectorAll("rect").length).toBeGreaterThan(0);
});

it("renders a product-v2 assembly the same way", () => {
  const { container } = render(
    <PositionThumb
      design={design({
        version: "product-v2",
        assembly: {
          modules: [
            {
              id: "m1",
              width_mm: "900.00",
              tree: { id: "b1", type: "BAY", opening_type: "TILT_TURN_LEFT" },
            },
            {
              id: "m2",
              width_mm: "900.00",
              tree: { id: "b2", type: "BAY", opening_type: "FIXED" },
            },
          ],
          couplings: [
            {
              id: "c1",
              left_module_id: "m1",
              right_module_id: "m2",
              angle_deg: "90.0",
              coupler_sku: null,
            },
          ],
        },
      })}
    />,
  );

  const svg = container.querySelector('svg[role="img"]');
  expect(svg).not.toBeNull();
  expect(container.querySelectorAll("rect").length).toBeGreaterThan(0);
});

it("still draws the frame shell for trees it does not recognise", () => {
  const { container } = render(<PositionThumb design={design({ bogus: true })} />);
  expect(container.querySelector('svg[role="img"]')).not.toBeNull();
});
