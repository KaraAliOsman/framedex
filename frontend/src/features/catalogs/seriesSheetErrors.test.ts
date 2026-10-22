import { describe, expect, it } from "vitest";

import { ApiError } from "../../api/apiMutator";
import { cell, sheetFixture } from "./seriesSheet.test.fixtures";
import { sheetValidationError } from "./seriesSheetErrors";
import { sheetTables } from "./seriesSheetModel";

describe("sheet rejection coordinates", () => {
  it("points to the failing field in the exact nested row without marking another limit", () => {
    const limits = [0, 1].map(() => ({
      opening_type: "TURN",
      min_leaf_width_mm: "300.00",
      max_leaf_width_mm: "200.00",
    }));
    const sheet = sheetFixture([cell("dimensional_limits", JSON.stringify(limits))]);
    sheet.tabs.rules.dimensional_limits = limits as NonNullable<
      typeof sheet.tabs.rules.dimensional_limits
    >;
    const table = sheetTables(sheet, "typologies")[0]!;
    const error = new ApiError(400, {
      error: {
        resource: "systems",
        row_id: "system",
        fields: {
          dimensional_limits: [
            {},
            { max_leaf_width_mm: ["El máximo debe ser mayor o igual al mínimo."] },
          ],
        },
      },
    });
    expect(sheetValidationError(error, table)?.cells).toEqual([
      {
        rowId: "limits-1",
        columnId: "max_leaf_width_mm",
        message: "El máximo debe ser mayor o igual al mínimo.",
      },
    ]);
  });

  it("ignores another resource, another row and non-validation failures", () => {
    const table = sheetTables(sheetFixture([cell("rebate_depth_mm", "3.00")]), "rules")[0]!;
    for (const [status, resource, row_id] of [
      [400, "articles", "system"],
      [400, "systems", "foreign"],
      [409, "systems", "system"],
    ] as const)
      expect(
        sheetValidationError(
          new ApiError(status, {
            error: { resource, row_id, fields: { rebate_depth_mm: ["Error"] } },
          }),
          table,
        ),
      ).toBeNull();
    expect(sheetValidationError(new Error("network"), table)).toBeNull();
  });
});
