import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { GlassSummary, glassSummaryCsv, type GlassPiece } from "./GlassSummary";

const glasses: GlassPiece[] = [
  {
    bay_id: "bay_1",
    width_mm: "680.00",
    height_mm: "1310.00",
    area_m2: "0.8908",
    weight_kg: "17.82",
    thickness_net_mm: "8.00",
    glass_spec: "4-16-4 Float Incoloro",
    article_sku: "GLS-441",
  },
  {
    bay_id: "bay_1",
    leaf_id: "leaf_1",
    width_mm: "680.00",
    height_mm: "1310.00",
    area_m2: "0.8908",
    weight_kg: "17.82",
    thickness_net_mm: "8.00",
    glass_spec: "4-16-4 Float Incoloro",
    article_sku: "GLS-441",
  },
  {
    bay_id: "bay_2",
    width_mm: "546.00",
    height_mm: "1176.00",
    area_m2: "0.6421",
    weight_kg: "12.84",
    thickness_net_mm: "9.00",
    glass_spec: "4.4.2-12-4 Laminado",
    article_sku: "GLS-LAM",
  },
];

describe("GlassSummary", () => {
  it("groups pieces by composition, sku and thickness with per-size counts and totals", () => {
    render(<GlassSummary glasses={glasses} polishing={[]} onExport={vi.fn()} />);
    expect(screen.getByText("Resumen de vidrios")).toBeTruthy();
    expect(screen.getByText("4-16-4 Float Incoloro")).toBeTruthy();
    expect(screen.getByText("4.4.2-12-4 Laminado")).toBeTruthy();
    // two identical panes collapse into one dims row with qty 2
    expect(screen.getByText("680.00×1310.00 mm")).toBeTruthy();
    // group area 2 × 0.8908, total = 1.7816 + 0.6421
    expect(screen.getByText("1.782 m²")).toBeTruthy();
    expect(screen.getByText("2.424 m²")).toBeTruthy();
    // totals: 3 panes, weight 17.82*2 + 12.84 = 48.48
    expect(screen.getByText("48.48 kg")).toBeTruthy();
  });

  it("shows the sealed edge polishing per pane and exports a deterministic CSV", () => {
    const onExport = vi.fn();
    render(
      <GlassSummary
        glasses={glasses}
        polishing={[
          { bay_id: "bay_1", edges: { top: true, bottom: true } },
          { bay_id: "bay_1", leaf_id: "leaf_1", edges: { left: true } },
        ]}
        onExport={onExport}
      />,
    );
    const cells = screen.getAllByText(/^(S·I|Z)$/);
    expect(cells.length).toBe(2);
    fireEvent.click(screen.getByText("Exportar vidrios (CSV)"));
    expect(onExport).toHaveBeenCalledTimes(1);
    const groups = onExport.mock.calls[0]![0];
    const csv = glassSummaryCsv(groups);
    const lines = csv.split("\n");
    expect(lines[0]).toContain("Composición");
    expect(lines.some((line) => line.includes("4-16-4 Float Incoloro"))).toBe(true);
    expect(lines.some((line) => line.includes("680.00×1310.00"))).toBe(true);
    expect(lines.some((line) => line.includes("Z"))).toBe(true);
  });
});
