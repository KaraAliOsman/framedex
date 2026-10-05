import { type ReactNode, useLayoutEffect, useMemo, useRef, useState } from "react";
import { compareDecimal, formatDecimal } from "../decimal";
import { Button, TextInput } from "./Controls";
import { BlockedState, DeniedState, EmptyState, ErrorState, LoadingState } from "./States";

export type TableColumn<Row> = {
  id: string;
  label: string;
  value: (row: Row) => string | number | null | undefined;
  render?: (row: Row) => ReactNode;
  numeric?: boolean;
  unit?: string;
  sortable?: boolean;
};
export type TableState =
  | { kind: "ready" }
  | { kind: "loading" }
  | { kind: "error"; cause: string; retry: () => void; technical?: string }
  | { kind: "denied"; role: string; contact: string }
  | { kind: "blocked"; cause: string; action: ReactNode };

export function DataTable<Row>({
  rows,
  columns,
  rowKey,
  label,
  state = { kind: "ready" },
  emptyReason,
  emptyAction,
  selectionActions,
  onSelectionChange,
  filterable = true,
}: {
  rows: readonly Row[];
  columns: readonly TableColumn<Row>[];
  rowKey: (row: Row) => string;
  label: string;
  state?: TableState;
  emptyReason: string;
  emptyAction?: ReactNode;
  selectionActions?: (ids: readonly string[]) => ReactNode;
  onSelectionChange?: (ids: readonly string[]) => void;
  filterable?: boolean;
}): JSX.Element {
  const [filter, setFilter] = useState("");
  const [sort, setSort] = useState<{ id: string; descending: boolean } | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [scroll, setScroll] = useState(0);
  const [rowHeight, setRowHeight] = useState(32);
  const viewport = useRef<HTMLDivElement>(null);
  const collator = useMemo(
    () => new Intl.Collator("es-CL", { numeric: true, sensitivity: "base" }),
    [],
  );
  const data = useMemo(() => {
    const candidates = rows.filter((row) =>
      columns.some((column) =>
        String(column.value(row) ?? "")
          .toLocaleLowerCase("es-CL")
          .includes(filter.toLocaleLowerCase("es-CL")),
      ),
    );
    const column = columns.find((entry) => entry.id === sort?.id);
    return column
      ? candidates.sort((a, b) => {
          const av = column.value(a),
            bv = column.value(b);
          const order =
            av == null && bv == null
              ? 0
              : av == null
                ? 1
                : bv == null
                  ? -1
                  : column.numeric
                    ? compareDecimal(String(av), String(bv))
                    : collator.compare(String(av), String(bv));
          return order * (sort?.descending ? -1 : 1);
        })
      : candidates;
  }, [rows, columns, sort, filter, collator]);
  const virtual = data.length > 200;
  useLayoutEffect(() => {
    const row = viewport.current?.querySelector("tbody tr:not([aria-hidden])");
    if (!row) return;
    const measure = () => {
      const height = row.getBoundingClientRect().height;
      if (height > 0) setRowHeight(height);
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(row);
    return () => observer.disconnect();
  }, [virtual, data.length, state.kind]);
  const viewportHeight = viewport.current?.clientHeight || 448;
  const first = virtual ? Math.max(0, Math.floor(scroll / rowHeight) - 8) : 0;
  const last = virtual
    ? Math.min(data.length, first + Math.ceil(viewportHeight / rowHeight) + 16)
    : data.length;
  const visibleIds = new Set(rows.map(rowKey));
  const selectedIds = Array.from(selected).filter((id) => visibleIds.has(id));
  function resetScroll(): void {
    setScroll(0);
    if (viewport.current) viewport.current.scrollTop = 0;
  }
  function select(ids: Set<string>): void {
    setSelected(ids);
    onSelectionChange?.(Array.from(ids));
  }
  if (state.kind === "loading")
    return (
      <LoadingState
        label={`Cargando ${label}`}
        shape={
          <table className="ui-data-table" aria-hidden>
            <tbody>
              {Array.from({ length: 5 }, (_, index) => (
                <tr key={index}>
                  {columns.map((column) => (
                    <td key={column.id}>
                      <span className="ui-skeleton__line" />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        }
      />
    );
  if (state.kind === "error")
    return (
      <ErrorState
        title={`No se pudo cargar ${label}`}
        body={state.cause}
        onRetry={state.retry}
        technical={state.technical}
      />
    );
  if (state.kind === "denied")
    return (
      <DeniedState
        reason={`Esta tabla requiere el rol ${state.role}. Pídelo a ${state.contact}.`}
      />
    );
  if (state.kind === "blocked") return <BlockedState reason={state.cause} action={state.action} />;
  if (!rows.length)
    return <EmptyState title={`Todavía no hay ${label}`} body={emptyReason} action={emptyAction} />;
  return (
    <section className="ui-table-region" data-region={`tabla-${label}`} aria-label={label}>
      {filterable ? (
        <TextInput
          aria-label={`Filtrar ${label}`}
          placeholder="Filtrar…"
          value={filter}
          onChange={(event) => {
            setFilter(event.target.value);
            resetScroll();
          }}
        />
      ) : null}
      {selectedIds.length ? (
        <div className="ui-table-selection" role="status">
          <span>{formatDecimal(selectedIds.length)} seleccionadas</span>
          {selectionActions?.(selectedIds)}
          <Button variant="ghost" onClick={() => select(new Set())}>
            Limpiar selección
          </Button>
        </div>
      ) : null}
      <div
        ref={viewport}
        className={`ui-table-scroll ${virtual ? "is-virtual" : ""}`}
        onScroll={(event) => setScroll(event.currentTarget.scrollTop)}
      >
        <table className="ui-data-table" aria-label={label} aria-rowcount={data.length + 1}>
          <thead>
            <tr>
              {selectionActions ? (
                <th scope="col">
                  <input
                    type="checkbox"
                    aria-label={`Seleccionar todas las ${label} filtradas`}
                    checked={data.length > 0 && data.every((row) => selected.has(rowKey(row)))}
                    onChange={(event) =>
                      select(event.target.checked ? new Set(data.map(rowKey)) : new Set())
                    }
                  />
                </th>
              ) : null}
              {columns.map((column) => (
                <th
                  key={column.id}
                  scope="col"
                  className={column.numeric ? "is-numeric" : ""}
                  aria-sort={
                    sort?.id === column.id ? (sort.descending ? "descending" : "ascending") : "none"
                  }
                >
                  {column.sortable === false ? (
                    column.label
                  ) : (
                    <button
                      type="button"
                      onClick={() => {
                        resetScroll();
                        setSort({
                          id: column.id,
                          descending: sort?.id === column.id ? !sort.descending : false,
                        });
                      }}
                    >
                      {column.label}
                      {sort?.id === column.id ? (
                        <span aria-hidden>{sort.descending ? " ↓" : " ↑"}</span>
                      ) : null}
                    </button>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {first ? (
              <tr aria-hidden>
                <td
                  colSpan={columns.length + (selectionActions ? 1 : 0)}
                  style={{ height: first * rowHeight, padding: 0, border: 0 }}
                />
              </tr>
            ) : null}
            {data.slice(first, last).map((row, index) => (
              <tr
                key={rowKey(row)}
                aria-rowindex={first + index + 2}
                data-selected={selected.has(rowKey(row)) || undefined}
              >
                {selectionActions ? (
                  <td>
                    <input
                      type="checkbox"
                      aria-label={`Seleccionar fila ${first + index + 1}`}
                      checked={selected.has(rowKey(row))}
                      onChange={(event) => {
                        const next = new Set(selectedIds);
                        if (event.target.checked) next.add(rowKey(row));
                        else next.delete(rowKey(row));
                        select(next);
                      }}
                    />
                  </td>
                ) : null}
                {columns.map((column) => (
                  <td key={column.id} className={column.numeric ? "is-numeric ui-value" : ""}>
                    {column.render
                      ? column.render(row)
                      : column.numeric
                        ? formatDecimal(column.value(row))
                        : (column.value(row) ?? "Sin dato")}
                    {column.unit ? <span className="ui-value__unit"> {column.unit}</span> : null}
                  </td>
                ))}
              </tr>
            ))}
            {last < data.length ? (
              <tr aria-hidden>
                <td
                  colSpan={columns.length + (selectionActions ? 1 : 0)}
                  style={{ height: (data.length - last) * rowHeight, padding: 0, border: 0 }}
                />
              </tr>
            ) : null}
          </tbody>
        </table>
        {data.length === 0 ? (
          <EmptyState
            title="Sin coincidencias"
            body="Prueba con otro código o nombre."
            action={<Button onClick={() => setFilter("")}>Limpiar filtro</Button>}
          />
        ) : null}
      </div>
    </section>
  );
}
