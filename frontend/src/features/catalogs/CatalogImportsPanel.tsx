import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, apiFetchBlob } from "../../api/apiMutator";
import {
  catalogImportPublish,
  catalogImportReview,
  catalogImportTimeline,
  catalogImportUndo,
  catalogImportsCreate,
  catalogImportsList,
  catalogTemplateSchema,
} from "../../api/generated/dekopen";
import type {
  CatalogImportResponse,
  CatalogReviewResponse,
  CatalogTemplateColumn,
  CatalogTemplateSheet,
  CatalogImportTimeline,
} from "../../api/generated/models";
import { UnsavedChangesGuard } from "../../app/UnsavedChangesGuard";
import { formatDate, formatDateTime, formatDecimal, fmtMm, formatMoney } from "../../format";
import { domainLabel } from "../../i18n/domainLabels";
import { useConfirm } from "../../ui/ConfirmDialog";
import { OpeningCapabilitiesEditor, type PairedRule } from "./OpeningCapabilitiesEditor";
import { ExtraAuthorityEditor } from "../projects/ExtraDefinitionEditor";
import type { ExtraAuthority } from "../projects/extraModel";
import { FinishAuthorityEditor } from "./FinishAuthorityEditor";
import type { FinishAuthority } from "../../api/generated/models";
import { physicalLabel, type Capability } from "../canvas/physicalOpenings";
import { SourceHighlight } from "./CatalogProvenance";
import { ImportedSectionFields } from "./ImportedSectionFields";

type Evidence = {
  ref?: string;
  quote?: string;
  literal?: string;
  confidence?: string;
  proposed?: unknown;
};
type ReviewRow = {
  key: string;
  sheet: string;
  row: number;
  method: string;
  confidence: string;
  include: boolean;
  values: Record<string, unknown>;
  fields: Record<string, Evidence>;
  errors: Array<{ field: string; message: string }>;
};
const STATUS: Record<string, string> = {
  UPLOADED: "En cola",
  EXTRACTING: "Analizando fuente",
  REVIEW_READY: "Requiere revisión",
  CONFIRMED: "Publicado",
  UNDONE: "Publicación deshecha",
  FAILED: "No se pudo analizar",
};
const WARNINGS: Record<string, string> = {
  "catalog.no_candidates":
    "No se encontraron filas. Usa la plantilla oficial o una fuente con texto legible.",
  "catalog.source_parse_failed":
    "No se pudo leer el texto. Sube una fuente legible para verificar sus valores.",
  "catalog.candidates_capped":
    "La fuente excede 2 000 filas. Divide el archivo para revisar el resto.",
};
function inputText(value: unknown): string {
  if (value == null) return "";
  if (Array.isArray(value)) return value.join("|") || "[]";
  if (typeof value === "boolean") return value ? "Sí" : "No";
  return String(value);
}
function errorText(error: unknown): string {
  if (error instanceof ApiError) {
    const detail = (error.payload as { error?: { detail?: string } })?.error?.detail;
    if (detail && !/^[a-z_]+[.][a-z_.]+$/.test(detail)) return detail;
    if (error.status === 403)
      return "Tu rol no puede publicar esta información. Pide revisión al dueño o encargado de taller.";
    if (error.status === 409) return "El catálogo cambió. Actualiza el diff antes de publicar.";
  }
  return "No se pudo completar la acción. Conservamos la revisión; intenta de nuevo.";
}
function display(value: unknown, column?: CatalogTemplateColumn, field?: string): string {
  if (value == null || value === "") return "Sin dato";
  if ((field ?? column?.key) === "finish_authority" && typeof value === "object") {
    const chart = value as FinishAuthority;
    return `${chart.colors?.length ?? 0} muestras · ${chart.combinations?.length ?? 0} combinaciones · ${chart.source ?? "Fuente sin dato"}`;
  }
  if (field === "opening_capabilities" && Array.isArray(value))
    return (
      (value as Capability[])
        .map(
          (cap) =>
            `${cap.hinge_sides.map((hinge_side) => physicalLabel({ ...cap, hinge_side }, cap.use)).join(" / ")}${cap.leaf_role === "SINGLE" ? "" : ` · ${domainLabel(cap.leaf_role)}`} · ${cap.source}`,
        )
        .join("; ") || "Sin dato"
    );
  if (field === "paired_leaf_rule" && typeof value === "object") {
    const rule = value as PairedRule;
    return `Traslape ${fmtMm(rule.meeting_overlap_mm)} mm · separación ${fmtMm(rule.meeting_gap_mm)} mm · descuento del inversor ${fmtMm(rule.inversor_end_deduction_mm)} mm · ${rule.source}`;
  }
  if (typeof value === "object")
    return Array.isArray(value)
      ? value.map((item) => (typeof item === "string" ? item : "Componente declarado")).join(" · ")
      : "Regla declarada";
  if (typeof value === "boolean") return value ? "Sí" : "No";
  if (column?.choices?.[String(value)]) return String(column.choices[String(value)]);
  const labels: Record<string, string> = {
    BAR: "Barra",
    M: "Metro",
    M2: "Metro cuadrado",
    KIT: "Kit",
    EA: "Unidad",
    UNIT: "Unidad",
    unit: "Unidad",
    pair: "Par",
    kit: "Kit",
    m: "Metro",
    PROFILE: "Perfil",
    GLASS: "Vidrio",
    HARDWARE: "Herraje",
    REINFORCEMENT: "Refuerzo",
    ACCESSORY: "Accesorio",
    CONSUMABLE: "Consumible",
  };
  const label = labels[String(value)];
  if (label) return label;
  if (field === "category") return domainLabel(String(value));
  if (column?.kind === "date") return formatDate(String(value));
  if (column?.key === "unit_cost") return formatMoney(String(value));
  if ((column?.key ?? field ?? "").startsWith("weight_")) return formatDecimal(String(value), 2);
  if (["decimal", "positive", "integer", "count", "angle"].includes(column?.kind ?? ""))
    return fmtMm(String(value));
  return String(value);
}
function typedRow(raw: Record<string, unknown>): ReviewRow | null {
  if (!raw.sheet || !raw.values || typeof raw.values !== "object") return null;
  return {
    key: String(raw.key),
    sheet: String(raw.sheet),
    row: Number(raw.row),
    method: String(raw.method),
    confidence: String(raw.confidence ?? "REVIEW_REQUIRED"),
    values: { ...(raw.values as Record<string, unknown>) },
    fields: (raw.fields ?? {}) as ReviewRow["fields"],
    errors: (raw.errors ?? []) as ReviewRow["errors"],
    include:
      raw.confidence === "HIGH_CANDIDATE" &&
      !Object.values((raw.fields ?? {}) as Record<string, Evidence>).some(
        (field) => field.confidence === "LOW",
      ),
  };
}
export function CatalogImportsPanel({
  orgId,
  canWrite,
  onConfirmed,
  onExpandedChange,
}: {
  orgId: string;
  canWrite: boolean;
  systems: Array<{ id: string; name: string; code: string }>;
  onConfirmed?: () => void;
  onExpandedChange?: (expanded: boolean) => void;
}): JSX.Element {
  const confirm = useConfirm();
  const requestedImport = useRef(new URLSearchParams(window.location.search).get("import"));
  const [expanded, setExpanded] = useState(!!requestedImport.current);
  useEffect(() => onExpandedChange?.(expanded), [expanded, onExpandedChange]);
  const [imports, setImports] = useState<CatalogImportResponse[]>([]);
  const [sheets, setSheets] = useState<CatalogTemplateSheet[]>([]);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [paste, setPaste] = useState("");
  const [reviewId, setReviewId] = useState<string | null>(null);
  const [rows, setRows] = useState<ReviewRow[]>([]);
  const [sheetName, setSheetName] = useState("Sistemas");
  const [rowKey, setRowKey] = useState("");
  const [diff, setDiff] = useState<CatalogReviewResponse | null>(null);
  const [reviewed, setReviewed] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [timeline, setTimeline] = useState<CatalogImportTimeline | null>(null);
  const [timelineError, setTimelineError] = useState("");
  const [timelineReload, setTimelineReload] = useState(0);
  const mounted = useRef(true);
  const generation = useRef(0);
  const fileInput = useRef<HTMLInputElement>(null);
  const options = { headers: { "X-Organization-ID": orgId } };
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const load = useCallback(async () => {
    const version = ++generation.current;
    setLoading(true);
    try {
      const response = await catalogImportsList({ headers: { "X-Organization-ID": orgId } });
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      if (mounted.current && version === generation.current) setImports(response.data.imports);
    } catch (error) {
      if (mounted.current && version === generation.current) setMessage(errorText(error));
    } finally {
      if (mounted.current && version === generation.current) setLoading(false);
    }
  }, [orgId]);
  useEffect(() => {
    if (!expanded) return;
    void load();
    const controller = new AbortController();
    void catalogTemplateSchema({
      headers: { "X-Organization-ID": orgId },
      signal: controller.signal,
    })
      .then((response) => {
        if (response.status === 200) setSheets(response.data.sheets);
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setMessage("No se pudo cargar la plantilla. Vuelve a abrir Importar catálogo.");
      });
    return () => controller.abort();
  }, [expanded, load, orgId]);
  useEffect(() => {
    if (!imports.some((entry) => ["UPLOADED", "EXTRACTING"].includes(entry.status))) return;
    const timer = window.setTimeout(() => void load(), 2500);
    return () => window.clearTimeout(timer);
  }, [imports, load]);
  useEffect(() => {
    const wanted = imports.find((item) => item.id === requestedImport.current);
    if (wanted) {
      requestedImport.current = null;
      const candidates = wanted.candidates
        .map(typedRow)
        .filter((row): row is ReviewRow => row !== null);
      setReviewId(wanted.id);
      setRows(candidates);
      setSheetName(candidates[0]?.sheet ?? "Sistemas");
      setRowKey(candidates[0]?.key ?? "");
    }
    // A deep link opens once; subsequent list refreshes preserve local edits.
  }, [imports]);
  useEffect(() => {
    if (!reviewId) return;
    const controller = new AbortController();
    setTimeline(null);
    setTimelineError("");
    void catalogImportTimeline(reviewId, {
      headers: { "X-Organization-ID": orgId },
      signal: controller.signal,
    })
      .then((result) => {
        if (result.status === 200 && !controller.signal.aborted) setTimeline(result.data);
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setTimelineError("No se pudo cargar el historial. Reintenta para revisar la auditoría.");
      });
    return () => controller.abort();
  }, [reviewId, orgId, timelineReload]);
  async function download(url: string): Promise<void> {
    setBusy(true);
    setMessage("");
    try {
      const result = await apiFetchBlob(url);
      const local = URL.createObjectURL(result.blob);
      const anchor = document.createElement("a");
      anchor.href = local;
      anchor.download = result.filename ?? "catalogo.csv";
      anchor.click();
      window.setTimeout(() => URL.revokeObjectURL(local), 1000);
    } catch (error) {
      setMessage(errorText(error));
    } finally {
      setBusy(false);
    }
  }
  async function upload(file: File): Promise<void> {
    setBusy(true);
    setMessage("");
    try {
      const response = await catalogImportsCreate({ file }, options);
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      setPaste("");
      await load();
      setMessage(
        "Archivo recibido. La extracción aparecerá aquí para que revises su fuente y sus cambios.",
      );
    } catch (error) {
      setMessage(errorText(error));
    } finally {
      setBusy(false);
    }
  }
  async function openReview(entry: CatalogImportResponse): Promise<void> {
    if (dirty && !(await confirm({ title: "¿Descartar los cambios de esta revisión?" }))) return;
    const candidates = entry.candidates
      .map(typedRow)
      .filter((row): row is ReviewRow => row !== null);
    if (!candidates.length) {
      setMessage(
        "Esta importación no tiene filas de la plantilla vigente. Sube nuevamente el archivo para revisar sus hojas.",
      );
      return;
    }
    const first = candidates[0];
    if (!first) return;
    setReviewId(entry.id);
    setRows(candidates);
    setSheetName(first.sheet);
    setRowKey(first.key);
    setDiff(null);
    setReviewed(false);
    setDirty(false);
    setMessage("");
  }
  function patch(key: string, field: string, value: unknown): void {
    setRows((current) =>
      current.map((row) =>
        row.key === key
          ? {
              ...row,
              values: {
                ...row.values,
                [field]: value,
                ...(field === "finish_authority" && value
                  ? { finishes: (value as FinishAuthority).combinations.map((c) => c.code) }
                  : {}),
              },
            }
          : row,
      ),
    );
    setDiff(null);
    setReviewed(false);
    setDirty(true);
  }
  const items = () =>
    rows.filter((row) => row.include).map((row) => ({ key: row.key, values: row.values }));
  async function preview(): Promise<void> {
    if (!reviewId) return;
    setBusy(true);
    setMessage("");
    setReviewed(false);
    try {
      const response = await catalogImportReview(reviewId, { items: items() }, options);
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      setDiff(response.data);
      setTimelineReload((value) => value + 1);
      if (response.data.errors.length)
        setMessage(
          "Corrige los campos indicados o excluye sus filas. La publicación está bloqueada.",
        );
    } catch (error) {
      setMessage(errorText(error));
    } finally {
      setBusy(false);
    }
  }
  async function publish(): Promise<void> {
    if (!reviewId || !diff || diff.errors.length || !reviewed) return;
    setBusy(true);
    setMessage("");
    try {
      const response = await catalogImportPublish(
        reviewId,
        { items: items(), review_token: diff.review_token, reviewed: true },
        options,
      );
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      if (response.data.errors.length) {
        setDiff({
          ...diff,
          errors: response.data.errors as unknown as CatalogReviewResponse["errors"],
        });
        setMessage("Corrige la revisión antes de publicar.");
        return;
      }
      setReviewId(null);
      setDirty(false);
      setDiff(null);
      await load();
      onConfirmed?.();
      setMessage(
        `Publicación completa: ${response.data.created.length} cambios con fuente y revisor. Puedes deshacerla desde el historial.`,
      );
    } catch (error) {
      setDiff(null);
      setReviewed(false);
      setMessage(errorText(error));
    } finally {
      setBusy(false);
    }
  }
  async function undo(entry: CatalogImportResponse): Promise<void> {
    if (
      !(await confirm({
        title: "¿Deshacer esta publicación?",
        body: "Se restaurará el catálogo anterior si todavía no se usa en productos ni tiene cambios posteriores.",
        confirmLabel: "Deshacer publicación",
        danger: true,
      }))
    )
      return;
    setBusy(true);
    setMessage("");
    try {
      const response = await catalogImportUndo(entry.id, { confirmed: true }, options);
      if (response.status !== 200) throw new ApiError(response.status, response.data);
      await load();
      onConfirmed?.();
      setMessage("Publicación deshecha. La fuente y la revisión quedan en el historial.");
      setTimelineReload((value) => value + 1);
    } catch (error) {
      setMessage(errorText(error));
    } finally {
      setBusy(false);
    }
  }
  async function close(): Promise<void> {
    if (dirty && !(await confirm({ title: "¿Descartar los cambios de esta revisión?" }))) return;
    setReviewId(null);
    setDirty(false);
    setDiff(null);
  }
  const entry = imports.find((item) => item.id === reviewId);
  const selected = rows.find((row) => row.key === rowKey);
  const sheet = sheets.find((item) => item.name === sheetName);
  const canReview = canWrite && entry?.status === "REVIEW_READY";

  if (!expanded)
    return (
      <section className="catalog-ingest">
        <button type="button" aria-expanded="false" onClick={() => setExpanded(true)}>
          Importar catálogo
        </button>
      </section>
    );
  return (
    <section className="catalog-ingest" aria-label="Importar catálogo" aria-busy={busy}>
      <UnsavedChangesGuard
        dirty={dirty || paste.trim().length > 0}
        message="Hay cambios de catálogo sin publicar."
      />
      <header className="catalog-toolbar">
        <h3>Importar catálogo</h3>
        <button
          type="button"
          disabled={busy || dirty || !!paste.trim()}
          onClick={() => setExpanded(false)}
        >
          Cerrar importador
        </button>
      </header>
      <p>
        Sube los datos del proveedor. La plantilla y la IA llegan a la misma revisión: compara la
        fuente, corrige lo dudoso y publica con tu visto bueno.
      </p>
      {!canWrite && (
        <p role="status">
          Puedes consultar las importaciones. Para cargar y publicar datos necesitas el rol de dueño
          o encargado de taller.
        </p>
      )}
      {canWrite && (
        <div className="catalog-ingest-methods">
          <div>
            <h4>Con plantilla</h4>
            <p>
              Hojas para sistemas, perfiles, corte, refuerzos, límites, colores, vidrios, herrajes y
              costos. Una celda vacía queda como Sin dato.
            </p>
            <div className="catalog-toolbar">
              <button
                type="button"
                disabled={busy}
                onClick={() => void download("/api/v1/catalog-imports/template/?format=xlsx")}
              >
                Descargar plantilla XLSX
              </button>
              <label>
                Hoja CSV
                <select value={sheetName} onChange={(event) => setSheetName(event.target.value)}>
                  {sheets.map((item) => (
                    <option key={item.name}>{item.name}</option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                disabled={busy || !sheets.length}
                onClick={() =>
                  void download(
                    `/api/v1/catalog-imports/template/?format=csv&sheet=${encodeURIComponent(sheetName)}`,
                  )
                }
              >
                Descargar CSV
              </button>
            </div>
          </div>
          <div>
            <h4>Con tus archivos e IA</h4>
            <p>
              PDF, planilla, correo, texto o foto. La IA propone lecturas con su fuente. Una foto o
              un escaneo sin texto verificable requiere tu revisión y queda desmarcado.
            </p>
            <div
              className={`catalog-dropzone${dragging ? " is-dragging" : ""}`}
              onDragOver={(event) => {
                event.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(event) => {
                event.preventDefault();
                setDragging(false);
                const file = event.dataTransfer.files[0];
                if (file && !busy) void upload(file);
              }}
            >
              <input
                ref={fileInput}
                type="file"
                className="imports-file-input"
                accept=".pdf,.xlsx,.xlsm,.csv,.txt,.eml,.png,.jpg,.jpeg,.webp"
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  event.target.value = "";
                  if (file) void upload(file);
                }}
              />
              <button type="button" disabled={busy} onClick={() => fileInput.current?.click()}>
                {busy ? "Procesando archivo…" : "Elegir o arrastrar archivo"}
              </button>
              <span>Hasta 15 MB</span>
            </div>
            <details>
              <summary>Pegar texto del proveedor</summary>
              <label>
                Texto de origen
                <textarea
                  value={paste}
                  onChange={(event) => setPaste(event.target.value)}
                  rows={4}
                />
              </label>
              <button
                type="button"
                disabled={busy || !paste.trim()}
                onClick={() =>
                  void upload(new File([paste], "texto-proveedor.txt", { type: "text/plain" }))
                }
              >
                Analizar texto
              </button>
            </details>
          </div>
        </div>
      )}
      {message && (
        <p className="catalog-ingest-message" role="status">
          {message}
        </p>
      )}
      {loading && imports.length === 0 && <p role="status">Cargando importaciones…</p>}
      {!loading && !imports.length && (
        <p>
          Tu catálogo todavía no tiene importaciones. Descarga la plantilla o sube una ficha para
          comenzar.
        </p>
      )}
      <div className="catalog-import-history">
        {imports.map((item) => (
          <div key={item.id} className="catalog-import-entry">
            <div>
              <strong>{item.file_name}</strong>
              <span>
                {STATUS[item.status] ?? "Estado pendiente"} · {item.candidates.length} filas
              </span>
              <time>{formatDateTime(item.created_at)}</time>
            </div>
            <div className="catalog-toolbar">
              {["REVIEW_READY", "CONFIRMED", "UNDONE"].includes(item.status) && (
                <button type="button" disabled={busy} onClick={() => void openReview(item)}>
                  {item.status === "REVIEW_READY" ? "Revisar fuente y cambios" : "Ver fuente"}
                </button>
              )}
              {canWrite && item.status === "CONFIRMED" && (
                <button type="button" disabled={busy} onClick={() => void undo(item)}>
                  Deshacer publicación
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
      {entry && (
        <div className="catalog-import-review">
          <header className="catalog-toolbar">
            <h4>Revisión · {entry.file_name}</h4>
            <button type="button" disabled={busy} onClick={() => void close()}>
              Cerrar revisión
            </button>
          </header>
          <p>
            Las filas con dudas o errores están desmarcadas. Lo ausente queda Sin dato; selecciona
            una fila solo después de contrastarla con la fuente.
          </p>
          {canWrite ? (
            <button
              type="button"
              disabled={busy}
              onClick={() => void download(`/api/v1/catalog-imports/${entry.id}/source/`)}
            >
              Descargar original para contrastar
            </button>
          ) : null}
          {entry.warnings.map((warning) => (
            <p key={warning} className="catalog-ingest-message">
              {WARNINGS[warning] ?? warning}
            </p>
          ))}
          <div className="catalog-sheet-tabs" role="group" aria-label="Hojas de la importación">
            {sheets
              .filter((item) => rows.some((row) => row.sheet === item.name))
              .map((item) => (
                <button
                  type="button"
                  key={item.name}
                  aria-pressed={sheetName === item.name}
                  onClick={() => {
                    setSheetName(item.name);
                    setRowKey(rows.find((row) => row.sheet === item.name)?.key ?? "");
                  }}
                >
                  {item.name} · {rows.filter((row) => row.sheet === item.name).length}
                </button>
              ))}
          </div>
          <div className="catalog-review-layout">
            <div className="catalog-review-rows">
              {rows
                .filter((row) => row.sheet === sheetName)
                .map((row) => (
                  <div key={row.key} className={rowKey === row.key ? "is-selected" : ""}>
                    {canReview && (
                      <input
                        type="checkbox"
                        aria-label={`Incluir fila ${row.row}`}
                        checked={row.include}
                        disabled={busy}
                        onChange={(event) => {
                          setRows((current) =>
                            current.map((item) =>
                              item.key === row.key
                                ? { ...item, include: event.target.checked }
                                : item,
                            ),
                          );
                          setDiff(null);
                          setReviewed(false);
                          setDirty(true);
                        }}
                      />
                    )}
                    <button
                      type="button"
                      aria-pressed={rowKey === row.key}
                      onClick={() => setRowKey(row.key)}
                    >
                      <strong>
                        {inputText(row.values.sku || row.values.system_code) || "Sin código"}
                      </strong>
                      <span>
                        Fila {row.row} · {row.method === "AI" ? "Propuesta de IA" : "Plantilla"}
                      </span>
                      <span>
                        {row.confidence === "HIGH_CANDIDATE"
                          ? "Lectura con fuente"
                          : row.confidence === "LOW"
                            ? "Lectura dudosa"
                            : "Requiere revisión"}
                      </span>
                      {row.errors.length > 0 && <span>Requiere corrección</span>}
                    </button>
                  </div>
                ))}
            </div>
            {selected && sheet && (
              <fieldset className="catalog-review-fields" disabled={busy || !canReview}>
                <legend>
                  {sheet.name} · fila {selected.row}
                </legend>
                <div className="catalog-review-heading">
                  <span>Campo</span>
                  <span>Valor revisado</span>
                  <span>Fuente del proveedor</span>
                </div>
                {sheet.columns.map((column) => {
                  if (column.key === "paired_leaf_rule") return null;
                  if (column.key === "finishes" && selected.values.finish_authority) return null;
                  const evidence = selected.fields[column.key] ?? {};
                  const value = selected.values[column.key];
                  const errors = diff
                    ? diff.errors.filter(
                        (error) => error.key === selected.key && error.field === column.key,
                      )
                    : selected.errors.filter((error) => error.field === column.key);
                  const id = `review-${selected.key}-${column.key}`;
                  return (
                    <div className="catalog-review-field" key={column.key}>
                      <label htmlFor={id}>
                        {column.label}
                        {column.required && <small>Requerido</small>}
                      </label>
                      <div>
                        {column.key === "section" ? (
                          <ImportedSectionFields
                            value={value}
                            onChange={(next) => patch(selected.key, column.key, next)}
                          />
                        ) : column.key === "extra_authority" ? (
                          <ExtraAuthorityEditor
                            value={(value as ExtraAuthority | null) ?? null}
                            onChange={(next) => patch(selected.key, column.key, next)}
                          />
                        ) : column.key === "finish_authority" ? (
                          <FinishAuthorityEditor
                            value={(value as FinishAuthority | null) ?? null}
                            material={String(selected.values.material ?? "PVC")}
                            onChange={(next) => patch(selected.key, column.key, next)}
                          />
                        ) : column.key === "opening_capabilities" ? (
                          <OpeningCapabilitiesEditor
                            capabilities={Array.isArray(value) ? (value as Capability[]) : []}
                            paired={(selected.values.paired_leaf_rule as PairedRule | null) ?? null}
                            family={String(selected.values.system_family ?? "CASEMENT")}
                            kits={rows
                              .filter(
                                (row) =>
                                  row.sheet === "Herrajes" &&
                                  row.values.system_code === selected.values.system_code,
                              )
                              .map((row) => ({
                                id: row.key,
                                sku: String(row.values.sku ?? ""),
                                name: String(
                                  row.values.name ?? "Sin dato: falta el nombre del herraje",
                                ),
                              }))}
                            onChange={(next) => patch(selected.key, column.key, next)}
                            onPair={(next) => patch(selected.key, "paired_leaf_rule", next)}
                          />
                        ) : column.kind === "json" ? (
                          <ComponentFields
                            id={id}
                            value={value}
                            onChange={(next) => patch(selected.key, column.key, next)}
                          />
                        ) : column.choices || column.kind === "boolean" ? (
                          <select
                            id={id}
                            value={inputText(value)}
                            onChange={(event) =>
                              patch(selected.key, column.key, event.target.value || null)
                            }
                          >
                            <option value="">Sin dato</option>
                            {Object.entries(column.choices ?? { Sí: "Sí", No: "No" }).map(
                              ([key, label]) => (
                                <option key={key} value={key}>
                                  {String(label)}
                                </option>
                              ),
                            )}
                          </select>
                        ) : (
                          <input
                            id={id}
                            value={inputText(value)}
                            placeholder="Sin dato"
                            inputMode={
                              ["decimal", "positive"].includes(column.kind) ? "decimal" : undefined
                            }
                            onChange={(event) =>
                              patch(selected.key, column.key, event.target.value || null)
                            }
                          />
                        )}
                        {errors.map((error) => (
                          <p key={error.message} className="catalog-field-error" role="alert">
                            {error.message}
                          </p>
                        ))}
                      </div>
                      <div className="catalog-source">
                        <span>
                          {evidence.ref?.replace(/^(.+)!([A-Z]+[0-9]+)$/u, "$1 · celda $2") ||
                            "Sin referencia"}
                        </span>
                        {column.kind === "json" ||
                        column.key === "finishes" ||
                        /\d+[.,]\d{4,}/u.test(evidence.quote ?? "") ? (
                          <details>
                            <summary>Ver texto original de la fuente</summary>
                            <div>
                              <SourceHighlight quote={evidence.quote} literal={evidence.literal} />
                            </div>
                          </details>
                        ) : (
                          <SourceHighlight quote={evidence.quote} literal={evidence.literal} />
                        )}
                        {evidence.confidence !== "HIGH" && (
                          <strong>
                            {evidence.confidence === "LOW"
                              ? "Lectura dudosa · revisa la fuente"
                              : "Sin dato · la fuente no lo declara"}
                          </strong>
                        )}
                        {evidence.proposed != null && value == null && (
                          <small>Lectura dudosa: {display(evidence.proposed, column)}</small>
                        )}
                      </div>
                    </div>
                  );
                })}
              </fieldset>
            )}
          </div>
          <div className="catalog-toolbar">
            {canReview && (
              <button
                type="button"
                className="ui-button--primary"
                disabled={busy || !rows.some((row) => row.include)}
                onClick={() => void preview()}
              >
                Comparar cambios
              </button>
            )}
            <button
              type="button"
              disabled={busy}
              onClick={() =>
                void download(
                  `/api/v1/catalog-imports/${entry.id}/export/?sheet=${encodeURIComponent(sheetName)}`,
                )
              }
            >
              Exportar esta hoja CSV
            </button>
          </div>
          {diff && (
            <div className="catalog-review-diff">
              <h4>Cambios antes de publicar</h4>
              {diff.errors.length > 0 && (
                <ul role="alert">
                  {diff.errors.map((error, index) => (
                    <li key={index}>
                      <button
                        type="button"
                        onClick={() => {
                          const row = rows.find((item) => item.key === error.key);
                          if (row) {
                            setSheetName(row.sheet);
                            setRowKey(row.key);
                          }
                        }}
                      >
                        Fila {rows.find((row) => row.key === error.key)?.row}: {error.message}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              {diff.changes.map((change, index) => {
                const row = rows.find((item) => item.key === change.key);
                const definition = sheets.find((item) => item.name === change.sheet);
                return (
                  <details key={`${change.key}-${index}`} open>
                    <summary>
                      {change.sheet} ·{" "}
                      {inputText(
                        row?.values.name ||
                          row?.values.glass_spec ||
                          row?.values.sku ||
                          row?.values.system_code,
                      )}{" "}
                      ·{" "}
                      {
                        { create: "Crear", update: "Actualizar", none: "Sin cambios" }[
                          change.action
                        ]
                      }
                    </summary>
                    <DiffFields
                      before={change.before}
                      after={change.after}
                      columns={definition?.columns ?? []}
                    />
                  </details>
                );
              })}
              {!diff.errors.length && canReview && (
                <>
                  <label className="catalog-review-attestation">
                    <input
                      type="checkbox"
                      checked={reviewed}
                      onChange={(event) => setReviewed(event.target.checked)}
                    />
                    <span>
                      Revisé la fuente y los cambios seleccionados. Autorizo su publicación técnica.
                    </span>
                  </label>
                  <button
                    type="button"
                    className="ui-button--primary"
                    disabled={busy || !reviewed}
                    onClick={() => void publish()}
                  >
                    Publicar catálogo revisado
                  </button>
                </>
              )}
            </div>
          )}
          <details className="catalog-import-timeline">
            <summary>Historial de la importación</summary>
            {timelineError ? (
              <>
                <p role="alert">{timelineError}</p>
                <button type="button" onClick={() => setTimelineReload((value) => value + 1)}>
                  Reintentar historial
                </button>
              </>
            ) : timeline === null ? (
              <p role="status">Cargando historial…</p>
            ) : (
              <ol>
                {timeline.items.map((event) => (
                  <li key={event.id}>
                    <strong>
                      {{
                        UPLOADED: "Archivo recibido",
                        EXTRACTING: "Extracción iniciada",
                        REVIEW_READY: "Candidatos preparados",
                        REVIEW: "Diff revisado",
                        PUBLISH: "Publicación confirmada",
                        UNDO: "Publicación deshecha",
                        FAILED: "Extracción fallida",
                        HISTORICAL_STATE: "Estado histórico; pasos anteriores sin registro",
                      }[event.action] ?? "Paso de importación"}
                    </strong>
                    <span>
                      {event.actor} · {formatDateTime(event.created_at)}
                    </span>
                  </li>
                ))}
              </ol>
            )}
          </details>
        </div>
      )}
    </section>
  );
}
function ComponentFields({
  id,
  value,
  onChange,
}: {
  id: string;
  value: unknown;
  onChange: (value: unknown) => void;
}): JSX.Element {
  const components = Array.isArray(value) ? (value as Record<string, unknown>[]) : [];
  const patch = (index: number, field: string, next: string) =>
    onChange(
      components.map((component, current) =>
        current === index ? { ...component, [field]: next } : component,
      ),
    );
  return (
    <div id={id} className="catalog-components">
      {components.map((component, index) => (
        <div key={index}>
          {["sku", "name", "qty", "unit"].map((field, column) => (
            <label key={field}>
              {["SKU", "Nombre", "Cantidad", "Unidad"][column]}
              {field === "unit" ? (
                <select
                  value={inputText(component[field])}
                  onChange={(event) => patch(index, field, event.target.value)}
                >
                  <option value="">Sin dato</option>
                  {Object.entries({
                    EA: "Unidad",
                    unit: "Unidad del proveedor",
                    pair: "Par",
                    set: "Conjunto",
                    KIT: "Kit",
                    M: "Metro",
                  }).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  value={inputText(component[field])}
                  onChange={(event) => patch(index, field, event.target.value)}
                />
              )}
            </label>
          ))}
          <button
            type="button"
            onClick={() => onChange(components.filter((_, current) => current !== index))}
          >
            Quitar componente
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={() => onChange([...components, { sku: "", name: "", qty: "", unit: "" }])}
      >
        Agregar componente
      </button>
    </div>
  );
}
function DiffFields({
  before,
  after,
  columns,
  prefix = "",
}: {
  before: unknown;
  after: unknown;
  columns: CatalogTemplateColumn[];
  prefix?: string;
}): JSX.Element {
  if (Array.isArray(after))
    return (
      <>
        {after.map((value, index) => (
          <DiffFields
            key={index}
            before={Array.isArray(before) ? before[index] : null}
            after={value}
            columns={columns}
            prefix={prefix}
          />
        ))}
      </>
    );
  if (after && typeof after === "object")
    return (
      <div className="catalog-diff-values">
        {Object.entries(after).map(([key, value]) => {
          if (key === "finishes" && (after as Record<string, unknown>).finish_authority)
            return null;
          if (
            key.endsWith("_id") ||
            [
              "id",
              "sku",
              "system_code",
              "code",
              "catalog_id",
              "composition_origin",
              "system_id",
              "profile_article_id",
              "bead_article_id",
              "cost_list_id",
              "catalog_import",
              "method",
            ].includes(key)
          )
            return null;
          const previous =
            before && typeof before === "object" ? (before as Record<string, unknown>)[key] : null;
          if (key === "finish_authority")
            return (
              <section key={key} aria-label="Comparación de carta por caras">
                {(
                  [
                    ["Antes de publicar", previous],
                    ["Carta a publicar", value],
                  ] as const
                ).map(([label, chart]) => (
                  <details key={label} open={label === "Carta a publicar"}>
                    <summary>{label}</summary>
                    {chart ? (
                      <fieldset disabled>
                        <FinishAuthorityEditor
                          value={chart as FinishAuthority}
                          material={(chart as FinishAuthority).material}
                          onChange={() => {}}
                        />
                      </fieldset>
                    ) : (
                      <p>Sin carta por caras.</p>
                    )}
                  </details>
                ))}
              </section>
            );
          if (key === "extra_authority")
            return (
              <section key={key} aria-label="Comparación de accesorios y extras">
                {(
                  [
                    ["Antes de publicar", previous],
                    ["Extras a publicar", value],
                  ] as const
                ).map(([label, authority]) => (
                  <details key={label} open={label === "Extras a publicar"}>
                    <summary>{label}</summary>
                    {authority ? (
                      <fieldset disabled>
                        <ExtraAuthorityEditor
                          value={authority as ExtraAuthority}
                          onChange={() => {}}
                        />
                      </fieldset>
                    ) : (
                      <p>Sin autoridad de accesorios.</p>
                    )}
                  </details>
                ))}
              </section>
            );
          if (
            value &&
            typeof value === "object" &&
            !["opening_capabilities", "paired_leaf_rule"].includes(key)
          )
            return (
              <DiffFields
                key={key}
                before={previous}
                after={value}
                columns={columns}
                prefix={key === "sliding_parameters" ? "sliding." : prefix}
              />
            );
          const column = columns.find(
            (column) =>
              column.key === prefix + key ||
              column.key === key ||
              (key === "code" && column.key === "system_code"),
          );
          const label =
            column?.label ??
            (
              {
                technical_sku: "SKU técnico",
                purchasing_sku: "SKU de compra",
                purchase_unit: "Unidad de compra",
                description: "Descripción",
                category: "Clasificación",
                qty: "Cantidad",
                source: "Fuente",
              } as Record<string, string>
            )[key] ??
            "Dato de catálogo";
          return (
            <div key={key}>
              <span>
                {column?.kind === "date" ? label.replace("aaaa-mm-dd", "dd-mm-aaaa") : label}
              </span>
              <del>{display(previous, column, key)}</del>
              <ins>{display(value, column, key)}</ins>
            </div>
          );
        })}
      </div>
    );
  return <span>{display(after)}</span>;
}
