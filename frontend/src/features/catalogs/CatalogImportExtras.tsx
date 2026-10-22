import { useEffect, useState } from "react";

import { apiFetchBlob } from "../../api/apiMutator";
import { catalogImportRetry } from "../../api/generated/dekopen";
import { Button, Loading } from "../../ui";
import { Icon } from "../../ui/Icon";
import { actionErrorDetail } from "../errors";

type Progress = {
  pages_total?: number;
  pages_done?: number;
  pages?: { text?: number; scan?: number; mixed?: number };
  chunks?: {
    index: number;
    first: number;
    last: number;
    state: string;
    error?: string | null;
    candidates?: number;
  }[];
};

/** Real progress of a PDF read in internal page batches: pages read, how
 * they were read and which batches failed — with a retry of only those. */
export function ImportProgress({
  importId,
  status,
  progress,
  orgId,
  canWrite,
  onRetried,
}: {
  importId: string;
  status: string;
  progress?: Progress | null;
  orgId: string;
  canWrite: boolean;
  onRetried(): void;
}): JSX.Element | null {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  if (!progress?.pages_total) {
    return ["UPLOADED", "EXTRACTING"].includes(status) ? (
      <Loading label="Preparando el análisis del catálogo" />
    ) : null;
  }
  const total = progress.pages_total;
  const done = progress.pages_done ?? 0;
  const failed = (progress.chunks ?? []).filter((chunk) => chunk.state === "FAILED");
  const visual = (progress.pages?.scan ?? 0) + (progress.pages?.mixed ?? 0);
  async function retry(): Promise<void> {
    setBusy(true);
    setError("");
    try {
      await catalogImportRetry(importId, { headers: { "X-Organization-ID": orgId } });
      onRetried();
    } catch (caught) {
      setError(
        actionErrorDetail(caught, "No se pudo reintentar. Vuelve a intentarlo en un momento."),
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="import-progress">
      {["UPLOADED", "EXTRACTING"].includes(status) ? (
        <Loading
          label="Analizando el catálogo"
          progress={(done / Math.max(total, 1)) * 100}
          detail={`Página ${Math.min(done + 1, total)} de ${total}`}
        />
      ) : (
        <p className="import-progress__summary">
          {total === 1 ? "1 página" : `${total} páginas`}
          {visual ? ` · ${visual} leídas también como imagen` : ""}
          {failed.length
            ? ` · ${failed.reduce((sum, chunk) => sum + chunk.last - chunk.first + 1, 0)} sin analizar`
            : ""}
        </p>
      )}
      {failed.length && status === "REVIEW_READY" ? (
        <div className="import-progress__failed" role="status">
          <span>
            {failed.map((chunk) => `páginas ${chunk.first}–${chunk.last}`).join(", ")} no se
            pudieron analizar. Lo demás ya está listo para revisar.
          </span>
          {canWrite ? (
            <Button size="compact" loading={busy} onClick={() => void retry()}>
              <Icon name="refresh" size={16} />
              Reintentar esas páginas
            </Button>
          ) : null}
        </div>
      ) : null}
      {error ? <p role="alert">{error}</p> : null}
    </div>
  );
}

type Row = {
  key: string;
  confidence: string;
  errors: { message: string }[];
  warnings?: string[];
  fields: Record<string, { confidence?: string; ref?: string }>;
  values: Record<string, unknown>;
  sheet: string;
};

const CAUSES: { id: string; title: string; effect: string; test(row: Row): boolean }[] = [
  {
    id: "errors",
    title: "Requieren corrección",
    effect: "No se pueden publicar hasta corregirlas.",
    test: (row) => row.errors.length > 0,
  },
  {
    id: "conflict",
    title: "Distintas de tu catálogo",
    effect: "Publicarlas cambiaría datos que ya usas; revisa antes.",
    test: (row) => (row.warnings ?? []).includes("catalog_conflicts_existing"),
  },
  {
    id: "document",
    title: "El PDF las dice distinto en dos lugares",
    effect: "Elige qué página manda; ambas referencias se conservan.",
    test: (row) => (row.warnings ?? []).includes("catalog_conflict_in_document"),
  },
  {
    id: "doubtful",
    title: "Lecturas dudosas",
    effect: "Contrasta el valor con la página antes de incluirlas.",
    test: (row) => Object.values(row.fields).some((field) => field.confidence === "LOW"),
  },
];

/** Exceptions grouped by cause and practical effect; consistent rows need no
 * cell-by-cell approval. */
export function ExceptionGroups({
  rows,
  label,
  onPick,
}: {
  rows: Row[];
  label(row: Row): string;
  onPick(row: Row): void;
}): JSX.Element {
  const groups = CAUSES.map((cause) => ({ cause, rows: rows.filter(cause.test) })).filter(
    (group) => group.rows.length > 0,
  );
  const clean = rows.filter((row) => !CAUSES.some((cause) => cause.test(row))).length;
  return (
    <section className="exception-groups" aria-label="Qué revisar">
      <p className="exception-groups__clean">
        <Icon name="check" size={16} />
        {clean === 1 ? "1 fila consistente" : `${clean} filas consistentes`} con su referencia
      </p>
      {groups.length === 0 ? (
        <p className="exception-groups__none">No hay excepciones que revisar.</p>
      ) : (
        groups.map(({ cause, rows: affected }) => (
          <details key={cause.id} className="exception-group" open={cause.id === "errors"}>
            <summary>
              <strong>{cause.title}</strong>
              <span className="exception-group__count">{affected.length}</span>
            </summary>
            <p className="exception-group__effect">{cause.effect}</p>
            <ul>
              {affected.slice(0, 40).map((row) => (
                <li key={row.key}>
                  <button type="button" className="ui-link" onClick={() => onPick(row)}>
                    {label(row)}
                  </button>
                  <span>{row.sheet}</span>
                </li>
              ))}
            </ul>
            {affected.length > 40 ? (
              <p className="exception-group__effect">Y {affected.length - 40} más en esta causa.</p>
            ) : null}
          </details>
        ))
      )}
    </section>
  );
}

export function sourcePageOf(
  row: { fields: Record<string, { ref?: string }> } | null,
): number | null {
  if (!row) return null;
  for (const field of Object.values(row.fields)) {
    const match = /p[áa]gina\s+(\d+)/iu.exec(field.ref ?? "");
    if (match) return Number(match[1]);
  }
  return null;
}

/** The source page beside the reviewed row. */
export function SourcePage({
  importId,
  page,
  orgId,
}: {
  importId: string;
  page: number | null;
  orgId: string;
}): JSX.Element | null {
  const [url, setUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    if (!page) return;
    let alive = true;
    let created: string | null = null;
    setFailed(false);
    void apiFetchBlob(`/api/v1/catalog-imports/${importId}/pages/${page}/`, {
      headers: { "X-Organization-ID": orgId },
    })
      .then(({ blob }) => {
        created = URL.createObjectURL(blob);
        if (alive) setUrl(created);
      })
      .catch(() => alive && setFailed(true));
    return () => {
      alive = false;
      if (created) URL.revokeObjectURL(created);
    };
  }, [importId, page, orgId]);
  if (!page) return null;
  return (
    <figure className="source-page">
      <figcaption>Página {page} del catálogo</figcaption>
      {failed ? (
        <p className="source-page__missing">No se pudo mostrar la página.</p>
      ) : url ? (
        <img src={url} alt={`Página ${page} del catálogo original`} />
      ) : (
        <Loading label="Cargando la página" />
      )}
    </figure>
  );
}

type CutTemplate = {
  sheets: number;
  lines: string[];
  typologies: string[];
  profiles: string[];
  consistent_offsets: {
    line: string | null;
    typology: string | null;
    code: string;
    side: "width" | "height";
    angles: number[];
    offset_mm: string;
    examples: { page: number; literal: string }[];
  }[];
  source_notes: { pages: number[]; note: string }[];
};

/** Manufacturer cut sheets found in the PDF: worked examples kept as
 * evidence to verify cut rules. Offsets that repeat across sizes are shown
 * as observations for a technical reviewer, never as published rules. */
export function CutTemplatePanel({
  template,
}: {
  template?: CutTemplate | null;
}): JSX.Element | null {
  if (!template?.sheets) return null;
  return (
    <details className="cut-template">
      <summary>
        <Icon name="cut" size={16} />
        Plantilla de corte del fabricante · {template.sheets} hojas · {template.lines.join(", ")}
      </summary>
      <p className="cut-template__lead">
        Son ejemplos resueltos por el fabricante. DEKOPEN los conserva para comprobar las reglas de
        corte que publiques; no se convierten en reglas por sí solos.
      </p>
      {template.consistent_offsets.length ? (
        <table className="ui-data-table cut-template__table">
          <caption>Medidas que se repiten en ejemplos de distinto tamaño</caption>
          <thead>
            <tr>
              <th scope="col">Perfil</th>
              <th scope="col">Lado</th>
              <th scope="col">Cortes</th>
              <th scope="col" className="is-numeric">
                Largo respecto a la medida
              </th>
              <th scope="col">Dónde</th>
              <th scope="col">Evidencia</th>
            </tr>
          </thead>
          <tbody>
            {template.consistent_offsets.map((item) => (
              <tr
                key={`${item.line}-${item.typology}-${item.code}-${item.side}-${item.angles.join("-")}`}
              >
                <td>{item.code}</td>
                <td>{item.side === "width" ? "Ancho" : "Alto"}</td>
                <td>{item.angles.map((angle) => `${angle}°`).join(" / ")}</td>
                <td className="is-numeric">
                  {Number(item.offset_mm) > 0 ? "+" : ""}
                  {item.offset_mm.replace("-", "−").replace(".", ",")} mm
                </td>
                <td>{item.typology ?? "Todas las tipologías"}</td>
                <td>
                  <span title={item.examples.map((example) => example.literal).join("\n")}>
                    {item.examples.length} ejemplos · págs.{" "}
                    {[...new Set(item.examples.map((example) => example.page))].join(", ")}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
      {template.source_notes.length ? (
        <ul className="cut-template__notes" aria-label="Inconsistencias de la referencia">
          {template.source_notes.map((note, index) => (
            <li key={index}>
              <Icon name="warning" size={16} />
              Págs. {note.pages.join("–")}: {note.note}
            </li>
          ))}
        </ul>
      ) : null}
    </details>
  );
}
