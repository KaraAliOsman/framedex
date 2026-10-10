import { DemoBadge } from "../../ui";
import { fmtMm, formatDateTime } from "../../format";
import type { AuthorityProvenance, EvidenceRow, SectionFacts } from "../../api/generated/models";
import { catalogVocabulary } from "./catalogModel";

export function SourceHighlight({
  quote,
  literal,
}: {
  quote?: string | null;
  literal?: string | null;
}) {
  if (!quote) return <p>La fuente no declara este campo.</p>;
  const at = literal ? quote.indexOf(literal) : -1;
  return (
    <blockquote>
      {at < 0 ? (
        quote
      ) : (
        <>
          {quote.slice(0, at)}
          <mark>{literal}</mark>
          {quote.slice(at + (literal?.length ?? 0))}
        </>
      )}
    </blockquote>
  );
}

export function CatalogProvenance({
  row,
  evidence = [],
}: {
  row: {
    id?: string;
    is_demo?: boolean;
    data_provenance?: string;
    authority_provenance?: AuthorityProvenance;
    technical_reviewed_at?: string | null;
    review_pending?: boolean;
  };
  evidence?: EvidenceRow[];
}) {
  const authority = row.authority_provenance;
  const demo =
    row.is_demo || row.data_provenance === "SEED_SYNTHETIC" || authority?.state === "DEMO";
  const label = demo
    ? "DEMO"
    : ({
        VERIFIED: "Verificado con evidencia",
        REVIEWED: "Revisado por técnico",
        DECLARED: "Declarado",
        UNKNOWN: "Sin fuente verificada",
      }[authority?.state ?? ""] ?? "Fuente pendiente");
  const sources = evidence.filter((source) => source.row_id === row.id);
  return (
    <details className="catalog-provenance">
      <summary>
        {demo ? (
          <DemoBadge />
        ) : (
          <span className={`ws-badge${authority?.state === "VERIFIED" ? " ws-badge--ok" : ""}`}>
            {label}
          </span>
        )}
      </summary>
      <div>
        <p>
          {authority?.reason ??
            (demo
              ? "Datos sintéticos; sin certificación del fabricante."
              : "La revisión humana no equivale a un certificado del fabricante.")}
        </p>
        <p>
          {authority?.reviewer ?? "Revisor: Sin dato"} ·{" "}
          {authority?.reviewed_at
            ? formatDateTime(authority.reviewed_at)
            : "Fecha de revisión: Sin dato"}
        </p>
        {authority?.missing_fields.length ? (
          <p>
            Falta evidencia vigente para:{" "}
            {authority.missing_fields
              .map((key) => catalogVocabulary[`field.${key}`] ?? "parámetro técnico")
              .join(", ")}
            .
          </p>
        ) : null}
        {sources.length ? (
          sources.map((source) => (
            <details key={source.id}>
              <summary>
                {catalogVocabulary[`field.${source.field_name}`] ?? "Dato técnico"} ·{" "}
                {source.source_document}
              </summary>
              <p>
                {source.source_ref ??
                  (source.source_page ? `Página ${source.source_page}` : "Referencia: Sin dato")}
              </p>
              <SourceHighlight quote={source.source_quote} literal={source.source_literal} />
              <p>
                {source.extraction_method === "HUMAN_CORRECTION"
                  ? "Corrección humana; no se atribuye al fabricante."
                  : source.review_state === "REVIEWED"
                    ? "Evidencia revisada"
                    : source.review_state === "REJECTED"
                      ? "Evidencia rechazada"
                      : "Evidencia pendiente de revisión"}
              </p>
              {source.reviewed_at ? <time>{formatDateTime(source.reviewed_at)}</time> : null}
              {source.source_url && /^https?:\/\//.test(source.source_url) ? (
                <a href={source.source_url} target="_blank" rel="noreferrer">
                  Abrir documento de origen
                </a>
              ) : null}
              {source.source_import_id ? (
                <a href={`/catalogs/systems?import=${source.source_import_id}`}>
                  Ver importación e historial
                </a>
              ) : null}
            </details>
          ))
        ) : (
          <p>
            Documento de origen: Sin dato. Declara y revisa una fuente para respaldar los valores.
          </p>
        )}
      </div>
    </details>
  );
}

export function SectionReviewFacts({ facts }: { facts?: SectionFacts }) {
  const origins: Record<string, string> = {
    TOP_LEFT: "Esquina superior izquierda",
    TOP_RIGHT: "Esquina superior derecha",
    BOTTOM_LEFT: "Esquina inferior izquierda",
    BOTTOM_RIGHT: "Esquina inferior derecha",
    CENTROID: "Centroide",
  };
  const orientations: Record<string, string> = {
    EXTERIOR_LEFT: "Exterior a la izquierda",
    EXTERIOR_RIGHT: "Exterior a la derecha",
    EXTERIOR_UP: "Exterior arriba",
    EXTERIOR_DOWN: "Exterior abajo",
  };
  const reasons: Record<string, string> = {
    section_missing: "Falta la geometría de la sección.",
    section_invalid: "El contorno es inválido o se cruza.",
    section_interpretation_missing: "Declara la orientación y el origen local.",
    section_depth_mismatch: "La profundidad no coincide con el contorno en su orientación.",
    section_origin_mismatch: "El origen local no coincide con las coordenadas declaradas.",
  };
  return (
    <div className="catalog-section-facts">
      <p>Coordenadas en mm · vista ajustada al contenedor, sin escala física 1:1</p>
      <dl>
        <div>
          <dt>Orientación</dt>
          <dd>{orientations[facts?.orientation ?? ""] ?? "Sin dato"}</dd>
        </div>
        <div>
          <dt>Origen local</dt>
          <dd>{origins[facts?.local_origin ?? ""] ?? "Sin dato"}</dd>
        </div>
        {facts?.bounds ? (
          <div>
            <dt>Contorno</dt>
            <dd>
              {fmtMm(facts.bounds.width_mm)} × {fmtMm(facts.bounds.height_mm)} mm
            </dd>
          </div>
        ) : null}
      </dl>
      {facts?.reasons.map((reason) => (
        <p key={reason} className="catalog-field-error">
          {reasons[reason] ?? "Revisa la geometría antes de verificar este artículo."}
        </p>
      ))}
    </div>
  );
}
