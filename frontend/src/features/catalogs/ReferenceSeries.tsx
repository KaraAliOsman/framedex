import type {
  ReferenceRegistry,
  ReferenceSeries as ReferenceSeriesRecord,
} from "../../api/generated/models";
import { StatusBadge } from "../../ui";
import { FamilyIllustration, familyDepth, type ProfileFamily } from "../canvas/profileFamilies";

/** The source's own function wording (already Spanish, not an enum). */
function functionLabel(article: { role: string }): string {
  return article.role;
}

/** The family a source role names, for the illustrative silhouette. */
function familyForSourceRole(role: string): ProfileFamily {
  const value = role.toLocaleLowerCase("es-CL");
  if (value.includes("junquillo")) return "bead";
  if (value.includes("marco")) return "frame";
  if (value.includes("hoja") || value.includes("batiente")) return "sash";
  if (value.includes("travesa") || value.includes("montante") || value.includes("inversor"))
    return "mullion";
  if (value.includes("umbral") || value.includes("zócalo")) return "threshold";
  if (value.includes("acople") || value.includes("unión")) return "coupler";
  return "generic";
}

/** Recognisable family silhouette (never a verified section): helps tell a
 * frame from a sash or a bead at a glance in the series table. */
function ArticleGlyph({
  article,
  material,
}: {
  article: { role: string };
  material: string;
}): JSX.Element {
  const role = functionLabel(article);
  const family = familyForSourceRole(role);
  const width = family === "bead" ? 22 : 60;
  const depth = familyDepth(family);
  return (
    <svg
      className="reference-series__glyph"
      viewBox={`-4 -4 ${width + 8} ${depth + 8}`}
      role="img"
      aria-label={`Silueta ilustrativa de ${role.toLocaleLowerCase("es-CL")}`}
    >
      <FamilyIllustration
        family={family}
        widthMm={width}
        depthMm={depth}
        material={material}
        fill="var(--mat-pvc-fill)"
        edge="var(--text-secondary)"
      />
    </svg>
  );
}

/** Capability chips: reference, quotable, manufacturable and CNC are
 * different states; a reference never reads as «ready». */
export function CapabilityChips({
  capabilities,
}: {
  capabilities: ReferenceSeriesRecord["capabilities"];
}): JSX.Element {
  const rows: [keyof typeof capabilities, string][] = [
    ["reference", "Manual disponible"],
    ["quotable", "Cotizable"],
    ["manufacturable", "Fabricable"],
    ["cnc", "CNC"],
  ];
  return (
    <ul className="capability-chips" aria-label="Capacidades de la serie">
      {rows.map(([key, label]) => (
        <li key={key} data-state={capabilities[key] ? "yes" : "no"}>
          <span aria-hidden="true">{capabilities[key] ? "✓" : "—"}</span> {label}
          <span className="sr-only">{capabilities[key] ? ": sí" : ": no"}</span>
        </li>
      ))}
    </ul>
  );
}

/** Reference ficha of a real manufacturer's series: facts and articles exactly
 * as the cited pages state them, the sources, what is missing to quote, and
 * incidents of the source itself — never corrected by inference. */
export function ReferenceSeriesPanel({
  series,
  registry,
  canPrepare,
  onPrepare,
}: {
  series: ReferenceSeriesRecord;
  registry: ReferenceRegistry;
  canPrepare: boolean;
  onPrepare(series: ReferenceSeriesRecord): void;
}): JSX.Element {
  const source = (id: string) => registry.sources[id];
  return (
    <article className="reference-series" aria-labelledby={`ref-${series.id}`}>
      <header className="reference-series__head">
        <div>
          <p className="reference-series__brand">{series.manufacturer}</p>
          <h2 id={`ref-${series.id}`}>{series.series_name}</h2>
          <p className="reference-series__meta">
            {series.material} · {series.family}
            {series.uses.length ? ` · ${series.uses.join(", ")}` : ""}
          </p>
        </div>
        <StatusBadge tone="warning" showIcon={false}>
          {!series.capabilities.reference
            ? "Identidad sin resolver"
            : series.needs_manufacturer_manual
              ? "Necesita manual del fabricante"
              : "Completar serie para cotizar"}
        </StatusBadge>
      </header>
      <CapabilityChips capabilities={series.capabilities} />

      {series.facts.length ? (
        <section>
          <h3>Datos de la referencia</h3>
          <dl className="reference-series__facts">
            {series.facts.map((fact) => (
              <div key={fact.label}>
                <dt>{fact.label}</dt>
                <dd>
                  {fact.value}
                  <span className="reference-series__cite">
                    {source(fact.source)?.title ?? fact.source}
                    {fact.pages ? ` · pág. ${fact.pages}` : ""}
                  </span>
                </dd>
              </div>
            ))}
          </dl>
        </section>
      ) : null}

      {series.articles.length ? (
        <section>
          <h3>Artículos citados ({series.articles.length})</h3>
          <table className="reference-series__articles">
            <thead>
              <tr>
                <th>
                  <span className="sr-only">Silueta</span>
                </th>
                <th>Código</th>
                <th>Nombre en la referencia</th>
                <th>Función</th>
                <th>Documento</th>
              </tr>
            </thead>
            <tbody>
              {series.articles.map((article) => (
                <tr key={article.code}>
                  <td className="reference-series__glyph-cell">
                    <ArticleGlyph article={article} material={series.material} />
                  </td>
                  <td className="reference-series__code">{article.code}</td>
                  <td>{article.name}</td>
                  <td>{functionLabel(article)}</td>
                  <td className="reference-series__cite">
                    {source(article.source)?.title ?? article.source}
                    {article.pages ? ` · pág. ${article.pages}` : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="reference-series__hint">
            Las siluetas son ilustrativas de cada familia, no secciones verificadas. Sin largos de
            barra, pesos ni costos: la referencia no los acredita.
          </p>
        </section>
      ) : null}

      <section className="reference-series__missing">
        <h3>Qué falta para cotizar con esta serie</h3>
        <ul>
          {series.missing.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        {canPrepare && series.capabilities.reference ? (
          <button type="button" className="ui-button" onClick={() => onPrepare(series)}>
            Preparar esta serie en mi catálogo
          </button>
        ) : null}
      </section>

      {series.incidents.length ? (
        <section>
          <h3>Incidencias de la propia referencia</h3>
          <ul>
            {series.incidents.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {series.sources.length ? (
        <section>
          <h3>Documentos</h3>
          <ul className="reference-series__sources">
            {series.sources.map((id) => {
              const item = source(id);
              if (!item) return null;
              return (
                <li key={id}>
                  {item.url ? (
                    <a href={item.url} target="_blank" rel="noreferrer noopener">
                      {item.title}
                    </a>
                  ) : (
                    <strong>{item.title}</strong>
                  )}
                  <span>
                    {item.kind} · {item.holder}
                    {item.pages_total ? ` · ${item.pages_total} págs.` : ""}
                  </span>
                  {item.sha256 ? (
                    <code title="Huella SHA-256 del documento aportado">
                      {item.sha256.slice(0, 12)}…
                    </code>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}
    </article>
  );
}
