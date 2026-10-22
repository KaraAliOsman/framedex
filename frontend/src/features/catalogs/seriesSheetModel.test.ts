import { describe, expect, it } from "vitest";

import { cell, sheetFixture } from "./seriesSheet.test.fixtures";
import { address, bindChanges, sheetTables, usageLabel } from "./seriesSheetModel";

describe("series sheet projection", () => {
  it("names handed openings from the shared glossary and keeps unknown additions visible", () => {
    const sheet = sheetFixture();
    sheet.tabs.rules.dimensional_limits = [
      "FIXED",
      "TURN_LEFT",
      "TURN_RIGHT",
      "TILT_TURN_LEFT",
      "NEW_OPENING",
    ].map((opening_type) => ({ opening_type })) as NonNullable<
      typeof sheet.tabs.rules.dimensional_limits
    >;
    expect(sheetTables(sheet, "typologies")[0]!.rows.map((row) => row.label)).toEqual([
      "Fijo",
      "Abatible izquierda",
      "Abatible derecha",
      "Oscilobatiente izquierda",
      "Ventana 5",
    ]);
  });

  it("keeps explicit missing values, zero, exact weight and readonly SKU distinct", () => {
    const sheet = sheetFixture([
      cell("face_width_mm", null, { resource: "articles", row_id: "profile", origin: null }),
      cell("commercial_length_mm", "0.00", { resource: "articles", row_id: "profile" }),
      cell("weight_kg_m", "1.2345", { resource: "articles", row_id: "profile" }),
    ]);
    const table = sheetTables(sheet, "profiles")[0]!;
    expect(table.rows[0]!.values).toEqual({
      sku: "PRO-M",
      face_width_mm: null,
      commercial_length_mm: "0.00",
      weight_kg_m: "1.2345",
    });
    expect(table.columns.find((item) => item.id === "sku")!.readOnly).toBe(true);
    expect(table.columns.find((item) => item.id === "face_width_mm")!.precision).toBe(2);
    expect(table.columns.find((item) => item.id === "weight_kg_m")).toMatchObject({
      precision: 4,
      unit: "kg/m",
    });
    expect(() =>
      bindChanges(table, [
        { rowId: "profile", columnId: "sku", value: "other", previousValue: "PRO-M" },
      ]),
    ).toThrow("Esta celda cambió");
  });

  it("binds a rule to its real address without deriving any number", () => {
    const source = cell("rebate_depth_mm", "3.00");
    const table = sheetTables(sheetFixture([source]), "rules")[0]!;
    expect(table.rows[0]!.suggested).toBe(true);
    expect(
      bindChanges(table, [
        { rowId: address(source), columnId: "value", previousValue: "3.00", value: "2.25" },
      ]),
    ).toEqual([{ resource: "systems", row_id: "system", field: "rebate_depth_mm", value: "2.25" }]);
    expect(source.value).toBe("3.00");
    expect(table.rows[0]!.cellOptions?.value).toMatchObject({
      min: "0",
      nullable: true,
      max: "99999999.99",
    });
  });

  it("keeps required small rules distinct from optional values and four decimal typology weights", () => {
    const table = sheetTables(sheetFixture([cell("sash_overlap_mm", "3.00")]), "rules")[0]!;
    expect(table.rows[0]!.cellOptions?.value).toMatchObject({
      min: "0",
      max: "99.99",
      nullable: false,
      precision: 2,
    });
    const weights = sheetTables(sheetFixture(), "typologies")[0]!.columns.find(
      (item) => item.id === "max_leaf_weight_kg",
    );
    expect(weights).toMatchObject({
      precision: 4,
      nullable: true,
      min: "0.0001",
      max: "999999.9999",
    });
  });

  it("combines several cells of an array into one atomic write and preserves other fields", () => {
    const values = [
      {
        opening_type: "TURN",
        min_leaf_width_mm: "300.00",
        max_leaf_width_mm: "1500.00",
        max_leaf_weight_kg: "80.1234",
      },
      { opening_type: "FIXED", min_leaf_width_mm: null, max_leaf_width_mm: "2200.00" },
    ];
    const sheet = sheetFixture([cell("dimensional_limits", JSON.stringify(values))]);
    sheet.tabs.rules.dimensional_limits = values as NonNullable<
      typeof sheet.tabs.rules.dimensional_limits
    >;
    const table = sheetTables(sheet, "typologies")[0]!;
    expect(
      bindChanges(table, [
        {
          rowId: "limits-0",
          columnId: "min_leaf_width_mm",
          previousValue: "300.00",
          value: "310.00",
        },
        {
          rowId: "limits-0",
          columnId: "max_leaf_width_mm",
          previousValue: "1500.00",
          value: "1490.00",
        },
        { rowId: "limits-1", columnId: "min_leaf_width_mm", previousValue: null, value: "0.00" },
      ]),
    ).toEqual([
      {
        resource: "systems",
        row_id: "system",
        field: "dimensional_limits",
        value: [
          { ...values[0], min_leaf_width_mm: "310.00", max_leaf_width_mm: "1490.00" },
          { ...values[1], min_leaf_width_mm: "0.00" },
        ],
      },
    ]);
    expect(JSON.parse(sheet.cells[0]!.value!)).toEqual(values);
  });

  it("keeps finish arrays and manufacturer colors in their separate atomic fields", () => {
    const colors = [{ code: "WHITE", name: "Blanco", manufacturer_code: "9016" }];
    const sheet = sheetFixture([
      cell("finishes", '["WHITE","OAK"]'),
      cell("finish_authority.colors", JSON.stringify(colors)),
    ]);
    sheet.tabs.glazing_colors.finishes = ["WHITE", "OAK"];
    sheet.tabs.rules.finish_authority = { colors } as typeof sheet.tabs.rules.finish_authority;
    const tables = sheetTables(sheet, "glazing_colors");
    expect(
      bindChanges(
        tables.find((table) => table.id === "finishes")!,
        [{ rowId: "finish-1", columnId: "code", previousValue: "OAK", value: "BLACK" }],
      )[0]!.value,
    ).toEqual(["WHITE", "BLACK"]);
    expect(
      bindChanges(
        tables.find((table) => table.id === "colors")!,
        [
          { rowId: "colors-0", columnId: "name", previousValue: "Blanco", value: "Blanco liso" },
          {
            rowId: "colors-0",
            columnId: "manufacturer_code",
            previousValue: "9016",
            value: "R-9016",
          },
        ],
      )[0],
    ).toMatchObject({
      field: "finish_authority.colors",
      value: [{ code: "WHITE", name: "Blanco liso", manufacturer_code: "R-9016" }],
    });
  });

  it("labels each API level and keeps examples explicitly synthetic", () => {
    const usage = sheetFixture().usage;
    expect(usageLabel({ ...usage, level: null })).toBe("Completar serie");
    expect(usageLabel(usage)).toBe("Lista para dibujar");
    expect(usageLabel({ ...usage, level: "QUOTABLE" })).toBe("Lista para cotizar");
    expect(usageLabel({ ...usage, level: "MANUFACTURABLE" })).toBe("Lista para fabricar");
    expect(usageLabel({ ...usage, level: "MACHINE_READY" })).toBe("Lista para máquina");
    expect(usageLabel({ ...usage, level: "MACHINE_READY", is_example: true })).toBe("Ejemplo");
  });
});
