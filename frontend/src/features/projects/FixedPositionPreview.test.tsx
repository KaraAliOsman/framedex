import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import type { EngineCalculateResponse } from "../../api/generated/models";
import type { CanvasDesignInputs } from "../canvas/canvasStore";
import { OPENINGS, type IntentNode } from "../canvas/intentEditing";
import { FixedPositionPreview } from "./FixedPositionPreview";

afterEach(cleanup);

function design(): CanvasDesignInputs {
  return {
    systemId: "system-a",
    nominalWidthMm: "1000.00",
    nominalHeightMm: "800.00",
    color: "WHITE",
    parametricTree: {
      id: "bay-a",
      type: "BAY",
      opening_type: "FIXED",
    },
    product: null,
  };
}

// Synthetic API-boundary fixture: these tests verify rendering, not engine formulas.
function calculation(): EngineCalculateResponse {
  return {
    profile_cuts: [],
    reinforcements: [],
    glasses: [
      {
        bay_id: "bay-a",
        leaf_id: null,
        width_mm: "910.00",
        height_mm: "710.00",
        area_m2: "0.6461",
        weight_kg: "6.46",
        thickness_net_mm: "4.00",
      },
    ],
    panels: [],
    hardware_items: [],
    leaf_weights: [],
    calculation_hash: `sha256:${"a".repeat(64)}`,
  };
}

it("renders supplied dimensions and removes stale geometry until a result arrives", () => {
  const inputs = design();
  const first = calculation();
  const view = render(<FixedPositionPreview inputs={inputs} result={first} />);

  expect(screen.getByTestId("position-preview-frame")).toHaveAttribute("width", "1000");
  expect(screen.getByTestId("position-preview-frame")).toHaveAttribute("height", "800");
  expect(screen.getByTestId("position-preview-glass")).toHaveAttribute("width", "910");
  expect(screen.getByTestId("position-preview-glass")).toHaveAttribute("height", "710");
  expect(screen.getByText("910.00 × 710.00 mm")).toBeInTheDocument();

  view.rerender(<FixedPositionPreview inputs={inputs} result={null} />);
  expect(view.container).toBeEmptyDOMElement();

  const next = calculation();
  next.glasses = next.glasses.map((glass) => ({
    ...glass,
    width_mm: "884.25",
    height_mm: "688.50",
  }));

  view.rerender(<FixedPositionPreview inputs={inputs} result={next} />);
  const glass = screen.getByTestId("position-preview-glass");
  expect(glass).toHaveAttribute("width", "884.25");
  expect(glass).toHaveAttribute("height", "688.5");
  expect(glass).toHaveAttribute("data-height-mm", "688.50");
  expect(screen.getByText("884.25 × 688.50 mm")).toBeInTheDocument();
  expect(screen.queryByText("910.00 × 710.00 mm")).not.toBeInTheDocument();
});

it("renders ROOT → FIXED exactly like the bare bay without changing either input", () => {
  const bare = design();
  const result = calculation();
  const wrapped: CanvasDesignInputs = {
    ...bare,
    parametricTree: {
      id: "root-a",
      type: "ROOT",
      children: [bare.parametricTree],
    },
  };
  const before = structuredClone({ bare, wrapped, result });
  const view = render(<FixedPositionPreview inputs={bare} result={result} />);
  const markup = view.container.innerHTML;

  view.rerender(<FixedPositionPreview inputs={wrapped} result={result} />);

  expect(view.container.innerHTML).toBe(markup);
  expect({ bare, wrapped, result }).toEqual(before);
  expect(wrapped.parametricTree.children?.[0]).toBe(bare.parametricTree);
  expect(screen.getByTestId("position-preview-glass")).toHaveAttribute("x", "45");
  expect(screen.getByTestId("position-preview-glass")).toHaveAttribute("y", "45");
});

it.each(OPENINGS.filter((opening) => opening !== "FIXED"))(
  "returns null for unsupported opening %s",
  (opening) => {
    const inputs = design();
    inputs.parametricTree.opening_type = opening;
    const { container } = render(<FixedPositionPreview inputs={inputs} result={calculation()} />);
    expect(container).toBeEmptyDOMElement();
  },
);

it.each(["SPLIT_V", "SPLIT_H"] as const)(
  "returns null for %s without changing its tree",
  (type) => {
    const inputs = design();
    const first = inputs.parametricTree;
    const tree: IntentNode = {
      id: "split-a",
      type,
      children: [first, { ...first, id: "bay-b" }],
    };
    inputs.parametricTree = tree;
    const before = structuredClone(inputs);

    const { container } = render(<FixedPositionPreview inputs={inputs} result={calculation()} />);

    expect(container).toBeEmptyDOMElement();
    expect(inputs).toEqual(before);
  },
);

it.each(["wrong-bay", "missing", "multiple", "invalid", "oversized"] as const)(
  "returns null for %s glass rather than drawing guessed geometry",
  (failure) => {
    const inputs = design();
    const result = calculation();

    result.glasses = result.glasses.flatMap((glass) => {
      switch (failure) {
        case "wrong-bay":
          return [{ ...glass, bay_id: "another-bay" }];
        case "missing":
          return [];
        case "multiple":
          return [glass, { ...glass }];
        case "invalid":
          return [{ ...glass, width_mm: "NaN" }];
        case "oversized":
          return [{ ...glass, width_mm: "1001.00" }];
      }
    });

    const before = structuredClone({ inputs, result });
    const view = render(<FixedPositionPreview inputs={inputs} result={calculation()} />);
    expect(screen.getByTestId("fixed-position-preview")).toBeInTheDocument();

    view.rerender(<FixedPositionPreview inputs={inputs} result={result} />);

    expect(view.container).toBeEmptyDOMElement();
    expect({ inputs, result }).toEqual(before);
  },
);
