import {
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
  type ReactNode,
} from "react";

import { compareDecimal, parseDecimalInput } from "../decimal";
import { Button } from "./Controls";
import { Dialog } from "./Dialog";
import "./EditableTable.css";

export type EditableColumn = {
  id: string;
  label: string;
  kind?: "decimal" | "text";
  precision?: number;
  nullable?: boolean;
  min?: string;
  max?: string;
  unit?: string;
  readOnly?: boolean;
  validate?: (value: string | null) => string | null;
};

export type EditableRow = {
  id: string;
  label: string;
  values: Record<string, string | null>;
  before?: ReactNode;
  after?: ReactNode;
  suggested?: boolean;
  cellOptions?: Record<
    string,
    Partial<Pick<EditableColumn, "precision" | "nullable" | "min" | "max" | "validate">>
  >;
};

export type TableChange = {
  rowId: string;
  columnId: string;
  value: string | null;
  previousValue: string | null;
};

export type TableCellError = { rowId: string; columnId: string; message: string };

/** A rejected batch can point to exact cells, including cross-field checks. */
export class TableValidationError extends Error {
  constructor(readonly cells: TableCellError[]) {
    super("Revisa las celdas indicadas antes de guardar.");
  }
}

const cellKey = (row: string, column: string) => JSON.stringify([row, column]);
const shown = (value: string | null, column: EditableColumn) =>
  column.kind === "decimal" ? (value ?? "").replace(".", ",") : (value ?? "");

function parsed(
  text: string,
  column: EditableColumn,
): { value: string | null; error: string | null } {
  const value =
    text.trim() === ""
      ? null
      : column.kind === "decimal"
        ? parseDecimalInput(text, column.precision ?? 4)
        : text;
  if (value === null && text.trim() !== "")
    return {
      value,
      error: `Escribe un número con hasta ${column.precision ?? 4} decimales, por ejemplo 3,25.`,
    };
  if (value === null && !column.nullable) return { value, error: "Completa este valor." };
  if (value !== null && column.kind === "decimal") {
    if (column.min !== undefined && compareDecimal(value, column.min) < 0)
      return { value, error: `Usa un valor de al menos ${shown(column.min, column)}.` };
    if (column.max !== undefined && compareDecimal(value, column.max) > 0)
      return { value, error: `Usa un valor de hasta ${shown(column.max, column)}.` };
  }
  return { value, error: column.validate?.(value) ?? null };
}

/** Exact textual editing. The server owns validation, revisions and calculation.
 * A paste is one batch; undo writes a new batch and never erases audit history.
 */
export function EditableTable({
  label,
  columns,
  rows,
  onSave,
  readOnly = false,
  beforeLabel,
  afterLabel = "Origen",
  toolbar,
  onHistory,
  onActiveChange,
  focusRequest,
  onDirtyChange,
  pageSize = 50,
}: {
  label: string;
  columns: EditableColumn[];
  rows: EditableRow[];
  onSave: (changes: TableChange[]) => Promise<void>;
  readOnly?: boolean;
  beforeLabel?: string;
  afterLabel?: string;
  toolbar?: ReactNode;
  onHistory?: (rowId: string, columnId: string) => void;
  onActiveChange?: (rowId: string, columnId: string) => void;
  focusRequest?: { rowId: string; columnId: string } | null;
  onDirtyChange?: (dirty: boolean) => void;
  pageSize?: number;
}): JSX.Element {
  const id = useId();
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [failure, setFailure] = useState("");
  const [cellErrors, setCellErrors] = useState<Record<string, string>>({});
  const [undo, setUndo] = useState<TableChange[] | null>(null);
  const [page, setPage] = useState(0);
  const [active, setActive] = useState<[string, string] | null>(null);
  const [pasteText, setPasteText] = useState<string | null>(null);
  const [pasteError, setPasteError] = useState("");
  const [editingText, setEditingText] = useState(false);
  const tableRef = useRef<HTMLTableElement>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const locked = useRef(false);
  const mounted = useRef(true);
  const draftsRef = useRef(drafts);
  draftsRef.current = drafts;
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const entries = useMemo(
    () =>
      rows.flatMap((row) =>
        columns.map((baseColumn) => ({
          row,
          column: { ...baseColumn, ...row.cellOptions?.[baseColumn.id] },
          key: cellKey(row.id, baseColumn.id),
        })),
      ),
    [rows, columns],
  );
  const changed = entries.flatMap(({ row, column, key }) => {
    const text = drafts[key];
    if (text === undefined) return [];
    const result = parsed(text, column);
    if (!result.error && result.value === (row.values[column.id] ?? null)) return [];
    return [
      {
        rowId: row.id,
        columnId: column.id,
        value: result.value,
        previousValue: row.values[column.id] ?? null,
        error: result.error,
      },
    ];
  });
  const dirty = changed.length > 0;
  const invalid = changed.some((item) => item.error) || Object.keys(cellErrors).length > 0;
  const safePage = Math.min(page, Math.max(0, Math.ceil(rows.length / pageSize) - 1));
  const visible = rows.slice(safePage * pageSize, (safePage + 1) * pageSize);
  const activeVisible = visible.some((row) => row.id === active?.[0]);
  const hasAfter = rows.some((row) => row.after !== undefined) || onHistory !== undefined;
  const firstEditable = Math.max(
    0,
    columns.findIndex((column) => !column.readOnly),
  );
  useEffect(() => {
    onDirtyChange?.(dirty);
  }, [dirty, onDirtyChange]);

  async function persist(changes: TableChange[], reversing = false) {
    if (!changes.length || locked.current || readOnly) return;
    locked.current = true;
    setSaving(true);
    setFailure("");
    setCellErrors({});
    try {
      await onSave(changes);
      if (!mounted.current) return;
      setDrafts({});
      setUndo(reversing ? null : changes);
    } catch (error) {
      if (mounted.current) {
        if (error instanceof TableValidationError)
          setCellErrors(
            Object.fromEntries(
              error.cells.map((cell) => [cellKey(cell.rowId, cell.columnId), cell.message]),
            ),
          );
        setFailure(
          error instanceof Error ? error.message : "No se pudo guardar. Vuelve a intentarlo.",
        );
      }
    } finally {
      locked.current = false;
      if (mounted.current) setSaving(false);
    }
  }

  function save() {
    if (!invalid) void persist(changed.map(({ error: _error, ...change }) => change));
  }

  // Save after the user leaves a cell; keyboard navigation and typing stay
  // immediate. A failed request keeps the draft for an explicit retry.
  function blur(event: React.FocusEvent<HTMLTableElement>) {
    if (rootRef.current?.contains(event.relatedTarget as Node | null)) return;
    if (!failure) save();
  }

  function focus(rowIndex: number, columnIndex: number) {
    const row = rows[rowIndex];
    const column = columns[columnIndex];
    if (!row || !column) return;
    const targetPage = Math.floor(rowIndex / pageSize);
    setPage(targetPage);
    setActive([row.id, column.id]);
    setEditingText(false);
    requestAnimationFrame(() => {
      const target = Array.from(
        tableRef.current?.querySelectorAll<HTMLInputElement>("input[data-cell]") ?? [],
      ).find((input) => input.dataset.cell === cellKey(row.id, column.id));
      target?.focus();
      target?.select();
    });
  }

  const focusLatest = useRef(focus);
  focusLatest.current = focus;
  useEffect(() => {
    if (focusRequest)
      focusLatest.current(
        rows.findIndex((row) => row.id === focusRequest.rowId),
        columns.findIndex((column) => column.id === focusRequest.columnId),
      );
  }, [focusRequest]);

  function keydown(event: KeyboardEvent<HTMLInputElement>, rowIndex: number, columnIndex: number) {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "z" && !editingText) {
      event.preventDefault();
      reverse();
      return;
    }
    if (event.key === "F2") {
      event.preventDefault();
      setEditingText(true);
      return;
    }
    if (event.key === "Escape") {
      setCellErrors({});
      const row = rows[rowIndex]!;
      const column = columns[columnIndex]!;
      setDrafts((current) => {
        const next = { ...current };
        delete next[cellKey(row.id, column.id)];
        return next;
      });
      setEditingText(false);
      return;
    }
    if (editingText && event.key.startsWith("Arrow")) return;
    const move: Record<string, [number, number]> = {
      ArrowUp: [-1, 0],
      ArrowDown: [1, 0],
      ArrowLeft: [0, -1],
      ArrowRight: [0, 1],
      Enter: [event.shiftKey ? -1 : 1, 0],
    };
    if (event.key === "Tab") {
      const next = rowIndex * columns.length + columnIndex + (event.shiftKey ? -1 : 1);
      if (next < 0 || next >= rows.length * columns.length) return;
      event.preventDefault();
      focus(Math.floor(next / columns.length), next % columns.length);
      return;
    }
    const delta = move[event.key];
    if (!delta) return;
    event.preventDefault();
    if (event.key === "Enter") save();
    focus(
      Math.max(0, Math.min(rows.length - 1, rowIndex + delta[0])),
      Math.max(0, Math.min(columns.length - 1, columnIndex + delta[1])),
    );
  }

  function paste(text: string, start: [string, string] | null): boolean {
    if (readOnly || locked.current) return false;
    const rowIndex = rows.findIndex((row) => row.id === start?.[0]);
    const columnIndex = columns.findIndex((column) => column.id === start?.[1]);
    const fromRow = rowIndex < 0 ? 0 : rowIndex;
    const fromColumn = columnIndex < 0 ? firstEditable : columnIndex;
    const block = text
      .replace(/\r\n?/g, "\n")
      .replace(/\n$/, "")
      .split("\n")
      .map((line) => line.split("\t"));
    if (
      !text.trim() ||
      block.length + fromRow > rows.length ||
      block.some((line) => line.length + fromColumn > columns.length)
    ) {
      setPasteError(
        "El bloque no cabe. Elige una celda con espacio para todas las filas y columnas.",
      );
      return false;
    }
    if (block.some((line) => line.some((_, offset) => columns[fromColumn + offset]!.readOnly))) {
      setPasteError(
        "El bloque incluye una columna de consulta. Pega solo en las columnas editables.",
      );
      return false;
    }
    const next = { ...draftsRef.current };
    block.forEach((line, r) =>
      line.forEach((value, c) => {
        next[cellKey(rows[fromRow + r]!.id, columns[fromColumn + c]!.id)] = value;
      }),
    );
    setDrafts(next);
    setCellErrors({});
    setFailure("");
    setPasteError("");
    return true;
  }

  function reverse() {
    if (locked.current || readOnly) return;
    if (dirty) {
      setDrafts({});
      setCellErrors({});
      setFailure("");
      return;
    }
    if (undo) {
      const changedElsewhere = undo.some((change) => {
        const row = rows.find((item) => item.id === change.rowId);
        const column = columns.find((item) => item.id === change.columnId);
        if (!row || !column) return true;
        const current = row.values[change.columnId] ?? null;
        return (
          current !== change.value &&
          !(
            column.kind === "decimal" &&
            current !== null &&
            change.value !== null &&
            compareDecimal(current, change.value) === 0
          )
        );
      });
      if (changedElsewhere) {
        setUndo(null);
        setFailure(
          "La celda cambió después de tu edición. Revisa el valor actual antes de modificarla.",
        );
        return;
      }
      void persist(
        undo.map((change) => ({
          ...change,
          value: change.previousValue,
          previousValue: change.value,
        })),
        true,
      );
    }
  }

  return (
    <div className="ui-editable-table" ref={rootRef}>
      <div className="ui-editable-table__toolbar">
        {toolbar}
        <span className="ui-editable-table__status" role="status" aria-live="polite">
          {saving
            ? "Guardando…"
            : invalid
              ? "Revisa las celdas indicadas"
              : dirty
                ? "Cambios por guardar"
                : "Guardado"}
        </span>
        {!readOnly && (
          <>
            <Button size="compact" onClick={reverse} disabled={saving || (!dirty && !undo)}>
              Deshacer
            </Button>
            <Button
              size="compact"
              onClick={() => {
                setPasteError("");
                setPasteText("");
              }}
              disabled={saving || !rows.length}
            >
              Pegar desde Excel
            </Button>
            <Button size="compact" onClick={save} disabled={!dirty || invalid || saving}>
              Guardar cambios
            </Button>
          </>
        )}
      </div>
      {failure && (
        <p className="ui-editable-table__error" role="alert">
          {failure}
        </p>
      )}
      {pasteError && pasteText === null && (
        <p className="ui-editable-table__error" role="alert">
          {pasteError}
        </p>
      )}
      {!rows.length ? (
        <p className="ui-editable-table__empty">Todavía no hay filas en esta sección.</p>
      ) : (
        <>
          <p className="sr-only" id={`${id}-help`}>
            Usa flechas para moverte, Enter para guardar y bajar, Tab para avanzar y F2 para mover
            el cursor dentro del texto. Escape cancela la celda. Alt y Enter abre su historial.
          </p>
          <div className="ui-editable-table__scroll" role="region" aria-label={label} tabIndex={0}>
            <table
              role="grid"
              aria-label={label}
              aria-describedby={`${id}-help`}
              aria-rowcount={rows.length + 1}
              onBlur={blur}
              ref={tableRef}
            >
              <thead>
                <tr>
                  {beforeLabel && <th scope="col">{beforeLabel}</th>}
                  <th scope="col">Nombre</th>
                  {columns.map((column) => (
                    <th
                      scope="col"
                      key={column.id}
                      className={column.kind === "decimal" ? "is-number" : undefined}
                    >
                      {column.label}
                      {column.unit ? ` · ${column.unit}` : ""}
                    </th>
                  ))}
                  {hasAfter && <th scope="col">{afterLabel}</th>}
                </tr>
              </thead>
              <tbody>
                {visible.map((row, index) => (
                  <tr
                    key={row.id}
                    aria-rowindex={safePage * pageSize + index + 2}
                    data-suggested={row.suggested || undefined}
                  >
                    {beforeLabel && <td>{row.before}</td>}
                    <th scope="row">{row.label}</th>
                    {columns.map((baseColumn, colIndex) => {
                      const column = { ...baseColumn, ...row.cellOptions?.[baseColumn.id] };
                      const key = cellKey(row.id, column.id);
                      const text = drafts[key];
                      const error =
                        (text === undefined ? null : parsed(text, column).error) ?? cellErrors[key];
                      const selected = active?.[0] === row.id && active[1] === column.id;
                      return (
                        <td
                          role="gridcell"
                          key={column.id}
                          className={column.kind === "decimal" ? "is-number" : undefined}
                        >
                          <input
                            aria-label={`${row.label} · ${column.label}`}
                            aria-invalid={error ? true : undefined}
                            aria-describedby={
                              error ? `${id}-${safePage * pageSize + index}-${colIndex}` : undefined
                            }
                            data-cell={key}
                            inputMode={column.kind === "decimal" ? "decimal" : undefined}
                            readOnly={readOnly || saving || column.readOnly}
                            placeholder={readOnly || column.readOnly ? "—" : "Completar"}
                            tabIndex={
                              selected ||
                              (!activeVisible && index === 0 && colIndex === firstEditable)
                                ? 0
                                : -1
                            }
                            value={text ?? shown(row.values[column.id] ?? null, column)}
                            style={
                              column.kind === "decimal"
                                ? {
                                    minWidth: `${Math.max(12, (text ?? row.values[column.id] ?? "").length + 1)}ch`,
                                  }
                                : undefined
                            }
                            onFocus={(event) => {
                              setActive([row.id, column.id]);
                              setEditingText(false);
                              onActiveChange?.(row.id, column.id);
                              event.target.select();
                            }}
                            onDoubleClick={() => setEditingText(true)}
                            onChange={(event) => {
                              setDrafts({ ...draftsRef.current, [key]: event.target.value });
                              setCellErrors({});
                              setFailure("");
                            }}
                            onKeyDown={(event) => {
                              if (event.altKey && event.key === "Enter" && onHistory) {
                                event.preventDefault();
                                onHistory(row.id, column.id);
                              } else keydown(event, safePage * pageSize + index, colIndex);
                            }}
                            onPaste={(event) => {
                              event.preventDefault();
                              paste(event.clipboardData.getData("text/plain"), [row.id, column.id]);
                            }}
                          />
                          {error && (
                            <span
                              className="ui-editable-table__error"
                              id={`${id}-${safePage * pageSize + index}-${colIndex}`}
                              role="alert"
                            >
                              {error}
                            </span>
                          )}
                        </td>
                      );
                    })}
                    {hasAfter && (
                      <td className="ui-editable-table__after">
                        {row.after}
                        {onHistory && (
                          <Button
                            size="compact"
                            variant="ghost"
                            onClick={() =>
                              onHistory(
                                row.id,
                                active?.[0] === row.id ? active[1] : columns[firstEditable]!.id,
                              )
                            }
                            aria-label={`Historial de ${row.label}`}
                          >
                            Historial
                          </Button>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {rows.length > pageSize && (
            <nav className="ui-editable-table__pages" aria-label={`Páginas de ${label}`}>
              <Button
                size="compact"
                disabled={safePage === 0}
                onClick={() => {
                  save();
                  setPage(safePage - 1);
                }}
              >
                Anterior
              </Button>
              <span>
                {safePage * pageSize + 1}–{Math.min((safePage + 1) * pageSize, rows.length)} de{" "}
                {rows.length}
              </span>
              <Button
                size="compact"
                disabled={(safePage + 1) * pageSize >= rows.length}
                onClick={() => {
                  save();
                  setPage(safePage + 1);
                }}
              >
                Siguiente
              </Button>
            </nav>
          )}
        </>
      )}
      {pasteText !== null && (
        <Dialog
          title="Pegar desde Excel"
          onClose={() => setPasteText(null)}
          footer={
            <Button
              variant="primary"
              onClick={() => {
                if (paste(pasteText, active)) setPasteText(null);
              }}
            >
              Pegar bloque
            </Button>
          }
        >
          <label className="ui-editable-table__paste">
            Copia las celdas en Excel y pégalas aquí.
            <textarea
              value={pasteText}
              rows={7}
              onChange={(event) => setPasteText(event.target.value)}
              spellCheck={false}
            />
          </label>
          {pasteError && (
            <p role="alert" className="ui-editable-table__error">
              {pasteError}
            </p>
          )}
        </Dialog>
      )}
    </div>
  );
}
