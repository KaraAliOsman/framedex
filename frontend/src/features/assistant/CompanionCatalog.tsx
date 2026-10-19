import { useState } from "react";

import { COMPANION_STATES, Companion, companionStateText } from "./Companion";

/** Internal pose catalog for the final review (contract 06 · 07): every
 * state at the optical sizes with one controllable clock. Reached only with
 * `?poses=1` on the assistant activity page; not a product screen. */
const SIZES = [24, 28, 32, 64, 96];

export function CompanionCatalog(): JSX.Element {
  const [clock, setClock] = useState<number | null>(null);
  const [size, setSize] = useState(64);
  return (
    <section className="aiws-hero" aria-label="Catálogo interno de poses del asistente">
      <div>
        <h2>Poses del asistente</h2>
        <p className="aiws-empty">
          Revisión interna: cada estado real con su gesto. El reloj congela la animación en un
          instante; vacío, se anima en vivo.
        </p>
        <label>
          Reloj (ms){" "}
          <input
            type="range"
            min={0}
            max={8000}
            step={50}
            value={clock ?? 0}
            onChange={(event) => setClock(Number(event.target.value))}
          />{" "}
          <span>{clock === null ? "en vivo" : `${clock} ms`}</span>
        </label>{" "}
        <button
          type="button"
          className="ui-button ui-button--ghost ui-button--compact"
          onClick={() => setClock(null)}
        >
          En vivo
        </button>{" "}
        <label>
          Tamaño{" "}
          <select value={size} onChange={(event) => setSize(Number(event.target.value))}>
            {SIZES.map((value) => (
              <option key={value} value={value}>
                {value} px
              </option>
            ))}
          </select>
        </label>
        <div className="companion-catalog">
          {COMPANION_STATES.map((state) => (
            <figure key={state}>
              <Companion state={state} size={size} clock={clock ?? undefined} />
              <figcaption>{companionStateText(state)}</figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}
