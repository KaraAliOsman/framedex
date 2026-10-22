import { useMemo, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import {
  catalogSeriesCellHistory,
  catalogSeriesConfirmCells,
  catalogSeriesEditCells,
  catalogSeriesSheet,
} from "../../api/generated/dekopen";
import type { SeriesCell, SeriesSheet } from "../../api/generated/models";
import { ApiError } from "../../api/apiMutator";
import { UnsavedChangesGuard } from "../../app/UnsavedChangesGuard";
import { formatDate, formatDateTime, fmtMm } from "../../format";
import { Button, Dialog, Loading, Tabs } from "../../ui";
import { EditableTable, type TableChange } from "../../ui/EditableTable";
import {
  address,
  bindChanges,
  seriesTabs,
  sheetTables,
  usageLabel,
  type SeriesTab,
  type SheetTable,
} from "./seriesSheetModel";
import "./series-sheet.css";
import { SeriesPricesTable } from "./SeriesPricesTable";
import { sheetValidationError } from "./seriesSheetErrors";

function problem(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 409)
      return "La serie cambió. Revisa los cambios del catálogo y vuelve a guardar.";
    if (error.status === 403)
      return "Tu rol permite consultar esta serie. Pide al dueño o encargado que guarde los cambios.";
    if (error.status === 400) return "Revisa los valores indicados y sus límites antes de guardar.";
  }
  return "No se pudo guardar. Conservamos tus cambios para que vuelvas a intentarlo.";
}

export function CellOrigin({
  cell,
  example = false,
}: {
  cell?: SeriesCell;
  example?: boolean;
}): JSX.Element {
  const page = cell?.source_ref?.match(/(?:pág(?:ina)?\.?|page)\s*(\d+)/i)?.[1];
  const label = example
    ? "Ejemplo"
    : cell?.value === null
      ? "Falta · Completar"
      : cell?.origin === "MANUAL"
        ? `Del manual${page ? ` · pág. ${page}` : ""}`
        : cell?.origin === "WORKSHOP"
          ? `Taller${cell.actor_name ? ` · ${cell.actor_name}` : ""}${cell.set_at ? `, ${formatDate(cell.set_at)}` : ""}`
          : cell?.origin === "SUGGESTED"
            ? "Sugerido"
            : "Por confirmar";
  return (
    <span className="series-origin" data-origin={example ? "EXAMPLE" : (cell?.origin ?? "MISSING")}>
      <span aria-hidden="true" />
      {label}
    </span>
  );
}

export function SeriesSheetView({
  orgId,
  systemId,
  canEdit,
  onBack,
  onChanged,
  onAdvanced,
  onTrial,
  onSetup,
}: {
  orgId: string;
  systemId: string;
  canEdit: boolean;
  onBack: () => void;
  onChanged: (sheet: SeriesSheet) => void;
  onAdvanced: (cell?: SeriesCell) => void;
  onTrial: (sheet: SeriesSheet) => void;
  onSetup?: () => void;
}): JSX.Element {
  const queryClient = useQueryClient();
  const queryKey = ["series-sheet", orgId, systemId];
  const options = { headers: { "X-Organization-ID": orgId } };
  const query = useQuery({
    queryKey,
    queryFn: async ({ signal }) => {
      const response = await catalogSeriesSheet(systemId, { ...options, signal });
      if (response.status !== 200) throw new Error("sheet");
      return response.data;
    },
    // Never replace the revision behind a draft when a tab regains focus.
    refetchOnWindowFocus: false,
  });
  const [tab, setTab] = useState<SeriesTab>("profiles");
  const [dirtyTables, setDirtyTables] = useState<Record<string, boolean>>({});
  const dirty = Object.values(dirtyTables).some(Boolean);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [active, setActive] = useState<Record<string, [string, string]>>({});
  const [focusRequest, setFocusRequest] = useState<{
    table: string;
    rowId: string;
    columnId: string;
  } | null>(null);
  const [historyCell, setHistoryCell] = useState<SeriesCell | null>(null);
  const lock = useRef(false);
  const sheet = query.data;
  const tables = useMemo(() => (sheet ? sheetTables(sheet, tab) : []), [sheet, tab]);
  const history = useQuery({
    queryKey: [
      "series-cell-history",
      orgId,
      systemId,
      historyCell && address(historyCell),
      sheet?.revision,
    ],
    enabled: historyCell !== null,
    queryFn: async ({ signal }) => {
      const { resource, row_id, field } = historyCell!;
      const response = await catalogSeriesCellHistory(
        systemId,
        { resource, row_id, field },
        {
          ...options,
          signal,
        },
      );
      if (response.status !== 200) throw new Error("history");
      return response.data.items;
    },
  });

  function accept(next: SeriesSheet) {
    queryClient.setQueryData(queryKey, next);
    onChanged(next);
  }

  async function save(table: SheetTable, changes: TableChange[]) {
    if (!sheet || lock.current) throw new Error("Espera a que termine el guardado actual.");
    lock.current = true;
    setBusy(true);
    setFailure("");
    try {
      const response = await catalogSeriesEditCells(
        systemId,
        {
          revision: sheet.revision,
          changes: bindChanges(table, changes),
        },
        options,
      );
      if (response.status !== 200) throw new Error("save");
      accept(response.data);
    } catch (error) {
      const validation = sheetValidationError(error, table);
      if (validation) throw validation;
      const message = problem(error);
      setFailure(message);
      throw new Error(message);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }

  async function confirm(cells: SeriesCell[]) {
    if (!sheet || lock.current || dirty || !cells.length) return;
    lock.current = true;
    setBusy(true);
    setFailure("");
    try {
      const response = await catalogSeriesConfirmCells(
        systemId,
        {
          revision: sheet.revision,
          cells: cells.map(({ resource, row_id, field }) => ({ resource, row_id, field })),
        },
        options,
      );
      if (response.status !== 200) throw new Error("confirm");
      accept(response.data);
      setSelected(new Set());
    } catch (error) {
      setFailure(problem(error));
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }

  function goFirst() {
    if (!sheet) return;
    const first = sheet.cells.find((cell) => cell.origin === "SUGGESTED");
    if (!first) {
      onTrial(sheet);
      return;
    }
    for (const item of seriesTabs) {
      for (const table of sheetTables(sheet, item.id)) {
        for (const [rowId, columns] of Object.entries(table.bindings)) {
          const match = Object.entries(columns).find(
            ([, binding]) => address(binding.cell) === address(first),
          );
          if (match) {
            setTab(item.id);
            setFocusRequest({ table: table.id, rowId, columnId: match[0] });
            return;
          }
        }
      }
    }
    onAdvanced(first);
  }

  if (query.isPending) return <Loading label="Cargando la serie" />;
  if (!sheet)
    return (
      <div>
        <p role="alert">No se pudo abrir la serie.</p>
        <Button onClick={() => void query.refetch()}>Volver a intentar</Button>
      </div>
    );
  const system = sheet.tabs.rules;
  const writable = canEdit && !system.read_only && !sheet.usage.is_example;
  const suggested = sheet.cells.filter((cell) => cell.origin === "SUGGESTED");
  const needsVerification = !sheet.usage.verified;
  const emptyHistory = !history.data?.length;
  return (
    <section className="series-sheet" aria-label={`Ficha de ${system.name}`}>
      <UnsavedChangesGuard dirty={dirty || busy} message="Hay cambios de la serie por guardar" />
      <Button
        variant="ghost"
        className="series-sheet__back"
        disabled={dirty || busy}
        onClick={onBack}
      >
        ‹ Catálogo
      </Button>
      <header className="series-sheet__header">
        <span className="series-sheet__monogram" aria-hidden="true">
          {(system.manufacturer || system.name).slice(0, 7).toLocaleUpperCase("es-CL")}
        </span>
        <div className="series-sheet__identity">
          <p>{system.manufacturer || "Tu taller"}</p>
          <h1>{system.name}</h1>
          <p>
            {system.material === "PVC" ? "PVC" : "Aluminio"} · {fmtMm(system.depth_mm)} mm
          </p>
        </div>
        <span className="series-sheet__level">{usageLabel(sheet.usage)}</span>
        {writable && onSetup && (
          <Button disabled={dirty || busy} onClick={onSetup}>
            Continuar alta
          </Button>
        )}
        <Button variant="primary" disabled={dirty || busy} onClick={() => onTrial(sheet)}>
          Ventana de prueba
        </Button>
      </header>
      {sheet.usage.is_example ? (
        <p className="series-sheet__notice">
          Valores sintéticos para aprender. Prepara tu propia serie antes de cotizar un trabajo
          real.
        </p>
      ) : suggested.length > 0 ? (
        <div className="series-sheet__pending" role="status">
          <strong>
            {suggested.length}{" "}
            {suggested.length === 1
              ? "valor sugerido por confirmar"
              : "valores sugeridos por confirmar"}{" "}
            antes de fabricar
          </strong>
          <Button size="compact" disabled={dirty || busy} onClick={goFirst}>
            Ir al primero
          </Button>
        </div>
      ) : needsVerification ? (
        <div className="series-sheet__pending" role="status">
          <strong>Verifica una ventana de prueba antes de fabricar.</strong>
        </div>
      ) : null}
      <Tabs
        label="Secciones de la serie"
        items={seriesTabs.map((item) => ({ ...item, disabled: dirty || busy }))}
        value={tab}
        onChange={(id) => {
          setTab(id as SeriesTab);
          setSelected(new Set());
        }}
      />
      <div className="series-sheet__tools">
        <div className="series-sheet__legend">
          <span className="series-origin" data-origin="MANUAL">
            <span aria-hidden="true" />
            Del manual
          </span>
          <span className="series-origin" data-origin="WORKSHOP">
            <span aria-hidden="true" />
            Del taller
          </span>
          <span className="series-origin" data-origin="SUGGESTED">
            <span aria-hidden="true" />
            Sugerido · confírmalo
          </span>
        </div>
        <Button size="compact" disabled={dirty || busy} onClick={() => onAdvanced()}>
          Más ajustes de la serie
        </Button>
        {writable && selected.size > 0 && (
          <Button
            size="compact"
            disabled={dirty || busy}
            onClick={() => void confirm(suggested.filter((cell) => selected.has(address(cell))))}
          >
            Confirmar {selected.size} valores
          </Button>
        )}
      </div>
      {failure && (
        <div>
          <p role="alert">{failure}</p>
          <Button size="compact" onClick={() => void query.refetch()}>
            Revisar cambios del catálogo
          </Button>
        </div>
      )}
      {tables.map((table) => (
        <div key={table.id} className="series-sheet__table">
          {tables.length > 1 && <h2>{table.label}</h2>}
          <EditableTable
            label={table.label}
            columns={table.columns}
            readOnly={!writable || busy}
            beforeLabel={writable ? "Elegir" : undefined}
            rows={table.rows.map((row) => {
              const bindings = table.bindings[row.id] ?? {};
              const pending = [
                ...new Map(
                  Object.values(bindings).map(({ cell }) => [address(cell), cell]),
                ).values(),
              ].filter((cell) => cell.origin === "SUGGESTED");
              const focused = active[table.id];
              const field =
                focused?.[0] === row.id
                  ? focused[1]
                  : Object.keys(bindings).find(
                      (key) => !table.columns.find((column) => column.id === key)?.readOnly,
                    );
              const cell = field ? bindings[field]?.cell : undefined;
              return {
                ...row,
                suggested: pending.length > 0,
                before:
                  pending.length > 0 ? (
                    <input
                      type="checkbox"
                      aria-label={`Elegir sugeridos de ${row.label}`}
                      checked={pending.every((item) => selected.has(address(item)))}
                      disabled={dirty || busy}
                      onChange={(event) =>
                        setSelected((current) => {
                          const next = new Set(current);
                          for (const item of pending) {
                            if (event.target.checked) next.add(address(item));
                            else next.delete(address(item));
                          }
                          return next;
                        })
                      }
                    />
                  ) : null,
                after: (
                  <>
                    <CellOrigin cell={cell} example={sheet.usage.is_example} />
                    {cell?.origin === "SUGGESTED" && writable && (
                      <Button
                        size="compact"
                        disabled={dirty || busy}
                        onClick={() => void confirm([cell])}
                      >
                        Confirmar
                      </Button>
                    )}
                  </>
                ),
              };
            })}
            onSave={(changes) => save(table, changes)}
            onDirtyChange={(value) =>
              setDirtyTables((current) =>
                current[table.id] === value ? current : { ...current, [table.id]: value },
              )
            }
            focusRequest={focusRequest?.table === table.id ? focusRequest : null}
            onActiveChange={(row, column) =>
              setActive((current) => ({ ...current, [table.id]: [row, column] }))
            }
            onHistory={(row, column) => {
              const cell = table.bindings[row]?.[column]?.cell;
              if (cell) setHistoryCell(cell);
            }}
          />
        </div>
      ))}
      {tab === "prices" && (
        <SeriesPricesTable
          orgId={orgId}
          sheet={sheet}
          onSaved={accept}
          onDirtyChange={(value) =>
            setDirtyTables((current) =>
              current.prices === value ? current : { ...current, prices: value },
            )
          }
        />
      )}
      {historyCell && (
        <Dialog title="Historial de la celda" onClose={() => setHistoryCell(null)}>
          <CellOrigin cell={historyCell} example={sheet.usage.is_example} />
          {history.isPending ? (
            <Loading label="Cargando el historial" />
          ) : history.isError ? (
            <p role="alert">No se pudo cargar el historial. Cierra y vuelve a abrir la celda.</p>
          ) : emptyHistory ? (
            <p>Este valor todavía no tiene cambios registrados.</p>
          ) : (
            <ol className="series-sheet__history">
              {history.data.map((entry) => (
                <li key={entry.id}>
                  <strong>{entry.value?.replace(".", ",") ?? "Vacío"}</strong>
                  <p>Anterior: {entry.previous_value?.replace(".", ",") ?? "Vacío"}</p>
                  <p>{formatDateTime(entry.set_at)}</p>
                  {entry.actor_name && <p>{entry.actor_name}</p>}
                  <p>{entry.source_ref}</p>
                </li>
              ))}
            </ol>
          )}
        </Dialog>
      )}
    </section>
  );
}
