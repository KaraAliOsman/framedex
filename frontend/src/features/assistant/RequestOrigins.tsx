import type { AiAgentStep, AiStepAssumption, AiStepOrigin } from "../../api/generated/models";

/** P08 · where each window the assistant created comes from. The request is
 * shown with every cited phrase marked and numbered like its window; the
 * choices the request does not state are listed for confirmation. Every
 * span and assumption is computed by the server — nothing is re-derived. */

const FIELD: Record<AiStepAssumption["field"], string> = {
  series: "Serie",
  glass: "Vidrio",
  color: "Color",
  opening: "Apertura",
};

function marked(text: string, marks: { origin: AiStepOrigin; number: number }[]): JSX.Element[] {
  const parts: JSX.Element[] = [];
  let cursor = 0;
  for (const { origin, number } of marks) {
    if (origin.start < cursor || origin.end > text.length) continue;
    if (origin.start > cursor)
      parts.push(<span key={`t${cursor}`}>{text.slice(cursor, origin.start)}</span>);
    parts.push(
      <mark key={`m${origin.start}`} className="request-origins__mark" data-window={number}>
        {text.slice(origin.start, origin.end)}
        <sup aria-label={`ventana ${number}`}>{number}</sup>
      </mark>,
    );
    cursor = origin.end;
  }
  if (cursor < text.length) parts.push(<span key={`t${cursor}`}>{text.slice(cursor)}</span>);
  return parts;
}

export function RequestOrigins({ step }: { step: AiAgentStep }): JSX.Element | null {
  const origins = step.origins ?? [];
  if (!origins.length) return null;
  const sources = step.sources ?? [];
  const numbered = origins.map((origin, index) => ({ origin, number: index + 1 }));
  const assumptions = step.assumptions ?? [];
  const flagged = assumptions.filter((item) => item.source === "agent");
  const usual = assumptions.filter((item) => item.source === "usual");
  return (
    <section className="request-origins" aria-label="Origen de las ventanas">
      {sources.map((source, index) => {
        const marks = numbered
          .filter(({ origin }) => origin.source === index)
          .sort((left, right) => left.origin.start - right.origin.start);
        if (!marks.length) return null;
        return (
          <figure key={index} className="request-origins__source">
            <figcaption>
              {source.kind === "request" ? "Mensaje original" : `Adjunto ${index}`}
            </figcaption>
            <blockquote>{marked(source.text, marks)}</blockquote>
          </figure>
        );
      })}
      <ol className="request-origins__windows" aria-label="Ventanas y su frase">
        {numbered.map(({ origin, number }) => (
          <li key={number}>
            <span className="request-origins__number" aria-hidden="true">
              {number}
            </span>
            <span>
              <strong>{origin.location || `Ventana ${number}`}</strong> · «{origin.quote}»
            </span>
          </li>
        ))}
      </ol>
      {flagged.length ? (
        <div className="request-origins__assumptions" role="note">
          <h4>
            {flagged.length === 1
              ? "1 supuesto que conviene confirmar"
              : `${flagged.length} supuestos que conviene confirmar`}
          </h4>
          <ul>
            {flagged.map((item, index) => (
              <li key={index}>
                <strong>{item.location}</strong> · {FIELD[item.field]}: {item.value}
                {item.reason ? <span> — {item.reason}</span> : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {usual.length ? (
        <p className="request-origins__usual">
          Lo habitual de tu empresa:{" "}
          {usual.map((item) => `${FIELD[item.field].toLowerCase()} ${item.value}`).join(" · ")}
        </p>
      ) : null}
    </section>
  );
}
