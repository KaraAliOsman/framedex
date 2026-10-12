import { BrandMark, Wordmark } from "../brand/Brand";
import { EmptyIllustration } from "../ui/EmptyIllustration";
import { Orb, type OrbState } from "../features/assistant/Orb";
import { BotFigure } from "../features/assistant/BotFigure";
import "./brand-page.css";

const STATES: [OrbState, string][] = [
  ["idle", "En reposo"],
  ["input", "Recibiendo"],
  ["queued", "En cola"],
  ["thinking", "Pensando"],
  ["working", "Trabajando"],
  ["waiting", "Necesita un dato"],
  ["approval", "Requiere aprobación"],
  ["success", "Completado"],
  ["error", "Error"],
  ["canceled", "Cancelado"],
];

export function BrandPage(): JSX.Element {
  return (
    <main className="brand-specimen" data-density="office">
      <h1>Construcción de la marca</h1>
      <p>Sección de perfil · IBM Plex Sans 600 · ajuste óptico por debajo de 24 px.</p>
      <section aria-label="Prueba de tamaño">
        <h2>Marca</h2>
        <div className="brand-specimen-sizes">
          {[16, 24, 32, 72, 160].map((size) => (
            <figure key={size}>
              <BrandMark size={size} title={`Marca a ${size} píxeles`} />
              <figcaption>{size} px</figcaption>
            </figure>
          ))}
        </div>
        <h2>Logotipo</h2>
        {[72, 160].map((width) => (
          <figure key={width}>
            <Wordmark width={width} />
            <figcaption>{width} px</figcaption>
          </figure>
        ))}
      </section>
      <section>
        <h2>Asistente DEKOPEN</h2>
        <div className="brand-specimen-orbs">
          {STATES.map(([state, label]) => (
            <figure key={state}>
              <Orb state={state} size={32} title="Asistente DEKOPEN" />
              <BotFigure state={state} size={96} />
              <figcaption>{label}</figcaption>
            </figure>
          ))}
        </div>
      </section>
      <section>
        <h2>Láminas de estados vacíos</h2>
        <div className="brand-specimen-sizes">
          {(["positions", "cut-plan", "sheet", "connection"] as const).map((kind) => (
            <EmptyIllustration key={kind} kind={kind} />
          ))}
        </div>
      </section>
    </main>
  );
}
