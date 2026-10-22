import { ApiError } from "../../api/apiMutator";
import { TableValidationError, type TableCellError } from "../../ui/EditableTable";
import type { SheetTable } from "./seriesSheetModel";

function issues(value: unknown, path: string[] = []): { path: string; message: string }[] {
  if (typeof value === "string") return [{ path: path.join("."), message: value }];
  if (Array.isArray(value))
    return value.flatMap((item, index) =>
      issues(item, typeof item === "string" ? path : [...path, String(index)]),
    );
  if (value && typeof value === "object")
    return Object.entries(value).flatMap(([key, item]) => issues(item, [...path, key]));
  return [];
}

/** Bind the server's row and nested field to the same visible spreadsheet cell. */
export function sheetValidationError(
  error: unknown,
  table: SheetTable,
): TableValidationError | null {
  if (!(error instanceof ApiError) || error.status !== 400) return null;
  const payload = error.payload as {
    error?: { resource?: string; row_id?: string; fields?: unknown };
  } | null;
  const detail = payload?.error;
  if (!detail?.resource || !detail.row_id || !detail.fields) return null;
  const failures = issues(detail.fields);
  const cells: TableCellError[] = [];
  for (const [rowId, bindings] of Object.entries(table.bindings)) {
    for (const [columnId, binding] of Object.entries(bindings)) {
      if (binding.cell.resource !== detail.resource || binding.cell.row_id !== detail.row_id)
        continue;
      const path = [binding.cell.field, binding.index, binding.field]
        .filter((item) => item !== undefined)
        .join(".");
      const failure = failures.find(
        (item) =>
          item.path === path ||
          path.startsWith(item.path + ".") ||
          item.path.startsWith(path + "."),
      );
      if (!failure) continue;
      cells.push({
        rowId,
        columnId,
        message:
          failure.message === "Maximum must not be below minimum."
            ? "El máximo debe ser mayor o igual al mínimo."
            : failure.message,
      });
    }
  }
  return cells.length ? new TableValidationError(cells) : null;
}
