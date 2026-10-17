import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import type { PositionResponse, GlassPiece } from "../../api/generated/models";
import { PositionMaterials } from "./PositionMaterials";

afterEach(cleanup);
function sample(): PositionResponse {
  const glass = (bay_id: string, label: string): GlassPiece => ({
    bay_id,
    leaf_id: null,
    width_mm: "600",
    height_mm: "800",
    shape: null,
    area_m2: "0.4800",
    weight_kg: null,
    thickness_net_mm: "4",
    glass_spec: label,
    article_sku: null,
    exposed_edges: null,
  });
  return {
    id: "p1",
    project_id: "work1",
    position_index: 1,
    location_tag: "Living",
    quantity: 2,
    typology: "COMPOSITE",
    price_net: "0",
    discount_pct: "0",
    updated_at: "2026-10-17T00:00:00Z",
    design: {
      system_id: "",
      nominal_width_mm: "1200",
      nominal_height_mm: "1000",
      color: "WHITE",
      parametric_tree: {
        version: "product-v2",
        assembly: {
          modules: [
            {
              id: "left",
              width_mm: "600",
              height_mm: "1000",
              tree: { id: "bay", type: "BAY", opening_type: "FIXED" },
            },
            {
              id: "right",
              width_mm: "600",
              height_mm: "1000",
              tree: { id: "bay", type: "BAY", opening_type: "FIXED" },
            },
          ],
          couplings: [],
        },
      },
    },
    bom: {
      calculation_hash: "sha256:" + "a".repeat(64),
      profile_cuts: [],
      reinforcements: [],
      panels: [],
      hardware_items: [],
      fittings: [],
      leaf_weights: [],
      glasses: [glass("left|bay", "Izquierda"), glass("right|bay", "Derecha")],
    },
  };
}

it("links a material to its module without selecting an identically named bay in the other module", () => {
  const { container } = render(<PositionMaterials position={sample()} orgId="org" />);
  fireEvent.click(screen.getByRole("button", { name: "Derecha" }));
  expect(container.querySelector('[data-module-id="right"] .bay-select-ring')).not.toBeNull();
  expect(container.querySelector('[data-module-id="left"] .bay-select-ring')).toBeNull();
  expect(screen.getByRole("button", { name: "Derecha" })).toHaveAttribute("aria-pressed", "true");
  expect(container.querySelector(".add-handle")).toBeNull();
  expect(container.querySelector("foreignObject input")).toBeNull();
  fireEvent.click(container.querySelector('[data-module-id="left"] .module-bay')!);
  expect(screen.getByRole("button", { name: "Izquierda" })).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByRole("button", { name: "Derecha" })).toHaveAttribute("aria-pressed", "false");
});

it("does not guess the destination of a material whose identity is absent", () => {
  const position = sample();
  position.bom.glasses[0]!.bay_id = "unknown|bay";
  const { container } = render(<PositionMaterials position={position} orgId="org" />);
  fireEvent.click(screen.getByRole("button", { name: "Izquierda" }));
  expect(screen.getByRole("status")).toHaveTextContent("no tiene un destino individual");
  expect(container.querySelector(".bay-select-ring")).toBeNull();
});
