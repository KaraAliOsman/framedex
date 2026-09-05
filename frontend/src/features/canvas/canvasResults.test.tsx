import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { EngineCalculateResponse } from "../../api/generated/models";
import { CADViewportSvg } from "./CADViewportSvg";
import { useCanvasStore } from "./canvasStore";
import { CanvasTechnicalResults } from "./CanvasTechnicalResults";

const sentinelResponse: EngineCalculateResponse = {
  profile_cuts: [
    {
      sku: "FRAME-SENTINEL",
      role: "FRAME",
      length_mm: "1111.25",
      angle_left: "45.0",
      angle_right: "45.0",
      qty: 2,
      bay_id: "g1",
    },
    {
      sku: "FRAME-SENTINEL",
      role: "FRAME",
      length_mm: "1222.50",
      angle_left: "45.0",
      angle_right: "45.0",
      qty: 2,
      bay_id: "g1",
    },
    {
      sku: "BEAD-SENTINEL",
      role: "GLAZING_BEAD",
      length_mm: "777.75",
      angle_left: "45.0",
      angle_right: "45.0",
      qty: 4,
      bay_id: "g1",
    },
  ],
  reinforcements: [
    {
      parent_profile_sku: "FRAME-SENTINEL",
      reinforcement_sku: "STEEL-SENTINEL",
      role: "FRAME",
      length_mm: "1066.60",
      qty: 4,
      bay_id: "g1",
    },
  ],
  glasses: [
    {
      bay_id: "g1",
      width_mm: "876.54",
      height_mm: "765.43",
      area_m2: "0.6708",
      weight_kg: "6.71",
      thickness_net_mm: "4.00",
    },
  ],
  hardware_items: [],
};

describe("API-owned canvas outputs", () => {
  beforeEach(() => useCanvasStore.getState().reset());

  it("renders changed API sentinel values in the SVG and technical panel", () => {
    const inputs = {
      ...useCanvasStore.getState().inputs,
      systemId: "sentinel-system",
    };
    const commit = vi.fn().mockResolvedValue(true);
    const { rerender } = render(
      <CADViewportSvg
        inputs={inputs}
        response={sentinelResponse}
        disabled={false}
        onCommit={commit}
        onEditStart={() => undefined}
      />,
    );

    expect(screen.getByText("FIXED")).toBeInTheDocument();
    expect(screen.getByTestId("canvas-glass-dimension")).toHaveTextContent("876.54 × 765.43 mm");
    expect(screen.getByTestId("fixed-glass")).toHaveAttribute("data-width-mm", "876.54");

    rerender(<CanvasTechnicalResults response={sentinelResponse} />);
    expect(screen.getByTestId("technical-frame")).toHaveTextContent("1111.25 × 1222.50 mm");
    expect(screen.getByTestId("technical-reinforcement")).toHaveTextContent("1066.60 mm");
    expect(screen.getByTestId("technical-glass")).toHaveTextContent("876.54 × 765.43 mm");
    expect(screen.getByTestId("technical-bead")).toHaveTextContent("777.75 mm");
  });
});
