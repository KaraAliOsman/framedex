import { useState } from "react";
import type { CatalogTemplateSheet } from "../../api/generated/models";
import { Button } from "../../ui";
import { formatDecimal } from "../../format";
import { SourceHighlight } from "./CatalogProvenance";
import {
  doubleReadFields,
  readingText,
  reviewRowLabel,
  unresolvedReadFields,
  type CatalogReviewRow,
} from "./catalogDoubleReadModel";
import "./catalog-double-read.css";

/** Both citations remain visible. Choosing a reading changes only the draft;
 * the existing server review and explicit publication remain authoritative. */
export function CatalogDoubleReadReview({
  rows,
  sheets,
  disabled,
  onPatch,
  onInclude,
  onOpenRow,
}: {
  rows: CatalogReviewRow[];
  sheets: CatalogTemplateSheet[];
  disabled: boolean;
  onPatch: (row: string, field: string, value: unknown) => void;
  onInclude: (row: string, include: boolean) => void;
  onOpenRow: (row: CatalogReviewRow) => void;
}): JSX.Element {
  const [page, setPage] = useState(0);
  const disputed = rows.filter((row) => doubleReadFields(row).length > 0);
  const agreements = rows.reduce(
    (total, row) =>
      total + Object.values(row.fields).filter((field) => field.comparison === "AGREED").length,
    0,
  );
  const pending = rows.reduce((total, row) => total + unresolvedReadFields(row).length, 0);
  const pages = Math.max(1, Math.ceil(disputed.length / 10));
  const current = Math.min(page, pages - 1);
  return (
    <section className="catalog-double-read" aria-label="Diferencias entre las dos lecturas">
      <header>
        <h4>Revisa las diferencias del manual</h4>
        <p>
          {agreements} {agreements === 1 ? "campo coincide" : "campos coinciden"} en las dos
          lecturas. Quedan como propuestas; no necesitas confirmarlos uno por uno.
        </p>
        <p role="status">
          {pending === 0
            ? "No quedan diferencias por resolver. Revisa las filas que vas a incluir."
            : `${pending} ${pending === 1 ? "diferencia por resolver" : "diferencias por resolver"}. Elige una lectura citada o corrige el dato del taller.`}
        </p>
      </header>
      {!disputed.length && (
        <p>
          Ambas lecturas coinciden. Puedes comparar los cambios antes de publicar. Los datos que el
          manual no declara siguen pendientes de completar.
        </p>
      )}
      {disputed.slice(current * 10, (current + 1) * 10).map((row) => {
        const sheet = sheets.find((item) => item.name === row.sheet);
        const remaining = unresolvedReadFields(row);
        return (
          <article className="catalog-double-read__row" key={row.key}>
            <header>
              <div>
                <h5>{reviewRowLabel(row)}</h5>
                <p>
                  {row.sheet} · fila {row.row}
                </p>
              </div>
              <Button onClick={() => onOpenRow(row)}>Ver fila completa</Button>
            </header>
            {row.double_read?.identity_unique === false && (
              <p className="catalog-double-read__notice">
                Las lecturas no identifican la misma pieza con certeza. Contrasta el código y la
                serie con el original; excluye cualquier fila duplicada.
              </p>
            )}
            {doubleReadFields(row).map((field) => {
              const column = sheet?.columns.find((item) => item.key === field);
              const evidence = row.fields[field]!;
              const label = column?.label ?? "Campo por revisar";
              const value = row.values[field];
              const numeric = ["decimal", "positive", "integer", "count", "angle"].includes(
                column?.kind ?? "",
              );
              const structured =
                column?.kind === "json" ||
                evidence.readings?.some(
                  (reading) => reading.value != null && typeof reading.value === "object",
                );
              return (
                <fieldset className="catalog-double-read__field" key={field} disabled={disabled}>
                  <legend>{label}</legend>
                  <div className="catalog-double-read__readings">
                    {[0, 1].map((index) => {
                      const reading = evidence.readings?.[index];
                      const selected =
                        value != null && JSON.stringify(value) === JSON.stringify(reading?.value);
                      const cited =
                        reading?.confidence === "HIGH" && !!reading.ref && !!reading.quote;
                      return (
                        <div className="catalog-double-read__reading" key={index}>
                          <h6>Lectura {index + 1}</h6>
                          <ReadingValue value={reading?.value} numeric={numeric} />
                          <p>{reading?.ref || "Sin página citada"}</p>
                          {reading?.quote ? (
                            <SourceHighlight quote={reading.quote} literal={reading.literal} />
                          ) : (
                            <p>Esta lectura no aporta una cita.</p>
                          )}
                          <p className="catalog-double-read__origin">
                            {cited
                              ? "Con cita del manual"
                              : "Lectura dudosa · al elegirla queda como dato del taller"}
                          </p>
                          <Button
                            aria-pressed={selected}
                            disabled={reading?.value == null || reading.value === ""}
                            onClick={() => onPatch(row.key, field, reading?.value)}
                          >
                            {selected
                              ? `Lectura ${index + 1} elegida`
                              : `Usar lectura ${index + 1}`}
                          </Button>
                        </div>
                      );
                    })}
                  </div>
                  {structured ? (
                    <Button onClick={() => onOpenRow(row)}>Corregir en la fila completa</Button>
                  ) : (
                    <label className="catalog-double-read__correction">
                      Corregir {label.toLocaleLowerCase("es-CL")} como dato del taller
                      {column?.choices || column?.kind === "boolean" ? (
                        <select
                          className="ui-field__input"
                          value={value == null ? "" : String(value)}
                          onChange={(event) =>
                            onPatch(
                              row.key,
                              field,
                              column?.kind === "boolean" && event.target.value !== ""
                                ? event.target.value === "true"
                                : event.target.value || null,
                            )
                          }
                        >
                          <option value="">Elegir</option>
                          {Object.entries(column?.choices ?? { true: "Sí", false: "No" }).map(
                            ([key, text]) => (
                              <option key={key} value={key}>
                                {String(text)}
                              </option>
                            ),
                          )}
                        </select>
                      ) : (
                        <input
                          className="ui-field__input"
                          inputMode={
                            column &&
                            ["decimal", "positive", "integer", "count", "angle"].includes(
                              column.kind,
                            )
                              ? "decimal"
                              : undefined
                          }
                          value={value == null ? "" : String(value)}
                          onChange={(event) => onPatch(row.key, field, event.target.value || null)}
                        />
                      )}
                    </label>
                  )}
                  {value != null && (
                    <div className="catalog-double-read__chosen">
                      Valor revisado: <ReadingValue value={value} numeric={numeric} />
                    </div>
                  )}
                </fieldset>
              );
            })}
            <label className="catalog-double-read__include">
              <input
                type="checkbox"
                checked={row.include}
                disabled={disabled || (!row.include && remaining.length > 0)}
                onChange={(event) => onInclude(row.key, event.target.checked)}
              />
              Incluir {reviewRowLabel(row)} al comparar los cambios
            </label>
            {remaining.length > 0 && <p>Resuelve las diferencias para incluir esta fila.</p>}
          </article>
        );
      })}
      {pages > 1 && (
        <nav className="catalog-double-read__pagination" aria-label="Páginas de diferencias">
          <Button disabled={current === 0} onClick={() => setPage(current - 1)}>
            Anterior
          </Button>
          <span>
            Página {current + 1} de {pages} · {disputed.length} filas
          </span>
          <Button disabled={current === pages - 1} onClick={() => setPage(current + 1)}>
            Siguiente
          </Button>
        </nav>
      )}
    </section>
  );
}

function ReadingValue({
  value,
  numeric = false,
}: {
  value: unknown;
  numeric?: boolean;
}): JSX.Element {
  if (Array.isArray(value))
    return (
      <ul>
        {value.map((item, index) => (
          <li key={index}>
            <ReadingValue value={item} />
          </li>
        ))}
      </ul>
    );
  if (value !== null && typeof value === "object")
    return (
      <dl>
        {Object.entries(value).map(([key, item]) => (
          <div key={key}>
            <dt>{key.replaceAll("_", " ")}</dt>
            <dd>
              <ReadingValue value={item} />
            </dd>
          </div>
        ))}
      </dl>
    );
  const text = readingText(value);
  const digits = text.split(".")[1]?.length ?? 0;
  return (
    <span className="catalog-double-read__value">
      {numeric && /^-?\d+(\.\d+)?$/.test(text) && digits <= 12 ? formatDecimal(text, digits) : text}
    </span>
  );
}
