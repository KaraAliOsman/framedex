import type { SeriesCell, SeriesSheet } from "../../api/generated/models";

export function cell(
  field: string,
  value: string | null,
  extra: Partial<SeriesCell> = {},
): SeriesCell {
  return {
    resource: "systems",
    row_id: "system",
    field,
    value,
    origin: "SUGGESTED",
    source_ref: "Plantilla de prueba",
    set_by: null,
    actor_name: null,
    set_at: null,
    version_id: null,
    ...extra,
  };
}

export function sheetFixture(cells: SeriesCell[] = []): SeriesSheet {
  // Only the response fields used by this projection are needed in these tests.
  return {
    id: "system",
    revision: "revision-1",
    setup: { template_id: null, template_version: null, verified_by: null, verified_at: null },
    usage: {
      level: "DRAWABLE",
      levels: [],
      pending: [],
      suggested_count: cells.filter((item) => item.origin === "SUGGESTED").length,
      verified: false,
      is_example: false,
      scope: "SERIES",
    },
    tabs: {
      profiles: [{ id: "profile", name: "Marco", sku: "PRO-M", face_width_mm: "60.00" }],
      rules: {
        id: "system",
        name: "PRO6004 sintética",
        manufacturer: "Taller de prueba",
        code: "PRO6004",
        system_family: "CASEMENT",
        material: "PVC",
        depth_mm: "60.00",
        version: 1,
        is_active: true,
        is_demo: false,
        read_only: false,
        dimensional_limits: [],
        finish_authority: null,
      },
      hardware: [],
      glazing_colors: { beads: [], finishes: [] },
      typologies: { dimensional_limits: [], series_max_weight_kg: null },
      prices: { can_view: false, items: [], purchase_mappings: [], reinforcements: [] },
    },
    cells,
  } as unknown as SeriesSheet;
}
